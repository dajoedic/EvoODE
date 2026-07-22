# CLAUDE.md - EvoODE

This file is the single source of truth for the EvoODE project.
All project vision, architecture, roadmap, status, and research priorities live here.
Do not maintain a second planning document elsewhere.

Exception: `docs/paper1_study_protocol.md` is an intentionally standalone companion document
for Paper 1 that duplicates some configurations from this file (system list, hyperparameters,
variant definitions). It exists as a self-contained supplementary artifact. Both documents must
be kept in sync manually whenever a configuration changes.

## Collaboration

All communication with the user happens in **German**.
Code, comments, docstrings, and commit messages remain in **English**.
This applies to all responses, reviews, and planning discussions.

## What This Project Is

EvoODE is a Julia research framework for data-driven discovery of interpretable ODE systems from time-series data.
It supports both scalar (1D) and coupled multi-dimensional systems, with a research focus on coupled systems.

The core idea is simple:
instead of fitting a fixed library like SINDy or searching globally from large random structures like GP,
EvoODE starts small and grows model structure incrementally, only increasing complexity when simpler structures are not sufficient.

This is a PhD research project.
Scientific correctness, reproducibility, and research clarity matter more than speed or feature volume.
Every architectural decision must be defensible as part of a research contribution.

## Vision

EvoODE is a research platform for discovering interpretable, coupled dynamical systems from data through structured, iterative growth.

The goal is not merely to fit ODEs, but to study how model structures should be constructed, expanded, validated, and controlled.

## Core Idea

Data -> Structure -> Parameters -> Simulation -> Evaluation -> Iteration

Key principle:
structured, iterative growth instead of global search.

## PhD Focus

Efficient and robust search strategies for interpretable discovery of coupled ODE systems.

## Scientific Position and Contribution

### Positioning vs. Baselines

| Method | Search Space | Growth Strategy | Complexity Control |
|--------|-------------|-----------------|-------------------|
| SINDy | Restricted: fixed linear library | None (direct regression) | L1 sparsity |
| GP | Unrestricted | Global: starts large, random | Parsimony pressure |
| EvoODE | Unrestricted | Incremental: starts minimal, grows | Staged grammar + stopping criterion |

### Core Scientific Claims

1. Starting small and growing incrementally can be more efficient than global search.
2. Grammar-staged complexity unlocking can reduce wasted computation.
3. The stopping and promotion criterion can serve as a principled complexity-control mechanism.

### Core Research Questions

- What is the best stopping and promotion criterion?
- How should structure grow: term-wise, equation-wise, staged, coupling-aware, or error-guided?
- How should structure search and parameter optimization be coupled?
- How should coupled systems be handled specifically?
- How should discovered models be evaluated?
- How does performance scale with noise, sample size, coupling strength, and dimensionality?

## Project Structure

