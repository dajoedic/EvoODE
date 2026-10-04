# REPORT WP-G2A2-a

## Summary

Implemented the Gate 2A v2 Python scaffold for the Oracle -> Stage K -> Appendix A slice under
`experiments/annihilator_gate2a_v2/`.

Status is `blocked`, not `done`: the official 100-digit oracle and full Stage K calibration were not completed in
this Codex session. The required official `results/calibration/appendix_A.json` is intentionally absent. A limit-mode
smoke wrote `results/calibration/appendix_A_limit.json` only.

## Implemented

- Added K7 and K8 to the frozen v2 configuration and to numeric/SymPy function evaluation.
- Added z-coordinate reference coefficients for K1-K8 for Stage K calibration.
- Added FNS/AML run fields for A3/projective uncertainty, FNS iteration count, and convergence.
- Added `run_gate2a.py` for v2 smoke/run infrastructure, reading `ell_max` and `tau` from Appendix A for non-calibration runs.
- Reworked `acceptance/accept_01_oracle.py` as a v2 entry point with metadata and v1-cache comparison logic.
- Added `acceptance/stage_k_calibration.py` with K-a/K-b/K-c structure, `--limit`, `--reps`, and `--part`.
- Added finite-difference unit coverage for `nabla J = 2 X(c)c`.
- Corrected v2 unit tests so they import v2 modules rather than v1 modules.

## Executed Commands

```text
$env:PYTHONPATH='.'; pytest experiments/annihilator_gate2a_v2/tests -q
```

Result: `8 passed in 6.06s`.

```text
$env:PYTHONPATH='.'; pytest experiments/annihilator_gate2a/tests -q
```

Result: `8 passed in 3.03s`.

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.accept_01_oracle --limit
```

Result file: `experiments/annihilator_gate2a_v2/results/acceptance/accept_01_oracle.json`.

Result payload: `passed=true`, limit entry point only. It does not build the full 100-digit oracle cache.

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --limit
```

Result file: `experiments/annihilator_gate2a_v2/results/calibration/appendix_A_limit.json`.

Limit settings: `n=120`, `reps=2`.

Limit K-a smoke result: failed, maximum scaled error `0.163894301315622` on the reduced smoke grid. This is not an
official K-a result because the full command requires `n=2000` and all K1-K8 cells at ell 3-5.

## Commands Still Required

Full oracle:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.accept_01_oracle
```

Full Stage K as one command, if runtime permits:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 2000 --reps 1000
```

Partitioned Stage K, if the full command exceeds the runtime budget:

```text
$env:PYTHONPATH='.'; python -m experiments.annihilator_gate2a_v2.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 0/8
```

Repeat with `--part 1/8` through `--part 7/8`.

## Spec Deviations / Open Points

- `stage_k_calibration.py` currently uses the specified analytic K reference operators in z-coordinates for K-a/K-b
  instead of independently recomputing every K reference via the high-precision oracle.
- K-a compares the trapezoidal weak residual against the exact zero residual implied by the specified operator. The
  spec asks for mpmath 30-digit high-precision integrals row by row.
- The full official oracle JSON `results/oracle_reference_v2.json` was not produced.
- The official Appendix A files `results/calibration/appendix_A.json` and `appendix_A.md` were not produced.
- Stale v1-derived acceptance scripts `accept_02` through `accept_06` remain present and are not part of this
  work package. They should not be used for the Oracle -> Stage K acceptance.

## Files Written By Smoke Runs

- `experiments/annihilator_gate2a_v2/results/acceptance/accept_01_oracle.json`
- `experiments/annihilator_gate2a_v2/results/calibration/appendix_A_limit.json`
- `experiments/annihilator_gate2a_v2/results/calibration/appendix_A_limit.md`
