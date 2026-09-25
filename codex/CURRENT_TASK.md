# WP-N27 — Das ODEFormer-Referenzraster auf Orion: CI-Image, Wiederholungen, Job-Manifest
**Language: Python**

## Ausführung

Lokal umsetzbar. Kein Docker-Build, kein `oc`/`kubectl`, kein Push; das macht Claude bzw. der
Nutzer. Python-Tests nur gezielt für die geänderten Dateien. Nichts, was länger als 15 Minuten
läuft.

## Ausgangslage

Entscheidung vom 2026-09-25 (`docs/paper1_phaseC_benchmark_plan.md`, Absatz "The output is not
deterministic …"): Das ODEFormer-Referenzraster für Claim D läuft im Modus **`faithful`**
(ODEFormers eigene 1-s-Integrationsgrenze), mit **drei Wiederholungen pro Zelle** und **einem
ODEFormer-Prozess pro CPU**. Berichtet wird die Rate mit ihrer Streuung. Das Raster umfasst 63
Systeme × 2 Richtungen (Fit-IC 1 → Ziel 2, Fit-IC 2 → Ziel 1) × 4 Konfigurationen = 504 Zellen,
also 1.512 Zell-Wiederholungen. Gemessen am WP-N23-Raster (`elapsed_s_non_evidence` in
`analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_wp_n23/records.jsonl`): 8,35 h pro
Wiederholung sequentiell, Median 36 s pro Zelle, Maximum 940 s. Nach der 8-Stunden-Regel gehört das
auf Orion.

Was fehlt:

1. **Kein Image in der Registry.** `.gitlab-ci.yml` baut nur das Kampagnen-Image
   (`build_campaign_image`, `containers/Dockerfile`). `baselines/Dockerfile.odeformer-reference`
   wird nirgends gebaut. Es lädt die Gewichte beim Bau per `gdown` von Google Drive und prüft den
   SHA-256; daneben liegt `baselines/Dockerfile.odeformer-reference.dockerignore`.
2. **Keine Wiederholungen im Grid-Runner.** `baselines/run_odeformer_grid.py` kennt
   `--shard-index/--shard-count` (Modulo-Aufteilung über die Arbeitszellen), aber keine
   Wiederholung. `baselines/run_odeformer_repeatability.py` kennt Wiederholungen, rechnet aber nur
   die ausgewählten Zellen.
3. **Die Trajektorien liegen nicht im Image.** `baselines/configs/odeformer_grid.json` zeigt auf
   `outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export`; `outputs/` ist gitignored und im
   CI-Checkout nicht vorhanden. Die Trajektorien werden deshalb auf das NFS gelegt (das macht
   Claude), und der Runner braucht einen Weg, den Export-Pfad von außen zu setzen.
4. **Kein Job-Manifest.**

## Was zu tun ist

1. **CI-Job `build_odeformer_reference_image`** in `.gitlab-ci.yml`, nach dem Muster von
   `build_campaign_image`: gleiche Runner-Tags, gleicher per Digest gepinnter dind-Dienst, gleiche
   Flags gegen Attestations (`--provenance=false --sbom=false`, `BUILDX_NO_DEFAULT_ATTESTATIONS`).
   - Image: `$CI_REGISTRY_IMAGE/odeformer-reference:$CI_COMMIT_SHA`, zusätzlich der Tag
     `:$CI_COMMIT_REF_SLUG`.
   - Er läuft nur auf `main` und nur, wenn sich `baselines/**` geändert hat (`rules: changes`).
     Außerdem ist er manuell startbar (`when: manual` als zusätzliche Regel), damit ein Build auch
     ohne Änderung möglich ist. Den Kampagnen-Job nicht verändern.
   - Ein Trivy-Image-Scan für dieses Image, `allow-failure: true` wie beim Kampagnen-Image. Die
     Befunde sind unter der bestehenden Ausnahme E7 dokumentiert; im `CHANGELOG.md` darauf
     verweisen.
   - `CHANGELOG.md`: ein Eintrag nach dem Stil der vorhandenen Einträge, mit Datum 2026-09-25, was
     der Job baut, warum (Claim D auf Orion, 8-h-Regel), und ein Hinweis auf das Risiko, dass der
     Runner Google Drive (`gdown`) erreichen muss. Falls das scheitert, ist das der erste Ort, an dem
     es sichtbar wird.
2. **Wiederholungen im Grid-Runner.** `run_odeformer_grid.py` bekommt `--repetition N` (1-basiert).
   Jede Wiederholung schreibt in ein eigenes Unterverzeichnis `rep_{N:03d}/` unter dem
   Ausgabeordner. Sonst ändert sich nichts: gleiche Zellen, gleiche Records, gleicher Seed. Die
   Wiederholungen unterscheiden sich nur durch die Uhr, genau das wird gemessen. Ohne
   `--repetition` bleibt das Verhalten **bitgleich** zum heutigen (Test).
3. **Export-Pfad und Modus von außen.** `--trajectory-export-dir` überschreibt
   `trajectory_export_dir` aus der Konfiguration. Jeder Record trägt den tatsächlich benutzten
   Pfad und die Hashes aus `trajectory_manifest.csv`, wie bisher. Der Runner prüft beim Start, dass
   die Integrationsgrenze ODEFormers eigene ist (`faithful`, d. h. keine Überschreibung von
   `integration_timeout_seconds`), schreibt das in jeden Record und bricht ab, falls die
   Konfiguration etwas anderes verlangt.
4. **Threads.** Ein ODEFormer-Prozess pro CPU: Im Manifest `OMP_NUM_THREADS`, `MKL_NUM_THREADS`,
   `OPENBLAS_NUM_THREADS` auf 1 setzen. Zusätzlich setzt der Runner `torch.set_num_threads(1)`,
   wenn eine Umgebungsvariable (z. B. `ODEFORMER_TORCH_THREADS`) das verlangt, und protokolliert die
   tatsächliche Thread-Zahl im Record. Ohne die Variable bleibt das heutige Verhalten.
5. **Indizierter Job** `k8s/odeformer_reference_grid_job.yaml`, nach dem Muster von
   `k8s/phase_c_c1_c2_campaign_job.yaml`: gleicher Namespace, gleiche Labels (Komponente eigen),
   gleiche NFS-Einbindung, `imagePullSecrets: evoode-gitlab-pull`, `requests == limits`,
   `cpu: "1"`. Den Speicher aus dem WP-N23-Lauf herleiten, falls dort gemessen; sonst 4 Gi mit
   Kommentar, dass geschätzt.
   - Aufteilung: **pro Wiederholung 42 Shards** über die 504 Arbeitszellen, also 12 Zellen pro
     Shard, 3 × 42 = **126 Completions**. Der Completion-Index `i` (0-basiert) ergibt
     Wiederholung = `i // 42 + 1` und Shard = `i % 42`. Die Umrechnung macht ein kleiner
     Einstiegspunkt (Python, z. B. `baselines/run_odeformer_grid_k8s.py`), der
     `JOB_COMPLETION_INDEX` liest und den Grid-Runner aufruft. Keine Shell-Arithmetik im YAML.
   - `parallelism: 16`, mit Kommentar, vor dem Start Quota und laufende Phase-C-Pods zu prüfen.
   - **`activeDeadlineSeconds` für den ganzen Job** als großzügige obere Schranke, nicht als
     Punktschätzung. Herleitung im Kommentar: 1.512 Zell-Wiederholungen × 940 s (Maximum) / 16
     parallel, mal Sicherheitsfaktor 2, aufgerundet. Zur Lehre vom 23.09.: Eine Deadline aus einer
     Punktschätzung hätte WP-T1d abgebrochen.
   - Pfade: Export unter `/outputs/odeformer_grid_<COMMIT_SHA>/trajectory_export`, Ausgabe unter
     `/outputs/odeformer_grid_<COMMIT_SHA>/reference/`. `<COMMIT_SHA>` bleibt Platzhalter wie in
     den anderen Manifesten.
   - `backoffLimit` und `ttlSecondsAfterFinished` wie beim Kampagnen-Job, mit denselben Kommentaren
     zu Infrastruktur- vs. Wissenschaftsfehlern.
6. **Smoke-Manifest** `k8s/odeformer_reference_grid_smoke_job.yaml`: ein Pod, eine Wiederholung,
   `--limit 2`, eigener Ausgabeordner `smoke/`, kurze Deadline. Er prüft Image-Pull, NFS, Gewichte
   und Export-Pfad, bevor 126 Pods starten.
7. **Collect**: Nach dem Lauf müssen alle drei Wiederholungen je 504 Records haben. Der vorhandene
   Collect-Pfad des Grid-Runners bzw. von `summarize_odeformer_grid.py` muss mit `rep_*/` umgehen
   und abbrechen, wenn eine Wiederholung unvollständig ist. Zusätzlich eine Streuungsübersicht pro
   Zelle über die drei Wiederholungen: bitgleich ja/nein, min/max Handler-Timeouts, R²>0.9-Kipper.
   Das ist dieselbe Logik wie in `run_odeformer_repeatability.py`; wiederverwenden, nicht kopieren.
8. `SCRIPTS.md`: ein Abschnitt "ODEFormer-Referenzraster auf Orion" mit der Reihenfolge Push → CI
   → NFS-Vorbereitung → Smoke → Job → Collect. Wo ein Befehl vom Nutzer kommt, ist das markiert.

## Verboten

- Keine Git-Operationen.
- `build_campaign_image`, `containers/Dockerfile`, die Phase-C-Manifeste und alles unter `src/`
  und `studies/` nicht ändern.
- `baselines/Dockerfile.odeformer-reference` nur ändern, wenn es für den CI-Bau zwingend ist; dann
  im Report begründen. Die Paketversionen und der ODEFormer-Commit bleiben unverändert.
- Nichts unter `analysis/data/` schreiben.
- Keine Wall-Clock-Grenze einführen oder verändern; der Modus ist `faithful`.

## Abnahme

1. Tests für: `--repetition` (eigenes Unterverzeichnis, ohne Argument bitgleich), die Umrechnung
   Completion-Index → (Wiederholung, Shard) für 0, 41, 42 und 125, Abbruch bei nicht-`faithful`,
   Collect bricht bei unvollständiger Wiederholung ab, die Shards einer Wiederholung decken die 504
   Zellen genau einmal ab.
2. `python -m pytest baselines/tests -q` für die neuen bzw. betroffenen Testdateien grün.
3. Beide YAML-Dateien und `.gitlab-ci.yml` sind syntaktisch gültiges YAML (mit PyYAML geprüft).
4. Report `codex/reports/REPORT_WP_N27.md`: geänderte Dateien, die Herleitung der Deadline, die
   Befehle für Claude (lokaler Docker-Test des Einstiegspunkts mit dem vorhandenen Image
   `evoode/odeformer-reference:wp-n21`) und was nicht verifiziert ist.
