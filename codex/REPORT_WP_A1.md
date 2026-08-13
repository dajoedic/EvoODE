# WP-A1 Report

## Scope Checked

The Python analysis pipeline is Phase-A shaped:

1. `analysis/scripts/aggregate/aggregate_run_registry.py` reads `run_registry.csv`.
2. It writes `analysis/data/<experiment>/aggregate_by_variant_system.csv`.
3. Downstream consumers read that aggregate CSV.

The campaign path is JSONL shaped:

1. Batch cells write `cell_<index>.jsonl`.
2. `studies/regression/merge_batch_records.jl` concatenates successful cell records into a history-style JSONL file.

## Pilot Data Access

The requested pilot location was not reachable in this session:

```text
Get-ChildItem -Path 'S:\BigDataOrion\data-science\joedicke'
Cannot find drive. A drive with the name 'S' does not exist.
```

Available filesystem drives were only `C:\` and `E:\`. Because of that, I could not copy from:

- `S:\BigDataOrion\data-science\joedicke\pilot_sweep_tasks\`
- `S:\BigDataOrion\data-science\joedicke\pilot_sweep3_tasks\`
- `S:\BigDataOrion\data-science\joedicke\pilot_e20af80\tasks_dim*\`

As a fallback format probe, I used existing local campaign-path JSONL output:

```text
outputs/studies/regression/wp_b3/scratch_history_merge.jsonl
copied to outputs/wp_a1/pilot_format_probe/campaign_history.jsonl
records=43
```

This is not claimed as the requested shared-drive pilot dataset. It is only a local campaign-format compatibility probe.

## Pipeline Expected Shape

`aggregate_run_registry.py` requires these input columns:

| Expected column | Used for | Campaign mapping |
| --- | --- | --- |
| `variant_slug` | group key; output variant id | `variant`; bridge writes both `variant` and `variant_slug` |
| `system_id` | group key | `system_id` direct |
| `system_name` | aggregate label | `system_name` direct |
| `seed` | `n_seeds` count | `seed` direct |
| `loss` | validity filter and `mean_loss`/`std_loss` | `loss` direct |
| `exact_support_match` | `exact_match_rate` | campaign has `pruned_match`, not raw `exact_support_match` |
| `final_stage` | `mean_final_stage` | `final_stage` direct |
| `stage_overshoot` | `mean_stage_overshoot` | `stage_overshoot` direct where expected stage exists |
| `wasted_levels` | `mean_wasted_levels` | `wasted_levels` direct where expected stage exists |
| `total_invalid_evals` | `mean_invalid_evals` | no exact campaign equivalent; bridge leaves blank |
| `elapsed_s` | `mean_elapsed_s` | `elapsed_s` direct |

Downstream aggregate consumers require:

| Consumer | Required aggregate columns |
| --- | --- |
| `table_main_results.py` | `variant_slug`, `system_id`, `system_name`, `mean_loss`, `std_loss`, `exact_match_rate`, `n_valid` |
| `plot_stage_overshoot.py` | `variant_slug`, `system_id`, `system_name`, `mean_stage_overshoot`, `n_valid` |
| `plot_exact_match_rates.py` | `variant_slug`, `system_id`, `system_name`, `exact_match_rate`, `n_valid` |
| `evaluate_hypotheses.py` | `variant_slug`, `system_id`, `system_name`, `n_valid`, `mean_loss`, `exact_match_rate`, `mean_stage_overshoot`, `mean_wasted_levels` |

## Campaign Record Shape

Fields observed across the local campaign-format probe:

```text
T, batch_output_file, config_fingerprint, derivative_active_fractions,
derivative_screening_active, elapsed_s, eq_final_stages, eq_overshoot,
eq_wasted_levels, error, expected_stage, final_stage, git_dirty, git_hash,
initial_condition_set, invalid_screening_evals, loss, manifest_index,
manifest_path, n_levels, optimizer_retcodes, polish_budget_exhausted,
polish_convergence_failures, polish_maxiters, polish_time_s, polished_candidates,
pruned_match, rank_agreement_spearman, rejected_beats_best_selected,
rejected_diagnostic_budget_exhausted, rejected_diagnostic_candidates,
rejected_diagnostic_convergence_failures, rejected_diagnostic_samples,
rejected_diagnostic_time_s, screen_k, screening_budgets_active, screening_evals,
screening_time_s, seed, solver_retcodes, stage_cap_policy_active, stage_caps,
stage_overshoot, support_terms, system_id, system_name, timestamp,
total_diverged_solves, total_invalid_solves, total_loss_evals,
total_nonfinite_solves, total_ode_solves, total_optimizer_eval_budget_limit_hits,
total_optimizer_failure_hits, total_optimizer_iteration_limit_hits,
total_optimizer_limit_hits, total_optimizer_safety_limit_hits,
total_optimizer_unknown_retcode_hits, total_parameter_fits,
total_parameter_optimization_time_s, total_simulation_time_s,
total_solver_unstable_solves, total_step_limit_solves, tspan, u0, use_pretuning,
variant, wasted_levels
```

Campaign-only fields are retained by the source JSONL but not consumed by the current Phase-A Python pipeline unless bridged into CSV columns.

## Same Name, Different or Risky Meaning

These are the dangerous fields:

| Name or metric | Risk |
| --- | --- |
| `exact_support_match` vs `pruned_match` | Phase A writes raw `exact_support_match`; campaign records expose `pruned_match`. Mapping it gives a useful recovery-rate bridge, but the semantics are not identical. For surrogate systems `pruned_match: null` is legitimate and must remain blank. |
| `total_invalid_evals` | Phase A means evaluations producing NaN or failed simulation. Campaign records split related concepts across `total_invalid_solves`, `total_optimizer_invalid_result_fits`, `invalid_screening_evals`, solver instability counts, and optimizer failure counts. The bridge leaves `total_invalid_evals` blank rather than inventing a unit. |
| `variant_slug` | Phase A downstream scripts assume a fixed Paper-1 variant set. Campaign variants such as `evogrow_v3` or `evogrow_v2_2_stage_capped` can aggregate correctly but disappear or produce blanks in hard-coded Phase-A tables. |
| `stage_overshoot` and `wasted_levels` | Same aggregate intent, but campaign records can legitimately carry blanks for surrogate or expected-stage-missing systems. Existing aggregation treats blanks as NaN and still counts the run valid if `loss` exists. |
| `git_hash` | Pilot records may use `unknown`. This is provenance loss, not an analysis defect, and is not required by current Python consumers. |

## Direct Pipeline Test Against JSONL

Command:

```text
python scripts/aggregate/aggregate_run_registry.py --config ../outputs/wp_a1/pilot_format_probe/aggregate_config.json
```

Result:

```text
Error: Error tokenizing data. C error: Expected 19 fields in line 22, saw 20
```

Conclusion: direct campaign JSONL input is a hard failure, not a silent pass.

## Bridge Implemented

New bridge:

```text
analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py
```

It converts campaign history JSONL to a Phase-A-style `run_registry.csv` in one place before the existing Python pipeline:

```text
python analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py \
  --input outputs/wp_a1/pilot_format_probe/campaign_history.jsonl \
  --output outputs/wp_a1/pilot_format_probe/run_registry.csv \
  --experiment-id wp_a1_campaign_bridge_probe
