# EvoODE – Evolutionary ODE Discovery Framework

EvoODE ist ein Julia-Forschungsframework für die **datengetriebene Entdeckung interpretierbarer ODE-Systeme** aus Zeitreihendaten.

Statt eine feste Bibliothek wie SINDy direkt zu fitten oder global im gesamten Strukturraum zu suchen wie GP, startet EvoODE mit minimalen Modellen und wächst schrittweise in Komplexität — nur dann, wenn einfachere Strukturen nicht ausreichen.

> **Kernidee:** Strukturiertes, iteratives Wachstum statt globale Suche.

Dies ist ein laufendes PhD-Forschungsprojekt. Wissenschaftliche Korrektheit, Reproduzierbarkeit und Interpretierbarkeit haben Vorrang vor Geschwindigkeit oder Feature-Umfang.

---

## Wissenschaftliche Position

| Methode | Suchraum | Wachstumsstrategie | Komplexitätskontrolle |
|---------|----------|-------------------|-----------------------|
| SINDy | Eingeschränkt: feste lineare Bibliothek | Keine (direkte Regression) | L1-Sparsität |
| GP | Unbeschränkt | Global: startet groß, zufällig | Parsimony-Druck |
| **EvoODE** | **Unbeschränkt** | **Inkrementell: startet minimal, wächst** | **Gestufte Grammatik + Stoppkriterium** |

### Kernhypothesen

1. Klein starten und inkrementell wachsen kann effizienter sein als globale Suche.
2. Grammatik-gestuftes Entsperren von Komplexität reduziert vergudete Rechenzeit.
3. Das Stopp- und Promotionskriterium dient als prinzipielles Komplexitätskontrollmechanismus.

---

## Projektstruktur

```text
EvoODE/
├─ CLAUDE.md                         ← Master-Dokument: Architektur, Roadmap, Paper-1-Protokoll
├─ DIARY.md                          ← Chronologisches Projekttagebuch
├─ SCRIPTS.md                        ← Runbook für alle Skripte
├─ Project.toml / Manifest.toml
├─ src/
│   ├─ EvoODE.jl                     ← Zentrales Modul
│   ├─ core/
│   │   ├─ types.jl                  ← Trajectory, StructureSpec, DiscoveryResult, …
│   │   ├─ discover.jl               ← discover() Hauptpipeline
│   │   └─ stopping.jl               ← Stopp- und Promotionslogik
│   ├─ structure/
│   │   ├─ evogrow.jl                ← EvoGrow v1, v2.1, v2.2 (Hauptalgorithmus)
│   │   ├─ gp.jl                     ← GP-Baseline
│   │   └─ utils.jl
│   ├─ basis/
│   │   ├─ polynomial.jl             ← PolynomialBasis (flach)
│   │   └─ staged_polynomial.jl      ← StagedPolynomialBasis (5 Stufen)
│   ├─ loss/
│   │   └─ mse.jl                    ← MSELoss
│   ├─ optimize/
│   │   ├─ bfgs.jl                   ← BFGSOptimizer
│   │   └─ pretune.jl                ← OLS Warm-Start (intern)
│   ├─ simulate/
│   │   └─ solve.jl
│   └─ plotting/
│       └─ search_animation.jl       ← Suchanimation (render_frame, render_all_frames)
├─ benchmarks/
│   ├─ benchmark_evogrow.jl          ← Haupt-Benchmark: 10 Systeme × 6 Varianten × 5 Seeds
│   ├─ run_odebench.jl               ← ODEBench-Stil-Runner
│   └─ data/
│       └─ strogatz_extended.json    ← 63 Systeme (1D–4D) aus dem Strogatz-Katalog
├─ experiments/
│   ├─ generate_manifest.jl          ← Erzeugt Experiment-Verzeichnis + Manifeste
│   ├─ run_experiment.jl             ← Sequentieller Runner (restart-fähig)
│   └─ aggregate.jl                  ← run_registry.csv aus per-Run-Ordnern ableiten
├─ studies/
│   ├─ debug/debug_single.jl
│   ├─ profiling/profile_init.jl     ← Vergleich: random vs. OLS-Warm-Start
│   └─ generalization/generalization_study.jl
├─ analysis/                         ← Python-Analysepipeline (pandas, matplotlib)
│   ├─ configs/
│   ├─ scripts/
│   └─ utils/
└─ outputs/                          ← (gitignored) alle generierten Outputs
```

---

## Abhängigkeiten

Alle Packages stehen in `Project.toml`:

| Package | Zweck |
|---------|-------|
| `DifferentialEquations.jl` | ODE-Solver (Tsit5, …) |
| `Optimization.jl` + `OptimizationOptimJL.jl` | BFGS-Parameterfit |
| `JSON3.jl` | Laden der Systemdefinitionen |
| `Plots.jl` | Trajektorien- und Animationsplots |
| `CairoMakie.jl` | Suchanimations-Rendering |
| `Printf`, `Dates`, `Random` | Standard-Utilities |

---

## Installation

```bash
git clone <repo-url> EvoODE
cd EvoODE
julia --project=.
```

In der Julia-REPL (nur beim ersten Mal):

```julia
using Pkg
Pkg.instantiate()
```

---

## Kernkonzepte

### Typen

```julia
# Datensatz-Container
struct Trajectory
    t::Vector{Float64}
    x::Matrix{Float64}   # T × dim
end

# Modellstruktur: Menge aktiver Basistermindizes pro Gleichung
struct StructureSpec
    active_idxs::Vector{Vector{Int}}
end
```

