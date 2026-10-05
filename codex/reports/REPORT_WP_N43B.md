# WP-N43b Report

## Outputs

- C-6 SINDy merge: `outputs/c6_sindy_baselines_5dd1df8/merged/`
- Hierarchy: `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n43b/`
- Main files: `per_run.csv`, `per_system.csv`, `benchmark.csv`, `sensitivity.csv`, `controls.csv`,
  `sindy_old_vs_new_deltas.csv`, `sindy_old_vs_new_changed_rows.csv`,
  `sindy_c4c_changed_rows.csv`, `sindy_clean_realization_deltas.csv`, `metadata.json`.

## Merge Checks

`outputs/c6_sindy_baselines_5dd1df8/merged/merge_checks.csv`:

| n_shards | n_rows | n_distinct_cells | duplicate_run_keys | hash_check_rows | hash_check_passed_rows | cells_with_all_configurations |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 90,720 | 4,536 | 0 | 4,536 | 4,536 | 4,536 |

The merged `summary.csv` was built with `build_summary` from
`analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`.

## Controls

- `controls.csv`: 571 / 571 controls passed.
- EvoGrow back-compatibility controls: 8 / 8 passed.
- ODEFormer back-compatibility controls: all controls emitted by the WP-N40 reference summary passed.
- SINDy old WP-N31 back-compatibility is reported as deltas, not a stop condition: 400 rows in
  `sindy_old_vs_new_deltas.csv`, 5 non-zero unit-rate deltas.
- New C-6 SINDy vs WP-C4c: 2,520 / 2,520 rows matched on R2 > 0.9 verdict, raw support and pruned
  support; `sindy_c4c_changed_rows.csv` has 0 rows.
- Equal-system-weight controls passed for arithmetic and variance-weighted reconstruction and
  generalization where available.
- Dim-1 equality controls passed for reconstruction and generalization for EvoGrow, SINDy and
  ODEFormer.
- EvoGrow generalization variance-weighted input: 337 / 378 rows available; 41 / 378 rows are
  non-finite/diverged. One of those 41 has `generalization_diverged_or_nonfinite == false` but
  `generalization_r2 == NaN`, so it is treated as non-finite for availability.
- C-6 clean SINDy realization identity: verdicts, status flags and supports are identical across
  realizations 1, 2 and 3. Raw continuous R2 can differ in extreme failed integrations; ranges are
  recorded in `sindy_clean_realization_deltas.csv`.

## SINDy Old vs New

Changed row list: `sindy_old_vs_new_changed_rows.csv`.

Counts:

| changed field | rows |
|---|---:|
| R2 > 0.9 verdict | 4 |
| raw support hit | 2 |
| pruned support hit | 2 |
| any listed change | 6 |

Non-zero old-vs-new unit-rate deltas:

| library_id | direction | dimension | class | regime | n_units | old | new | new-old |
|---|---|---:|---|---|---:|---:|---:|---:|
| poly_deg2_stlsq_0.01 | IC1_to_IC2 | 1 | partially_representable | generalization | 11 | 0.545455 | 0.636364 | 0.090909 |
| poly_deg3_sin_cos_stlsq_0.1 | IC1_to_IC2 | 3 | partially_representable | reconstruction | 2 | 0.500000 | 0.000000 | -0.500000 |
| poly_deg4_stlsq_0.01 | IC1_to_IC2 | 3 | partially_representable | reconstruction | 2 | 0.000000 | 0.500000 | 0.500000 |
| poly_deg4_stlsq_0.01 | IC2_to_IC1 | 2 | partially_representable | reconstruction | 17 | 0.764706 | 0.705882 | -0.058824 |
| poly_deg5_stlsq_0.01 | IC2_to_IC1 | 3 | partially_representable | reconstruction | 2 | 0.500000 | 0.000000 | -0.500000 |

## Overall Benchmark

