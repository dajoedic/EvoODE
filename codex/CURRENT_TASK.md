# WP-X1c — WISP explorable: size budget, re-simulation tolerance matched to the Q5 evaluation, first layout fixes
**Language: Python** (data export, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-02. Follows WP-X1b (`codex/reports/REPORT_WP_X1B.md`, done). Everything WP-X1/X1b built and every rule
they set stays; this WP changes only what is listed here.

## Why

Claude's review of WP-X1b found three things:
1. **Size.** `results.json` is 138.8 MB and the built page 141.6 MB. The page must be publishable as one file
   (hard limit 16 MB) and committable to git. Almost all of it is the drill-down curve bundles.
2. **Re-simulation failures are mostly integrator differences.** Of the 267 failed cells, 253 differ from the stored
   R² by less than 1e-3 (median 4.4e-6); 14 differ by more. The verification integrates with DOP853 at rtol = atol =
   1e-8, while the stored scores come from the Julia evaluation in `studies/regression/sideproject_q5_noise_fits.jl`
   with its own solver and tolerances. Failures concentrate on systems 61, 27, 26, 52, 8, 63.
3. **Layout** (from a headless Edge screenshot at 1280 px): see Scope 3.

## Scope

1. **Size budget.** The built `explainer/wisp/dist/wisp_explainer.html` must be **≤ 12 MB**, and
   `explainer/wisp/data/` in total ≤ 15 MB.
   - Displayed curves are a presentation copy: thin each curve to at most ~200 points per variable (keep the first
     and last point; a uniform-in-time selection is fine) and store values with a fixed, documented number of
     significant digits that is visually lossless (e.g. 5). Verification stays on the full-resolution integration —
     thinning happens after the check.
   - Store each cell's observed data for display thinned the same way; the live-computation reference cells
     (sys0003_ic1_s0.03_r0_n1, sys0001_ic1_s0.01_r0_n1, sys0001_ic1_s0_r0_n1) keep their full observations, since
     the live path must stay bit-faithful to the reference.
   - Use a compact layout for repeated structures (e.g. a shared time axis per cell instead of per-point objects).
   - Bump the results contract version in the README if the curve encoding changes, and keep the swap test passing.
   - Report the sizes before and after, and confirm the strict JS check still exits 0.

2. **Re-simulation matched to the evaluation that produced the stored scores.** Read
   `studies/regression/sideproject_q5_noise_fits.jl` (and what it calls) to find the solver, tolerances, time grid and
   initial state used for the stored reconstruction and generalization R². Reproduce those settings in Python as
   closely as available (same tolerances and grid; the closest available explicit Runge–Kutta solver if the Julia
   solver has no Python twin — document the substitution). Keep the pass tolerance at **1e-6 absolute on R²**; do not
   loosen it. Then report:
   - passed / failed / withheld per stratum, before (WP-X1b) and after;
   - for every remaining failure: cell, system, stored vs recomputed R², and a classification into (a) integrator
     sensitivity — the recomputed R² moves by more than the tolerance when the Python tolerance is tightened by 10×,
     (b) stable disagreement — it does not move. Do not speculate beyond that classification.
   Curves stay withheld for every cell that does not pass, as before. This is a technical display check; it changes
   no scientific number.

3. **Layout fixes.**
   - The margin note beside the term cards in section 2 ("Which pieces make the rule?") runs off the right edge at
     1280 px. Margin notes must never overflow the viewport at any width; at widths where there is no room they flow
     inline (the existing ≤ 1150 px rule should apply wherever the margin column would not fit).
   - The term playground starts at `du/dt = 0.5u`, whose curve shoots off to ~1,100 against data that saturates near
     74, with "mean squared mismatch 92,800". For readers who know nothing, start from something that visibly almost
     fits (e.g. the growth term only, at a small coefficient, so the reader sees "close, but it doesn't bend"), and
     keep the y-range readable (clip the model curve to a sensible multiple of the data range, with a visible note
     when it is clipped).
   - Every chart gets axis titles (what the axis is, with the variable name, e.g. "time t", "population u", "rate of
     change du/dt"). No unlabelled axis anywhere.
   - In the FROLS bar chart, the term labels and the bar values must stay readable at 360 px width.

## Forbidden

Everything WP-X1 and WP-X1b forbade. In addition: no change to the pass tolerance of the re-simulation check; no change
to any number shown in the results explorer (rates come unchanged from `q5_rates.csv`); no Julia execution.

## Acceptance

1. Built HTML ≤ 12 MB, `explainer/wisp/data/` ≤ 15 MB; rebuild byte-identical.
2. Strict `check_wisp_explainer_js.py` exits 0 on the three reference cells.
3. Re-simulation report as in Scope 2 with before/after counts and the per-failure classification.
4. All tests pass (existing ten plus any you add); a test asserts the size budget.
5. Report `codex/reports/REPORT_WP_X1C.md`.
