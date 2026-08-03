# Paper 1 — Phase A Reproducibility Protocol

Moved out of `CLAUDE.md` on 2026-08-03. **Historical record of the frozen `paper1_phaseA_v1`
experiment** (10 systems x 6 variants x 5 seeds = 300 runs, frozen 2026-05-11, not used for final
paper claims). It documents exactly what was executed, including hyperparameters that no longer
apply to the final variant or to Phase B.

For the **Phase B** protocol see `docs/paper1_odebench_protocol_alignment.md` §3.
For the Phase A claims, hypotheses and evidence rules see `docs/paper1_study_protocol.md`.

---


## 1. Scope

This document defines the exact experimental setup used for the frozen Phase A experiment.
All configurations listed here are fixed for reproducibility.
Any change to these parameters requires creating a new experiment block with a new identifier and explicit versioning.
This section documents what is implemented and executed, not aspirational behavior.

---

## 2. Compared Methods

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

## 3. Benchmark Dataset

The benchmark consists of exactly 10 systems drawn from `benchmarks/data/strogatz_extended.json`.

### Exact systems (8 systems)

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

### Surrogate systems (2 systems)

| ID | Name | Dim | Expected stage | Note |
|----|------|-----|----------------|------|
| 23 | Overdamped pendulum | 1 | 5 | Constant offset outside basis. Evaluate stage reached and trig term usage. |
| 37 | Van der Pol oscillator | 2 | 4 | Cubic cross term `u1^2*u2` outside basis. Evaluate stage reached and cubic term usage. |

Exact and surrogate systems must never be mixed in a single structure-correctness metric.
Exact systems are evaluated on `exact_support_match`.
Surrogate systems are evaluated on stage reached, target term usage, and fit quality.

---

## 4. Fixed Hyperparameters

All parameters below are fixed for Paper 1.
No parameter may vary across runs except `seed`.

### EvoGrow (all variants)

```
pop_size             = 10
n_levels             = 20
children_per_parent  = 2
max_terms_per_eq     = 6
λ                    = 1e-3
min_levels_per_stage = 2   (STAGE_MIN_LEVELS)
new_term_bias_prob   = 0.75 (SOFT_BIAS, used by :soft and :hard modes)
```

### GP baseline

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

### DiscoveryOptions (shared across all variants)

```
min_levels       = 2
max_levels       = 50
loss_tol         = 1e-8
plateau_window   = 3
plateau_tol      = 1e-4
plateau_relative = false
plateau_rtol     = 1e-3
```

### Optimizer

```
BFGSOptimizer(maxiters = 200, time_limit_s = 300.0)
```

### Trajectory generation

Trajectories are generated from the ground-truth ODE using `Tsit5()` with `abstol = 1e-9`, `reltol = 1e-9`.
Each system specifies its own `u0`, `tspan`, and `T` as defined in the BENCHMARKS table in `benchmark_evogrow.jl`.

### Effective minimum levels per stage

Due to the interaction between `plateau_window` and `min_levels_per_stage`:

```
effective_min = max(min_levels_per_stage, plateau_window + 1) = max(2, 4) = 4
```

This means each stage requires at least 4 levels before promotion is possible.
`n_levels = 20` is sufficient to reach Stage 4, covering all systems in the benchmark.

---

## 5. Seed Configuration

Exactly five seeds are used per (variant, system) cell:

```julia
seeds = [42, 123, 7, 99, 17]
```

Every combination of (variant, system, seed) is executed independently.
Total number of runs: 6 variants × 10 systems × 5 seeds = 300 runs.

---

## 6. Metrics

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

### Aggregation metrics (per variant × system cell, across seeds)

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

## 7. Execution Procedure

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

## 8. Output Artifacts

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

## 9. Aggregation Rules

Aggregation groups runs by `(variant_slug, system_id)`.
Within each group, `n_valid` is the count of runs with non-NaN loss.
All aggregate statistics (mean, std, rates) are computed over valid runs only.

Exact and surrogate systems are reported in separate analysis blocks.
`exact_match_rate` is only meaningful for exact systems and must not be reported for surrogate systems.
Surrogate systems are assessed separately on stage reached, target term usage, and fit quality.

These two categories must never be merged into a single structure-correctness metric.

---

## 10. Versioning

Every run records the current git commit hash at the time of execution (from `config.json: git_hash`).
Every run records `started_at` and `finished_at` timestamps in ISO 8601 format.

Before publishing results, verify that all runs were executed from the same commit hash.
If any run used a different hash, re-run that cell and record the discrepancy in the paper supplement.

---

## 11. Paper 1 Freeze

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
