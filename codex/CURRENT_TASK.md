# WP-N45b — make Weak-SINDy reproducible (seed the subdomain sampling)
**Language: Python**

## Why

WP-N45 found that the WP-N34 Weak-SINDy clean rows differ between noise realizations although the clean data are
identical. Claude traced the cause: pysindy 2.1.0's `WeakPDELibrary` samples its integration subdomain centers with
`np.random.uniform`, and `fit_weak_sindy` in `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py` never
seeds NumPy's global RNG. **Every existing Weak-SINDy result is therefore not reproducible.** Weak-SINDy is a
mandatory Paper 1 baseline (plan §9.5a); a reviewer must be able to recompute it. Claude will re-run Weak-SINDy on
the full C-6 export after this fix.

## Deliverables

1. In `run_phasec_noise_sindy_baselines.py`, seed NumPy's global RNG immediately before each Weak-SINDy fit (before
   the `WeakPDELibrary` is constructed or fitted — check in the pysindy source at which point the sampling happens
   and seed before it) with a deterministic per-row seed. Use **the same derivation as the E-SINDy seed from WP-N45**
   (same hashed fields, same configuration key), but with a method tag so that Weak-SINDy and E-SINDy of the same
   cell and configuration never share a seed. Record the seed per row in an output column (a `weak_seed` column, or
   generalise the existing seed column to a method-agnostic name while keeping `ensemble_seed` readable — say which
   in the report).
2. SINDy (`sindy`) must stay **byte-identical** in its outputs; it has no randomness and gets no seed.
3. E-SINDy must stay **byte-identical** to WP-N45 (its seed derivation does not change).
4. Hierarchy (`aggregate_phasec_hierarchy_n43.py`): Weak-SINDy clean rows keep being treated as realization-level
   repetitions, as WP-N45 decided (the seed includes the realization). No other change.
5. Tests: running the same Weak-SINDy cell twice gives identical coefficients and seed; Weak-SINDy and E-SINDy seeds
   differ for the same cell and configuration; SINDy output unchanged.
6. Smoke on the same ≤ 6 cells as WP-N45: Weak-SINDy run twice, byte-identical coefficient output both times.
7. `SCRIPTS.md`: the full re-run command for `weak_sindy,e_sindy` on the C-6 export, 10 shards, into a **new** output
   directory (do not overwrite `outputs/c6_sindy_baselines_5dd1df8/` or the tracked
   `analysis/data/paper1_phaseC_v1/c6_sindy_5dd1df8/`), and the merge step for it.
8. Report `codex/reports/REPORT_WP_N45B.md`: where in pysindy the sampling happens, the seed derivation, test and
   smoke results.

## Verboten

- Running Weak-SINDy or E-SINDy on more than 6 cells.
- Changing any library, threshold, `WeakPDELibrary` argument (`K`, `H_xt`, `p`, …) or `EnsembleOptimizer` argument.
- Overwriting existing outputs or tracked data.
- Looking at or comparing C-6 EvoGrow results (blind rule).
- Committing. Editing `codex/CURRENT_TASK.md`.

## Abnahme

- `python -m pytest analysis/tests -q -k "sindy or hierarchy"` passes (workspace `--basetemp` if needed, say so).
- Smoke: two Weak-SINDy runs on the same cells are byte-identical.
- `STATUS.md` set to `done` with WP-N45b and the report path, or `blocked` with the reason.
