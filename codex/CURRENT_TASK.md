# WP-N26 — Die Claim-A-Auswertung für Phase C korrekt machen
**Language: Python**

## Ausführung

Lokal umsetzbar und testbar. **Wichtig: Auf dem Laptop läuft zeitgleich eine lastempfindliche
ODEFormer-Messung.** Deshalb nur die neuen und geänderten Tests gezielt ausführen, nicht die ganze
Suite, und nichts, was länger als 5 Minuten rechnet. Permutationstests und Bootstraps nicht starten.

## Ausgangslage

Eine Generalprobe der Phase-C-Auswertung lief am 2026-09-25 auf 885 von 936 Records (lokale Kopie
unter `outputs/phase_c_dryrun_2026-09-25/`: `tasks/`, `history.jsonl`, `run_registry.csv`). Registry
und Invarianten sind sauber. Die Strukturauswertung für Claim A hat dagegen vier Defekte.

1. **Keine Phase-C-Wahrheit.** `analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py`
   liest die wahre Struktur aus `matched_basis_terms` in `system_classification.csv`
   (`load_truth`). Für `--campaign paper1_phaseC_v1` wird dort
   `analysis/data/paper1_phaseC_v1/system_classification.csv` gesucht, und diese Datei existiert
   nicht. Die einzige Klassifikation (`analysis/data/paper1_phaseB_v1/system_classification.csv`)
   stammt von `classify_odebench_systems.py` und damit von der **alten Basis ohne Konstante**. Bei
   System 1 steht dort als Wahrheit nur `u1`, und die Konstante gilt als Lücke `constant_offset`.
   Mit dieser Datei würden die zehn Systeme, die unter der kanonischen Basis exakt sind (1, 5, 9,
   17, 23, 43, 52, 57, 58, 59), **stillschweigend** gegen eine falsche Wahrheit bewertet. Die
   Phase-C-Wahrheit steht in `studies/regression/phase_c_support.json`: pro System
   `representability`, `dim`, `support_terms` pro Gleichung, `basis_name =
   staged_polynomial_basis_with_constant`, 30 exakt und 33 Surrogat. Diese Datei ist auch die
   Wahrheit, gegen die die Kampagne selbst `exact_support_match_*` berechnet.
2. **Koeffizientenfehler nie berechnet.** Im selben Skript stehen
   `coefficient_relative_error_mean`, `coefficient_relative_error_max` und `n_coefficient_terms` fest
   auf `None`/`0` (etwa Zeilen 148–150 und 173–175). `analysis/utils/metrics.py` hat eine Funktion
   `coefficient_metrics(found_coefficients, true_coefficients)`, die nie aufgerufen wird.
   Phase-C-Records tragen die gefundenen Koeffizienten in `model_terms` (pro Gleichung eine Liste
   von `{term, term_index, coefficient}`); in der Registry landen sie als JSON-Spalte `model_terms`.
   Die wahren Koeffizienten stehen in der Spalte `equation` der Klassifikation (ODEBench-Ausdrücke
   mit eingesetzten Parametern, Variablen `x_0, x_1, …`, Zuordnung `x_i -> u{i+1}` in
   `variable_mapping`). `classify_odebench_systems.py` zerlegt diese Ausdrücke bereits mit sympy in
   Terme.
3. **Falscher Abgleich mit der Registry.** Das Skript vergleicht seinen **rohen** Treffer mit
   `exact_support_match` der Registry. In Phase C trägt diese Spalte den **gepruneten** Treffer
   (`exact_support_match_definition = pruned_support_terms_exact_match`). Ergebnis: 80 gemeldete
   Abweichungen, alle mit null fehlenden wahren Termen und mindestens einem überzähligen Term, also
   roh `False` gegen gepruned `True`. Das sind keine Datenfehler, sondern der in
   `docs/paper1_phaseC_benchmark_plan.md` §4b beschriebene Zustand "ein Spaltenname, zwei
   Definitionen". Phase-C-Registries haben dafür die Spalten `exact_support_match_raw`,
   `exact_support_match_pruned`, `exact_support_match_definition` und `pruned_support_terms`.
4. **`merge_batch_records.jl` nimmt Heartbeat-Zeilen an.** Liegen Heartbeat-Dateien im
   Eingabeordner, übernimmt das Skript deren Zeilen ohne Fehler als Records. In der Generalprobe sind
   so 8 Zeilen in die History geraten. `SCRIPTS.md` warnt davor, das Skript selbst prüft es nicht.
   Das ist Julia; siehe Punkt 4 unten, der Teil wird nur geschrieben.

## Was zu tun ist

1. **Phase-C-Wahrheit.** Ein neues Skript unter `analysis/scripts/aggregate/` erzeugt aus
   `studies/regression/phase_c_support.json` und den ODEBench-Ausdrücken
   `analysis/data/paper1_phaseC_v1/system_classification.csv`, und zwar im **Spaltenschema der
   Phase-B-Datei**, damit alle Konsumenten sie lesen können. Dabei gilt:
   - `representability` und `matched_basis_terms` kommen ausschließlich aus der Support-Tabelle.
     Für exakte Systeme ist `matched_basis_terms` die Support-Termliste, mit `|` verbunden, in
     Basis-Termnamen (`1`, `u1`, `u1^2`, `u1*u2`, …).
   - Die übrigen Spalten (`description`, `equation`, `variable_mapping`, `source` usw.) werden aus
     der Phase-B-Datei übernommen. `unmatched_terms` und `gap_reason` werden für die kanonische
     Basis neu bestimmt, also mit der Konstante als Basisterm. Wo das nicht sauber geht, bleibt die
     Spalte leer, und die Lücke wird im Report benannt.
   - `expected_stage` / `expected_eq_stage` wie in `phase_c_config.jl`
     (`phase_c_expected_stage_from_support`). Die Regel wird in Python nachgebildet und per Test
     gegen die Werte geprüft, die die Records in `expected_stage` tragen.
   - **Abbruch**, wenn die erzeugte Wahrheit für ein exaktes System nicht mit der Support-Tabelle
     übereinstimmt, oder wenn die Zahl exakter Systeme nicht 30 ist.
   - Die Datei gehört unter `analysis/data/paper1_phaseC_v1/`. Sie darf nur **dieses** Skript
     schreiben, und nur diese eine Datei dort.
