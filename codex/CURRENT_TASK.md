# WP-FA6b — Q5-W: revised acceptance, smoke, and the MATLAB identity check (infrastructure only)
**Language: Python**

Stand 2026-10-30. Authority: `docs/sideproject_residual_growth_protocol_q5w.md`, **frozen today with a revised §5**.
Read §5 (points 1–5 and the "Revision" paragraph) and §7 in full first. Builds on WP-FA6
(`codex/reports/REPORT_WP_FA6.md`, commit `9b49329`), which was `blocked` only on the old gate 1(ii) ≥ 15/20 — that
gate no longer exists.

## Scope

1. **Acceptance gate.** In `analysis/scripts/aggregate/accept_sideproject_q5w_wsindy.py` the pre-smoke verdict follows
   the frozen §5: points 1(i), 2, 3, 4 gate; 1(ii) is reported in full but does not gate. Point 5 is a separate verdict
   (`matlab_identity_passed`, absent/`null` until the MATLAB outputs exist) and does **not** block the smoke or the full
   run — it unseals the results (§7). Re-evaluate from the preserved `acceptance/lorenz.jsonl` (stage `complete-pre`);
   never rerun or overwrite the preserved Lorenz run. Then run the smoke stage (20 clean surrogate cells × 6
   configurations, twice, determinism) and put its technical facts and the full-run cost projection in the report.
2. **Port output for the comparison.** Make sure every W1 equation record carries what point 5 compares: the λ̂ grid
   **index** (not only its value), the support, and the coefficients on the original data scale. If WP-FA6 rows already
   carry it, say so; otherwise add it without changing any existing field.
3. **MATLAB input export.** A script that writes, for (a) the 21 Lorenz data sets of point 1 and (b) every C-6 cell with
   ρ = 0, the exact arrays the port receives (observed times, observed states, as written/read losslessly — 17
   significant digits or binary) plus a per-cell manifest (cell key, data hash, library name). Output under
   `outputs/sideproject_q5w_wsindy/matlab_inputs/`. State the number of cells.
4. **Library expressibility (point 5(b)).** Decide from the original code's library inputs (`polys`, `trigs`,
   `custom_tags`/`custom_fcns`, see `build_theta.m`, `get_tags.m`, `build_poly_lib.m`) whether L-C6 and L-Q5 can be
   expressed **exactly** — same columns, same order or a fixed permutation. Extend the mapping test of point 2 to prove
   it numerically. Report per library: expressible yes/no, and how.
5. **MATLAB driver** (`analysis/matlab/run_wsindy_original_q5w.m`, new folder): calls the **unmodified** original code
   from `outputs/reference_wsindy_ode_72d8d6e/` via `addpath` and `wsindy_ode_fun` with the §3 settings on every exported
   input, writes per cell the coefficients (17 digits), the selected λ̂ and its grid index per equation, and the tags /
   column order. Resumable, one file per cell. Base MATLAB only. The driver calls the original; it must not contain any
   code, comment or text copied from it. A working reference for the call signature, written by Claude, is
   `C:\Users\joedicke\AppData\Local\Temp\claude\c--Users-joedicke-Documents-Repositories-EvoODE\0d123bc4-4199-4b50-8574-de7ebd1aefc0\scratchpad\octave_check\run_reference.m`
   (Octave, Lorenz only) — check every setting in it against §3 rather than trusting it. If the original returns λ̂
   only implicitly, derive the index from the original's own outputs and say how.
6. **Comparison script** for point 5: reads the MATLAB outputs and the port's rows, applies the frozen criterion (same
   support and λ̂ index in every equation, max |Δc| ≤ 1e-6·max |c| per equation), writes per-cell verdicts and a summary
   (`cells`, `passed`, list of failing cells with the first differing equation). It prints **no** rate, structure hit,
   R² or comparison — identity verdicts only. Test it on synthetic fixtures (an identical and a deliberately perturbed
   case).
7. Focused tests for the changed and new Python code; run only those plus the existing WP-FA6 tests.

## Verboten

- Running MATLAB (not installed yet) or Octave; the full run over all 4,536 cells; any fit on noisy cells. Claude runs
  those.
- Computing, printing or reporting any rate, structure hit, R², or comparison against Q5 or other baselines — the full
  run's results are sealed until point 5 passes.
- Copying code, comments or text from `outputs/reference_wsindy_ode_72d8d6e/` into the repository.
- Changing the WSINDy algorithm in `wsindy_reference.py` (output fields only, scope 2), the frozen Q5 files,
  `run_phasec_noise_sindy_baselines.py` behaviour, the export, WP-N47 outputs, or the preserved `acceptance/lorenz.jsonl`.
- Touching the uncommitted WP-N48b files: `analysis/scripts/aggregate/aggregate_c6_symbolic_baselines.py`,
  `analysis/scripts/aggregate/run_k8s_symbolic_shard.py`, `baselines/c6_shards.py`,
  `baselines/tests/test_c6_symbolic_execution.py`, `codex/reports/REPORT_WP_N48.md`, `k8s/phase_c_c6_pysr*.yaml`.
- Git operations; cluster jobs; anything running longer than 15 minutes.

## Abnahme

- `summary.json` shows points 1(i), 2, 3, 4 passed and 1(ii) reported; smoke complete on 20 × 6 without error,
  deterministic; projection for 4,536 × 6 in counts, wall-clock as context.
- MATLAB inputs exported (Lorenz 21 + all ρ = 0 cells, count stated), driver and comparison script in place, tests pass;
  the exact MATLAB command Claude has to run is in the report.
- Expressibility of L-C6 and L-Q5 decided and proven numerically.
- Report `codex/reports/REPORT_WP_FA6B.md`; `codex/STATUS.md` as `CODEX_PROTOCOL.md` prescribes.
