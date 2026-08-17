# WP-C2 — Horizont bis ans Basisende ziehen und die fünf verbleibenden Abschneidefälle diagnostizieren
**Language: Julia**

## Ausgangslage

WP-C1 (`docs/wp_c1_stage_cap_horizon_audit.md`, Commit `d472f8e`) hat den Look-ahead-Horizont von 2
auf 3 gehoben. Damit landen die Caps der Systeme 28, 32 und 38 exakt auf der benötigten Stufe.
Zwei Dinge bleiben offen.

**Erstens** ist die 3 eine getunte Konstante. Die Audit-CSV zeigt, dass die Horizonte 3, 4 und 5 auf
**allen 80 Gleichungszeilen cap-identisch** sind — der Parameter ist oberhalb von 3 wirkungslos.
Dann soll er auch nicht als Stellschraube im Paper stehen.

**Zweitens** überleben fünf Gleichungszeilen jeden geprüften Horizont:

| System | Gleichung | IC-Set | benötigte Stufe | Cap |
|---|---|---|---|---|
| 55 Lorenz (komplex periodisch) | 3 | 1 und 2 | 3 | 2 |
| 56 Lorenz (Standardparameter) | 3 | 1 und 2 | 3 | 2 |
| 31 | 1 | nur 2 | 3 | 1 |

Das ist ein **zweiter, anderer Defekt**. Bei Lorenz liegt Stufe 3 von Stufe 2 aus schon bei Horizont
2 im Vorausblick — der Kreuzterm `u1*u2` wird also *gesehen* und trotzdem nicht als Gewinn gezählt.
Der Horizont ist hier nicht die Ursache.

## Umfang

Zwei Teile. Teil 1 ist eine Konstantenänderung, Teil 2 ist reine Diagnose **ohne** Codeänderung am
Produktivpfad.

### Teil 1 — Horizont auf das Basisende

`lookahead_horizon` von 3 auf **5** setzen, an denselben drei Stellen wie in WP-C1:

- `LookAheadStageCapPolicy` in `src/structure/stage_cap.jl`
- `LOOKAHEAD_CAP_POLICY` in `studies/regression/run_regression.jl`
- `LOOKAHEAD_CAP_POLICY_REGRESSION` in `studies/lookahead/measure_dataset_grid_caps.jl`

Die 5 ist **nicht** als getunter Wert zu verstehen, sondern als „so weit wie die gestaffelte
Polynombasis Stufen hat". Das ist im Docstring von `LookAheadStageCapPolicy` in einem Satz
festzuhalten, damit der Wert nicht später als freier Parameter missverstanden wird.

Daraus folgt eine Absicherung: Wird die Basis irgendwann um Stufen erweitert, wird aus der 5
stillschweigend wieder ein echter Horizont, und der Defekt aus WP-C1 kehrt unbemerkt zurück. Es ist
deshalb eine Prüfung zu ergänzen, die **laut fehlschlägt**, sobald `lookahead_horizon` kleiner ist
als die Stufenzahl der verwendeten Basis. Ort und Form wählst du; sie darf keine Cap-Werte ändern,
sondern nur eine unzulässige Konfiguration sichtbar machen.

**Abnahme von Teil 1:** Das Audit-Skript aus WP-C1
(`studies/lookahead/audit_exact_stage_cap_horizons.jl`) erneut laufen lassen und zeigen, dass die
Caps unter dem neuen Default **zeilenweise identisch** zu Horizont 3 sind — nicht nur in den
Zählwerten, sondern je (System, IC-Set, Gleichung). Danach `config_fingerprint()` und
`phase_b_fingerprint()` neu ausgeben, alte und neue Werte festhalten.

### Teil 2 — Diagnose der fünf Zeilen

Neues Diagnoseskript unter `studies/lookahead/`, Ausgabe nach
`outputs/studies/lookahead/<script_slug>/`.

Zielzeilen: 55 Gl. 3 (beide IC-Sets), 56 Gl. 3 (beide IC-Sets), 31 Gl. 1 (IC-Set 2).
**Kontrollzeilen, verpflichtend mitzuführen:** 61 Gl. 1–3 (Cap `[3,3,3]`, korrekt), 26 und 27 (Caps
korrekt), 31 Gl. 1 auf IC-Set **1** (dort korrekt). Ohne Kontrollen lässt sich nicht sagen, ob ein
auffälliger Wert der Defekt ist oder überall so aussieht.

Je Zeile und je Stufe protokollieren, was `_cap_split_decision` zur Entscheidung heranzieht:

