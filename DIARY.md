# EvoODE — Projekt-Tagebuch

Neueste Einträge zuerst. Aktueller Projektzustand: siehe `CLAUDE.md`.

---

## 2026-04-26

### Repository-Housekeeping und Ordnerstruktur

**Alte ODEFormer-Run-Artefakte entfernt**
- `benchmarks/odeformer/results/` aus dem Repository entfernt: alte uncommitted Ergebnisdateien ohne reproduzierbaren Kontext
- `.gitignore` um `benchmarks/odeformer/results/` ergänzt, damit diese generierten Dateien nicht wieder versehentlich committed werden
- Ergebnis: Benchmark-Daten (`strogatz_extended.json`) bleiben versioniert, alte Output-Artefakte sind raus

**Neue Struktur für Analyse und Paper-Artefakte**
- `analysis/` als dedizierter Bereich für Python-Auswertung angelegt
- `paper/` als dedizierter Bereich für eingefrorene Paper-Artefakte angelegt
- Initiale Skeletons:
  - `analysis/requirements.txt`
  - `analysis/paper1/.gitkeep`
  - `analysis/exploratory/.gitkeep`
  - `paper/figures/.gitkeep`
  - `paper/tables/.gitkeep`
  - `paper/snapshots/.gitkeep`
- Danach Analyse-Struktur erweitert:
  - `analysis/configs/`
  - `analysis/data/`
  - `analysis/figures/`
  - `analysis/notebooks/`
  - `analysis/scripts/aggregate/`
  - `analysis/scripts/plot/`
  - `analysis/tables/`
  - `analysis/utils/`
- `.gitignore` um Python- und Analyse-Artefakte ergänzt:
  - `analysis/.venv/`
  - `analysis/__pycache__/`
  - `**/*.pyc`
  - `analysis/data/`
  - `analysis/figures/`
  - `analysis/tables/`
  - `analysis/notebooks/.ipynb_checkpoints/`

### Analyse-Pipeline für Paper 1 angelegt

**Konventionen und Aufgabenstruktur**
- `analysis/CONVENTIONS.md` als zentrale Architektur- und Regeldatei für die Python-Analyse angelegt
- Trennung festgelegt:
  - Julia schreibt Rohdaten in `experiments/`
  - Python liest Rohdaten und erzeugt abgeleitete Daten, Figuren und Tabellen
  - generierte Analyse-Artefakte bleiben aus Git raus
- `codex/CURRENT_TASK_ANALYSIS.md` als separate Task-Datei für Python-/Analyse-Arbeiten etabliert
- `codex/PENDING_REPO_MIGRATION.md` angelegt: spätere Repo-Migrationen (u.a. `studies/`) dokumentiert, aber blockiert bis laufende Runs fertig sind

**Shared Python Utilities**
- `analysis/utils/io.py`: gemeinsames Laden von CSV-Dateien
- `analysis/utils/metrics.py`: Validitätsfilter (`loss` nicht NaN) und Pflichtspaltenprüfung
- `analysis/utils/style.py`: feste Variant-Reihenfolge, Labels und Farben für Paper-1-Plots
- `analysis/utils/__init__.py` ergänzt

**Aggregation**
- `analysis/configs/paper1_phaseA_v1.json` angelegt
- `analysis/scripts/aggregate/aggregate_run_registry.py` implementiert
- Aggregation liest `experiments/paper1_phaseA_v1/run_registry.csv` und schreibt:
  - `analysis/data/paper1_phaseA_v1/aggregate_by_variant_system.csv`
- Aggregierte Kennzahlen pro `(variant_slug, system_id)`:
  - `n_seeds`
  - `n_valid`
  - `mean_loss`
  - `std_loss`
  - `exact_match_rate`
  - `mean_final_stage`
  - `mean_stage_overshoot`
  - `mean_wasted_levels`
  - `mean_elapsed_s`
  - `mean_invalid_evals`
- Wichtig: gültige Runs sind Analyse-seitig definiert als Runs mit nicht-NaN `loss`

**Plot- und Tabellen-Skripte**
- `analysis/scripts/plot/plot_exact_match_rates.py`
  - erzeugt Exact-Match-Rate-Plot für `paper1_phaseA_v1`
  - nutzt feste Variant-Reihenfolge und konsistente Farben
- `analysis/scripts/plot/plot_stage_overshoot.py`
  - erzeugt Stage-Overshoot-Plot
  - GP wird aus Stage-Metriken ausgeschlossen, weil GP keine Stage-Struktur hat
- `analysis/scripts/plot/table_main_results.py`
  - erzeugt LaTeX-Tabelle für die Main Results
  - nutzt aggregierte Paper-1-Daten statt manuell bearbeiteter CSVs

