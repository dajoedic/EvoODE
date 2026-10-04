# REPORT WP-G2A3-a

## Scope

Implemented Gate 2A v3 under `experiments/annihilator_gate2a_v3/` as a copy of v2 without inherited result files. v1 and v2 code paths were left unchanged.

## Implementation

- Replaced the FNS candidate step with AML (L-BFGS) in `operator_search.py`.
  - Objective: `J(x / ||x||)`.
  - Start: SVD candidate.
  - SciPy method: `L-BFGS-B`, no bounds.
  - Options: `gtol=1e-12`, `ftol=1e-15`, `maxiter=2000`.
  - Gradient: `2 X(c)c`, projected to the tangent space and divided by `||x||`.
  - Non-convergence is retained in per-run output via `aml_converged`, `aml_iterations`, and `aml_message`; the result is still used.
  - Output estimator name: `AML (L-BFGS)`.
- Updated v3 run CSV fields from FNS names to AML names.
- Updated v3 oracle handling.
  - The v2 nullspace cache is promoted into `results/oracle_reference_v3.json`.
  - Metadata records `source_cache=experiments/annihilator_gate2a_v2/results/oracle_reference_v2.json`.
  - Narrow-domain `n_exact` uses the wide-domain table.
  - Direct narrow `n_exact` is retained as `diagnostic_direct_n_exact`.
  - Narrow reference coefficients are transformed from the wide reference by solving the existing narrow-to-wide transfer matrix.
  - Direct narrow reference-class agreement is checked.
  - Symbolic verification rationalizes domain scales and projective coefficient ratios.
- Updated Stage K partitioning.
  - K-c Clean cells are distributed by `cell_index % part_count`.
  - Merge requires each clean cell exactly once.
  - Each part prints timestamped progress at K-c start and after each clean cell.
  - `--limit` now respects `--n`; it still caps reps to 2 and disables statistical MC gating while retaining the reported MC numbers.

## AML K1 check

Command:

```text
python -c "<K1 wide 1% seed 0 AML diagnostic>"
```

Numbers for K1 wide, eta=0.01, seed=0, N=2000, class (2,0):

| quantity | value |
|---|---:|
| `J(SVD start)` | 16.366220452812094 |
| `J(AML)` | 0.04876889893227632 |
| projected gradient norm | 5.09758616956135e-06 |
| angle to `c*` | 0.26969307351067323 deg |
| iterations | 11 |
| converged | True |

## Oracle verification

Command:

```text
python -m experiments.annihilator_gate2a_v3.acceptance.accept_01_oracle --workers 1
```

Result file: `experiments/annihilator_gate2a_v3/results/acceptance/accept_01_oracle.json`

| quantity | value |
|---|---:|
| passed | True |
| runtime_seconds | 1.0741797999980918 |
| metadata_ok | True |
| direct_narrow_references_match | True |
| reference verifications passed | 36 |

Direct narrow `n_exact` diagnostic differences:

| function | differing classes |
|---|---:|
| K7 | 3 |
| K8 | 4 |

These are diagnostic only in v3; the wide `n_exact` table is decisive for both domains.

## Stage K smoke

Command:

```text
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --limit --n 2000 --reps 1000
```

Result file: `experiments/annihilator_gate2a_v3/results/calibration/appendix_A_limit.json`

| quantity | value |
|---|---:|
| passed | True |
| ell_max | 3 |
| tau | 1.0161964895394882e-10 |
| runtime_seconds | 41.65392880000218 |
| limit_mc_gate_disabled | True |
| K-c points 1-3 | True |
| K-c point 4 | True |

Clean cells in the limit smoke:

| cell | state | passed |
|---|---|---:|
| K1_wide | CORRECT | True |
| K1_narrow | CORRECT | True |

The limit MC record used 2 seeds and is retained in JSON for diagnostics only.

## Tests

Commands run:

```text
python -m pytest experiments/annihilator_gate2a_v3/tests -q
python -m pytest experiments/annihilator_gate2a_v2/tests -q
python -m pytest experiments/annihilator_gate2a/tests -q
```

Results:

| suite | result |
|---|---|
| v3 | 19 passed in 38.57s |
| v2 | 16 passed in 48.90s |
| v1 | 8 passed in 3.57s |

## Full Stage K commands for Claude

Do not run full Stage K inside Codex. Exact commands for 8 parts with `--n 2000 --reps 1000`:

```text
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 0/8
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 1/8
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 2/8
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 3/8
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 4/8
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 5/8
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 6/8
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --part 7/8
python -m experiments.annihilator_gate2a_v3.acceptance.stage_k_calibration --n 2000 --reps 1000 --merge-parts 8
```

## Notes

- Full Stage K was not run, per task prohibition.
- Full F1-F10 gate runs were not run.
- `experiments/annihilator_gate2a_v3/results/` contains only v3 outputs generated during this task: oracle acceptance/cache and Stage-K limit smoke files.