- das Residuum der Stufe
- den zugehörigen Floor
- das Usability-Flag
- ob die Gewinnregel gegenüber der Vorstufe anschlägt, inklusive der beiden Größen, die sie
  vergleicht (absolute Differenz und relative Differenz gegen `tau_abs` und `tau_rel`)

Und je Zeile: **welcher Zweig die Entscheidung beendet hat** — der Floor-Zweig
(`residuals[stage] <= floors[stage]`), die erschöpfte Gewinnsuche über den Horizont, oder die
Usability-Prüfung. Das ist die eigentliche Frage von Teil 2. Es genügt, das aus den protokollierten
Größen nachvollziehbar herzuleiten; die Funktion selbst ist nicht umzubauen.

**Das entscheidende Experiment.** Zusätzlich dieselbe Cap-Schätzung einmal mit **analytisch exakten
Ableitungen** aus der wahren rechten Seite statt mit der geschätzten Ableitung rechnen, und die
resultierenden Caps gegenüberstellen.

- Wird der Cap auf 55 und 56 damit zu 3, liegt der Defekt in der **Ableitungsschätzung auf
  chaotischen Trajektorien** — derselbe Mechanismus, an dem v3 gescheitert ist (WP-L2).
- Bleibt er 2, liegt er in der **Gewinnregel oder ihren Schwellen**, unabhängig von der Ableitung.

Das ist ausdrücklich ein **Diagnoseinstrument und darf niemals in den Produktivpfad**: Es verletzt
die Regel aus dem Docstring von `estimate_stage_caps`, dass nur Trajektorie, Basis und Schwellen
gesehen werden dürfen. Es lebt ausschließlich im Studienskript, nie in `src/`, und geht in keine
Kampagnenkonfiguration ein.

**Schwellensensitivität, nur als Messung.** Zusätzlich berichten, wie sich die Caps der fünf Zeilen
unter Variation von `tau_rel` und `tau_abs` verhalten (je zwei Dekaden nach oben und unten). Das
dient dem Verständnis, ob die Entscheidung knapp oder deutlich ausfällt. **Die Defaults dieser
Schwellen sind in diesem Auftrag nicht zu ändern** — siehe Verboten.

**Abnahme von Teil 2:** Ein Report unter `docs/` beantwortet in dieser Reihenfolge:

1. Welcher Zweig beendet die Entscheidung auf 55 Gl. 3, 56 Gl. 3 und 31 Gl. 1 / IC 2?
2. Unterscheidet sich dieser Zweig von dem der Kontrollzeilen? Wenn nein, ist die Erklärung
   woanders zu suchen und das ist zu sagen.
3. Wie lautet der Cap mit exakten Ableitungen, je Zielzeile?
4. Welche der beiden oben genannten Ursachen ist damit belegt — oder ist es keine von beiden?

Eine Empfehlung, was zu tun ist, gehört in den Report. **Umgesetzt wird sie in diesem Auftrag
nicht.**

## Verboten

- **Keine Kampagne, keine Discovery-Läufe, keine Cluster-Jobs**, weder starten noch Manifeste dafür
  erzeugen. Beide Teile rechnen ausschließlich Ableitungsregressionen und sind Minutenarbeit. Sollte
  etwas über 15 Minuten laufen: abbrechen und berichten.
- **Die Cap-Logik nicht umbauen.** `_cap_split_decision`, `_cap_rule_counts_gain` und
  `_cap_aggregate_split_decisions` bleiben in Teil 2 unverändert. Teil 2 misst, es repariert nicht.
- **`tau_rel`, `tau_abs`, `cond_cap`, `excitation_floor`, `estimator`, `weighting` und `aggregation`
  behalten ihre Defaults.** Schwellen so lange zu verstellen, bis Lorenz durchgeht, wäre Anpassung
  an das Ergebnis und würde die Aussage des Papiers wertlos machen. Die Sensitivität wird berichtet,
  nicht ausgenutzt.
- **Keine Ground-Truth im Produktivpfad.** Die exakten Ableitungen aus dem entscheidenden Experiment
  bleiben im Studienskript.
- **Kein `git add -A`.** Nur die zu dieser Aufgabe gehörenden Dateien stagen.

## Abnahme insgesamt

- Default steht an allen drei Stellen auf 5, Docstring erklärt den Wert, Prüfung gegen zu kleine
  Horizonte vorhanden.
- Zeilenweise Cap-Identität zu Horizont 3 nachgewiesen, alte und neue Fingerprints im Report.
- Diagnose-CSV und Report liegen vor, Ziel- **und** Kontrollzeilen enthalten.
- Die vier Fragen aus Teil 2 sind mit Zahlen beantwortet.
