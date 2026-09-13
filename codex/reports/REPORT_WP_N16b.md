# REPORT WP-N16b

## Cause

`studies/regression/run_batch_cell.jl` loaded `phase_c_config.jl` lazily inside
`_ensure_phase_c_config()`. The Phase-C dispatch path then immediately called
names defined by that include at three sites:

- `_batch_fingerprint`: `phase_c_fingerprint()`
- `_batch_variant`: `phase_c_variant(...)`
- `_batch_system`: `phase_c_system(...)`

On Julia 1.12 this crosses a world-age boundary: the running function is in the
older world, while the methods created by `include` are in the newer world.

## Change

`phase_c_config.jl` is now included at top level in `run_batch_cell.jl`, directly
beside `run_regression.jl` and `phase_b_config.jl`.

The lazy loader `_ensure_phase_c_config()` and its three call sites were removed.
Phase-C rows now call already-loaded Phase-C functions and constants.

## Why This Is World-Age Safe

Top-level includes are evaluated before `main()` calls `run_batch_cell(...)`.
Therefore `phase_c_fingerprint`, `phase_c_variant`, `phase_c_system`, and the
Phase-C constants are defined before any batch-cell function begins executing.
No Phase-C method is created during the dynamic execution of `_batch_fingerprint`,
`_batch_variant`, or `_batch_system`.

This matches the existing Phase-B loading pattern in the same file.

## Same Pattern Elsewhere

I statically scanned Julia files under `studies/`, `src/`, `test/`,
`benchmarks/`, and `experiments/` for `include(` inside `function` bodies using
a simple function-depth audit. Result: 0 matches after this change.

`studies/regression/wp_n1_basis_probe.jl` still has guarded includes, but both
guards are at top level, not inside a function body.

## Verification Status

Julia was not executed in this Codex session. The local protocol says Julia is
environment-blocked for Codex and Claude runs Julia acceptance. No runtime result
is claimed here.

Commands for Claude:

```text
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl 1 --manifest outputs/studies/regression/phase_c/manifest.csv --output-dir outputs/studies/regression/phase_c/smoke_tasks
```

```text
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl 1 --manifest outputs/studies/regression/phase_b/manifest.csv --output-dir outputs/studies/regression/phase_b/smoke_tasks
```
