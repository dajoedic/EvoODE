# EvoODE — Projekt-Tagebuch

Neueste Einträge zuerst. Aktueller Projektzustand: siehe `CLAUDE.md`.

---

## 2026-04-30

### `analysis/status.py` — Logdatei-Auswertung (WP4)
`<!-- hash folgt -->`

`status.py` um Auswertung der neuen `run.log`-Dateien (aus WP2) erweitert:

- `LOG_PATHS`-Dict: Skript → `run.log`-Pfad im jeweiligen OUT_DIR
- `read_log_markers()`: liest `=== Started/Finished at ===`-Marker aus Logdatei (letzte 500 Zeilen)
- `build_log_info()`: leitet ab ob letzter Run sauber beendet (`clean=True/False/None`)
- `print_known_scripts()`: zeigt Log-Zeile pro Skript (Start-/Endzeit, sauber/unterbrochen)
- WMI-Logik, Output-Timestamps und ETA-Berechnung vollständig erhalten

### Resume-Logik für `benchmark_evogrow.jl` (WP1) + Stdout-Logging (WP2)
`0c74f2d`

Benchmark konnte bisher nicht sicher gestoppt werden: `open(summary_file, "w")` überschrieb
die CSV bei jedem Start. Lösung:

- `seed`-Spalte in CSV eingeführt (Header + Row + Fehler-Record)
- `parse_csv_fields()`: korrekter CSV-Parser für Semikolon-Trenner mit Quote-Handling
- `load_done_set()`: liest existierende CSV und baut `Set{Tuple{String,Int,Int}}` aus `(variant_slug, id, seed)`
- `load_records_from_csv()`: lädt alle Rows für Aggregate nach Resume
- Hauptloop: Skip-Check vor jedem Run, Append-Mode wenn CSV existiert
- Einmalige Migration der bestehenden 140-Row-CSV: `seed`-Spalte per Positionszählung
  nachträglich eingetragen (Seeds-Reihenfolge ist deterministisch → sicher ableitbar)

### Repository-Strukturmigration (WP-R)
`706549f`

Alle drei laufenden Skripte gestoppt. Migration durchgeführt:

- `benchmarks/odeformer/` → `benchmarks/data/` (Datenpfade in beiden Benchmark-Skripten aktualisiert)
- `benchmarks/results/` → `outputs/benchmarks/` (OUT_DIR in `benchmark_evogrow.jl`)
- `generalization_study.jl` → `studies/generalization/`, OUT_DIR → `outputs/studies/generalization/`
- `profile_init.jl` → `studies/profiling/`, OUT_DIR → `outputs/studies/profiling/`
- `debug_single.jl` → `studies/debug/`, OUT_DIR → `outputs/studies/debug/`
- `.gitignore`: `outputs/` eingetragen
- Vorhandene Output-Daten nach `outputs/` kopiert (Resume-Kontinuität)
- `SCRIPTS.md` + `CLAUDE.md` aktualisiert

### Stdout-Logging in alle Skripte (WP2)
`0c74f2d`

Alle fünf Skripte schreiben jetzt `run.log` im jeweiligen OUT_DIR (Append-Modus):

- `=== Started at <ts> ===` / `=== Finished at <ts> ===` als Marker
- `log_println()` + `@logf`-Makro für formatierte Ausgaben
- Betrifft: `benchmark_evogrow.jl`, `studies/profiling/profile_init.jl`,
  `studies/generalization/generalization_study.jl`, `studies/debug/debug_single.jl`,
  `experiments/run_experiment.jl`
- Bestehender per-Run-Log-Mechanismus in `profile_init.jl` bleibt erhalten

---

## 2026-04-29

### `analysis/status.py` — Study Status Checker (Codex-Task)
`756b512`, `b94601f`

Ziel: Skript, das aus SCRIPTS.md alle bekannten Scripts extrahiert und prüft, welche davon gerade laufen.

**Technische Analyse (Windows/WMI):**

- `julia.exe`-Prozesse per PowerShell + WMI abfragbar
- Problem: Command Line von `julia.exe` enthält auf Windows oft keine Script-Argumente
- Wenn Parent-Prozess `julialauncher.exe` ist: Argumente im Parent sichtbar → Script identifizierbar
- Wenn Parent `cmd.exe` ist (auch wenn cmd noch offen): Argumente gehen verloren — gilt für alle über cmd gestarteten Skripte

