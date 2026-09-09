# Report WP-N11b

## Status

Blocked: implementation is complete, but Julia acceptance cannot be executed in this Codex environment.

## Single helper definition

`_append_unique_strings!` now has exactly one definition at `src/utils/strings.jl:3`.

`src/EvoODE.jl` includes `src/utils/strings.jl` immediately after logging setup and before interface, optimizer, and structure-search includes. This keeps the helper in a neutral utility layer: `src/optimize/bfgs.jl`, `src/structure/evogrow.jl`, `src/structure/evogrow_screening.jl`, and `src/structure/evogrow_v3.jl` can all use it without making the optimizer depend on the structure-search layer.

Static check performed:

```text
rg -n "^function _append_unique_strings!" src
```

Observed one definition:

```text
src\utils\strings.jl:3:function _append_unique_strings!(target::Vector{String}, values)
```

## Changed files

- `src/utils/strings.jl`: added the shared `_append_unique_strings!` definition.
- `src/EvoODE.jl`: included `utils/strings.jl` before `optimize/bfgs.jl` and the `evogrow` files.
- `src/optimize/bfgs.jl`: removed the local duplicate `_append_unique_strings!` definition.
- `src/structure/evogrow.jl`: removed the local duplicate `_append_unique_strings!` definition.
- `test/test_bfgs_retry_policy.jl`: added a local tolerance helper and changed float-valued assertions from exact equality to tolerance comparisons.

## Float equality changes

Exact equality was replaced by `retry_test_isapprox(...; rtol = 1e-12, atol = 1e-12)` at:

- `test/test_bfgs_retry_policy.jl:75`: `lval` against `EvoODE.MSE_SENTINEL_LOSS`.
- `test/test_bfgs_retry_policy.jl:111`: `params` against `[0.25]`.
- `test/test_bfgs_retry_policy.jl:112`: `lval` against `0.25`.
- `test/test_bfgs_retry_policy.jl:179`: `lval` against `0.25`.
- `test/test_bfgs_retry_policy.jl:211`: `params` against `[0.125]`.
- `test/test_bfgs_retry_policy.jl:212`: `lval` against `0.125`.

Exact comparisons left in place are counters, booleans, strings, and retcode text:

```text
calls[], meta.fit_attempts, meta.accepted_attempt, meta.retry_triggered,
meta.fit_failed, meta.loss_evals, meta.ode_solves, meta.method, meta.retcode
```

## Acceptance commands for Claude

Short package load / precompile check:

```bash
julia --project=. -e 'using EvoODE'
```

Focused tests:

```bash
julia --project=. test/test_bfgs_retry_policy.jl
julia --project=. test/test_bfgs_budget.jl
julia --project=. test/test_bfgs_fallback_order.jl
```

Fingerprint checks:

```bash
julia --project=. -e 'using EvoODE; println(EvoODE.phase_b_fingerprint()); println(EvoODE.config_fingerprint()); println(EvoODE.stage_cap_behavior_fingerprint())'
```

No campaign, regression cell, or long run was started by Codex.
