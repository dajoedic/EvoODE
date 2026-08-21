# WP-A4b Report

## Fixture location

The WP-A4 handwritten input fixtures now live under `analysis/fixtures/`:

- `analysis/fixtures/wp_a4_r2_fixture/campaign_history.jsonl`
- `analysis/fixtures/wp_a4_error_fixtures/no_overlap_classification.csv`
- `analysis/fixtures/wp_a4_error_fixtures/partial_classification.csv`

I chose `analysis/fixtures/` because these files are small, manual input fixtures for analysis reproducibility checks. `analysis/data/` remains reserved for derived cached data, and generated registries, aggregates, and tables remain under `outputs/`, `analysis/data/`, and `analysis/tables/`.

## Acceptance results

1. Config path check:
   - Checked moved handwritten fixture references with `rg -n "outputs/wp_a4_error_fixtures|wp_a4_r2_fixture/campaign_history" analysis/configs`.
   - Result: no config references the moved handwritten fixture paths under ignored `outputs/`.
   - Checked remaining generated-registry references with `rg -n "../outputs" analysis/configs`.
   - Remaining `../outputs/wp_a4_r2_fixture/run_registry.csv` references are generated registry inputs and were left in place by task instruction.
   - Byte equality against the former ignored fixture files: 3 equal, 0 different.
   - SHA-256 hashes of the moved fixtures:
     - `analysis/fixtures/wp_a4_r2_fixture/campaign_history.jsonl`: `8BA2615C686B66F9BAE40BCCBB59D20BAD83529EFCFE414BE83A332073B7C982`
     - `analysis/fixtures/wp_a4_error_fixtures/no_overlap_classification.csv`: `25EC4C22FBECF941686BC56981D2C12923381B2A03063BB9F3205DEB0D690803`
     - `analysis/fixtures/wp_a4_error_fixtures/partial_classification.csv`: `1CCB61C9BD93774DEAB48D509BDB77898852E9785F4368C13B8ED0B43484FE6B`

2. R2 fixture rerun:
   - Converted `analysis/fixtures/wp_a4_r2_fixture/campaign_history.jsonl` to `outputs/wp_a4_r2_fixture/run_registry.csv`: 6 records.
   - Aggregated `analysis/configs/wp_a4_r2_fixture.json`: 5 rows.
   - `r2_zero`: `mean_r2 = 0.0`, `n_r2 = 1`.
   - `r2_null`: empty `mean_r2`, `n_r2 = 0`.
   - `r2_missing`: empty `mean_r2`, `n_r2 = 0`.
   - Error case `wp_a4_error_no_overlap`: `Error: System classification does not cover any observed system. Observed systems: [1, 2, 4, 5]; classified systems: [999].`
   - Error case `wp_a4_error_partial_classification`: `Error: Observed systems without classification entry: [2, 4, 5]. Observed systems: [1, 2, 4, 5].`

3. Phase A byte identity:
   - Rebuilt `analysis/data/wp_a4_phasea_bytecheck/aggregate_by_variant_system.csv`, `analysis/tables/wp_a4_phasea_bytecheck/main_results.csv`, and `analysis/tables/wp_a4_phasea_bytecheck/main_results.tex`.
   - Byte comparisons against `analysis/data/paper1_phaseA_v1/aggregate_by_variant_system.csv`, `analysis/tables/paper1_phaseA_v1/main_results.csv`, and `analysis/tables/paper1_phaseA_v1/main_results.tex`: 3 equal, 0 different.