**Lösung: Hybrid-Ansatz**

1. Prozessbaum: julialauncher.exe-Parent → Script-Name direkt lesbar
2. Output-File-Timestamp: wenn Output-Datei < 90 min alt und Orphan-Prozess läuft → `[LÄUFT?]`

**ETA-Schätzung:**

- Rate über letzte 20 Runs (nicht Gesamtlaufzeit) — robust gegen stuck runs
- Für Experiment-Runner: Rate aus `finished_at`-Timestamps der status.json-Dateien
- Für Benchmark: Rate aus `elapsed_s`-Spalte in summary.csv
- Stuck-Run-Erkennung wenn Run seit >2h im Status `running`

**Implementierung und Nachtrag:**

- `analysis/status.py` als standalone Python-Skript mit Standard Library umgesetzt
- `SCRIPTS.md` wird per Regex auf `julia <path>.jl`-Aufrufe in Codeblöcken geparst
- Output-Mapping hart codiert, aber ohne Experiment-ID-Hardcoding (`glob`-Patterns)
- Fortschritt/ETA implementiert für:
  - `experiments/run_experiment.jl`
  - `benchmarks/benchmark_evogrow.jl`
  - `profile_init.jl`
  - `generalization_study.jl`
- Stuck-Run-Warnung erkennt aktuell hängende `status.json`-Runs, z.B. alte Lorenz-Runs mit `status="running"`
- Fehler passiert: Datei war zunächst nur untracked und wurde dadurch bei Workspace-Cleanup/Refresh entfernt
- Fix: `analysis/status.py` aus der implementierten Version wiederhergestellt und mit `b94601f` committed, damit sie nicht erneut verloren geht

---

## 2026-04-28

### Experiment-Runner: zweiter Lorenz-3D-Run hängt
`57c4ff3`

Run `54_evogrow_v1_seed7` (Lorenz periodic, EvoGrow v1, Seed 7) läuft seit 2026-04-28T07:46 ohne Fortschritt.
Ursache: Run wurde mit Git-Hash `04f458a7` generiert — **vor** der BFGS-Timeout-Implementierung.
Der neue Timeout greift nicht rückwirkend auf Runs mit altem Config-Hash.

Experiment-Runner: 234 → 242/300 Runs abgeschlossen.
Benchmark `benchmark_evogrow.jl`: ~93 → ~128/300 Runs (~43%).
`profile_init.jl`: weiterhin hängend auf Level 11, Stage 2, Lorenz 3D, Seed 42 — Daten bereits vorhanden.

---

## 2026-04-27

### BFGS-Timeout implementiert (`src/optimize/bfgs.jl`)
`59d6c16`

**Motivation**: `profile_init.jl` hängt seit 48+ Stunden auf einem einzelnen BFGS-Call (Lorenz 3D, Stage 2). `maxiters` begrenzt nur Iterationen, nicht Wall-Clock-Zeit.

**Umsetzung:**
- `time_limit_s::Float64 = 300.0` zu `BFGSOptimizer` ergänzt
- `time_limit = opt.time_limit_s` an beide `Optimization.solve`-Aufrufe (BFGS + Nelder-Mead Fallback) übergeben
- Bei Timeout gibt Optim.jl das beste bisher gefundene Ergebnis zurück — kein Absturz, kein NaN
- Logging: `log_warn("BFGS hit time_limit", ...)` wenn `retcode != Success`

**Parameterwahl**: 300s ist ~100× der medianen per-Call-Zeit (ca. 2–3s), greift bei normalen Runs nie.

### Paper 1 Reproducibility Protocol dokumentiert
`844bbe4`

Vollständige Dokumentation der Paper-1-Konfiguration direkt aus dem Code abgeleitet:
- alle 6 Varianten mit Slug, Basis, Progressions- und Usage-Mode
- alle 10 Benchmark-Systeme (exakt/Surrogate) mit IDs und True-Struktur
- sämtliche Hyperparameter explizit
- Seeds, Metriken, Execution-Loop, Output-Artefakte, Aggregationsregeln, Freeze-Klausel

