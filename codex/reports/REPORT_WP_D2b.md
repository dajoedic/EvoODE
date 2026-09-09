# REPORT WP-D2b

## Preference Levels

The fit result now has three distinct acceptance levels:

1. `optimizer_return`: a finite result returned by an optimizer that completed.
2. `best_observed`: immediate best-so-far acceptance for the budget-stop path.
3. `last_resort_best_observed`: best-so-far accepted only after no optimizer produced a usable
   result.

The WP-D2 metadata fields remain:

- `stop_reason`
- `result_valid`
- `result_source`
- `best_loss_seen`
- `best_observed_loss`

The implementation now also tracks internally whether an optimizer return was accepted, separately
from whether a best observed loss exists. This is the distinction WP-D2b needed.

## Fallback Guard

The fallback guard is now:

```julia
if !optimizer_result_accepted[] && loss_eval_count[] < opt.max_loss_evals
```

The primary BFGS non-finite-minimum and generic-exception branches record `method`, `retcode`, and
`stop_reason`, but they do not accept best-so-far. That leaves the fit eligible for Nelder-Mead when
budget remains.

After the fallback has either run or been skipped, best-so-far is accepted only if no result is
valid yet. That path reports `result_source = "last_resort_best_observed"`.

## Budget Path

The budget path is unaffected: `BFGSLossEvalBudgetExceeded` still immediately accepts best-so-far
with:

- `retcode = "MaxLossEvals"`
- `stop_reason = "loss_eval_budget"`
- `result_source = "best_observed"`

Since the budget is exhausted, the fallback guard is false by the shared total-budget condition.

## Tests

Added `test/test_bfgs_fallback_order.jl`.

The test uses a private solve hook with default `nothing`; production execution still calls
`Optimization.solve`. The hook lets the test force BFGS failure and Nelder-Mead success/failure
while still evaluating the real objective closure, so best-so-far tracking and the shared
`loss_evals` counter are exercised.

Command:

```powershell
julia --project=. --startup-file=no test\test_bfgs_fallback_order.jl
```

Output:

```text
Test Summary:                                | Pass  Total   Time
BFGS failure falls back before best observed |    7      7  12.5s
Test Summary:                                 | Pass  Total  Time
Best observed is accepted only as last resort |    8      8  0.2s
```

Unmodified WP-D2 budget test:

```powershell
julia --project=. --startup-file=no test\test_bfgs_budget.jl
```

Output:

```text
Test Summary:                                | Pass  Total   Time
BFGS budget returns best observed evaluation |    9      9  11.6s
Test Summary:                                       | Pass  Total  Time
BFGS distinguishes no valid loss from sentinel loss |    7      7  2.0s
```

## Unchanged Files

`test/test_bfgs_budget.jl` is byte-unchanged:

- SHA-256: `968fa0be3add7ce9b219bc9904d72572288c21922d797800d89bfb0a022d7671`
- `git diff -- test/test_bfgs_budget.jl` is empty.

No changes were made to `src/core/discover.jl`, optimizer call sites, runner record schemas, or
`Manifest.toml`.