```

Result:

```text
Converted 43 campaign records
```

Bridge behavior:

- Direct mappings: `variant`, `system_id`, `system_name`, `seed`, `loss`, `final_stage`, `stage_overshoot`, `wasted_levels`, `total_loss_evals`, `elapsed_s`.
- Compatibility additions: `variant_slug = variant`, `status`/`success` from `error`, `finished_at = timestamp`, `system_dim` from `u0` or `support_terms`.
- Scientific gaps left blank: `objective`, `total_invalid_evals`, surrogate `exact_support_match`.
- Campaign provenance kept as extra columns: `campaign_manifest_index`, `initial_condition_set`, `config_fingerprint`, `git_hash`, `git_dirty`.

The Phase-A path remains unchanged. Existing `paper1_phaseA_v1` config still points at `experiments/paper1_phaseA_v1/run_registry.csv`.

## Pipeline Test After Bridge

Aggregation:

```text
python scripts/aggregate/aggregate_run_registry.py --config ../outputs/wp_a1/pilot_format_probe/bridge_config.json
Aggregated wp_a1_campaign_bridge_probe
  Input:  outputs/wp_a1/pilot_format_probe/run_registry.csv  (43 rows, 43 valid)
  Output: analysis/data/wp_a1_campaign_bridge_probe/aggregate_by_variant_system.csv  (15 rows)
  Cells with 0 valid runs: 0
```

Downstream table consumer:

```text
python scripts/plot/table_main_results.py --config ../outputs/wp_a1/pilot_format_probe/bridge_config.json
Saved: tables/wp_a1_campaign_bridge_probe/main_results.tex
Saved: tables/wp_a1_campaign_bridge_probe/main_results.csv
```

However, this is a partial silent-success risk:

```text
agg_variants=evogrow_v2_2_stage_capped,evogrow_v2_2_stage_local,evogrow_v3,evogrow_v3_stage_capped
table_variants=evogrow_v1,evogrow_v2_1,evogrow_v2_2_passive,evogrow_v2_2_soft,evogrow_v2_2_stage_local,gp_baseline
table_rows=30
table_nonempty_mean_loss=5
```

`table_main_results.py` reindexes to the frozen Phase-A variant list and therefore drops or blanks campaign variants it does not know about. That script can run cleanly while producing an incomplete campaign table.

Hypothesis evaluator:

```text
python scripts/aggregate/evaluate_hypotheses.py --config ../outputs/wp_a1/pilot_format_probe/bridge_config.json
Error: Missing expected variants: evogrow_v1, evogrow_v2_1, evogrow_v2_2_passive, evogrow_v2_2_soft, gp_baseline
```

This is a clean hard failure caused by Phase-A study assumptions, not by record shape after conversion.

## Parts Not Exercised

- The requested shared-drive pilot data was not exercised because `S:` is not mounted in this session.
- Surrogate pilot records with `git_hash: "unknown"` and `pruned_match: null` from the named shared-drive folders were not exercised directly.
- `plot_stage_overshoot.py` and `plot_exact_match_rates.py` were not run after the bridge because the table consumer already demonstrated the relevant hard-coded Phase-A variant-list risk, and generating new figures is out of scope.
- No surrogate scoring metric was invented.

## Bottom Line

The existing Python aggregation cannot read campaign JSONL directly. A one-step converter makes campaign records consumable by `aggregate_run_registry.py` without changing the Phase-A path. Downstream scripts then split into two categories: aggregation works, strict Phase-A hypothesis evaluation fails clearly, and fixed-variant tables can succeed silently with incomplete campaign values.