```text
EvoODE/
|-- CLAUDE.md                              (project master document — this file)
|-- DIARY.md                               (chronological project log; design decisions, bug history)
|-- SCRIPTS.md                             (execution runbook for all scripts)
|-- Project.toml
|-- Manifest.toml
|-- src/
|   |-- EvoODE.jl
|   |-- core/
|   |   |-- types.jl
|   |   |-- discover.jl
|   |   `-- stopping.jl
|   |-- structure/
|   |   |-- interface.jl
|   |   |-- evogrow.jl
|   |   |-- gp.jl
|   |   |-- null.jl
|   |   `-- utils.jl
|   |-- basis/
|   |   |-- interface.jl
|   |   |-- polynomial.jl
|   |   `-- staged_polynomial.jl
|   |-- loss/
|   |   |-- interface.jl
|   |   `-- mse.jl
|   |-- optimize/
|   |   |-- interface.jl
|   |   |-- bfgs.jl
|   |   |-- dummy.jl
|   |   `-- pretune.jl
|   |-- simulate/
|   |   |-- solve.jl
|   |   `-- export.jl
|   |-- plotting/
|   |   `-- plot_solution.jl
|   `-- utils/
|       |-- checks.jl
|       `-- logging.jl
|-- benchmarks/                            (exploratory, direct-execution scripts — see note below)
|   |-- benchmark_evogrow.jl
|   |-- run_odebench.jl
|   |-- data/
|   |   `-- strogatz_extended.json
|-- experiments/                           (formal, manifest-based Paper 1 runs — see note below)
|   |-- generate_manifest.jl
|   |-- run_experiment.jl
|   |-- aggregate.jl
|   `-- paper1_phaseA_v1/
|-- docs/
|   `-- paper1_study_protocol.md          (standalone Paper 1 protocol; intentionally duplicates some config from CLAUDE.md)
|-- analysis/                              (Python analysis pipeline — see analysis/CONVENTIONS.md)
|   |-- CONVENTIONS.md                     (pipeline rules, naming, anti-patterns)
|   |-- requirements.txt
|   |-- status.py                         (study/process status checker)
|   |-- configs/
|   |   `-- paper1_phaseA_v1.json         (experiment config driving all analysis scripts)
|   |-- scripts/
|   |   |-- aggregate/
|   |   |   `-- aggregate_run_registry.py (WP-A2/A3: run_registry.csv -> aggregate CSV)
|   |   `-- plot/
|   |       |-- plot_exact_match_rates.py (WP-A4)
|   |       |-- plot_stage_overshoot.py   (WP-A5)
|   |       `-- table_main_results.py     (WP-A6)
|   |-- utils/
|   |   |-- io.py
|   |   |-- metrics.py
|   |   `-- style.py                      (VARIANT_COLORS, VARIANT_LABELS)
|   |-- data/                             (gitignored; derived CSVs from run_registry)
|   |-- figures/                          (gitignored; generated plots)
|   |-- tables/                           (gitignored; generated LaTeX + CSV)
|   |-- notebooks/                        (gitignored; exploratory)
|   `-- paper1/                           (frozen submission artifacts)
|-- outputs/                               (gitignored; unified generated-output root)
|   |-- benchmarks/
|   `-- studies/
|       |-- debug/
|       |-- generalization/
|       `-- profiling/
|-- studies/                               (direct-execution study scripts)
|   |-- debug/
|   |   `-- debug_single.jl
|   |-- generalization/
|   |   `-- generalization_study.jl
|   `-- profiling/
|       `-- profile_init.jl
|-- codex/                                (task management for AI-assisted development)
|   `-- CURRENT_TASK.md                   (active task — Julia or Python)
```

### benchmarks/ vs experiments/

These two directories serve distinct purposes and must not be conflated.

| | `benchmarks/` | `experiments/` |
|---|---|---|
| Execution | direct `julia script.jl` | manifest-based runner |
| Purpose | exploratory, qualitative | formal, paper-grade |
| Reproducibility | best-effort | atomic writes, full status tracking |
| Failure handling | per-run catch, logs to stdout | per-run status.json, metrics.json |
| Output | `outputs/benchmarks/` (gitignored) | `experiments/<id>/runs/` (per-run folders) |

### codex/ convention

One single task file for all work:
- `CURRENT_TASK.md` — active task (Julia algorithm, Python analysis, or infrastructure)

The second line of every task spec must declare the language:
`**Language: Python**` or `**Language: Julia**`

Contains "Kein aktiver Task" when no work is pending.
Write the next task spec into this file before handing off to an AI coding assistant.

### See also

`SCRIPTS.md` — runbook with exact commands for all scripts and typical workflows.
`DIARY.md` — chronological log of design decisions, bug fixes, and implementation notes.

The module structure is intentionally extensible.
New structure search algorithms, bases, losses, and optimizers should be added through the relevant interface layer and registered in `src/EvoODE.jl`.
Do not hardcode algorithm-specific logic into `discover()`.

## Key Types

### `Trajectory`

```julia
struct Trajectory
    t::Vector{Float64}
    x::Matrix{Float64}   # shape: T x dim
end
```

- `dim = 1` for scalar ODEs and `dim > 1` for coupled systems.
- This is the standard dataset container used throughout the pipeline.

### `StructureSpec`

```julia
struct StructureSpec
    active_idxs::Vector{Vector{Int}}
end
```

- `active_idxs[k]` contains the active basis term indices for equation `k`.
- The current representation is index-based and linear in basis terms.
- Expression trees are a later-phase extension and are not implemented yet.

### `DiscoveryOptions`

Controls shared, algorithm-agnostic search behavior:

- RNG seed and verbosity
- minimum and maximum levels
- absolute loss threshold
- plateau detection and relative plateau settings

### `DiscoveryResult`

```julia
struct DiscoveryResult
    structure::Any
    params::Vector{Float64}
    loss::Float64
    objective::Float64
    meta::NamedTuple
end
```

- `loss` is the validated loss on the final simulated trajectory.
- `objective` is the search objective returned by structure search.
- `meta` contains diagnostics from structure search, building, optimization, prediction, and sanity checks.

## Core Pipeline

```text
discover(traj; structure, optimizer, basis, loss, options)
    |
    |-- 1. search_structure(strategy, traj, basis, loss, optimizer, options)
    |       -> returns structure, params, loss, objective, meta
    |
    |-- 2. build_rhs(structure, basis)
    |       -> returns f!, n_params, build_meta
    |
    |-- 3. simulate(f!, params, traj; ...)
    |       -> returns Yhat with shape T x dim
    |
    `-- 4. evaluate_loss(loss, Yhat, traj.x)
            -> DiscoveryResult
```

Important:
`discover()` does not blindly refit parameters after structure search.
It only refits if the returned parameter count does not match the built RHS parameter count.

## Search Algorithms

### EvoGrow

Main research algorithm.

```julia
Base.@kwdef struct EvoGrow <: AbstractStructureSearch
    pop_size::Int = 20
    n_levels::Int = 5
    children_per_parent::Int = 2
    max_terms_per_eq::Int = 5
    λ::Float64 = 1e-3
    progression::StageProgressionPolicy = StageProgressionPolicy()
    usage::StageUsagePolicy = StageUsagePolicy()
    use_pretuning::Bool = true
end
```

Behavior:

