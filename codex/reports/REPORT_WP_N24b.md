# REPORT WP-N24b

## Summary

Implemented the repeatability-script fixes in `baselines/run_odeformer_repeatability.py`.

- Compute runs now require `--environment-id reference|candidate`.
- The script checks the installed environment before the first cell using the same `environment` record feature used by `_wp_n23`: `torch`.
- Shard processes write only per-cell JSON records under `records/`; `--collect` builds `records.jsonl`, `records.csv`, `cell_summary.csv`, and `collection_summary.json`.
- Cells skipped after the global time limit are written as individual `status=not_run_global_time_limit` records.
- Changed-cell default is 30, with required per-environment counts 18 reference and 12 candidate.
- Controls are selected per environment: 4 reference and 4 candidate.
- `--compare-modes` only reads directories matching `<environment>_<mode>_<shards>`.
- `--limit-cells` supports smoke runs.

`baselines/harness.py` was not changed for WP-N24b.

## Verification

Commands run:

```text
python -m py_compile baselines/run_odeformer_repeatability.py baselines/tests/test_harness.py
python -m baselines.run_odeformer_repeatability --derive-only --environment-id reference --limit-cells 1 --output-dir outputs/odeformer_repeatability/derive_probe_n24b
python -m pytest baselines/tests -q
python -m baselines.run_odeformer_repeatability --environment-id reference --limit-cells 1 --repetitions 1 --max-hours 0.01 --output-dir outputs/odeformer_repeatability/reference_faithful_1_local_env_check
```

Results:

- `pytest`: 23 passed, 1 skipped in 12.07 s.
- Derived changed cells: 30 total; reference 18, candidate 12.
- Derived controls: 8 total; reference 4, candidate 4.
- Expected record environment signatures: reference `torch=2.0.0+cpu`, candidate `torch=2.14.0+cpu`.
- Local installed signature: `torch=2.6.0`.
- Wrong local environment abort result: `RuntimeError: installed environment does not match reference: torch: expected 2.0.0+cpu, installed 2.6.0`.

The abort occurs before benchmark/export loading and before any cell execution.

## Config Source Check

The repeatability script uses `baselines/configs/odeformer_grid.json` and `run_odeformer_grid.selected_config_objects(...)`, the same source as the grid run. Reference and candidate config objects differ only in `environment_id`:

```text
beam10_noopt: environment_id reference vs candidate
beam10_opt: environment_id reference vs candidate
beam50_noopt: environment_id reference vs candidate
beam50_opt: environment_id reference vs candidate
```

The script writes this check to `grid_config_differences.json` in each repeatability run directory.

## Docker Commands For Claude

All commands follow the WP-N22 mount pattern for `baselines/`, `outputs/`, and `analysis/`.

