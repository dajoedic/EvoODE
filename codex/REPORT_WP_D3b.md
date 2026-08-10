# WP-D3b Report

## Corrected counter conditions

The four per-run optimizer counters now mean:

- `total_optimizer_budget_stop_fits`: `stop_reason == "loss_eval_budget"`
- `total_optimizer_fallback_result_fits`: `method == "NelderMead"` and `result_source == "optimizer_return"`
- `total_optimizer_last_resort_fits`: `result_source == "last_resort_best_observed"`
- `total_optimizer_invalid_result_fits`: `result_valid == false`

The fix is shared through `_fit_fallback_optimizer_return(fit_meta)` in `src/structure/evogrow.jl` and used by all four aggregation sites:

- `src/structure/evogrow.jl`
- `src/structure/evogrow_v3.jl`
- `src/structure/evogrow_screening.jl`
- `src/structure/gp.jl`

## Mutual exclusivity

From `src/optimize/bfgs.jl` acceptance logic:

- Budget stop accepts the best observed value through `accept_best_observed!` with `stop_reason = "loss_eval_budget"` and default `result_source = "best_observed"`.
- Fallback result accepts through `accept_optimizer_result!("NelderMead", ...)`, which sets `result_source = "optimizer_return"`.
- Last resort accepts through `accept_best_observed!(...; source = "last_resort_best_observed")`.

Those three `result_source`/`stop_reason` combinations cannot all be true for the same accepted fit. In particular, a failed fallback can leave `method == "NelderMead"` while the accepted value is last resort; requiring `result_source == "optimizer_return"` prevents that last-resort path from being counted as a fallback result.

`invalid result` is allowed to overlap. A budget stop with no finite observed loss is both `stop_reason == "loss_eval_budget"` and `result_valid == false`; that is intentional, because it tells campaign analysis both why the fit stopped and that no valid result survived.

## Test changes

`test/test_bfgs_fallback_order.jl` now asserts the counter-driving semantics for both WP-D2b cases:

- Genuine fallback: `method == "NelderMead"` and `result_source == "optimizer_return"` counts as fallback result and not last resort.
- Last resort after failed fallback: `method == "NelderMead"` and `result_source == "last_resort_best_observed"` counts as last resort and not fallback result.

`test/test_bfgs_budget.jl` was not edited. Its SHA256 remained:

```text
968FA0BE3ADD7CE9B219BC9904D72572288C21922D797800D89BFB0A022D7671
```

## Fingerprint

Measured after WP-D3b:

```text
7acd3ebf3f60b974
```

This matches WP-D3; WP-D3b did not change `config_fingerprint()`.

## Verification performed

Smoke only; no regression suite or experiment run was started.

Commands run:

```powershell
Get-FileHash test/test_bfgs_budget.jl -Algorithm SHA256
rg -n "_fit_fallback_optimizer_return|optimizer_fallback_result_fits \+=|fallback_result_count|last_resort_count" src/structure test/test_bfgs_fallback_order.jl
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); println(config_fingerprint())"
```

Pass observations:

- budget-test hash stayed unchanged
- all four aggregation paths now route fallback counting through `_fit_fallback_optimizer_return`
- fingerprint printed `7acd3ebf3f60b974`

Two attempted Julia smoke commands timed out at 124 seconds during startup/precompile and produced no code-level failure output. The later fingerprint command completed successfully with a longer timeout.

## Commands for user-run verification

Targeted counter test. Expected runtime: about 1-2 minutes.

```powershell
julia --project=. --startup-file=no test\test_bfgs_fallback_order.jl
```

Pass looks like both testsets reporting all tests passed, including the new fallback/last-resort counter assertions.

Budget test unchanged. Expected runtime: about 1-2 minutes.

```powershell
julia --project=. --startup-file=no test\test_bfgs_budget.jl
```

Pass looks like all tests passed with no failures or errors.

Fingerprint check. Expected runtime: under 2 minutes after Julia precompile is warm, but allow up to 5 minutes on a cold start.

```powershell
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); println(config_fingerprint())"
```

Pass looks like:

```text
7acd3ebf3f60b974
```