2. **Kein stiller Rückfall.** `aggregate_phaseb_structure_metrics.py` bricht für
   `--campaign paper1_phaseC_v1` ab, wenn die übergebene Klassifikation nicht zur Basis der Registry
   passt. Prüfkriterium: `basis_name` der Registry-Zeilen gegen eine Basis-Kennung, die das Skript
   aus Punkt 1 in die Klassifikation schreibt (neue Spalte `basis_name`). Fehlt die Spalte, ist das
   ein Abbruch, kein Default.
3. **Koeffizientenfehler berechnen**, über das vorhandene `coefficient_metrics`. Gefundene
   Koeffizienten aus `model_terms`, wahre aus `equation` über die Variablenzuordnung. Nur für exakte
   Systeme; für Surrogate bleiben die Felder leer. Welche Definition gilt (relativ pro Term, über
   die **wahren** Terme; nicht gefundene wahre Terme zählen mit gefundenem Koeffizienten 0), steht
   im Report und im Docstring. Zur Kontrolle: Ein Test mit einem handgebauten Record für System 1
   (`0.30303 - 0.36075*x_0`) liefert den erwarteten Fehler.
4. **Registry-Abgleich nach Definition.** Liegt `exact_support_match_definition` vor, wird der
   rohe Treffer gegen `exact_support_match_raw` und der gepruned-Treffer gegen
   `exact_support_match_pruned` abgeglichen (gepruned aus `pruned_support_terms`). Beide Abgleiche
   erscheinen getrennt in der Ausgabe. Ohne die Spalte (Phase B) bleibt das Verhalten **bitgleich**
   wie bisher.
5. **Heartbeat-Schutz in `studies/regression/merge_batch_records.jl`** (nur schreiben, Julia wird
   von Claude ausgeführt): Eine Zeile mit Feld `event` oder ohne `git_hash`/`loss` ist ein Abbruch
   mit Datei und Zeilennummer, kein Überspringen. Der Abbruch passiert, bevor irgendetwas in die
   History geschrieben wird.
6. **Ausgabenamen.** Die Ausgaben heißen für Phase C noch `phaseb_structure_metrics_by_*.csv`. Für
   `--campaign paper1_phaseC_v1` sollen sie `phasec_structure_metrics_by_cell.csv` /
   `..._by_equation.csv` heißen, wie im Plan §1b vorgesehen. Die Phase-B-Namen bleiben unverändert.
7. `SCRIPTS.md`: Die Phase-C-Kette (von WP-N25 ergänzt) um den Schritt aus Punkt 1 erweitern,
   **vor** den Strukturmetriken, mit der Ausführungsreihenfolge.

## Verboten

- Keine Git-Operationen.
- Nichts unter `analysis/data/paper1_phaseB_v1/` und `experiments/` ändern. Phase-B-Ausgaben
  müssen bitgleich bleiben.
- Keine Pruning-Schwelle anfassen oder neu wählen.
- `studies/regression/phase_c_config.jl`, `run_regression.jl`, `src/`: nicht ändern. Die Kampagne
  läuft noch.
- Keine Permutations- oder Bootstrap-Läufe, keine vollständige Testsuite (siehe Ausführung).

## Abnahme

1. Neue Tests für die Punkte 1–4 und 6 grün. Nur die neuen bzw. betroffenen Testdateien ausführen.
2. **Phase-B-Bitgleichheit:** `aggregate_phaseb_structure_metrics.py` mit den Phase-B-Defaults
   erzeugt vor und nach der Änderung byte-identische Ausgaben. Den Befehl in den Report schreiben;
   ausführen nur, wenn er unter 5 Minuten läuft, sonst als offen melden.
3. Das Skript aus Punkt 1 läuft und erzeugt die Phase-C-Klassifikation mit 30 exakten Systemen.
   Ein Test prüft die zehn neu exakten Systeme einzeln: Ihre Wahrheit enthält den Term `1`.
4. Auf `outputs/phase_c_dryrun_2026-09-25/run_registry.csv` mit der neuen Klassifikation: 0
   Abweichungen im gepruned-Abgleich, und der Koeffizientenfehler ist für jede exakte Zelle gesetzt.
   Ausgabe nach `outputs/phase_c_dryrun_2026-09-25/agg/structure_n26/`, **nicht** nach
   `analysis/`. Zahlen daraus sind Probe und werden nicht zitiert.
5. Report `codex/reports/REPORT_WP_N26.md`: geänderte Dateien, Koeffizientenfehler-Definition,
   Befehle, was nicht verifiziert wurde. Der Julia-Teil (Punkt 5) ist immer "nicht verifiziert".
