# REPORT WP-G2A-c

## Status

Blocked.

The requested code and acceptance-script updates were implemented, and the full acceptance scripts
`accept_01` through `accept_06` were run. The acceptance is blocked on the substance of the method:
`accept_02_weak_strong` fails for F4 and F9, and `accept_03_covariance_mc` fails for F4 and F9.

The known F10 oracle-table mismatch is also reported by `accept_01`, but per task text it is not the
reason for the blocked status.

## Changes

- `accept_01_oracle.py`
  - Reads the existing oracle cache with `force=False`.
  - Checks metadata, all 20 reference classes, reference `n_exact = 1`, wide/narrow `n_exact` tables,
    exact symbolic verification for F1-F9, and the high-precision F10 residual check.
  - Rationalizes coefficients by ratios to the largest coefficient and uses exact rational domain
    parameters for symbolic verification.
- `accept_02_weak_strong.py`
  - Compares `A_val c` against strong-form integrals on a 200,000 point grid for F2, F4, F9.
  - Uses stable local-`u` evaluation of the test function itself.
  - Tests both oracle `c*` and a fixed seed-0 random vector in the reference class.
- `accept_03_covariance_mc.py`
  - Runs the full estimated-coefficient path for F2, F4, F9, seeds 0-999.
  - Reuses `WeightContext.with_values` so the fixed grid weights are built once per function.
  - Reports the same tests with and without the coefficient-covariance term.
  - Supports `--part F2|F4|F9`.
- `accept_05_determinism.py`
  - Compares the `run_gate2a` multiprocessing path with `--workers 1` vs `--workers 4`.
  - Uses the required tasks: F2 wide clean, F2 wide 1% seed 0, F7 narrow 1% seed 0.
- `accept_06_smoke.py`
  - Measures F2 as the early-stopping function and F10 as the late-stopping function.
  - Extrapolates the main workload and the 11-variant sensitivity grid by reference complexity for
    1 and 8 workers.
- `run_gate2a.py`, `operator_search.py`, `transfer.py`
  - Carries the selected class coefficient covariance in `Selection`.
  - Transfers covariance as `T Sigma_c T^T` and rescales it consistently after coefficient
    normalization.
- `evaluate_gate2a.py`
  - Restricts K2 to 1% cells.
- Tests
  - Added the 5% K2 regression test.
  - Changed the oracle test to read the cache instead of forcing an oracle rebuild.

## Acceptance Results

### 1. Oracle

Command:

```powershell
python -m experiments.annihilator_gate2a.acceptance.accept_01_oracle
```

Result JSON: `experiments/annihilator_gate2a/results/acceptance/accept_01_oracle.json`

- Metadata matches the required oracle metadata.
- All 20 reference classes match the specification.
- All 20 reference classes have `n_exact = 1`.
- F1-F9 symbolic verification passes exactly with residual `0` for wide and narrow domains.
- F10 high-precision residuals pass:
  - wide max relative residual: `1.147028509148724702e-58`
  - narrow max relative residual: `6.5358037367225088134e-60`
  - threshold: `1e-25`
- Wide/narrow `n_exact` table equality fails only for F10:
  - `(4,6)`: wide `10`, narrow `11`
  - `(5,6)`: wide `16`, narrow `17`
  - `(6,6)`: wide `22`, narrow `23`
- `n_exact > 0` presence is identical for F10.
- JSON `passed`: `false`, due to the known F10 table mismatch.

Runtime: `1.617171399993822` seconds.

### 2. Weak Matrix vs Strong Form

Command:

```powershell
python -m experiments.annihilator_gate2a.acceptance.accept_02_weak_strong
```

Result JSON: `experiments/annihilator_gate2a/results/acceptance/accept_02_weak_strong.json`

- F2 passes:
  - oracle weak annihilation relative: `1.709590073253837e-10`
  - random seed-0 strong relative error: `8.346570965056877e-10`
- F4 fails the oracle annihilation threshold:
  - oracle weak annihilation relative: `1.3969531743861472e-08`
  - required: `< 1e-8`
  - random seed-0 strong relative error: `9.015434937486124e-09`
- F9 fails both checks:
  - oracle weak annihilation relative: `4.411116825849872e-05`
  - required: `< 1e-8`
  - random seed-0 strong relative error: `0.00022399814238479646`
  - required: `< 1e-6`
