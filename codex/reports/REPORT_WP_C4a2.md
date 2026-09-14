# WP-C4a2 Report

## Summary

Implemented the Phase-C SINDy R2 aggregation fix and replaced the WP-N6 raw byte check with the corrected reported-measure criterion.

Changed files:

- `analysis/scripts/aggregate/run_phasec_sindy_baseline.py`
- `analysis/tests/test_phasec_sindy_baseline.py`
- `analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/summary.csv`
- `analysis/tables/paper1_phaseC_v1/phasec_sindy_baseline/phasec_sindy_summary.csv`
- `analysis/tables/paper1_phaseC_v1/phasec_sindy_baseline/phasec_sindy_summary.tex`

`analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py` and the WP-N6 output files were not changed.

## Phase-C R2 Aggregation

The summary median now uses this filter:

- source rows must be `valid_for_analysis`
- `r2` must be finite
- `diverged_or_nonfinite` must be false

The ambiguous `r2_valid_count` summary column was replaced by `r2_finite_nondiverged_count`.
The existing `diverged_or_nonfinite_count` remains in the output and reports the excluded divergent/nonfinite rows.

Added R2 quantile columns over the same cleaned selection:

- `r2_q000_finite_nondiverged`
- `r2_q025_finite_nondiverged`
- `r2_q075_finite_nondiverged`
- `r2_q100_finite_nondiverged`

Regenerated summary outputs from the existing checked-in Phase-C details, without rerunning SINDy.

Measured output:

- summary rows: 382
- detail rows: 2,520
- divergent/nonfinite detail rows: 473
- divergent/nonfinite rows still marked `valid_for_analysis`: 324
- summed `diverged_or_nonfinite_count` in summary: 324
- summed `r2_finite_nondiverged_count` in summary: 2,030
- `r2_finite_nondiverged_count == n_cells - diverged_or_nonfinite_count`: true for all 382 rows
- empty cleaned R2 selections reported as `NaN`: 58 groups
- `r2_median_valid` range after fix: -439.59709375714624 to 0.9999768941412284
- `r2_q000_finite_nondiverged` minimum: -4253810807.8030896
- `r2_q100_finite_nondiverged` maximum: 0.9999996357105206
- no R2 value/rate column exceeds 1.0

The threshold metric was not changed. Recomputing `r2_gt_0_9_rate_over_cells` from `details.csv` gives 382/382 matching groups, with maximum absolute float roundoff difference `1.1102230246251565e-16` and all differences below `1e-12`. Divergent rows with `r2_gt_0_9 == True`: 0.

## WP-N6 Reported-Measure Check

`check-wpn6-bitidentical` now keeps the old command name but applies the corrected criterion:

- `summary.csv` and `trajectory_check.csv` are byte-identical.
- `wp_n6_summary.csv`, `wp_n6_trajectory_check.csv`, `wp_n6_summary.tex`, and `wp_n6_trajectory_check.tex` are byte-identical.
- `details.csv` is compared column-by-column, ignoring only `fit_elapsed_s_non_evidence` and allowing `r2` differences only when both reference and candidate rows have `integration_status == "diverged"`.
- `costs.csv` and `wp_n6_costs.csv` are compared column-by-column, ignoring only `elapsed_s_non_evidence_total`.
- Reported columns such as `r2_gt_0_9`, `structure_hit`, term counts, `fit_status`, and `integration_status` are compared and named in the failure message if they change.

Focused tests derived from real WP-N6 CSVs verify both paths:

- runtime-only differences plus diverged-row `r2` differences pass
- a reported `r2_gt_0_9` flip fails and names the changed column

Command result:

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py check-wpn6-bitidentical --config analysis/configs/wp_n6_sindy_baseline.json
WP-N6 bit-identical check passed
```

The command emitted PySINDy sparsity warnings during the temporary WP-N6 rerun; it exited with code 0.

## Tests

```text
pytest analysis/tests/test_phasec_sindy_baseline.py -q --basetemp .pytest_tmp/wp_c4a2_phasec
9 passed in 15.66s

pytest analysis/tests -q --basetemp .pytest_tmp/wp_c4a2_all
56 passed in 12.07s
```

The first attempt without `--basetemp` failed before running the tmp-path tests because pytest tried to use `C:\Users\joedicke\AppData\Local\Temp\pytest-of-joedicke`, which is inaccessible in this sandbox. The rerun with a workspace basetemp passed.