1. Start with minimal structures.
2. Evaluate the current population.
3. Generate children by structure growth.
4. Fit parameters and score loss plus complexity penalty.
5. Select the best population.
6. Use shared stopping logic to stop or, for staged bases, unlock more complexity.

#### EvoGrow variants

- v1: flat growth over all available basis terms
- v2: staged complexity release
- v2.1: stage-aware child generation after stage unlock
- v2.2: stage-local progression with minimum stage budget and configurable stage usage policy
- v3: planned equation-wise growth
- v4: planned coupling-aware growth

#### EvoGrow v2.2 design freeze

Paper 1 focuses on staged growth as a complexity-control mechanism.

The v2.2 method direction is fixed:

- each stage gets a minimum search budget measured in levels
- plateau detection is stage-local, not global
- promotion requires sufficient stage exploration plus plateau plus loss still above target
- global loss tolerance remains a hard stop

#### Population behavior on stage promotion

When EvoGrow promotes from one stage to the next, the current population is carried
over without modification. Individuals discovered in earlier stages continue into the
new stage and are expanded using the newly unlocked basis terms.

This is intentional. The warm-start effect preserves good structures found so far
and avoids restarting from scratch at each stage boundary.

The accepted risk is anchoring: the population may remain biased toward structures
built from lower-stage terms, reducing exploration pressure on newly unlocked terms.
The stage usage policy (hard / soft / passive) is the mechanism designed to
counteract this.

A population reset on promotion is a planned variant for future work.
It must not be implemented in the current phase.

Two design axes must be kept separate:

1. Stage progression policy
   Controls when a stage is kept, promoted, or terminated.
2. Stage usage policy
   Controls how strongly newly introduced terms are encouraged after unlock.

The current v2.1 baseline is the existing code behavior:

- staged term unlocking
- global plateau-driven promotion
- hard stage-aware child generation after unlock

The passive unlock-only behavior is not the baseline.
It is a separate control variant for benchmarking.

The current v2.2 usage-policy comparison is:

- `:hard`
- `:passive`
- `:soft`

Do not collapse stage progression and stage usage into a single mechanism again.

#### Phase A findings (paper1_phaseA_v1, 300/300 runs, frozen 2026-05-11)

Results are frozen. Full verdicts in `docs/paper1_freeze_memo_phaseA.md`.

- H1 (stage overshoot reduction): PARTIAL — supported only on System 54.
- H2 (competitive recovery quality): SUPPORTED — v2.2 competitive on majority of exact systems.
- H3 (wasted levels reduction): PARTIAL — supported on Systems 11 and 54.
- H4 (usage policy ordering): vacuous — all exact_match_rate values are 0 for the H4 systems; the ordering claim cannot be meaningfully evaluated.

Key limitation: growth-without-pruning causes exact_match=0 on System 11 despite loss ~4e-15. Genuine algorithmic limitation; stated in the paper.

### GPStructureSearch

Baseline genetic programming search over the full basis.

- tournament selection
- per-equation crossover
- add/remove/replace mutation
- no staged complexity release

This is a comparison baseline, not the central contribution.

## Basis Libraries

### `PolynomialBasis`

Flat basis with all supported polynomial terms available immediately.

### `StagedPolynomialBasis`

Default staged basis with five complexity levels:

1. linear terms
2. self-quadratic terms
3. pairwise cross terms
4. self-cubic terms
5. trigonometric terms

For non-staged bases, all terms are available from the start.

## Losses and Evaluation

### Implemented loss

- `MSELoss`: state MSE on simulated trajectories

### Evaluation axes used or planned

- state MSE
- derivative loss
- simulation loss
- complexity penalty
- validation splits

## Optimizers

### Implemented

- `BFGSOptimizer`: primary parameter fitting backend
- `DummyOptimizer`: testing and pipeline smoke-check placeholder

### Pretuning

`src/optimize/pretune.jl` implements a least-squares warm-start for parameter initialization.
It estimates derivatives via finite differences, builds a design matrix from the active basis terms,
and solves the resulting linear system to produce an initial parameter vector before BFGS.

This is not a separate optimizer and is not exported from the public API.
It is used internally by EvoGrow and GPStructureSearch when `use_pretuning = true` (the default).
Setting `use_pretuning = false` in `EvoGrow` disables it and falls back to zero-initialization.

### Removed for now

- There is currently no public Adam optimizer in the package API.
- Do not reintroduce one unless it is actually implemented and research-motivated.

## Stopping Logic

Shared across all structure search algorithms through `should_stop()`:

1. hard maximum level limit
2. minimum level guard
3. absolute loss threshold
4. absolute plateau detection
5. relative plateau detection

For EvoGrow specifically, plateau can trigger stage promotion instead of termination if more stages remain.

This stopping and promotion logic is part of the core research contribution and must be treated carefully.

## Experiment Infrastructure

The formal Paper-1 experiment layer lives in `experiments/` and is separate from the exploratory `benchmarks/` runner.

### Scripts