Dabei 5 Diskrepanzen zwischen Dokumentation und Codebasis gefunden und behoben:
1. `EvoGrow`-Struct fehlte `progression`, `usage`, `use_pretuning`
2. `test.jl` und `test_evogrow_v2_lotka.jl` im Dateibaum, existieren nicht mehr
3. `run_odebench.jl` als Root-Datei angegeben, liegt in `benchmarks/`
4. `src/optimize/pretune.jl` existiert und wird genutzt, war undokumentiert
5. `experiments/` fehlte komplett im Dateibaum

### Experiment-Status (Stichtag 27.04.)

| Skript | Status |
|--------|--------|
| `experiments/run_experiment.jl paper1_phaseA_v1` | läuft — 234/300, ~6–7h Restlaufzeit |
| `benchmarks/benchmark_evogrow.jl` | läuft — 93/300, ~27–40h Restlaufzeit |
| `generalization_study.jl` | fertig (Output-CSVs vorhanden, 24.04.) |
| `profile_init.jl` | hängt seit 2 Tagen — Level 11, Stage 2, Lorenz 3D, Seed 42 |

---

## 2026-04-26

### Repository-Housekeeping
`1f9c643`

- `benchmarks/odeformer/results/` entfernt: alte Ergebnisdateien ohne reproduzierbaren Kontext
- `.gitignore` um `benchmarks/odeformer/results/` ergänzt

### Analyse-Pipeline für Paper 1 angelegt
`6eab0cf`, `ea3cc44`, `053d717`, `c1f51ef`, `0f8e677`, `8c1152d`, `d983abf`

- `analysis/` als dedizierter Bereich für Python-Auswertung angelegt
- `analysis/CONVENTIONS.md`: Architektur- und Regelwerk für die Python-Analyse
- `analysis/utils/`: `io.py`, `metrics.py`, `style.py` (Variant-Farben und Labels)
- `analysis/scripts/aggregate/aggregate_run_registry.py`: liest `run_registry.csv`, schreibt `aggregate_by_variant_system.csv`
- `analysis/scripts/plot/plot_exact_match_rates.py`: Exact-Match-Rate-Plot
- `analysis/scripts/plot/plot_stage_overshoot.py`: Stage-Overshoot-Plot (GP ausgeschlossen)
- `analysis/scripts/plot/table_main_results.py`: LaTeX-Tabelle Main Results

### Paper-1-Protokoll eingefroren (`docs/paper1_study_protocol.md`)
`2e65d57`, `9ca633a`, `c810703`

Core Goal: Paper 1 untersucht staged growth als Mechanismus zur kontrollierten Komplexitätssteigerung — nicht "bestes ODE-Discovery-System".

Hypothesen:
- H1: Stage-local v2.2 zeigt niedrigeren `mean_stage_overshoot` als v2.1 und v1
- H2: v2.2 liefert kompetitive `exact_match_rate` bei niedrigerem Complexity-Efficiency-Cost
- H3: `mean_wasted_levels` nur zwischen EvoGrow-Varianten; GP ausgeschlossen
- H4: usage-policy comparison (`hard`, `soft`, `passive`) als sekundäre Hypothese

Evidenzregeln:
- Surrogate-Systeme nicht für `exact_support_match` oder H1–H4-Strukturaussagen
- Systeme 2 und 24 (expected_stage=1) aus H1/H3/H4 ausgeschlossen
- No post-hoc cherry-picking; keine neuen Runs nach Ergebnisinspektion

### Variant-Slug vereinheitlicht
`9d25f44`

`evogrow_v2_2_stage_local` überall standardisiert: `benchmark_evogrow.jl`, Analyse-Skripte, `style.py`, Dokumentation.

### Logging: Datum im Timestamp ergänzt
`035e354`

`src/utils/logging.jl`: Timestamp-Format von `HH:MM:SS` auf `yyyy-mm-dd HH:MM:SS` erweitert.
Grund: über Nacht laufende Skripte erzeugen sonst Logs ohne Datumszuordnung.

---

## 2026-04-23

### Bugs gefunden und gefixt
`d27b697`

**Bug 1: `PolynomialBasis` fehlte kubischer Term für System 11**
- `evogrow_v1` nutzte `PolynomialBasis` (nur bis Grad 2), System 11 (Critical slowing down) erwartet `u1^3`
- Entscheidung: `evogrow_v1` auf `default_staged_polynomial_basis` umgestellt — gleicher Suchraum wie alle anderen Varianten, alles sofort entsperrt

