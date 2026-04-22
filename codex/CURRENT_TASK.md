# WP-E3: Aggregator — run_registry.csv

## Kontext

EvoODE ist ein Julia-Forschungsprojekt zur datengetriebenen Entdeckung interpretierbarer ODE-Systeme.
WP-E1 hat die Experiment-Verzeichnisstruktur und Manifest angelegt.
WP-E2 hat den Runner implementiert, der Runs ausführt und pro Run folgende Dateien schreibt:
- `status.json` (status, success, failure_reason, started_at, finished_at, git_hash)
- `result.json` (finale wissenschaftliche Outputs)
- `metrics.json` (numerische Metriken für Aggregation, flaches Dict)
- `log.txt`, `summary.txt`

Ziel dieses Work Packages: ein Aggregations-Skript, das alle Run-Folder eines Experiments scannt
und daraus eine vollständige `run_registry.csv` ableitet.
Die CSV ist **nicht primär** — sie wird immer vollständig aus den per-Run-Folder neu generiert
und kann jederzeit ohne Informationsverlust neu erzeugt werden.

---

## Dateien, die vor jeder Implementierung vollständig zu lesen sind

- `experiments/run_experiment.jl` — vollständig lesen (Referenz für alle Datei-Schemas)
- `experiments/generate_manifest.jl` — vollständig lesen (Referenz für config.json-Schema)
- `experiments/paper1_phaseA_v1/runs/26_evogrow_v2_2_stage_local_seed42/config.json` — Beispiel EvoGrow-Config
- `experiments/paper1_phaseA_v1/runs/26_gp_baseline_seed42/config.json` — Beispiel GP-Config
- `experiments/paper1_phaseA_v1/runs/26_evogrow_v2_2_stage_local_seed42/status.json` — Beispiel Status
- Wenn vorhanden: `experiments/paper1_phaseA_v1/runs/26_evogrow_v2_2_stage_local_seed42/metrics.json` — Beispiel Metrics

---

## Was zu implementieren ist

### Neues Skript `experiments/aggregate.jl`

Das Skript nimmt `experiment_id` als erstes Kommandozeilenargument.
Beispiel: `julia experiments/aggregate.jl paper1_phaseA_v1`

---

### Schritt 1: Startup

- Pkg.activate auf das Projektroot (ein Verzeichnis über `experiments/`)
- Imports: `Dates`, `JSON3`, `Printf`
- Kein `include` von EvoODE nötig — der Aggregator liest nur JSON-Dateien und schreibt CSV.
- Lese `experiment_id` aus `ARGS[1]`. Falls kein Argument: Fehler mit Nutzungshinweis.
- Setze `experiment_dir = joinpath(@__DIR__, experiment_id)`
- Prüfe, ob `experiment_dir` existiert. Falls nicht: Fehler.
- Lese `manifest.json`. Falls nicht vorhanden oder kein valides JSON: Fehler.

---

### Schritt 2: Alle Run-Folder scannen

Iteriere über alle `run_ids` aus `manifest.json` (nicht über `readdir` — das Manifest ist die
autoritative Liste).

Für jeden `run_id`:

**Lese `config.json`:**
Falls nicht vorhanden oder kein valides JSON: markiere Run als `corrupted`, überspringe restliche Felder.

**Lese `status.json`:**
Falls nicht vorhanden: `inferred_status = "never_started"`, alle Status-Felder null.
Falls kein valides JSON: markiere als `corrupted`.
Falls valide:
- Lese `status`, `success`, `failure_reason`, `failure_detail`, `started_at`, `finished_at`.
- **Interrupt-Inferenz:** Wenn `status == "running"` und `finished_at` ist null:
  setze `inferred_status = "interrupted"`.
  Schreibe `status.json` nicht um — das ist rein eine Aggregator-Sicht.
- Sonst: `inferred_status = status`.

