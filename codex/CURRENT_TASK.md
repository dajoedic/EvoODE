# WP-N24c — Timeouts dort zählen, wo sie feuern; Ausgänge ehrlich benennen
**Language: Python**

## Ausführung

Lokal umsetzbar und testbar, kein Docker nötig. Den Rauchtest in Docker macht Claude.
Nichts starten, was länger als 15 Minuten läuft.

## Ausgangslage

WP-N24 und WP-N24b liegen uncommittet im Working Tree. Der Rauchtest in Docker (Claude,
2026-09-24) hat einen Messfehler der Instrumentierung gezeigt. Eine Diagnosesonde hat ihn
eingegrenzt.

- Kandidat, System 11, Fit-IC 1, `beam10_opt`, Modus `faithful`: Zwei Wiederholungen sind **nicht**
  bitgleich. `nfev` ist 31 gegen 35, die Rekonstruktion nach der Optimierung endet einmal `finite`,
  einmal `wrong_shape`. Die Timeout-Zähler stehen beide Male auf **0**. Unter `lifted` sind die
  Wiederholungen bitgleich.
- Die Sonde protokollierte jeden `_integrate_ode`-Aufruf der Konstantenoptimierung. Pro
  Wiederholung dauert **ein Aufruf genau 1,0001 s**, das ist der Timeout. Er kommt aber als
  Rückgabewert `None` zurück, nicht als Ausnahme. 45 von 51 Aufrufen liefern `None`.

**Ursache:** `odeformer/envs/generators.py`, Zweig `solve_ivp` in `_integrate_ode` (ca.
Zeile 890–905): `try: ... solve_ivp(...) except: return None`. Das **nackte `except`** fängt den
`MyTimeoutError`, den der `SIGALRM`-Handler mitten in `solve_ivp` wirft. Der Timeout kommt als
`None` heraus und erreicht den Zähler in `counted_integrate_ode` nie. Ein Timeout ist damit von
einem gewöhnlichen Solver-Fehler nicht zu unterscheiden.

Zwei weitere Befunde im selben Code:

- Das NaN-Sentinel am Ende von `_integrate_ode` (Liste aus NaN, Länge `len(times)`) entsteht bei
  NaN in der Trajektorie, bei einer zu kurzen Trajektorie **und bei jeder abgefangenen Warnung**.
  Nur im Nicht-`solve_ivp`-Pfad kommt es auch aus einem Timeout (`integrate_ode`, ca.
  Zeile 919–924). Das Label `odeformer_timeout` ist deshalb sachlich falsch.
- `ODEFormerAdapter.integrate_expression` und `optimize_constants` wandeln die Vorhersage mit
  `np.asarray(..., dtype=float)` um. Aus `None` wird so ein **0-dimensionales NaN-Array**, und das
  landet als `wrong_shape` im Record statt als `none`. So kam der `wrong_shape` im Rauchtest
  zustande.

## Was zu tun ist

1. **Timeouts im Handler zählen.** Die Zählung erfolgt in dem Moment, in dem der Alarm feuert,
   nicht beim Abfangen der Ausnahme. Dafür ersetzt der Adapter ODEFormers `timeout`-Dekorator
   (`odeformer/utils.py:147`) durch eine **semantisch identische** Nachbildung mit Zählhaken im
   Handler. Identisch heißt: gleiche Sekunden, gleiche Behandlung eines schon laufenden äußeren
   Timers (nicht überschreiten, Restzeit wiederherstellen), gleiches erneutes Scharfschalten im
   Handler, gleiche Ausnahmeklasse `MyTimeoutError` aus `odeformer.utils`. Die Zählung bleibt je
   Phase, wie in WP-N24. Die Ersetzung gilt auch im Modus `faithful` (1 s), und dort muss das
   Verhalten bitgleich zum ausgelieferten Dekorator sein. Das belegt Abnahme 1.
2. **Aufrufe klassifizieren.** Je Phase zählen, wie viele `_integrate_ode`-Aufrufe es gab und wie
   viele davon eine Trajektorie liefern, `None` liefern oder das NaN-Sentinel liefern. Zusätzlich
   zählen, wie viele `None`- bzw. Sentinel-Rückgaben mit einem gefeuerten Alarm im selben Aufruf
   zusammenfallen. Das ist die eigentliche Timeout-Zahl je Ausgang. Kein Zeitschwellen-Kriterium
   über die gemessene Dauer: Die Zuordnung erfolgt über den Handler, nicht über die Uhr.
3. **Ausgänge ehrlich benennen.**
   - `odeformer_timeout` umbenennen in einen Namen, der das Sentinel beschreibt und keine Ursache
     unterstellt, z. B. `odeformer_nan_sentinel`. Alle Stellen nachziehen: Wertemengen, Summary,
     Tests.
   - `None` bleibt beim Umwandeln in `integrate_expression` und `optimize_constants` `None`, damit
     `prediction_outcome` `none` meldet und nicht `wrong_shape`.
   - R²-Werte und die 0.0-Konvention ändern sich dadurch nicht. Test dafür.
4. **Wiederholbarkeitsskript** unverändert, bis auf die Nachführung der Feldnamen. Die
   Zusammenfassung pro Zelle zeigt zusätzlich min/max der Handler-Timeouts.

## Verboten

- Keine Git-Operationen.
- ODEFormer-Quellen nicht verändern, weder im Image noch unter `outputs/third_party/`. Nur
  Laufzeit-Ersetzung im Adapter.
- Nichts unter `analysis/data/` verändern.
- Die Zuordnung Timeout ↔ Ausgang **nicht** über eine Dauer-Schwelle lösen.

## Abnahme

1. **Äquivalenz des nachgebildeten Dekorators**, als Test ohne ODEFormer-Import (reine
   Signal-Logik) gegen ODEFormers Originalfunktion, falls sie importierbar ist, sonst gegen eine
   wörtliche Kopie im Test. Geprüft werden: Timeout feuert nach der eingestellten Zeit, ein äußerer
   kürzerer Timer wird nicht überschritten, die Restzeit wird wiederhergestellt, und ohne Timeout
   gibt es kein Scharfschalten danach.
2. Test mit einer Funktion, die **innerhalb** eines nackten `except` schläft, wie der
   `solve_ivp`-Zweig: Sie gibt `None` zurück, und der Handler-Zähler steht trotzdem auf 1. Das ist
   der Fall, den WP-N24 übersehen hat.
3. Test: `None` aus der Integration führt zu Ausgang `none`, nicht `wrong_shape`, und R² bleibt 0.0.
4. `python -m pytest baselines/tests -q` grün.
5. Report `codex/reports/REPORT_WP_N24c.md` mit der neuen Feldliste und dem Rauchtest-Befehl aus
   WP-N24b. Die Image-Namen dort sind falsch: richtig sind `evoode/odeformer-reference:wp-n21` und
   `evoode/odeformer-candidate:wp-n21`. Außerdem ist anzugeben, dass die Shard-Befehle **eines**
   Laufs **gleichzeitig** gestartet werden und nur die Läufe untereinander strikt nacheinander
   laufen.
