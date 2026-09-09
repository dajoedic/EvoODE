# REPORT WP-N11

## Result

Implemented the BFGS retry-on-failure policy as a named optimizer parameter, but did not run Julia tests in this environment. Per `codex/CODEX_PROTOCOL.md`, Julia execution is blocked here, so this task is reported as `blocked` for environment reasons after implementation.

## Implementation

- `src/optimize/bfgs.jl`: added `max_fit_attempts::Int = 1` to `BFGSOptimizer`, documented it as a maximum attempt count after failure, and kept the previous single-fit implementation as `_fit_parameters_once`.
- `src/optimize/bfgs.jl`: added `fit_attempt_failed(loss_value, result_valid)` with the three required conditions: non-finite loss, loss `>= MSE_SENTINEL_LOSS`, or invalid result.
- `src/optimize/bfgs.jl`: wrapped `fit_parameters` in a retry loop. Attempt 1 passes through the caller's `p0`; attempts 2..k pass `p0 = nothing`, forcing a fresh random start.
- `src/optimize/bfgs.jl`: aggregates cost counters across attempts and returns diagnostics from the accepted attempt, plus `attempt_solver_retcodes`, `attempt_optimizer_retcodes`, `fit_attempts`, `accepted_attempt`, `retry_triggered`, and `fit_failed`.
- `src/loss/mse.jl`: introduced `MSE_SENTINEL_LOSS = 1e6` and reused it in `evaluate_loss(::MSELoss, ...)`.
- `src/EvoODE.jl`: exported `MSE_SENTINEL_LOSS`.
- `src/structure/evogrow.jl`: added `total_parameter_fit_attempts` and per-level `parameter_fit_attempts` without changing `total_parameter_fits`.
- `src/structure/evogrow_v3.jl`: added the same attempt counter for EvoGrowV3 and EvoGrowStageCapped metadata.
- `src/structure/evogrow_screening.jl`: added the same attempt counter to screening totals and level logs.
- `studies/regression/run_regression.jl`: added `total_parameter_fit_attempts` to emitted records without touching fingerprint inputs.
- `test/test_bfgs_retry_policy.jl`: added hook-based tests for the failure predicate, k=1 no retry, k=3 retry success, k=3 all failures, cost-counter aggregation, and first-attempt success.

## RNG preservation for k = 1

The unchanged random stream for `max_fit_attempts = 1` is ensured in `src/optimize/bfgs.jl:752-758`: the wrapper computes `max_attempts`, enters exactly one loop iteration, passes the original `p0` as `attempt_p0`, and immediately calls `_fit_parameters_once`.

The random start is still drawn only inside `_fit_parameters_once` at `src/optimize/bfgs.jl:306`, exactly where the previous `fit_parameters` body drew it. No random vector is precomputed for later attempts. Retry attempts use `attempt_p0 = nothing` at `src/optimize/bfgs.jl:757`, so random draws for attempts 2..k occur only after a failed prior result.

## Test commands for Claude

Short focused test:

```bash
julia --project=. test/test_bfgs_retry_policy.jl
```

Related BFGS regression tests:

```bash
julia --project=. test/test_bfgs_budget.jl
julia --project=. test/test_bfgs_fallback_order.jl
```

Full package test:

```bash
julia --project=. -e 'using Pkg; Pkg.test()'
```

Fingerprint checks:

```bash
julia --project=. -e 'include("studies/regression/phase_b_config.jl"); println(phase_b_fingerprint()); println(stage_cap_behavior_fingerprint())'
```

Expected unchanged values:

- `phase_b_fingerprint() == "604e79733b22d64d"`
- `stage_cap_behavior_fingerprint() == "ffb0266c7913352c"`

## Not run

No Julia command was run by Codex. The environment is expected to fail with `A specified logon session does not exist`; Claude must run the acceptance commands.

## B1 reminder

The retry parameter is intentionally not added to the Phase-B fingerprint. B1 must add the Phase-C restart parameter to the Phase-C fingerprint when that fingerprint is introduced.

