> **Claude-Status:** `waiting for codex` — WP-C3 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Diese Datei schreibe nur ich.
> Committe nichts — das übernehme ich nach der Prüfung.

# WP-C3 — Der Cap darf nicht mehr behaupten, was die Ableitung nicht hergibt
**Language: Julia**

## Ausgangslage

WP-C2 (`docs/wp_c2_stage_cap_failure_diagnosis.md`, Commit `5d2f4f2`) hat bewiesen, dass die fünf
verbleibenden Abschneidefälle am Ableitungs-Input hängen: Mit exakten Ableitungen gehen alle fünf
auf die benötigte Stufe 3, und über ein 5×5-Raster von `tau_rel` und `tau_abs` liefert **keine
einzige von 25 Zellen** je den korrekten Cap. Schwellen sind damit als Ursache ausgeschlossen.

Die Ursachenformulierung im Report („Ableitungsfehler auf chaotischen Trajektorien") ist allerdings
zu grob: System 61 (Chen-Lee) ist ebenso chaotisch und wird korrekt gedeckelt. Aus
`stage_diagnostics.csv` ergibt sich der tatsächliche Mechanismus, und er zerfällt in **zwei
verschiedene Fälle**.

**Fall A — der Lauf hält bei der ersten Floor-Unterschreitung an, zu früh.**

| | Floor | Residuen Stufe 1→5 | erste Unterschreitung |
|---|---|---|---|
| 56 Lorenz Gl. 3 | 123 | 7793 → **66,1** → 2,61 → 2,61 → 2,61 | Stufe 2 — falsch |
| 61 Chen-Lee Gl. 3 (Kontrolle) | 44,6 | 1360 → 141 → **1,75** → 1,60 → 1,63 | Stufe 3 — richtig |
| 27 Gl. 1 (Kontrolle) | 0,254 | 152 → 148 → **0,0021** → … | Stufe 3 — richtig |

Bei allen Kontrollen fällt das Residuum erstmals auf der korrekten Stufe unter den Floor, und danach
ist es **flach**. Bei Lorenz fällt bereits Stufe 2 darunter, und Stufe 3 senkt es danach noch einmal
um **Faktor 25**. Diese Verbesserung wird nie betrachtet, weil `_cap_split_decision` bei der
Unterschreitung sofort zurückkehrt.

**Fall B — behauptet, wo nichts zu behaupten ist.** System 31 auf IC-Set 2: Floor 2,7e-37, Residuen
um 1e-16, Stufe 2 wird sogar schlechter als Stufe 1. Die Trajektorie trägt keine Dynamik. Der Cap
liefert dort 1. Richtig wäre `nothing` — das ist wörtlich die Regel aus dem System-63-Vorfall:
*der Cap muss auf positiver Evidenz ruhen, nie auf deren Abwesenheit.*

## Umfang

Dies ist die erste Aufgabe der Reihe, die **die Cap-Logik selbst** ändern darf und soll. In WP-C1
und WP-C2 war das gesperrt; die Sperre ist hiermit für die unten genannten Stellen aufgehoben.

### Teil 1 — Fall A: Die Floor-Unterschreitung beendet die Suche nicht mehr bedingungslos

Der Zweig in `_cap_split_decision`, der bei `residuals[stage] <= floors[stage]` zurückkehrt, darf
den Cap erst setzen, wenn feststeht, dass spätere Stufen das Residuum **nicht mehr erheblich
senken**. Senkt eine spätere Stufe es weiterhin deutlich, war der Floor für diese Gleichung zu hoch
angesetzt und die Unterschreitung ist kein Beleg für Ausreichen.

Was „erheblich" heißt, ist von dir zu entwerfen und im Report zu begründen. Anforderungen an das
Kriterium:

- Es darf **ausschließlich** Residuen, Floors und die bestehenden Policy-Schwellen verwenden. Keine
  Ground-Truth, keine Systemkennung, keine erwartete Stufe — die Zusicherung im Docstring von
  `estimate_stage_caps` gilt unverändert.
- Es muss **relativ** argumentieren, nicht absolut. Die Residuenskalen der geprüften Gleichungen
  liegen zwischen 1e-16 und 1e5; jede absolute Schranke wäre eine an diesen Datensatz angepasste
  Konstante.
- Es soll **möglichst keinen neuen freien Parameter** einführen. Führt es doch einen ein, ist im
  Report zu zeigen, über welchen Wertebereich das Ergebnis unverändert bleibt — sonst wird nur der
  getunte Horizont durch eine getunte Schwelle ersetzt.

Beobachtung als Ausgangspunkt, nicht als Vorgabe: In den Kontrollzeilen ist das Residuum nach der
Unterschreitung flach oder wird schlechter; in den Lorenz-Zeilen fällt es danach noch um mehr als
eine Größenordnung.

### Teil 2 — Fall B: Ablehnen statt behaupten

Ist die Anregung einer Gleichung so gering, dass die Stufenresiduen keine belastbare Unterscheidung
zulassen, muss `nothing` zurückgegeben werden statt eines Caps. Die Policy hat mit
`excitation_floor` bereits ein Feld für diesen Zweck; ob es dafür genügt oder ob die Erkennung
woanders greifen muss, ist Teil der Aufgabe.

Kennzeichen des Falls, aus den Daten: Die Residuen bewegen sich im Bereich der
Maschinengenauigkeit, die Stufenfolge ist **nicht monoton** (Stufe 2 schlechter als Stufe 1), und
der Floor liegt um Größenordnungen unter allen Residuen. Auch hier gilt: nur datenseitige Größen.

Wichtig ist die Richtung des Fehlers. Ein `nothing` kostet ausschließlich Rechenzeit — die Suche
läuft ungedeckelt — und niemals Korrektheit. Ein falscher Cap kostet die Lösung. Im Zweifel ist
abzulehnen. Rechenzeit ist nach dem Pilotbefund reichlich vorhanden.

### Teil 3 — Abnahme über das vollständige Audit

`studies/lookahead/audit_exact_stage_cap_horizons.jl` erneut laufen lassen und **zeilenweise** gegen
den heutigen Stand stellen. Zielbild:

| Zeilen | Soll |
|---|---|
| 55 Gl. 3 und 56 Gl. 3, beide IC-Sets (4 Zeilen) | Cap **3**, Klassifikation `ok` |
| 31 Gl. 1, IC-Set 2 (1 Zeile) | Cap **`nothing`**, Klassifikation `uncapped` |
| alle übrigen 75 Gleichungszeilen | **unverändert**, Cap-Wert für Cap-Wert |

Die dritte Zeile ist die eigentliche Hürde. Eine Änderung, die Lorenz repariert und dabei
irgendeinen der korrekten Caps verschiebt oder auf `nothing` setzt, ist **nicht** anzunehmen; dann
ist das im Report zu berichten statt es durchzudrücken.

Zusätzlich `studies/lookahead/diagnose_stage_cap_failures.jl` erneut laufen lassen, damit die
Diagnose den neuen Stand zeigt, und `config_fingerprint()` sowie `phase_b_fingerprint()` mit alten
und neuen Werten festhalten.

Testabdeckung in `test/test_stage_cap.jl` ergänzen: je ein Fall für die zu frühe
Floor-Unterschreitung und für die Ablehnung bei fehlender Anregung, beide auf synthetischen Daten
formuliert, nicht auf Systemkennungen.

## Verboten

- **Keine Kampagne, keine Discovery-Läufe, keine Cluster-Jobs**, weder starten noch Manifeste dafür
  erzeugen. Alles hier rechnet Ableitungsregressionen und ist Minutenarbeit.
- **`tau_rel`, `tau_abs`, `cond_cap`, `estimator`, `weighting` und `aggregation` behalten ihre
  Defaults.** WP-C2 hat gezeigt, dass die Schwellen die fünf Zeilen nicht erklären; sie jetzt doch
  zu bewegen, wäre Anpassung an das Ergebnis.
- **Keine Ground-Truth in `estimate_stage_caps` und keinerlei Sonderbehandlung einzelner Systeme.**
  Eine Lösung, die Lorenz namentlich kennt, ist keine.
- **Kein Zurückdrehen des Horizonts** und keine weiteren Änderungen an den Konstanten aus WP-C1/C2.
- **Kein `git add -A`.**

## Abnahme

- Zielbild aus Teil 3 zeilenweise erfüllt, oder begründet berichtet, dass es nicht erreichbar ist.
- Das Kriterium aus Teil 1 ist im Report beschrieben und begründet, inklusive seiner Parameter und
  deren Unempfindlichkeitsbereich, falls es welche hat.
- Die Ablehnung aus Teil 2 greift auf 31 / IC 2 und auf keiner der 75 unbeteiligten Zeilen.
- Neue Tests vorhanden, alte grün.
- Alte und neue Fingerprints im Report.
