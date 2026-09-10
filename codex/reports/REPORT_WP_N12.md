# WP-N12 Report

## Result

Implemented the Phase-B record fields for raw support, pruned support, raw exact match, pruned exact match, and the explicit support-match definition tag.

Julia acceptance was not executed in this Codex environment. Per `codex/CODEX_PROTOCOL.md`, Julia is blocked locally with an environment issue, so the task is reported as `blocked` for Claude-side acceptance.

## Pruning Rule

The extracted pruning rule is in `studies/regression/diagnostic_systems.jl:183`:

- `pruned_support_idxs_for_equation(term_idxs, params)` owns the frozen threshold `max(1e-6, 1e-3 * max_abs)` and returns the surviving term indices for one equation.
- `pruned_support_idxs(structure, params)` applies that rule across equations with the existing parameter ordering.

Callers using the extracted Julia rule:

- `support_match_pruned` in `studies/regression/diagnostic_systems.jl:202`.
- `pruned_active_term_names` in `studies/regression/run_regression.jl:614`, which writes `pruned_support_terms`.
- `_pruned_terms_from_model` in `studies/regression/wp_n3_oracle_refit.jl`.
- `_pruned_terms_from_model` in `studies/regression/wp_n4_multistart_refit.jl`.
- `_pruned_terms` in `studies/regression/wp_n5_ic_generalization.jl`.

The remaining grep hits for the literal pruning threshold are outside the editable Phase-B regression path for this task: `experiments/run_experiment.jl` is explicitly forbidden, and `analysis/scripts/aggregate/phase1_diagnostic.py` is a separate Python parser.

## Record Fields

`studies/regression/run_regression.jl` now writes:

- `pruned_support_terms`: term names by equation after the extracted pruning rule.
- `exact_support_match_raw`: `support_match(result.structure, expected_idxs)`, or `nothing` without true support.
- `exact_support_match_pruned`: the same value as `pruned_match`, or `nothing` without true support.
- `exact_support_match_definition`: fixed value `pruned_support_terms_exact_match`.

`pruned_match` is unchanged in name, meaning, and calculation path: it is still computed with `support_match_pruned(result.structure, result.params, expected_idxs)`.

## Definition Guard

The selected definition field is `exact_support_match_definition`.

The selected value is `pruned_support_terms_exact_match`.

This was checked against `analysis/utils/support_match_definition.py:13`, where `PRUNED_SUPPORT_MATCH = "pruned_support_terms_exact_match"`, and against `analysis/utils/support_match_definition.py:36` plus `analysis/utils/support_match_definition.py:45`, where explicit registry values from `exact_support_match_definition` are accepted and mapped to the pruned definition.

`analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py` now preserves the new fields in generated Phase-B registry CSVs and defaults the definition column to `pruned_support_terms_exact_match` for older Phase-B records.

## Changed Files

- `studies/regression/diagnostic_systems.jl`: extracted the Phase-B pruning threshold into one named equation-level helper and rebuilt `support_match_pruned` on it.
- `studies/regression/run_regression.jl`: added `pruned_support_terms`, `exact_support_match_raw`, `exact_support_match_pruned`, and `exact_support_match_definition` to the Phase-B record.
- `analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py`: carries the new support fields and definition tag into Phase-B registry CSV output.
- `studies/regression/wp_n3_oracle_refit.jl`: replaced its inline pruning threshold with the shared helper.
- `studies/regression/wp_n4_multistart_refit.jl`: replaced its inline pruning threshold with the shared helper.
- `studies/regression/wp_n5_ic_generalization.jl`: replaced its inline pruning threshold with the shared structure-level helper.

`codex/CURRENT_TASK.md` was already modified in the working tree before this task and was not edited by Codex.

## Verification

Commands run:

```powershell
python -m py_compile analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py analysis/utils/support_match_definition.py
python -m pytest analysis/tests/test_phaseb_support_acceptance.py
git diff --check
```

Results:

- `py_compile`: passed.
- `analysis/tests/test_phaseb_support_acceptance.py`: 5 passed.
- `git diff --check`: passed.

Julia commands for Claude-side acceptance:

```powershell
$env:FRESH="1"; $env:EVO_REGRESSION_VARIANT="evogrow_v2_2_stage_local"; $env:EVO_REGRESSION_SYSTEM_ID="3"; $env:EVO_REGRESSION_IC_SET="1"; $env:EVO_REGRESSION_SEED="42"; $env:EVO_REGRESSION_HISTORY_PATH="outputs/studies/regression/wp_n12_smoke/history.jsonl"; julia --project=. studies/regression/run_regression.jl
```

```powershell
$env:FRESH="1"; Remove-Item Env:EVO_REGRESSION_VARIANT -ErrorAction SilentlyContinue; Remove-Item Env:EVO_REGRESSION_SYSTEM_ID -ErrorAction SilentlyContinue; Remove-Item Env:EVO_REGRESSION_IC_SET -ErrorAction SilentlyContinue; Remove-Item Env:EVO_REGRESSION_SEED -ErrorAction SilentlyContinue; $env:EVO_REGRESSION_HISTORY_PATH="outputs/studies/regression/wp_n12_full/history.jsonl"; julia --project=. studies/regression/run_regression.jl
```

Open Julia acceptance points:

1. All four new fields are present and plausible in a real regression cell.
2. `exact_support_match_pruned == pruned_match` in the same record.
3. `pruned_support_terms` is a per-equation subset of `support_terms`.
4. Existing numerical and accounting fields remain bit-identical to `HEAD`.
5. `phase_b_fingerprint()`, `config_fingerprint()`, and `stage_cap_behavior_fingerprint()` are unchanged.
6. Full Julia tests pass.
