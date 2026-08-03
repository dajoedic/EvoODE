# EvoODE — Architecture Reference

Component-level detail extracted from `CLAUDE.md` on 2026-08-03 to keep the master document at
orientation length. This file is **reference, not planning**: it describes what exists and how the
pieces fit together. Project state, priorities and decisions stay in `CLAUDE.md`; chronology stays
in `DIARY.md`.

---

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
## Implemented and Working

- `discover()` end-to-end pipeline
- `EvoGrow` v1, v2.1, v2.2
- `EvoGrowV3` (per-equation staging: child generation, promotion via derivative residual `r_k`, metrics) — failed Gate 2, kept as failure analysis
- **look-ahead stage cap** (`estimate_stage_caps`, `src/structure/stage_cap.jl`) — search-independent, combines with both v2.2 and v3
- **`evogrow_v2_2_stage_capped`** — v2.2 substrate + stage cap; **the final Paper 1 variant**
- `EvoGrowScreening` (nested-model gate + decoupled polish start; performance-only, not a core claim)
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

## System Handling Directions

- full-system discovery
- equation-wise discovery
- equation-wise discovery with teacher forcing
- sequential discovery
- hybrid approaches

These are research directions, not all implemented features.
