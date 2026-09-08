# WP-N3b Report - wp_n3_oracle_refit runtime fix

## Status

Implemented by static inspection. Julia was not started in this Codex session because the task states
that this environment cannot start Julia (`A specified logon session does not exist`), so no refit
results or numerical conclusions are reported here.

## Changed Locations

`studies/regression/wp_n3_oracle_refit.jl`

| area | change | reason |
|---|---|---|
| `_json_has`, `_json_get`, `_json_require` | Added shared JSON access helpers for JSON3 records and Dict rows. | Avoid ad hoc `getproperty` calls outside the helper and produce explicit errors for required missing fields. |
| `_read_history` | Replaced the direct error-field `getproperty` with `_json_get`. | Keeps record access through the guarded path. |
| `_terms_from_expected` | Added equation-count check, null-equation check, and explicit basis-term lookup check. | Prevents indexing malformed/null truth data and replaces basis lookup `KeyError` with a record-specific error. |
| `_terms_from_model` | Added required `model_terms` check, equation-count check, null-equation check, and guarded `term_index` access. | Prevents missing-field, wrong-dimension, and null-index failures before the refit loop. |
| `_pruned_terms_from_model` | Added the same `model_terms` checks and guarded `coefficient`/`term_index` access. | Preserves the existing pruning threshold while preventing missing-field and null-index failures. |
| `_intersect_terms` | Changed `sort(intersect(Set(...), Set(...)))` to `sort(collect(intersect(Set(...), Set(...))))`. | Fixes the reported `MethodError: no method matching sort(::Set{Int64})`. |
| `_record_key`, `_run_record` | Routed required record fields through `_json_require`; added explicit unknown-`system_id` check. | Prevents direct missing-field failures for `condition`, `system_id`, `initial_condition_set`, `seed`, `basis_name`, `system_name`, and `loss`. |
| `main` | Added non-negative `--limit` validation and iterates via `Iterators.take(records, run_count)`. | Makes the cheap-test path robust for `--limit 0` and rejects negative limits clearly. |

## Checked Error Classes

| class requested in WP-N3b | static result |
|---|---|
| `Set` sorted as a vector | Fixed in `_intersect_terms`; remaining `intersect(Set(...))` use is only passed to `isempty`, which accepts sets. |
| `JSON3.Object` where Dict is expected | JSON access in the script now goes through `_json_get`/`_json_require`; output rows remain `Dict{String, Any}`. |
| missing `collect` calls | The reported set intersection now collects before sorting. No other `sort(::Set)` pattern remains. |
| indexing with `nothing` | `wp_n1_expected_support_terms`, `model_terms`, and each equation entry are checked before indexing/iteration. |
| possibly missing `model_terms` | Required through `_json_require` before original/original-pruned structure reconstruction. |
| possibly missing `wp_n1_expected_support_terms` | Treated as unavailable truth and skipped with `error = "true support is unavailable for this basis"`. |
| possibly missing `basis_name` | Required through `_json_require` before basis reconstruction. |
| truth equal to `nothing` | Existing skip path preserved; oracle/reference refits are not run for those cells. |

PowerShell inventory of the current input file:

| metric | count |
|---|---:|
| rows | 132 |
| missing `model_terms` | 0 |
| missing `wp_n1_expected_support_terms` | 0 |
| records with `wp_n1_expected_support_terms == null` | 30 |
| missing `basis_name` | 0 |
| missing `loss` | 0 |
| `model_terms` wrong equation count | 0 |
| null `model_terms` equations | 0 |
| non-null `wp_n1_expected_support_terms` wrong equation count | 0 |
| null non-null-truth equations | 0 |

## Commands For Claude

Short smoke test over a few cells:

```powershell
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n3_oracle_refit_smoke --limit 3 --fresh
```

Full WP-N3 run over the 132 input cells:

```powershell
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n3_oracle_refit --fresh
```

## Verification Performed Here

No Julia execution was attempted. Static text checks found no remaining `sort(intersect(...))`,
`records[1:min(...)]`, or raw `getproperty(...)` use outside `_json_get`.
