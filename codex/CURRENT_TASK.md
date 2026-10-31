# WP-FA7c — Q6 stage 1: end reason `no_gain`
**Language: Python**

Stand 2026-10-31. Authority: `docs/sideproject_residual_growth_protocol_q6.md`, **Amendment 2** at the top. Builds on
WP-FA7/FA7b (`codex/reports/REPORT_WP_FA7.md`, uncommitted files `build_sideproject_q6_paths.py`,
`test_sideproject_q6.py`).

## Scope

1. In `growth_path_with_end` only (not in the frozen `growth_path`, and **not** in the cap=6 control path, which must
   keep reproducing Q5 including its raise): when the best available gain is ≤ 0, end the path; every equation still
   eligible receives end reason `no_gain`. Same handling for all three scientific end conditions.
2. `primary_clean_identity = False` is a recorded deviation (protocol §6), not an acceptance failure; the runner already
   records it without raising — keep it so.
3. Test: a synthetic or real case reaching `no_gain` (the `sys0063_ic1_s0_r0.5_n1` cell is acceptable if fast).
4. Rerun the focused tests and the real-manifest smoke pair (serial, fresh output dirs), compare bytes, report the
   candidate-state projection in counts if the smoke completes.

## Verboten

All of WP-FA7's "Verboten" applies unchanged (no T/R/P, end-reason counts, recall, R², estimator quality; no full
run, fits, Julia, cluster; no changes to frozen code, inputs, protocols; WP-N48b files untouched; git only read-only
`git show f454a32:…`; nothing over 15 minutes; no built-in timeout).

## Abnahme

- `no_gain` implemented and tested; capped control unchanged; tests green.
- Smoke pair complete, byte-identical, Q5 identity and hash controls pass on all 20 cells; clean-identity deviations
  listed by cell ID only.
- Full-run command; report section "WP-FA7c" appended to `codex/reports/REPORT_WP_FA7.md`; `codex/STATUS.md`.
