# REPORT WP-N38

## Change

Implemented shared Sympy expansion for symbolic baseline expressions in `baselines/harness.py`:

- `symbolic_active_terms_by_equation` expands ODEFormer/PySR expressions and maps supported terms to the Phase-C support vocabulary (`1`, `u1`, `u1^2`, `u1*u2`, `sin(u1)`, `cos(u1)`, ...).
- Raw terms use nonzero expanded coefficients.
- Pruned terms use the existing Phase-C rule `max(1e-6, 1e-3 * max_abs)` per equation, matching `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py::serialize_coefficients`.
- Terms outside the Phase-C basis are recorded in `odeformer_outside_basis_terms` and counted in `odeformer_outside_basis_term_count`; any outside-basis term prevents a structure hit.
- PySR now uses the same expansion path for raw/pruned active terms.

`baselines/run_odeformer_noise.py` now has `--recompute-structure-fields`, which reads existing `records.jsonl` and rewrites:

```text
outputs/wp_n38_noise_odeformer/stages/records.jsonl
outputs/wp_n38_noise_odeformer/stages/details.csv
outputs/wp_n38_noise_odeformer/stages/summary.csv
outputs/wp_n38_noise_odeformer/stages/comparison_with_robustness_stage_report.csv
outputs/wp_n38_noise_odeformer/stages/structure_hits_by_condition.csv
```

No ODEFormer run was started.

## WP-N31 dependency

WP-N31 did not compute ODEFormer support from expressions. The code path is
`analysis/scripts/aggregate/run_phasec_sindy_baseline.py::build_odeformer_pair_rows`, which reads
`structure_hit_raw` and `structure_hit_pruned` directly from the ODEFormer records and reports their
mean rates. Therefore the WP-N31 ODEFormer structure-hit rates depend on the same record fields
recomputed here.

## Recomputed structure counts

Input rows: 240. Empty `active_terms_raw` after recompute: 0. Raw hits: 48. Pruned hits: 48.
Outside-basis term count total: 348.

Full per-system/per-condition/per-config table is in:

```text
outputs/wp_n38_noise_odeformer/stages/structure_hits_by_condition.csv
```

Aggregate over the 16 condition/config groups per system:

| system_id | groups | n records | raw hits | pruned hits | outside terms |
|---:|---:|---:|---:|---:|---:|
| 1 | 16 | 48 | 48 | 48 | 0 |
| 17 | 16 | 48 | 0 | 0 | 0 |
| 18 | 16 | 48 | 0 | 0 | 0 |
| 24 | 16 | 48 | 0 | 0 | 180 |
| 41 | 16 | 48 | 0 | 0 | 168 |

Each row in `structure_hits_by_condition.csv` is grouped by:

```text
system_id, noise_sigma, subsample_rho, noise_realization, odeformer_config_id
```

and contains `n`, `raw_hits`, `pruned_hits`, and `outside_terms`. Every group has `n = 3`.

System 17 note: the expression `x_0*(0.3965 - 0.0041*x_0)` expands to `["u1","u1^2"]`, but
`phase_c_support.json` gives true terms `["1","u1","u1^2"]` for system 17
(`0.4*x_0*(1 - 0.01*x_0) - 0.3`). Because the task also says true terms come from
`phase_c_support.json`, the recomputed exact hit is `False`.

System 24 note: rational expressions such as
`(-7.6414272*x_0**2 + 2.0244288*x_0 - 0.0284)/(4.103*x_0 - 1.087)` are counted outside the basis
and do not crash.

## Commands

```text
python -m baselines.run_odeformer_noise --output-dir outputs/wp_n38_noise_odeformer/stages --recompute-structure-fields
```

The direct script form is not valid on this Windows setup because it does not put the repository
root on `sys.path`:

```text
python baselines/run_odeformer_noise.py --output-dir outputs/wp_n38_noise_odeformer/stages --recompute-structure-fields
```

failed with `ModuleNotFoundError: No module named 'baselines'`.

## Tests

```text
python -m py_compile baselines/harness.py baselines/run_odeformer_noise.py
```

```text
python -m pytest baselines/tests/test_run_odeformer_noise.py --basetemp .pytest_tmp
9 passed in 6.07s
```

```text
python -m pytest baselines/tests/test_harness.py --basetemp .pytest_tmp
45 passed, 5 skipped in 18.08s
```