- `experiments/generate_manifest.jl`: creates a full experiment directory with `manifest.json` and all per-run `config.json` / `status.json` files before any run starts
- `experiments/run_experiment.jl`: reads a manifest and executes all queued runs sequentially; one run per process; crashes of individual runs do not stop the runner
- `experiments/aggregate.jl`: scans all per-run folders and derives `run_registry.csv`; idempotent; can be called at any time

### Per-run file protocol

Each run lives in `experiments/<experiment_id>/runs/<run_id>/`:

- `config.json`: immutable after creation; all algorithm and system parameters
- `status.json`: overwritten on each status transition; never atomic (crash leaves `status=running`)
- `result.json`: written atomically (tmp → rename) on completion; only for `success=true`
- `metrics.json`: written atomically; also written as partial on failure if any data is available
- `log.txt`: append-only; restart marker `=== RESTART at <timestamp> ===` on re-run
- `summary.txt`: human-readable; overwritten on completion

### Status semantics

| status | meaning |
|--------|---------|
| `queued` | not yet started |
| `running` | started; if `finished_at=null` after process death → aggregator infers `interrupted` |
| `finished` | completed without exception; does not imply good results |
| `failed` | exception caught by runner |
| `interrupted` | inferred by aggregator only; never written by runner |

`success=true` means: run completed, finite loss available, result/metrics written.
`success=false` means: exception, all-NaN output, or write failure.
`failure_reason` is always a controlled enum: `exception`, `all_invalid`, `write_failure`, `unknown`.

### `run_registry.csv`

Derived, never primary. Generated by `aggregate.jl` from per-run folders.
Contains one row per run with all config, status, and metrics fields.
Can be regenerated at any time without data loss.

### Execution

```
julia experiments/generate_manifest.jl   # once per experiment
julia experiments/run_experiment.jl <experiment_id>
julia experiments/aggregate.jl <experiment_id>
```

### Current experiments

- `paper1_phaseA_v1`: Phase A exploratory run — 10 systems × 6 variants × 5 seeds = 300 runs; `run_type=exploratory`, `include_in_paper=false`

## Benchmark Data and Scripts

### Main dataset

Location:
`benchmarks/data/strogatz_extended.json`

Source:
extended Strogatz benchmark used in the ODEFormer context.

Dataset summary:

- 63 total systems
- 23 scalar systems
- 28 coupled 2D systems
- 10 coupled 3D systems
- 2 coupled 4D systems

### Benchmark scripts

- `benchmarks/benchmark_evogrow.jl`: curated benchmark pack for EvoGrow
- `benchmarks/run_odebench.jl`: ODEBench-style runner over JSON-loaded systems

### Benchmark parameter rationale

The following parameter interaction governs when EvoGrow can promote stages:

effective minimum levels per stage = max(min_levels_per_stage, plateau_window + 1)

With min_levels_per_stage = 2 and plateau_window = 3:
  effective minimum = max(2, 4) = 4 levels per stage

Minimum levels required to reach each stage:
  Stage 2: 4 levels
  Stage 3: 8 levels
  Stage 4: 12 levels
  Stage 5: 16 levels

The benchmark contains systems requiring up to Stage 4 (IDs 11, 37).
EVO_LEVELS = 20 provides sufficient budget for all systems in the benchmark.
EVO_LEVELS = 8 (QUICK mode) is sufficient only for systems requiring Stage 1 or 2.

GP_GENERATIONS is set equal to EVO_LEVELS to ensure comparable search budgets.

### Benchmark evaluation split

The full benchmark set remains in scope for method development.

Systems must be split into two evaluation categories:

1. Exact structural recovery
   For systems exactly representable in the current basis.
   Evaluate exact support recovery and fit quality separately.
2. Surrogate structural recovery
   For systems not exactly representable in the current basis.
   Do not score them as exact recovery.
   Evaluate stage reached, relevant term-class usage, fit quality, and stability instead.

These two categories must never be mixed into one structure-correctness metric.

## Current Status

### Phase 1 - Stable Core

Status: DONE
Completed on: 2026-04-20

Core pipeline, `discover()`, `GPStructureSearch`, `EvoGrow` baseline, shared stopping logic, structured logging, and sanity checks are all stable and validated.
Details in `DIARY.md` (2026-04-20).

### Phase 2 - EvoGrow Variants

Status: IN PROGRESS

#### v1: simple growth

Status: DONE
Completed on: 2026-04-20

- flat term-wise growth over the available basis
- serves as the first EvoGrow baseline

#### v2: complexity tiers

Status: DONE
Completed on: 2026-04-21

`StagedPolynomialBasis` with 5 stages, staged basis release, and stage-aware child generation (v2.1) all implemented.

#### v2.2: stage progression policy

Status: DONE
Completed on: 2026-04-21

Implemented:

- `StageProgressionPolicy`: configurable mode (`:global_plateau` or `:stage_local`) with `min_levels_per_stage`
- `StageUsagePolicy`: configurable mode (`:hard`, `:passive`, `:soft`) with `new_term_bias_prob`
- `_stage_progression_decision`: stage-local plateau detection with minimum stage budget
- `_expand_with_usage_policy`: dispatches child generation based on usage policy
- all wired into `search_structure` main loop
- benchmark covers all four comparison variants plus GP baseline

