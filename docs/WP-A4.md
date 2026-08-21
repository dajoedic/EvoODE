# WP-A4 Report

## Decisions

- `convert_campaign_history_to_run_registry.py` preserves the existing column names and order and appends the campaign fields `r2`, `r2_by_dim`, `total_parameter_fits`, `total_ode_solves`, and `stage_cap_behavior_fingerprint`.
- The converter does not interpret campaign fields. Missing `r2` and explicit JSON `null` both become empty CSV cells; measured `r2 = 0.0` remains a numeric zero.
- `aggregate_run_registry.py` keeps the Phase-A default grouping by `variant_slug, system_id`. Config key `group_by_initial_condition_set: true` adds `initial_condition_set` as a grouping key.
- R2 aggregation writes `mean_r2` and `n_r2` when the registry contains `r2`. `n_r2` is the number of valid runs with numeric R2, so an empty mean is interpretable.
- Effort counters are aggregated as means (`mean_total_parameter_fits`, `mean_total_ode_solves`) to match the existing per-cell mean fields such as elapsed time and invalid evaluations.
- `table_main_results.py` uses `system_classification_path` when configured. One row in the classification file is one equation; a system is exact only if all of its equation rows are `exact`. One surrogate equation makes the whole system surrogate.
- Phase A has no classification path in its config. The explicit fallback is to infer exact systems from non-empty `exact_match_rate` and surrogate systems from systems whose aggregate rows have no support-match rate. If a classification path is configured but does not cover observed systems, the table script aborts.

## Acceptance Results

1. Real campaign pilot data:
   - Input `outputs/wp_a1_realdata/campaign_history.jsonl`: 33 records.
   - Converted output `outputs/wp_a4_realdata/run_registry.csv`: 33 rows.
   - Aggregated output `analysis/data/wp_a4_realdata/aggregate_by_variant_system.csv`: 27 rows, 27 observed systems, 33 valid runs, 0 zero-valid cells.
   - Classification split in `analysis/tables/wp_a4_realdata/main_results.*`: 9 exact systems, 18 surrogate systems.
   - The pilot file has no `r2`; aggregate R2 is `mean_r2 = NaN`, `n_r2 = 0` for all 27 rows.

2. R2 fixture:
   - Fixture input `outputs/wp_a4_r2_fixture/campaign_history.jsonl`: 6 records.
   - Converted output `outputs/wp_a4_r2_fixture/run_registry.csv`: 6 rows.
   - Standard aggregate `analysis/data/wp_a4_r2_fixture/aggregate_by_variant_system.csv`: 5 rows.
   - `r2_zero`: `mean_r2 = 0.0`, `n_r2 = 1`.
   - `r2_null`: empty `mean_r2`, `n_r2 = 0`.
   - `r2_missing`: empty `mean_r2`, `n_r2 = 0`.
   - `ic_split_probe`: `mean_r2 = 0.5`, `n_r2 = 2`.
   - Surrogate CSV `analysis/tables/wp_a4_r2_fixture/surrogate_systems_summary.csv` has no `exact_match_rate` column and carries `mean_r2,n_r2`.

3. IC grouping:
   - Real pilot data contains only `initial_condition_set = 1`, so standard and IC-split aggregates both have 27 rows.
   - The R2 fixture demonstrates the grouping behavior: standard aggregation has 5 rows; `group_by_initial_condition_set: true` has 6 rows.
   - In the fixture, `ic_split_probe/system 1` is one standard row with `mean_r2 = 0.5`, and two IC rows with `mean_r2 = 0.25` for IC 1 and `mean_r2 = 0.75` for IC 2.

4. Loud failure cases:
   - Empty classification/system selection:
     `Error: System classification does not cover any observed system. Observed systems: [1, 2, 4, 5]; classified systems: [999].`
   - Observed system without classification entry:
     `Error: Observed systems without classification entry: [2, 4, 5]. Observed systems: [1, 2, 4, 5].`
   - IC split without required column:
     `Error: Config requests group_by_initial_condition_set, but input data has no initial_condition_set column.`

5. Phase A byte identity:
   - Generated check aggregate: `analysis/data/wp_a4_phasea_bytecheck/aggregate_by_variant_system.csv`, 60 rows.
   - Generated check tables: `analysis/tables/wp_a4_phasea_bytecheck/main_results.csv` and `.tex`.
   - Byte comparisons against `analysis/data/paper1_phaseA_v1/aggregate_by_variant_system.csv`, `analysis/tables/paper1_phaseA_v1/main_results.csv`, and `analysis/tables/paper1_phaseA_v1/main_results.tex`: no differences encountered.

## Not Carried Further

- `r2_by_dim` is passed through by the bridge but is not aggregated or displayed in the main table.
- `stage_cap_behavior_fingerprint` is passed through for provenance but not aggregated.
- The package does not interpret missing R2 causes, stage-cap behavior, or surrogate quality; it only preserves, aggregates, and displays available fields.
