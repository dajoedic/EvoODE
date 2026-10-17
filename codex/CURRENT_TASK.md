# WP-FA2 — Side project Q1/Q2: weak-space identifiability and residual guidance from C-1 starts
**Language: Python**

## Why

`docs/sideproject_residual_growth_protocol.md` (frozen at `e61f48f`) defines two questions, their metrics and the go
rules. **That document is the specification.** Implement it exactly; where this task and the protocol differ, the
protocol wins — report the difference. Nothing here may be tuned after seeing a number.

## Inputs (read-only)

- Trajectories: `outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/` via the existing loader
  `load_exported_trajectories` (hash check included). This is the **only** path under `outputs/` you may read.
- True support: `studies/regression/phase_c_support.json` (exact systems only).
- Starting structures and strata: `analysis/data/paper1_phaseC_v1/c1_structure_inventory/equations.csv` (WP-FA1),
  `kind == "pruned"` primary, `kind == "raw"` secondary.
- Reuse, by import and without modification: `analysis/exploratory/term_relevance/term_relevance.py`
  (`phasec_basis`, `evaluate_basis`, `build_design` with signal `weak`, `load_exported_trajectories`,
  `verify_basis_consistency`).

## Deliverables

1. `analysis/scripts/aggregate/run_sideproject_residual_growth.py` (CLI with `--repo-root`, `--output-dir`).
2. Outputs under `analysis/data/sideproject_residual_growth/`:
   - `q1_units.csv`: one row per (system, IC, equation): stratum, k*, number of subsets of size k*, rank of S*
     (ties against S*), SSE(S*), SSE and terms of the best subset ≠ S*, margin Q1b, ‖b‖², condition number of the
     unit-norm-scaled full weak design.
   - `q2_units.csv`: one row per unique (system, IC, equation, S0) for pruned and raw S0 (column `kind`): stratum,
     WP-FA1 class, number of C-1 cells collapsed into the unit, S0, missing and extra terms, m; for G and for OMP:
     terms added in order, Q2a, first-step rank of each missing term, set after backward elimination, Q2b; analytic
     random-addition probability; F0 set and exact flag; ρ and ρ'.
   - `rules_by_stratum.csv`: per stratum and kind: R1–R4 with numerator, denominator, value, threshold, pass/fail
     (decision only for the three primary strata; the other two rows carry `decision = "reported_only"`).
   - `by_system.csv`: the same counts per system.
   - `run_metadata.json`: input SHA256s, git HEAD, protocol commit `e61f48f`, runtime.
3. `analysis/tests/test_sideproject_residual_growth.py`.

## Implementation constraints (from the protocol, repeated because they are easy to get wrong)

- Weak design uncentred, constant as an ordinary column, least squares by an orthogonal-factorisation solver on the
  design (column scaling allowed); **no normal equations / Gram matrix** — designs reach condition numbers ~1e9.
- Q1 enumerates **all** subsets of size k* of the full basis of that dimension. Q2 candidates are all basis terms
  not in the current set. Ties in any argmax/argmin: lowest basis index; in Q1 ranking: against S*.
- m is the oracle step count |S* \ S0|; backward elimination stops at size k*. If S0 already has more than k* terms
  after G, backward elimination still runs down to k*.
- Q2c AUC: units needing addition (missing > 0) as positives, `exact` and `superset` units as negatives; ties count
  one half. Computed per stratum and kind.

## Tests (must exist and pass)

- Classifier-free synthetic case: a design built from known columns with an exact sparse target — Q1 rank 1, G finds
  the missing term, G+B returns the truth.
- G started from ∅ with m = k* gives the same set as F0 (code consistency), on real data for a handful of units.
- Q1 subset enumeration count equals the binomial coefficient; tie handling against S* demonstrated on a constructed
  tie.
- OMP and G differ on a constructed case with correlated columns (shows the projection matters).
- AUC on a tiny hand-made example, ties included.

## Hard controls (abort non-zero)

- Trajectory hashes match the manifest; basis consistency check passes for all 30 exact systems.
- 118 Q1 units; every Q2 unit's (system, IC, equation) exists in Q1; the pruned Q2 units with `exact` class have S0 =
  S* (consistency with WP-FA1).

## Runtime

Expected a few minutes on the laptop. Run the full script once. If a progress estimate exceeds 30 minutes, stop and
report `blocked` with the estimate instead of continuing.

## Forbidden

- No change to existing files (in particular not to `term_relevance.py` or WP-FA1 outputs), nothing under `src/`,
  `studies/`, `experiments/`, `k8s/`, `containers/`, `benchmarks/`.
- Nothing from C-6 or any other `outputs/` path than the trajectory export above; no reading of other result tables
  under `analysis/data/` except the WP-FA1 inventory.
- No thresholds or rules other than the protocol's; no re-running with changed settings after seeing results.
- No commit.

## Verification to run

- `python -m pytest analysis/tests/test_sideproject_residual_growth.py -q`
- the script once with defaults
- `python -m pytest analysis/tests -q` (two known pre-existing failures: the Phase-A frozen-artifact test and
  `test_t2a_candidate_priors.py::test_build_priors_from_minimal_real_shape_fixture`; do not fix them)

Report: `codex/reports/REPORT_WP_FA2.md` — what was built, controls, the rules table exactly as produced, runtime. No
interpretation of the scientific result beyond the table.
