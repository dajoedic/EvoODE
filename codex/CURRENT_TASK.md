# WP-N46 — accurate integration and correct trig truth for the SINDy-family baselines
**Language: Python**

## Why

Two evaluation defects in the Phase C SINDy-family baselines (SINDy, Weak-SINDy, E-SINDy), both against the baselines:

1. **Integrator.** `simulate_model` in `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py` is explicit Euler on the
   512-point grid (Δt ≈ 0.02). EvoGrow's R² comes from Tsit5 at `abstol = reltol = 1e-9`. Claude re-integrated the clean
   C-6 rows (σ = 0, ρ = 0; 3 methods × 10 configurations × 63 systems × 2 ICs × 3 realizations × 2 regimes = 22,680
   integrations) with `scipy.integrate.solve_ivp(method="DOP853", rtol=1e-9, atol=1e-9)` from the stored active
   coefficients: the R² > 0.9 rate rises by **+2 to +15 pp per configuration** (e.g. Weak-SINDy deg3 0.01:
   reconstruction 71.7 → 87.0 %, generalization 46.8 → 61.4 %; cell level, not the hierarchy aggregation). Euler
   divergence 4,133 → DOP853 2,427 (+259 step-budget stops). This is not a refinement, it changes the paper's comparison.
   Caveat: `sindy_coefficients_active` is thresholded at `max(1e-6, 1e-3·max_abs)` (`serialize_coefficients`), so the
   probe integrated slightly pruned models; the full coefficient matrix is not stored anywhere. Hence a refit, not a
   re-integration from the details files.
2. **Trig truth.** `polynomial_true_terms` (`run_wp_n6_sindy_baseline.py:210`) returns an empty truth set for every
   equation that `sp.Poly` rejects, including the exactly representable `sin(x_i)` equations of systems **23, 28, 43**.
   The two `poly_deg3_sin_cos_*` configurations find the exact support there (threshold 0.1: 18/18 rows in every method),
   but are scored as misses. The structure rate over the 30 exact systems is understated by 5–10 pp for those rows, and
   F1/precision/recall are wrong there too.

## Deliverables

### A. Accurate integrator (Phase C paths only)

- New function (e.g. `simulate_model_accurate`) next to `simulate_model`: same signature and return shape
  `(prediction, status)`; `solve_ivp(method="DOP853", rtol=1e-9, atol=1e-9, t_eval=<the evaluation grid>)` from the
  reference IC; status `diverged` when the state becomes non-finite or `max|y| > 1e9` (terminal event); status
  `max_evals` when the right-hand side has been evaluated more than **1.2e6** times (≈ Tsit5 `maxiters = 1e5` × 12
  stages); `max_evals` counts as not-R² > 0.9 exactly like `diverged`. **No wall-clock timeout** anywhere.
- Build the right-hand side once per model as a vectorised expression from the full coefficient matrix and the
  feature names — the per-call string parsing of `feature_value` is too slow (Claude's probe: ~75 s for a budget stop
  with a compiled RHS). Verify the compiled RHS against `feature_value`-based evaluation on random states in a test.
- `run_phasec_noise_sindy_baselines.py` and `run_phasec_sindy_baseline.py` (the C-4c path) get `--integrator
  {dop853,euler}`, **default `dop853`**. `euler` must reproduce the existing outputs byte-identically (test on a small
  slice). Record the integrator in every details row and in the run metadata.
- `run_wp_n6_sindy_baseline.py`'s own `simulate_model` and the historical scripts (WP-N6, WP-T1b) stay unchanged.

### B. Store the full model

- New details column `sindy_coefficients_full`: the unthresholded coefficient matrix with feature names (JSON). Keep
  `sindy_coefficients_active` as it is. Integration uses the full matrix.

### C. Library-aware true terms

- New function (do not change `polynomial_true_terms`, WP-N6 uses it) that maps each true equation to the library's term
  names: polynomial monomials as today; `sin(x_i)` / `cos(x_i)` appearing linearly with a constant coefficient map to the
  library names exactly as `normalize_feature_name` emits them (`sin(1*x0)` etc.). An equation with any other
  non-polynomial part keeps today's behaviour (empty set → never a hit). Use it in the Phase C paths for
  `true_terms`, structure hits (raw and pruned) and the structural metrics.
- Test: systems 23 → `[{1, sin(1*x0)}]`, 28 → `[{x1}, {sin(1*x0)}]`, 43 → `[{x1}, {1, x1, sin(1*x0)}]`; every
  polynomial system's truth unchanged against `polynomial_true_terms`; list in the report every system whose truth
  changes (expected: only equations containing linear `sin`/`cos` of a single state).
- Check whether the EvoGrow and ODEFormer structure paths in `aggregate_phasec_hierarchy_n43.py` have the same defect
  on 23/28/43; report, and fix only if they do (EvoGrow uses `phase_c_support.json`, expected fine).

### D. Incremental writing

- The noise-baseline runner writes `details.csv` only at the end of a shard (the seeded Weak/E-SINDy run took ~15.5 h
  with nothing on disk). Append rows per finished cell and make a restarted shard skip cells already written
  (resume). The final file must be identical in content to a non-interrupted run (row order may be normalised by a
  final sort; document it).

### E. Hierarchy

- `aggregate_phasec_hierarchy_n43.py` must accept the new outputs for SINDy, Weak-SINDy and E-SINDy and the dop853 C-4c
  control (the C-6 (0,0) vs C-4c control must compare like with like — both dop853). Add an old-vs-new delta table
  (per method × configuration × stratum, both regimes, both structure columns) between `hierarchy_n45` and the new run.
- ODEFormer: report (read-only) which integrator and tolerances its R² path uses. No change.

### F. Commands

- Add to `SCRIPTS.md` the exact commands for: (1) the clean re-run (σ = 0, ρ = 0 only, all three methods, all ten
  configurations, the existing seeds); (2) the C-4c re-run with dop853; (3) the hierarchy as
  `hierarchy_n46`; (4) the full noisy grid re-run — **with a cost estimate** derived from the smoke counts, not run.

## Verboten

- Running anything beyond the smoke below (the clean re-run is Claude's, the noisy grid the user's decision).
- Changing thresholds, libraries, configurations, seeds, the pruning rule, or anything in the EvoGrow / Julia path.
- Committing. Editing this file.

## Smoke (allowed)

- Systems 23, 24, 43 and one system that hits `max_evals` or diverges in the old outputs (pick from
  `outputs/c6_sindy_baselines_5dd1df8`), σ = 0, ρ = 0, all three methods, two configurations incl. a `sin_cos` one.
- `--integrator euler` on the same slice is byte-identical to the existing rows (R² columns, statuses, active terms).

## Abnahme

- Tests pass (python), smoke as above, report `codex/reports/REPORT_WP_N46.md` with: the changed-truth list, the smoke
  table euler vs dop853, the ODEFormer integrator finding, the cost estimate for the noisy grid.
- `STATUS.md` `done` or `blocked`.
