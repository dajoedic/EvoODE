# REPORT WP-D2

## Budget Semantics

`max_loss_evals` is implemented as a total budget for one parameter fit. The loss closure checks the
budget before each objective evaluation. Once the budget is exhausted, it throws
`BFGSLossEvalBudgetExceeded`; the fit stops there and the Nelder-Mead fallback does not run unless
there is still budget left and no valid result exists.

## Best-So-Far Tracking

The objective closure now records the best finite loss as evaluations happen:

- `best_observed_loss`: `nothing` until the first finite loss is observed.
- `best_observed_p`: the parameter vector corresponding to that loss.

The recorded parameter vector is clamped with the same `clamp_val` used before simulation. That
keeps the returned vector consistent with the loss value, because `_predict_traj` simulates with
the clamped parameters. The final return clamp remains in place, so normal clamping semantics are
unchanged.

The MSE sentinel `1e6` is still just a finite observed loss. It can become best-so-far. The
distinction from "no valid loss was observed" is carried by metadata, not by overloading `1e6`.

## Method, Stop Reason, Validity

Existing fields remain present:

- `method`
- `retcode`
- all evaluation, solve, limit-hit and retcode counters

New optimizer metadata fields:

- `stop_reason`: e.g. `success`, `iteration_limit`, `loss_eval_budget`,
  `nonfinite_optimizer_minimum`, `exception`
- `result_valid`: whether the returned `(params, loss)` represents a finite observed/returned loss
- `result_source`: `optimizer_return`, `best_observed`, or `none`
- `best_loss_seen`: whether any finite loss was observed
- `best_observed_loss`: the finite best-so-far loss, or `nothing`

On a budget stop with at least one finite evaluation, the result is represented as:

- `method = "BFGS"` or `"NelderMead"`
- `retcode = "MaxLossEvals"`
- `stop_reason = "loss_eval_budget"`
- `result_valid = true`
- `result_source = "best_observed"`

If no finite loss was observed, `result_valid = false`, `best_loss_seen = false`, and the returned
loss is `Inf` rather than the MSE sentinel.

## Fallback Guard

The fallback guard changed from:

```julia
if method_used == "none"
```

to:

```julia
if !result_valid[] && loss_eval_count[] < opt.max_loss_evals
```

This separates "which method ran" from "is there a usable result" and keeps the budget total across
both methods.

## Tests

Added `test/test_bfgs_budget.jl`.

Test 1 records each evaluated parameter vector independently through the RHS/loss pair, forces a
small budget stop, and asserts that the returned loss and parameters equal the minimum finite
recorded evaluation.

Test 2 compares a fit whose loss is always `NaN` with a fit whose loss is always `1e6`. The first
must report no valid result and `Inf`; the second must report a valid result with best observed loss
`1e6`.

Command:

```powershell
julia --project=. --startup-file=no test\test_bfgs_budget.jl
```

Final output:

```text
Test Summary:                                | Pass  Total   Time
BFGS budget returns best observed evaluation |    9      9  11.3s
Test Summary:                                       | Pass  Total  Time
BFGS distinguishes no valid loss from sentinel loss |    7      7  2.7s
```

The first run in this environment paid Julia precompile cost; the testset times above are the
relevant smoke-test timings.

## Non-Binding Path

The non-binding path still accepts `res.u` and `res.minimum` from the optimizer return, then applies
the existing final clamp. I did not replace normal successful results with best-so-far. The closure
does not add objective evaluations, ODE solves, or random draws; it only records the already
computed finite loss after `evaluate_loss` returns.

The focused diff confirms no changes to optimizer defaults, call sites, `src/core/discover.jl`,
runner schemas, or `Manifest.toml`.
