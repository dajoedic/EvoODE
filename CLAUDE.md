# CLAUDE.md – EvoODE

## What This Project Is

EvoODE is a Julia research framework for **data-driven discovery of interpretable ODE systems from time-series data**. The framework supports both scalar (1D) and coupled (multi-dimensional) systems, with a research focus on coupled systems.

The core idea: instead of fitting a fixed library (SINDy) or searching globally from large structures (GP), EvoODE starts with minimal structures and grows them **incrementally and intelligently** — only increasing complexity when simpler structures are demonstrably insufficient.

This is a **PhD research project**. Code quality and scientific correctness matter more than speed. Every architectural decision must be justifiable as a research contribution.

---

## Scientific Position and Contribution

### Positioning vs. Baselines

| Method | Search Space | Growth Strategy | Complexity Control |
|--------|-------------|-----------------|-------------------|
| SINDy | Restricted: fixed linear library | None (direct regression) | L1 sparsity |
| GP | Unrestricted | Global: starts large, random | Parsimony pressure |
| **EvoODE** | **Unrestricted** | **Incremental: starts minimal, grows** | **Staged grammar + stopping criterion** |

### Core Scientific Claims (to be validated)
1. Starting small and growing incrementally is more efficient than global search
2. Grammar-staged complexity unlocking reduces wasted computation
3. The stopping/promotion criterion is a principled way to control complexity

### Open Research Questions (PhD core)
- What is the optimal stopping/promotion criterion? (stagnation vs. validation-based vs. information-theoretic)
- How should structure grow? (term-wise, equation-wise, coupling-aware)
- How to handle coupled systems specifically?
- How does performance scale with noise, sample size, coupling strength, and dimensionality?

---

## Project Structure

```
EvoODE/                          ← project root (CLAUDE.md lives here)
├── CLAUDE.md
├── src/                         ← the EvoODE Julia package
│   ├── EvoODE.jl                ← module entry point, all exports
│   ├── core/
│   │   ├── types.jl             ← Trajectory, DiscoveryOptions, DiscoveryResult
│   │   ├── discover.jl          ← main discover() pipeline
│   │   └── stopping.jl          ← shared stopping logic (all algorithms)
│   ├── structure/
│   │   ├── interface.jl         ← AbstractStructureSearch, StructureSpec
│   │   ├── evogrow.jl           ← EvoGrow (main algorithm, v2.1)
│   │   ├── gp.jl                ← GPStructureSearch (baseline)
│   │   ├── null.jl              ← NullStructureSearch (stub)
│   │   └── utils.jl             ← pretty-printing helpers
│   ├── basis/
│   │   ├── interface.jl         ← AbstractBasis (extendable!)
│   │   ├── polynomial.jl        ← PolynomialBasis (flat, all terms at once)
│   │   └── staged_polynomial.jl ← StagedPolynomialBasis (5 complexity stages)
│   ├── loss/
│   │   ├── interface.jl         ← AbstractLoss (extendable!)
│   │   └── mse.jl               ← MSELoss (state MSE on simulated trajectory)
│   ├── optimize/
│   │   ├── interface.jl         ← AbstractOptimizer (extendable!)
│   │   ├── bfgs.jl              ← BFGSOptimizer (primary, via Optimization.jl)
│   │   └── dummy.jl             ← DummyOptimizer (returns zeros, for testing)
│   ├── simulate/
│   │   ├── solve.jl             ← simulate() function
│   │   └── export.jl            ← CSV export helpers
│   ├── plotting/
│   │   └── plot_solution.jl     ← solve_and_save_plot()
│   └── utils/
│       ├── checks.jl            ← (stub, empty)
│       └── logging.jl           ← (stub, empty)
├── benchmarks/
│   └── strogatz_extended.json   ← ODEbench from ODEFormer paper (63 systems)
├── examples/                    ← example scripts (to be added)
└── test_evogrow_v2_lotka.jl     ← current integration test (Lotka-Volterra)
```

