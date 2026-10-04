# WP-G2A2-c Report

## Changes

- Added explicit SymPy lambdify mappings for `airyai`, `airyaiprime`, and `besselj` in `experiments/annihilator_gate2a_v2/oracle.py`.
- Added SciPy-side derivative lambdify support for the same functions.
- Verified K3/K4 derivatives through order 6 against high-precision mpmath differentiation at 3 z-points per domain.
- Changed K3/K4 reference verification to use the exact defining ODE in z-coordinates for `definition_ode_numeric`, avoiding float SVD coefficient residuals against the `1e-45` verification threshold.
- Added worker-cache resume for `accept_01_oracle --workers N`: a worker cache is reused only when metadata, class list, domain set, and exact function list match.
- Changed Stage K part runs so K-c clean search runs only in part `0/N`.
- Changed Stage K merge to require:
  - part 0 contains clean results,
  - nonzero parts contain no clean results,
  - K-a, K-b, `ell_max`, `tau`, and ex-ante classes match across all parts.

Worker helper cache files are intentionally retained after merge. They are expected at:

- `experiments/annihilator_gate2a_v2/results/acceptance/accept_01_oracle_worker_*.cache.json`

## Commands Run

```text
python -m pytest experiments/annihilator_gate2a_v2/tests/test_config_and_oracle.py experiments/annihilator_gate2a_v2/tests/test_stage_k_and_caching.py
```

Result: 9 passed in 5.66s on the final run.

```text
python -m pytest experiments/annihilator_gate2a_v2/tests
```

Result: 16 passed in 41.14s on the final run.

```text
python -m pytest experiments/annihilator_gate2a/tests
```

Result: 8 passed in 2.65s on the final run.

```text
python -m experiments.annihilator_gate2a_v2.acceptance.accept_01_oracle --part 12/18
```

Result: K3-only oracle smoke completed in 144.02837949999957s.

Smoke output files:

- `experiments/annihilator_gate2a_v2/results/acceptance/accept_01_oracle_part_12_of_18.json`
- `experiments/annihilator_gate2a_v2/results/acceptance/accept_01_oracle_part_12_of_18.summary.json`

## K3 Smoke Numbers

Metadata:

- `precision_digits`: 100
- `points`: 220
- `relative_threshold`: 1e-60

K3 wide:

- `reference_class`: [2, 1]
- `expected_reference_class`: [2, 1]
- `reference_class_ok`: true
- `reference_n_exact`: 1
- `reference_n_exact_one`: true
- `verification.mode`: `definition_ode_numeric`
- `verification.max_abs_on_sample`: 0.0
- `verification.passed`: true

K3 narrow:

- `reference_class`: [2, 1]
- `expected_reference_class`: [2, 1]
- `reference_class_ok`: true
- `reference_n_exact`: 1
- `reference_n_exact_one`: true
- `verification.mode`: `definition_ode_numeric`
- `verification.max_abs_on_sample`: 0.0
- `verification.passed`: true

Other smoke checks:

- `metadata_ok`: true
- `wide_narrow_n_exact_passed`: true
- `passed`: true

## Exact Commands For Claude

Resume/build the full oracle with worker-cache reuse:

```text
python -m experiments.annihilator_gate2a_v2.acceptance.accept_01_oracle --workers 8
```

Run Stage K in 8 parts:

```text
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --part 0/8
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --part 1/8
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --part 2/8
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --part 3/8
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --part 4/8
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --part 5/8
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --part 6/8
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --part 7/8
```

Merge Stage K parts:

```text
python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 400 --reps 1000 --merge-parts 8
```

## Notes

- No full oracle run over F1-F10 was started.
- No Stage K full part run or merge was started.
- Existing worker cache files were not deleted.
