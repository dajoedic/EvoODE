# WP-N33c — Stufe-2-Orion-Job um System 24 erweitern
**Language: YAML** (+ `SCRIPTS.md`)

## Anlass

Stufe 2 lokal (`DIARY.md` 2026-10-01): System 24 hat bei `(0.01, 0)` und `(0.05, 0.5)` die
55-Minuten-Grenze des Laptops gerissen (Exit 124). Nach der Laufort-Regel gehört es deshalb auf
Orion, mit höchstens 24 h. System 18 war ohnehin für Orion vorgesehen
(`k8s/phase_c_robustness_stage2_system18_job.yaml`, WP-N33b).

## Umsetzung

1. Ein Manifest `k8s/phase_c_robustness_stage2_orion_job.yaml` ersetzt das System-18-Manifest. Das
   alte bleibt liegen, wird aber im Kopfkommentar als ersetzt markiert. Inhalt:
   - Bootstrap und Smoke wie bisher. Smoke ist System 1 bei `(0.01, 0)`, bitgleich zu
     `outputs/stage1/s0.01_r0/tasks/cell_000001.jsonl`.
   - Die Stufenzellen: **System 18 und System 24**, je `(0.01, 0)` und `(0.05, 0.5)`, Seed 42,
     IC-Set 1, Realisierung 1, `clamp_val = 10`. Das sind **4 Zellen**, `completions: 4`,
     `parallelism: 4`, `activeDeadlineSeconds: 86400`.
   - Image-Tag `eb630b5` oder später im Kopfkommentar. Dieses Image trägt die Heartbeats mit der
     Struktur je Level (WP-N35).
2. `SCRIPTS.md`: den Abschnitt für Stufe 2 auf das neue Manifest umstellen, Befehle als Vorlage,
   nicht als „jetzt ausführen“. Dazu die lokalen Vergleichsdaten: Exportindex
   `outputs/stage2/data_export/index.csv` (enthält 17, 18, 24). Der Tor-Bericht nach dem Einsammeln
   läuft wie bei den lokalen Zellen.

## Verboten

Jobs starten, `oc` ausführen, Code ändern, Git, `docs/`, `codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

YAML gültig (`yaml.safe_load_all` in deiner Sitzung), jede Deadline ≤ 86400, die vier Zellen im
Report aufgelistet mit Manifest-Index. Report `codex/reports/REPORT_WP_N33C.md`, `STATUS.md` nach
Protokoll.
