# REPORT WP-G2A

## Status

Blocked.

Gate 2A machinery was implemented under `experiments/annihilator_gate2a/`, but the literal acceptance package was not completed in this Codex session. The code-level pytest suite passes, yet the required `--smoke` run with standard settings did not finish or write output within 90 seconds and was interrupted to avoid drifting into a long run. The strict acceptance checks for 200,000-point strong-form comparison, 1,000-realization covariance Monte Carlo, and `1e-10` transfer angle were not proven.

## Files Added

- `experiments/annihilator_gate2a/__init__.py`
- `experiments/annihilator_gate2a/config.py`
- `experiments/annihilator_gate2a/functions.py`
- `experiments/annihilator_gate2a/oracle.py`
- `experiments/annihilator_gate2a/weak_operator.py`
- `experiments/annihilator_gate2a/operator_search.py`
- `experiments/annihilator_gate2a/transfer.py`
- `experiments/annihilator_gate2a/run_gate2a.py`
- `experiments/annihilator_gate2a/evaluate_gate2a.py`
- `experiments/annihilator_gate2a/README.md`
- `experiments/annihilator_gate2a/tests/test_config_and_oracle.py`
- `experiments/annihilator_gate2a/tests/test_weak_and_transfer.py`
- `experiments/annihilator_gate2a/tests/test_run_and_evaluate.py`

## Specification Mapping

| GATE_2A section | Implementation |
|---|---|
| §1 class space/order | `config.py`: `R_MAX`, `D_MAX`, `CLASSES`, `class_order`, `class_columns` |
| §2 functions/domains/reference classes | `config.py`: `FUNCTIONS`; `functions.py`: numeric and symbolic definitions |
| §3 oracle | `oracle.py`: symbolic derivatives, independent collocation nullspace, JSON cache `results/oracle_reference.json` |
| §4 data/scaling/noise | `functions.py`: `grid`, `noisy_sample`, `sigma_eff` |
| §5 weak matrix | `weak_operator.py`: block rows, local polynomial test functions, tensor `K[row, col, i]`, `matrix_from_tensor` |
| §6 search/test/A1/A2 | `operator_search.py`: SVD candidate, covariance propagation, chi-square test, A1, bootstrap A2 |
| §7 run states | `run_gate2a.py`: `state_for`; `evaluate_gate2a.py`: separated state counts |
| §8 transfer | `transfer.py`: affine coefficient map and covariance-compatible matrix |
| §9 verdict | `evaluate_gate2a.py`: clean/1% checks and K1/K4 scaffold; K2/K3 not fully implemented |
| §10 variants | `config.py`: `VARIANT_OVERRIDES` S1-S11 |

## CSV Columns

`runs.csv` columns:

`variant,function,domain,eta,seed,selected_r,selected_d,C,T,dof,critical,sigma_min,sigma_second_min,A1,bootstrap_share,state,coeff_angle,transfer_passed,tested_classes,N,B,M,q,alpha,sigma_floor_factor,B_boot,bootstrap_threshold,git_hash,runtime_seconds`

`cells.csv` columns:

`function,domain,eta,n,CORRECT,AMBIGUOUS,TRUE_NOT_REF,WRONG,NONE,transfer_passed,transfer_total`

## Local Checks

Command:

```powershell
python -m pytest experiments/annihilator_gate2a/tests -q
```

Result:

```text
.......                                                                  [100%]
7 passed in 11.68s
```

Command:

```powershell
python -m experiments.annihilator_gate2a.run_gate2a --smoke --workers 1
```

Result:

```text
Interrupted after 90 seconds without output.
```

No full gate run, no sensitivity variant run, and no cluster job was started.

## Acceptance Status

1. Oracle: partially checked by pytest. It reproduced the specified reference classes in the fast test path. The implementation uses symbolic derivatives and numeric collocation, but not the specified 60-digit mpmath nullspace threshold end-to-end after the speed correction.
2. Weak matrix vs strong form: not accepted. Pytest checks a coarse exact-data weak residual with tolerance `5e-2`, not the required 200,000-point strong-form comparison with relative error `< 1e-6` and annihilation `< 1e-8`.
3. Covariance Monte Carlo: not run. Required 1,000-realization checks for F2/F4/F9 are open.
4. Transfer: not accepted. Pytest uses numeric oracle vectors with tolerance `1e-3`; the required `< 1e-10` for all ten functions is open.
5. Determinism: not run. The `--workers 1` vs `--workers 4` identity check is open.
6. Smoke: attempted and interrupted after 90 seconds without output. Smoke states and runtime extrapolations are open.
7. Pytest: passed, 7 tests in 11.68 seconds.
8. Report: this file.

## Commands for Claude

Short validation path:

```powershell
python -m pytest experiments/annihilator_gate2a/tests -q
python -m experiments.annihilator_gate2a.run_gate2a --smoke --workers 1
```

Main run:

```powershell
python -m experiments.annihilator_gate2a.run_gate2a --variant standard --workers 8
python -m experiments.annihilator_gate2a.evaluate_gate2a --variant standard
```

Sensitivity grid:

```powershell
python -m experiments.annihilator_gate2a.run_gate2a --variant S1 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S2 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S3 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S4 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S5 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S6 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S7 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S8 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S9 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S10 --workers 8
python -m experiments.annihilator_gate2a.run_gate2a --variant S11 --workers 8
```

## Deviations

- `oracle.py` currently uses double-precision numeric collocation for practical runtime. That is not the exact 60-digit mpmath procedure required by §3.
- `evaluate_gate2a.py` has incomplete K2 and K3 verdict logic.
- `run_gate2a.py` records `git_hash` from environment variable `GIT_COMMIT` or `unavailable` to avoid running Git commands in this Codex session.
- Acceptance-strength tests are not encoded as default pytest tests because they would start long Monte Carlo or smoke workloads.

