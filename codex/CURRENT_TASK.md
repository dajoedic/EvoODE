# WP-N44 — P-04 restart curve: Orion manifest and Python aggregator
**Language: Python**

## Why

Plan `docs/paper1_phaseC_benchmark_plan.md` §9.8 was frozen by the user on 2026-10-13. It specifies the restart
curve (Abl-3): the existing Julia runner `studies/regression/wp_n4_multistart_refit.jl` in Phase C mode refits the
true structure (and the found ∩ true structure) of every exact C-1 cell from 10 seeded starts with one attempt each.
The runner needs **no change**: it already stores, per start, `loss`, `r2`, `start_index`, `start_seed` and `fit_meta`
(including `loss_evals`). What is missing is the Orion manifest and an aggregator that computes the §9.8 metrics
from the raw shard outputs. Read §9.8 in full before starting; it is the specification, this file only assigns the
work.

The Julia `--collect` mode of the runner writes some CSVs, but it lacks the cost axis, the threshold grid, the strata
and the control. Do not extend the Julia script; build the aggregation in Python so that it can be run and tested here.

## Inputs

1. **Raw runner output** (after the Orion run, not available yet): one `starts.jsonl` per shard under
   `<output-dir>/shard_<i>_of_036/`, written by `wp_n25_shard_path`. One JSON row per cell, fields as built in
   `_base_record_phase_c` and `_run_record_phase_c` of `wp_n4_multistart_refit.jl`: cell metadata
   (`cell_key`, `system_id`, `initial_condition_set`, `seed`, `original_loss`, `oracle_structure`,
   `true_structure`, `oracle_structure_hit`, `error`, …), `reference_starts` and `oracle_starts` (lists of per-start
   dicts as returned by `_fit_fixed_structure_once`). Read the Julia code to get the exact field names; do not guess.
   Note that the runner fits the oracle structure for every cell, also where it equals the truth.
2. **C-5 oracle output (control reference):** `outputs/wp_n3_oracle_refit_phase_c/shard_*_of_036/results.jsonl`,
   fields `reference_loss` / `reference_fit_meta` (with `accepted_attempt`, `fit_attempts`, `loss_evals`). Present
   locally.
3. **C-1 search records** for the duplicate-rate distribution: `experiments/paper1_phaseC_v1/run_registry.csv`
   and the records it points to; the per-cell field is `structure_repeat_quantiles` (also present in the raw C-1
   records under `outputs/phase_c_campaign_221a3a7/`). Use whichever is tracked or present; say which in the report.
4. **WP-T1f cold starts** (independent reference, bound ∞):
   `analysis/data/wp_t1d_neighbourhood/wp_t1f_campaign_1db11932c4335e480d374c7de1be35593b62b447/truth_cold_by_cell.csv`.
5. **Feasibility labels:** systems 54, 55, 56, 57, 58, 59 are infeasible under the bound `[-10, 10]`; all other exact
   systems are feasible (plan §9.2, §9.8). Take the system dimension from the Phase C support / classification
   files the existing aggregators use; do not hard-code dimensions.

## Deliverables

1. **`k8s/phase_c_c5_restart_curve_job.yaml`** — modelled on `k8s/phase_c_c5_oracle_job.yaml`: indexed Job,
   36 completions, round-robin shards via `JOB_COMPLETION_INDEX`, image placeholder `<COMMIT_SHA>`, input
   `/outputs/phase_c_c5_restart_curve_<COMMIT_SHA>/input/history.jsonl`, output
   `/outputs/phase_c_c5_restart_curve_<COMMIT_SHA>/out`, `--campaign paper1_phaseC_v1 --starts 10`.
   **No `activeDeadlineSeconds`** (project rule: no hard time cuts). Keep `ttlSecondsAfterFinished`, labels in the
   same scheme with component `c5-restart-curve`. A header comment states the cost from §9.8 (expected ~100
   core hours, upper bound 338 h, largest cell bound ~17 h) and that the figures are capacity planning, not evidence.
