# WP-E2E-A2 Report

## Status

Done. The end-to-end Annihilator resampling now uses `scipy.interpolate.CubicSpline` on sorted duplicate-averaged `(x, f)` pairs. Plausibility check 2 excludes system 7 from the aggregate pass decision, stores its full numbers, and marks it with `"documented_exception": true`.

No `--run` command on systems 3, 7, 19, or 21 was executed.

## Files

- `experiments/annihilator_odebench_smoke/end2end.py`
- `experiments/annihilator_odebench_smoke/tests/test_end2end.py`
- `experiments/annihilator_odebench_smoke/results_e2e/sanity.json`

## Commands And Output

```text
python -m pytest experiments/annihilator_odebench_smoke/tests/test_end2end.py -q
10 passed, 1 error in 23.42s
```

This first run failed during fixture setup because Pytest could not scan `C:\Users\joedicke\AppData\Local\Temp\pytest-of-joedicke`:

```text
PermissionError: [WinError 5] Access is denied: 'C:\\Users\\joedicke\\AppData\\Local\\Temp\\pytest-of-joedicke'
```

The same test file passed with a workspace basetemp:

```text
python -m pytest experiments/annihilator_odebench_smoke/tests/test_end2end.py -q --basetemp=.pytest_tmp/e2e_a2_unit
11 passed in 1.60s
```

```text
python -m pytest experiments/annihilator_odebench_smoke/tests -q --basetemp=.pytest_tmp/e2e_a2_smoke
25 passed in 11.85s
```

```text
python -m pytest experiments/annihilator_gate2a_v3/tests -q --basetemp=.pytest_tmp/e2e_a2_v3
54 passed in 151.95s (0:02:31)
```

```text
python -m experiments.annihilator_odebench_smoke.end2end --sanity
exit code: 0
results: experiments/annihilator_odebench_smoke/results_e2e/sanity.json
```

`--sanity` emitted repeated PySINDy `AxesWarning: 2 axes labeled for array with 1 axes` warnings during the synthetic selection check and completed successfully.

## Sanity Results

`sanity.json` top-level `passed`: `true`.

Total sanity seconds: `590.1524760000175`.

Synthetic 1D ODE, eta 0:

| method | validation NRMSE_x | passed |
|---|---:|---|
| annihilator | 1.5791940095116773e-07 | true |
| sindy | 1.960490741024021e-07 | true |
| wsindy | 7.172187082240551e-09 | true |

Exact derivative, fixed reference class:

| system | reference class | validation NRMSE_x | fail reason | seconds | AML iterations | documented exception | passed |
|---:|---|---:|---|---:|---:|---|---|
| 3 | [3, 0] | 5.225989326623184e-07 | null | 28.011702699994203 | 1 | false | true |
| 7 | [3, 1] | Infinity | LEADING_ZERO_IN_TRAINING_DOMAIN | 34.331259300000966 | 90 | true | false |
| 19 | [2, 2] | 1.2686126456014222e-06 | null | 28.866915700025856 | 1 | false | true |
| 21 | [3, 0] | 3.06157799821987e-06 | null | 30.670484600006603 | 1 | false | true |

The aggregate pass decision for check 2 used only systems 3, 19, and 21. System 7 was computed and stored with its failure reason and `"documented_exception": true`, but it did not enter the aggregate `passed` value.

## Test Coverage Added

- Cubic spline resampling reproduces a cubic smooth function on irregular points with duplicate-`x` averaging at relative error below `1e-8`.
- Plausibility check 2 treats system 7 as a documented exception while preserving its failed per-system row.
