# WP-FA10 — Q5-W: WSINDy rows from the MATLAB original; diagnose the port's deviation
**Language: Python**

Stand 2026-11-02. Authority: `docs/sideproject_residual_growth_protocol_q5w.md`, in particular the new paragraph
"Revision 2026-11-02" at the end of §5 (read the whole protocol). Builds on WP-FA6, FA6b, FA6c — read
`codex/reports/REPORT_WP_FA6.md`, `_FA6B.md`, `_FA6C.md` first.

## Situation

Claude ran the unmodified original WSINDy code (commit `72d8d6e`, `outputs/reference_wsindy_ode_72d8d6e/`) in MATLAB
R2026b through `analysis/matlab/run_wsindy_original_q5w.m` on every exported input:

- `outputs/sideproject_q5w_wsindy/matlab_outputs/*.json` — 4,557 tasks (21 Lorenz + W1 × {L-C6, L-Q5} on every ρ = 0
  C-6 cell)
- `outputs/sideproject_q5w_wsindy/matlab_outputs/w1_interp/*.json` — 4,536 tasks (W1-interp × {L-C6, L-Q5} on every
  ρ = 0.5 cell)

The identity check against the port (`compare_sideproject_q5w_matlab.py`) failed: verdicts under
`outputs/sideproject_q5w_wsindy/matlab_identity/` and `.../matlab_identity/w1_interp/`. The user decided that every
uniform-grid WSINDy row is taken from the original's output; the port stays the source only for arms with no
original counterpart.

## Scope

1. **Rows from the original.** Produce WSINDy result rows for W1 (ρ = 0) and W1-interp (ρ = 0.5), both libraries,
   from the MATLAB output JSON instead of the port's coefficients. The evaluation (R² reconstruction and
   generalization, raw and pruned structure fields, every other per-row field the port's `details.csv` carries) must
   go through **the same evaluation code path** the port's rows use — only the coefficient source changes. Output
   files with the same schema as `outputs/sideproject_q5w_wsindy/full/details.csv` and
   `.../w1_interp_full/details.csv`, in new folders (e.g. `full_matlab/`, `w1_interp_full_matlab/`); never overwrite
   the port's files. Every row records its coefficient source (`matlab_original_72d8d6e` vs `port`) and the input
   hashes from the manifest. Cost counts that only the port can supply (least-squares solves etc.) are left empty for
   MATLAB rows and declared, not estimated.
2. **Controls before any row is trusted:**
   - On every task where the identity verdict passed, the MATLAB-sourced row equals the port's row in every
     evaluation field (R², structure fields) — bit-identical, or name each exception with the reason (coefficients
     agree only to 1e-6·max|c| by the §5.5 criterion, so tiny R² differences are possible; report their maximum).
   - Every manifest task has exactly one MATLAB output; hashes in the output match the manifest; no task missing.
3. **Downstream switch.** Every consumer that reads the port's W1 / W1-interp rows for the Q5-W comparison (at least
   `aggregate_sideproject_q7.py`; search for all) gets an explicit option/default to read the MATLAB-sourced rows for
   those arms, port rows for W1 on the native irregular grid, W1-cap and W2. Old behaviour reproducible by option.
4. **Diagnosis of the port's deviation (report only, change nothing in the port).** On the failing tasks versus a
   sample of passing ones: condition number / numerical rank of the weak-form design matrices the original builds
   at the selected λ, and whether replacing the port's least-squares call by a MATLAB-backslash-equivalent choice
   (e.g. QR with column pivoting and MATLAB's rank tolerance) would reproduce MATLAB on the failing tasks — as an
   offline experiment in a separate script, not as a change to `wsindy_reference.py`. State the cause with evidence.
5. Tests for 1–3 (small fixtures; no full run in tests).

## Forbidden

- **No WSINDy rate, structure rate or comparison with Q5/Q7 is computed or reported** — not in the report, not in
  logs. Produce the rows and the controls only; opening the numbers is Claude's step with the user.
- No edit to the original reference code, the MATLAB driver's call or settings, the port (`wsindy_reference.py`), the
  frozen protocols, Q5/Q7 output tables, WP-N48b files.
- No MATLAB execution (Claude does that), no cluster work, no git operations.

## Acceptance

Controls of scope 2 pass (or every exception named and explained); both row files complete (4,536 + 4,536 C-6 rows);
downstream switch tested; diagnosis with evidence. Report `codex/reports/REPORT_WP_FA10.md`, status in
`codex/STATUS.md`, exact commands Claude runs to reproduce.