**The module structure is intentionally extensible.** New structure search algorithms, bases, losses, and optimizers are added by implementing the abstract interface and registering in `EvoODE.jl`. Do not hardcode algorithm-specific logic in `discover()`.

---

## Key Types

### `Trajectory`
```julia
struct Trajectory
    t::Vector{Float64}   # time points, length T
    x::Matrix{Float64}   # states, shape (T × dim)
end
```
- `dim = 1` for scalar ODEs, `dim > 1` for coupled systems
- Supports both coupled and uncoupled systems

### `StructureSpec`
```julia
struct StructureSpec
    active_idxs::Vector{Vector{Int}}  # length dim, each entry = active basis indices for that eq
end
```
- Index-based representation: each equation is a linear combination of selected basis terms
- Example for 2D Lotka-Volterra: `[[1,3,5], [3,4]]` means eq1 uses basis terms 1,3,5; eq2 uses 3,4
- **NOTE**: Expression Trees (nested terms like `sin(x*y)`) are planned for later phases but NOT implemented. The current index-based representation is a deliberate Phase 1 simplification.

### `DiscoveryOptions`
Controls stopping behavior (algorithm-agnostic):
- `verbose`: 0=silent, 1=basic, 2=detailed, 3=debug
- `min_levels`, `max_levels`: safety bounds
- `loss_tol`: absolute convergence threshold
- `plateau_window`, `plateau_tol`, `plateau_relative`, `plateau_rtol`: stagnation detection

### `DiscoveryResult`
```julia
struct DiscoveryResult
    structure::Any              # discovered StructureSpec (or algorithm-specific)
    params::Vector{Float64}     # fitted parameters
    loss::Float64               # validated loss (on simulated trajectory)
    objective::Float64          # search objective (loss + λ * complexity)
    meta::NamedTuple            # diagnostics: structure, build, optimize, search, prediction, sanity
end
```

---

## Core Pipeline

```
discover(traj; structure, optimizer, basis, loss, options)
    │
    ├── 1. search_structure(strategy, traj, basis, loss, optimizer, options)
    │       → returns (structure, params, loss, objective, meta)
    │
    ├── 2. build_rhs(structure, basis)
    │       → returns (f!, n_params, build_meta)
    │       → f! has signature f!(du, u, params, t)
    │
    ├── 3. simulate(f!, params, traj; ...)
    │       → solves ODE, returns Yhat (T × dim)
    │
    └── 4. validate: evaluate_loss(loss, Yhat, traj.x)
            → DiscoveryResult
```

**Important**: `discover()` does NOT re-fit parameters after structure search. It only re-fits if `length(params) != n_params` (parameter count mismatch guard).

---

## Algorithm: EvoGrow

### Key Parameters
```julia
Base.@kwdef struct EvoGrow <: AbstractStructureSearch
    pop_size::Int = 20                # population size
    n_levels::Int = 5                 # max growth levels (also capped by options.max_levels)
    children_per_parent::Int = 2      # children generated per parent per level
    max_terms_per_eq::Int = 5         # hard cap on terms per equation
    λ::Float64 = 1e-3                 # complexity penalty: objective = loss + λ * n_params
end
```

### Growth Loop
1. Initialize population: each individual has 1 random term per equation
2. Per level: evaluate parents → generate children → evaluate children → select top `pop_size` by objective
3. Objective = loss + λ * n_params (penalizes complexity)
4. Stopping check via `should_stop()` → if plateau AND more stages available → unlock next stage
5. Stage-aware child generation: when a new stage is unlocked, children preferentially include terms from the new stage

### Staged Complexity (StagedPolynomialBasis, default 5 stages)
Stage progression is triggered by plateau detection in `should_stop()`:
- **Stage 1**: Linear terms: `u1, u2, ..., udim`
- **Stage 2**: Self-quadratic: `u1^2, u2^2, ..., udim^2`
- **Stage 3**: Cross terms: `u1*u2, u1*u3, ..., u(dim-1)*udim`
- **Stage 4**: Cubic (self only): `u1^3, u2^3, ..., udim^3`
- **Stage 5**: Trigonometric: `sin(u1), cos(u1), ..., sin(udim), cos(udim)`

