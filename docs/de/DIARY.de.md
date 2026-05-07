# EvoODE - Projekt-Tagebuch

Deutsche Lesefassung/Kopie von `DIARY.md`.

Neueste Einträge zuerst. Aktueller Projektzustand: siehe `CLAUDE.md`.

---

## 2026-05-08

### paper1_phaseA_v1 vollständig abgeschlossen

`experiments/run_experiment.jl paper1_phaseA_v1` hat alle 300 Runs erfolgreich durchlaufen (300/300, alle `success=true`, 0 failed, 0 interrupted). Gesamtlaufzeit ca. 4,5 Tage.

Aggregation: `julia experiments/aggregate.jl paper1_phaseA_v1` → `run_registry.csv` (300 Zeilen).
Python-Pipeline: `aggregate_run_registry.py` → `data/paper1_phaseA_v1/aggregate_by_variant_system.csv` (60 Zeilen, 6 Varianten × 10 Systeme, alle Zellen vollständig).

### Erste vollständige Auswertung: paper1_phaseA_v1

**Exact Match:**

- Systeme 2, 3, 24: alle EvoGrow-Varianten `exact_match=1.0`
- GP auf System 24 (harmonischer Oszillator, 2D linear): `exact_match=0`, Loss ~4,5e-3 gegenüber EvoGrow 5,4e-14 — dramatischer Unterschied auf dem einfachsten 2D-linearen System
- System 11 (`du = -u³`, Stage 4): alle EvoGrow-Varianten `exact_match=0` trotz Loss ~4,4e-15 — Bug in `exact_support_match` vermutet; GP hingegen `exact_match=1.0`
- Systeme 26, 31, 54, 63: `exact_match=0` für alle Varianten — kein exakter Strukturfund bei Stage-3-Systemen

**Loss EvoGrow vs. GP auf höherdimensionalen Systemen:**

| System | Beste EvoGrow | GP | Faktor |
|--------|--------------|-----|--------|
| 31 SIR | 7,0e-05 | 0,314 | ~4.500× |
| 54 Lorenz | 7,4e-04 | 0,921 | ~1.200× |
| 26 Lotka-Volterra | 2,5e-04 | 2,98e-03 | ~12× |

GP versagt auf gekoppelten Systemen deutlich — stärkstes Argument für EvoGrow.

**Stage Overshoot (Kernhypothese):**

- **System 54 (Lorenz):** v1 = +2, v2.1 = +1,6, alle v2.2 = 0 Overshoot, 0 Wasted Levels → klarste Bestätigung der Kernhypothese
- **System 3 (Logistic):** v1 = 0 (flache Basis, keine Stage-Promotions), alle v2.x = +3 Overshoot — v2.2_stage_local erhöht Wasted Levels auf 12 durch Mindestbudget-Mechanismus
- **Systeme 26, 31, 63:** alle Varianten +2 Overshoot — kein Differenzierungssignal zwischen den Varianten

**Offene Fragen:**
- `exact_support_match`-Bug bei System 11 untersuchen (Loss ~0, aber kein Match)
- Warum versagt GP auf System 24 (harmonischer Oszillator)?
- Kein Stage-3-System hat exact match → algorithmisches Problem oder zu strenges Loss-Toleranzkriterium?
- Kein Run konvergiert auf `loss_tol=1e-8` außer Systeme 2 und 24 → Stopp-Mechanismus greift ausschließlich über Level-Budget, nie über Loss-Toleranz

### WP3: Frame Layout Redesign (search_animation.jl)

`render_frame` auf Zweispalten-Layout umgestellt: linke Spalte = Trajektorien-Subplots, rechte Spalte = Info-Panel (Loss, entdeckte Gleichungen, wahre Gleichungen, farbige Legende). Aktuelle Level-Kandidaten in Orange, Historie in Grau. `plot_title` über allen Subplots. Koeffizientenformat in `structure_to_string` auf `%.3f` geändert.

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
- `codex/PENDING_REPO_MIGRATION.md` angelegt: spätere Repo-Migrationen, unter anderem `studies/`, dokumentiert, aber blockiert bis laufende Runs fertig sind

**Shared Python Utilities**
- `analysis/utils/io.py`: gemeinsames Laden von CSV-Dateien
- `analysis/utils/metrics.py`: Validitätsfilter (`loss` nicht NaN) und Pflichtspaltenprüfung
- `analysis/utils/style.py`: feste Variant-Reihenfolge, Labels und Farben für Paper-1-Plots
- `analysis/utils/__init__.py` ergänzt

