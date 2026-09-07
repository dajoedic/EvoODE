# WP-A5 Report

## Commands run

```powershell
python analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py --input experiments/paper1_phaseB_v1/history.jsonl --experiment-id paper1_phaseB_v1 --output experiments/paper1_phaseB_v1/run_registry.csv
```

Output:

```text
Converted 756 campaign records
  Input:  experiments\paper1_phaseB_v1\history.jsonl
  Output: experiments\paper1_phaseB_v1\run_registry.csv
```

```powershell
python analysis/scripts/aggregate/verify_campaign_registry.py --input experiments/paper1_phaseB_v1/run_registry.csv
```

Output:

```text
Verified campaign registry: 756 rows
  Unique identities: 756
  Condition column: variant_slug
  Rows per condition: {'evogrow_v2_2_stage_capped_pretune_off': 378, 'evogrow_v2_2_stage_capped_pretune_on': 378}
  Representability: exact=240, surrogate=516
  git_hash: 91f88c4
  config_fingerprint: 604e79733b22d64d
  stage_cap_behavior_fingerprint: ffb0266c7913352c
  Numeric surrogate r2 rows: 516
```

```powershell
python scripts/aggregate/aggregate_run_registry.py --config configs/paper1_phaseB_v1.json
```

Run from `analysis/`.

Output:

```text
Aggregated paper1_phaseB_v1
  Input:  experiments/paper1_phaseB_v1/run_registry.csv  (756 rows, 756 valid)
  Output: analysis/data/paper1_phaseB_v1/aggregate_by_variant_system.csv  (252 rows)
  Grouped by: variant_slug, system_id, initial_condition_set
  Cells with 0 valid runs: 0
```

## Forced failure

```powershell
python analysis/scripts/aggregate/verify_campaign_registry.py --input analysis/fixtures/wp_a5_broken_registry.csv --expected-row-count 1 --expected-unique-identities 1 --expected-rows-per-condition 1 --expected-exact-rows 0 --expected-surrogate-rows 1; exit $LASTEXITCODE
```

Exit code: `1`

Output:

```text
Invariant failed: corrupted rows expected 0, got 1
```

## Aggregate row count

The aggregate has 252 rows. This matches 63 systems x 2 conditions x 2 initial-condition sets.

## Column coverage gap

The Phase-B campaign record has 77 fields. The converter writes 42 registry columns. Counting direct
columns plus explicit semantic mappings for `manifest_index`, `representability`, `expected_stage`,
`timestamp`, and `pruned_match`, these 53 record fields are not carried forward:

- `T`
- `batch_output_file`
- `condition`
- `derivative_active_fractions`
- `derivative_screening_active`
- `eq_final_stages`
- `eq_overshoot`
- `eq_wasted_levels`
- `error`
- `invalid_screening_evals`
- `manifest_path`
- `n_levels`
- `optimizer_retcodes`
- `polish_budget_exhausted`
- `polish_convergence_failures`
- `polish_maxiters`
- `polish_time_s`
- `polished_candidates`
- `rank_agreement_spearman`
- `rejected_beats_best_selected`
- `rejected_diagnostic_budget_exhausted`
- `rejected_diagnostic_candidates`
- `rejected_diagnostic_convergence_failures`
- `rejected_diagnostic_samples`
- `rejected_diagnostic_time_s`
- `screen_k`
- `screening_budgets_active`
- `screening_evals`
- `screening_time_s`
- `solver_retcodes`
- `stage_cap_policy_active`
- `stage_caps`
- `support_terms`
- `total_diverged_solves`
- `total_invalid_solves`
- `total_nonfinite_solves`
- `total_optimizer_budget_stop_fits`
- `total_optimizer_eval_budget_limit_hits`
- `total_optimizer_failure_hits`
- `total_optimizer_fallback_result_fits`
- `total_optimizer_invalid_result_fits`
- `total_optimizer_iteration_limit_hits`
- `total_optimizer_last_resort_fits`
- `total_optimizer_limit_hits`
- `total_optimizer_safety_limit_hits`
- `total_optimizer_unknown_retcode_hits`
- `total_parameter_optimization_time_s`
- `total_simulation_time_s`
- `total_solver_unstable_solves`
- `total_step_limit_solves`
- `tspan`
- `u0`
- `use_pretuning`
