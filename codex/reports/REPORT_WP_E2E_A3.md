# REPORT WP-E2E-A3

## Summary

Implemented worker-safe end-to-end record handling in `experiments/annihilator_odebench_smoke/end2end.py`.

- `fit_record` now returns a recursively JSON-safe record: dict/list/string/integer/float/bool/null values only, with NumPy arrays converted to lists and callables removed.
- `run_command` now catches per-task failures for both serial and `ProcessPoolExecutor` execution, writes task-keyed tracebacks to `run.log` and `failed_tasks.jsonl`, and continues remaining tasks.
- `DONE` markers now include `failed_tasks`.
- Added real `ProcessPoolExecutor` tests for serializable records and continued execution after a worker failure.

No `--run` was executed on ODEBench systems 3, 7, 19, or 21.

## Tests

Command:

```text
python -m pytest experiments/annihilator_odebench_smoke/tests/test_end2end.py -q --basetemp=.pytest_tmp_wp_e2e_a3
```

Output:

```text
..............                                                           [100%]
14 passed in 21.20s
```

Command:

```text
python -m pytest experiments/annihilator_odebench_smoke/tests -q --basetemp=.pytest_tmp_wp_e2e_a3_smoke
```

Output:

```text
............................                                             [100%]
28 passed in 55.21s
```

Command:

```text
python -m pytest experiments/annihilator_gate2a_v3/tests -q --basetemp=.pytest_tmp_wp_e2e_a3_v3
```

Output:

```text
......................................................                   [100%]
54 passed in 221.69s (0:03:41)
```

## Notes

An initial `pytest` run without `--basetemp` failed before affected tests executed because the sandbox could not access `C:\Users\joedicke\AppData\Local\Temp\pytest-of-joedicke`. The accepted runs above used workspace-local basetemp directories.