#### v3: equation-wise

Status: NOT STARTED

Planned direction:

- discover equations separately or semi-separately
- compare against full-system discovery
- possibly use teacher forcing or hybrid simulation

#### v4: coupling-aware

Status: NOT STARTED

Planned direction:

- prioritize discovery of coupling terms explicitly
- bias search using system-level structural information

### Phase 3 - Benchmarking

Status: IN PROGRESS
Started on: 2026-04-21

Benchmark infrastructure complete:

- 10 systems (dim 1–4, exact and surrogate split)
- 6 variants: EvoGrow v1, v2.1, v2.2 progression-only, v2.2 passive, v2.2 soft, GP baseline
- 5 seeds per (variant, system) combination
- metrics: loss, exact_support_match, final_stage, stage_overshoot, wasted_levels, elapsed_s
- output: per-run CSV + aggregate CSV with mean/std

Planned next benchmark axes:

- noise
- sampling density
- coupling strength
- dimensionality

### Phase 4 - Paper 1

Status: IN PROGRESS
Started on: 2026-04-22

Experiment infrastructure complete (WP-E1 through WP-E3):

- manifest generator, sequential runner, aggregator
- per-run file protocol with atomic writes and robust failure handling
- `run_registry.csv` as derived aggregation view

Active experiment:

- `paper1_phaseA_v1`: 300 runs total (10 systems × 6 variants × 5 seeds), exploratory — 242 finished as of 2026-04-29; 1 run stuck (System 54, EvoGrow v1, Seed 7, Lorenz 3D, no BFGS timeout)

Target:
EvoGrow baseline vs GP and SINDy

Likely scope:

- simple systems
- staged growth concept
- first systematic benchmark comparison

### Phase 5 - Advanced Methods

Status: NOT STARTED

- expression trees
- error-guided growth
- backtracking
- hybrid search
- validation-based stage promotion
- multi-hypothesis models

## Active Studies (as of 2026-05-11)

| Artifact | Status | Note |
|----------|--------|------|
| `paper1_phaseA_v1` | **frozen** (300/300) | H1–H4 verdicts in freeze memo; evidence scope closed |
| `studies/generalization/` | fertig | Auxiliary only; insufficient cells for supplementary inclusion |
| `studies/profiling/profile_init.jl` | Daten vorhanden | Methods section / Discussion only; not evidence for H1–H4 |

## Current Priorities

Current priorities as of 2026-07-22:

Done (do not re-open):
- WP-0.1 (H4 claim → VACUOUS in `evaluate_hypotheses.py`) — done 2026-05-17.
- WP-0.2 (generalization data path in `evaluate_hypotheses.py`) — done 2026-05-17.
- WP-1.3 (Phase 1 diagnostic run) and Gate 1 — done 2026-05-30; v2.2 fails Gate 1, Phase 2 (EvoGrow v3) triggered.
- WP-v3.1 (design note `docs/evogrow_v3_design.md`) — done 2026-07-20.
- WP-v3.2 (`EvoGrowV3` lockstep bridge) — done 2026-07-20; regression equivalence to v2.2 confirmed.
- WP-H1 through WP-H1d (regression history, `studies/regression/`) — done 2026-07-20.
- WP-P1 / WP-P1b / WP-P1c (evaluation cost: determinism, separate screening budgets, per-level
  instrumentation, micro-benchmark) — done 2026-07-22. Measured 2.71x on System 26; wall-clock
  dependence removed from the regression result path.
- WP-P2.1 through WP-P2.3 (derivative-based screening) — **discontinued 2026-07-22** by stop rule.
  Artifacts kept: `docs/evogrow_screening_design.md`, `src/structure/evogrow_screening.jl`,
  `studies/debug/compare_screening_variant.jl`. Do not resume without new evidence.

Active (Phase 2 — EvoGrow v3):
1. WP-v3.3: equation-aware child generation (design note section 6).
2. WP-v3.4 through WP-v3.6: per-equation residual signal and promotion rule, v3 metrics,
   validation run vs. v2.2.
3. Gate 2: decide whether v3 is paper-ready.

Pending before the next regression baseline:
- The regression configuration has changed since Baseline v0 (`config_fingerprint`
  `0c739d4e36ee6498`): `time_limit_s` is now explicit, and additional config fields entered the
  fingerprint. Baseline v0 stays valid as a historical record, but a new baseline must be run
  under the current configuration before v3.3 results can be regression-checked.

After Gate 2:
4. Phase 3 (PAPER_1.md): ODEBench protocol alignment — system classification, R² metric, protocol-audit document.
5. Phase B experiment (`paper1_phaseB_v1`) — 63 systems × 2 conditions × 3 seeds.

Open, not scheduled:
- Hypothesis from WP-P2.3: the ODE solver tolerance in the evaluation path (`abstol = reltol = 1e-6`)
  may make finite-difference gradients meaningless once the loss falls below roughly that scale,
  which would affect every warm-started fit and the attainability of `loss_tol = 1e-8`. Unverified.

