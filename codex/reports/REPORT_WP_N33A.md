# WP-N33a Report

## Summary

Implemented the Stage-C control comparison fix, the per-cell staged-entry gate report, and the WP-N33a clean-evaluation path for Phase-C records. The session is `blocked` only because Julia cannot be executed in this Codex environment; Python acceptance items ran successfully.

## Changes

- `analysis/scripts/aggregate/compare_phasec_controls.py`
  - Skips `*.heartbeat.jsonl` for directory inputs.
  - Uses `(variant, system_id, initial_condition_set, seed)` as the campaign comparison key.
  - Ignores candidate records for variants absent from the reference key set.
  - Reports missing fields as `field <name> missing on candidate/reference` before normalization.

- `analysis/tests/test_compare_phasec_controls.py`
  - Added real-record-derived tests from `outputs/wp_n32_stage0/tasks/`, including a copied heartbeat file.
  - Added missing-field and variant-key coverage.

- `analysis/scripts/aggregate/robustness_stage_report.py`
  - Writes `robustness_stage_report.csv` and `robustness_stage_report.md`.
  - Emits one row per stage record, with the matching C-1 cell by variant/system/IC/seed.
  - Includes executed levels, loss evals, parameter fits, factors against C-1, final stage, per-equation stage-cap changes, exact-system support hits, clean R2 columns, prediction hashes, and `elapsed_s_capacity_context_no_evidence`.
  - Leaves clean R2 columns blank and marks `clean_eval_status=missing_clean_eval` when WP-N33a clean-eval output is absent.
  - Adds per-cell hard checks: no `error`/`failure_reason`, fingerprint `0c9672de35c75a9d` at `clamp_val=10`, non-null new fields, and observed-data hash check when an export index is supplied.

- `analysis/tests/test_robustness_stage_report.py`
  - Added real-record-derived coverage for Stage-0 report generation without clean eval.
  - Added clean-eval and export-index join coverage.

- `studies/regression/wp_n5_ic_generalization.jl`
  - Reuses the existing Phase-C model reconstruction and integration path.
  - Adds `--clean-eval` for clean full-grid reconstruction and clean other-IC generalization.
  - Stores both arithmetic and variance-weighted R2, divergence flags, errors, prediction trajectory hashes, and exported prediction trajectories under the output directory.
  - Applies the stored-record reconstruction R2 control only when `noise_sigma == 0` and `subsample_rho == 0`.
  - Adds optional `--reference-generalization` for bitwise comparison against existing C-1 WP-N5 generalization results.
  - Accepts input directories such as `outputs/wp_n32_stage0/tasks/` and filters heartbeat JSONL files.

## Field Origins Checked

For the Stage-0 fixture, the gate-report fields come from:

| Field | Origin |
|---|---|
| `noise_sigma`, `subsample_rho`, `noise_realization`, `clamp_val` | new WP-N32 record fields |
| `data_condition_fingerprint`, `observed_data_sha256`, `n_observed_points` | new WP-N32 data-condition fields |
| `executed_levels`, `total_loss_evals`, `total_parameter_fits`, `final_stage`, `stage_caps`, `elapsed_s` | existing campaign record fields |
| `exact_support_match_raw`, `exact_support_match_pruned`, `representability` | existing Phase-C support/truth fields |
| clean reconstruction/generalization R2 and prediction hashes | WP-N33a clean-eval output |

## Python Verification

Ran:

```bash
python -m py_compile analysis/scripts/aggregate/compare_phasec_controls.py analysis/scripts/aggregate/robustness_stage_report.py analysis/tests/test_compare_phasec_controls.py analysis/tests/test_robustness_stage_report.py
```

Result: exit 0.

Ran:

```bash
python -m pytest analysis/tests/test_compare_phasec_controls.py analysis/tests/test_robustness_stage_report.py -q --basetemp .pytest_tmp_wp_n33a
```

Result: `7 passed in 1.08s`.

Ran the required control comparison:

```bash
python analysis/scripts/aggregate/compare_phasec_controls.py --candidate outputs/wp_n32_stage0/tasks --reference-c1 outputs/phase_c_campaign_221a3a7
```

Result: exit 0, `Compared 2 matching records with no differences`.

Ran the required gate report without clean-eval output:

```bash
python analysis/scripts/aggregate/robustness_stage_report.py --stage-records outputs/wp_n32_stage0/tasks --reference-c1 outputs/phase_c_campaign_221a3a7 --output-dir outputs/wp_n33a_stage_report
```

Result: exit 0, `rows=2`. Outputs:

- `outputs/wp_n33a_stage_report/robustness_stage_report.csv`
- `outputs/wp_n33a_stage_report/robustness_stage_report.md`

The two Stage-0 rows have `loss_eval_factor_vs_c1=1`, `parameter_fit_factor_vs_c1=1`, `stage_caps_change_vs_c1=eq1:gleich`, `clean_eval_status=missing_clean_eval`, and hard checks `passed, passed, passed, not_checked`.

## Julia Status

Julia was not run in this Codex session because this environment cannot execute Julia. Static review covered the full new code path for directory input, heartbeat filtering, JSON3/Dict access through `_json_get`/`_json_require`, `nothing` prediction branches, prediction export paths, and reference-generalization lookup.

## Commands for Claude

1. Clean evaluation on Stage 0 with both controls. Purpose: compute clean full-grid reconstruction/generalization, export prediction trajectories, check reconstruction R2 against the stored Stage-0 record R2, and compare generalization bitwise to the existing C-1 WP-N5 output. Expected duration: under 2 minutes after compilation for the two Stage-0 cells.

```bash
julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl \
  --campaign paper1_phaseC_v1 \
  --input outputs/wp_n32_stage0/tasks \
  --output-dir outputs/wp_n33a_clean_eval_stage0 \
  --clean-eval --fresh \
  --reference-generalization outputs/wp_n5_ic_generalization_phase_c/shard_001_of_001/results.jsonl
```

2. Gate report with filled R2 columns. Purpose: join the Stage-0 records, WP-N33a clean-eval output, and C-1 reference into the per-cell gate table. Expected duration: under 10 seconds.

```bash
python analysis/scripts/aggregate/robustness_stage_report.py \
  --stage-records outputs/wp_n32_stage0/tasks \
  --clean-eval outputs/wp_n33a_clean_eval_stage0/results.jsonl \
  --reference-c1 outputs/phase_c_campaign_221a3a7 \
  --output-dir outputs/wp_n33a_stage_report_filled
```

