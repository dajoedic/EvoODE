# REPORT WP-RC-A2

## Status

Implemented the requested follow-up for the direct regression reality check. The Annihilator comparison is now
reported separately by group (`N1` = F4/F5/F8, `I` = F1/F2/F6) and by scope (`paired`, `reference`), and the baseline
false-unique rate is reported by group and method (`BS`, `STLSQ`).

## Files

- `experiments/annihilator_gate2a_v3/diagnostics/direct_regression_check.py`
  - Added `COMPARISON_GROUPS`.
  - Replaced the combined Annihilator summary with `annihilator.<scope>.<group>`.
  - Renamed the conditional Annihilator rate to `wrong_given_unambiguous`.
  - Added `baseline_false_unique.<group>.<method>`.
  - Changed `summary.md` output to a comparison table with rows by group and columns for paired Annihilator,
    reference Annihilator, BS, and STLSQ.
- `experiments/annihilator_gate2a_v3/tests/test_direct_regression_check.py`
  - The summary test now checks `summarize_records` output directly.
  - The test asserts the real `records_merged.jsonl` Annihilator counts by group and scope.
  - The synthetic baseline records now include both BS and STLSQ so the grouped baseline summary is exercised.

## Real Annihilator Counts Used In The Test

Source: `experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/orion/results/records_merged.jsonl`.

| Scope | Group | Functions | Total records | State counts | WRONG / (CORRECT + TRUE_NOT_REF + WRONG) |
|---|---|---|---:|---|---:|
| paired | N1 | F4, F5, F8 | 60 | AMBIGUOUS=35, WRONG=25 | 25/25 |
| paired | I | F1, F2, F6 | 60 | AMBIGUOUS=3, CORRECT=57 | 0/57 |
| reference | N1 | F4, F5, F8 | 300 | AMBIGUOUS=182, WRONG=118 | 118/118 |
| reference | I | F1, F2, F6 | 300 | AMBIGUOUS=3, CORRECT=297 | 0/297 |

## Old-Calculation Failure Check

The old combined calculation over F1, F2, F4, F5, F6, and F8 gives:

```text
paired old_combined_wrong_over_unambiguous=25/82
reference old_combined_wrong_over_unambiguous=118/415
```

The new test expects `annihilator.reference.N1 = 118/118` and `annihilator.reference.I = 0/297`, and it addresses the
output of `summarize_records` directly. With the old flat `annihilator.reference` summary, the nested
`annihilator.reference.N1` assertion is not satisfiable, and the combined denominator is 415 instead of the required
118 for N1.

## Commands

```text
python -m pytest experiments/annihilator_gate2a_v3/tests/test_direct_regression_check.py -q
python -m pytest experiments/annihilator_gate2a_v3/tests -q --basetemp .pytest_tmp
```

## Test Output

```text
python -m pytest experiments/annihilator_gate2a_v3/tests/test_direct_regression_check.py -q
................                                                         [100%]
16 passed in 1.49s
```

```text
python -m pytest experiments/annihilator_gate2a_v3/tests -q --basetemp .pytest_tmp
......................................................                   [100%]
54 passed in 86.21s (0:01:26)
```

## Notes

- No noisy-data run was started.
- No `--exact` run was started.
- No v3 files outside `direct_regression_check.py` and `test_direct_regression_check.py` were changed.
- No `docs/` files were changed.
