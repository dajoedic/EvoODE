# WP-N31 — ODEFormer-Paarung gegen C-1 (Claim D) und Stratifizierung nach der echten Dreiwege-Klasse
**Language: Python**

## Ausführung

Reines Python. Tests und die Neuberechnung laufen in der Sitzung, jeweils unter einer Minute.
Keine Git-Operationen, kein `oc`/`kubectl`, kein Julia, kein Docker, kein ODEFormer-Lauf.

## Ausgangslage

- **C-1** ist vollständig: Die Records liegen unter `outputs/phase_c_campaign_221a3a7/records/`, die
  Generalisierung (WP-N5, Phase C) unter `outputs/wp_n5_ic_generalization_phase_c/cells.csv`.
- **WP-N30** (`7173f7b`) paart SINDy gegen C-1 gleich gegen gleich: dasselbe System, dieselbe
  Trainings-IC, dieselbe Richtung, dasselbe Regime. Die EvoGrow-R²-Werte kommen aus `cells.csv`,
  Identität und Strukturtreffer aus den Records. Diese Logik ist die Vorlage.
- **ODEFormer-Referenz, kanonisch:**
  `analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records.csv`. Das sind
  1.512 Records = 63 Systeme × 2 Fit-ICs × 4 Konfigurationen (`beam10/50` × `opt/noopt`) × 3
  Wiederholungen. Je Record gibt es Rekonstruktion und Generalisierung
  (`reconstruction_r2_arithmetic_mean`, `generalization_r2_arithmetic_mean`, dazu die
  `_variance_weighted`-Varianten und die `_gt_0_9`-Flags), außerdem `structure_hit_raw`,
  `structure_hit_pruned`, `fit_initial_condition_set`, `generalization_initial_condition_set` und
  `timeout_enforced`. ODEFormer ist nicht deterministisch (Wall-Clock-Timeout, DIARY 24./25.09.);
  deshalb gibt es 3 Wiederholungen.
- **Die echte Dreiwege-Klasse für Phase C** liegt jetzt unter
  `analysis/data/paper1_phaseC_v1/representability_threeway/representability_threeway_by_system.csv`,
  Zeilen mit `basis_name == staged_polynomial_basis_with_constant`. Die Klassen sind
  `fully_representable` (30), `partially_representable` (31) und `non_representable` (2), und sie
  stimmen 30/30 bzw. 33/33 mit `studies/regression/phase_c_support.json` überein. Die
  SINDy-Zusammenfassung von WP-N30 stratifiziert dagegen noch nach
  `phasec_representability_threeway` aus `details.csv` (`exact` / `surrogate:eqK_not_representable`).
  Das ist **nicht** die Dreiwege-Klasse, sondern nur die erste nicht repräsentierbare Gleichung.

## Was zu tun ist

1. **ODEFormer-Paarung gegen C-1**, entweder als eigener Unterbefehl oder als eigenes Skript neben
   `run_phasec_sindy_baseline.py`; die gemeinsame EvoGrow-Seite wird wiederverwendet, nicht
   kopiert. Die Paarungseinheit ist (Konfiguration, System, Richtung, Regime), mit Richtung =
   Fit-IC → Generalisierungs-IC, wie in WP-N30. Auf beiden Seiten gilt dieselbe Trainings-IC und
   dasselbe Regime.
2. **Wiederholungen und Seeds werden je Seite deklariert:** ODEFormer als Mittelwert der Raten über
   die 3 Wiederholungen, EvoGrow wie in WP-N30 als Mittelwert über die Seeds. Beides steht als
   Policy-Spalte in der Tabelle. Zusätzlich je Einheit die Streuung über die Wiederholungen: die
   Zahl der Wiederholungen, in denen das R² > 0,9-Urteil kippt.
3. **Kanonische R²-Definition:** das arithmetische Mittel über die Zustände (`_arithmetic_mean`),
   wie in der EvoGrow-Auswertung. Die `_variance_weighted`-Rate steht als Sensitivitätsspalte
   daneben und ersetzt die kanonische nicht. Falls die EvoGrow-Seite eine andere Mittelung nutzt
   als das arithmetische Mittel, steht das im Report und wird **nicht** stillschweigend angeglichen.
4. **Ungültige Fälle:** Fehler, Nicht-Erfolgs-Status, fehlendes R² und `timeout_enforced` bleiben
   in der Tabelle und sind markiert. Sie zählen als „nicht R² > 0,9“. Die Zusammenfassung zeigt die
   Rate über alle Einheiten und über die gültigen sowie die Zahl der Timeouts.