**Bug 2: `log_exception` speicherte `DataType` statt `String`**
- `merged[:exception_type] = typeof(err)` schlug fehl weil `Dict{Symbol,String}` keinen `DataType` akzeptiert
- Fix: `string(typeof(err))` in `src/utils/logging.jl`

### Generalisierungsstudie geplant und implementiert (`generalization_study.jl`)
`f30af7c`

Frage: Wenn EvoODE auf Parametersatz A die korrekte Struktur findet — passt diese Struktur nach reinem Parameter-Refit auch auf ungesehene Parametersätze B–E derselben ODE-Familie?

- 3 Systeme (Logistic growth, Lotka-Volterra, SIR), je 5 Parametersätze (1 Train + 4 Test)
- 2 Varianten (evogrow_v2_2_stage_local, gp_baseline), 3 Seeds
- Baseline: frischer Discovery direkt auf Testtrajektorie
- Output: `debug_results/generalization_study/generalization_summary.csv`, `generalization_detail.csv`

### Erste Experiment-Befunde (paper1_phaseA_v1, ~40/300 Runs)

Bisher abgeschlossen: System 2 (Population growth) und System 3 (Logistic growth).

- Alle Runs: `success=true`, `exact_support_match=true`
- Loss ist deterministisch: identisch über alle Seeds (Pretuning + BFGS konvergiert immer ins gleiche Minimum)
- **Stage Overshoot:**
  - `evogrow_v2_1` (global plateau): mittlerer Overshoot 1.5 auf System 3 (expected_stage=2, landet in Stage 3–4)
  - Alle v2.2-Varianten (stage_local): Overshoot 0 — bleiben korrekt in Stage 2
  - Direkte Bestätigung der Kernhypothese

---

## 2026-04-22

### Pretuning (OLS Warm-Start)
`c4fad8a`

- `src/optimize/pretune.jl`: Ableitung per finite Differenzen, Design-Matrix aus Basistermen, OLS-Lösung als BFGS-Startwert
- `use_pretuning::Bool`-Flag in `EvoGrow`
- `level_log` um `elapsed_s`-Feld erweitert

### Experiment-Infrastruktur (WP-E1 bis WP-E3)
`c4fad8a`

- `experiments/generate_manifest.jl`: erzeugt Experiment-Verzeichnis, `manifest.json`, alle per-Run `config.json` + `status.json`
- `experiments/run_experiment.jl`: sequentieller Runner mit robustem Fehlerhandling, atomaren Writes, restart-fähig
- `experiments/aggregate.jl`: leitet `run_registry.csv` aus per-Run-Ordnern ab, idempotent
- Per-Run-Dateiprotokoll: `config.json` (immutable), `status.json` (non-atomic), `result.json` + `metrics.json` (atomar via tmp→rename)

### Debug- und Profiling-Skripte
`c4fad8a`

- `debug_single.jl`: Einzelrun auf Lotka-Volterra mit verbose Logging und PNG-Output
- `profile_init.jl`: Vergleich random vs. pretune Initialisierung auf Lotka-Volterra + Lorenz, 3 Seeds

### Experiment gestartet

`paper1_phaseA_v1`: 10 Systeme × 6 Varianten × 5 Seeds = 300 Runs, exploratory

---

## 2026-04-21

### EvoGrow v2.2 (stage_local)
`224714d`

- `StageProgressionPolicy` mit Modus `:stage_local` und `min_levels_per_stage`
- `StageUsagePolicy` mit Modi `:hard`, `:soft`, `:passive` und `new_term_bias_prob`
- Stage-lokale Plateau-Detektion mit Mindestbudget pro Stage
- Benchmark-Matrix: 10 Systeme × 6 Varianten × 5 Seeds vollständig

---

## 2026-04-20

### Projekt-Fundament
`84f94e8`, `4d8bd2e`, `f5e1d9c`, `a811927`

- Core stabilisiert: EvoGrow und GP laufen sauber mit konsistentem Loss (`discover()` end-to-end)
- Benchmark-Infrastruktur angelegt: 10-System-Suite, erste Varianten
- Housekeeping: Stubs gefixt, Docstrings, Interface-Bereinigung

---
