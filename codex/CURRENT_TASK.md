# WP-FA3 — Side project Q3: weak-form coefficients as warm start for the trajectory fit
**Language: Python + Julia**

## Why

`docs/sideproject_residual_growth_protocol_q3.md` (frozen at `c81e7c6`) is the specification: arms W0/W1, the P-04
reference, rules R5/R6, controls. Implement it exactly; where this task and the protocol differ, the protocol wins —
report the difference. Nothing may be tuned after seeing a number.

**You cannot execute Julia in this environment** (`codex/CODEX_PROTOCOL.md`). Write the Julia part, test the Python
parts, and report `blocked` with "Julia run pending (Claude)" if everything else is done. Claude runs the Julia
script and the final aggregation.

## Deliverables

1. **Python, weak coefficients** — `analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py`. For each of the
   60 (system, IC) units of the 30 exact systems: weak least-squares coefficients on the true support, computed with
   the same design and solver as WP-FA2 (reuse `analysis/scripts/aggregate/run_sideproject_residual_growth.py` /
   `term_relevance.py` by import; do not modify them). Output
   `analysis/data/sideproject_residual_growth/q3_weak_starts.json`: per unit system_id, IC, dim, stratum, the true
   support per equation (term names and 1-based basis indices), the coefficient per (equation, term), the flat
   parameter vector **in the order `build_rhs` uses** for that `StructureSpec` (read `src/` to establish the order;
   state in the report where it is defined), trajectory SHA256 from the export, and the weak SSE per equation.
   **Run this script.**
2. **Julia, fits** — `studies/regression/sideproject_q3_weak_start.jl`. Reuse the P-04 machinery by `include`
   (`wp_n4_multistart_refit.jl`, `wp_n25_phase_c_c5_common.jl`, `run_regression.jl`), no edits to those files and
   nothing under `src/`. Per unit: build the training trajectory exactly as the P-04 runner does; W0 = simulate `p0`
   with the reference optimizer's simulation settings; W1 = one `fit_parameters` call with
   `build_reference_optimizer(max_fit_attempts = 1)` and `p0` = the weak vector; record loss, R², R² by dim,
   `fit_meta` (loss evaluations, retcodes, sentinel), coefficients. Controls from protocol §6: trajectory agreement
   with the export, and the `p0 = nothing` start-1 reproduction of P-04 on three units (one each in dim 1, 2, 3 —
   name them). CLI options: `--units <list>` for a smoke run, `--output <path>`; write JSONL append-only, one line per
   unit, so an interrupted run can resume by skipping finished units. Default output
   `outputs/sideproject_q3_weak_start/results.jsonl`.
3. **Python, aggregation** — `analysis/scripts/aggregate/aggregate_sideproject_q3.py`: reads the Julia JSONL and the
   P-04 records (`outputs/phase_c_c5_restart_curve_5dd1df8/out/**/*.jsonl`, field `oracle_starts`, best-of-k by loss
   with the same tie rule as `analysis/scripts/aggregate/` restart-curve aggregation — find and reuse it). Writes to
   `analysis/data/sideproject_residual_growth/`: `q3_units.csv` (one row per unit, W0, W1, P-04 best-of-1/3/10 per
   seed, loss-eval sums, |c| > 10 count, sentinel flag, W1-vs-P-04-best-of-10 loss comparison), `q3_rules_by_stratum.csv`
   (R5, R6 with numerator, denominator, rate, reference rate, pass/fail; `reported_only` for non-primary strata) and
   `q3_run_metadata.json` (input hashes, protocol commit `c81e7c6`). Must abort if any of the 60 units is missing.
4. Tests: `analysis/tests/test_sideproject_q3.py` — parameter-order mapping on a constructed 2-equation structure;
   weak coefficients recover known coefficients on a synthetic exact linear system; aggregation best-of-k and rule
   logic on a small fixture built from the shape of real P-04 records (derive it from one real record).

## Forbidden

- No changes to existing files; nothing under `src/`, `experiments/`, `k8s/`, `containers/`, `benchmarks/`.
- Nothing from C-6; under `outputs/` read only the WP-C4c trajectory export and the P-04 restart-curve outputs.
- No thresholds or rules beyond the protocol; no re-runs with changed settings after seeing results.
- No commit.

## Verification

- `python -m pytest analysis/tests/test_sideproject_q3.py -q`
- the weak-start builder once with defaults
- `python -m pytest analysis/tests -q` (two known pre-existing failures; do not fix)
- Give Claude the exact Julia commands: smoke (three control units), full run, and the aggregation command.

Report: `codex/reports/REPORT_WP_FA3.md`.