5. **Stratifizierung nach der echten Dreiwege-Klasse, für ODEFormer und für SINDy:** Beide
   Zusammenfassungen gruppieren nach (Dimension, Dreiwege-Klasse aus der Datei oben). Für SINDy
   wird die neue Spalte ergänzt; die alte Spalte `phasec_representability_threeway` bleibt stehen,
   bekommt im Report aber den Hinweis, dass sie nicht die Dreiwege-Klasse ist. Die Paarungslogik
   von WP-N30 bleibt unverändert. Ein System ohne Klasse bricht laut ab.
6. **Kostenachse:** Neben jede ODEFormer-Qualitätszeile kommen die Strahlbreite und der Median von
   `odeformer_candidates_evaluated`, dazu der Hinweis, ob die Konstantenoptimierung aktiv ist.
   Keine Zeiten; `elapsed_s_non_evidence` bleibt draußen.
7. **Strukturtreffer:** ODEFormer `structure_hit_raw` / `_pruned` neben EvoGrow roh / gepruned,
   nur auf `fully_representable`-Systemen als Rate ausgewiesen, auf den übrigen als nicht
   anwendbar.
8. **Neuberechnung** auf den echten Daten, ohne `--allow-incomplete`:
   - ODEFormer nach `outputs/phase_c_campaign_221a3a7/agg/odeformer_n31/`
   - SINDy (nur neu stratifiziert) nach `outputs/phase_c_campaign_221a3a7/agg/sindy_n31/`
9. `SCRIPTS.md`, Abschnitt „Campaign bridge and C-5 evaluation for Phase-C data“: Den
   ODEFormer-Aufruf **und** den Aufruf von `aggregate_representability_threeway.py` mit den
   Phase-B-Eingaben (`--classification analysis/data/paper1_phaseB_v1/system_classification.csv
   --adequacy analysis/data/paper1_phaseB_v1/representational_adequacy.csv --output-dir
   analysis/data/paper1_phaseC_v1/representability_threeway`) an der Stelle der Zeile „Three-way
   representability: NOT available …“ eintragen, mit einem Satz, warum die Phase-B-Eingaben
   richtig sind (symbolische Terme je Gleichung, die Konstanten-Regel steckt im Skript).

## Verboten

- Keine Änderung an den ODEFormer-Records, an `details.csv`, an `cells.csv`, an `src/`, an
  `wp_n5_ic_generalization.jl`, an den R²-Schwellen oder der Pruning-Regel.
- Keine Änderung an der Paarungslogik von WP-N30. Hinzu kommt nur die neue Schichtspalte.
- Keine Konfiguration auswählen oder weglassen, keine Kennzahl über die Schichten hinweg und keine
  Kandidaten-Umgebung (`candidate*`); kanonisch ist nur `reference_orion_55e9c75`.
- Die Referenzwerte unten sind eine Gegenprobe, **kein Ziel**. Abweichungen werden erklärt und nicht
  wegkalibriert.

## Abnahme

1. **Tests:**
   - eine Fixture, in der beide Seiten einer Einheit dieselbe Trainings-IC und dasselbe Regime
     haben;
   - eine fehlende ODEFormer-Wiederholung bricht laut ab;
   - ein System ohne Dreiwege-Klasse bricht laut ab;
   - Timeout- und Fehlerzeilen zählen als nicht bestanden und sind markiert.

   Alle Tests unter `analysis/tests/` bleiben grün, bis auf den schon vorher fehlschlagenden
   `test_phase_a_evaluation_does_not_overwrite_frozen_artifacts`.
2. **Gegenprobe gegen Claudes ad-hoc-Rechnung.** ODEFormer-Rate R² > 0,9 (arithmetisches Mittel),
   gemittelt über die Wiederholungen je (System, Fit-IC), dann über die 126 Einheiten:

   | Konfiguration | Rekonstruktion | Generalisierung |
   |---|---|---|
   | beam10_noopt | 0,577 | 0,262 |
   | beam10_opt | 0,728 | 0,310 |
   | beam50_noopt | 0,648 | 0,278 |
   | beam50_opt | 0,775 | 0,323 |

   Nach Dimension, Generalisierung, beam50_opt: dim 1 0,587, dim 2 0,244, dim 3 0,000, dim 4 0,000.
   Der Report rechnet diese Werte aus der neuen Ausgabe nach und erklärt jede Abweichung.
3. Report `codex/reports/REPORT_WP_N31.md` mit der ODEFormer-Tabelle je (Dimension, Dreiwege-Klasse,
   Regime) neben EvoGrow, der neu stratifizierten SINDy-Tabelle, den Testergebnissen aus diesem Lauf
   und der Gegenprobe.
4. `codex/STATUS.md`: `status: done`, `task: WP-N31`, Report-Pfad.
