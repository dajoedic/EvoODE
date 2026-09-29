# WP-N30 — SINDy-Paarung (Claim D): gleiche Anfangsbedingung, gleiches Regime auf beiden Seiten
**Language: Python**

## Ausführung

Reines Python. Tests und die Neuberechnung (unten) laufen in der Sitzung, jeweils unter einer
Minute. Keine Git-Operationen, kein `oc`/`kubectl`, kein Julia.

## Ausgangslage

C-1/C-2 ist vollständig (756/756). Die Records liegen lokal unter
`outputs/phase_c_campaign_221a3a7/records/`, die zusammengeführte Historie unter
`outputs/phase_c_campaign_221a3a7/history.jsonl`. Die Generalisierung von C-1 (WP-N5, Phase C)
ist gerechnet: `outputs/wp_n5_ic_generalization_phase_c/cells.csv`, 378 Zellen, eine je (System,
Seed, Trainings-IC). Die Rekonstruktionskontrolle ist in 378 von 378 Zellen exakt.

**Der Defekt.** `pair_sindy_evogrow` in `analysis/scripts/aggregate/run_phasec_sindy_baseline.py`
vergleicht zwei verschiedene Größen und paart dabei über die falsche Anfangsbedingung:

1. Auf der SINDy-Seite behält `valid_sindy_for_pairing` nur `regime == "generalization"`, also das
   R² auf der **ungesehenen** Anfangsbedingung.
2. Auf der EvoGrow-Seite ist `r2` das Feld aus dem Record, also die **Rekonstruktion** auf der
   Trainingstrajektorie.
3. Verbunden wird über `initial_condition_set`. Die SINDy-Generalisierungszeilen tragen dort die
   **Ziel**-IC (`target_initial_condition_set`), die EvoGrow-Records die **Trainings**-IC. Damit
   steht ein SINDy-Modell, das auf IC 1 trainiert und auf IC 2 bewertet wurde, neben einem
   EvoGrow-Modell, das auf IC 2 trainiert und auf IC 2 bewertet wurde. Dasselbe gilt für die
   Strukturtreffer: Sie stammen von Modellen, die auf verschiedenen Trajektorien trainiert wurden.

Das Ergebnis verzerrt systematisch zugunsten von EvoGrow. Nach einer unabhängigen ad-hoc-Rechnung
von Claude: Die Pipeline stellt auf dim 2 eine EvoGrow-R²-Rate um 0,9 neben SINDy-Raten von
0,1–0,5. Gleich gegen gleich liegt EvoGrow bei der Generalisierung auf dim 2 bei **0,256**.

## Was zu tun ist

1. **Paarungseinheit** ist (Bibliothek, System, Richtung, Regime). Richtung heißt Trainings-IC →
   Ziel-IC (`IC1_to_IC2`, `IC2_to_IC1`), Regime ist `reconstruction` oder `generalization`. Beide
   Seiten stehen in jeder Einheit **auf derselben Trainings-IC und im selben Regime**. SINDy liefert
   je Einheit eine Zeile, EvoGrow drei Seeds. Der Umgang mit den Seeds bleibt der bisherige
   (Mittelwert der Raten über die vorhandenen Seeds) und bleibt als Spalte deklariert.
2. **Die R²-Werte von EvoGrow kommen aus `cells.csv` von WP-N5**: `reconstruction_r2` und
   `generalization_r2`, verbunden über (System, Seed, Trainings-IC) bzw. `direction`. Neues
   Pflichtargument, z. B. `--evogrow-generalization <cells.csv>`. Die Records bleiben die Quelle für
   die Identität (git, Fingerprint, Behaviour) und für die Strukturtreffer roh und gepruned.
   **Abgleich, der laut abbricht:** `reconstruction_r2` aus `cells.csv` muss je Zelle mit `r2` aus
   dem Record übereinstimmen (Toleranz als benannte Konstante mit Kommentar). Außerdem müssen die
   Records und `cells.csv` dieselben 378 Zellen abdecken.
3. **Strukturtreffer:** Der SINDy-Treffer (aus der Rekonstruktionszeile, also dem Modell der
   Trainings-IC) steht neben dem EvoGrow-Treffer derselben Trainings-IC. Die Treffer hängen nicht
   vom Regime ab; sie stehen in der Tabelle je Richtung einmal, nicht doppelt.