### Paper-1-Protokoll eingefroren

**`docs/paper1_study_protocol.md` angelegt und gehärtet**
- Standalone-Protokoll für Paper 1 erstellt; bewusst redundant zu `CLAUDE.md`, damit Paper-Ergebnisse eigenständig nachvollziehbar sind
- Core Goal festgelegt:
  - Paper 1 ist nicht "best ODE discovery system"
  - Paper 1 untersucht staged growth als Mechanismus zur kontrollierten Komplexitätssteigerung
- Hauptclaim definiert:
  - stage-local stopping reduziert Stage-Overshoot und wasted search levels, ohne Recovery-Qualität systematisch zu opfern
- Begriff **complexity efficiency** präzisiert:
  - gemeinsame Betrachtung von `stage_overshoot` und `wasted_levels`
  - niedrigere Werte bedeuten effizientere Nutzung des Suchbudgets

**Hypothesen und Claims geschärft**
- H1: Stage-local v2.2 soll niedrigeren `mean_stage_overshoot` zeigen als v2.1 und v1
- H2: v2.2 soll kompetitive `exact_match_rate` liefern, aber gemeinsam mit niedrigerem Complexity-Efficiency-Cost bewertet werden
- H3: `mean_wasted_levels` nur zwischen EvoGrow-Varianten vergleichen; GP explizit ausgeschlossen
- H4: usage-policy comparison (`hard`, `soft`, `passive`) als sekundäre Hypothese markiert
- GP aus allen Stage-Metriken entfernt, weil `final_stage`, `stage_overshoot` und `wasted_levels` für GP methodisch nicht definiert sind

**System- und Evidenzregeln festgelegt**
- 10 Systeme in zwei Kategorien getrennt:
  - 8 exakt darstellbare Systeme
  - 2 Surrogate-Systeme (`Overdamped pendulum`, `Van der Pol`)
- Surrogate-Systeme dürfen nicht für `exact_support_match` oder H1-H4-Strukturaussagen verwendet werden
- Systeme 2 und 24 bleiben Sanity Checks und werden aus H1/H3/H4 ausgeschlossen, weil `expected_stage = 1`
- No post-hoc cherry-picking:
  - keine manuell editierten CSVs
  - keine neuen Paper-1-Experimente nach Ergebnisinspektion
  - keine Resultate ohne Trace auf Hypothese, Experiment und definierte Metrik

**Figures und Tables formalisiert**
- Maximal 3 Main-Paper-Figures:
  - Figure 1: Exact Match Rate
  - Figure 2: Stage Overshoot
  - Figure 3: qualitative Stage-Progression-Trace für System 3, Seed 42
- Figure 3 ausdrücklich als illustrative Einzelfallgrafik definiert, nicht als quantitative Evidenz
- Main-Paper-Tabellen begrenzt auf:
  - Table 1: Main results / exact systems
  - Table 2: Stage overshoot + wasted levels
- Generalization Study als auxiliary evidence eingeordnet:
  - nur Runs mit `exact_support_match = true`
  - eine supplementary table
  - keine Hauptclaim-Stütze, keine Behauptung "besser als GP/SINDy"

### Projekt-Dokumentation aktualisiert

**`CLAUDE.md` erweitert**
- Projektstruktur auf den neuen Stand gebracht:
  - `docs/`
  - `analysis/`
  - getrennte Codex-Task-Dateien
  - geplantes `studies/` als noch nicht existierender Migrationszielordner
- `docs/paper1_study_protocol.md` als bewusst eigenständiges Companion-Dokument dokumentiert
- `analysis/CONVENTIONS.md` als Source of Truth für Python-Analyse verlinkt
- `benchmarks/` vs. `experiments/` klarer abgegrenzt
- aktuelle Paper-1-Analyse-Skripte in der Projektstruktur ergänzt

**`SCRIPTS.md` ergänzt**
- Pfade für Debug-/Profiling-Outputs aktualisiert
- `generalization_study.jl` als eigenes Skript mit Zweck und Output-Artefakten dokumentiert

**Variant-Slug vereinheitlicht**
- Der Slug `evogrow_v2_2_stage_local` wurde überall standardisiert
- Betroffene Stellen:
  - `CLAUDE.md`
  - `docs/paper1_study_protocol.md`
  - `benchmarks/benchmark_evogrow.jl`
  - Analyse-Plot- und Tabellen-Skripte
  - `analysis/utils/style.py`
- Ziel: keine Vermischung mehr zwischen "progression-only" als Label und `stage_local` als maschinenlesbarem Slug

### Logging verbessert

