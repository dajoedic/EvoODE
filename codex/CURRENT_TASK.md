# WP-N27b — Deadlock im Zell-Worker des ODEFormer-Grids beheben
**Language: Python**

## Ausführung

Lokal umsetzbar und testbar. Kein Docker, kein `oc`, kein Push. Nur die betroffenen Tests ausführen.

## Ausgangslage

Der Smoke-Job des ODEFormer-Referenzrasters auf Orion (`k8s/odeformer_reference_grid_smoke_job.yaml`,
Image `9ff548e`) hängt seit dem Start mit 0 CPU. Diagnose im laufenden Pod:

- PID 1 (Elternprozess) steht in `do_wait`, also in `process.join()`.
- PID 69 (Kind, per `fork`) hat zwei Threads. Der Hauptthread wartet in `futex_wait_queue`: Beim
  Beenden wartet er auf den Feeder-Thread der Queue. Der Feeder-Thread steht in `write(fd=4,
  8395 Bytes)`, fd 4 ist das Schreibende der Queue-Pipe.
- Lokal (Docker Desktop) läuft derselbe Code mit derselben Zelle in 4–7 s durch.

Ursache: `baselines/run_odeformer_grid.py`, `run_cell_with_hard_timeout`. Dort steht
`process.join(...)` **vor** `result_queue.get_nowait()`. Das Kind kann nicht enden, solange der
Feeder-Thread seine Daten nicht in die Pipe schreiben konnte. Passt der Record nicht auf einmal in
den Pipe-Puffer, wartet das Kind auf den Leser und der Elternprozess auf das Kind. Lokal fasst die
Pipe 64 KiB. Auf Orion war sie beim Anlegen vermutlich kleiner: Linux vergibt nur eine Seite, wenn
`pipe-user-pages-soft` überschritten ist. Die genaue Größe ist unerheblich. Das Muster ist in der
Python-Dokumentation von `multiprocessing` als Deadlock beschrieben ("joining processes that use
queues").

## Was zu tun ist

1. In `run_cell_with_hard_timeout` erst das Ergebnis aus der Queue holen, **dann** joinen:
   - Blockierendes `get` mit dem Budget als Timeout (`None` = ohne Grenze).
   - Kommt nichts, weil das Budget abgelaufen ist oder das Kind ohne Ergebnis gestorben ist, gilt
     das bisherige Verhalten: `terminate`/`kill` und derselbe Timeout- bzw. Fehler-Record wie heute.
   - Ein Kind, das stirbt, ohne etwas zu schicken, darf den Elternprozess **nicht** ewig blockieren,
     auch nicht bei `budget=None`. Deshalb nicht blind blockierend lesen, sondern das Lesen mit der
     Lebendprüfung des Kindes verbinden (z. B. `get` in kurzen Intervallen, dazwischen
     `is_alive()`/`exitcode` prüfen). Eine Wall-Clock-Grenze für ODEFormer selbst wird dadurch
     **nicht** eingeführt; das Intervall ist nur ein Warte-Takt.
   - Danach `join` mit kurzer Frist, dann wie heute ggf. `terminate`/`kill`.
2. Records, Felder und Ausgänge bleiben unverändert. Das betrifft nur die Prozesskommunikation.
3. Prüfen, ob `run_odeformer_repeatability.py` oder andere Stellen (`grep` nach
   `get_context("fork")`, `.join(` vor `.get`) dasselbe Muster haben. Wenn ja, dort dieselbe
   Korrektur, im Report aufgeführt.

## Verboten

- Keine Git-Operationen.
- Nichts an ODEFormer-Aufruf, Timeout-Zählung, Modus oder Records ändern.
- Kein `spawn` statt `fork`: Das würde das Laden der Gewichte und den Zustand pro Zelle verändern.

## Abnahme

1. **Regressionstest für den Deadlock:** ein Test-Runner, der einen Payload **deutlich größer als
   64 KiB** (z. B. 1 MiB) in die Queue legt. Mit dem alten Code hängt er, mit dem neuen liefert er
   den Record zurück. Der Test braucht eine eigene Zeitgrenze, damit er nicht die Suite blockiert,
   falls die Korrektur fehlschlägt.
2. Test: Ein Kind, das ohne Ergebnis endet (`os._exit(3)`), liefert den bisherigen Fehler-Record,
   auch bei `budget=None`, und zwar schnell.
3. Test: Ein Kind, das länger als ein kleines Budget braucht, liefert den bisherigen Timeout-Record.
4. `python -m pytest baselines/tests -q` grün.
5. Report `codex/reports/REPORT_WP_N27b.md`.
