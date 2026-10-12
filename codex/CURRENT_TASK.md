# WP-N45 — E-SINDy arm and Weak-SINDy / E-SINDy rows in the §9.3 hierarchy
**Language: Python**

## Why

The user decided on 2026-10-13 that **E-SINDy and Weak-SINDy are full Paper 1 baselines** in every table, clean and
noisy (plan `docs/paper1_phaseC_benchmark_plan.md` §9.5a — read it in full; it is the specification). Earlier work of
the user was rejected for lacking exactly these two.

- **Weak-SINDy** already ran (WP-N34) on all 4,536 exported cells × ten configurations, the clean `(0, 0)` condition
  included; its rows sit in the C-6 SINDy shard outputs next to SINDy (`method == "weak_sindy"`). It is missing from
  the §9.3 hierarchy built by WP-N43b, which carries EvoGrow, SINDy and ODEFormer only.
- **E-SINDy** does not exist yet.

## Deliverables

1. **E-SINDy arm in `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`**, as a third method
   `e_sindy` beside `sindy` and `weak_sindy`, selectable like the existing two (default method list stays
   `sindy, weak_sindy` so that existing commands are unchanged; E-SINDy is requested explicitly).
   - Exactly the SINDy arm (`fit_sindy`: same library from `build_library(cfg)`, same derivative estimate, same STLSQ
     threshold, `alpha` and `normalize_columns`) with the STLSQ wrapped in pysindy 2.1.0's `EnsembleOptimizer`:
     `bagging=True`, and **every other argument at its library default** (`library_ensemble=False`, `n_models=20`,
     `n_subset=None`, `replace=True`, `ensemble_aggregator=None` → median). Do not pass the defaults implicitly by
     omission only: record them explicitly in the output metadata so the record shows what ran.
   - **Reproducibility:** the bootstrap uses NumPy's global RNG inside pysindy. Seed it immediately before each
     E-SINDy fit from a stable hash of the cell key and configuration name (SHA-256, first 8 hex digits → int);
     record the seed per row. Running the same cell twice must give identical coefficients — test it.
   - Everything after the fit (integration, reconstruction/generalization R², raw and pruned structure, metrics,
     export-hash checks, output columns) is the shared path the other two methods use. No E-SINDy-specific metric.
   - The `(0, 0)` control logic that exists for SINDy must not be applied to E-SINDy as a pass criterion (there is
     no E-SINDy reference); report E-SINDy `(0, 0)` rows as plain results.
2. **Hierarchy:** extend `analysis/scripts/aggregate/aggregate_phasec_hierarchy_n43.py` so that the clean §9.3
   tables (`benchmark.csv`, `per_system.csv`, `per_run.csv`, `sensitivity.csv` as applicable) carry **Weak-SINDy**
   and **E-SINDy** rows next to SINDy, read from the same C-6 `(0, 0)` source and processed by exactly the SINDy
   rules (realization-identity check on the clean group, both directions, variance-weighted and arithmetic R²,
   raw/pruned structure, three-way class). Methods are separate rows; never pool them with SINDy. All ten
   configurations per method, none selected. E-SINDy input comes from a new `--esindy-details` /
   `--esindy-shards-dir` argument; when E-SINDy outputs are not present yet, the script must still run and say in
   `metadata.json` that E-SINDy rows are absent — it must **not** fail and must **not** fabricate rows. Existing
   EvoGrow, SINDy and ODEFormer numbers must stay **byte-identical** (add a control row comparing against
   `analysis/data/paper1_phaseC_v1/hierarchy_n43b/benchmark.csv`).
3. **Tests:** E-SINDy determinism (same cell twice → identical coefficients and seed), E-SINDy metadata carries the
   explicit defaults, method selection keeps the old default, hierarchy with and without E-SINDy input, Weak-SINDy
   rows present, unchanged EvoGrow/SINDy/ODEFormer rows.
4. **Smoke (allowed, small):** run the E-SINDy arm on **at most 6 exported cells** (dim 1 and dim 2, clean and one
   noisy condition) with all ten configurations; report fit status, wall time per cell (context only) and the
   projected time for all 4,536 cells. Do **not** run the full set.
5. **`SCRIPTS.md`:** the E-SINDy run command (sharded the same way the C-6 SINDy run was, 10 shards) and the
   hierarchy command with the new arguments.
6. **Report** `codex/reports/REPORT_WP_N45.md`: what was built, the exact `EnsembleOptimizer` arguments as
   recorded, smoke results, projected full-run time, anything in §9.5a that was ambiguous against pysindy 2.1.0.

## Verboten

- Running E-SINDy on more than 6 cells; running the full C-6 set (Claude runs it).
- Changing any SINDy or Weak-SINDy fitting behaviour, any threshold, library or configuration, or the
  `EnsembleOptimizer` arguments beyond `bagging=True`.
- Looking at, aggregating or comparing **C-6 EvoGrow** results in any form (blind rule, plan §9.4d pending). The
  clean Phase C EvoGrow rows already in WP-N43b may be read for the byte-identity control only.
- Means or medians as effect sizes.
- Committing. Editing `codex/CURRENT_TASK.md`.

## Abnahme

- New and existing tests for both scripts pass (`python -m pytest analysis/tests -q -k "sindy or hierarchy"`,
  use a workspace `--basetemp` if the sandbox needs it, and say so).
- The hierarchy run without E-SINDy input reproduces the WP-N43b EvoGrow/SINDy/ODEFormer rows byte-identically and
  adds the Weak-SINDy rows.
- Smoke: all E-SINDy fits on the ≤ 6 cells either `success` or a reported failure reason; projected full-run time
  stated.
- `STATUS.md` set to `done` with WP-N45 and the report path, or `blocked` with the reason.
