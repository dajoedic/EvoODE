# WP-X7e — WISP explorable: page 2 start state and column balance, page 3 term-comparison layout
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X7d (commit `393152a`, preview version 8). All rules from WP-X1..X7d stay in force
(whitelist, blind rule, no Q7/Q8 results, no hand-typed result numbers, both metrics, i18n parity, byte-identical
rebuild, swap test, size ≤ 14 MB, fallbacks, wheel routing, `data-claim="review"` on prose, no next-page-only links,
endless dish loop, fit at 1366 × 657 and 1366 × 768). No change to `compute.js` or any data file. Scope: pages 2 and 3.
Page 1 stays as it is (a real video is postponed; do not add anything for it).

## User feedback (2026-11-03, version 8)

"Page 2: at the start no term should be selected. The sizes still don't match — the left side with the controls and the
text below is less tall than the right side; I'm picky about that. Page 3: below the chart a legend in a box saying
which line means what. The actual equations to the right of it, but presented in a cool way." Claude proposed a term
comparison table; the user agreed ("mach mal").

## Scope

### 1. Page 2 (`p-challenge`)

- **Start state: no term selected.** All six checkboxes off, all controls disabled, the equation reads `du/dt = 0`,
  the curve is the constant first measurement, the meter shows the resulting R². "Neu anfangen" returns to this
  state. The page-3 reader equation for an untouched playground is this empty equation.
- **Remove the native number-input spinners** (the small up/down arrows inside the typed field) in all browsers
  (`appearance: textfield` / `-moz-appearance` / `::-webkit-inner-spin-button` etc.). Only the ± buttons remain; arrow
  keys in the field may keep working.
- **Columns flush.** The left column (legend line, card grid, icon buttons, punchline) and the right chart panel must
  start and end at the same height: top edges and bottom edges equal within 2 px at 1366 × 768 and 1366 × 657, EN and
  DE. Achieve it by layout (e.g. grid with stretched rows, the card grid growing to fill, the punchline anchored to the
  bottom of the left column), not by fixed pixel heights tuned to one language. Add this measurement to
  `check_wisp_explainer_fit.py` (both columns' bounding rects) so Claude's browser run checks it.

### 2. Page 3 (`p-solution`) — new layout

Top: headline and idea text unchanged. Below, two columns:

- **Left: the chart** (as large as fits), and **directly beneath it a legend box** (a bordered box): one row per line
  style with an exact swatch — Messwerte / Measurements (dots), Deine Gleichung / Your equation, WISP, Wahre Gleichung
  / True equation. Legend only; no formulas, no numbers in the box.
- **Right: the term comparison.** A small table:
  - Columns: the six catalogue blocks `1, u, u², u³, sin u, cos u` in the same order and notation as the page-2 cards
    (header row), plus a final column R².
  - Rows, top to bottom: **Wahr / True**, **WISP**, **Du / You**. Each row label carries a short line swatch matching
    its chart line.
  - Each cell shows the coefficient of that block in that equation (3 significant digits, locale decimal separator),
    or stays empty. Cell styling by comparison with the true support: block present and in the truth → filled green
    chip with a ✓; block present but not in the truth → red/orange chip with a ✗ ("überflüssig" / "extra" in its
    tooltip); block in the truth but missing in this row → empty dashed outline ("fehlt" / "missing" in its tooltip).
    The True row uses neutral chips. Colour must not be the only signal (✓/✗/dashed outline), and both themes must
    keep sufficient contrast.
  - R² column: the WP-X7b/X7c browser R² to the measurements (same values), as a number plus a small bar (0–1,
    negative values shown at 0 with the number still negative).
  - Below the table, small: the three equations as normal formulas (`du/dt = …`), the true one in its stored form
    as today.
  - One short caption under the table: DE "Grün: Baustein steckt auch in der wahren Gleichung. ✗: überflüssig.
    Gestrichelt: fehlt. R² zu den Messwerten, im Browser berechnet." / EN "Green: block is also in the true equation.
    ✗: extra. Dashed: missing. R² to the measurements, computed in the browser."
- **Where the true coefficients per block come from.** The table needs the truth as block coefficients (the stored
  truth string is in product form, `0.79u(1-0.01346u)`). Use, in this order: (a) structured true terms/coefficients
  already present in the exported data or the benchmark file the exporter already reads; (b) otherwise expand the
  stored truth string with a small, tested expander restricted to polynomials in the state (sums/products/powers of
  `u` with numeric constants); (c) if neither works for a cell, show the True row with the stored formula only and no
  chips, and mark WISP/You cells without ✓/✗. Report which path the running cell uses. No hand-typed coefficients.
- WISP and reader coefficients come from the same sources as today (stored WISP equation, page-2 state).
- At phone width: chart, legend box, then the table (horizontally scrollable inside its own box if needed, never the
  page).

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all 45 tests adapted and passing, plus new tests: page 2 starts
   with no term enabled and `du/dt = 0`, reset returns there, no native spinners (CSS present), column measurement
   added to the fit checker; page 3 legend box has four rows without numbers, the table has the six block columns in
   catalogue order plus R², three rows in the order True/WISP/You, chip classes follow the support comparison (test
   with a reader equation containing one correct, one extra and one missing block), the true coefficients equal the
   expansion of the stored truth to 1e-12, R² equal to the page-2 meter for the same state.
2. Strict numerical checks exit 0.
3. `check_wisp_explainer_fit.py`: if blocked in your sandbox, status `blocked` with "browser not runnable here —
   environment, not the task"; Claude runs it (including the new column check).
4. Report `codex/reports/REPORT_WP_X7E.md`: what changed, the truth-coefficient path, and the test count.
