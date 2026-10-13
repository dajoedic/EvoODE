# WP-N46b Report

## Changes

- Added `--clean-only` to `analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py`.
- In clean-only mode, the C-6 SINDy-family shard merge requires exactly 378 distinct clean cells, rejects any nonzero `noise_sigma` or `subsample_rho`, and requires the methods `sindy`, `weak_sindy`, and `e_sindy` in the main shard tree.
- Recorded `clean_only` in `metadata.json`; `esindy_status` remains `absent` because no separate E-SINDy input was used. E-SINDy rows are loaded from the main N46 shard tree.
- Updated the `hierarchy_n46` command in `SCRIPTS.md` with `--clean-only`.
- Fixed the hierarchy N45 old-vs-new delta join to use the full common stratum key, including `arm`, `dimension`, `threeway_class`, and `feasible_bound_10` when present.

## Validation

Commands run:

```text
python -m py_compile analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py analysis/tests/test_aggregate_phasec_hierarchy_n43.py
python -m pytest analysis/tests/test_aggregate_phasec_hierarchy_n43.py -q --basetemp tmp/pytest_n46b
python analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py --sindy-shards-dir outputs\c6_n46_clean_dop853 --sindy-merged-dir outputs\c6_n46_clean_dop853\merged --sindy-c4c-details analysis\data\paper1_phaseC_v1\phasec_sindy_baseline_wp_c4c_export_n46\details.csv --output-dir outputs\phase_c_campaign_221a3a7\agg\hierarchy_n46 --clean-only
```

Results:

- Tests: 11 passed.
- Clean merge: 10 shards, 11,340 rows, 378 distinct cells, 378/378 export hash checks passed, 0 duplicate run keys.
- Controls: 652/652 passed.
- C-6 clean SINDy vs C-4c DOP853 control: 2,520 rows checked, 0 changed rows.
- Clean SINDy realization deltas: 1,260 groups, max range 0.0 for reconstruction/generalization arithmetic and variance-weighted R2.
- `hierarchy_n45_old_vs_new_deltas.csv`: 2,340 rows, 390 rows for each of 6 metrics.
- Outputs written under `outputs/phase_c_campaign_221a3a7/agg/hierarchy_n46/`.

Per-run rows:

| method | rows |
|---|---:|
| E-SINDy | 3,780 |
| EvoGrow | 378 |
| ODEFormer | 3,024 |
| SINDy | 1,260 |
| Weak-SINDy | 3,780 |

## Overall old -> new

Rates are `old->new`. Reconstruction and generalization show arithmetic / variance-weighted R2 > 0.9 rates.

