# WP-N27b Report

## Scope

Fixed the ODEFormer grid hard-timeout worker communication in `baselines/run_odeformer_grid.py`.

## Changes

- `run_cell_with_hard_timeout` now reads from the multiprocessing queue before joining the child process.
- The parent uses bounded queue polling (`0.05` s) and checks `process.is_alive()` / `exitcode` between polls, so `budget=None` does not block forever when the child exits without sending a result.
- The timeout path still terminates, joins, kills if needed, and returns the existing timeout record shape.
- The child-exited-without-record path still returns the existing error record shape.
- Process cleanup after receiving a queue result still joins with a short grace period and terminates/kills if the child remains alive.

## Pattern Search

Searched `baselines` for:

- `get_context("fork")`
- `process.join`
- `result_queue.get`
- `result_queue.get_nowait`
- `run_cell_with_hard_timeout`

Findings:

- `baselines/run_odeformer_grid.py` contained the affected implementation and was updated.
- `baselines/run_odeformer_repeatability.py` does not implement a separate fork/join/queue pattern; it calls `run_odeformer_grid.run_cell_with_hard_timeout`, so it uses the fixed path.

## Tests Added

Added three focused tests in `baselines/tests/test_harness.py`:

- A large queue payload test writes a 1 MiB record payload and verifies `run_cell_with_hard_timeout(..., budget=None)` returns the record. It has a 3.0 s `SIGALRM` guard so a regression cannot hang the suite on POSIX.
- A child `os._exit(3)` test verifies `budget=None` returns quickly with the existing error-record behavior.
- A slow child test verifies a `0.05` s budget returns the existing timeout-record behavior.

These tests are POSIX/fork-specific and are skipped on Windows.

## Verification

Command run:

```text
python -m pytest baselines/tests -q
```

Result on this Windows session:

```text
29 passed, 5 skipped in 24.05s
```

The 5 skipped tests include the POSIX/fork-specific hard-timeout tests added here.