For non-staged bases (e.g. `PolynomialBasis`), all terms are available from the start (fallback behavior).

---

## Algorithm: GPStructureSearch (Baseline)

Standard genetic programming over the full basis. Used as comparison baseline only.
- Tournament selection (configurable k)
- Crossover: per-equation swap between parents
- Mutation: add/remove/replace a random term
- No staged complexity — full basis available from start

---

## Stopping Logic (`should_stop`)

Shared across all algorithms:
1. **Hard limit**: stop if `level >= max_levels`
2. **Min levels**: never stop before `min_levels`
3. **Loss tolerance**: stop if `best_loss < loss_tol`
4. **Plateau (absolute)**: stop if improvement over `plateau_window` steps < `plateau_tol`
5. **Plateau (relative)**: stop if relative improvement < `plateau_rtol`

For EvoGrow specifically: plateau triggers stage promotion (not termination) if more stages are available.

**This stopping/promotion criterion is a core research contribution — treat it carefully. Do not simplify or remove nuance here.**

---

## Dependencies (Julia 1.11.5)

| Package | Role |
|---------|------|
| `DifferentialEquations.jl` | ODE solving in `simulate()` |
| `SciMLBase.jl` | SciML interface types |
| `Optimization.jl` + `OptimizationOptimJL.jl` | BFGS parameter optimization |
| `Plots.jl` | Plotting |
| `Statistics` (stdlib) | `mean()` in MSELoss |
| `Random` (stdlib) | RNG seeding |
| `Printf` (stdlib) | Formatted output |
| `Logging` (stdlib) | Log suppression |

---

## Benchmark Dataset: ODEbench / strogatz_extended.json

Location: `benchmarks/strogatz_extended.json`
Source: ODEFormer paper (extended Strogatz benchmark)

**Dataset statistics:**
- 63 total systems
- 23 scalar (dim=1), 28 coupled 2D (dim=2), 10 coupled 3D (dim=3), 2 coupled 4D (dim=4)
- 40 systems have dim > 1 (coupled)

**JSON format per entry:**
```json
{
  "id": 24,
  "eq": "x_1 | - c_0 * x_0",         // pipe-separated equations (one per dimension)
  "dim": 2,
  "consts": [[1.5, 1.0, 1.0, 3.0]],  // parameter sets
  "init": [[1.2, 1.1]],               // initial conditions
  "init_constraints": "...",
  "const_constraints": "...",
  "eq_description": "Harmonic oscillator without damping",
  "const_description": "...",
  "var_description": "...",
  "source": "strogatz p.XX",
  "substituted": [["expr_with_substituted_consts"]],
  "solutions": [...]                  // pre-computed solutions
}
```

**Usage**: The benchmark will be used to evaluate EvoGrow vs GP vs SINDy across varied system complexity, dimension, and coupling strength.

---

## Current Status

### Implemented and Working
- `discover()` pipeline (end-to-end)
- `EvoGrow` v2.1 with staged complexity and stage-aware child generation
- `GPStructureSearch` baseline
- `StagedPolynomialBasis` (5 stages) and `PolynomialBasis` (flat)
- `BFGSOptimizer` (primary optimizer)
- `MSELoss` (state MSE on simulated trajectory)
- `DummyOptimizer` (for testing pipeline without optimization)
- Lotka-Volterra integration test (`test_evogrow_v2_lotka.jl`)
- Plotting and CSV export

### Stubs / Not Yet Implemented
- `utils/checks.jl` — empty
- No train/validation split — currently evaluates on training data only
- No noise injection for robustness testing
- Benchmark scripts exist, but benchmarking is not yet systematic or unified
- No systematic comparison against GP or SINDy
- Expression Trees — not implemented (planned for Phase 5)

