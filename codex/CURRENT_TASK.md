# WP-FA7b — Q6 stage 1: resolve the two control conflicts of WP-FA7
**Language: Python**

Stand 2026-10-31. Authority: `docs/sideproject_residual_growth_protocol_q6.md`, **new amendment at the top** (read it).
Builds on your WP-FA7 work (`codex/reports/REPORT_WP_FA7.md`; files `build_sideproject_q6_paths.py`,
`test_sideproject_q6.py`, uncommitted). Your diagnosis of both conflicts was right; the protocol was wrong.

## Scope

1. **Replace the reference-prefix control** by the amendment's control: a fourth end condition "Q5" (cap 6 or the
   numerical-zero stop, i.e. the existing test hook `cap=6`) is built for every cell and must reproduce the Q5
   candidate list and weak coefficients bit-identically (raised on failure). Its paths are a control artefact, written
   only to `controls.csv` as pass/fail per cell — no path file, no classification. Remove the old prefix check and its
   test; keep a test that the uncapped reference may legitimately differ from Q5 (the `sys0024` case) without raising.
2. **Q5 protocol digest:** verify `docs/sideproject_residual_growth_protocol_q5.md` against the content at git commit
   `f454a32` (read via `git show f454a32:<path>`, read-only git), not the working copy. The other three digests stay as
   they are. No relaxed comparison.
3. Run the focused tests, then the real-manifest smoke twice (`smoke_a`, `smoke_b`, serial) and verify byte-identical
   outputs. Projection in counts (paths, equation rows, candidate states — the latter is now allowed as a technical
   count; per-stratum totals of candidate states beyond 6 terms are **not** reported).

## Verboten

Everything under "Verboten" of WP-FA7 still applies (no T/R/P, end-reason counts, recall, R², estimator quality; no
full run; no fits; no changes to frozen code, inputs, protocols; WP-N48b files untouched; no git operations except the
read-only `git show` of item 2; nothing longer than 15 minutes; no built-in timeout).

## Abnahme

- Controls as amended; tests green; smoke 20 × (3 + control) deterministic, all controls pass.
- The exact full-run command in the report. Report: append a section "WP-FA7b" to `codex/reports/REPORT_WP_FA7.md`;
  `codex/STATUS.md` as `CODEX_PROTOCOL.md` prescribes.
