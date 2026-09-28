# REPORT WP-T1f-d

## Status

Implemented, blocked for execution verification because Julia cannot be run in this Codex environment.

## Changes

- Added `WP_T1F_TRAJECTORY_DATA_TOLERANCE = 1e-9` in `studies/regression/wp_t1f_warm_neighbourhood.jl`, tied to the Phase-C trajectory generation tolerance documented in `run_regression.jl` and `phase_c_config.jl`.
- Split the true-parameter control measurement into:
  - `control_loss_data_tolerance`: simulated at `abstol = reltol = 1e-9`; this is the only value checked against `WP_T1F_CONTROL_LOSS_ABORT = 1e-4`.
  - `control_loss_optimizer_tolerance`: simulated with the WP-T1f optimizer tolerances; recorded as the optimizer-tolerance floor measurement and never used for aborting.
- Updated raw rows, `--control-only`, and `control_and_floor_loss_by_cell.csv` to use the two explicit control names instead of the previous ambiguous `control_loss` output column.
- Added `floor_to_control_optimizer_tolerance_ratio` to `control_and_floor_loss_by_cell.csv`.
- Updated `test/test_wp_t1f_warm_neighbourhood.jl` so a high optimizer-tolerance control value alone does not abort, and so aggregation checks both control fields and the floor/control-optimizer ratio.
- Updated `SCRIPTS.md` WP-T1f section with the control/floor separation sentence.

## Static checks

- Reviewed the modified WP-T1f control, aggregate, raw-output, and `--control-only` paths.
- Searched remaining `control_loss` occurrences. Remaining uses are the helper name, explicit compatibility fallbacks for older aggregate input, and test references; the raw output and control-only CSV columns now use `control_loss_data_tolerance` and `control_loss_optimizer_tolerance`.
- Ran `python -m pytest analysis/tests/test_wp_t1f_true_coefficients.py -q --basetemp .pytest_tmp`: 2 passed in 1.68 s.

## Commands for Claude

Run these checks:

```bash
julia --project=. test/test_wp_t1f_warm_neighbourhood.jl
python -m pytest analysis/tests/test_wp_t1f_true_coefficients.py -q
```

Run the WP-T1f script checks:

```bash
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --self-test --fresh
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --control-only --fresh
julia --project=. studies/regression/wp_t1f_warm_neighbourhood.jl --smoke --fresh
```

Expected `--control-only` result after Claude runs Julia: exit 0, `control_only.csv` has 36 rows, and all 36 `control_loss_data_tolerance` values are `<= 1e-4`. High `control_loss_optimizer_tolerance` values alone must not fail the command.

## Not run

No Julia commands were executed by Codex, per `codex/CODEX_PROTOCOL.md`.
