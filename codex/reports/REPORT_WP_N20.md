# WP-N20 Report - Variance-Weighted R2 Analysis

## Delivered files

- `analysis/scripts/aggregate/aggregate_variance_weighted_r2.py`
- `analysis/tests/test_variance_weighted_r2.py`
- `analysis/data/paper1_phaseB_v1/variance_weighted_r2/variance_weighted_r2_cells.csv`
- `analysis/data/paper1_phaseB_v1/variance_weighted_r2/variance_weighted_r2_rates.csv`
- `analysis/data/paper1_phaseB_v1/variance_weighted_r2/variance_weighted_r2_flip_rates.csv`
- `analysis/data/paper1_phaseB_v1/variance_weighted_r2/variance_weighted_r2_difference_quantiles.csv`
- `analysis/data/paper1_phaseB_v1/variance_weighted_r2/variance_weighted_r2_controls.csv`
- `analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke_variance_weighted_r2/*.csv`

## Commands run

```text
python -m pytest analysis/tests/test_variance_weighted_r2.py --basetemp .codex_tmp/pytest
python analysis/scripts/aggregate/aggregate_variance_weighted_r2.py --campaign paper1_phaseB_v1
python analysis/scripts/aggregate/aggregate_variance_weighted_r2.py --campaign paper1_phaseC_v1 --input analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke/records.jsonl --output-dir analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke_variance_weighted_r2
```

Test result: 4 passed in 0.91 s. The first pytest attempt without `--basetemp` failed before setup because pytest tried to use `C:\Users\joedicke\AppData\Local\Temp\pytest-of-joedicke`, which is not accessible in this sandbox.

## Field origin

Existing record fields from `experiments/paper1_phaseB_v1/run_registry.csv`:

- `system_id`
- `initial_condition_set`
- `condition` as the reported arm
- `r2`
- `r2_by_dim`

Existing trajectory-export fields from `outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/trajectory_manifest.csv`:

- `dimension`
- `dtype`
- `byte_order`
- `state_axis_order`
- `state_shape`
- `state_sha256`
- `state_path`

Analysis-layer fields added by the script:

- `r2_arithmetic_mean`
- `r2_variance_weighted`
- `r2_arithmetic_mean_gt_0_9`
- `r2_variance_weighted_gt_0_9`
- `r2_difference_variance_weighted_minus_arithmetic`
- `threshold_flip`
- `threshold_flip_direction`
- `arithmetic_control_abs_error`
- `one_dim_abs_delta`
- grouped rates, flip rates, and difference quantiles

For the versioned WP-N19 smoke input, the existing fields are already `reconstruction_r2_arithmetic_mean`, `reconstruction_r2_variance_weighted`, `generalization_r2_arithmetic_mean`, and `generalization_r2_variance_weighted`; the script explodes these into reconstruction/generalization analysis-layer rows. That input has no `r2_by_dim`, so the arithmetic-control row has `n_checked=0`.

## Control behavior

The script aborts on an arithmetic-control violation. Reason: if `mean(r2_by_dim)` does not reproduce `r2`, either the record mapping or record schema is wrong, and continuing would produce plausible but invalid rates. The script also aborts if a one-dimensional cell has different arithmetic and variance-weighted aggregations.

Phase-B run controls:

| control | n_checked | n_failed | max_abs_error | tolerance |
|---|---:|---:|---:|---:|
| arithmetic_mean_reproduces_r2 | 756 | 0 | 1.110223e-16 | 1.0e-12 |
| one_dimensional_aggregations_identical | 276 | 0 | 1.110223e-16 | 1.0e-12 |
| multi_dimensional_aggregations_differ | 480 | 35 | 6.712142e-01 | 1.0e-12 |

The third row is a descriptive control row, not an abort condition: 445 of 480 multidimensional cells differ, and 35 are exactly equal within tolerance.

## Phase-B results

Input cells: 756.

Dimension counts:

| dimension | n_cells |
|---:|---:|
| 1 | 276 |
| 2 | 336 |
| 3 | 120 |
| 4 | 24 |

Multidimensional cells with different arithmetic and variance-weighted R2: 445.

Threshold flips at `R2 > 0.9`: 53 of 756 cells. All 53 flips were `arithmetic <= 0.9` to `variance_weighted > 0.9`; 0 flipped in the opposite direction.

Largest grouped flip rates:

| dimension | arm | initial_condition_set | n_cells | flip_count | flip_rate |
|---:|---|---:|---:|---:|---:|
| 4 | pretune_off | 2 | 6 | 4 | 0.666667 |
| 4 | pretune_on | 2 | 6 | 3 | 0.500000 |
| 3 | pretune_on | 1 | 30 | 9 | 0.300000 |
| 3 | pretune_off | 1 | 30 | 9 | 0.300000 |
| 4 | pretune_on | 1 | 6 | 1 | 0.166667 |

Global quantiles of `variance_weighted - arithmetic`:

| q | value |
|---:|---:|
| 0.00 | -5.128534e-02 |
| 0.25 | 0.000000e+00 |
| 0.50 | 1.110223e-16 |
| 0.75 | 3.032433e-03 |
| 1.00 | 6.712142e-01 |

Every grouped rate output includes `n_cells` as denominator.

## Phase-B registry `r2_by_dim` format check

`experiments/paper1_phaseB_v1/run_registry.csv` has 756 rows and 756 nonmissing `r2_by_dim` values. A sample parses as a JSON list, e.g. `[0.9999880667006428]`. The fields used for this task are `system_id`, `system_dim`, `initial_condition_set`, `condition`, `r2`, and `r2_by_dim`.

Conclusion: the Phase-B registry carries `r2_by_dim` in the same JSON-array shape expected for reconstruction from records. The versioned Phase-C WP-N19 smoke file is a different external-baseline schema and does not carry `r2_by_dim`; it carries precomputed arithmetic and variance-weighted fields.

## Parameterization check

The campaign identifier is a CLI parameter. The default input is `experiments/<campaign>/run_registry.csv`, and `--input` allows a second recordbestand without code changes.

Second input run:

- input: `analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke/records.jsonl`
- output cells: 24, from 12 records times reconstruction/generalization scopes
- one-dimensional equality control: 16 checked, 0 failed, max_abs_error 1.110223e-16
- multidimensional rows: 8 checked, 4 differed within tolerance
- threshold flips: 0
