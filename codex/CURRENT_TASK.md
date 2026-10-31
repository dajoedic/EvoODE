# WP-FA7 — Q6 stage 1: data-derived path end, rebuilt WISP paths in the weak space
**Language: Python**

Stand 2026-10-31. Authority: `docs/sideproject_residual_growth_protocol_q6.md` (frozen; read it in full). Builds on
the Q5 path builder `analysis/scripts/aggregate/build_sideproject_q5_paths.py` and `build_sideproject_q4_paths.py`
(`growth_path`), the weak design `build_design(..., 'weak', ...)` in
`analysis/exploratory/term_relevance/term_relevance.py`, and the Q5 inputs `outputs/sideproject_q5_inputs/`
(`q5_grid_paths.json`, 1,632 cells, the C-6 export it points to).

## Scope

1. **Noise estimator (§3.1)** as a named function: local leverage-corrected cubic residuals over 9 observed points,
   per-point variance as the mean over 21 points, actual times, per state component. No noise model.
2. **Floors (§3.2, §3.3)** as named functions: primary `F(S) = trace((I − P_S) C_b)` with `C_b` from the window
   endpoints of every weak row (shared endpoints correlate); secondary with the linearised right-hand-side term on the
   path state's weak least-squares coefficients and the trapezoid weights. State in the report how ∂f/∂x is obtained
   for every basis term (incl. `sin`, `cos`, constant) and verify it against finite differences in a test. Watch memory:
   rows are ~5 × n_observed; build `C_b` sparsely or use the row structure, do not form dense matrices you do not need.
3. **Path with a pluggable end condition (§3.4):** a new path function that reproduces `growth_path` exactly, except
   that the end condition per equation is a parameter (primary floor / secondary floor / reference = numerical zero and
   full basis only) and a repeated FoBa model ends the path with reason `cycle`. `growth_path` itself and the Q4/Q5
   builders are not changed. Each path records per equation: end reason, length, states beyond 6 terms.
4. **Runner** over all 1,632 Q5 cells × three end conditions, writing per-cell paths (same candidate schema as
   `q5_grid_paths.json`, so stage 2 can fit them unchanged) plus a per-equation table with the §4 classification
   T / R / P and its fields, and the estimator-check table (σ̂ against σ · |x_clean| per point, quantiles per
   condition). Output into `outputs/sideproject_q6_paths/` (gitignored; a later aggregation moves tables into
   `analysis/data/sideproject_residual_growth/`). Parallel over cells allowed (processes), deterministic output order.
5. **Controls (§6)** inside the runner, failing loudly: σ = ρ = 0 primary path vs Q5 (reported per cell, not raised —
   the protocol counts a deviation, it does not forbid it); reference-path prefix identity against Q5 (raised); hashes
   (raised).
6. Focused tests: estimator on synthetic data with known heteroscedastic noise; floor against a Monte Carlo estimate on
   a small synthetic weak problem (primary and secondary); path reproduction of `growth_path` with the reference end
   condition plus the cap on a few Q5 cells; `cycle` handling.
7. **Smoke:** 20 cells (dim 1/2/3_feasible/4, σ = 0 and noisy, both ρ), three end conditions, run twice, identical.
   Report technical facts and a projection for the full run in counts (wall-clock as context).

## Verboten

- Computing, printing or reporting any T/R/P count, rate, structure hit, recall, R² or estimator-quality number —
  smoke included; technical facts only (row counts, end-reason **counts are also forbidden**, control pass/fail allowed).
- The full run over 1,632 cells (Claude runs it); any fit, ODE simulation, Julia, cluster job.
- Changing `growth_path`, the Q4/Q5 builders, the weak design, the Q5 inputs or records, any frozen protocol.
- Choosing any constant other than those in the protocol.
- Touching the uncommitted WP-N48b files: `analysis/scripts/aggregate/aggregate_c6_symbolic_baselines.py`,
  `analysis/scripts/aggregate/run_k8s_symbolic_shard.py`, `baselines/c6_shards.py`,
  `baselines/tests/test_c6_symbolic_execution.py`, `codex/reports/REPORT_WP_N48.md`, `k8s/phase_c_c6_pysr*.yaml`.
- Git operations; anything running longer than 15 minutes; any built-in timeout in the scripts.

## Abnahme

- Estimator, floors, pluggable path and runner exist; tests green (run only the new tests plus the Q4/Q5 path tests).
- Reference end condition plus cap reproduces `growth_path` on the test cells bit-identically.
- Smoke 20 × 3 deterministic, controls pass, projection in counts; the exact full-run command for Claude in the report.
- Report `codex/reports/REPORT_WP_FA7.md`; `codex/STATUS.md` as `CODEX_PROTOCOL.md` prescribes.
