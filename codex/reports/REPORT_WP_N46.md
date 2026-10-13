# REPORT WP-N46

## Implementation

- Added `simulate_model_accurate` in `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py`.
  - Solver: `scipy.integrate.solve_ivp(method="DOP853", rtol=1e-9, atol=1e-9, t_eval=t_grid)`.
  - Divergence limit: `max|y| > 1e9`.
  - RHS budget: `1,200,000` evaluations, reported as `max_evals`.
  - RHS is compiled once per model from feature names and the full coefficient matrix.
- Kept historical `simulate_model` unchanged.
- Added `--integrator {dop853,euler}` to:
  - `analysis/scripts/aggregate/run_phasec_sindy_baseline.py`
  - `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`
  - Default: `dop853`.
- Added details columns:
  - `integrator`
  - `sindy_coefficients_full`
- Noise runner now appends `details.csv` per finished cell, skips already complete cells on restart, and writes `metadata.json`.
- Added `library_true_terms` for Phase C SINDy-family truth terms. It maps polynomial terms as before and maps linear `sin(x_i)` / `cos(x_i)` terms to SINDy library names such as `sin(1*x0)`.
- `aggregate_phasec_hierarchy_n43.py` now accepts SINDy-family merged inputs containing `sindy`, `weak_sindy`, and `e_sindy`, and writes `hierarchy_n45_old_vs_new_deltas.csv`.
- `SCRIPTS.md` now contains the N46 clean rerun, C-4c rerun, hierarchy_n46, and full noisy-grid rerun commands.

## Changed Truth

Changed systems from `polynomial_true_terms` to `library_true_terms`:

| system_id | old behavior | new behavior |
|---:|---|---|
| 23 | non-polynomial equation scored as empty truth | `[{1, sin(1*x0)}]` |
| 28 | equation 2 scored as empty truth | `[{x1}, {sin(1*x0)}]` |
| 33 | equation 1 now maps its linear sine term; equation 2 remains unsupported because of `cos(x1)/x0` | changed, but not fully exact |
| 43 | equation 2 scored as empty truth | `[{x1}, {1, x1, sin(1*x0)}]` |

Every changed equation contains a linear `sin`/`cos` of one state. Polynomial-only systems are unchanged.

EvoGrow structure uses the stored Phase C support/registry path, not `polynomial_true_terms`, so I did not change it. ODEFormer structure is recomputed through `baselines/harness.py:support_true_terms_from_system`, which uses `symbolic_active_terms_by_equation`; I did not find the same `sp.Poly` empty-truth defect there.

## Smoke

Smoke slice:

- Systems: 23, 24, 43, and 31.
- Reason for 31: old C-6 outputs contain clean divergence/max failure rows for system 31.
- Conditions: `noise_sigma = 0`, `subsample_rho = 0`, `noise_realization = 1`.
- Methods: `sindy`, `weak_sindy`, `e_sindy`.
- Configurations: `poly_deg3_stlsq_0.01`, `poly_deg3_sin_cos_stlsq_0.01`.
- Rows: 48 model rows.

Outputs:

- `outputs/wp_n46_smoke/euler_fresh/details.csv`
- `outputs/wp_n46_smoke/dop853_fresh/details.csv`
- `outputs/wp_n46_smoke/smoke_euler_vs_dop853.csv`

Smoke summary:

| method | library_id | n | Euler rec >0.9 | DOP853 rec >0.9 | Euler gen >0.9 | DOP853 gen >0.9 |
|---|---|---:|---:|---:|---:|---:|
| e_sindy | poly_deg3_sin_cos_stlsq_0.01 | 8 | 6 | 6 | 5 | 5 |
| e_sindy | poly_deg3_stlsq_0.01 | 8 | 3 | 3 | 1 | 2 |
| sindy | poly_deg3_sin_cos_stlsq_0.01 | 8 | 5 | 5 | 5 | 5 |
| sindy | poly_deg3_stlsq_0.01 | 8 | 4 | 4 | 1 | 2 |
| weak_sindy | poly_deg3_sin_cos_stlsq_0.01 | 8 | 8 | 8 | 7 | 7 |
| weak_sindy | poly_deg3_stlsq_0.01 | 8 | 7 | 7 | 6 | 6 |

Euler compatibility on the same slice against old C-6 outputs:

- Matched old rows: 48/48.
- `fit_status`, reconstruction/generalization integration statuses, `active_terms_raw`, and `active_terms_pruned`: 48/48 exact string matches.
- R2 values match numerically except for diverged or last-digit float serialization cases. Counts with absolute delta `<= 1e-12`:
  - reconstruction arithmetic: 47/48
  - reconstruction variance-weighted: 47/48
  - generalization arithmetic: 48/48
  - generalization variance-weighted: 46/48

## ODEFormer Integrator Finding

The local harness does not call `solve_ivp` for ODEFormer directly. `baselines/harness.py` delegates ODEFormer trajectories to:

```text
ODEFormerAdapter.integrate_expression -> self.model.integrate_prediction(...)
```

`baselines/run_odeformer_grid.py` enforces faithful mode by rejecting `timeout_seconds_per_cell` and ODEFormer config `integration_timeout_seconds`; the current ODEFormer records have `timeout_seconds_per_cell = null`. The harness passes no `rtol`/`atol` arguments for ODEFormer. The exact internal solver/tolerances of `integrate_prediction` are not recorded in the output artifacts and are not visible in the vendored repo code.

## Cost Estimate

The DOP853 smoke ran 48 model rows in about 7 seconds on this machine. Full noisy grid size:

```text
4536 cells * 10 configs * 3 methods = 136080 model rows
```

Linear estimate from the smoke rate:

```text
136080 / 48 * 7 s = 19845 s = 5.5 h
```

This is a local linear estimate before cluster parallelism and filesystem overhead.

## Validation

Passed:

```text
python -m py_compile analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py analysis/scripts/aggregate/run_phasec_sindy_baseline.py analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py
python -m pytest --basetemp outputs/pytest_tmp analysis/tests/test_phasec_sindy_baseline.py analysis/tests/test_phasec_noise_sindy_baselines.py analysis/tests/test_aggregate_phasec_hierarchy_n43.py
```

Result: 41 passed, 14 warnings.

Full analysis suite:

```text
python -m pytest --basetemp outputs/pytest_tmp analysis/tests
```

Result: 143 passed, 1 failed, 222566 warnings. The failure is `analysis/tests/test_evaluate_hypotheses_dataset_classification.py::test_phase_a_evaluation_does_not_overwrite_frozen_artifacts`; it is in the Phase A hypothesis evaluation path, not in the SINDy/Phase C files touched here.

