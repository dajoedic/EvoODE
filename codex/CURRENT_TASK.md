# WP-N44b — restart curve aggregator: zero-parameter oracle structures
**Language: Python**

## Why

The real P-04 output (`outputs/phase_c_c5_restart_curve_5dd1df8/out/`, 180 cells) stops the WP-N44 aggregator with
`sys0011_seed123_ic1: missing oracle fit_meta.loss_evals`. Cause (checked by Claude): on all six system-11 cells the
found ∩ true oracle structure is **empty** (`oracle_structure == [[]]`), so it has zero parameters, and
`_fit_fixed_structure_once` in `studies/regression/wp_n4_multistart_refit.jl` skips the fit (`n_params == 0`) and
writes `fit_meta = null` and `optimizer_loss = null`, while `loss` and `r2` are still computed from the zero model. This
is legitimate data, not a defect of the run.

## Deliverables

1. In `analysis/scripts/aggregate/aggregate_phasec_restart_curve.py`: a start whose `fit_meta` is null is accepted
   **only** if the corresponding structure has zero active terms in every equation; it then counts **0 loss
   evaluations**. Its `loss` and `r2` are used as recorded. Any other null `fit_meta` stays a hard error, as now.
2. Report the number of such zero-parameter structures (per structure type, per stratum) in the output, e.g. a column
   or a small table, so that the reader sees that six oracle cells carry no fit at all.
3. Test with a synthetic zero-parameter oracle structure (accepted, 0 evals) and a synthetic non-empty structure with
   null `fit_meta` (still an error).
4. Report `codex/reports/REPORT_WP_N44B.md`.

## Verboten

- Changing anything else in the aggregator's metrics, strata, thresholds or the control.
- Running the aggregator on the real P-04 data (Claude does it). Running Julia. Committing. Editing this file.

## Abnahme

- `python -m pytest analysis/tests/test_aggregate_phasec_restart_curve.py -q` passes (workspace `--basetemp` if
  needed).
- `STATUS.md` set to `done` with WP-N44b, or `blocked` with the reason.
