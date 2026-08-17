# WP-A2 Report

## Scope

Changed only Python analysis code. No Julia code, no campaign runs, no regression runs, no
probe runs, no experiment artifacts under `experiments/`, and no Git staging or commits.

## Implementation

The silent drop came from using `VARIANT_ORDER` as both display order and row selector.
I changed the affected plot/table scripts to derive the displayed variant set from the
observed data and use the fixed list only as a preferred ordering prefix:

- `analysis/scripts/plot/table_main_results.py`
- `analysis/scripts/plot/plot_exact_match_rates.py`
- `analysis/scripts/plot/plot_stage_overshoot.py`

For these scripts I chose "unknown observed variants appear in the output" rather than
"abort", because tables and diagnostic plots are useful for campaign comparison even when
the campaign variant set differs from the frozen Phase-A list. Missing cells are still
shown explicitly by reindexing each observed variant against the selected systems.

`analysis/utils/style.py` now contains the shared ordering helper and non-throwing
`variant_label` / `variant_color` helpers. Labels and colors were added for the variants
listed in `VARIANTS` in `studies/regression/run_regression.jl`:

- `evogrow_v2_2_stage_local`
- `evogrow_v2_2_stage_capped`
- `evogrow_v3`
- `evogrow_v3_stage_capped`

`evogrow_v2_2_stage_capped` now has label `EvoGrow v2.2 (stage capped)` and color
`#6F4E7C`.

## Campaign-data acceptance run

Input aggregate:

- Path: `analysis/data/wp_a1_campaign_bridge_probe/aggregate_by_variant_system.csv`
- Aggregate rows: 15
- Observed variants: `evogrow_v2_2_stage_capped`, `evogrow_v2_2_stage_local`,
  `evogrow_v3`, `evogrow_v3_stage_capped`
- Systems: 5
- Nonempty `mean_loss` cells in aggregate: 15

Old table-selection behavior, reconstructed with the old fixed `VARIANT_ORDER` selector:

- Output rows: 30
- Output variants: `evogrow_v1`, `evogrow_v2_1`, `evogrow_v2_2_stage_local`,
  `evogrow_v2_2_passive`, `evogrow_v2_2_soft`, `gp_baseline`
- Nonempty `mean_loss` cells: 5

New table-selection behavior:

- Command: `python scripts/plot/table_main_results.py --config configs/wp_a2_campaign_bridge_probe.json`
- Output: `analysis/tables/wp_a2_campaign_bridge_probe/main_results.csv`
- Output rows: 20
- Output variants: `evogrow_v2_2_stage_local`, `evogrow_v2_2_stage_capped`,
  `evogrow_v3`, `evogrow_v3_stage_capped`
- Nonempty `mean_loss` cells: 15
- Nonempty cells by variant:
  - `evogrow_v2_2_stage_local`: 5
  - `evogrow_v2_2_stage_capped`: 4
  - `evogrow_v3`: 4
  - `evogrow_v3_stage_capped`: 2

The campaign variants no longer disappear silently.

The two affected plot scripts also ran against the same campaign aggregate:

- `python scripts/plot/plot_exact_match_rates.py --config configs/wp_a2_campaign_bridge_probe.json`
- `python scripts/plot/plot_stage_overshoot.py --config configs/wp_a2_campaign_bridge_probe.json`

Both completed and wrote outputs under `analysis/figures/wp_a2_campaign_bridge_probe/`.

## Phase-A preservation

Phase-A aggregate regeneration:

- Command: `python scripts/aggregate/aggregate_run_registry.py --config configs/paper1_phaseA_v1.json`
- Input rows: 300
- Valid rows: 300
- Output rows: 60
- Cells with 0 valid runs: 0
- Aggregate SHA-256 before and after regeneration:
  `861D9A273361BB09546FF299C6A7A000FA177F7050B7470F29CA12300B552D56`

Phase-A table equivalence against the old fixed-order algorithm on the same aggregate:

- Old rows: 60
- New rows: 60
- Old nonempty `mean_loss`: 60
- New nonempty `mean_loss`: 60
- CSV value equality: `True`
- TeX byte equality against the old fixed-order algorithm: `True`
- TeX bytes compared: 4007

The Phase-A path is unchanged in values. The aggregate is byte-identical after regeneration.

## Regression test

Added `tests/test_analysis_variant_visibility.py`.

Old-code result after adding the test and before changing the implementation:

- Command: `pytest tests/test_analysis_variant_visibility.py -q --basetemp=.pytest_tmp_wp_a2_old`
- Result: failed
- Failure reason: `campaign_unknown_variant` was absent after `build_csv_table`.

New-code result:

- Command: `pytest tests/test_analysis_variant_visibility.py -q --basetemp=.pytest_tmp_wp_a2_new`
- Result: `1 passed in 1.72s`

Final verification:

- `pytest tests/test_analysis_variant_visibility.py -q --basetemp=.pytest_tmp_wp_a2_final`
  -> `1 passed in 0.79s`
- `python -m compileall -q analysis tests/test_analysis_variant_visibility.py`
  -> exit code 0