**Aggregation**
- `analysis/configs/paper1_phaseA_v1.json` angelegt
- `analysis/scripts/aggregate/aggregate_run_registry.py` implementiert
- Aggregation liest `experiments/paper1_phaseA_v1/run_registry.csv` und schreibt `analysis/data/paper1_phaseA_v1/aggregate_by_variant_system.csv`
- Aggregierte Kennzahlen: `n_seeds`, `n_valid`, `mean_loss`, `std_loss`, `exact_match_rate`, `mean_final_stage`, `mean_stage_overshoot`, `mean_wasted_levels`, `mean_elapsed_s`, `mean_invalid_evals`
- Gültige Runs sind Analyse-seitig Runs mit nicht-NaN `loss`

**Plot- und Tabellen-Skripte**
- `analysis/scripts/plot/plot_exact_match_rates.py`: Exact-Match-Rate-Plot
- `analysis/scripts/plot/plot_stage_overshoot.py`: Stage-Overshoot-Plot, GP aus Stage-Metriken ausgeschlossen
- `analysis/scripts/plot/table_main_results.py`: LaTeX-Tabelle für Main Results

### Paper-1-Protokoll eingefroren

**`docs/paper1_study_protocol.md` angelegt und gehärtet**
- Standalone-Protokoll für Paper 1 erstellt; bewusst redundant zu `CLAUDE.md`
- Core Goal: Paper 1 ist nicht "best ODE discovery system"
- Paper 1 untersucht staged growth als Mechanismus zur kontrollierten Komplexitätssteigerung
- Hauptclaim: stage-local stopping reduziert Stage-Overshoot und wasted search levels, ohne Recovery-Qualität systematisch zu opfern
- **complexity efficiency** als gemeinsame Betrachtung von `stage_overshoot` und `wasted_levels` präzisiert

**Hypothesen und Claims geschärft**
- H1: Stage-local v2.2 soll niedrigeren `mean_stage_overshoot` zeigen als v2.1 und v1
- H2: v2.2 soll kompetitive `exact_match_rate` liefern und niedrigere Complexity-Efficiency-Kosten haben
- H3: `mean_wasted_levels` nur zwischen EvoGrow-Varianten vergleichen; GP ausgeschlossen
- H4: Usage-Policy-Vergleich (`hard`, `soft`, `passive`) als sekundäre Hypothese
- GP aus allen Stage-Metriken entfernt, weil diese methodisch nicht definiert sind

**System- und Evidenzregeln**
- 10 Systeme in 8 exakt darstellbare und 2 Surrogate-Systeme getrennt
- Surrogate-Systeme dürfen nicht für `exact_support_match` oder H1-H4-Strukturaussagen verwendet werden
- Systeme 2 und 24 bleiben Sanity Checks und werden aus H1/H3/H4 ausgeschlossen
- Keine manuell editierten CSVs, keine post-hoc Paper-1-Experimente, keine Resultate ohne Trace auf Hypothese, Experiment und Metrik

**Figures und Tables formalisiert**
- Maximal 3 Main-Paper-Figures: Exact Match Rate, Stage Overshoot, qualitative Stage-Progression-Trace für System 3
- Figure 3 ist ausdrücklich illustrativ, nicht quantitative Evidenz
- Main-Paper-Tabellen: Main results / exact systems und Stage overshoot + wasted levels
- Generalization Study ist auxiliary evidence, nicht Hauptclaim-Stütze

### Projekt-Dokumentation aktualisiert

**`CLAUDE.md` erweitert**
- Projektstruktur aktualisiert: `docs/`, `analysis/`, getrennte Codex-Task-Dateien, geplantes `studies/`
- `docs/paper1_study_protocol.md` als eigenständiges Companion-Dokument dokumentiert
- `analysis/CONVENTIONS.md` verlinkt
- `benchmarks/` vs. `experiments/` klarer abgegrenzt
- Paper-1-Analyse-Skripte ergänzt

**`SCRIPTS.md` ergänzt**
- Pfade für Debug-/Profiling-Outputs aktualisiert
- `generalization_study.jl` mit Zweck und Output-Artefakten dokumentiert

**Variant-Slug vereinheitlicht**
- `evogrow_v2_2_stage_local` überall standardisiert
- Betroffen: `CLAUDE.md`, Paper-Protokoll, Benchmark, Analyse-Skripte, `analysis/utils/style.py`

### Logging verbessert

**WP-LOG1: Datum im Logging-Timestamp ergänzt**
- `src/utils/logging.jl`: zentraler Logger schreibt Timestamp nun mit Datum und Uhrzeit
- Vorher: `HH:MM:SS`
- Nachher: `yyyy-mm-dd HH:MM:SS`
- Grund: über Nacht laufende Skripte erzeugen sonst Logs ohne eindeutiges Datum
- Beispiel: `[2026-04-26 20:34:24 | 0.2s | INFO ] test`

### Tagesabschluss

