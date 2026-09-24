# REPORT WP-N23

## Scope

Implemented diagnostics for failed or unusable baseline predictions without changing the existing R2 values, thresholds, aggregation formulas, or configurations.

Changed files:

- `baselines/harness.py`
- `baselines/summarize_odeformer_grid.py`
- `baselines/tests/test_harness.py`

No files under `analysis/data/` were changed. `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py` was inspected only.

## Record Fields

For both `reconstruction` and `generalization`, records now include:

- `<prefix>_prediction_outcome`
- `<prefix>_r2_dimension_status`
- `<prefix>_r2_zero_reason`
- `<prefix>_integration_error_type`
- `<prefix>_integration_error_message`

Fixed value sets in `baselines/harness.py:38`:

- prediction outcome: `finite`, `none`, `wrong_shape`, `nonfinite`
- per-dimension R2 status: `regular`, `zero_convention`
- per-dimension zero reason: empty string, `prediction_none`, `prediction_wrong_shape`, `prediction_nonfinite`, `nonfinite_score`, `reference_no_variance`

The existing R2 convention is unchanged: `r2_by_dimension` still returns `0.0` for `None`, wrong shape, non-finite prediction values, non-finite scores, and exactly zero reference variance. The new fields are written by `r2_diagnostic_fields` at `baselines/harness.py:243`.

Integration exceptions are recorded with type and message fields by `integration_error_fields` at `baselines/harness.py:264`. ODEFormer integration calls are caught per reconstruction/generalization in `run_odeformer_record_with_adapter` at `baselines/harness.py:558`, so a failed integration becomes prediction outcome `none` instead of disappearing into an undifferentiated R2 value. The SINDy harness path writes the same fields in `run_sindy_record` at `baselines/harness.py:662`; the imported C-4 `simulate_model` reports caught simulation exceptions as status strings, and the harness records those `None` predictions with outcome `none` plus diagnostic fields.

## Summary

`baselines/summarize_odeformer_grid.py` now counts prediction outcomes separately for reconstruction and generalization. `outcome_counts` at `baselines/summarize_odeformer_grid.py:40` maps missing or unknown fields to `not_captured`, so old records without the new fields are reported as not captured rather than as zero.

## Tests

Command run locally:

```text
python -m pytest baselines/tests -q
```

Result:

```text
17 passed, 1 skipped in 13.53s
```

Acceptance cases covered with exported trajectories:

- `None` prediction: R2 remains `0.0`, reason `prediction_none` (`baselines/tests/test_harness.py:108`)
- non-finite prediction: R2 remains `0.0`, reason `prediction_nonfinite` (`baselines/tests/test_harness.py:108`)
- wrong-shape prediction: R2 remains `0.0`, reason `prediction_wrong_shape` (`baselines/tests/test_harness.py:108`)
- reference dimension without variance: R2 remains `0.0`, reason `reference_no_variance` (`baselines/tests/test_harness.py:125`)
- regular finite prediction: R2 remains `1.0`, status `regular` (`baselines/tests/test_harness.py:140`)
- summary old-record fallback to `not_captured` (`baselines/tests/test_harness.py:317`)
- summary new outcome counts (`baselines/tests/test_harness.py:349`)

## C-4 SINDy Baseline Check

`analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py` does not use the same silent `0.0` convention. It returns `NaN` for invalid R2 cases:

- `r2_score` starts at `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py:247`
- wrong shape or non-finite prediction returns `NaN` at line 249
- reference dimension without variance returns `NaN` at line 256
- missing prediction is assigned `NaN` at line 387
- `r2_gt_0_9` is false unless the score is finite and above threshold at line 405

It also records integration failure as `diverged_or_nonfinite` at line 403 and counts that at line 461.

## Full ODEFormer Grid Commands For Claude

Use fresh output directories so existing complete records are not skipped:

```text
python -m baselines.run_odeformer_grid --config baselines/configs/odeformer_grid.json --environment-id reference --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_wp_n23
python -m baselines.run_odeformer_grid --config baselines/configs/odeformer_grid.json --environment-id candidate --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_wp_n23
python -m baselines.summarize_odeformer_grid --reference-records analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_wp_n23/records.jsonl --candidate-records analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_wp_n23/records.jsonl --output-dir analysis/data/paper1_phaseC_v1/odeformer_baseline/summary_wp_n23
```
