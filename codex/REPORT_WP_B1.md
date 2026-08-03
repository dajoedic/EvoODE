# REPORT WP-B1

## Fingerprint

- New `config_fingerprint`: `fa2469a4dad1b72c`
- Differs from old WP-C1 fingerprint `df5db7763bcd2449`: `true`

## Trajectory Checks

| system | ic_set | points | t_start | t_end | first state matches dataset init | derivative_active_fractions |
|---:|---:|---:|---:|---:|---|---|
| 3 | 1 | 512 | 0.0 | 10.0 | true | `[1.0]` |
| 3 | 2 | 512 | 0.0 | 10.0 | true | `[0.875]` |
| 11 | 1 | 512 | 0.0 | 10.0 | true | `[0.08984375]` |
| 11 | 2 | 512 | 0.0 | 10.0 | true | `[0.40234375]` |
| 26 | 1 | 512 | 0.0 | 10.0 | true | `[0.07421875,0.076171875]` |
| 26 | 2 | 512 | 0.0 | 10.0 | true | `[0.17578125,0.08984375]` |
| 31 | 1 | 512 | 0.0 | 10.0 | true | `[0.302734375,0.998046875]` |
| 31 | 2 | 512 | 0.0 | 10.0 | true | `[0.052734375,0.748046875]` |
| 63 | 1 | 512 | 0.0 | 10.0 | true | `[1.0,1.0,0.984375,1.0]` |
| 63 | 2 | 512 | 0.0 | 10.0 | true | `[1.0,1.0,0.99609375,1.0]` |

All checked trajectories have 512 points, start at 0.0, end at 10.0, and their first state matches the dataset `init` entry exactly.

## Single-Cell Result

- Scratch history path: `C:\Users\joedicke\Documents\reps\EvoODE\outputs\studies\regression\wp_b1\scratch_history.jsonl`
- Variant: `evogrow_v2_2_stage_capped`
- System: `3`
- Initial-condition set: `1`
- Seed: `42`
- Loss: `5.18873247985214e-9`
- Cap: `[2]`
- `eq_overshoot`: `[0]`
- `pruned_match`: `true`
- Support: `[["u1","u1^2"]]`

## Initial-Condition Selection

System 3 gives different trajectories for `EVO_REGRESSION_IC_SET=1` and `EVO_REGRESSION_IC_SET=2`: max absolute trajectory difference `23.08705546423844`.

## IC Set Threading

- `diagnostic_systems.jl`: `REGRESSION_IC_SETS`, dataset `init_sets`, and dataset `t_grid` are loaded from `benchmarks/data/strogatz_extended.json`.
- `config_fingerprint()`: includes `initial_condition_sets`, per-system `init_sets`, and the dataset `t_grid`.
- Selection: `selected_ic_sets()` reads `EVO_REGRESSION_IC_SET`.
- Resume key: `completed_key()` and `load_completed_cells()` use `(variant, system, initial-condition set, seed)`.
- Record schema: records include `initial_condition_set`, `u0`, `tspan`, `T`, and `derivative_active_fractions`.
- Execution: `build_trajectory()` and `run_one()` both take `ic_set`; `main()` loops over IC sets and logs them.
- Verification: this script writes the smoke cell to the scratch history path, not to `studies/regression/history.jsonl`.
