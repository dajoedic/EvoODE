# REPORT WP-N24

## Summary

Implemented ODEFormer integration timeout control, timeout counters, timeout-sentinel outcome naming, summary support, and `baselines/run_odeformer_repeatability.py`.

Status is blocked for acceptance execution, not for implementation:

- Docker is not reachable from this Codex environment: `docker image inspect evoode/odeformer-candidate:wp-n21 --format '{{.Id}}'` fails with `permission denied while trying to connect to the docker API at npipe:////./pipe/docker_engine`.
- The current `_wp_n23` data derive 30 changed cells, not the expected 26. The script aborts by default as required: `expected 26 changed cells, found 30; difference=4`.

## Code Changes

- `baselines/harness.py`
  - Added `integration_timeout_seconds` ODEFormer config support. Missing or `null` maps to the delivered 1.0 s limit in the record field.
  - Replaces `odeformer.envs.generators._integrate_ode` at adapter runtime using the function's `__wrapped__` target and ODEFormer's own `timeout`.
  - Counts `MyTimeoutError` by phase: `fit_candidate_ranking`, reconstruction/generalization before optimization, generalization after optimization, `constant_optimization`, and `unclassified`.
  - Restores the original `_integrate_ode` on adapter close.
  - Adds `odeformer_timeout` prediction outcome for the one-dimensional all-NaN ODEFormer sentinel.
- `baselines/summarize_odeformer_grid.py`
  - Picks up `odeformer_timeout` automatically through `harness.PREDICTION_OUTCOMES`.
- `baselines/run_odeformer_repeatability.py`
  - Derives changed and control cells from existing `reference/`, `reference_wp_n23/`, `candidate/`, and `candidate_wp_n23/` records.
  - Aborts if changed-cell count differs from the expected 26.
  - Supports `faithful` (`integration_timeout_seconds=null`) and `lifted` (`10.0`) modes, repetitions, sharding, 900 s per-cell hard timeout, global `--max-hours`, per-cell JSON records, `records.csv`, `cell_summary.csv`, and `--compare-modes`.
- `baselines/tests/test_harness.py`
  - Added tests for sentinel naming, timeout patch counting/restoration, and summary counting.

## ODEFormer Source Evidence

Local vendored source inspection:

- `outputs/third_party/odeformer/odeformer/envs/generators.py:823`: `_integrate_ode` is decorated with `@timeout(1)`.
- `outputs/third_party/odeformer/odeformer/envs/generators.py:922-924`: `MyTimeoutError` is caught and returned as `[np.nan for _ in range(len(times))]`.
- `outputs/third_party/odeformer/odeformer/model/sklearn_wrapper.py:173`: `fit(... sort_candidates=True ...)` calls `self.sort_candidates(...)`.
- `outputs/third_party/odeformer/odeformer/model/sklearn_wrapper.py:205`: sklearn wrapper `sort_candidates` evaluates candidates.
- `outputs/third_party/odeformer/odeformer/model/mixins.py:312` and `:342`: `integrate_prediction` calls module-level `integrate_ode`, which resolves to `odeformer.envs.generators.integrate_ode`.
- `outputs/third_party/odeformer/param_optimizer.py:98` and `:124`: `ConstantOptimizer.simulate()` integrates through the same `PredictionIntegrationMixin`, and `optimize()` calls the objective repeatedly.

The adapter patch targets `odeformer.envs.generators._integrate_ode`, so both `sort_candidates` and harness `integrate_prediction` paths are covered. Constant optimization is covered because `ConstantOptimizer` inherits the same integration mixin.

## Cell Derivation

Default command:

```bash
python -m baselines.run_odeformer_repeatability --derive-only --output-dir outputs/odeformer_repeatability/derive_probe
```

Observed result:

```text
ValueError: expected 26 changed cells, found 30; difference=4
```

Diagnostic run allowing the observed count:

```bash
python -m baselines.run_odeformer_repeatability --derive-only --expected-changed 30 --output-dir outputs/odeformer_repeatability/derive_probe_30
```

Output:

- `outputs/odeformer_repeatability/derive_probe_30/changed_cells.json`: 30 cells
- `outputs/odeformer_repeatability/derive_probe_30/control_cells.json`: 8 cells
- `outputs/odeformer_repeatability/derive_probe_30/selected_cells.json`: 38 cells

Breakdown of observed changed cells:

- reference: 18
- candidate: 12

## WP-N23 Record Check

Read-only check over existing `_wp_n23` records:

- `reference_wp_n23`: 504 records; `wrong_shape` outcomes: reconstruction 7, generalization 47; prediction array fields found: 0.
- `candidate_wp_n23`: 504 records; `wrong_shape` outcomes: reconstruction 7, generalization 49; prediction array fields found: 0.

Because prediction arrays are not stored in the records, acceptance point 3 cannot prove the exact sentinel shape from existing records. It is replaced by acceptance point 5, per task text.

## Commands Run

```bash
python -m pytest baselines/tests -q
```

Result:

```text
19 passed, 1 skipped in 14.65s
```

```bash
python -m py_compile baselines/run_odeformer_repeatability.py baselines/harness.py baselines/summarize_odeformer_grid.py
```

Result: no output, exit code 0.

```bash
docker image inspect evoode/odeformer-candidate:wp-n21 --format '{{.Id}}'
```

Result:

```text
permission denied while trying to connect to the docker API at npipe:////./pipe/docker_engine
```

## Full Repeatability Commands

Faithful, 4 shards, 3 repetitions:

```bash
python -m baselines.run_odeformer_repeatability --mode faithful --repetitions 3 --shards 4 --shard-index 0 --max-hours 24 --output-dir outputs/odeformer_repeatability/faithful_4
python -m baselines.run_odeformer_repeatability --mode faithful --repetitions 3 --shards 4 --shard-index 1 --max-hours 24 --output-dir outputs/odeformer_repeatability/faithful_4
python -m baselines.run_odeformer_repeatability --mode faithful --repetitions 3 --shards 4 --shard-index 2 --max-hours 24 --output-dir outputs/odeformer_repeatability/faithful_4
python -m baselines.run_odeformer_repeatability --mode faithful --repetitions 3 --shards 4 --shard-index 3 --max-hours 24 --output-dir outputs/odeformer_repeatability/faithful_4
```

Faithful, 1 shard, 3 repetitions:

```bash
python -m baselines.run_odeformer_repeatability --mode faithful --repetitions 3 --shards 1 --max-hours 24 --output-dir outputs/odeformer_repeatability/faithful_1
```

Lifted, 4 shards, 3 repetitions:

```bash
python -m baselines.run_odeformer_repeatability --mode lifted --repetitions 3 --shards 4 --shard-index 0 --max-hours 24 --output-dir outputs/odeformer_repeatability/lifted_4
python -m baselines.run_odeformer_repeatability --mode lifted --repetitions 3 --shards 4 --shard-index 1 --max-hours 24 --output-dir outputs/odeformer_repeatability/lifted_4
python -m baselines.run_odeformer_repeatability --mode lifted --repetitions 3 --shards 4 --shard-index 2 --max-hours 24 --output-dir outputs/odeformer_repeatability/lifted_4
python -m baselines.run_odeformer_repeatability --mode lifted --repetitions 3 --shards 4 --shard-index 3 --max-hours 24 --output-dir outputs/odeformer_repeatability/lifted_4
```

Mode comparison:

```bash
python -m baselines.run_odeformer_repeatability --compare-modes --output-dir outputs/odeformer_repeatability
```

## Runtime Bound

For the observed 30 changed + 8 control cells:

- 38 cells per repetition.
- 3 repetitions.
- 900 s hard per-cell limit.
- Bound per mode: `38 * 3 * 900 s = 102600 s = 28.5 h`.
- Faithful 4-shard wall-clock bound per shard: at most `ceil(38 / 4) * 3 * 900 s = 27000 s = 7.5 h`, before process overhead.
- Faithful 1-shard bound: 28.5 h.
- Lifted 4-shard wall-clock bound per shard: at most 7.5 h.
- Combined full campaign bound from hard per-cell limits: `3 * 28.5 h = 85.5 h` of cell budget; with four-way shard parallelism for two modes, expected wall-clock budget from limits is 43.5 h plus overhead.

The script also enforces `--max-hours`; cells skipped after that limit are written as `status=not_run_global_time_limit`.

## Acceptance Status

1. Not run against real ODEFormer because Docker daemon access is denied. Unit tests verify defaults and fields; real no-key same-cell equivalence remains open.
2. Partially verified by `test_odeformer_timeout_patch_counts_and_restores`: fake ODEFormer module proves replacement, count increment, configured 10.0 s, and restoration. Real tiny-timeout Docker test remains open.
3. Existing records lack prediction arrays; read-only counts are listed above. Per task, this is replaced by point 5.
4. Passed: `python -m pytest baselines/tests -q` -> 19 passed, 1 skipped.
5. Blocked: Docker daemon is not reachable from this environment.
6. This report provides source evidence, derivation result, runtime bounds, and exact full-run commands.