`PAPER_1.md` is the authoritative execution plan and takes precedence if this list drifts.

## Implemented and Working

- `discover()` end-to-end pipeline
- `EvoGrow` v1, v2.1, v2.2
- `StageProgressionPolicy`, `StageUsagePolicy`
- `GPStructureSearch`
- `PolynomialBasis`
- `StagedPolynomialBasis`
- `MSELoss`
- `BFGSOptimizer`
- `DummyOptimizer`
- plotting and CSV export
- pretuning warm-start via least-squares derivative matching
- 10-system benchmark with 6 variants, 5 seeds, exact/surrogate split
- aggregate statistics (mean/std loss, exact_match_rate, wasted_levels)
- experiment infrastructure: manifest generation, per-run execution, aggregation to run_registry.csv

## Known Gaps

- `utils/checks.jl` is still effectively a placeholder
- no train/validation split in discovery yet
- no noise injection utilities yet
- no systematic comparison against ODEBench baselines (SINDy, PySR) yet — planned for Phase 5
- `paper1_phaseA_v1` analysis complete; Phase B experiment not yet started
- expression trees are not implemented
- environment and test execution still need cleanup and faster verification
- no strong parameter-count validation before optimization beyond mismatch guard
- `simulate()` still returns NaNs on failed solves and needs stronger failure handling

## Design Principles

1. Modular: every component is swappable behind an abstract interface.
2. Reproducible: seed all stochastic behavior through `DiscoveryOptions.rng_seed`.
3. Interpretable: always preserve a human-readable structure description.
4. Minimal: do not add features without direct research motivation.
5. Consistent logging: route diagnostics through the common verbosity and logging pattern.
6. Preserve metadata: do not silently discard search or fit diagnostics.

## System Handling Directions

- full-system discovery
- equation-wise discovery
- equation-wise discovery with teacher forcing
- sequential discovery
- hybrid approaches

These are research directions, not all implemented features.

## Non-Goals

- no GPU work in the current research phases
- no UI
- no PDE expansion
- no premature optimization
- no unnecessary dependencies

## Coding Conventions

- Julia only
- target Julia 1.11.5
- public API is exported from `src/EvoODE.jl`
- use `Base.@kwdef` for defaulted configuration structs
- keep ODE RHS functions in-place with signature `f!(du, u, params, t)`
- keep parameter vectors as `Vector{Float64}`
- use `NamedTuple` metadata consistently
- prefer modular interfaces over special-casing in orchestration

## Guiding Rule

Every change must support a research hypothesis.
If you cannot state which research question a change addresses, do not make it.

## Paper 1 — Execution Roadmap

The full execution plan lives in `PAPER_1.md`. That document contains:
- All phases (0–5) with Go/No-Go criteria
- Work package breakdown
- EvoGrow v3 design specification (conditional on Phase 1 decision)
- Implementation and scientific risk register
- Frozen elements

**Current phase:** Phase 2 — EvoGrow v3 design and implementation (Phase 0 and Phase 1 complete; Gate 1 decided 2026-05-30, v2.2 fails, v3 triggered)

**Active WPs:**
- WP-v3.1: Design note `docs/evogrow_v3_design.md` (per-equation progress signal and promotion rule) — active Codex task, not yet delivered
- WP-v3.2 through WP-v3.6: EvoGrow v3 implementation and validation run vs. v2.2

**Final experiment scope:**
- All 63 ODEBench systems (`benchmarks/data/strogatz_extended.json`)
- Two conditions only: final EvoODE variant with pretuning=true vs. pretuning=false
- No GP baseline, no v1, no v2.1 in final experiment
- All results from new runs (experiment ID `paper1_phaseB_v1`)

**Archived baseline:** `paper1_phaseA_v1` — 300/300 runs, all success=true.
Evidence frozen. H1–H4 verdicts in `docs/paper1_freeze_memo_phaseA.md`.
Phase A results are not used for final paper claims.

---

## Paper 1 – Reproducibility Protocol

### 1. Scope

This section defines the exact experimental setup used for Paper 1.
All configurations listed here are fixed for reproducibility.
Any change to these parameters requires creating a new experiment block with a new identifier and explicit versioning.
This section documents what is implemented and executed, not aspirational behavior.

---

### 2. Compared Methods

Six methods are included in the Paper 1 comparison.
Each is defined by its implementation mapping in `benchmarks/benchmark_evogrow.jl`.

| Label | Slug | Basis | Progression mode | Usage mode |
|-------|------|-------|------------------|------------|
| EvoGrow v1 (flat) | `evogrow_v1` | `StagedPolynomialBasis` (all terms) | `:global_plateau` | `:hard` |
| EvoGrow v2.1 baseline | `evogrow_v2_1` | `StagedPolynomialBasis` | `:global_plateau` | `:hard` |
| EvoGrow v2.2 progression-only | `evogrow_v2_2_stage_local` | `StagedPolynomialBasis` | `:stage_local` | `:hard` |
| EvoGrow v2.2 passive usage | `evogrow_v2_2_passive` | `StagedPolynomialBasis` | `:stage_local` | `:passive` |
| EvoGrow v2.2 soft usage | `evogrow_v2_2_soft` | `StagedPolynomialBasis` | `:stage_local` | `:soft` |
| GP baseline | `gp_baseline` | `StagedPolynomialBasis` (all terms) | N/A | N/A |

