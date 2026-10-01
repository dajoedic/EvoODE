# WP-N33b — Orion-Jobs für die nächsten Stufen (Stufe 2 / System 18, Grenzen-Orakel B-02)
**Language: YAML + Python** (Manifeste, Eingabevorbereitung)

Spezifikation: `docs/paper1_phaseC_benchmark_plan.md` §9.4a und §9.6. Backlog: `CLAUDE.md`,
„Backlog Paper 1“ (R-05, B-02). Laufort-Regel: `CLAUDE.md`, „Collaboration“. Auf Orion läuft nur,
was per `activeDeadlineSeconds` auf **höchstens 24 h** begrenzt ist.

## Ziel

Zwei Orion-Jobs, die der Nutzer per `oc apply` startet. **Nur diese beiden**, kein Manifest für
das ganze Raster.

### Job 1 — Stufe 2, System 18 (R-05, Orion-Anteil)

- Zellen: System 18, Variante `evogrow_v2_2_stage_capped`, Seed 42, IC-Set 1, Realisierung 1, bei
  `(sigma, rho) = (0.01, 0)` und `(0.05, 0.5)`, `clamp_val = 10`. Das sind **2 Zellen**.
- Weg: `studies/regression/run_batch_cell.jl` über ein kleines Manifest im Phase-C-Format mit den
  WP-N32-Spalten. Das Manifest erzeugt `generate_phase_c_manifest.jl` (je Bedingung einmal), die
  Zeilen von System 18 werden ausgewählt. Bau es so, dass es in einem Bootstrap-Schritt auf dem
  Cluster entsteht, wie bei den bestehenden Phase-C-Jobs (`k8s/phase_c_bootstrap_campaign_job.yaml`).
  Alternativ legt es Claude lokal an und kopiert es aufs NFS. Wähle einen Weg und begründe ihn.
- Indexed Job mit `completions: 2`, `parallelism: 2`, **`activeDeadlineSeconds: 86400`**,
  Ressourcen wie die bestehenden Phase-C-Jobs (1 CPU, Threads = 1).
- Ausgabe nach `/outputs/phase_c_robustness_stage2_<COMMIT_SHA>/…`, Records und Heartbeats je Zelle.
- Dazu ein Smoke-Job auf **System 1** bei `(0.01, 0)` (1 Zelle, Deadline 1 h). Er beweist, dass das
  Image den neuen Pfad trägt. Der Record muss bitgleich zu `outputs/stage1/s0.01_r0/tasks/cell_000001.jsonl`
  sein (`loss`, `support_terms`, Koeffizienten, `total_loss_evals`, `stage_caps`,
  `observed_data_sha256`). Gib das Vergleichskommando an.

### Job 2 — B-02: Grenzen-Orakel auf allen exakten dim-1/2-Systemen

- 21 exakte Systeme mit dim ≤ 2 (`phase_c_support.json`) × 3 Seeds × 2 IC-Sets = 126 C-1-Zellen, je
  bei `clamp_val` 10, 1000 und Inf. Das sind **378 Refits**.
- Eingabe: eine aus `outputs/phase_c_campaign_221a3a7/history.jsonl` **gefilterte** Datei mit genau
  den C-1-Records (Variante `evogrow_v2_2_stage_capped`) dieser 21 Systeme. Schreib dafür ein kleines
  Python-Skript, das die Datei erzeugt, die Zahl der Records prüft (126) und den SHA-256 ausgibt. Der
  Orakel-Fingerprint enthält Pfad und Hash der Eingabe, darum muss der Hash im Report stehen.
- Je Grenze ein Indexed Job mit Shards (`--shards`, `--shard-index`). Die Zahl der Shards begründest
  du aus `--estimate-cost` des Orakelskripts. Das Kommando dafür steht im Report, Claude führt es aus.
  **`activeDeadlineSeconds: 86400`** pro Job.
- Ausgabe nach `/outputs/phase_c_c8_oracle_b02_<COMMIT_SHA>/bound_<10|1000|Inf>/…`.

## Für alle Jobs

- Image `registry.gitlab.scch.at:443/joedicke/evoode:<COMMIT_SHA>`, Platzhalter wie in den
  bestehenden Manifesten. Das Image muss WP-N32 und WP-N33a tragen. Schreib in den Kopfkommentar,
  ab welchem Commit das gilt (`49b0613` oder später).
- Labels, `imagePullSecrets`, NFS-Mount und `ttlSecondsAfterFinished` wie in
  `k8s/phase_c_c5_oracle_job.yaml`.
- Je Job ein Kopfkommentar mit Zweck, Zellenzahl, Deadline-Begründung und Backlog-Punkt.
- Ein Abschnitt in `SCRIPTS.md`: Vorbereitung, `oc apply`, Fortschritt lesen, Einsammeln. Die
  Befehle sind als Vorlage markiert, **nicht** als „jetzt ausführen“.

## Verboten

Jobs starten, `oc`-Befehle ausführen, Methodencode, Runner oder Fingerprints ändern, Git,
`codex/CURRENT_TASK.md` bearbeiten, `docs/` ändern. Kein Manifest für das ganze C-6-Raster und
keins für Stufe 3.

## Abnahme

1. Die Manifeste sind gültiges YAML. Prüf das mit Python (`yaml.safe_load_all`) in deiner Sitzung.
   Jedes trägt `activeDeadlineSeconds` ≤ 86400.
2. Das Filterskript für B-02 läuft in deiner Sitzung, erzeugt 126 Records und meldet den Hash. Ein
   Test zeigt, dass falsche Zahlen abbrechen.
3. Im Report stehen die Kommandos für Claude: `--estimate-cost` für B-02 und der lokale Vergleich des
   Smoke-Records.
4. Report `codex/reports/REPORT_WP_N33B.md`, `STATUS.md` nach Protokoll.
