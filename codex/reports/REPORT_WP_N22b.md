# WP-N22b Report

## Changes

- `baselines/run_odeformer_grid.py` now enforces per-cell timeouts on POSIX runners by running each ODEFormer grid cell in a forked child process.
- If the child is still alive after `timeout_seconds_per_cell`, the parent terminates it, writes an atomic `status=timeout` record, sets `timeout_enforced=true`, and continues with the next cell.
- Completed cells are no longer reclassified after they finish. On non-POSIX runners, including local Windows tests, the runner executes the old in-process path, writes `timeout_enforced=false` in each record, and logs `timeout_enforced=false: hard per-cell timeout is only enforced on POSIX runners` to `stderr`.
- Resume keeps existing `timeout` records by default. The new explicit switch is `--rerun-timeouts`.

## Mechanism

The selected mechanism is POSIX child-process termination via Python `multiprocessing` with the `fork` start method. This is stronger than `signal.alarm` for the defect described in the task because the parent can terminate a cell even when the child is inside ODEFormer, SciPy, or optimizer code that may not safely unwind from a Python exception.

The trade-off is model load cost: the ODEFormer adapter is built inside the child process for each cell instead of being cached once in the parent process. That cost is intentional for this fix. It prevents a timed-out integration or constant-optimizer call from leaving the parent process, cached model, or following cells in a partially interrupted state.

## Tests

Local command run:

```bash
python -m pytest baselines/tests -q
```

Result:

```text
13 passed, 1 skipped in 18.77s
```

The skipped test is `test_odeformer_grid_hard_timeout_kills_hanging_cell_and_continues`, skipped on Windows with the reason:

```text
hard per-cell timeout uses POSIX forked worker termination; Windows records timeout_enforced=false
```

## Linux Image Abort Test

Claude can run the artificial hanging-cell test in the Linux ODEFormer image with:

```bash
docker run --rm --entrypoint python \
  -v "$PWD/baselines:/workspace/EvoODE/baselines" \
  -v "$PWD/benchmarks:/workspace/EvoODE/benchmarks" \
  -v "$PWD/outputs:/workspace/EvoODE/outputs" \
  -v "$PWD/analysis:/workspace/EvoODE/analysis" \
  evocode/odeformer-candidate:wp-n22 \
  -m pytest baselines/tests/test_harness.py::test_odeformer_grid_hard_timeout_kills_hanging_cell_and_continues -q
```

Pass criterion: the command exits with code `0`, the test is not skipped, and pytest reports `1 passed`. The test patches the cell runner to sleep for the first cell, verifies that the first record is `status=timeout` with `timeout_enforced=true`, and verifies that the next cell is still computed as `status=success`.

## Claude's verification (2026-09-23)

Run in the reference image (`evoode/odeformer-reference:wp-n21`, `baselines/` mounted), pytest
installed only in the throwaway container: `1 passed, 8 warnings in 6.21s` — the test was not
skipped, the hanging cell is recorded as `status=timeout, timeout_enforced=true`, the next cell
computes `status=success`.