Notes:
- EvoGrow v1 uses `default_staged_polynomial_basis(dim)` with all terms available from the start (no staged release). This matches the GP baseline's term set and ensures a fair comparison — same search space, different strategy.
- EvoGrow v2.1 differs from v1 only in the staged release: same basis, global plateau progression.
- EvoGrow v2.2 progression-only differs from v2.1 only in the progression mode (`:stage_local`).
- EvoGrow v2.2 passive and soft share the same `:stage_local` progression as progression-only, but differ in usage mode.
- The GP baseline uses `default_staged_polynomial_basis(dim)` but ignores staging — all terms are available from initialization.
- "Progression-only" means only the progression policy changes relative to v2.1; the usage policy remains `:hard`.

---

### 3. Benchmark Dataset

The benchmark consists of exactly 10 systems drawn from `benchmarks/data/strogatz_extended.json`.

#### Exact systems (8 systems)

| ID | Name | Dim | Expected stage | True structure |
|----|------|-----|----------------|----------------|
| 2 | Population growth (linear) | 1 | 1 | `du1 = 0.23*u1` |
| 3 | Logistic growth | 1 | 2 | `du1 = 0.79*u1 - 0.0106*u1^2` |
| 11 | Critical slowing down | 1 | 4 | `du1 = -u1^3` |
| 24 | Harmonic oscillator | 2 | 1 | `du1 = u2 \| du2 = -2.1*u1` |
| 26 | Lotka-Volterra competition | 2 | 3 | `du1 = 3*u1 - u1^2 - 2*u1*u2 \| du2 = 2*u2 - u1*u2 - u2^2` |
| 31 | SIR model | 2 | 3 | `du1 = -0.4*u1*u2 \| du2 = 0.4*u1*u2 - 0.314*u2` |
| 54 | Lorenz (periodic) | 3 | 3 | `du1 = -5.1*u1 + 5.1*u2 \| du2 = 12*u1 - u2 - u1*u3 \| du3 = u1*u2 - 1.67*u3` |
| 63 | SEIR model | 4 | 3 | `du1 = -0.28*u1*u3 \| du2 = 0.28*u1*u3 - 0.47*u2 \| du3 = 0.47*u2 - 0.30*u3 \| du4 = 0.30*u3` |

#### Surrogate systems (2 systems)

| ID | Name | Dim | Expected stage | Note |
|----|------|-----|----------------|------|
| 23 | Overdamped pendulum | 1 | 5 | Constant offset outside basis. Evaluate stage reached and trig term usage. |
| 37 | Van der Pol oscillator | 2 | 4 | Cubic cross term `u1^2*u2` outside basis. Evaluate stage reached and cubic term usage. |

Exact and surrogate systems must never be mixed in a single structure-correctness metric.
Exact systems are evaluated on `exact_support_match`.
Surrogate systems are evaluated on stage reached, target term usage, and fit quality.

---

### 4. Fixed Hyperparameters

All parameters below are fixed for Paper 1.
No parameter may vary across runs except `seed`.

#### EvoGrow (all variants)

```
pop_size             = 10
n_levels             = 20
children_per_parent  = 2
max_terms_per_eq     = 6
λ                    = 1e-3
min_levels_per_stage = 2   (STAGE_MIN_LEVELS)
new_term_bias_prob   = 0.75 (SOFT_BIAS, used by :soft and :hard modes)
```

#### GP baseline

```
pop_size         = 10
n_generations    = 20
tournament_k     = 3
p_crossover      = 0.7
p_mutation       = 0.3
max_terms_per_eq = 6
init_min_terms   = 1
init_max_terms   = 2
λ                = 1e-3
```

#### DiscoveryOptions (shared across all variants)

```
min_levels       = 2
max_levels       = 50
loss_tol         = 1e-8
plateau_window   = 3
plateau_tol      = 1e-4
plateau_relative = false
plateau_rtol     = 1e-3
```

#### Optimizer

```
BFGSOptimizer(maxiters = 200, time_limit_s = 300.0)
```

#### Trajectory generation

Trajectories are generated from the ground-truth ODE using `Tsit5()` with `abstol = 1e-9`, `reltol = 1e-9`.
Each system specifies its own `u0`, `tspan`, and `T` as defined in the BENCHMARKS table in `benchmark_evogrow.jl`.

#### Effective minimum levels per stage

Due to the interaction between `plateau_window` and `min_levels_per_stage`:

```
effective_min = max(min_levels_per_stage, plateau_window + 1) = max(2, 4) = 4
```

This means each stage requires at least 4 levels before promotion is possible.
`n_levels = 20` is sufficient to reach Stage 4, covering all systems in the benchmark.

---

### 5. Seed Configuration

Exactly five seeds are used per (variant, system) cell:

```julia
seeds = [42, 123, 7, 99, 17]
```

