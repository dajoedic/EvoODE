# WP-E1 Report - Phase B regression batch path

## Scope

Implemented Phase B as a separate campaign on the existing `studies/regression/` batch path.
`REGRESSION_SYSTEMS` and the regression `config_fingerprint()` payload were not changed.

Changed files:

- `studies/regression/run_regression.jl`
- `studies/regression/run_batch_cell.jl`
- `studies/regression/phase_b_config.jl`
- `studies/regression/generate_phase_b_manifest.jl`

Generated smoke artifacts:

- `outputs/studies/regression/phase_b/wp_e1_manifest.csv`
- `outputs/studies/regression/phase_b/wp_e1_dim1_indices.txt`
- `outputs/studies/regression/phase_b/wp_e1_tasks/cell_000007.jsonl`

## Implementation Notes

Phase B is defined in `phase_b_config.jl`. It loads all 63 systems from
`benchmarks/data/strogatz_extended.json`, sorted by dataset id. The diagnostic protocol loader
`REGRESSION_PROTOCOL_BY_ID` supplies initial-condition sets and the shared time grid; the dataset
row supplies id, name, dimension, and substituted RHS expressions.

The Phase B arms are exactly:

- `evogrow_v2_2_stage_capped_pretune_on`, condition `pretune_on`, `use_pretuning=true`
- `evogrow_v2_2_stage_capped_pretune_off`, condition `pretune_off`, `use_pretuning=false`

Both use the same `EvoGrow` stage-local settings and the same
`LookAheadStageCapPolicy(; LOOKAHEAD_CAP_POLICY...)`.

The batch entry point `run_batch_cell.jl` still selects one row by manifest index. If the manifest
row has `campaign=phase_b`, it uses the Phase B fingerprint, variants, systems, and separate output
directory. Otherwise it uses the existing regression path.

## Expected Stage

The dataset does not carry `expected_stage`. Phase B represents it explicitly as `nothing` for all
63 systems.

Consumers affected by absent `expected_stage`:

- `run_regression.jl`: `stage_overshoot`, `wasted_levels`, `eq_overshoot`,
  `eq_wasted_levels`, and `pruned_match` now become `nothing` when expected stage/support is absent.
- `run_regression.jl`: summary formatting now prints `nothing` safely.
- Downstream aggregation/plot scripts such as `analysis/scripts/aggregate/aggregate_run_registry.py`
  and `analysis/scripts/plot/plot_stage_overshoot.py` read overshoot/wasted-level metrics and must
  keep Phase B exact and surrogate structure-correctness handling separate in WP-E2.

## Representability Split

Measured by fitting the current `default_staged_polynomial_basis(dim)` design matrix to the dataset
RHS values on the shipped reference trajectory points:

- exact systems: 23
- surrogate systems: 40
- total systems: 63

This split is reported only. WP-E1 does not use it for metrics.

## Fingerprints

Measured regression fingerprint:

```text
7acd3ebf3f60b974
```

Measured Phase B fingerprint:

```text
e577d9d692f3125b
```

## Enumeration

Manifest command:

```powershell
julia --project=. --startup-file=no studies/regression/generate_phase_b_manifest.jl --output outputs/studies/regression/phase_b/wp_e1_manifest.csv --dimension 1 --index-output outputs/studies/regression/phase_b/wp_e1_dim1_indices.txt
```

Runtime: 18.7 s wall time.

Measured output:

```text
manifest=outputs/studies/regression/phase_b/wp_e1_manifest.csv
phase_b_fingerprint=e577d9d692f3125b
regression_fingerprint=7acd3ebf3f60b974
rows=756
unique_identities=756
systems=63
expected_stage_missing=63
representability_exact=23
representability_surrogate=40
dimension=1
dimension_rows=276
dimension_index_output=outputs/studies/regression/phase_b/wp_e1_dim1_indices.txt
```

Enumeration order is deterministic: variant order, ascending system id, initial-condition set, seed.
Cell identity is `(campaign, variant, system_id, initial_condition_set, seed)`.

## One Verified Cell

Cell command:

```powershell
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl 7 --manifest outputs/studies/regression/phase_b/wp_e1_manifest.csv --output-dir outputs/studies/regression/phase_b/wp_e1_tasks
```

Runtime: 99.8 s wall time; record `elapsed_s=70.949867`.

Batch summary:

```text
variant=evogrow_v2_2_stage_capped_pretune_on sys=2 ic=1 seed=42 loss=1.864e-12 stage=1/nothing pruned=nothing elapsed=70.9s
output=outputs/studies/regression/phase_b/wp_e1_tasks/cell_000007.jsonl
```

