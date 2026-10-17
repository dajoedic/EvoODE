# WP-FA4 — Side project Q4: growth path, trajectory check, model size without oracle
**Language: Python + Julia**

## Why

`docs/sideproject_residual_growth_protocol_q4.md` (frozen at `24ede2d`) is the specification: growth path with FoBa
backward check, one weak-start fit per candidate, size rules (c) primary / (a) / (b), metrics, references, rules
R7–R9, controls. Implement it exactly; where this task and the protocol differ, the protocol wins — report the
difference. Nothing may be tuned after seeing a number.

**You cannot execute Julia.** Write the Julia part, test the Python parts, report `blocked` with "Julia run pending
(Claude)" when the rest is done. Claude runs Julia and the final aggregation.

**Lessons from WP-FA3, binding here:**
- No session timer, deadline or time-based exit in any script you write. The 15-minute rule in
  `CODEX_PROTOCOL.md` limits your own session only. (`CLAUDE.md`: no hard time cuts in runs.)
- The Julia file has never been parsed by you: avoid reserved words as identifiers (`export`, `import`, `module`,
  `type`, `end`, `local`, `global`, `public`, `outer`, …) and Python syntax. Claude will run `Meta.parseall` first.

## Deliverables

1. **Python, path builder** — `analysis/scripts/aggregate/build_sideproject_q4_paths.py`. For each of the 60
   (system, training IC) units: the growth path per protocol §3.1 on the weak design of the **training** trajectory
   (reuse WP-FA2/WP-FA3 code by import: design, `WeakFit`/QR solver, basis, loaders; do not modify them). For every
   candidate: per-equation term lists (names and 1-based basis indices), the weak coefficients as the flat `p0` in
   `build_rhs` order (reuse the WP-FA3 flattening), per-equation weak SSE, n rows, the weak BIC of rule (a), the path
   step and whether it arose from an addition or a removal. Record the full step log (gains, removal checks). Output
   `analysis/data/sideproject_residual_growth/q4_paths.json`. **Run it.** Control: run the builder twice in-process
   and assert identical candidate lists (protocol §7).
2. **Julia, candidate fits** — `studies/regression/sideproject_q4_path_fits.jl`. Reuse the WP-FA3 runner's machinery
   (`sideproject_q3_weak_start.jl` may be `include`d or its approach copied; no edits to it, nothing under `src/`).
   Per candidate: one `fit_parameters` call with `build_reference_optimizer(max_fit_attempts = 1)`, `p0` = weak
   vector; simulate on the training trajectory (MSE, R², R² by dim, loss evaluations, sentinel/divergence flags) and
   from the **test IC** (`build_trajectory(system, other_ic)`) for generalisation, storing the predicted and target
   states needed for the canonical R² definitions or computing them in Julia exactly as the canonical pipeline does
   (find where EvoGrow's `generalization_r2_variance_weighted` / `_arithmetic` are produced and match that definition;
   name the source in the report). Control (protocol §7): for one unit, the true structure as the only candidate
   reproduces the Q3 W1 loss in `outputs/sideproject_q3_weak_start/results.jsonl` bit-identically. Append-only JSONL
   with resume (skip finished candidates), default `outputs/sideproject_q4_path_fits/results.jsonl`, `--units` for a
   smoke run.
3. **Python, aggregation** — `analysis/scripts/aggregate/aggregate_sideproject_q4.py`: applies rules (c), (a), (b)
   per unit (sentinel/diverged candidates never chosen by (b)/(c)); the pruning rule `max(1e-6, 1e-3·max_abs)` per
   equation exactly as the campaign (find and reuse the existing implementation); raw/pruned exact structure,
   reconstruction and generalisation R² > 0.9 (variance-weighted primary, arithmetic reported); upper bounds of §3.4;
   references from `analysis/data/paper1_phaseC_v1/hierarchy_n47_e935c37/per_run.csv` (clean rows only: noise 0,
   subsampling 1; methods `EvoGrow` configuration `C-1_capped`, and `Weak-SINDy` per configuration over its
   realisations), joined on (system, training IC) — verify the column semantics of `source_/target_initial_condition_set`
   and `direction` against the hierarchy script before joining. Outputs in
   `analysis/data/sideproject_residual_growth/`: `q4_units.csv` (one row per unit × size rule, plus the upper-bound
   rows), `q4_candidates.csv` (one row per candidate), `q4_rules_by_stratum.csv` (R7, R8, R9 with numerators,
   denominators, reference rates incl. Weak-SINDy median and min–max over configurations, pass/fail;
   `reported_only` for non-primary strata), `q4_run_metadata.json` (input hashes, protocol commit `24ede2d`).
   Abort if any unit or candidate is missing.
4. Tests `analysis/tests/test_sideproject_q4.py`: FoBa path on a constructed design (a correlated decoy is added
   first and later removed); normalised cross-equation gain; length cap; determinism; size rules on a hand-built
   candidate table incl. a sentinel candidate; reference join on a fixture derived from real `per_run.csv` rows.

## Forbidden

- No changes to existing files; nothing under `src/`, `experiments/`, `k8s/`, `containers/`, `benchmarks/`.
- No C-6 data (the hierarchy table: clean rows only). Under `outputs/` read only the WP-C4c trajectory export and the
  Q3 results file.
- No thresholds or rules beyond the protocol; no re-runs with changed settings after seeing results. No commit.

## Verification

- `python -m pytest analysis/tests/test_sideproject_q4.py -q`; the path builder once with defaults;
  `python -m pytest analysis/tests -q` (two known pre-existing failures).
- In the report: number of candidates per unit and stratum (needed for the runtime estimate), and the exact Julia
  commands (smoke on two units incl. the control unit, full run, aggregation).

Report: `codex/reports/REPORT_WP_FA4.md`.
