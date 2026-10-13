# WP-N44b Report

## Built

- Updated `analysis/scripts/aggregate/aggregate_phasec_restart_curve.py`.
  - `fit_meta = null` is accepted only when the corresponding structure has zero active terms in every equation.
  - Accepted zero-parameter fitless starts contribute `0` loss evaluations.
  - Non-empty structures with null or missing `fit_meta.loss_evals` still raise `AggregationError`.
  - `restart_curve.csv` now includes `zero_parameter_fitless_cells` per `k`, `structure`, and `stratum`.
- Updated `analysis/tests/test_aggregate_phasec_restart_curve.py`.
  - Added a synthetic zero-parameter oracle case with `oracle_structure == [[]]`, null per-start `fit_meta`, `0` summed loss evaluations, and one counted fitless cell.
  - Added a synthetic non-empty oracle case with null per-start `fit_meta` that still errors.

## Checks

- `python -m pytest analysis/tests/test_aggregate_phasec_restart_curve.py -q --basetemp tmp/pytest_wp_n44b`: 5 passed.
- `python -m py_compile analysis/scripts/aggregate/aggregate_phasec_restart_curve.py analysis/tests/test_aggregate_phasec_restart_curve.py`: passed.

## Notes

- The real P-04 restart output was not aggregated, per task restriction.
- Julia was not run.
