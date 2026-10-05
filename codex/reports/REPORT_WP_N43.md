# WP-N43 Report

## Summary

Implemented `analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py` and
`analysis/tests/test_aggregate_phasec_hierarchy_n43.py`.

Outputs were written to:

- `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43/per_run.csv`
- `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43/per_system.csv`
- `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43/benchmark.csv`
- `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43/sensitivity.csv`
- `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43/controls.csv`
- `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43/metadata.json`

Output row counts:

| table | rows | columns |
|---|---:|---:|
| per_run | 4662 | 41 |
| per_system | 1197 | 25 |
| benchmark | 190 | 22 |
| sensitivity | 76 | 9 |
| controls | 529 | 7 |

`metadata.json` lists all input paths and SHA-256 hashes.

## Commands

```powershell
python -m pytest analysis/tests/test_aggregate_phasec_hierarchy_n43.py
python analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py
```

Both commands completed successfully.

## Controls

All controls passed: 529/529.

| control | expected | actual | passed |
|:--|--:|--:|:--|
| evogrow_backcompat_overall_reconstruction | 0.823 | 0.822751 | True |
| evogrow_backcompat_overall_generalization | 0.373 | 0.373016 | True |
| evogrow_backcompat_dim1_reconstruction | 0.978 | 0.978261 | True |
| evogrow_backcompat_dim1_generalization | 0.703 | 0.702899 | True |
| evogrow_backcompat_dim2_reconstruction | 0.917 | 0.916667 | True |
| evogrow_backcompat_dim2_generalization | 0.256 | 0.255952 | True |
| evogrow_backcompat_dim3_reconstruction | 0.283 | 0.283333 | True |
| evogrow_backcompat_dim3_generalization | 0.017 | 0.016667 | True |

Additional controls in `controls.csv`:

- SINDy back-compatibility against `outputs/phase_c_campaign_221a3a7/agg/sindy_n31/phasec_sindy_paired_summary.csv`.
- ODEFormer reference back-compatibility against `outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_reference/phasec_odeformer_paired_summary.csv`.
- Variance-weighted equality on dim 1 where variance-weighted fields are available.
- Equal-system-weight checks: benchmark overall values equal unweighted means of the per-system table.

## Overall Benchmark

Rates are equal-weighted per system under the hierarchy
`run -> direction -> system -> benchmark`. Structure metrics use exact systems only.

| method | configuration | arm | n_systems | recon arithmetic | recon variance-weighted | gen arithmetic | gen variance-weighted | raw exact | pruned exact | pruned F1 |
|:--|:--|:--|--:|--:|--:|--:|--:|--:|--:|--:|
| EvoGrow | C-1_capped | canonical | 63 | 82.3% | 88.6% | 37.3% | NaN | 13.3% | 29.4% | 0.582 |
| ODEFormer | beam10_noopt | reference | 63 | 57.7% | 60.8% | 26.2% | 27.0% | 18.3% | 18.3% | 0.551 |
| ODEFormer | beam10_opt | reference | 63 | 72.8% | 75.4% | 31.0% | 31.7% | 18.3% | 18.3% | 0.551 |
| ODEFormer | beam50_noopt | reference | 63 | 64.8% | 70.4% | 27.8% | 28.6% | 16.7% | 16.7% | 0.544 |
| ODEFormer | beam50_opt | reference | 63 | 77.5% | 79.9% | 32.3% | 33.6% | 16.7% | 18.3% | 0.547 |
| SINDy | poly_deg2_stlsq_0.01 | canonical | 63 | 60.3% | NaN | 31.0% | NaN | 28.3% | 28.3% | NaN |
| SINDy | poly_deg2_stlsq_0.1 | canonical | 63 | 52.4% | NaN | 26.2% | NaN | 40.0% | 40.0% | NaN |
| SINDy | poly_deg3_sin_cos_stlsq_0.01 | canonical | 63 | 65.1% | NaN | 41.3% | NaN | 16.7% | 16.7% | NaN |
| SINDy | poly_deg3_sin_cos_stlsq_0.1 | canonical | 63 | 61.1% | NaN | 41.3% | NaN | 31.7% | 31.7% | NaN |
| SINDy | poly_deg3_stlsq_0.01 | canonical | 63 | 63.5% | NaN | 35.7% | NaN | 28.3% | 28.3% | NaN |
| SINDy | poly_deg3_stlsq_0.1 | canonical | 63 | 59.5% | NaN | 35.7% | NaN | 43.3% | 43.3% | NaN |
| SINDy | poly_deg4_stlsq_0.01 | canonical | 63 | 57.9% | NaN | 34.1% | NaN | 23.3% | 23.3% | NaN |
| SINDy | poly_deg4_stlsq_0.1 | canonical | 63 | 57.1% | NaN | 33.3% | NaN | 36.7% | 36.7% | NaN |
| SINDy | poly_deg5_stlsq_0.01 | canonical | 63 | 57.1% | NaN | 34.1% | NaN | 28.3% | 28.3% | NaN |
| SINDy | poly_deg5_stlsq_0.1 | canonical | 63 | 55.6% | NaN | 31.7% | NaN | 36.7% | 36.7% | NaN |

## Sensitivity

Threshold crossings between arithmetic and variance-weighted aggregation:

| method | arm | reconstruction crossings | generalization crossings | reconstruction available runs | generalization available runs |
|:--|:--|--:|--:|--:|--:|
| EvoGrow | canonical | 24 | 0 | 378 | 0 |
| ODEFormer | candidate | 64 | 21 | 1512 | 1512 |
| ODEFormer | reference | 58 | 14 | 1512 | 1512 |
| SINDy | canonical | 0 | 0 | 0 | 0 |

## Missing Fields

- SINDy `details.csv` has scalar `r2` only; it lacks per-dimension R2 or precomputed
  variance-weighted R2. The script therefore writes variance-weighted SINDy R2/rates as `NaN` and
  `*_available = False`.
- EvoGrow WP-N5 `cells.csv` has scalar generalization R2 only; it lacks `generalization_r2_by_dim`.
  The script therefore writes EvoGrow generalization variance-weighted R2/rates as `NaN` and
  `generalization_r2_variance_weighted_available = False`.
- SINDy details do not contain pruned structural F1 / precision / recall fields, only exact raw and
  pruned support hits. Those continuous structure fields are `NaN` for SINDy.

No missing variance-weighted value was approximated.

## C-6 Requirements

The hierarchy code already keeps `noise_level`, `subsampling_ratio`, and `realization` columns in
the per-run table. To run on C-6, the loader must provide these keys from the C-6 producer and add
them as benchmark stratification keys before the system-level average. The seed level then becomes
`seed x noise realization` within each `(system, direction, noise sigma, subsampling rho)` data
condition. C-6 also needs per-dimension generalization R2 for EvoGrow if the variance-weighted
generalization headline is required.