- JSON `passed`: `false`.

Runtime: `50.4380766999966` seconds.

### 3. Covariance Monte Carlo

Command:

```powershell
python -m experiments.annihilator_gate2a.acceptance.accept_03_covariance_mc
```

Result JSON: `experiments/annihilator_gate2a/results/acceptance/accept_03_covariance_mc.json`

- F2 passes:
  - rejection rate: `0.008`
  - mean `T/dof`: `0.9995783557391357`
  - trace ratio: `0.9945046125009535`
  - without coefficient covariance: rejection rate `0.301`, mean `T/dof` `1.4283906709168317`
- F4 fails:
  - rejection rate: `1.0`
  - mean `T/dof`: `22.741218208910194`
  - trace ratio: `0.6523823890946604`
  - required: rejection in `[0, 0.03]`, mean `T/dof` in `[0.85, 1.15]`, trace ratio in `[0.8, 1.25]`
  - without coefficient covariance: rejection rate `1.0`, mean `T/dof` `523.777782227211`
- F9 fails:
  - rejection rate: `0.989`
  - mean `T/dof`: `3.235117912250076`
  - trace ratio: `218.5764969746438`
  - required: rejection in `[0, 0.03]`, mean `T/dof` in `[0.85, 1.15]`, trace ratio in `[0.8, 1.25]`
  - without coefficient covariance: rejection rate `1.0`, mean `T/dof` `8.319423493924981`
- JSON `passed`: `false`.

Runtime: `56.14171739999438` seconds.

### 4. Transfer Angle

Command:

```powershell
python -m experiments.annihilator_gate2a.acceptance.accept_04_transfer
```

Result JSON: `experiments/annihilator_gate2a/results/acceptance/accept_04_transfer.json`

- F1-F10 all have matching transferred classes.
- F1-F10 all have transfer angle `0.0`.
- F1-F10 all pass.

Runtime: `0.0328610000142362` seconds.

### 5. Determinism

Command:

```powershell
python -m experiments.annihilator_gate2a.acceptance.accept_05_determinism
```

Result JSON: `experiments/annihilator_gate2a/results/acceptance/accept_05_determinism.json`

- Workers compared: `1` and `4`.
- Rows compared: `3`.
- Results are bit-identical after excluding `runtime_seconds`: `true`.
- The three task outcomes are:
  - F2 wide clean: `AMBIGUOUS`, selected `(2,1)`
  - F2 wide 1% seed 0: `CORRECT`, selected `(1,0)`
  - F7 narrow 1% seed 0: `WRONG`, selected `(1,1)`, transfer `false`

Runtime: `135.92254010000033` seconds.

### 6. Smoke Timing

Command:

```powershell
python -m experiments.annihilator_gate2a.acceptance.accept_06_smoke
```

Result JSON: `experiments/annihilator_gate2a/results/acceptance/accept_06_smoke.json`

- Measured early function F2 row runtime: `2.3133532000065316` seconds.
- Measured late function F10 row runtime: `79.54984610000974` seconds.
- Main workload estimate:
  - rows: `820`
  - workers 1: `23430.48384452625` seconds
  - workers 8: `2928.8104805657813` seconds
- Sensitivity grid estimate:
  - variants: `11`
  - rows per variant: `420`
  - workers 1: `132010.7748313552` seconds
  - workers 8: `16501.3468539194` seconds

Runtime: `81.86323000001721` seconds.

## Test Results

Command:

```powershell
python -m py_compile @(rg --files experiments/annihilator_gate2a | Where-Object { $_ -like '*.py' })
```

Result: passed.

Command:

```powershell
python -m pytest experiments/annihilator_gate2a/tests -q
```

Result:

```text
........                                                                 [100%]
8 passed in 2.77s
```

An earlier full pytest attempt was interrupted after about 8 minutes because
`test_oracle_reference_classes` forced a full oracle rebuild. That test now uses `build_reference(force=False)`,
matching this task's cache-read requirement.

## Blocker

The blocker is substantive, not environmental: the full acceptance checks execute, but F4 and F9 fail the
specified weak-vs-strong and covariance Monte Carlo thresholds. The fixed tolerances were not changed.
