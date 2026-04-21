# CLAUDE.md - EvoODE

This file is the single source of truth for the EvoODE project.
All project vision, architecture, roadmap, status, and research priorities live here.
Do not maintain a second planning document elsewhere.

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
|-- CLAUDE.md
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
|   |   `-- dummy.jl
|   |-- simulate/
|   |   |-- solve.jl
|   |   `-- export.jl
|   |-- plotting/
|   |   `-- plot_solution.jl
|   `-- utils/
|       |-- checks.jl
|       `-- logging.jl
|-- benchmarks/
|   |-- benchmark_evogrow.jl
|   |-- odeformer/
|   |   `-- strogatz_extended.json
|   `-- results/
|-- run_odebench.jl
|-- test.jl
`-- test_evogrow_v2_lotka.jl
```

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

#### Current findings

- On simple linear systems, EvoGrow v2 stays in Stage 1 as desired.
- On Lotka-Volterra, EvoGrow v2 improves significantly after Stage 2.
- Current stage progression still does not reliably recover the mechanistically correct cross-term structure.
- This is now a core research question, not just an implementation detail.

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

## Benchmark Data and Scripts

### Main dataset

Location:
`benchmarks/odeformer/strogatz_extended.json`

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
- `run_odebench.jl`: ODEBench-style runner over JSON-loaded systems

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

Completed work:

- fixed the inconsistency between optimization loss and final simulation loss
- verified `loss(search) == loss(simulate)` on stable synthetic tests
- implemented stable `discover()` orchestration
- implemented and validated `GPStructureSearch`
- implemented and validated EvoGrow baseline behavior
- added shared stopping logic through `should_stop()`
- added sanity-check reporting and final simulation validation
- stabilized module include order and method registration
- added structured logging with timestamps and elapsed time
- golden harmonic-oscillator test works

Notes:

- Phase 1 is complete enough for research work.
- Further refinements are still allowed, but Phase 1 is no longer the main focus.

### Phase 2 - EvoGrow Variants

Status: IN PROGRESS

#### v1: simple growth

Status: DONE
Completed on: 2026-04-20

- flat term-wise growth over the available basis
- serves as the first EvoGrow baseline

#### v2: complexity tiers

Status: IN PROGRESS
Started on: 2026-04-21

Current state:

- `StagedPolynomialBasis` with 5 stages is implemented
- EvoGrow v2 staged basis release is implemented
- EvoGrow v2.1 stage-aware child generation is implemented

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

Status: NOT STARTED

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

## Current Priorities

Current priorities as of 2026-04-21:

1. Run full benchmark (6 variants × 10 systems × 5 seeds) and collect results.
2. Analyze summary_aggregate.csv: exact recovery rates, stage progression, wasted levels.
3. Identify failure cases and determine whether they are algorithmic or parametric.
4. Plan Paper 1 experiment section based on first real results.

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
- 10-system benchmark with 6 variants, 5 seeds, exact/surrogate split
- aggregate statistics (mean/std loss, exact_match_rate, wasted_levels)

## Known Gaps

- `utils/checks.jl` is still effectively a placeholder
- no train/validation split in discovery yet
- no noise injection utilities yet
- first benchmark results not yet analyzed (full run pending)
- no systematic comparison against GP and SINDy yet
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
