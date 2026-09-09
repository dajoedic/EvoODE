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
7. [Reset studies](#7-reset-studies-wp-n-september-2026) — the constant term, generalization, the baseline
8. [Analysis pipeline](#8-analysis-pipeline-python)

---

## 1. Campaign path (Phase B and regression)

These four scripts are what runs on the cluster. They are used in this order.

> **Every Job manifest must set `ttlSecondsAfterFinished`.** A finished Kubernetes Job keeps its
> pods forever unless told otherwise. By 2026-08-18 that had left 105 `Completed` pods behind —
> 85 % of every pod in a namespace shared with other groups. The templates in `k8s/` set it to one
> hour: long enough to read a log, and nothing is lost, because the results are the records on NFS
> and not the pod logs.
>
> **`generate_manifest.jl` writes an index list only together with `--dimension`.** Passing
> `--index-output` on its own is inert — the block is guarded by `--dimension`. There is no
> all-rows list for the regression campaign, only per-dimension lists, so it needs one bootstrap
> per dimension, run **sequentially** because they all write the same `manifest.csv`.
>
> **The NFS share is read-only from Windows.** A hand-picked index list cannot be placed there, so
> the indexed-cell path does not fit a non-contiguous set of rows. Use
> `k8s/phase_b_single_cell_job.yaml` instead: `run_batch_cell.jl` takes the manifest index as a
> positional argument and needs no list at all.
>
> **The commands in this file are Bash; the working environment is PowerShell**, where `sed` does
> not exist. Translate before pasting.

### `studies/regression/generate_phase_b_manifest.jl`

Writes the campaign work list: one row per cell, plus index lists that map a cluster task number to
a manifest row. With `--all-dimensions`, it writes `indices_all.txt`, `indices_cost_desc.txt`, and
the per-dimension lists `indices_dim1.txt` ... `indices_dim4.txt`.

```
julia studies/regression/generate_phase_b_manifest.jl --output <dir>/manifest.csv --all-dimensions
```

| Flag | Meaning |
|---|---|
| `--output <path>` | Where `manifest.csv` goes. Index lists are written next to it |
| `--all-dimensions` | Write `indices_all.txt`, `indices_cost_desc.txt`, and `indices_dim1.txt` ... `indices_dim4.txt` |
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
>
> **Campaign start order:** build and substitute the bootstrap manifest, run it, verify that
> `manifest.csv`, `indices_all.txt`, `indices_cost_desc.txt`, and `indices_dim1.txt` through
> `indices_dim4.txt` exist, then start `k8s/phase_b_indexed_campaign_job.yaml`, watch the Job, and
> clean it up after completion. Use the command sequence in
> `docs/hpc_deployment_guide.md` Section 7 as the maintained source for login, apply, wait, logs,
> observe, and delete commands.

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

`--input-dir` must contain final per-cell records only. If heartbeat streams are mixed into the
same directory, this script can merge those heartbeat rows instead of campaign records; the
heartbeat shape is recognizable by about 15 fields, an `event` field, and missing `git_hash` /
`loss` fields, while Phase-B final records have 77 fields.

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

If a default manifest or default dimension index already exists and no explicit path is passed, the
script writes a timestamp-suffixed sibling instead of overwriting it. Passing `--output` and
`--index-output` keeps the caller-owned target explicit.

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

Closed studies that write CSVs or reports under `outputs/` accept `--output-dir <dir>`. Closed
studies that write a Markdown report under `docs/` also accept `--report <path>`. Existing direct
invocations still work; if the default target already contains files, the script writes a
timestamp-suffixed sibling instead of silently overwriting existing evidence.

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
| `studies/lookahead/audit_exact_stage_cap_horizons.jl` | The horizon audit over all 20 exact systems, both IC sets, horizons 2-5 - the measurement behind `lookahead_horizon = 5` |
| `studies/lookahead/diagnose_stage_cap_failures.jl` | Why five equation rows still truncated: analytic derivatives repair all five, a 5x5 threshold sweep repairs none |
| `studies/lookahead/wp_c4_stage_cap_doubt_band_report.jl` | The doubt band that was added and then removed again |
| `studies/lookahead/wp_c5_stage_cap_binary_audit.jl` | The closing audit: 0 truncated rows of 80, 48 finite caps |
| `studies/lookahead/wp_v1_stage_cap_reliability.jl` | Whether the reopen threshold can be selected from data - leave-one-system-out says no |
| `studies/regression/analyze_wasted_search_levels.jl` | The level-budget question: what a global "stop after k silent levels" would cost (WP-B1) |
| `studies/representation/wp_r1_full_basis_reference.jl` | The search-free reference fit: how well the full basis approximates surrogate systems in derivative space |

The two audit scripts that write a Markdown report take `--report <path>`:

```bash
julia studies/lookahead/audit_exact_stage_cap_horizons.jl --report docs/wp_c1_stage_cap_horizon_audit.md
julia studies/lookahead/wp_v1_stage_cap_reliability.jl --report docs/WP-V1.md
```

`studies/output_path_guard.jl` is **not** a runnable script. It is the shared helper the closed
studies include for `--output-dir` / `--output` handling and for the guard that writes a
timestamp-suffixed sibling instead of overwriting existing evidence.

---

## 7. Reset studies (WP-N, September 2026)

The September 2026 review found four gaps the campaign was not designed to close: no constant term
in the basis, no persisted coefficients, no held-out evaluation, and no baseline ever run. These
scripts are the measurements that closed them. Unlike section 6 they are **not** closed - they are
the current line of work, and the numbers they produce are the ones under external discussion.

They run in this order, because each consumes the previous one's records.

### `studies/regression/wp_n1_basis_probe.jl`

Compares the default staged basis against `staged_polynomial_basis_with_constant` on the same cells,
and persists the fitted coefficients alongside the term names.

```bash
julia --project=. --startup-file=no studies/regression/wp_n1_basis_probe.jl --dim=1
```

`--dim=2` is prepared but **unstarted**. Only the user starts long runs.
Use `--limit=N` (with the equals sign) for a bounded smoke run over the first `N` cells.

> **This serial path is for dimension 1 only.** dim 2 costs **~1,200 core hours** — measured from the
> campaign's own dim-2 arm, which is the same 336 cells (1,167.5 h, mean 3.47 h per cell). The
> "114 core hours" quoted until 2026-09-09 was unsourced and wrong by an order of magnitude. Serial
> execution would take roughly seven weeks; use the cluster path below.

### `studies/regression/generate_wp_n1_basis_probe_manifest.jl`

Generates the manifest and index list that let the basis probe run on the cluster through the same
path as the campaign — `run_k8s_indexed_cell.jl` → `run_batch_cell.jl`. The probe's two basis modes
are resolved as variants by `phase_b_variant`, so there is no second execution path.

```bash
julia --project=. --startup-file=no studies/regression/generate_wp_n1_basis_probe_manifest.jl \
  --dimension 2 --output outputs/wp_n1_dim2_probe/manifest.csv \
  --index-output outputs/wp_n1_dim2_probe/indices_dim2.txt
```

Expected: **336 rows** for dim 2 (28 systems × 2 bases × 2 IC sets × 3 seeds), 132 for dim 1. The
generator prints `base_phase_b_fingerprint`, which **must** stay `604e79733b22d64d` — the campaign
identity depends on it.

Cluster jobs: `k8s/wp_n1_basis_probe_dim2_smoke_job.yaml` (3 cells) and
`k8s/wp_n1_basis_probe_dim2_campaign_job.yaml` (336 cells, `parallelism: 32`, ~47 h wall clock —
floored by the longest single cell at 47 h, so more pods do not help).

**Equivalence to the serial path is verified** (WP-N9, 2026-09-09): 10 dim-1 cells over systems 2, 3
and 6 in both bases reproduce `loss`, `pruned_match` and the term set exactly, including the case
where the two bases disagree (system 3, constant basis: `pruned_match` False, 3 terms). Re-check with
`analysis/scripts/aggregate/compare_wp_n1_manifest_equivalence.py` after any change to the path.

The script aborts before writing records if `git_hash` is missing, empty, `not_collected`, or
`unknown`; that means the run lacks the git identity required for configuration decisions. Set
`WP_N1_ALLOW_PLACEHOLDER_IDENTITY=1` only for development runs; records are then marked with
`probe_identity_mode = "development"`.

> **The existing dim-1 records predate this fix** (WP-N8, 2026-09-09) and carry
> `git_hash = "not_collected"` with no `probe_identity_definition` field. They are deliberately left
> unchanged — a retrofitted hash would be an unverifiable claim. New records carry
> `probe_identity_definition = "collected_git_identity_v1"`, so the two sets are distinguishable, and
> the resume logic treats records without the identity fields as not completed. **Do not merge the
> two sets in one evaluation.**

Writes `outputs/wp_n1_dim1_probe/history.jsonl`, which the next three scripts read.

### `studies/regression/wp_n3_oracle_refit.jl`

Hands the search the *true* structure and fits only parameters - the reference point that separates
"the search failed" from "the parameter fit failed".

```bash
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n3_oracle_refit --fresh
```

Smoke test: add `--limit 3` and a separate `--output-dir`.

### `studies/regression/wp_n4_multistart_refit.jl`

The same refit at k parameter starts, which is how the multistart was found to be load-bearing: a
single start hits the sentinel loss `1e6` in 15 of 102 cells, k = 3 in none.

```bash
julia --project=. --startup-file=no studies/regression/wp_n4_multistart_refit.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n4_multistart_refit --starts 10 --fresh
```

Write-up and the placement against SINDy / PySR / ODEFormer / ProGED: `docs/WP-N4.md`.

### `studies/regression/wp_n5_ic_generalization.jl`

The first held-out evaluation in the project. Rebuilds the model from its record, keeps the
parameters, and integrates from the *unseen* initial condition.

```bash
julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n5_ic_generalization --fresh
```

Smoke test: `--limit 6`. The control that makes the result trustworthy is inside the script - 132 of
132 reconstruction probes must come out exact to zero, otherwise `model_terms` is not doing its job.

### `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py`

SINDy on **identical** trajectories - the first baseline the project has ever run. Ten
configurations are reported in full and none is selected, so the number is not tuned in our favour.

```bash
python analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py --config analysis/configs/wp_n6_sindy_baseline.json
```

Error path on a deliberately broken fixture, which must fail rather than report success:

```bash
python analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py --config analysis/configs/wp_n6_sindy_error_fixture.json
```

Write-up, cost line and caveats: `docs/WP-N6.md`.

### `analysis/scripts/aggregate/aggregate_wp_n2_pruning_sensitivity.py`

How much of `pruned_match` is the pruning rule rather than the search. Over a 24-rule grid the sum
of hits and both error types is constant, so the threshold is a zero-sum dial.

```bash
python analysis/scripts/aggregate/aggregate_wp_n2_pruning_sensitivity.py --config analysis/configs/wp_n2_pruning_sensitivity.json
```

---

## 8. Analysis pipeline (Python)

Conventions and environment: `analysis/CONVENTIONS.md`, dependencies in
`analysis/requirements.txt`.

| Script | Purpose |
|---|---|
| `analysis/scripts/aggregate/aggregate_run_registry.py` | Builds the analysis table from an experiment's run registry |
| `analysis/scripts/aggregate/analyze_pretuning_contrast.py` | Paired Phase-B pretuning contrast with naive and cluster-robust tests |
| `analysis/scripts/aggregate/classify_odebench_systems.py` | Exact / surrogate classification of the ODEBench systems |
| `analysis/scripts/aggregate/verify_campaign_registry.py` | Checks converted campaign registry invariants before aggregation |
| `analysis/scripts/aggregate/evaluate_hypotheses.py` | Evaluates H1–H4 against the aggregated data |
| `analysis/scripts/aggregate/phase1_diagnostic.py` | Phase 1 diagnostic evaluation |
| `analysis/scripts/aggregate/aggregate_phaseb_descriptive_tables.py` | Descriptive tables T1-T5: fit quality, support recovery, stage economy, robustness |
| `analysis/scripts/aggregate/aggregate_phaseb_heartbeat_waste_systems.py` | Level waste from the heartbeat stream - defined for all 63 systems, unlike `wasted_levels` |
| `analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py` | The seed-collapse mechanism: pretuning collapses diversity on support, R2 and loss |
| `analysis/scripts/plot/plot_exact_match_rates.py` | Support recovery rates |
| `analysis/scripts/plot/plot_stage_overshoot.py` | Stage overshoot per system |
| `analysis/scripts/plot/table_main_results.py` | The main results table |
| `analysis/scripts/plot/table_phaseb_descriptive_results.py` | Renders T1-T5 to CSV and LaTeX under `analysis/tables/<id>/` |
| `analysis/scripts/plot/table_phaseb_heartbeat_waste_systems.py` | Renders the waste summary and the per-system table |
| `analysis/status.py` | Status overview of an experiment |

Campaign bridge for Phase-B data:

```
studies/regression/merge_batch_records.jl final records -> experiments/<id>/history.jsonl
analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py -> experiments/<id>/run_registry.csv
analysis/scripts/aggregate/verify_campaign_registry.py -> invariant check
analysis/scripts/aggregate/aggregate_run_registry.py -> analysis/data/<id>/aggregate_by_variant_system.csv
```
