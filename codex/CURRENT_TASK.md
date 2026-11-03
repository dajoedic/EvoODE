# WP-X11 — WISP explorable: adapt tests and checker to Claude's chapter-1 rework (no design changes)
**Language: Python** (tests, checker) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03, late. Follows WP-X10 (commit `5d11df7`, preview version 13). **Claude has already implemented the
following in the working tree (uncommitted) after the user's review — treat it as the specification, do not redesign
it:**

1. **Navigation directions swapped** (`explainer/wisp/src/pages.js`): chapters stack top to bottom, sub-steps of a
   chapter run left to right. `←`/`→` = previous/next page (linear, crossing chapter ends); `↑`/`↓` = previous/next
   chapter (`chapterTarget`); `PageDown`/`PageUp`/`Space`/wheel = linear next/previous page (unchanged). A change
   inside a chapter slides horizontally (translateX with the sign of the index delta); a chapter change scrolls
   vertically (`smoothTo`). Sub-step dots sit in a horizontal row at the bottom (`pages.css`).
2. **1a morph** (`app.js` `initChapterMorph`, `index.html` `#c1-show-u` / `#c1-show-diff` / `#c1-morph-note`): two
   toggle buttons; the 512 measured dots animate (900 ms, reduced motion: instant) from u(t) to the change to the next
   point, u(i+1) − u(i), at the midpoint time; the axis range and label morph with them. `window.WispChapterMorph`
   exposes `states`, `show`, `current`.
3. **New sub-step `p-c1-noise`** (6 of 8, between `p-c1-every` and `p-c1-percent`; `app.js` `initChapterNoise`):
   explains the noise estimate of `compute.js` `noiseVariance` (cubic through 9 neighbours, leverage correction,
   neighbourhood average). Slider `#c1-noise-center`; chart shows the 9 points, the local cubic, the centre point and
   its deviation; result line compares the estimated mean relative noise with `teaching.sigma` and states the floor.
   `window.WispChapterNoise` exposes `variance`, `relative`, `local`, `draw`. Eyebrows now read "{i} von {n}" with
   n = 8.
4. New i18n keys `x11_*` (DE/EN), `x10_eye` and `x10_text_5` changed; CSS additions at the end of `pages.css`.

Claude's browser checks pass for this state: no console errors; keys behave as in 1; fit at 1366 × 657 / 768 has no
overflow (the fit checker only fails on its hard-coded delivered inventory, see below).

## Scope — tests and checker only

- Adapt every test and the fit checker to the new state: delivered inventory includes `p-c1-noise` (10 visible pages,
  27 sections in total); section-order assertions; the old `←→` = chapter / `↑↓` = sub-step key tests become the new
  mapping; chapter-1 eyebrow totals (8); any test that reads `x10_eye` / `x10_text_5` or the old 1a chart
  (`chart(...)` on `#c1-visual-0`); `test_hook_bilingual_history_and_illustration_only` and the other 8 currently
  failing tests (`python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp`).
- Add tests: (a) morph — clicking `#c1-show-diff` sets `aria-pressed`, the note text and, after the animation (fake
  timers / rAF stub), each dot's y equals the neighbour difference of the data (last dot hidden), and back to u(t);
  reduced motion jumps directly; (b) noise page — `WispChapterNoise.variance` equals `WispCompute.noiseVariance` on the
  teaching data; `relative` equals the mean of sqrt(variance)/|u|; the result line contains that value, `teaching.sigma`
  and the 1f floor (identical to the 1f number); the local cubic for a fixed centre equals a least-squares cubic through
  the same 9 points; (c) keys — `→` from the last intro page reaches `p-c1-data`, `↓` from `p-hook` reaches `p-c1-data`,
  `↑` from any chapter-1 page reaches `p-hook`; inputs keep their arrow keys.
- **Do not change** `src/` files except to fix a genuine bug you find (report it); no change to `compute.js` or data.
- Build with `python analysis/scripts/explainer/build_wisp_explainer_html_x2.py` (the README's builder), byte-identical
  rebuild, size budget, strict numerical checks.

## Acceptance

1. All explainer tests pass (report the count), plus the new tests; strict checks exit 0; byte-identical rebuild.
2. `check_wisp_explainer_fit.py`: delivered inventory updated; if the browser is blocked in your sandbox, status
   `blocked` with "browser not runnable here — environment, not the task"; Claude runs it.
3. Short report `codex/reports/REPORT_WP_X11.md`.
