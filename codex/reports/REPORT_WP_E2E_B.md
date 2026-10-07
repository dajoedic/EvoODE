# REPORT WP-E2E-B

## Status

Done.

## Changed Files

- `experiments/annihilator_odebench_smoke/end2end.py`
- `experiments/annihilator_odebench_smoke/tests/test_end2end.py`
- `experiments/annihilator_odebench_smoke/results_e2e_v2/setup.json`
- `experiments/annihilator_odebench_smoke/results_e2e_v2/reference.json`
- `experiments/annihilator_odebench_smoke/results_e2e_v2/sanity.json`
- `experiments/annihilator_odebench_smoke/results_e2e_v2/summary.json`

## Implementation

- Added `--spec` with default `end2end_v1`; `end2end_v2` defaults to `results_e2e_v2`.
- Kept v1 resampling as cubic spline over unique x-values.
- Added v2 Annihilator resampling: 200 equal-width bins, non-empty bin means for x and f, bin counts as weights, `make_smoothing_spline(..., lam=None)`, evaluated on 2000 points.
- Recorded v2 resampling metadata in Annihilator records: method, bins, non-empty bins, and `smoothing_lambda: "gcv_lam_none"` because SciPy did not expose a fitted lambda attribute.
- Added `--reuse-baselines-from`; it copies only SINDy/W-SINDy records, rewrites `spec` to `end2end_v2`, adds `reused_from: "end2end_v1"`, and skips duplicates by task key.
- Updated v2 sanity handling: systems 3 and 21 must pass; systems 7 and 19 are stored with numbers and `documented_exception: true`, excluded from overall pass.
- Added record-level failure handling for Annihilator full-refit resampling failures, so failed fits stay records with `refit_fail_reason`.

## Tests

Command:

```text
python -m pytest experiments/annihilator_odebench_smoke/tests -q --basetemp .pytest-tmp
```

Result:

```text
34 passed in 10.43s
```

No skips were reported.

## Sanity v2

Command:

```text
python -m experiments.annihilator_odebench_smoke.end2end --sanity --spec end2end_v2
```

Result: exit code 0. The run emitted one `RuntimeWarning` from `fhat.py:95` and repeated PySINDy `AxesWarning`s, but completed and wrote `results_e2e_v2/sanity.json`.

Overall:

- `passed`: true
- `seconds`: 443.0694841000077

Synthetic selection:

| method | validation_nrmse_x | passed |
|---|---:|---|
| annihilator | 3.7552970699009865e-06 | true |
| sindy | 1.960490741024021e-07 | true |
| wsindy | 7.368356039749292e-09 | true |

Exact derivative reference class:

| system | reference_class | validation_nrmse_x | passed | documented_exception | fail_reason | nonempty_bins | aml_iterations |
|---:|---|---:|---|---|---|---:|---:|
| 3 | [3, 0] | 1.6108850158907617e-06 | true | false | null | 200 | 33 |
| 7 | [3, 1] | Infinity | false | true | LEADING_ZERO_IN_TRAINING_DOMAIN | 136 | 115 |
| 19 | [2, 2] | Infinity | false | true | LEADING_ZERO_IN_TRAINING_DOMAIN | 200 | 49 |
| 21 | [3, 0] | 5.23360463297658e-06 | true | false | null | 200 | 34 |

Systems 3 and 21 satisfy `< 1e-4`. Systems 7 and 19 are recorded as documented exceptions and are not included in `passed`.