| method | configuration | arm | reconstruction arith/vw | generalization arith/vw | raw | pruned |
|---|---|---|---|---|---|---|
| E-SINDy | poly_deg2_stlsq_0.01 | canonical | 0.584656->0.666667 / 0.611111->0.693122 | 0.322751->0.378307 / 0.346561->0.407407 | 0.283333->0.283333 | 0.283333->0.283333 |
| E-SINDy | poly_deg2_stlsq_0.1 | canonical | 0.526455->0.608466 / 0.547619->0.629630 | 0.267196->0.349206 / 0.280423->0.362434 | 0.405556->0.405556 | 0.405556->0.405556 |
| E-SINDy | poly_deg3_sin_cos_stlsq_0.01 | canonical | 0.560847->0.629630 / 0.560847->0.632275 | 0.394180->0.460317 / 0.394180->0.462963 | 0.166667->0.216667 | 0.166667->0.216667 |
| E-SINDy | poly_deg3_sin_cos_stlsq_0.1 | canonical | 0.550265->0.645503 / 0.550265->0.648148 | 0.388889->0.484127 / 0.404762->0.502646 | 0.344444->0.444444 | 0.344444->0.444444 |
| E-SINDy | poly_deg3_stlsq_0.01 | canonical | 0.592593->0.687831 / 0.611111->0.714286 | 0.370370->0.478836 / 0.373016->0.481481 | 0.288889->0.288889 | 0.288889->0.288889 |
| E-SINDy | poly_deg3_stlsq_0.1 | canonical | 0.560847->0.682540 / 0.584656->0.703704 | 0.362434->0.460317 / 0.370370->0.468254 | 0.455556->0.455556 | 0.455556->0.455556 |
| E-SINDy | poly_deg4_stlsq_0.01 | canonical | 0.537037->0.616402 / 0.539683->0.621693 | 0.330688->0.402116 / 0.330688->0.410053 | 0.266667->0.266667 | 0.266667->0.266667 |
| E-SINDy | poly_deg4_stlsq_0.1 | canonical | 0.521164->0.624339 / 0.529101->0.637566 | 0.325397->0.404762 / 0.343915->0.420635 | 0.411111->0.411111 | 0.411111->0.411111 |
| E-SINDy | poly_deg5_stlsq_0.01 | canonical | 0.489418->0.544974 / 0.489418->0.552910 | 0.322751->0.375661 / 0.322751->0.386243 | 0.261111->0.261111 | 0.261111->0.261111 |
| E-SINDy | poly_deg5_stlsq_0.1 | canonical | 0.497354->0.589947 / 0.505291->0.603175 | 0.309524->0.396825 / 0.320106->0.410053 | 0.383333->0.383333 | 0.383333->0.383333 |
| EvoGrow | C-1_capped | canonical | 0.822751->0.822751 / 0.886243->0.886243 | 0.373016->0.373016 / 0.414021->0.414021 | 0.133333->0.133333 | 0.294444->0.294444 |
| ODEFormer | beam10_noopt | candidate | 0.579365->0.579365 / 0.587302->0.587302 | 0.261905->0.261905 / 0.277778->0.277778 | 0.166667->0.166667 | 0.166667->0.166667 |
| ODEFormer | beam10_noopt | reference | 0.576720->0.576720 / 0.608466->0.608466 | 0.261905->0.261905 / 0.269841->0.269841 | 0.183333->0.183333 | 0.183333->0.183333 |
| ODEFormer | beam10_opt | candidate | 0.708995->0.708995 / 0.740741->0.740741 | 0.325397->0.325397 / 0.341270->0.341270 | 0.166667->0.166667 | 0.166667->0.166667 |
| ODEFormer | beam10_opt | reference | 0.727513->0.727513 / 0.753968->0.753968 | 0.309524->0.309524 / 0.317460->0.317460 | 0.183333->0.183333 | 0.183333->0.183333 |
| ODEFormer | beam50_noopt | candidate | 0.640212->0.640212 / 0.687831->0.687831 | 0.261905->0.261905 / 0.261905->0.261905 | 0.200000->0.200000 | 0.200000->0.200000 |
| ODEFormer | beam50_noopt | reference | 0.648148->0.648148 / 0.703704->0.703704 | 0.277778->0.277778 / 0.285714->0.285714 | 0.166667->0.166667 | 0.166667->0.166667 |
| ODEFormer | beam50_opt | candidate | 0.746032->0.746032 / 0.796296->0.796296 | 0.320106->0.320106 / 0.328042->0.328042 | 0.200000->0.200000 | 0.200000->0.200000 |
| ODEFormer | beam50_opt | reference | 0.775132->0.775132 / 0.798942->0.798942 | 0.322751->0.322751 / 0.335979->0.335979 | 0.166667->0.166667 | 0.183333->0.183333 |
| SINDy | poly_deg2_stlsq_0.01 | canonical | 0.603175->0.690476 / 0.626984->0.714286 | 0.317460->0.380952 / 0.341270->0.412698 | 0.283333->0.283333 | 0.283333->0.283333 |
| SINDy | poly_deg2_stlsq_0.1 | canonical | 0.523810->0.611111 / 0.539683->0.626984 | 0.261905->0.341270 / 0.269841->0.349206 | 0.400000->0.400000 | 0.400000->0.400000 |
| SINDy | poly_deg3_sin_cos_stlsq_0.01 | canonical | 0.650794->0.746032 / 0.650794->0.746032 | 0.412698->0.492063 / 0.412698->0.492063 | 0.166667->0.216667 | 0.166667->0.216667 |
| SINDy | poly_deg3_sin_cos_stlsq_0.1 | canonical | 0.603175->0.706349 / 0.603175->0.714286 | 0.412698->0.500000 / 0.428571->0.507937 | 0.316667->0.416667 | 0.316667->0.416667 |
| SINDy | poly_deg3_stlsq_0.01 | canonical | 0.634921->0.746032 / 0.658730->0.769841 | 0.357143->0.452381 / 0.365079->0.476190 | 0.283333->0.283333 | 0.283333->0.283333 |
| SINDy | poly_deg3_stlsq_0.1 | canonical | 0.595238->0.714286 / 0.619048->0.738095 | 0.357143->0.452381 / 0.373016->0.468254 | 0.433333->0.433333 | 0.433333->0.433333 |
| SINDy | poly_deg4_stlsq_0.01 | canonical | 0.579365->0.682540 / 0.603175->0.706349 | 0.341270->0.420635 / 0.349206->0.436508 | 0.233333->0.233333 | 0.233333->0.233333 |
| SINDy | poly_deg4_stlsq_0.1 | canonical | 0.571429->0.666667 / 0.603175->0.706349 | 0.333333->0.404762 / 0.357143->0.436508 | 0.366667->0.366667 | 0.366667->0.366667 |
| SINDy | poly_deg5_stlsq_0.01 | canonical | 0.563492->0.682540 / 0.579365->0.698413 | 0.341270->0.396825 / 0.341270->0.396825 | 0.283333->0.283333 | 0.283333->0.283333 |
| SINDy | poly_deg5_stlsq_0.1 | canonical | 0.555556->0.682540 / 0.579365->0.706349 | 0.317460->0.396825 / 0.325397->0.412698 | 0.350000->0.350000 | 0.350000->0.350000 |
| Weak-SINDy | poly_deg2_stlsq_0.01 | canonical | 0.621693->0.738095 / 0.640212->0.759259 | 0.378307->0.486772 / 0.394180->0.505291 | 0.633333->0.633333 | 0.633333->0.633333 |
| Weak-SINDy | poly_deg2_stlsq_0.1 | canonical | 0.518519->0.637566 / 0.542328->0.661376 | 0.296296->0.402116 / 0.304233->0.407407 | 0.561111->0.561111 | 0.561111->0.561111 |
| Weak-SINDy | poly_deg3_sin_cos_stlsq_0.01 | canonical | 0.724868->0.878307 / 0.724868->0.878307 | 0.502646->0.634921 / 0.502646->0.637566 | 0.616667->0.716667 | 0.616667->0.716667 |
| Weak-SINDy | poly_deg3_sin_cos_stlsq_0.1 | canonical | 0.589947->0.735450 / 0.595238->0.743386 | 0.402116->0.544974 / 0.404762->0.544974 | 0.555556->0.655556 | 0.555556->0.655556 |
| Weak-SINDy | poly_deg3_stlsq_0.01 | canonical | 0.693122->0.865079 / 0.716931->0.894180 | 0.462963->0.613757 / 0.468254->0.619048 | 0.650000->0.650000 | 0.650000->0.650000 |
| Weak-SINDy | poly_deg3_stlsq_0.1 | canonical | 0.568783->0.716931 / 0.603175->0.748677 | 0.357143->0.484127 / 0.359788->0.492063 | 0.561111->0.561111 | 0.561111->0.561111 |
| Weak-SINDy | poly_deg4_stlsq_0.01 | canonical | 0.661376->0.825397 / 0.671958->0.835979 | 0.428571->0.574074 / 0.431217->0.576720 | 0.577778->0.577778 | 0.577778->0.577778 |
| Weak-SINDy | poly_deg4_stlsq_0.1 | canonical | 0.566138->0.685185 / 0.574074->0.693122 | 0.343915->0.462963 / 0.343915->0.473545 | 0.466667->0.466667 | 0.466667->0.466667 |
| Weak-SINDy | poly_deg5_stlsq_0.01 | canonical | 0.621693->0.746032 / 0.629630->0.764550 | 0.410053->0.513228 / 0.412698->0.518519 | 0.466667->0.466667 | 0.466667->0.466667 |
| Weak-SINDy | poly_deg5_stlsq_0.1 | canonical | 0.529101->0.608466 / 0.542328->0.619048 | 0.349206->0.417989 / 0.351852->0.425926 | 0.388889->0.388889 | 0.388889->0.388889 |
