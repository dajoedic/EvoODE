# EvoODE — Script Reference

Every runnable script in this project, what it is for, and how to call it.

For research context and design decisions see `CLAUDE.md`. For the cluster path — how code reaches
Orion and how a campaign is launched — see `docs/hpc_deployment_guide.md`.

All Julia scripts activate the project themselves, so `julia <script>` is sufficient. Inside the
container image the project lives at `/opt/EvoODE` and the invocation is
`julia --project=/opt/EvoODE /opt/EvoODE/<script>`.

**Sections**

1. [Campaign path](#1-campaign-path-phase-b-and-regression) — what the cluster runs
2. [Regression suite](#2-regression-suite) — the local correctness harness
3. [Support and configuration](#3-support-and-configuration)
4. [Benchmarks](#4-benchmarks)
5. [Phase A experiment infrastructure](#5-phase-a-experiment-infrastructure-frozen)
6. [Closed studies](#6-closed-studies-kept-for-provenance)
7. [Analysis pipeline](#7-analysis-pipeline-python)

---

## 1. Campaign path (Phase B and regression)

These four scripts are what runs on the cluster. They are used in this order.

### `studies/regression/generate_phase_b_manifest.jl`

Writes the campaign work list: one row per cell, plus per-dimension index lists that map a cluster
task number to a manifest row.

```
julia studies/regression/generate_phase_b_manifest.jl --output <dir>/manifest.csv --all-dimensions
```

| Flag | Meaning |
|---|---|
| `--output <path>` | Where `manifest.csv` goes. Index lists are written next to it |
| `--all-dimensions` | Write `indices_all.txt` and `indices_dim1.txt` … `indices_dim4.txt` |
| `--dimension <N>` | Only one dimension class |
| `--index-output <path>` | Explicit path for a single index list |

Environment: `EVO_PHASE_B_MANIFEST` supplies a default output path.

Prints `phase_b_fingerprint`, `rows`, `systems`, `representability_exact` / `_surrogate` and the row
count per dimension.

> **Run this exactly once per campaign, before any cell.** Cells only read these files. If every
> cell regenerated the manifest, concurrent writes to shared storage could make two cells disagree
> about what row *n* means.
>
> **Verify the fingerprint** against the expected value before starting cells. It is the cheapest
> check that code, configuration and support table are the ones you think they are.

Memory: needs about **8 GiB**. It loads all 63 systems; 2 GiB is not enough.

### `studies/regression/run_batch_cell.jl`

Runs **one** cell of a manifest and exits. The unit of work for any batch environment.

```
julia studies/regression/run_batch_cell.jl --manifest <path> --output-dir <dir> <MANIFEST_INDEX>
```

Environment alternatives: `EVO_BATCH_MANIFEST`, `EVO_BATCH_OUTPUT_DIR`.

Writes two files per cell into the output directory:

- `cell_<index>.jsonl` — the record, one line, with metrics and all work counters
- `cell_<index>.heartbeat.jsonl` — one event per level, plus `start` and `complete`

The heartbeat is the progress mechanism for batch runs. It is written to shared storage, so progress
is visible without cluster access.

> A runtime failure is caught and recorded in the record's `error` field, and the process still
> exits 0. **Exit code 0 does not mean the result is usable** — always check `error` is null.

### `studies/regression/run_k8s_indexed_cell.jl`

Wrapper for Kubernetes indexed Jobs. Resolves the task number to a manifest row, then delegates to
`run_batch_cell.jl`.

```
julia studies/regression/run_k8s_indexed_cell.jl [--dry-run]
```

| Environment | Meaning |
|---|---|
| `JOB_COMPLETION_INDEX` | Injected by Kubernetes. **Required** |
| `EVO_BATCH_INDEX_LIST` | Index list to read, default `/outputs/indices_dim1.txt` |
| `EVO_BATCH_MANIFEST` | default `/outputs/manifest.csv` |
| `EVO_BATCH_OUTPUT_DIR` | default `/outputs/tasks` |

`--dry-run` prints the resolved mapping and exits without computing — useful for checking an index
list before submitting a job.

> **Index bases differ.** `JOB_COMPLETION_INDEX` is 0-based, file lines are 1-based; the wrapper adds
> one and refuses an index beyond the end of the list. Slurm array IDs were 1-based, so the Slurm
> and Kubernetes paths are not interchangeable.

### `studies/regression/merge_batch_records.jl`

Consolidates per-cell records into the campaign history after all cells have finished.

```
julia studies/regression/merge_batch_records.jl --input-dir <tasks-dir> --history <history.jsonl>
```

Environment alternatives: `EVO_BATCH_TASK_DIR`, `EVO_BATCH_HISTORY_PATH`.

Refuses records whose `error` is not null, so a failed cell cannot silently enter the history.

---

## 2. Regression suite

### `studies/regression/run_regression.jl`

The local correctness harness: runs the regression systems across variants, seeds and
initial-condition sets, and appends to `studies/regression/history.jsonl`.

```
julia studies/regression/run_regression.jl [--short] [--porcelain]
```

| Flag / Environment | Meaning |
|---|---|
| `--short` | Reduced output |
| `--porcelain` | Machine-readable output |
| `FRESH=1` | Ignore existing history |
| `EVO_REGRESSION_HISTORY_PATH` | Alternative history file |
| `EVO_SCREENING_BUDGETS` | Toggle screening budgets |

A per-level progress display appears only when the output is attached to a terminal. In a batch pod
it is silent by design — use the heartbeat instead.

### `studies/regression/generate_manifest.jl`

The same idea as the Phase B generator, but for the **regression** campaign
(`VARIANTS × REGRESSION_SYSTEMS × REGRESSION_IC_SETS × REGRESSION_SEEDS`). Both campaigns are served
by the same cell entry point.

```
julia studies/regression/generate_manifest.jl --output <dir>/manifest.csv
```

Flags: `--output`, `--dimension`, `--index-output`.

---

## 3. Support and configuration

### `studies/regression/derive_phase_b_support.jl`

Derives the true support of every Phase B system from the dataset's right-hand sides and writes
`studies/regression/phase_b_support.json`.

```
julia studies/regression/derive_phase_b_support.jl
```

The support must be **exact** (reproduces the RHS to 1e-9) and **minimal** (no term removable). The
script aborts rather than writing a table that fails either test.

> **This changes the campaign fingerprint.** The derived support defines what `pruned_match` means,
> so it is part of the campaign identity. Do not rerun it casually.

Not an input file but worth knowing: `studies/regression/phase_b_config.jl` holds the Phase B system
list, variants, seeds and IC sets, and `studies/regression/diagnostic_systems.jl` the smaller
diagnostic set with hand-maintained expected stages.

---

## 4. Benchmarks

Exploratory and qualitative — best-effort reproducibility, not paper-grade.

### `benchmarks/benchmark_evogrow.jl`

Variant matrix over the benchmark suite.

```
julia benchmarks/benchmark_evogrow.jl
```

### `benchmarks/run_odebench.jl`

Runs the ODEBench suite from `benchmarks/data/strogatz_extended.json`.

```
julia benchmarks/run_odebench.jl
```

---

## 5. Phase A experiment infrastructure (frozen)

`paper1_phaseA_v1` is frozen and not used for final claims. These scripts remain so the frozen
experiment stays reproducible.

### `experiments/generate_manifest.jl`

Creates an experiment directory with per-run folders and initial files. Configuration via constants
at the top of the script (`EXPERIMENT_ID`, `PHASE`, `HYPOTHESIS`, `RUN_TYPE`, `INCLUDE_IN_PAPER`,
`SEEDS`). Aborts if the directory exists; never overwrites.

```
julia experiments/generate_manifest.jl
```

### `experiments/run_experiment.jl`

Runs all queued runs of a manifest sequentially. Skips finished runs, restarts interrupted ones,
continues past failures.

```
julia experiments/run_experiment.jl <experiment_id>
```

### `experiments/aggregate.jl`

Derives `run_registry.csv` from the per-run folders. Idempotent.

```
julia experiments/aggregate.jl <experiment_id>
```

---

## 6. Closed studies (kept for provenance)

These produced findings that the project's argument relies on. They are not part of any pipeline and
will most likely never run again — they are kept so that a published claim can be traced back to the
code that produced it. Each is a direct-execution script: `julia <path>`.

| Script | Question it answered |
|---|---|
| `studies/lookahead/stage_potential_probe.jl` | Can a per-equation stage cap be derived from the data before the search? — the paper's contribution |
| `studies/lookahead/derivative_estimator_probe.jl` | How much derivative error contaminates the promotion signal |
| `studies/lookahead/floor_gated_probe.jl` | Whether gating on the noise floor rescues the signal |
| `studies/lookahead/measure_dataset_grid_caps.jl` | The verified caps per system on the dataset grid |
| `studies/linesearch/diagnose_linesearch.jl` | Where the pathological line-search cost comes from |
| `studies/linesearch/diagnose_coupled_budget.jl` | The same on coupled systems |
| `studies/linesearch/replay_budget_20000.jl` | Whether the 20,000-evaluation budget changes any outcome |
| `studies/numerics/solver_tolerance_noise_floor.jl` | Which solver tolerance the error floor requires |
| `studies/numerics/system26_tolerance_screening.jl` | Whether the System 26 overshoot is numerical — it is not, it is algorithmic |
| `studies/gate2_do_or_die/readout.jl` | The Gate 2 decision readout for v3 |
| `studies/generalization/generalization_study.jl` | Generalization beyond the training trajectory. Closed: too few cells |
| `studies/profiling/profile_init.jl` | Random versus pretuned initialization |
| `studies/profiling/profile_eval_cost.jl` | Where evaluation time goes |
| `studies/phase1_diag/run_phase1_diag.jl` | Phase 1 diagnostics (closed 2026-04-20) |
| `studies/debug/debug_single.jl` | A single run with verbose logging and a plot |
| `studies/debug/compare_screening_variant.jl` | Screening on versus off |
| `studies/visualization/animate_search.jl` | Animation of a search trajectory |
| `studies/regression/verify_wp_b1.jl` | Acceptance check for WP-B1 (Phase B sampling protocol) |
| `studies/regression/verify_wp_c1.jl` | Acceptance check for WP-C1 |

---

## 7. Analysis pipeline (Python)

Conventions and environment: `analysis/CONVENTIONS.md`, dependencies in
`analysis/requirements.txt`.

| Script | Purpose |
|---|---|
| `analysis/scripts/aggregate/aggregate_run_registry.py` | Builds the analysis table from an experiment's run registry |
| `analysis/scripts/aggregate/classify_odebench_systems.py` | Exact / surrogate classification of the ODEBench systems |
| `analysis/scripts/aggregate/evaluate_hypotheses.py` | Evaluates H1–H4 against the aggregated data |
| `analysis/scripts/aggregate/phase1_diagnostic.py` | Phase 1 diagnostic evaluation |
| `analysis/scripts/plot/plot_exact_match_rates.py` | Support recovery rates |
| `analysis/scripts/plot/plot_stage_overshoot.py` | Stage overshoot per system |
| `analysis/scripts/plot/table_main_results.py` | The main results table |
| `analysis/status.py` | Status overview of an experiment |

> **Known gap:** this pipeline was written for `run_registry.csv` from the `experiments/`
> infrastructure. The cluster campaign writes per-cell `.jsonl` records that
> `merge_batch_records.jl` consolidates. Whether the pipeline consumes that format has not been
> verified. Test it on pilot data before relying on it for a campaign.