### Die `discover()`-Pipeline

```
discover(traj; structure, optimizer, basis, loss, options)
    │
    ├─ 1. search_structure(...)   →  Struktur + Parameter + Loss + Meta
    ├─ 2. build_rhs(...)          →  f!(du, u, p, t)
    ├─ 3. simulate(...)           →  Ŷ  (T × dim)
    └─ 4. evaluate_loss(...)      →  DiscoveryResult
```

### StagedPolynomialBasis

Die Standard-Basis mit 5 Komplexitätsstufen:

| Stufe | Terme |
|-------|-------|
| 1 | lineare Terme: `u1`, `u2`, … |
| 2 | selbst-quadratisch: `u1²`, `u2²`, … |
| 3 | paarweise Kreuzterme: `u1·u2`, … |
| 4 | selbst-kubisch: `u1³`, … |
| 5 | trigonometrisch: `sin(u1)`, `cos(u1)`, … |

EvoGrow entsperrt diese Stufen schrittweise — nur wenn der aktuelle Loss noch nicht gut genug ist.

---

## EvoGrow-Varianten

| Variante | Progression | Usage-Policy | Kernunterschied |
|----------|-------------|--------------|----------------|
| `evogrow_v1` | global plateau | hard | Flache Basis, alle Terme sofort verfügbar |
| `evogrow_v2_1` | global plateau | hard | Staged Release, globales Plateau löst Promotion aus |
| `evogrow_v2_2_stage_local` | stage-local | hard | Mindestbudget pro Stufe, lokale Plateau-Detektion |
| `evogrow_v2_2_passive` | stage-local | passive | Neue Terme werden nicht aktiv bevorzugt |
| `evogrow_v2_2_soft` | stage-local | soft | Neue Terme mit konfigurierbarer Wahrscheinlichkeit bevorzugt |
| `gp_baseline` | — | — | Klassische genetische Programmierung, kein Staged Release |

---

## Benchmark und Experimente

### Schnellstart: Benchmark

```bash
julia --project=. benchmarks/benchmark_evogrow.jl
```

Läuft alle 6 Varianten auf 10 Systemen mit 5 Seeds (300 Runs). Resume-fähig — kann jederzeit gestoppt und fortgesetzt werden.

Output: `outputs/benchmarks/summary.csv`, `outputs/benchmarks/summary_aggregate.csv`

### Formale Paper-1-Experimente

```bash
# Einmalig: Manifest erzeugen
julia --project=. experiments/generate_manifest.jl

# Runs ausführen (restart-fähig)
julia --project=. experiments/run_experiment.jl paper1_phaseA_v1

# Aggregieren
julia --project=. experiments/aggregate.jl paper1_phaseA_v1
```

Per-Run-Protokoll: `config.json` (immutable), `status.json`, `result.json` + `metrics.json` (atomar), `log.txt`.

---

## Erste Ergebnisse (paper1_phaseA_v1, 300/300 Runs)

EvoGrow schlägt GP auf allen höherdimensionalen und strukturell komplexen Systemen:

| System | Beste EvoGrow (Loss) | GP (Loss) | Faktor |
|--------|---------------------|-----------|--------|
| SIR (2D, Stage 3) | 7,0e-05 | 0,314 | ~4.500× |
| Lorenz (3D, Stage 3) | 7,4e-04 | 0,921 | ~1.200× |
| Lotka-Volterra (2D, Stage 3) | 2,5e-04 | 2,98e-03 | ~12× |

Stage-Overshoot (Kernhypothese — System 54, Lorenz):

| Variante | Overshoot | Wasted Levels |
|----------|-----------|---------------|
| evogrow_v1 | +2 | 1,6 |
| evogrow_v2_1 | +1,6 | 1,2 |
| evogrow_v2_2 (alle) | **0** | **0** |

Stage-lokale Progression verhindert Overshoot auf dem komplexesten System vollständig.

---

## Typischer Forschungs-Workflow

```
1. Experiment konfigurieren  →  CLAUDE.md (Paper-1-Protokoll)
2. Manifest erzeugen         →  generate_manifest.jl
3. Runs ausführen            →  run_experiment.jl <id>
4. Aggregieren               →  aggregate.jl <id>
5. Analysieren               →  analysis/scripts/ (Python)
6. Dokumentieren             →  DIARY.md
```

Status aller laufenden Prozesse:

```bash
python analysis/status.py
```

---

## Benchmark-Datensatz

`benchmarks/data/strogatz_extended.json` — erweiterter Strogatz-Benchmark:

- 63 Systeme gesamt: 23 skalare (1D), 28 gekoppelt 2D, 10 gekoppelt 3D, 2 gekoppelt 4D
- Paper-1-Auswahl: 8 exakte Systeme (Stage 1–4) + 2 Surrogate-Systeme

---

## Dokumentation

| Datei | Inhalt |
|-------|--------|
| `CLAUDE.md` | Master-Dokument: Architektur, Algorithmen, Paper-1-Protokoll |
| `DIARY.md` | Chronologisches Projekttagebuch |
| `SCRIPTS.md` | Runbook: alle Skripte mit exakten Kommandos |
| `docs/paper1_study_protocol.md` | Standalone Paper-1-Protokoll (Supplement) |

---

*EvoODE — PhD-Forschungsframework, Universität / SCCH. Aktueller Status und Roadmap: siehe `CLAUDE.md`.*
