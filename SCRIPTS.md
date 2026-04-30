# EvoODE — Script Reference

Quick reference for all runnable scripts in this project.
For architecture, research context, and design decisions see `CLAUDE.md`.

---

## Experiments

### `experiments/generate_manifest.jl`

Creates a new experiment directory with all per-run folders and initial files.
Must be run once before `run_experiment.jl`.

```
julia experiments/generate_manifest.jl
```

Configuration is set via constants at the top of the script:

| Constant | Meaning |
|----------|---------|
| `EXPERIMENT_ID` | Unique name for the experiment directory (no spaces) |
| `PHASE` | Paper phase (`"A"`, `"B"`, `"C"`, `"D"`) |
| `HYPOTHESIS` | Short hypothesis identifier string |
| `RUN_TYPE` | `"exploratory"` or `"final"` |
| `INCLUDE_IN_PAPER` | `true` / `false` |
| `SEEDS` | List of RNG seeds, e.g. `[42, 123, 7, 99, 17]` |

Output: `experiments/<EXPERIMENT_ID>/` with `manifest.json`, `notes.md`, and one subfolder per run under `runs/`.

**Safety:** Aborts if the experiment directory already exists. Never overwrites.

---

### `experiments/run_experiment.jl`

Sequentially executes all queued runs in an experiment manifest.

```
julia experiments/run_experiment.jl <experiment_id>
```

Example:
```
julia experiments/run_experiment.jl paper1_phaseA_v1
```

Behavior:
- Skips runs with `status=finished`
- Restarts runs with `status=running` or `status=interrupted` from scratch
- A failed run is written as `status=failed` and the runner continues with the next run
- Writes per-run: `status.json`, `result.json`, `metrics.json`, `log.txt`, `summary.txt`

No configuration needed — all parameters come from per-run `config.json`.

---

### `experiments/aggregate.jl`

Scans all run folders and writes `run_registry.csv`. Safe to run at any time, including while the runner is active.

```
julia experiments/aggregate.jl <experiment_id>
```

Example:
```
julia experiments/aggregate.jl paper1_phaseA_v1
```

Output: `experiments/<experiment_id>/run_registry.csv`

Prints a status summary to stdout:
```
Experiment: paper1_phaseA_v1
Total runs in manifest: 300
  finished (success=true):  ...
  finished (success=false): ...
  failed:                   ...
  interrupted:              ...
  queued:                   ...
  corrupted:                ...
```

---

## Debugging and Profiling

### `studies/debug/debug_single.jl`

Runs a single EvoGrow discovery on Lotka-Volterra competition with verbose logging.
Use this to inspect algorithm behavior on a known system.

```
julia studies/debug/debug_single.jl
```

Output: `outputs/studies/debug/debug_lotka.log`, `outputs/studies/debug/debug_lotka.png`

Key constants at top of file:

| Constant | Meaning |
|----------|---------|
| `SEED` | RNG seed |
| `POP_SIZE` | EvoGrow population size |
| `N_LEVELS` | Maximum search levels |
| `VERBOSE` | Log verbosity (1=level summaries, 2=BFGS, 3=per-candidate) |
| `PROGRESSION_MODE` | `:stage_local` or `:global_plateau` |
| `USAGE_MODE` | `:hard`, `:soft`, or `:passive` |

---

### `studies/profiling/profile_init.jl`

Compares random initialization vs. pretuned (OLS warm-start) initialization
on Lotka-Volterra and Lorenz, across 3 seeds.

```
julia studies/profiling/profile_init.jl
```

Output:
- `outputs/studies/profiling/profile_init_summary.csv` — one row per run
- `outputs/studies/profiling/profile_init_levels.csv` — one row per level per run
- `outputs/studies/profiling/profile_<system>_seed<N>_<mode>.log` — one log per run

---

### `studies/generalization/generalization_study.jl`

Tests whether a structure discovered on one parameter set generalizes to unseen parameter sets
of the same ODE family after parameter refit only.
Covers 3 systems (Logistic growth, Lotka-Volterra, SIR), 2 variants, 3 seeds.

```
julia studies/generalization/generalization_study.jl
```

Output:
- `outputs/studies/generalization/generalization_summary.csv` — one row per (system, variant, seed)
- `outputs/studies/generalization/generalization_detail.csv` — one row per (system, variant, seed, test param set)
- `outputs/studies/generalization/gen_<system>_<variant>_seed<N>_train.log` — discovery log per training run
- `outputs/studies/generalization/gen_<system>_<variant>_seed<N>_test<M>.log` — discovery log per fresh baseline run

---

## Benchmarks

### `benchmarks/benchmark_evogrow.jl`

Exploratory benchmark runner. Runs all 6 variants on all 10 systems.
For formal Paper-1 experiments use the `experiments/` infrastructure instead.

```
julia benchmarks/benchmark_evogrow.jl
julia benchmarks/benchmark_evogrow.jl QUICK=true   # reduced settings for quick check
```

Key constants:

| Constant | Default | QUICK |
|----------|---------|-------|
| `POP_SIZE` | 10 | 5 |
| `EVO_LEVELS` | 20 | 8 |
| `BFGS_MAXITERS` | 200 | 50 |
| `SEEDS` | 5 seeds | 2 seeds |

Output: `outputs/benchmarks/summary.csv`, `outputs/benchmarks/summary_aggregate.csv`

---

### `benchmarks/run_odebench.jl`

Runs EvoODE on the full 63-system Strogatz JSON dataset.
Less curated than `benchmark_evogrow.jl` — use for broad exploration only.

```
julia benchmarks/run_odebench.jl
```

---

## Typical Workflows

### Start a new formal experiment

```
# 1. Edit EXPERIMENT_ID, PHASE, HYPOTHESIS etc. in generate_manifest.jl
julia experiments/generate_manifest.jl

# 2. Run all queued runs (can be interrupted and resumed)
julia experiments/run_experiment.jl <experiment_id>

# 3. Aggregate results at any point
julia experiments/aggregate.jl <experiment_id>
```

### Debug a specific system

```
# Edit system/settings in studies/debug/debug_single.jl
julia studies/debug/debug_single.jl
# Check outputs/studies/debug/debug_lotka.log
```

### Quick algorithm sanity check

```
julia benchmarks/benchmark_evogrow.jl QUICK=true
```
