# WP-X19c — WISP explorable: chapters 6–8 browser acceptance fixes
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-05 evening. Follows WP-X19b (uncommitted, report `codex/reports/REPORT_WP_X19B.md`). The redesign is
good. Claude ran the browser fit checker (`python analysis/scripts/explainer/check_wisp_explainer_fit.py`, evidence
`outputs/wisp_explainer_checks/wp_x12_fit.json`, screenshots `outputs/wisp_explainer_checks/pages/*_p-c6-*`, `*_p-c7-*`,
`*_p-c8-*`); it fails on these pages and checks (variants = samples × 2 languages × 2 viewports):

| page | failing checks |
|---|---|
| p-c6-rounds (164 variants) | `exponent`, `rawNames`, `labelOverlaps` |
| p-c7-rounds (136) | `exponent`, `rawNames`, `labelOverlaps` |
| p-c6-stop (16) | `exponent`, `rawNames`, `labelOverlaps` |
| p-c6-system, p-c6-orbit, p-c8-comparison, p-c8-close (16 each) | `exponent`, `rawNames` |

1. **`exponent` / `rawNames` fail on every chapter 6–8 page, including pages whose visible text has neither** (e.g.
   c6-orbit). Find out whether visible text really contains exponent notation or raw catalogue names (check hidden
   but opacity > 0 nodes, `aria-label`s, `<title>` elements, data labels of other scenes left mounted on the shared
   stage) or whether the in-page check (`pages.js`) is wrong (inverted flag, scanning hidden nodes, regex matching `x·y`
   or a locale string). Fix the cause, not the check, unless the check is demonstrably wrong; report which.
2. **`labelOverlaps` in the bar lists** (c6-rounds, c6-stop, c7-rounds): rows are ~19 px apart with 14 px text whose
   line box is ~18.6 px, and the axis title „Gewinn / Rauschgewinn · logarithmisch“ collides with the tick labels
   (`0,01`, `1`, `100`, `10 000`). Give the rows enough pitch (≥ 1.4 em) or fewer rows per panel, and put the axis
   title above the ticks with clear spacing. Must fit at 1366×768 and 1366×657.
3. **One threshold format.** c6-rounds shows „Testschwelle 6,635“ at the top and „Schwelle = 6,64“ under each panel.
   Use the single threshold formatter of chapter 4 everywhere (6,635 / 6.635).
4. You cannot start a browser in your sandbox. To make the in-page check testable without one, reuse the existing
   Node DOM harness (`analysis/tests/wisp_slides_dom.cjs`) to evaluate the same `exponent` / `rawNames` predicates over
   the mounted text of every chapter 6–8 scene at its sample times, and assert them in a fast test. The geometric
   overlap check needs the browser — Claude reruns it.

Test policy: fast presentation tests while iterating; the full `-k wisp` suite once at the end (~5 min); no Julia,
no exporter changes unless item 1 traces into the data.

## Deliverables

Source changes, rebuilt HTML, tests; `codex/reports/REPORT_WP_X19C.md` (cause of item 1, what changed, test results);
`codex/STATUS.md`. Do not commit.
