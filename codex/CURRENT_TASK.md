# WP-N41 — Orion-Manifest für den Rest von B-04 und für B-05 (C-8 Teil B, Suche mit lockerer Grenze)
**Language: Julia** (Manifest-YAML, ggf. kleine Erweiterung des Auswahlskripts)

## Hintergrund

Plan §9.6 Teil B: volle EvoGrow-Suchen mit Grenze 1000 bzw. ∞, Seed 42, beide IC-Sets, **saubere
Daten** (σ = 0, ρ = 0). Die Grenze 10 ist C-1 selbst. Lokal gelaufen sind 6 von 8 Zellen von B-04
(System 1 komplett, System 24 bei Grenze 1000), Ausgabe `outputs/b04_search_bounds/`. Die beiden
Zellen **System 24, Grenze ∞, IC 1 und IC 2** wurden vom Laufzeitlimit abgebrochen: Ohne Grenze steigt
die Zeit je Eval stark, z. B. System 1 IC 1 mit 2.801 s statt 15 s in C-1. Sie gehen deshalb nach Orion,
zusammen mit **B-05: System 52 und 57, Grenzen 1000 und ∞, IC 1 und 2**.

Der Job umfasst **10 Zellen**: 24 × {IC1, IC2} × ∞ (2), 52 × {IC1, IC2} × {1000, ∞} (4) und
57 × {IC1, IC2} × {1000, ∞} (4).

## Umsetzung

1. Neue Datei `k8s/phase_c_c8_search_b05_job.yaml`. Vorlage ist
   `k8s/phase_c_robustness_stage3_orion_job.yaml` (Bootstrap → Smoke → indizierter Lauf). Der
   Bootstrap erzeugt mit `generate_phase_c_manifest.jl --clamp-val <b> --all-dimensions` je Grenze ein
   sauberes Manifest und wählt daraus die 10 Zeilen aus (Variante `evogrow_v2_2_stage_capped`, Seed 42).
   Kann `select_phase_c_stage2_manifest.jl` mehrere IC-Sets oder Grenzen noch nicht, erweitern. Die
   Erweiterung muss für die bisherigen Aufrufe (Stufe 2 und 3) **byte-identisch** dasselbe liefern,
   mit Test. Die Indizes bleiben wie bisher, die Zellen werden zusammengeführt und neu nummeriert.
2. **Smoke:** System 1, IC 1, Grenze 1000 (lokal fertig: `outputs/b04_search_bounds/bound_1000/tasks/cell_000001.jsonl`).
   Er muss bitgleich zu dieser Zelle sein in `loss`, `support_terms`, `total_loss_evals`,
   `model_terms` und `config_fingerprint`. Die Vergleichsanweisung steht im Report.
3. Eigene Job-Namen und Labels (`…-c8-search-b05…`), Ausgabebasis
   `/outputs/phase_c_c8_search_b05_<COMMIT_SHA>`. Kein `activeDeadlineSeconds`.
4. **Kopfkommentar mit erwarteter Laufzeit:** C-1 brauchte für 52 1,8 h und 1,0 h, für 57 17,2 h und
   22,5 h. Ohne Grenze kann die Zeit je Eval um ein Vielfaches steigen (Messung oben, B-03-Shard über
   12 h). **Zellen von System 57 können 24 h deutlich überschreiten.** Steht so im Kommentar, Claude
   bespricht es vor dem Apply mit dem Nutzer.
5. `SCRIPTS.md`: Abschnitt mit Apply, Fortschritt und Einsammeln vom NFS, wie bei WP-N37.

## Verboten

`src/`, Such- oder Fitpfad ändern. Bestehende Manifeste ändern. `activeDeadlineSeconds`/`timeout`.
Julia-Läufe über einen Smoke hinaus. Git, `oc`, `codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

YAML und gegebenenfalls Skripterweiterung samt Test. Report `codex/reports/REPORT_WP_N41.md` mit
dem Befehl, den Claude ausführen soll: ein lokaler Bootstrap-Trockenlauf, der die 10 ausgewählten
Zeilen ausgibt (System, IC, Grenze), mit Pass-Kriterium. `STATUS.md` nach Protokoll.
