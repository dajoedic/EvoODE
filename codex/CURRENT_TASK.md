# WP-N28 — Die Phase-C-Auswertungskette schließen: Registry mit Metriken, Arm-Filter, Cap-Ablation, SINDy-Paarung, Pretuning-Collapse
**Language: Python**

## Ausführung

Lokal umsetzbar. Nur die betroffenen Tests ausführen. Permutationen und Bootstraps in Tests klein
halten. Keine Git-Operationen. Nichts, was länger als 15 Minuten läuft.

## Ausgangslage

Am 2026-09-25 lief eine Generalprobe der Phase-C-Auswertung auf 885 von 936 Records
(`outputs/phase_c_dryrun_2026-09-25/`: `tasks/`, `history.jsonl`, `run_registry.csv`). Registry,
Invarianten und Strukturmetriken laufen seit WP-N26. Die Strukturmetriken liegen unter
`outputs/phase_c_dryrun_2026-09-25/agg/structure_n26/phasec_structure_metrics_by_cell.csv` und
sind per `run_id` an die Registry anschließbar. Danach scheitert die Kette an vier Stellen:

1. **Es fehlt ein Schritt, der die Strukturmetriken in die Registry einmischt.**
   `aggregate_phasec_cap_ablation.py` verlangt Spalten `structural_f1`, `term_precision`,
   `term_recall`, `coefficient_relative_error_mean`. Die Strukturmetriken liefern
   `structural_f1_micro/_macro`, `term_precision_micro/_macro` usw. **Entschieden am 2026-09-26 vom
   Nutzer:** Die unsuffigierten Namen sind **micro** (über alle Terme eines Laufs gepoolt), macro
   steht immer daneben.
2. **Cap-Ablation** (`aggregate_phasec_cap_ablation.py`):
   (a) Sie akzeptiert nur die Arme C-1/C-2 und bricht an der Kampagnen-Registry ab, die auch C-3
   (`evogrow_v2_2_stage_capped_pretune_on`) enthält.
   (b) Sie verlangt `system_expected_stage` und `coefficient_relative_error_mean` in **jeder**
   Zeile als Zahl. Beide sind für Surrogat-Systeme per Definition leer (Designprinzip 8: exakte und
   Surrogat-Systeme werden nie in einer Strukturmetrik gemischt).
3. **SINDy-Paarung** (`run_phasec_sindy_baseline.py pair`) leitet die erwartete Menge
   (Seed, Bedingung) global ab und verlangt sie für jedes System. C-3 deckt nur die 30 exakten
   Systeme ab, also scheitert sie auch auf vollständigen Daten (Beispiel System 4, Surrogat). Claim D
   paart laut `docs/paper1_phaseC_benchmark_plan.md` **nur C-1** gegen SINDy.
4. **Pretuning-Collapse** (`analyze_pretuning_distribution_collapse.py`) hat die Phase-B-Varianten
   fest verdrahtet (`..._pretune_on` / `..._pretune_off`), und es gibt keine Konfiguration
   `analysis/configs/paper1_phaseC_v1.json`. In Phase C ist `pretune_on` =
   `evogrow_v2_2_stage_capped_pretune_on` (C-3), `pretune_off` = `evogrow_v2_2_stage_capped` mit
   `use_pretuning = false` (C-1). Der Vergleich (Abl-2) umfasst nur die 30 exakten Systeme ×
   3 Seeds × 2 IC-Sets = **180 Paare** und gruppiert auf **roher** `support_terms` (Plan §1b).

## Was zu tun ist

