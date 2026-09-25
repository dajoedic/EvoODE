# WP-N27c — ODEFormers Konstantenoptimierung ins Image, und ein fehlendes Modul ist ein Abbruch
**Language: Python**

## Ausführung

Lokal umsetzbar. Kein Docker-Build, kein `oc`, kein Push; das macht Claude. Nur die betroffenen
Tests ausführen. Nichts, was länger als 15 Minuten läuft.

## Ausgangslage

Der Orion-Smoke mit dem CI-Image `odeformer-reference:3ca31bb` hat gezeigt:

- `beam10_noopt` ist bitgleich zum lokalen Lauf.
- `beam10_opt` endet mit `odeformer_optimization_error_type = ModuleNotFoundError`,
  `odeformer_optimization_error_message = "No module named 'param_optimizer'"`,
  `odeformer_optimization_status = error_unoptimized_expression_retained`, `nfev = 0`. Der Record
  sieht ansonsten gültig aus und trägt das **unoptimierte** R².

Ursache: `baselines/harness.py`, `ODEFormerAdapter.optimize_constants` (etwa Zeile 740) hängt
`REPO_ROOT / "outputs" / "third_party" / "odeformer"` an `sys.path` und importiert dann
`param_optimizer`. Dieser Ordner ist ein lokaler, gitignorierter Checkout des ODEFormer-Repos am
Commit `c9193012ad07a97186290b98d8290d1a177f4609`, also demselben Commit, den
`baselines/Dockerfile.odeformer-reference` per `pip install git+…@c919301…` installiert. Lokal
kommt er über das Einbinden von `outputs/` in den Container; im CI-Image fehlt er. Das per pip
installierte Paket enthält nur `odeformer/`, nicht die Dateien im Repo-Stamm. `param_optimizer.py`
(SHA-256 `5f73e0dff443bf7ab8d065a074c7279a30ceec53111456b72576d64f510e5328`) importiert zusätzlich
`from evaluate import *` aus dem Repo-Stamm.

Zwei Defekte also: Das Image ist unvollständig, und ein Infrastrukturfehler wird still in einen
gültig aussehenden Record verwandelt. Hätte der Smoke keine `_opt`-Konfiguration getroffen, wäre
die Hälfte des Referenzrasters unbemerkt ohne Konstantenoptimierung gerechnet worden.

## Was zu tun ist

1. **Dockerfile** (`baselines/Dockerfile.odeformer-reference`, und gleichartig
   `Dockerfile.odeformer-candidate`): Den ODEFormer-Quellbaum am **selben** gepinnten Commit ins
   Image legen, z. B. per `git clone` + `git checkout <commit>` nach `/opt/odeformer-src`.
   Anschließend beim Bau den SHA-256 von `param_optimizer.py` gegen den obigen Wert prüfen und bei
   Abweichung abbrechen, im selben Stil wie die Gewichtsprüfung. Den Pfad als
   `ENV ODEFORMER_SOURCE_ROOT=/opt/odeformer-src` setzen. Paketversionen, der pip-installierte
   ODEFormer und die Gewichte bleiben unverändert.
2. **harness.py:** Der Quellpfad kommt aus `ODEFORMER_SOURCE_ROOT`. Ist die Variable nicht
   gesetzt, gilt der bisherige Pfad `outputs/third_party/odeformer` (lokale Läufe bleiben
   bitgleich). Der Pfad, die Herkunft (env oder Default) und der SHA-256 von `param_optimizer.py`
   stehen in jedem Record.
3. **Kein stiller Rückfall bei Infrastrukturfehlern.** Kann `param_optimizer` (oder `evaluate`)
   nicht importiert werden, ist das ein **harter Abbruch des Laufs**, kein Record mit
   `error_unoptimized_expression_retained`. Dasselbe gilt für jeden anderen `ImportError` im
   Optimierungspfad. Wissenschaftliche Fehler der Optimierung (Nichtkonvergenz, Integrationsfehler,
   Ausnahmen aus `minimize`) bleiben wie bisher Records. Die Trennung steht im Docstring.
4. **Vorabprüfung beim Start** von `run_odeformer_grid.py` bzw. `run_odeformer_grid_k8s.py`:
   Enthält der Lauf eine `_opt`-Konfiguration, wird `param_optimizer` einmal importiert, bevor die
   erste Zelle rechnet. Ein Fehler bricht sofort ab, mit klarer Meldung. So scheitert ein
   unvollständiges Image in Sekunden statt nach Stunden.
5. `SCRIPTS.md`, Abschnitt "ODEFormer-Referenzraster auf Orion": Der Smoke muss mindestens eine
   `_opt`-Zelle enthalten, und seine Prüfung umfasst `odeformer_optimization_status`. Das kurz
   vermerken.

## Verboten

- Keine Git-Operationen.
- Keine Änderung an ODEFormers Verhalten, am Modus (`faithful`), an Records außer den neuen
  Herkunftsfeldern.
- `outputs/third_party/` nicht verändern.

## Abnahme

1. Tests: Mit gesetztem `ODEFORMER_SOURCE_ROOT` auf einen Ordner ohne `param_optimizer` bricht
   die Vorabprüfung ab. Ein simulierter `ImportError` im Optimierungspfad bricht ab und erzeugt
   keinen Record. Ein simulierter Optimierungsfehler anderer Art bleibt ein Record wie bisher. Ohne
   Variable wird der Default-Pfad benutzt.
2. `python -m pytest baselines/tests -q` für die betroffenen Dateien grün (Fork-Tests laufen unter
   Windows nicht; Claude führt sie im Linux-Container aus).
3. Report `codex/reports/REPORT_WP_N27c.md` mit dem lokalen Docker-Build-Befehl für Claude und der
   Prüfung, dass das gebaute Image `param_optimizer` importieren kann.