2. **`analysis/scripts/aggregate/aggregate_phasec_restart_curve.py`** — reads all shard `starts.jsonl` files from
   `--input-dir`, refuses to run if the cell set is not exactly the 180 expected exact C-1 cells (no duplicates, no
   missing cells, no row with a non-null `error`) unless `--allow-incomplete` is given, and writes to `--output-dir`:
   - **control:** for every cell where the C-5 oracle accepted attempt 1, reference start 1 loss compared with the
     C-5 reference loss; bit-identical required. Output a per-cell control table and exit non-zero on any deviation
     (hard stop, §9.8). Cells where C-5 accepted a later attempt are listed as "not comparable", not as failures.
   - **curve table:** per k ∈ {1, 2, 3, 5, 10} × structure (reference, oracle) × stratum: n cells, cumulative
     `loss_evals` over the first k starts (sum and quantiles q10/q50/q90 per cell), R² > 0.9 count and rate of the
     best-of-k fit, sentinel count (loss ≥ 1e6), `reaches_or_beats_original` count, and the full loss threshold grid
     1e-12, 1e-10, 1e-8, 1e-6, 1e-4 (count and share below each). Best-of-k = the start with minimal loss among
     `start_index ≤ k`, exactly as `_best_result` in the Julia script.
   - **strata (§9.8 item 5), never averaged across:** dimension; feasible versus infeasible; within dimension 3,
     systems 52 and 57 versus the other dimension-3 systems; plus an `all_feasible` stratum.
   - **per-cell first-hit table:** smallest k at which the best-of-k reference fit reaches R² > 0.9, or "not within
     10".
   - **k = 3 reading (§9.8, pre-declared):** on the feasible reference cells, R² > 0.9 rate at k = 3 and at k = 10,
     their difference in percentage points, and a boolean "within 5 pp". Also the extra cumulative loss evaluations
     from k = 3 to k = 10. Do not add any other threshold.
   - **beside-tables, not merged:** C-1 duplicate-rate quantiles per dimension; WP-T1f cold-start hit rates (loss
     < 1e-8, best of m = 10) per system, labelled "bound ∞".
   - a `manifest.json` with input paths, their SHA-256, row counts and the script's own version string.
3. **Tests** `analysis/tests/test_aggregate_phasec_restart_curve.py` on synthetic `starts.jsonl` input (no real
   data): nested best-of-k, cumulative cost, threshold grid boundaries, strata separation, incomplete-set refusal,
   control pass, control failure → non-zero exit, "not comparable" handling.
4. **`SCRIPTS.md`:** replace the `TODO(Claude)` C-5 Abl-3 block with the real sequence: upload of the input history
   to the NFS, `oc apply` with the manifest, collection from the NFS (mounted locally as
   `/s/BigDataOrion/data-science/joedicke/...`), and the aggregator call. Output directory for tracked results:
   `analysis/data/paper1_phaseC_v1/restart_curve/`.
5. **Report** `codex/reports/REPORT_WP_N44.md`: what was built, which input files and fields were used, test
   results, and anything in §9.8 that turned out to be ambiguous against the actual record format.

## Verboten

- Running Julia, running any refit, or launching anything on Orion. Codex cannot run Julia here anyway; do not try.
- Changing `studies/regression/wp_n4_multistart_refit.jl` or anything under `src/`.
- Choosing, adding or changing any threshold, k value, stratum or reading beyond §9.8.
- Reporting means or medians as effect sizes; quantiles and counts only.
- Committing. Editing `codex/CURRENT_TASK.md`.

## Abnahme

- `python -m pytest analysis/tests/test_aggregate_phasec_restart_curve.py -q` passes.
- The aggregator run on an empty or partial directory without `--allow-incomplete` exits non-zero with a clear
  message.
- The manifest parses as YAML, has 36 completions, no `activeDeadlineSeconds`, and differs from the C-5 oracle
  manifest only in names, labels, script, paths, `--starts 10` and the header comment.
- `STATUS.md` set to `done` with WP-N44 and the report path, or `blocked` with the reason.
