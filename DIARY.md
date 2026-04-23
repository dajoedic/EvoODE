# EvoODE — Projekt-Tagebuch

Chronologischer Log abgeschlossener Arbeit, Befunde und Entscheidungen.
Aktueller Projektzustand: siehe `CLAUDE.md`.

---

## 2026-04-20

**Projekt-Fundament**
- Core stabilisiert: EvoGrow und GP laufen sauber mit konsistentem Loss (`discover()` end-to-end)
- Benchmark-Infrastruktur angelegt: 10-System-Suite, erste Varianten
- Housekeeping: Stubs gefixt, Docstrings, Interface-Bereinigung
- `CLAUDE.md` als einzige Planungsdatei konsolidiert

## 2026-04-21

**EvoGrow v2.2 (stage_local)**
- `StageProgressionPolicy` mit Modus `:stage_local` und `min_levels_per_stage`
- `StageUsagePolicy` mit Modi `:hard`, `:soft`, `:passive` und `new_term_bias_prob`
- Stage-lokale Plateau-Detektion mit Mindestbudget pro Stage
- Benchmark-Matrix: 10 Systeme × 6 Varianten × 5 Seeds vollständig

## 2026-04-22

**Pretuning (OLS Warm-Start)**
- `src/optimize/pretune.jl`: Ableitung per finite Differenzen, Design-Matrix aus Basistermen, OLS-Lösung als BFGS-Startwert
- Steuerbares `use_pretuning::Bool`-Flag in `EvoGrow`
- `level_log` um `elapsed_s`-Feld erweitert

**Experiment-Infrastruktur (WP-E1 bis WP-E3)**
- `experiments/generate_manifest.jl`: erzeugt Experiment-Verzeichnis, `manifest.json`, alle per-Run `config.json` + `status.json`
- `experiments/run_experiment.jl`: sequentieller Runner mit robustem Fehlerhandling, atomaren Writes, restart-fähig
- `experiments/aggregate.jl`: leitet `run_registry.csv` aus per-Run-Ordnern ab, idempotent
- Per-Run-Dateiprotokoll: `config.json` (immutable), `status.json` (non-atomic), `result.json` + `metrics.json` (atomar via tmp→rename)

**Debug- und Profiling-Skripte**
- `debug_single.jl`: Einzelrun auf Lotka-Volterra mit verbose Logging und PNG-Output
- `profile_init.jl`: Vergleich random vs. pretune Initialisierung auf Lotka-Volterra + Lorenz, 3 Seeds

**Aufräumen**
- Obsolete Testskripte gelöscht (`test.jl`, `test_evogrow_v2_lotka.jl`, `test_evogrow_v2_2_semantics.jl`)
- `run_odebench.jl` nach `benchmarks/` verschoben
- `SCRIPTS.md` angelegt: praktisches Runbook für alle Skripte
- `codex/CURRENT_TASK.md` als einzige überschreibbare Codex-Instruktionsdatei etabliert

**Experiment gestartet**
- `paper1_phaseA_v1`: 10 Systeme × 6 Varianten × 5 Seeds = 300 Runs, exploratory

---

## 2026-04-23

### Bugs gefunden und gefixt

**Bug 1: `PolynomialBasis` fehlte kubischer Term für System 11**
- `evogrow_v1` nutzte `PolynomialBasis` (nur bis Grad 2), System 11 (Critical slowing down) erwartet `u1^3`
- `expected_active_idxs` warf `KeyError` beim Lookup des fehlenden Terms
- Entscheidung: `evogrow_v1` auf `default_staged_polynomial_basis` umgestellt — gleiche Termmenge wie alle anderen Varianten, alles sofort entsperrt. Fairer Vergleich: gleicher Suchraum, andere Strategie.
- Geändert: `experiments/run_experiment.jl`, `benchmarks/benchmark_evogrow.jl`, `CLAUDE.md`

**Bug 2: `log_exception` speicherte `DataType` statt `String`**
- `merged[:exception_type] = typeof(err)` schlug fehl weil `Dict{Symbol,String}` keinen `DataType` akzeptiert
- Fix: `string(typeof(err))` in `src/utils/logging.jl`
- Latenter Bug: wäre bei jeder Exception aufgetreten, nicht nur bei Bug 1

### Neue Studie geplant und beauftragt

**WP-G1: Strukturgeneralisierungs-Studie** (`generalization_study.jl`)
- Frage: Wenn EvoODE auf Parametersatz A die korrekte Struktur findet — passt diese Struktur nach reinem Parameter-Refit auch auf ungesehene Parametersätze B–E derselben ODE-Familie?
- 3 Systeme (Logistic growth, Lotka-Volterra, SIR), je 5 Parametersätze (1 Train + 4 Test)
- 2 Varianten (evogrow_v2_2_stage_local, gp_baseline), 3 Seeds
- Baseline: frischer Discovery direkt auf Testtrajektorie
- Kein Core-Code-Eingriff, standalone Skript

### Dokumentation

- `DIARY.md` angelegt (dieses Dokument)
- `CLAUDE.md`: "Active Studies"-Tabelle mit Kernthesen aller laufenden Skripte ergänzt

### Erste Experiment-Befunde (paper1_phaseA_v1, nach ~40/300 Runs)

Bisher abgeschlossen: System 2 (Population growth) und System 3 (Logistic growth).

- Alle Runs: `success=true`, `exact_support_match=true` — beide einfachen Systeme zuverlässig gefunden
- Loss ist deterministisch: identisch über alle Seeds (Pretuning + BFGS konvergiert immer ins gleiche Minimum)
- **Erster interessanter Befund — Stage Overshoot:**
  - `evogrow_v2_1` (global plateau): mittlerer Overshoot 1.5 auf System 3 (expected_stage=2, landet in Stage 3–4)
  - Alle v2.2-Varianten (stage_local): Overshoot 0 — bleiben korrekt in Stage 2
  - Direkte Bestätigung der Kernhypothese: stage-lokale Progression verhindert unnötiges Weitersuchen

---