**WP-LOG1: Datum im Logging-Timestamp ergänzt**
- `src/utils/logging.jl`: zentraler Logger schreibt Timestamp nun mit Datum und Uhrzeit
- Vorher: `HH:MM:SS`
- Nachher: `yyyy-mm-dd HH:MM:SS`
- Grund: über Nacht laufende Skripte erzeugen sonst Logs, bei denen ältere Einträge keinem Datum zugeordnet werden können
- Testaufruf von `log_info("test")` erzeugte z.B.:
  - `[2026-04-26 20:34:24 | 0.2s | INFO ] test`

### Tagesabschluss

- Alle heutigen Implementierungs- und Dokumentationsänderungen vor diesem Diary-Nachtrag sind committed
- Paper-1-Protokoll ist als Arbeitsgrundlage eingefroren
- Python-Analysepipeline ist vorbereitet:
  - Aggregation
  - Exact-Match-Plot
  - Stage-Overshoot-Plot
  - Main-Results-LaTeX-Tabelle
- Nächster sinnvoller Schritt:
  - Phase-A-Ergebnisse vollständig aggregieren
  - `aggregate_by_variant_system.csv` prüfen
  - H1-H3 direkt aus den aggregierten Daten bewerten, bevor finale Figuren/Tables als Paper-Artefakte eingefroren werden

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

### Neue Studie geplant und implementiert

**WP-G1: Strukturgeneralisierungs-Studie** (`generalization_study.jl`)
- Frage: Wenn EvoODE auf Parametersatz A die korrekte Struktur findet — passt diese Struktur nach reinem Parameter-Refit auch auf ungesehene Parametersätze B–E derselben ODE-Familie?
- 3 Systeme (Logistic growth, Lotka-Volterra, SIR), je 5 Parametersätze (1 Train + 4 Test)
- 2 Varianten (evogrow_v2_2_stage_local, gp_baseline), 3 Seeds
- Baseline: frischer Discovery direkt auf Testtrajektorie
- Output: `debug_results/generalization_summary.csv`, `debug_results/generalization_detail.csv`

### Dokumentation

- `DIARY.md` angelegt (dieses Dokument)
- `SCRIPTS.md` angelegt: praktisches Runbook für alle Skripte
- `codex/CURRENT_TASK.md` als einzige überschreibbare Codex-Instruktionsdatei etabliert
- `CLAUDE.md`: "Active Studies"-Tabelle mit Kernthesen aller laufenden Skripte ergänzt

### Erste Experiment-Befunde (paper1_phaseA_v1, nach ~40/300 Runs)

Bisher abgeschlossen: System 2 (Population growth) und System 3 (Logistic growth).

- Alle Runs: `success=true`, `exact_support_match=true` — beide einfachen Systeme zuverlässig gefunden
- Loss ist deterministisch: identisch über alle Seeds (Pretuning + BFGS konvergiert immer ins gleiche Minimum)
- **Erster interessanter Befund — Stage Overshoot:**
  - `evogrow_v2_1` (global plateau): mittlerer Overshoot 1.5 auf System 3 (expected_stage=2, landet in Stage 3–4)
  - Alle v2.2-Varianten (stage_local): Overshoot 0 — bleiben korrekt in Stage 2
  - Direkte Bestätigung der Kernhypothese: stage-lokale Progression verhindert unnötiges Weitersuchen

### Tagesabschluss — laufende Experimente

Vier Skripte laufen parallel über Nacht:
- `experiments/run_experiment.jl paper1_phaseA_v1` — 300 Runs, Hauptexperiment Paper 1
- `generalization_study.jl` — Strukturgeneralisierungs-Studie
- sowie weitere laufende Profiling-Skripte

Codebase ist sauber committed. Nächster Schritt: Ergebnisse analysieren wenn Runs durch sind.

---

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

**Experiment gestartet**
- `paper1_phaseA_v1`: 10 Systeme × 6 Varianten × 5 Seeds = 300 Runs, exploratory

---

## 2026-04-21

**EvoGrow v2.2 (stage_local)**
- `StageProgressionPolicy` mit Modus `:stage_local` und `min_levels_per_stage`
- `StageUsagePolicy` mit Modi `:hard`, `:soft`, `:passive` und `new_term_bias_prob`
- Stage-lokale Plateau-Detektion mit Mindestbudget pro Stage
- Benchmark-Matrix: 10 Systeme × 6 Varianten × 5 Seeds vollständig

---

## 2026-04-20

**Projekt-Fundament**
- Core stabilisiert: EvoGrow und GP laufen sauber mit konsistentem Loss (`discover()` end-to-end)
- Benchmark-Infrastruktur angelegt: 10-System-Suite, erste Varianten
- Housekeeping: Stubs gefixt, Docstrings, Interface-Bereinigung
- `CLAUDE.md` als einzige Planungsdatei konsolidiert

---
