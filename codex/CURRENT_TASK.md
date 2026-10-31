# WP-FA6c — Q5-W: arm W1-interp (linear interpolation onto a uniform grid on ρ = 0.5 cells)
**Language: Python**

Stand 2026-10-31. Authority: `docs/sideproject_residual_growth_protocol_q5w.md`, new **§4a** (read it in full, plus §2,
§3 and §5 point 5). Builds on WP-FA6/FA6b (`codex/reports/REPORT_WP_FA6.md`, `REPORT_WP_FA6B.md`, commit `8aa6eec`).

## Scope

1. **New configurations `W1-interp:L-C6` and `W1-interp:L-Q5`** in `analysis/scripts/aggregate/run_sideproject_q5w_wsindy.py`,
   selectable through the existing `--configurations` option, **not** added to the default `CONFIGS` tuple (the existing
   six-configuration behaviour and outputs must stay unchanged). Per §4a: for a cell with an irregular observed grid,
   interpolate the observed states piecewise linearly per state onto a uniform grid of M = number of observed points over
   [first, last observed time], then call the unchanged W1 fit on that uniform grid. The interpolation is a separate,
   named function; `wsindy_reference.py`'s algorithm is not changed. If a cell's observed grid is already uniform (ρ = 0),
   the configuration refuses or passes it through unchanged — state which, and test that it equals W1 bit-identically on
   such a cell.
2. **Output rows** carry everything W1 rows carry (incl. `q5w_equations` with λ̂ grid index, support, coefficients on
   the original scale), plus the interpolation facts: number of points, uniform `dt`, and a hash of the interpolated
   arrays. Evaluation unchanged (§2): it never sees interpolated data.
3. **Cell list for the full run:** a CSV of every C-6 cell with ρ = 0.5 in the same five-key format the runner's `--cells`
   reads; state the count (expected 2,268).
4. **MATLAB export (§4a, §5.5 extension):** extend `export_sideproject_q5w_matlab.py` with an option that exports the
   **interpolated** uniform inputs of every ρ = 0.5 cell (same lossless format and manifest as WP-FA6b, the manifest marks
   them as W1-interp), into a separate subfolder of `outputs/sideproject_q5w_wsindy/matlab_inputs/`. Extend
   `compare_sideproject_q5w_matlab.py` so it can compare W1-interp rows against those MATLAB outputs with the unchanged
   §5.5 criterion. The MATLAB driver must not need changes; if it does, say why.
5. **Smoke:** 20 ρ = 0.5 cells (mix of dim 1/2/3, noisy and σ = 0) × the two new configurations, run twice, identical
   output. Report technical facts and a cost projection for 2,268 × 2 rows in counts (wall-clock as context).
6. Focused tests for the new code; run only those plus the existing Q5-W tests.

## Verboten

- Computing, printing or reporting any rate, structure hit, R² or comparison (smoke included: technical facts only).
- The full run over 2,268 cells (Claude runs it); MATLAB or Octave; any other interpolant.
- Changing the existing six configurations, their outputs under `outputs/sideproject_q5w_wsindy/full*`, the WSINDy
  algorithm, the evaluation path, the frozen Q5 files, WP-N47 outputs.
- Copying code, comments or text from `outputs/reference_wsindy_ode_72d8d6e/` into the repository.
- Touching the uncommitted WP-N48b files: `analysis/scripts/aggregate/aggregate_c6_symbolic_baselines.py`,
  `analysis/scripts/aggregate/run_k8s_symbolic_shard.py`, `baselines/c6_shards.py`,
  `baselines/tests/test_c6_symbolic_execution.py`, `codex/reports/REPORT_WP_N48.md`, `k8s/phase_c_c6_pysr*.yaml`.
- Git operations; cluster jobs; anything running longer than 15 minutes.

## Abnahme

- Two new configurations, default behaviour unchanged (a test proves the default six still produce identical rows on a
  sample cell); identity W1-interp = W1 on a uniform-grid cell, or a documented refusal.
- ρ = 0.5 cell list written, count stated; interpolated MATLAB inputs exported, count stated; comparison extended and
  tested on synthetic fixtures.
- Smoke 20 × 2 deterministic, projection in counts; the exact full-run command for Claude in the report.
- Report `codex/reports/REPORT_WP_FA6C.md`; `codex/STATUS.md` as `CODEX_PROTOCOL.md` prescribes.
