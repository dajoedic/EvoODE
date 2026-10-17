# WP-FA1 — Inventory of C-1 final structures against the true support (exact systems)
**Language: Python**

## Why

Failure anatomy / side project "residual-guided growth" (`DIARY.md` 2026-10-17). Before any residual-guided growth
operator is studied, we need to know which kind of wrong structures EvoGrow produces: does a true term only need to be
added, does a false term only need to be removed, or both? Claude computed this inline and untracked; this work
package makes it a tracked, tested, reproducible aggregation. **No new runs, no Julia, no change to any frozen
artifact.**

## Inputs (read-only)

- `analysis/data/paper1_phaseC_v1/final_2026-10-05/phasec_analysis_registry_c1.csv` (378 rows, C-1 capped arm).
  Columns used: `run_id`, `system_id`, `system_dim`, `seed`, `initial_condition_set`, `r2`, `support_terms` (raw),
  `pruned_support_terms` (pruned), `exact_support_match_raw`, `exact_support_match_pruned`. The two support columns
  are JSON strings: one list of term names per equation.
- `studies/regression/phase_c_support.json`: true support per system (`systems[*].support_terms`, one list per
  equation); use only entries with `representability == "exact"` (30 systems).

## Definitions (fixed — do not alter)

For a true term set T and a found term set F: `missing = |T \ F|`, `extra = |F \ T|`, `tp = |T ∩ F|`. Class, checked
in this order:

1. `exact`: missing = 0 and extra = 0
2. `disjoint`: tp = 0
3. `subset`: extra = 0
4. `superset`: missing = 0
5. `mixed`: otherwise

Derived two-axis view: `needs_add = missing > 0`, `needs_remove = extra > 0`.

Apply the classification at **two levels**, each for both `raw` and `pruned`:

- **equation level**: T and F are the term sets of one equation;
- **cell level**: T and F are sets of (equation index, term) pairs over all equations of the cell.

**Strata** (a column `stratum`, used in every output): `dim1`, `dim2`, `dim3_feasible` (systems 52, 61),
`dim3_bound_infeasible` (systems 54, 55, 56, 57, 58, 59), `dim4` (system 63). The two dim-3 lists come from the
2026-10-01 decision in `CLAUDE.md` ("Known Gaps", first item: feasible under the bound vs not); if a tracked file in
`analysis/data/` already carries this label, read it from there, otherwise define the list once as a named constant
with a comment citing that decision.

## Deliverables

1. `analysis/scripts/aggregate/aggregate_c1_structure_inventory.py` (CLI, `--repo-root`, `--output-dir`, defaults
   as below). Follow `analysis/CONVENTIONS.md`.
2. Outputs under `analysis/data/paper1_phaseC_v1/c1_structure_inventory/`:
   - `equations.csv`: one row per cell × equation × kind (`raw`/`pruned`): ids, dim, stratum, seed, IC, eq index,
     class, n_true, missing, extra, needs_add, needs_remove, missing_terms, extra_terms (as JSON lists), cell r2.
   - `cells.csv`: one row per cell: ids, dim, stratum, seed, IC, r2, and for raw and pruned: class, missing, extra.
   - `summary_equations_by_stratum.csv`: counts of class × stratum × kind, plus counts of
     (needs_add, needs_remove) × stratum × kind.
   - `summary_cells_by_stratum.csv`: counts of class × stratum × kind.
   - `summary_by_system.csv`: counts of class per system × kind (cell level and equation level).
   - `transition_raw_to_pruned_cells.csv`: crosstab raw class → pruned class over cells.
   - `r2_by_class_cells.csv`: per pruned cell class, number of cells with r2 > 0.9 and total.
   - `run_metadata.json`: input paths with SHA256, row counts, git hash, the class definition text.
3. `analysis/tests/test_c1_structure_inventory.py`: unit tests of the classifier on hand-built cases covering all
   five classes and the order of checks (e.g. T = {x}, F = {y} must be `disjoint`, not `mixed`); a test that the
   cell-level pairs keep equation identity (the same term name in two equations is two distinct pairs).

## Hard controls (the script must abort with a non-zero exit if any fails)

- exactly 180 C-1 rows on exact systems; equation count per cell equals the true equation count;
- cell-level `exact` (raw) ⇔ `exact_support_match_raw`, and cell-level `exact` (pruned) ⇔
  `exact_support_match_pruned`, in 180 of 180 rows.

## Acceptance — must reproduce Claude's inline numbers exactly

Equation level, pruned, (needs_add, needs_remove) counts per stratum
`exact (F,F) / remove-only (F,T) / add-only (T,F) / both (T,T)`:

| stratum | F,F | F,T | T,F | T,T | Σ |
|---|---|---|---|---|---|
| dim1 | 31 | 10 | 9 | 16 | 66 |
| dim2 | 49 | 37 | 2 | 32 | 120 |
| dim3_feasible | 0 | 1 | 1 | 34 | 36 |
| dim3_bound_infeasible | 9 | 38 | 5 | 56 | 108 |
| dim4 | 4 | 0 | 5 | 15 | 24 |

Equation level, raw, same layout: dim1 21/24/6/15, dim2 19/67/2/32, dim3_feasible 0/1/1/34,
dim3_bound_infeasible 8/39/4/57, dim4 4/0/5/15.

Cell level, pruned, all strata together: exact 53, subset 10, superset 22, mixed 89, disjoint 6. Raw: exact 24,
subset 7, superset 55, mixed 88, disjoint 6. Raw superset → pruned exact: 29 cells.

If a number differs, do not adjust anything to match — report the difference in `STATUS.md` as `blocked` with the
diverging rows.

## Forbidden

- No changes under `src/`, `studies/`, `experiments/`, `k8s/`, `containers/`, `benchmarks/`, or to any existing file
  under `analysis/data/`.
- No new metric, no threshold, no re-pruning: raw and pruned come from the registry as they are.
- No reading of anything under `outputs/` and nothing from C-6 (blind rule).
- No commit.

## Verification to run

- `python -m pytest analysis/tests/test_c1_structure_inventory.py -q`
- the script once with defaults
- `python -m pytest analysis/tests -q` (report any pre-existing failures separately; do not fix them)

Report: `codex/reports/REPORT_WP_FA1.md` (what was built, the acceptance tables as produced, test results).
