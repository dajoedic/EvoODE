# WP-N13 Report

## Implemented

- Added `analysis/utils/campaign.py` with shared campaign path derivation and a single-campaign `experiment_id` guard.
- Added `--campaign` and derived defaults to:
  - `analysis/scripts/aggregate/verify_campaign_registry.py`
  - `analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py`
  - `analysis/scripts/aggregate/aggregate_phaseb_raw_pruned_support_comparison.py`
  - `analysis/scripts/aggregate/aggregate_representability_threeway.py`
  - `analysis/scripts/aggregate/aggregate_phaseb_descriptive_tables.py`
  - `analysis/scripts/aggregate/aggregate_phaseb_heartbeat_waste_systems.py`
- Added explicit `--campaign` consistency checks to the config-driven campaign aggregators:
  - `analysis/scripts/aggregate/aggregate_run_registry.py`
  - `analysis/scripts/aggregate/analyze_pretuning_contrast.py`
  - `analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py`
- Registry inputs now require exactly one `experiment_id`, and it must match the requested campaign before aggregation.
- `system_classification.csv` and `representational_adequacy.csv` are systemwide inputs and are intentionally not given synthetic campaign columns.

## Omitted Aggregate Scripts

- `convert_campaign_history_to_run_registry.py`: converter that writes a requested `experiment_id`, not an evaluator of an existing campaign registry.
- `classify_odebench_systems.py`: systemwide symbolic classification generator; no campaign registry input.
- `aggregate_wp_n1_coefficient_metrics.py`: WP-N1 probe-output aggregator; uses Phase-B classification only as system truth.
- `run_wp_n6_sindy_baseline.py`: SINDy baseline over benchmark systems and adequacy matrix; no campaign registry input.
- `aggregate_wp_n2_pruning_sensitivity.py`, `compare_wp_n1_manifest_equivalence.py`, `phase1_diagnostic.py`, `evaluate_hypotheses.py`: no direct campaign registry aggregation path matching WP-N13's guard target.

## Tests

Command:

```text
$env:TMP='C:\Users\joedicke\Documents\reps\EvoODE\.pytest_tmp'; $env:TEMP=$env:TMP; New-Item -ItemType Directory -Force $env:TMP | Out-Null; python -m pytest analysis/tests/ -q
```

Output:

```text
...................                                                      [100%]
19 passed in 1.98s
```

New tests in `analysis/tests/test_campaign_identity.py` cover:

- mixed `experiment_id` values fail and the message names both values,
- wrong `experiment_id` fails and names actual and requested campaigns,
- matching registry verification succeeds,
- campaign-derived paths are used unless an explicit option overrides them.

## Byte Comparison

All regenerated Phase-B files below matched the checked-in files byte-for-byte:

```text
analysis/data/paper1_phaseB_v1/phaseb_structure_metrics_by_equation.csv
analysis/data/paper1_phaseB_v1/phaseb_structure_metrics_by_cell.csv
analysis/data/paper1_phaseB_v1/phaseb_support_match_registry_discrepancies.csv
analysis/data/paper1_phaseB_v1/phaseb_raw_pruned_support_comparison.csv
analysis/data/paper1_phaseB_v1/representability_threeway_by_equation.csv
analysis/data/paper1_phaseB_v1/representability_threeway_by_system.csv
analysis/data/paper1_phaseB_v1/representability_threeway_summary.csv
analysis/data/paper1_phaseB_v1/descriptive_t1_surrogate_r2.csv
analysis/data/paper1_phaseB_v1/descriptive_t2_exact_fit_quality.csv
analysis/data/paper1_phaseB_v1/descriptive_t3_exact_support.csv
analysis/data/paper1_phaseB_v1/descriptive_t4_stage_economy.csv
analysis/data/paper1_phaseB_v1/descriptive_t5_robustness.csv
analysis/data/paper1_phaseB_v1/heartbeat_waste_cells.csv
analysis/data/paper1_phaseB_v1/heartbeat_waste_summary.csv
analysis/data/paper1_phaseB_v1/heartbeat_waste_threshold_grid.csv
analysis/data/paper1_phaseB_v1/heartbeat_level_event_counts.csv
analysis/data/paper1_phaseB_v1/heartbeat_last_improvement_level1_by_dim.csv
analysis/data/paper1_phaseB_v1/phaseb_system_table.csv
analysis/data/paper1_phaseB_v1/phaseb_system_waste_top10_by_class.csv
analysis/data/paper1_phaseB_v1/phaseb_system_worst_target_top10_by_class.csv
analysis/data/paper1_phaseB_v1/aggregate_by_variant_system.csv
analysis/data/paper1_phaseB_v1/pretuning_contrast.json
analysis/data/paper1_phaseB_v1/pretuning_distribution_collapse.json
analysis/tables/paper1_phaseB_v1/descriptive_t1_surrogate_r2.csv
analysis/tables/paper1_phaseB_v1/descriptive_t1_surrogate_r2.tex
analysis/tables/paper1_phaseB_v1/descriptive_t2_exact_fit_quality.csv
analysis/tables/paper1_phaseB_v1/descriptive_t2_exact_fit_quality.tex
analysis/tables/paper1_phaseB_v1/descriptive_t3_exact_support.csv
analysis/tables/paper1_phaseB_v1/descriptive_t3_exact_support.tex
analysis/tables/paper1_phaseB_v1/descriptive_t4_stage_economy.csv
analysis/tables/paper1_phaseB_v1/descriptive_t4_stage_economy.tex
analysis/tables/paper1_phaseB_v1/descriptive_t5_robustness.csv
analysis/tables/paper1_phaseB_v1/descriptive_t5_robustness.tex
analysis/tables/paper1_phaseB_v1/heartbeat_waste_summary.csv
analysis/tables/paper1_phaseB_v1/heartbeat_waste_summary.tex
analysis/tables/paper1_phaseB_v1/heartbeat_waste_threshold_grid.csv
analysis/tables/paper1_phaseB_v1/heartbeat_waste_threshold_grid.tex
analysis/tables/paper1_phaseB_v1/phaseb_system_table.csv
analysis/tables/paper1_phaseB_v1/phaseb_system_table.tex
analysis/tables/paper1_phaseB_v1/phaseb_system_waste_top10_by_class.csv
analysis/tables/paper1_phaseB_v1/phaseb_system_waste_top10_by_class.tex
analysis/tables/paper1_phaseB_v1/phaseb_system_worst_target_top10_by_class.csv
analysis/tables/paper1_phaseB_v1/phaseb_system_worst_target_top10_by_class.tex
```

No regenerated comparable file failed comparison. No comparable regenerated file was skipped.

Temporary bytecheck outputs were written under `outputs/wp_n13_bytecheck/` and `analysis/tables/wp_n13_bytecheck/`. The sandbox policy rejected recursive cleanup, so they remain as ignored/generated artifacts.

## Registry Verification

Command:

```text
python analysis/scripts/aggregate/verify_campaign_registry.py --campaign paper1_phaseB_v1 --input experiments/paper1_phaseB_v1/run_registry.csv
```

Output:

```text
Verified campaign registry: 756 rows
  Unique identities: 756
  Condition column: condition
  Rows per condition: {'pretune_off': 378, 'pretune_on': 378}
  Representability: exact=240, surrogate=516
  git_hash: 91f88c4
  config_fingerprint: 604e79733b22d64d
  stage_cap_behavior_fingerprint: ffb0266c7913352c
  Numeric surrogate r2 rows: 516
```

## Phase-C Note

The existing registry verifier defaults are Phase-B constants: 756 rows, 756 unique identities, 378 rows per condition, 240 exact rows, and 516 surrogate rows. A Phase-C run must pass Phase-C values explicitly, including 378 rows instead of 756 where applicable.