1. **Neuer Schritt `analysis/scripts/aggregate/build_phasec_analysis_registry.py`:** Er liest die
   verifizierte Kampagnen-Registry und die Strukturmetriken pro Zelle, verbindet sie 1:1 über
   `run_id` (Abbruch bei fehlender oder doppelter Zeile) und schreibt eine Analyse-Registry mit den
   unsuffigierten Namen = micro plus allen `_micro`/`_macro`-Spalten. Dazu kommen die abgeleiteten
   Teilmengen als eigene Dateien:
   - `…_c1_c2.csv`: C-1 und C-2, für die Cap-Ablation
   - `…_c1.csv`: nur C-1, für SINDy-Paarung und C-5
   - `…_pretuning.csv`: C-1 ∩ exakte Systeme und C-3, für Abl-2

   Jede Teilmenge wird über `variant_slug` **und** `use_pretuning` gebildet, nie über den Namen
   allein. Die Zeilenzahlen werden gegen die Erwartung aus `phase_c_support.json` geprüft (mit
   einer expliziten Option für unvollständige Kampagnen, die im Output vermerkt wird).
2. **Cap-Ablation:** Metriken, die nur für exakte Systeme existieren (`system_expected_stage`,
   Koeffizientenfehler, Strukturtreffer gegen die Wahrheit), dürfen bei Surrogaten leer sein. Ihre
   Qualitäts-Deltas werden **nur auf exakten Paaren** berechnet und so ausgewiesen (Zahl der Paare
   im Output). Kostenmetriken und R² laufen über alle Paare, stratifiziert wie bisher. Ein Leerwert
   bei einem **exakten** System bleibt ein Abbruch.
3. **SINDy-Paarung:** Im Modus für Claim D werden nur C-1-Records gepaart. Die erwartete Menge
   (Seed, Bedingung) wird pro Arm aus dessen Umfang abgeleitet, nicht global. Abbruch, wenn ein
   C-1-Record fehlt.
4. **Pretuning-Collapse:** `analysis/configs/paper1_phaseC_v1.json` anlegen. Das Skript bekommt die
   Variantenzuordnung aus der Konfiguration, nicht aus Konstanten. Die Phase-B-Konfiguration trägt
   die bisherigen Werte, damit Phase B **bitgleich** bleibt. Erwartete Paarzahlen für Phase C aus
   `phase_c_support.json` (180; exakt 180, Surrogat 0).
5. `SCRIPTS.md`, Abschnitt Phase-C-Kette: den neuen Schritt einfügen, zwischen Strukturmetriken und
   den Konsumenten. `docs/paper1_phaseC_benchmark_plan.md` §1a: bei Claim A "structural F1" mit dem
   Zusatz "(micro; macro reported beside it, decided 2026-09-26)".

## Verboten

- Keine Git-Operationen.
- Phase-A- und Phase-B-Ausgaben dürfen sich nicht ändern (bitgleich prüfen, wo ein Skript beide
  bedient).
- Keine Pruning-Schwelle, keine Metrikdefinition außer der micro/macro-Benennung ändern.
- Nichts unter `analysis/data/` oder `analysis/tables/` schreiben. Probe-Ausgaben nur nach
  `outputs/phase_c_dryrun_2026-09-25/agg_n28/`.

## Abnahme

1. Tests für jeden der fünf Punkte, einschließlich: fehlende oder doppelte `run_id` beim Join →
   Abbruch; Teilmengen über `use_pretuning`; Surrogat-Leerwert erlaubt, exakter Leerwert → Abbruch;
   SINDy-Paarung auf einem System ohne C-3 läuft; Pretuning-Zuordnung aus der Konfiguration.
2. **Die ganze Kette auf der Probe-Registry** mit der Option für unvollständige Daten: Analyse-
   Registry → Cap-Ablation → SINDy-Paarung (gegen
   `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv`, EvoGrow-Records aus
   `outputs/phase_c_dryrun_2026-09-25/tasks`) → Pretuning-Collapse. Alle laufen durch; Ausgaben nach
   `agg_n28/`. Die Befehle stehen im Report.
3. Phase-B-Bitgleichheit für `analyze_pretuning_distribution_collapse.py` mit der Phase-B-
   Konfiguration gegen die vorhandenen Phase-B-Ausgaben.
4. Report `codex/reports/REPORT_WP_N28.md`: geänderte Dateien, Befehle, Paarzahlen aus der Probe,
   was nicht verifiziert ist.
