# REPORT WP-N24c

## Summary

Implemented the timeout and outcome instrumentation fixes in `baselines/harness.py`, `baselines/run_odeformer_repeatability.py`, and `baselines/tests/test_harness.py`.

- Replaced ODEFormer's `_integrate_ode` timeout decorator at runtime with `odeformer_timeout_with_hook(...)`, a copy of the original signal timer logic with an `on_timeout` hook in the `SIGALRM` handler.
- Handler-fired timeouts are counted at alarm time, so a `MyTimeoutError` swallowed by a bare `except` is still counted.
- Per phase, `_integrate_ode` now records call outcomes: total calls, trajectory returns, `None` returns, NaN-sentinel returns, `None` after handler timeout, and NaN-sentinel after handler timeout.
- Renamed the prediction outcome value from `odeformer_timeout` to `odeformer_nan_sentinel`.
- Preserved `None` from `integrate_expression` and `optimize_constants` instead of converting it to a 0-dimensional NaN array.
- Repeatability cell summaries now include explicit `handler_timeout_count_min` and `handler_timeout_count_max` columns, while preserving the existing `timeout_count_min/max` columns.

ODEFormer sources under `outputs/third_party/` were not modified.

## Field List

Prediction outcome values:

```text
finite
none
odeformer_nan_sentinel
wrong_shape
nonfinite
```

R2 zero reasons:

```text
prediction_none
prediction_odeformer_nan_sentinel
prediction_wrong_shape
prediction_nonfinite
nonfinite_score
reference_no_variance
```

Handler timeout fields:

```text
odeformer_integration_timeout_seconds
odeformer_integration_timeout_count_total
odeformer_integration_timeout_count_<phase>
```

Integration outcome fields, for each phase:

```text
odeformer_integration_<phase>_call_count
odeformer_integration_<phase>_trajectory_count
odeformer_integration_<phase>_none_count
odeformer_integration_<phase>_nan_sentinel_count
odeformer_integration_<phase>_none_after_timeout_count
odeformer_integration_<phase>_nan_sentinel_after_timeout_count
```

Phases:

```text
fit_candidate_ranking
reconstruction_before_optimization
generalization_before_optimization
reconstruction_after_optimization
generalization_after_optimization
constant_optimization
unclassified
```

Repeatability summary additions:

```text
handler_timeout_count_min
handler_timeout_count_max
```

## Verification

Commands run:

```text
python -m pytest baselines/tests -q
python -m py_compile baselines/harness.py baselines/run_odeformer_repeatability.py baselines/tests/test_harness.py
```

Results:

- `python -m pytest baselines/tests -q` -> 25 passed, 3 skipped in 32.00 s.
- The skipped tests are platform-specific: two POSIX `SIGALRM` tests and the existing POSIX fork timeout test are skipped on this Windows runner.
- `py_compile` completed without output.

Acceptance coverage:

1. Decorator equivalence is covered by `test_odeformer_timeout_hook_matches_original_timer_semantics`; it is skipped locally because this runner has no `SIGALRM`, but it exercises the literal ODEFormer timer semantics on POSIX.
2. Bare-except timeout swallowing is covered by `test_odeformer_timeout_hook_counts_when_naked_except_returns_none`; it is skipped locally for the same `SIGALRM` reason.
3. `None` outcome and 0.0 R2 behavior are covered by `test_odeformer_adapter_preserves_none_prediction_for_outcome_and_r2` and `test_odeformer_constant_optimization_preserves_none_fit_prediction`.
4. Full local Python suite passed: 25 passed, 3 skipped.
5. Docker smoke remains for Claude.

## Docker Smoke Command For Claude

Correct image names:

```text
evoode/odeformer-reference:wp-n21
evoode/odeformer-candidate:wp-n21
```

Reference faithful smoke:

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evoode/odeformer-reference:wp-n21 -m baselines.run_odeformer_repeatability --environment-id reference --mode faithful --repetitions 2 --shards 1 --max-hours 1 --limit-cells 1 --output-dir outputs/odeformer_repeatability/reference_faithful_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evoode/odeformer-reference:wp-n21 -m baselines.run_odeformer_repeatability --collect --environment-id reference --mode faithful --repetitions 2 --shards 1 --output-dir outputs/odeformer_repeatability/reference_faithful_1_smoke
```

Candidate faithful smoke:

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evoode/odeformer-candidate:wp-n21 -m baselines.run_odeformer_repeatability --environment-id candidate --mode faithful --repetitions 2 --shards 1 --max-hours 1 --limit-cells 1 --output-dir outputs/odeformer_repeatability/candidate_faithful_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evoode/odeformer-candidate:wp-n21 -m baselines.run_odeformer_repeatability --collect --environment-id candidate --mode faithful --repetitions 2 --shards 1 --output-dir outputs/odeformer_repeatability/candidate_faithful_1_smoke
```

Full sharded runs: start all shard commands belonging to one run at the same time. Only separate runs are strict sequential units; for example, finish and collect `reference_faithful_4` before starting `reference_lifted_4`.

## Notes

The local Windows runner cannot execute the POSIX signal behavior tests, but the tests are present and run on a POSIX Docker/Python environment. No Docker smoke test was started in this Codex session.