**Lese `metrics.json`:**
Falls nicht vorhanden: alle Metrik-Felder auf null, `metrics_available = false`.
Falls kein valides JSON: alle Metrik-Felder auf null, `metrics_available = false`, markiere als `corrupted`.
Falls valide: lese alle Felder. `metrics_available = true`.

**Corrupted-Erkennung:**
Ein Run gilt als corrupted wenn:
- `status == "finished"` UND (`result.json` fehlt ODER ist kein valides JSON ODER `metrics.json` fehlt)
- ODER `config.json` ist nicht valides JSON
- ODER `metrics.json` existiert aber ist kein valides JSON

Setze `corrupted = true` in diesen Fällen.

---

### Schritt 3: CSV schreiben

Schreibe `experiments/<experiment_id>/run_registry.csv` — vollständiges Überschreiben bei jedem Aufruf.

**Spalten (in dieser Reihenfolge):**

Aus `config.json`:
- `run_id`
- `experiment_id`
- `phase`
- `hypothesis`
- `run_type`
- `include_in_paper`
- `system_id`
- `system_name`
- `system_dim`
- `system_representability`
- `system_expected_stage`
- `variant`
- `seed`

Aus `status.json`:
- `status`
- `inferred_status`
- `success`
- `failure_reason`
- `started_at`
- `finished_at`

Aus `metrics.json`:
- `loss`
- `objective`
- `exact_support_match`
- `final_stage`
- `stage_overshoot`
- `wasted_levels`
- `total_loss_evals`
- `total_invalid_evals`
- `elapsed_s`
- `partial`

Abgeleitet:
- `metrics_available` (bool)
- `corrupted` (bool)

**Format-Regeln:**
- Trennzeichen: Komma (`,`)
- Fehlende / null Werte: leerer String (kein `NA`, kein `null`)
- Bool-Werte: `true` / `false` als String
- Float-Werte: volle Präzision (kein gerundeter Printf)
- Strings mit Kommas oder Anführungszeichen: in doppelte Anführungszeichen einschließen
- Header in erster Zeile
- Keine Zeile darf fehlen — auch `corrupted`, `failed`, `never_started` Runs haben eine Zeile

**Keine stille Auslassung.** Jeder run_id aus dem Manifest erzeugt genau eine CSV-Zeile.

---

### Schritt 4: Stdout-Report

Nach dem Schreiben der CSV, gib auf stdout aus:

```
Experiment: <experiment_id>
Total runs in manifest: <N>
  finished (success=true):  <n>
  finished (success=false): <n>
  failed:                   <n>
  interrupted:              <n>
  queued:                   <n>
  never_started:            <n>
  corrupted:                <n>
run_registry.csv written to: <pfad>
```

---

## Was sich nicht ändern darf

- Alles in `src/`
- `benchmarks/benchmark_evogrow.jl`
- `experiments/generate_manifest.jl`
- `experiments/run_experiment.jl`
- Alle bestehenden `config.json`, `status.json`, `metrics.json`, `result.json` in den Run-Foldern
- Das Skript schreibt **ausschließlich** `run_registry.csv` — keine andere Datei wird verändert

---

## Abschlussbedingung

Codex führt das Skript auf dem bestehenden Experiment aus:
`julia experiments/aggregate.jl paper1_phaseA_v1`

Und prüft danach:

1. `experiments/paper1_phaseA_v1/run_registry.csv` existiert.
2. Die CSV hat genau 301 Zeilen (1 Header + 300 Datenzeilen).
3. Jede Datenzeile hat die korrekte Anzahl an Spalten.
4. Runs mit `status="queued"` haben leere Metrik-Felder.
5. Runs mit `status="running"` und null `finished_at` haben `inferred_status="interrupted"`.
6. Ein zweiter Aufruf überschreibt die CSV korrekt (idempotent).
7. Der Stdout-Report stimmt mit dem manuellen Zählen überein.

---

## Lokale Ausführung nach Implementierung

```
julia experiments/aggregate.jl paper1_phaseA_v1
```