4. **Ungültige und divergierte Fälle:** SINDy-Zeilen mit `valid_for_analysis == False` und
   EvoGrow-Zellen mit `generalization_diverged_or_nonfinite` bzw. ohne R² bleiben in der Tabelle,
   sind markiert und zählen als „nicht R² > 0,9“. Die Zusammenfassung zeigt für beide Seiten zwei
   Raten: über alle Einheiten und über die gültigen, dazu die Zahl der ungültigen bzw. divergierten
   Einheiten. Das entspricht `metric_summary.csv` von WP-N5.
5. **Zusammenfassung:** eine Zeile je (Bibliothek, Richtung, Regime, Dimension, Dreiwege-Klasse),
   mit Spaltennamen, die das Regime tragen, z. B. `sindy_generalization_r2_gt_0_9_rate`. Alle zehn
   Bibliotheken, keine ausgewählt, keine Kennzahl über die Schichten hinweg. Die Dreiwege-Spalte
   bleibt `phasec_representability_threeway` wie bisher (ihre Überarbeitung ist ein eigenes Paket).
6. **Kostenachse:** Neben jede Qualitätszeile den Median von `n_target_regressions` (SINDy) sowie
   `total_parameter_fits` und `total_loss_evals` (EvoGrow). Keine Zeiten.
7. **Neuberechnung** auf den echten Daten, Ausgabe nach
   `outputs/phase_c_campaign_221a3a7/agg/sindy_n30/` (gepaarte Tabelle und Zusammenfassung). Die
   Eingaben sind `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv`, die Records
   unter `outputs/phase_c_campaign_221a3a7/records/` und `cells.csv` von oben. Ohne
   `--allow-incomplete`: C-1 ist vollständig.
8. `SCRIPTS.md`, Abschnitt „Campaign bridge and C-5 evaluation for Phase-C data“: Den
   Pair-Aufruf auf die neue Signatur bringen, dazu ein Satz, was gepaart wird.

## Verboten

- Keine Änderung an den SINDy-Fits, an `details.csv`, am `fit`-Unterbefehl, an
  `wp_n5_ic_generalization.jl`, an `src/` oder an Schwellen (R² 0,9, Pruning-Regel).
- Keine Bibliothek auswählen oder weglassen. Keine Kennzahl über die Schichten hinweg.
- Die bisherige Ausgabe `analysis/data/paper1_phaseC_v1/phasec_sindy_paired.csv` nicht
  überschreiben. Die Neuberechnung geht nur nach `outputs/…/sindy_n30/`.
- Die Referenzwerte unten sind eine Gegenprobe, **kein Ziel**. Weicht die Implementierung ab, wird
  die Abweichung im Report erklärt und nicht durch Umbauen wegkalibriert.

## Abnahme

1. **Test mit einer Fixture**, auf der die alte Paarung nachweislich falsch paart. Er prüft: Beide
   Seiten einer Einheit haben dieselbe Trainings-IC und dasselbe Regime; ein SINDy-Generalisierungswert
   steht nie neben einem EvoGrow-Rekonstruktionswert. Dazu ein Test, dass ein Widerspruch zwischen
   `reconstruction_r2` und Record-`r2` laut abbricht, und einer, dass eine fehlende Zelle in
   `cells.csv` laut abbricht. Alle bestehenden Tests unter `analysis/tests/` bleiben grün.
2. **Gegenprobe gegen Claudes ad-hoc-Rechnung** (126 Einheiten aus System und Richtung, EvoGrow als
   Mittelwert über die Seeds, ungültig = nicht bestanden, Rate über alle Einheiten):

   | dim | Einheiten | EvoGrow Rekonstr. | EvoGrow Generalis. | SINDy Rekonstr. min–max | SINDy Generalis. min–max |
   |---|---|---|---|---|---|
   | 1 | 46 | 0,978 | 0,703 | 0,674–0,957 | 0,457–0,609 |
   | 2 | 56 | 0,917 | 0,256 | 0,554–0,732 | 0,214–0,464 |
   | 3 | 20 | 0,283 | 0,017 | 0,000–0,150 | 0,000–0,100 |
   | 4 | 4 | 0,417 | 0,000 | 0,000–0,500 | 0,000–0,000 |

   Min und Max laufen über die zehn Bibliotheken und sind über beide Richtungen gepoolt. Der Report
   zeigt dieselbe Tabelle aus der neuen Ausgabe nachgerechnet, dazu jede Abweichung und ihre
   Ursache.
3. Report `codex/reports/REPORT_WP_N30.md`: der Defekt in zwei Sätzen, die neue Signatur, die
   Testergebnisse aus diesem Lauf und die Tabelle aus Punkt 2.
4. `codex/STATUS.md`: `status: done`, `task: WP-N30`, Report-Pfad.