- Alle Implementierungs- und Dokumentationsänderungen vor dem Diary-Nachtrag sind committed
- Paper-1-Protokoll ist als Arbeitsgrundlage eingefroren
- Python-Analysepipeline ist vorbereitet
- Nächster sinnvoller Schritt: Phase-A-Ergebnisse aggregieren, Aggregate-CSV prüfen, H1-H3 direkt aus den Daten bewerten

---

## 2026-04-23

### Bugs gefunden und gefixt

**Bug 1: `PolynomialBasis` fehlte kubischer Term für System 11**
- `evogrow_v1` nutzte `PolynomialBasis` nur bis Grad 2, System 11 erwartet `u1^3`
- `expected_active_idxs` warf `KeyError`
- Entscheidung: `evogrow_v1` auf `default_staged_polynomial_basis` umgestellt
- Geändert: `experiments/run_experiment.jl`, `benchmarks/benchmark_evogrow.jl`, `CLAUDE.md`

**Bug 2: `log_exception` speicherte `DataType` statt `String`**
- `merged[:exception_type] = typeof(err)` schlug fehl, weil `Dict{Symbol,String}` keinen `DataType` akzeptiert
- Fix: `string(typeof(err))` in `src/utils/logging.jl`
- Latenter Bug: wäre bei jeder Exception aufgetreten

### Neue Studie geplant und implementiert

**WP-G1: Strukturgeneralisierungs-Studie** (`generalization_study.jl`)
- Frage: Wenn EvoODE auf Parametersatz A die korrekte Struktur findet, passt diese Struktur nach reinem Parameter-Refit auch auf ungesehene Parametersätze?
- 3 Systeme: Logistic growth, Lotka-Volterra, SIR
- 2 Varianten: `evogrow_v2_2_stage_local`, `gp_baseline`
- 3 Seeds
- Baseline: frische Discovery direkt auf Testtrajektorie
- Output: `debug_results/generalization_summary.csv`, `debug_results/generalization_detail.csv`

### Dokumentation

- `DIARY.md` angelegt
- `SCRIPTS.md` angelegt
- `codex/CURRENT_TASK.md` als überschreibbare Codex-Instruktionsdatei etabliert
- `CLAUDE.md`: Active-Studies-Tabelle ergänzt

### Erste Experiment-Befunde

Nach ca. 40/300 Runs waren System 2 und System 3 abgeschlossen.

- Alle Runs: `success=true`, `exact_support_match=true`
- Loss deterministisch über alle Seeds
- Stage Overshoot: `evogrow_v2_1` overshooted auf System 3 im Mittel um 1.5 Stages; v2.2-stage-local Varianten bleiben bei Overshoot 0

### Tagesabschluss

Vier Skripte laufen über Nacht:

- `experiments/run_experiment.jl paper1_phaseA_v1`
- `generalization_study.jl`
- weitere Profiling-Skripte

Codebase sauber committed. Nächster Schritt: Ergebnisse analysieren, wenn Runs durch sind.

---

## 2026-04-22

**Pretuning (OLS Warm-Start)**
- `src/optimize/pretune.jl`: finite differences, Design-Matrix, OLS-Lösung als BFGS-Startwert
- `use_pretuning::Bool`-Flag in `EvoGrow`
- `level_log` um `elapsed_s` erweitert

**Experiment-Infrastruktur**
- `experiments/generate_manifest.jl`: Manifest und per-run Config/Status
- `experiments/run_experiment.jl`: sequentieller Runner mit robustem Fehlerhandling
- `experiments/aggregate.jl`: erzeugt `run_registry.csv`
- atomare Writes für Result/Metrics

**Debug- und Profiling-Skripte**
- `debug_single.jl`
- `profile_init.jl`

**Aufräumen**
- obsolete Testskripte gelöscht
- `run_odebench.jl` nach `benchmarks/` verschoben

**Experiment gestartet**
- `paper1_phaseA_v1`: 10 Systeme x 6 Varianten x 5 Seeds = 300 Runs

---

## 2026-04-21

**EvoGrow v2.2 (`stage_local`)**
- `StageProgressionPolicy` mit `:stage_local`
- `StageUsagePolicy` mit `:hard`, `:soft`, `:passive`
- stage-lokale Plateau-Detektion mit Mindestbudget pro Stage
- Benchmark-Matrix: 10 Systeme x 6 Varianten x 5 Seeds

---

## 2026-04-20

**Projekt-Fundament**
- Core stabilisiert: EvoGrow und GP laufen sauber mit konsistentem Loss
- Benchmark-Infrastruktur angelegt
- Housekeeping: Stubs, Docstrings, Interface-Bereinigung
- `CLAUDE.md` als Planungsdatei konsolidiert