### Smoke: 1 Cell, 2 Repetitions, Each Mode, Each Environment

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode faithful --repetitions 2 --shards 1 --max-hours 1 --limit-cells 1 --output-dir outputs/odeformer_repeatability/reference_faithful_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id reference --mode faithful --repetitions 2 --shards 1 --output-dir outputs/odeformer_repeatability/reference_faithful_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode lifted --repetitions 2 --shards 1 --max-hours 1 --limit-cells 1 --output-dir outputs/odeformer_repeatability/reference_lifted_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id reference --mode lifted --repetitions 2 --shards 1 --output-dir outputs/odeformer_repeatability/reference_lifted_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode faithful --repetitions 2 --shards 1 --max-hours 1 --limit-cells 1 --output-dir outputs/odeformer_repeatability/candidate_faithful_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id candidate --mode faithful --repetitions 2 --shards 1 --output-dir outputs/odeformer_repeatability/candidate_faithful_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode lifted --repetitions 2 --shards 1 --max-hours 1 --limit-cells 1 --output-dir outputs/odeformer_repeatability/candidate_lifted_1_smoke
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id candidate --mode lifted --repetitions 2 --shards 1 --output-dir outputs/odeformer_repeatability/candidate_lifted_1_smoke
```

Runtime bound per smoke compute command: `1 cell * 2 repetitions * 900 s = 1800 s = 0.5 h`; `--max-hours 1` is looser than the per-cell bound.

### Full Runs: Strict Sequential Order

Run these commands strictly one after another. Do not overlap runs, because load is the measurement.

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode faithful --repetitions 3 --shards 4 --shard-index 0 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode faithful --repetitions 3 --shards 4 --shard-index 1 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode faithful --repetitions 3 --shards 4 --shard-index 2 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode faithful --repetitions 3 --shards 4 --shard-index 3 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id reference --mode faithful --repetitions 3 --shards 4 --output-dir outputs/odeformer_repeatability/reference_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode faithful --repetitions 3 --shards 1 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_faithful_1
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id reference --mode faithful --repetitions 3 --shards 1 --output-dir outputs/odeformer_repeatability/reference_faithful_1
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode lifted --repetitions 3 --shards 4 --shard-index 0 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode lifted --repetitions 3 --shards 4 --shard-index 1 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode lifted --repetitions 3 --shards 4 --shard-index 2 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --environment-id reference --mode lifted --repetitions 3 --shards 4 --shard-index 3 --max-hours 7 --output-dir outputs/odeformer_repeatability/reference_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-reference:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id reference --mode lifted --repetitions 3 --shards 4 --output-dir outputs/odeformer_repeatability/reference_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode faithful --repetitions 3 --shards 4 --shard-index 0 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode faithful --repetitions 3 --shards 4 --shard-index 1 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode faithful --repetitions 3 --shards 4 --shard-index 2 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode faithful --repetitions 3 --shards 4 --shard-index 3 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id candidate --mode faithful --repetitions 3 --shards 4 --output-dir outputs/odeformer_repeatability/candidate_faithful_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode faithful --repetitions 3 --shards 1 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_faithful_1
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id candidate --mode faithful --repetitions 3 --shards 1 --output-dir outputs/odeformer_repeatability/candidate_faithful_1
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode lifted --repetitions 3 --shards 4 --shard-index 0 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode lifted --repetitions 3 --shards 4 --shard-index 1 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode lifted --repetitions 3 --shards 4 --shard-index 2 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --environment-id candidate --mode lifted --repetitions 3 --shards 4 --shard-index 3 --max-hours 7 --output-dir outputs/odeformer_repeatability/candidate_lifted_4
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --collect --environment-id candidate --mode lifted --repetitions 3 --shards 4 --output-dir outputs/odeformer_repeatability/candidate_lifted_4
```

### Compare Modes

```text
docker run --rm --entrypoint python -v "$PWD/baselines:/workspace/EvoODE/baselines" -v "$PWD/outputs:/workspace/EvoODE/outputs" -v "$PWD/analysis:/workspace/EvoODE/analysis" evocode/odeformer-candidate:wp-n22 -m baselines.run_odeformer_repeatability --compare-modes --output-dir outputs/odeformer_repeatability
```

## Full-Run Bounds

Per-cell hard timeout: 900 s. Full commands also use `--max-hours 7`.

- Reference cells: 22 per repetition (18 changed + 4 controls), 66 cell-repetitions.
- Candidate cells: 16 per repetition (12 changed + 4 controls), 48 cell-repetitions.
- Reference faithful 4 shards: per shard at most `ceil(22 / 4) * 3 * 900 s = 16200 s = 4.5 h`, below `--max-hours 7`.
- Reference lifted 4 shards: same bound, 4.5 h.
- Reference faithful 1 shard: per-cell bound `22 * 3 * 900 s = 59400 s = 16.5 h`; `--max-hours 7` is the controlling bound and skipped cells are recorded.
- Candidate faithful 4 shards: per shard at most `ceil(16 / 4) * 3 * 900 s = 10800 s = 3.0 h`, below `--max-hours 7`.
- Candidate lifted 4 shards: same bound, 3.0 h.
- Candidate faithful 1 shard: per-cell bound `16 * 3 * 900 s = 43200 s = 12.0 h`; `--max-hours 7` is the controlling bound and skipped cells are recorded.

## Acceptance Status

1. Passed by tests and CLI: wrong environment aborts before any cell starts.
2. Passed by tests: simulated shard records merge through `--collect`, including `not_run_global_time_limit` records.
3. Passed by tests: cell derivation yields changed counts 18 / 12 and controls 4 / 4.
4. Passed: `python -m pytest baselines/tests -q` -> 23 passed, 1 skipped.
5. Docker smoke and full ODEFormer runs remain for Claude, per task text.
