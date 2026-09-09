# WP-D3 Report

## Optimizer parameters at the campaign call sites

`studies/regression/run_regression.jl` already constructed the reference optimizer with the campaign budget. WP-D3 made the remaining implicit deterministic values explicit in the builder/fingerprint:

- `maxiters = 200`
- `abstol = 1e-6`
- `reltol = 1e-6`
- `maxiters_solve = 10^6`
- `max_loss_evals = 100_000`
- `clamp_val = 10.0`
- `reject_nonfinite = false`
- `divergence_limit = Inf`
- `time_limit_s = Inf` is fingerprinted as disabled, but is not passed to `BFGSOptimizer`.

`experiments/generate_manifest.jl` now writes the experiment-run config fields:

- `bfgs_maxiters = 200`
- `bfgs_abstol = 1e-6`
- `bfgs_reltol = 1e-6`
- `bfgs_maxiters_solve = 10^6`
- `bfgs_max_loss_evals = 100_000`
- `bfgs_clamp_val = 10.0`

`experiments/run_experiment.jl` now constructs `BFGSOptimizer` from those config fields instead of struct defaults. `time_limit_s` remains unset, so the disabled default is preserved.

These values are duplicated in the manifest generator instead of imported from `studies/regression/run_regression.jl`: including the regression runner from the experiment generator would bring in regression systems, environment filters, progress/logging behavior, and script-level side effects. The duplicated values are listed above.

The transitive campaign optimizer construction in `src/structure/evogrow_screening.jl` was also audited. `_polish_optimizer` now preserves `max_loss_evals` when deriving the bounded polish optimizer from the campaign optimizer.

Frozen artifacts under `experiments/paper1_phaseA_v1/` were not touched.

## Out-of-scope backlog

These call sites still construct `BFGSOptimizer` without a campaign evaluation budget, and were deliberately not fixed because WP-D3 is limited to the campaign runners and their transitive optimizer construction:

- `benchmarks/run_odebench.jl`
- `benchmarks/benchmark_evogrow.jl`
- `studies/phase1_diag/run_phase1_diag.jl`
- `studies/generalization/generalization_study.jl`
- `studies/numerics/solver_tolerance_noise_floor.jl`
- `studies/numerics/system26_tolerance_screening.jl`
- `studies/profiling/profile_init.jl`
- `studies/profiling/profile_eval_cost.jl`
- `studies/debug/compare_screening_variant.jl`
- `studies/debug/debug_single.jl`
- `studies/visualization/animate_search.jl`

## Record schema

New per-run fields:

- `total_optimizer_budget_stop_fits`
- `total_optimizer_fallback_result_fits`
- `total_optimizer_last_resort_fits`
- `total_optimizer_invalid_result_fits`

Aggregation is done in the structure-search code where fit metadata is already counted:

- `src/structure/evogrow.jl`
- `src/structure/evogrow_v3.jl`
- `src/structure/evogrow_screening.jl`
- `src/structure/gp.jl`

Propagation to records is done in:

- `studies/regression/run_regression.jl`
- `experiments/run_experiment.jl` metrics and result payloads

The aggregation is observational only. It runs after `fit_parameters` returns, reads `fit_meta.method`, `fit_meta.stop_reason`, `fit_meta.result_source`, and `fit_meta.result_valid`, then increments counters. It does not alter params, loss, objective, sorting, promotion, stopping, polishing, or final refits.

## `Inf` serialization

This can reach records: WP-D2 returns `loss = Inf` when no finite loss was ever observed, and search results can propagate that into `result.loss`/record `loss`.

Observed JSON3 behavior:

```text
ERROR: Inf not allowed to be written in JSON spec
```

Both runners now sanitize at the JSON serialization boundary. Non-finite floats are written as strings (`"Inf"`, `"-Inf"`, `"NaN"`), preserving the distinction from a real numeric `1.0e6`.

Observed sanitized output:

```json
{"x":"Inf","y":1.0e6}
```

## Fingerprint

Before WP-D3:

```text
db8ec4003aa99a0e
```

After WP-D3:

```text
7acd3ebf3f60b974
```

This change is expected. The new value is the campaign identity for records generated with these optimizer/fingerprint settings.

## Verification performed

Smoke only; no regression suite or experiment run was started.

Commands run:

```powershell
julia --project=. --startup-file=no --% -e "code = read(`git show HEAD:studies/regression/run_regression.jl`, String); include_string(Main, code, \"studies/regression/run_regression.jl\"); println(config_fingerprint())"
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); println(config_fingerprint())"
julia --project=. --startup-file=no --% -e "using JSON3; println(JSON3.write(Dict(\"x\" => Inf, \"y\" => 1.0e6)))"
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); println(JSON3.write(json_safe(Dict(\"x\" => Inf, \"y\" => 1.0e6))))"
julia --project=. --startup-file=no --% -e "include(\"src/EvoODE.jl\"); using .EvoODE; println(\"load ok\")"
julia --project=. --startup-file=no --% -e "for f in (\"experiments/run_experiment.jl\", \"experiments/generate_manifest.jl\"); Meta.parseall(read(f, String)); println(f * \" parse ok\"); end"
```

Pass observations:

- old fingerprint printed `db8ec4003aa99a0e`
- new fingerprint printed `7acd3ebf3f60b974`
- raw JSON3 rejected `Inf`
- `json_safe` wrote `{"x":"Inf","y":1.0e6}`
- `EvoODE` printed `load ok`
- both experiment scripts printed `parse ok`

## Commands for user-run smoke

Single cheap regression cell, isolated from the normal history file. Expected runtime: about 1-3 minutes on this workstation.

```powershell
$env:EVO_REGRESSION_HISTORY_PATH = "outputs\studies\regression\wp_d3_smoke.jsonl"
$env:FRESH = "1"
$env:EVO_REGRESSION_VARIANT = "evogrow_v2_2_stage_capped"
$env:EVO_REGRESSION_SYSTEM_ID = "11"
$env:EVO_REGRESSION_IC_SET = "1"
$env:EVO_REGRESSION_SEED = "42"
julia --project=. --startup-file=no studies\regression\run_regression.jl
```

Pass looks like:

- `Regression history fingerprint: 7acd3ebf3f60b974`
- `Total cells: 1`
- `Appended 1 records to outputs\studies\regression\wp_d3_smoke.jsonl`
- the run completes with `error=null`

Check the new fields in the produced record:

```powershell
julia --project=. --startup-file=no --% -e "using JSON3; rec = JSON3.read(first(eachline(\"outputs/studies/regression/wp_d3_smoke.jsonl\"))); for k in (\"total_optimizer_budget_stop_fits\", \"total_optimizer_fallback_result_fits\", \"total_optimizer_last_resort_fits\", \"total_optimizer_invalid_result_fits\", \"total_loss_evals\", \"total_optimizer_eval_budget_limit_hits\"); println(k * \"=\" * string(getproperty(rec, Symbol(k)))); end"
```

Pass looks like integer values for the four new fields and existing numeric values for `total_loss_evals` and `total_optimizer_eval_budget_limit_hits`.

Targeted WP-D2/WP-D2b tests, unmodified. Expected runtime: about 1-2 minutes each.

```powershell
julia --project=. --startup-file=no test\test_bfgs_budget.jl
julia --project=. --startup-file=no test\test_bfgs_fallback_order.jl
```

Pass looks like both testsets reporting all tests passed, with no failures or errors.
