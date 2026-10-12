# WP-N44 Report

## Built

- Added `k8s/phase_c_c5_restart_curve_job.yaml`, modelled on the C-5 oracle job with 36 indexed completions, component `c5-restart-curve`, image placeholder `<COMMIT_SHA>`, `/outputs/phase_c_c5_restart_curve_<COMMIT_SHA>/input/history.jsonl`, `/outputs/phase_c_c5_restart_curve_<COMMIT_SHA>/out`, and `--campaign paper1_phaseC_v1 --starts 10`. It has no `activeDeadlineSeconds`.
- Added `analysis/scripts/aggregate/aggregate_phasec_restart_curve.py`.
  - Reads `starts.jsonl` shard outputs.
  - Checks the restart cell set against the exact C-1 set from `experiments/paper1_phaseC_v1/run_registry.csv` plus dimensions/exact labels from `studies/regression/phase_c_support.json`.
  - Stops on duplicate cells, missing cells, extra cells, or non-null `error` unless `--allow-incomplete` is passed.
  - Writes the C-5 control table before hard-stopping on comparable loss mismatches.
  - Writes the restart curve, first-hit table, k=3 reading, duplicate-rate beside table, WP-T1f cold-start beside table, and `manifest.json`.
- Added synthetic tests in `analysis/tests/test_aggregate_phasec_restart_curve.py`.
- Replaced the `TODO(Claude)` C-5 Abl-3 block in `SCRIPTS.md` with the NFS upload, `oc apply`, local NFS collection, and aggregator call.

## Input Fields Used

- Restart shard rows: `cell_key`, `system_id`, `initial_condition_set`, `seed`, `original_loss`, `error`, `reference_starts`, `oracle_starts`.
- Per-start rows: `start_index`, `loss`, `r2`, `fit_meta.loss_evals`.
- C-5 control rows: `reference_loss`, `reference_fit_meta.accepted_attempt`.
- C-1 expected cells: `variant_slug`, `condition`, `use_pretuning`, `system_id`, `system_representability`, `seed`, `initial_condition_set`.
- Phase-C support: `systems[].system_id`, `systems[].dim`, `systems[].representability`.
- Duplicate beside table source: `outputs/phase_c_campaign_221a3a7/history.jsonl`, field `structure_repeat_quantiles`.
- WP-T1f beside table source: `truth_cold_by_cell.csv`, fields `dimension`, `system_id`, `initial_condition_set`, `n_starts`, `n_loss_lt_1e_8`.

## Checks

- `python -m pytest analysis/tests/test_aggregate_phasec_restart_curve.py -q --basetemp tmp/pytest_wp_n44`: 3 passed.
- `python analysis/scripts/aggregate/aggregate_phasec_restart_curve.py --input-dir tmp/pytest_wp_n44/empty_restart --output-dir tmp/pytest_wp_n44/empty_out`: exited 1 with `restart input cell set is incomplete: expected=180 actual=0 missing=180 extra=0`.
- YAML parse check: `completions == 36` and no `activeDeadlineSeconds`.
- Static compile: `python -m py_compile analysis/scripts/aggregate/aggregate_phasec_restart_curve.py analysis/tests/test_aggregate_phasec_restart_curve.py`.
- Expected exact C-1 cell count from the real registry/support: 180.

Note: the exact acceptance command without `--basetemp` could not reach test execution in this sandbox because pytest tried to create `C:\Users\joedicke\AppData\Local\Temp\pytest-of-joedicke` and hit `PermissionError`. The same tests pass with a workspace-local base temp.

## Ambiguities

- Plan 9.8 says the oracle structure is "fitted only where it differs from the truth", while the assigned runner and real code fit `oracle_starts` for every cell. The aggregator follows the actual record format and reports oracle rows for every restart row.
- The duplicate-rate beside table is not merged into the curve. It summarizes each `structure_repeat_quantiles` key by dimension with across-cell q10/q50/q90, using `outputs/phase_c_campaign_221a3a7/history.jsonl` because it is present locally and contains the required per-cell field.
