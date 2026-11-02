# WP-X6 — WISP explorable: the opening becomes a challenge ("what exactly is the formula?"), plus polish
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X5 (`codex/reports/REPORT_WP_X5.md`, commit `6b08c92`, preview version 4). Every rule from
WP-X1..X5 stays in force (≈ 19 pages, one section per page, whitelist, blind rule, no Q7/Q8 results, no hand-typed
result numbers, both metrics, strata separate, i18n parity, byte-identical rebuild, swap test, size ≤ 14 MB, fallbacks,
wheel routing). No change to numerical WISP code (`compute.js` path/FoBa/stop) or data.

## User feedback (2026-11-03)

"The page where you build the term yourself is mega! The data on page one look great — you'd say: well, logistic
growth, right? **Put the reader directly in front of the question: nice, but what EXACTLY does the formula look
like?!**"

## Scope

### 1. New page 2: the challenge (replaces the "Which future?" guess page)

- Same real data as page 1 (the running example, logistic growth with 3 % noise). Headline along the lines of
  "Looks like logistic growth, right? Fine — but what exactly is the formula?" / "Sieht nach logistischem Wachstum
  aus, oder? Schön — aber wie genau lautet die Formel?" (final wording yours, both languages).
- **The term playground moves here** as the page's hero: term cards (the catalogue `1, u, u², u³, sin u, cos u`) to
  switch on/off, a coefficient control per active term, the live equation in formatted math, and the reader's curve
  simulated from the first measurement drawn over the data (curve thick and high-contrast, data dots lighter).
- Coefficient controls must make the right answer **reachable but not trivial**: a slider per term with a sensible
  range and step for this data (the scale of `u` coefficients is ~1, of `u²` ~0.01 — use per-term ranges or a
  log-scale/precision control; also allow typing a value), plus a fine-adjust (e.g. arrow keys / ± buttons).
- A **closeness meter** that updates live: the fit to the measurements as R² (or a 0–100 % score derived from it,
  clearly labelled) with a short verbal grade ("far off" … "very close"). Mark it as an illustration (simple
  simulation in the browser, not WISP).
- A **hint ladder** for readers who get stuck (each hint one click): (1) "logistic growth needs two terms"; (2) "try u
  and u²"; (3) "the u² coefficient is small and negative". No hint gives the numbers.
- A **reveal** button "Show me what WISP finds" that jumps to the solution page (page 3), where the reader's last
  equation is shown beside WISP's and the truth (keep the reader's equation in page state; no storage needed).
- The punchline in one or two sentences on the page: even when you know the shape, finding the exact terms and numbers
  by hand is hard — and with two or three interacting quantities, unknown shapes and more noise it becomes hopeless.
  That is the job WISP does. (Text, no numbers typed.)
- The later catalogue page keeps its role (catalogue, why combinations explode) but **no longer has its own
  playground**; it refers back to the challenge ("the building blocks you used on page 2").
- Tests: the challenge page exists as page 2 in both languages; toggling terms and changing coefficients updates the
  equation, curve and meter (DOM harness); the hint ladder reveals hints in order; the reveal carries the reader's
  equation to page 3; the old guess page is gone; page count stays within 18–22.

### 2. Polish from Claude's review of version 4

- Page 3 (solution): the model curve must be clearly visible over the data (thick, step/accent colour, drawn above the
  dots; dots lighter and smaller).
- Explorer: stratum labels "1D", "2D", "3D (fittable)", "4D" (DE: "1D", "2D", "3D (fittbar)", "4D") instead of
  "dim1"…; no clipped axis labels (give the chart panel the room or let the panel scroll internally with visible
  boundary).
- Fit at 1366 × 657: `p-headline` and `p-frols-intro` still overflow slightly — condense.
- If the guess page's end-label overlap logic is reused anywhere, add simple collision avoidance for direct line-end
  labels (shift vertically when closer than one line height).

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all existing tests (33) adapted and passing, plus the challenge
   tests of Scope 1.
2. Strict numerical checks (`check_wisp_explainer_js.py`, `check_wisp_explainer_x2.py`) exit 0.
3. `check_wisp_explainer_fit.py`: all pages fit at 1366 × 768 and 1366 × 657, EN and DE, navigation checks pass. If the
   browser is blocked in your sandbox, status `blocked` with "browser not runnable here — environment, not the task";
   Claude runs it.
4. Report `codex/reports/REPORT_WP_X6.md` with the coefficient ranges chosen and why, and the hint texts.