Every combination of (variant, system, seed) is executed independently.
Total number of runs: 6 variants × 10 systems × 5 seeds = 300 runs.

---

### 6. Metrics

All metrics are recorded per run and aggregated across seeds.

| Metric | Type | Definition |
|--------|------|------------|
| `loss` | Float64 | Final simulation MSE: `mean((Yhat - Ytrue)^2)` over all time steps and dimensions |
| `objective` | Float64 | Search objective returned by structure search: `loss + λ * complexity` |
| `exact_support_match` | Bool | True iff the discovered term indices match the ground-truth term indices exactly for all equations. Meaningful only for exact systems. |
| `final_stage` | Int | Last stage active at termination. -1 if not available (GP baseline). |
| `stage_overshoot` | Int | `final_stage - expected_stage`. Negative means undershooting. |
| `wasted_levels` | Int | Sum of levels spent in stages beyond `expected_stage`. |
| `total_loss_evals` | Int | Total number of loss function evaluations across all levels. |
| `total_invalid_evals` | Int | Number of evaluations that produced NaN or failed simulation. |
| `elapsed_s` | Float64 | Wall time in seconds for the full `discover()` call. |

#### Aggregation metrics (per variant × system cell, across seeds)

| Metric | Definition |
|--------|------------|
| `mean_loss` | Mean of `loss` over valid runs (non-NaN) |
| `std_loss` | Std of `loss` over valid runs |
| `exact_match_rate` | Fraction of valid runs with `exact_support_match = true` |
| `mean_final_stage` | Mean of `final_stage` over valid runs |
| `mean_wasted_levels` | Mean of `wasted_levels` over valid runs |
| `mean_elapsed_s` | Mean of `elapsed_s` over valid runs |
| `mean_invalid_evals` | Mean of `total_invalid_evals` over valid runs |

A run is valid if `loss` is not NaN.
Runs with NaN loss are excluded from mean/std computation but counted in `n_seeds`.

---

### 7. Execution Procedure

The benchmark is executed by running:

```
julia benchmarks/benchmark_evogrow.jl
```

Full mode (Paper 1): no environment flags set.
Quick mode (development only): `QUICK=true julia benchmarks/benchmark_evogrow.jl` — uses reduced parameters and must not be used for paper results.

The execution loop is:

```
for variant in VARIANTS          # 6 variants, fixed order
    for sys in BENCHMARKS        # 10 systems, fixed order
        for seed in seeds        # [42, 123, 7, 99, 17]
            run_one(sys, variant; seed=seed)
        end
    end
end
```

Each run is independent.
Exceptions are caught per run; failed runs are recorded with NaN loss and `recovery_label = "error"`.
Per-run results are written to `summary.csv` incrementally (flush after each run).

---

### 8. Output Artifacts

| Artifact | Location | Description |
|----------|----------|-------------|
| Per-run CSV | `outputs/benchmarks/summary.csv` | One row per (variant, system, seed). Semicolon-separated. |
| Aggregate CSV | `outputs/benchmarks/summary_aggregate.csv` | One row per (variant, system). Mean/std over seeds. Semicolon-separated. |
| Per-run trajectory plot | `outputs/benchmarks/<slug>/<slug>_<id>_<name>.png` | Predicted vs ground-truth trajectories. |
| Per-run convergence plot | `outputs/benchmarks/<slug>/<slug>_<id>_<name>_history.png` | Best objective per level (EvoGrow only). |
| Per-run prediction CSV | `outputs/benchmarks/<slug>/<slug>_<id>_<name>.csv` | Time, ground-truth, prediction columns. |

`summary.csv` and `summary_aggregate.csv` are the primary analysis artifacts.
All other files are diagnostic.

---

### 9. Aggregation Rules

Aggregation groups runs by `(variant_slug, system_id)`.
Within each group, `n_valid` is the count of runs with non-NaN loss.
All aggregate statistics (mean, std, rates) are computed over valid runs only.

Exact and surrogate systems are reported in separate analysis blocks.
`exact_match_rate` is only meaningful for exact systems and must not be reported for surrogate systems.
Surrogate systems are assessed separately on stage reached, target term usage, and fit quality.

These two categories must never be merged into a single structure-correctness metric.

---

### 10. Versioning

Every run records the current git commit hash at the time of execution (from `config.json: git_hash`).
Every run records `started_at` and `finished_at` timestamps in ISO 8601 format.

Before publishing results, verify that all runs were executed from the same commit hash.
If any run used a different hash, re-run that cell and record the discrepancy in the paper supplement.

---

### 11. Paper 1 Freeze

This configuration is fixed for Paper 1.

The following must not change without creating a new experiment block:
- system selection and initial conditions
- hyperparameter values
- seed list
- variant definitions
- metric definitions

If a parameter or variant changes, assign a new experiment identifier (e.g. `paper1_phaseA_v2`) and re-run the full matrix.
Do not overwrite results from a frozen experiment block.

Changes to analysis scripts (`aggregate.jl`, plotting) that do not affect run execution are permitted without versioning.
Changes that affect any value recorded in `summary.csv` require a new experiment block.