### Known Issues / Architectural Gaps
- Julia environment/test execution still needs cleanup and faster verification
- No parameter count sanity check before optimization (mismatch guard is a workaround)
- `simulate()` can fail silently on stiff/diverging cases — needs better error handling

---

## Roadmap

### Phase 1 — Stable Core (current)
Goal: EvoGrow works reliably on standard benchmark systems, GP baseline works, pipeline is stable

Missing for Phase 1 completion:
- [ ] Train/validation split in evaluation
- [ ] Benchmarking pipeline for `strogatz_extended.json`
- [ ] Proper `Manifest.toml` / `Project.toml`
- [ ] Noise injection utilities
- [ ] Stabilize `simulate()` for stiff/diverging cases

### Phase 2 — EvoGrow Variants
- v1: flat growth (already exists as PolynomialBasis fallback)
- v2: staged complexity tiers (current, v2.1)
- v3: equation-wise growth (grow one equation at a time)
- v4: coupling-aware growth (bias toward cross terms when coupling is suspected)

### Phase 3 — Systematic Benchmarking
Benchmark dimensions:
- Noise level (σ = 0, 0.01, 0.05, 0.1)
- Sampling density (T = 50, 100, 200, 500)
- Coupling strength (from strogatz dataset: varies naturally)
- Dimensionality (dim = 1, 2, 3, 4 from strogatz dataset)

### Phase 4 — Paper 1
Compare EvoGrow (v1, v2) vs GPStructureSearch vs SINDy on strogatz_extended benchmark.
Target: ICML, NeurIPS, or JMLR (quality over prestige, but no low-tier venues).

### Phase 5 — Advanced Methods
- Expression Trees (nested/composite terms)
- Error-guided growth
- Backtracking
- Hybrid search
- Validation-based stage promotion
- Multi-hypothesis models

---

## Design Principles

1. **Modular**: every component is swappable via abstract interface (`AbstractStructureSearch`, `AbstractBasis`, `AbstractLoss`, `AbstractOptimizer`). New implementations go in the appropriate subfolder and are exported from `EvoODE.jl`.

2. **Reproducible**: always seed RNG via `DiscoveryOptions.rng_seed`. Results must be exactly reproducible.

3. **Interpretable output**: `DiscoveryResult` always contains a human-readable equation string. The `structure_with_params_string()` utility in `structure/utils.jl` handles this.

4. **Minimal complexity**: do not add features without a direct research motivation. Complexity is the enemy.

5. **Verbosity levels**: all logging goes through `options.verbose` (0=silent, 1=basic, 2=detailed, 3=debug). No hardcoded `println` statements outside this pattern.

6. **Metadata**: all algorithms return a `meta::NamedTuple` with diagnostics. Never discard intermediate results silently.

---

## Non-Goals

- **No GPU work** (Phase 1-4 scope)
- **No UI** (ever, unless explicitly decided)
- **No PDE expansion** (out of scope for this PhD)
- **No premature optimization** (correctness first)
- **No unnecessary dependencies** (keep the package minimal)

---

## Coding Conventions

- **Language: Julia only.** All code in this project must be written in Julia 1.11.5. No Python, R, shell scripts, or other languages. No exceptions.
- Julia 1.11.5
- Module: `module EvoODE`
- All public API exported from `EvoODE.jl` — if it's not exported there, it's internal
- Keyword constructors via `Base.@kwdef` for all structs with defaults
- Interface functions (e.g. `search_structure`, `build_rhs`) defined in `interface.jl` files using `error("not implemented")` as default
- Mutable structs (`mutable struct`) only for population individuals that are updated in-place during search
- Parameter vectors are always `Vector{Float64}`
- ODE RHS always has signature `f!(du, u, params, t)` (in-place, SciML convention)
- `meta` fields use `NamedTuple` syntax: `(key = value, key2 = value2)`

---

## Guiding Rule

**Every change must support a research hypothesis. If you cannot state which research question a change addresses, do not make it.**