| method | configuration | arm | n_systems | rec_arith | rec_varw | gen_arith | gen_varw | raw_support | pruned_support | pruned_f1 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EvoGrow | C-1_capped | canonical | 63 | 0.822751 | 0.886243 | 0.373016 | 0.414021 | 0.133333 | 0.294444 | 0.582273 |
| ODEFormer | beam10_noopt | candidate | 63 | 0.579365 | 0.587302 | 0.261905 | 0.277778 | 0.166667 | 0.166667 | 0.531668 |
| ODEFormer | beam10_noopt | reference | 63 | 0.576720 | 0.608466 | 0.261905 | 0.269841 | 0.183333 | 0.183333 | 0.550792 |
| ODEFormer | beam10_opt | candidate | 63 | 0.708995 | 0.740741 | 0.325397 | 0.341270 | 0.166667 | 0.166667 | 0.531326 |
| ODEFormer | beam10_opt | reference | 63 | 0.727513 | 0.753968 | 0.309524 | 0.317460 | 0.183333 | 0.183333 | 0.550749 |
| ODEFormer | beam50_noopt | candidate | 63 | 0.640212 | 0.687831 | 0.261905 | 0.261905 | 0.200000 | 0.200000 | 0.535154 |
| ODEFormer | beam50_noopt | reference | 63 | 0.648148 | 0.703704 | 0.277778 | 0.285714 | 0.166667 | 0.166667 | 0.544088 |
| ODEFormer | beam50_opt | candidate | 63 | 0.746032 | 0.796296 | 0.320106 | 0.328042 | 0.200000 | 0.200000 | 0.532202 |
| ODEFormer | beam50_opt | reference | 63 | 0.775132 | 0.798942 | 0.322751 | 0.335979 | 0.166667 | 0.183333 | 0.547499 |
| SINDy | poly_deg2_stlsq_0.01 | canonical | 63 | 0.603175 | 0.626984 | 0.317460 | 0.341270 | 0.283333 | 0.283333 | 0.663181 |
| SINDy | poly_deg2_stlsq_0.1 | canonical | 63 | 0.523810 | 0.539683 | 0.261905 | 0.269841 | 0.400000 | 0.400000 | 0.724021 |
| SINDy | poly_deg3_sin_cos_stlsq_0.01 | canonical | 63 | 0.650794 | 0.650794 | 0.412698 | 0.412698 | 0.166667 | 0.166667 | 0.541482 |
| SINDy | poly_deg3_sin_cos_stlsq_0.1 | canonical | 63 | 0.603175 | 0.603175 | 0.412698 | 0.428571 | 0.316667 | 0.316667 | 0.648889 |
| SINDy | poly_deg3_stlsq_0.01 | canonical | 63 | 0.634921 | 0.658730 | 0.357143 | 0.365079 | 0.283333 | 0.283333 | 0.647932 |
| SINDy | poly_deg3_stlsq_0.1 | canonical | 63 | 0.595238 | 0.619048 | 0.357143 | 0.373016 | 0.433333 | 0.433333 | 0.721765 |
| SINDy | poly_deg4_stlsq_0.01 | canonical | 63 | 0.579365 | 0.603175 | 0.341270 | 0.349206 | 0.233333 | 0.233333 | 0.596433 |
| SINDy | poly_deg4_stlsq_0.1 | canonical | 63 | 0.571429 | 0.603175 | 0.333333 | 0.357143 | 0.366667 | 0.366667 | 0.676673 |
| SINDy | poly_deg5_stlsq_0.01 | canonical | 63 | 0.563492 | 0.579365 | 0.341270 | 0.341270 | 0.283333 | 0.283333 | 0.564530 |
| SINDy | poly_deg5_stlsq_0.1 | canonical | 63 | 0.555556 | 0.579365 | 0.317460 | 0.325397 | 0.350000 | 0.350000 | 0.657155 |

## Verification

- `python -m py_compile analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py analysis/tests/test_aggregate_phasec_hierarchy_n43.py`
- `python -m pytest analysis/tests/test_aggregate_phasec_hierarchy_n43.py -q --basetemp tmp/pytest_n43b` -> 6 passed.
- `python analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py` -> completed and wrote `hierarchy_n43b`.
