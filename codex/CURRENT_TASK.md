# WP-N40 — ODEFormer-Strukturtreffer im Referenz- und Kandidatenraster nachrechnen, WP-N31 neu aggregieren
**Language: Python**

## Hintergrund

WP-N38 Fortsetzung 3 hat gezeigt: Alle 1.512 Records des Orion-Referenzrasters
(`analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records.jsonl`) und
vermutlich auch des Kandidatenrasters (`candidate_orion_8e0e699`) haben leere `active_terms_*` und
`structure_hit_* = False`. WP-N31 liest diese Felder direkt
(`analysis/scripts/aggregate/run_phasec_sindy_baseline.py::build_odeformer_pair_rows`). Damit ist
**jede ODEFormer-Strukturrate aus WP-N31 ungültig**. Die R²-Raten sind nicht betroffen. Die
gemeinsame kanonische Expansion existiert seit WP-N38 (`baselines/harness.py`,
`symbolic_active_terms_by_equation` u. a.). Der Nachberechnungsmodus
`run_odeformer_noise.py --recompute-structure-fields` scheitert auf dem Rasterformat
(`KeyError: 'source_initial_condition_set'`).

## Umsetzung

1. Nachberechnung für das **Rasterformat** (Referenz und Kandidat): dieselbe Expansion, dieselbe
   Pruning-Regel und dieselben `true_terms` aus `phase_c_support.json` wie in WP-N38. Am besten ein
   gemeinsamer Kern, den beide Formate aufrufen. Die Rohdateien unter `analysis/data/…` werden
   **nicht überschrieben**. Die nachberechneten Records gehen in neue Dateien, z. B.
   `…/reference_orion_55e9c75/records_structure_recomputed.jsonl`, plus eine Manifest-Notiz mit
   Datum, Code-Hash und Grund.
2. WP-N31 neu aggregieren (`run_phasec_sindy_baseline.py`, ODEFormer-Paarung) auf den
   nachberechneten Records, in ein **neues** Ausgabeverzeichnis. Die alten Ausgaben bleiben liegen.
   Im Report die alten gegen die neuen Strukturraten je Konfiguration, Dimension und Dreiwege-Klasse,
   die R²-Raten als Kontrolle (müssen identisch bleiben).
3. Tests: Ein Rasterrecord für System 1 mit `0.2835 - 0.3557*x_0` ergibt Treffer `[1, u1]`. Ein
   rationaler Ausdruck wird außerhalb der Basis gezählt, ohne Absturz. Die R²-Felder bleiben
   unverändert.

## Verboten

ODEFormer laufen lassen. Rohdateien des Referenz- oder Kandidatenrasters ändern. Pruning-Regel
anpassen. Git, `oc`, `codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

Nachberechnung und Neuaggregation ausgeführt (Python). R²-Raten identisch zur alten Ausgabe.
Report `codex/reports/REPORT_WP_N40.md` mit der Vergleichstabelle. Tests grün. `STATUS.md` nach
Protokoll.
