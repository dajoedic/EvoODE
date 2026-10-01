# WP-N34 — SINDy und Weak-SINDy auf den exportierten Rausch-Daten (C-6, gestuft)
**Language: Python**

Spezifikation: `docs/paper1_phaseC_benchmark_plan.md` §9.3 und §9.4, besonders „One data set for
all methods“, „Evaluation targets are clean“ und „Each method treats an irregular grid with its own
documented default; we do not interpolate“. Backlog: `CLAUDE.md`, R-09.

## Ziel

Die SINDy-Baseline aus C-4 (`analysis/scripts/aggregate/run_phasec_sindy_baseline.py`, zehn
Konfigurationen, alle berichtet) läuft auf **denselben verfälschten Daten**, die EvoGrow sieht.
Dazu kommt **Weak-SINDy** als rauschspezifische SINDy-Referenz. Ausgewertet wird gegen die saubere
Wahrheit, genau wie bei EvoGrow (WP-N33a).

## Umsetzung

1. **Eingabe:** der Exportindex von `studies/regression/export_phase_c_data_conditions.jl`
   (gequotetes CSV, Hashes je Zelle). Jede Zelle wird über die Binärdateien gelesen, und vor der
   Verwendung wird der Hash geprüft. Bei Abweichung bricht das Skript ab. Beispiel:
   `outputs/stage1/data_export/index.csv` (System 1, vier Bedingungen).
2. **SINDy:** die bestehenden zehn Konfigurationen **unverändert**, auf den verfälschten `(t, x)`.
   Liegt ein unregelmäßiges Raster vor, bekommt SINDy die echten Zeitpunkte, also die
   Zeitvektor-Schnittstelle von pysindy, so wie es pysindy dokumentiert. Wir interpolieren nicht.
3. **Weak-SINDy:** pysindys schwache Formulierung mit ihren dokumentierten Standardwerten, über
   denselben Bibliotheken wie die SINDy-Konfigurationen, soweit sinnvoll. Jede Konfiguration wird
   berichtet, keine wird nachträglich ausgewählt. Kann die schwache Formulierung mit unregelmäßigen
   Rastern nicht umgehen, wird die Zelle als **Fehler mit Grund** festgehalten. Nichts wird
   repariert oder interpoliert. Halte im Report fest, was die pysindy-Version dazu sagt, und zwar
   gelesen in Quelle oder Doku, nicht vermutet. Das Modell, das Weak-SINDy liefert, wird wie bei
   SINDy als ODE integriert.
4. **Auswertung gegen die saubere Wahrheit:** Rekonstruktion aus der sauberen
   Trainings-Anfangsbedingung auf dem vollen sauberen Raster, Generalisierung aus der sauberen
   anderen Anfangsbedingung. R² in beiden Aggregationen (§6b), Divergenz markiert. Dazu
   Strukturmetriken (roh, gepruned, F1) nur auf exakten Systemen, mit derselben Pruning-Regel und
   derselben Term-Zuordnung wie in C-4. Saubere Trajektorien und R²-Definition werden aus dem
   bestehenden Pfad wiederverwendet (C-4 bzw. `phase_c_trajectory_hashes`), nicht neu gebaut.
5. **Ausgabe:** eine Zeile je Zelle × Methode × Konfiguration mit Schlüssel (System, IC-Set,
   `noise_sigma`, `subsample_rho`, `noise_realization`), Datenhash, Kennzahlen und Fehlergrund. Eine
   Vergleichstabelle neben dem Tor-Bericht (`robustness_stage_report.py`): je Zelle EvoGrow gegen
   alle Baseline-Konfigurationen, ohne Auswahl und ohne Urteil. Eigener Ausgabeordner unter
   `outputs/`.
6. **Kontrolle:** Auf C-1-Daten bei (0, 0) muss der neue Pfad die vorhandenen C-4-Ergebnisse der
   zehn SINDy-Konfigurationen exakt reproduzieren, für mindestens System 1 und 24. Die Daten dafür
   erzeugst du über den Export bei (0, 0), sofern er das kann; sonst sag, warum nicht.

## Verboten

SINDy-Konfigurationen ändern, auswählen oder neu tunen. Für Weak-SINDy keine Parameter auf
Ergebnisse hin wählen. Interpolation. Julia-, Methoden- oder Kampagnencode ändern. Git,
`codex/CURRENT_TASK.md` bearbeiten, `docs/` ändern, Läufe über 15 Minuten.

## Abnahme

1. Läuft **in deiner Sitzung** auf `outputs/stage1/data_export/index.csv` (System 1, alle vier
   Bedingungen) durch. Jede Konfiguration erscheint, Fehler mit Grund.
2. Die Kontrolle aus Punkt 6 ist bestanden, oder der Report sagt genau, woran sie scheitert.
3. Tests mit Fixtures aus den echten Exportdateien, grün in deiner Sitzung.
4. Der Report nennt die pysindy-Version, die Weak-SINDy-Konfigurationen und ihre Quelle, und die
   Zahlen für System 1 als Tabelle, ohne Bewertung.
5. Report `codex/reports/REPORT_WP_N34.md`, `STATUS.md` nach Protokoll.