Produced record:

```json
{"total_optimizer_eval_budget_limit_hits":0,"T":512,"polish_time_s":null,"eq_overshoot":null,"final_stage":1,"rejected_diagnostic_time_s":null,"total_optimizer_iteration_limit_hits":0,"total_optimizer_invalid_result_fits":0,"total_parameter_fits":30,"invalid_screening_evals":null,"expected_stage":null,"variant":"evogrow_v2_2_stage_capped_pretune_on","batch_output_file":"outputs/studies/regression/phase_b/wp_e1_tasks/cell_000007.jsonl","tspan":[0.0,10.0],"total_optimizer_limit_hits":30,"total_optimizer_budget_stop_fits":0,"solver_retcodes":["Success"],"stage_caps":[null],"polish_budget_exhausted":null,"derivative_active_fractions":[1.0],"total_optimizer_last_resort_fits":0,"total_optimizer_failure_hits":30,"rejected_diagnostic_budget_exhausted":null,"error":null,"eq_final_stages":[1],"use_pretuning":true,"total_optimizer_fallback_result_fits":0,"total_optimizer_unknown_retcode_hits":0,"u0":[4.78],"optimizer_retcodes":["Failure"],"manifest_index":7,"loss":1.8640674002408976e-12,"rank_agreement_spearman":null,"initial_condition_set":1,"total_diverged_solves":0,"total_solver_unstable_solves":0,"polish_convergence_failures":null,"pruned_match":null,"n_levels":30,"total_loss_evals":858540,"total_ode_solves":858540,"total_step_limit_solves":0,"rejected_diagnostic_samples":null,"config_fingerprint":"e577d9d692f3125b","system_id":2,"manifest_path":"outputs/studies/regression/phase_b/wp_e1_manifest.csv","eq_wasted_levels":null,"git_hash":"b43fcbf","representability":"exact","polish_maxiters":null,"total_simulation_time_s":44.26100015640259,"stage_cap_policy_active":true,"screen_k":null,"polished_candidates":null,"elapsed_s":70.949867,"rejected_diagnostic_candidates":null,"wasted_levels":null,"git_dirty":true,"derivative_screening_active":false,"condition":"pretune_on","total_invalid_solves":0,"support_terms":[["u1"]],"rejected_diagnostic_convergence_failures":null,"screening_time_s":null,"total_optimizer_safety_limit_hits":0,"screening_evals":null,"stage_overshoot":null,"system_name":"Population growth (naive)","seed":42,"total_parameter_optimization_time_s":23.00599956512451,"timestamp":"2026-08-10T19:23:31.251Z","rejected_beats_best_selected":null,"total_nonfinite_solves":0,"screening_budgets_active":false}
```

Required telemetry present:

- WP-D3 optimizer counters: `total_optimizer_iteration_limit_hits`,
  `total_optimizer_safety_limit_hits`, `total_optimizer_eval_budget_limit_hits`,
  `total_optimizer_failure_hits` are present. The record also carries the other optimizer retcode
  counters added around WP-D3.
- Existing fit/solve counters: `total_parameter_fits`, `total_loss_evals`,
  `total_ode_solves`, `total_invalid_solves`, `total_diverged_solves`,
  `total_nonfinite_solves`, `total_step_limit_solves`, `total_solver_unstable_solves`.
- Phase B identity fields: `condition`, `use_pretuning`, `initial_condition_set`,
  `config_fingerprint`, `manifest_index`, `manifest_path`, `batch_output_file`.

Schema compatibility: shared fields are produced by the same `run_one` function as the regression
records and keep the same meanings. Phase-B-only fields are `condition` and `representability`;
`use_pretuning` now records the actual variant setting instead of the global regression default.

## Verification

Load/fingerprint check:

```powershell
@'
include("studies/regression/run_regression.jl")
include("studies/regression/phase_b_config.jl")
println(config_fingerprint())
println(phase_b_fingerprint())
println(length(PHASE_B_SYSTEMS))
println(phase_b_representability_counts())
'@ | julia --project=. --startup-file=no -
```

Runtime: 33.8 s wall time.

Output:

```text
7acd3ebf3f60b974
e577d9d692f3125b
63
Dict("exact" => 23, "surrogate" => 40)
```

Pass criterion:

- Regression fingerprint remains `7acd3ebf3f60b974`.
- Phase B fingerprint is separate: `e577d9d692f3125b`.
- Manifest has exactly 756 rows and 756 unique identities.
- Exactly one successful 1D Phase B cell record was produced.
