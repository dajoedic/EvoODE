# WP-X18c — WISP explorable: chapter 5 recap layout
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-05. Follows WP-X18b (uncommitted). Claude made small edits after X18b in `explainer/wisp/src/app.js`
and `pages.css` (recap section count now from the record field `live.featured[0].path[0].equations[0].n_rows` with
integer formatting — keep that; recap y-positions, loop label position, chip grouping and font size were tried and
are free to be replaced). All explorable rules and the test policy stay in force.

## Problem

`c5-recap` still fails the browser fit checker: adjacent text lines overlap (bounding boxes of name / description /
result touch), and the in-page check requires every recap text at ≥ 14 px *rendered* size. Eight boxes with three
lines each do not fit into the 800×480 stage viewBox with ≥ 14 px rendered text and non-overlapping line boxes
(system-ui line boxes are ~1.33 em high; the stage is scaled ~0.92 at 1366 px width).

## Task

Make the recap fit without overlaps at both viewport heights (768 and 657) and both languages, keeping its content
(stage name, one-line description, live result; loop grouping of test / add / clean-up with the „Runde, bis der
Test scheitert“ label; the four candidate supports as chips, visibly grouped per candidate; one walking highlight).
You may choose the means, for example: render the recap as an HTML grid layered over the stage instead of SVG text;
or two columns of boxes; or move the descriptions into the page's left text column as a numbered list and keep
name + result in the boxes. Do not shrink text below 14 px rendered, do not drop the live results. Keep the
mini-graphics only if they still fit.

Tests: the fit checker reports zero overlaps and `chapterFiveOk` for every sample of `c5-recap`; the existing recap
tests still hold (non-empty texts, section count = record `n_rows` formatted as an integer — 2 529 / 2,529 —, one
highlight, loop label).

## Deliverables

Source changes, rebuilt `explainer/wisp/dist/wisp_explainer.html`, tests; `codex/reports/REPORT_WP_X18C.md`;
`codex/STATUS.md` entry. Do not commit. No exports, no Julia, no cluster jobs.
