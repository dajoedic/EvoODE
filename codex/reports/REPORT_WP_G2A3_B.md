# WP-G2A3-b Report

## Summary

- Changed the v3 AML objective path to normalize coefficient vectors only to unit length, without canonical sign flipping.
- Kept `normalize_coeffs` for output/comparison alignment after optimization and in reporting/transfer paths.
- Added `maxls=40` to the SciPy L-BFGS-B call. The same objective and analytic gradient otherwise remain in use; this lets the K1 sign-regression seeds finish with SciPy convergence instead of `ABNORMAL_TERMINATION_IN_LNSRCH`.
- Moved aborted v3 calibration outputs from `experiments/annihilator_gate2a_v3/results/calibration/appendix_A_part_*` and `logs/` to `experiments/annihilator_gate2a_v3/results/calibration/aborted_2026-10-05_sign_bug/`.

## K1 wide 1% regression seeds

Computed with `Settings(n=2000, ell_max=3, sigma_floor_factor=1e-8, boot_reps=1)` on class `(2, 0)`.

| Seed | Angle to c* (deg) | J(c_hat) | J(c*) | Ratio | Iterations | Converged |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.0599242432386 | 0.042954224816 | 0.0432996094964 | 0.992023376551 | 12 | True |
| 10 | 0.0102346522212 | 0.0445469491396 | 0.0445953263835 | 0.998915194756 | 13 | True |
| 18 | 0.0248465757232 | 0.0507900466027 | 0.050874718904 | 0.998335670385 | 13 | True |
| 26 | 0.0210002108791 | 0.0411613806929 | 0.0417280406799 | 0.98642016309 | 11 | True |

All four satisfy angle `< 1 deg`, `J(c_hat) <= 1.01 * J(c*)`, and `converged == True`.

## Sign-normalization audit

- `_aml_objective`, `aml_cost`, `aml_projected_gradient`, and `aml_matrices` now use `_unit_coeffs`, so the optimization computes with `c = x / ||x||` and does not flip signs internally.
- `aml_candidate` still canonicalizes the start and aligns the final output to the start. This is output orientation only; the L-BFGS objective and gradient no longer call sign normalization.
- Stage K Monte Carlo uses `normalize_coeffs(evaluation.coeffs, align_to=true_coeffs)` only before accumulating/reporting coefficient means. This is comparison alignment, not an optimization step.
- `_a1_passes` normalizes the alternate eigenvector for covariance/test evaluation. The test statistic is even under `c -> -c`, so the sign convention does not bias an iteration.
- Acceptance/oracle checks use `normalize_coeffs(..., align_to=...)` only to compare equivalent coefficient directions.
- Transfer functions canonicalize transferred coefficients for deterministic output. The covariance transform is sign-invariant under the final output convention and does not feed back into AML optimization.
- v2 FNS and v1 SVD paths still use their existing `normalize_coeffs`; no AML gradient/iteration there is affected by this v3 bug.

## Commands run

```text
python -m pytest experiments/annihilator_gate2a_v3/tests -q
```

Result: `25 passed in 42.25s`.

```text
python -m pytest experiments/annihilator_gate2a_v2/tests -q
```

Result: `16 passed in 43.53s`.

```text
python -m pytest experiments/annihilator_gate2a/tests -q
```

Result: `8 passed in 3.36s`.

The combined command

```text
python -m pytest experiments/annihilator_gate2a_v3/tests experiments/annihilator_gate2a_v2/tests experiments/annihilator_gate2a/tests -q
```

was not usable because pytest imports same-basename test modules from v3 first and then reports import-file mismatches for v2/v1.

Stage K smoke:

```text
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --limit
```

Result: wrote `experiments/annihilator_gate2a_v3/results/calibration/appendix_A_limit.json`; payload had `passed: true`, `ell_max: 3`, `tau: 5.5449993463420965e-06`, `runtime_seconds: 23.600724900003115`.
