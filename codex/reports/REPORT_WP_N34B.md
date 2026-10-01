# WP-N34b Report - C-4 control, structural F1, stage-report glob

## Implementation

Updated `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`.

Changes:

- `--stage-report` can be passed multiple times and may be a CSV file, directory, or glob. Directory
  inputs are searched for `robustness_stage_report.csv`.
- `details.csv` now includes pruned-support structural metrics from `analysis/utils/metrics.py`:
  `sindy_structure_precision_pruned`, `sindy_structure_recall_pruned`, and
  `sindy_structure_f1_pruned`.
- Structural metrics are populated only for `phasec_representability == exact`; other systems are
  marked with `sindy_structure_metrics_exact_system == False` and blank metric values.
- `--control-export-index` now runs a C-4 reproduction control in
  `outputs/wp_n34_noise_sindy_baselines/control_c4_reproduction/`.
- The control first compares the provided export hashes against
  `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export/trajectory_hashes.csv`.
  The control SINDy evaluation then uses the exported control trajectories, not a fresh integration.

## Outputs

Normal run outputs:

- `outputs/wp_n34_noise_sindy_baselines/details.csv`
- `outputs/wp_n34_noise_sindy_baselines/summary.csv`
- `outputs/wp_n34_noise_sindy_baselines/export_checks.csv`
- `outputs/wp_n34_noise_sindy_baselines/comparison_with_robustness_stage_report.csv`

Control outputs:

- `outputs/wp_n34_noise_sindy_baselines/control_c4_reproduction/details.csv`
- `outputs/wp_n34_noise_sindy_baselines/control_c4_reproduction/summary.csv`
- `outputs/wp_n34_noise_sindy_baselines/control_c4_reproduction/export_checks.csv`
- `outputs/wp_n34_noise_sindy_baselines/control_c4_reproduction/control_trajectory_hash_check.csv`
- `outputs/wp_n34_noise_sindy_baselines/control_c4_reproduction/control_c4_comparison.csv`

## Run

Command:

```text
python analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py --export-index outputs/stage1/data_export/index.csv --stage-report outputs/stage1/*/report/robustness_stage_report.csv --control-export-index outputs/wp_n34_control_export/index.csv --output-dir outputs/wp_n34_noise_sindy_baselines
```

Result: exit code `1`, because the C-4 control found a named comparison issue.

The script printed:

```text
control: failed: C-4 comparison incomplete/different; statuses={'differs_or_incomplete': 80}; coefficient_statuses={'reference_missing_coefficients': 80}
```

Warnings during PySINDy fitting:

- `AxesWarning: 2 axes labeled for array with 1 axes`
- `UserWarning: Sparsity parameter is too big (0.1) and eliminated all coefficients`

## C-4 Control

Trajectory hash check:

- rows checked: 4
- matched C-4 hashes: 4
- differing C-4 hashes: 0
- systems/ICs: `(1, 1)`, `(1, 2)`, `(24, 1)`, `(24, 2)`

Comparison against
`analysis/data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export/details.csv`:

- rows compared: 80
- `fit_status` matched: 80
- `integration_status` matched: 80
- `active_terms_raw` matched: 80
- `active_terms_pruned` matched: 80
- R2 matched within `1e-12`: 77
- R2 differed: 3
- coefficient comparison status `reference_missing_coefficients`: 80

The three R2 differences are all rows with `integration_status == diverged` in both control and
C-4:

| library_id | system_id | source_ic | regime | r2_control | r2_c4 | abs_delta |
|---|---:|---:|---|---:|---:|---:|
| poly_deg3_sin_cos_stlsq_0.01 | 24 | 2 | generalization | -8.378938e+17 | -1.504886e+22 | 1.504802e+22 |
| poly_deg3_sin_cos_stlsq_0.01 | 24 | 2 | reconstruction | -4.510310e+35 | -2.356239e+48 | 2.356239e+48 |
| poly_deg5_stlsq_0.01 | 24 | 1 | generalization | -4.714915e+19 | -4.714915e+19 | 1.310720e+05 |

The coefficient comparison cannot pass because the C-4 reference `details.csv` has no coefficient
column. The new control output writes `sindy_coefficients_active`, but there is no persisted C-4
coefficient payload to compare against.

## Structural Metrics

`outputs/wp_n34_noise_sindy_baselines/details.csv`:

- rows: 80
- rows with `sindy_structure_f1_pruned` populated: 80
- rows with `sindy_structure_precision_pruned` populated: 80
- rows with `sindy_structure_recall_pruned` populated: 80
- rows marked `sindy_structure_metrics_exact_system == True`: 80

## Stage Reports

The run used the glob:

```text
outputs/stage1/*/report/robustness_stage_report.csv
```

`comparison_with_robustness_stage_report.csv`:

- rows: 80
- `matched`: 40
- `missing_in_stage_report`: 40
- matched conditions: `(noise_sigma=0.01, subsample_rho=0.0)` and
  `(noise_sigma=0.05, subsample_rho=0.5)`

## Tests

Command:

```text
python -m pytest analysis/tests/test_phasec_noise_sindy_baselines.py -q
```

Result:

```text
4 passed, 10 warnings in 3.76s
```
