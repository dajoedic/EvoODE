# WP-X8 — WISP at work

Implementation complete; browser acceptance blocked by the environment.

## Changes

Page 2 has a third round SVG eye button with German/English show/hide labels,
title and pressed state. It toggles the stored true formula below the live reader
equation and a thin orange dashed clean curve above the dots and below the reader
curve. Reset hides both. The cards and coefficients are unchanged by the eye.
The short desktop chart leaves room for the extra formula. The existing stretched
columns and measured two-pixel alignment gate remain.

Page 3 was rebuilt as “WISP bei der Arbeit” / “WISP at work”: six display cards,
one recorded candidate chart, the current equation, narration, a nine-position
track and round play/pause, next and restart controls. Addition dots are round;
swap/removal dots are diamonds; the choice is a square. The old comparison table,
legend, measurement-fit scores, reader curve and reader-equation hand-over are
removed, together with their tests and obsolete page-3 translation keys/CSS.
Card heights follow the actual challenge cards through ResizeObserver; desktop
columns and gaps match the challenge. Phone layout stacks cards, chart and text.

## Data binding (existing fields checked against real exported records)

| Display | Source |
| --- | --- |
| Page-2 clean line | `live.teaching.t`, `live.teaching.truth` on their stored grid |
| True formula, pages 2 and 3 | Matching `results.cells[].truth`, through existing `displayTruth` |
| Recorded order | `live.featured[0].path`, eight entries |
| Current support | `path[].active_idxs[0]` |
| Addition/swap/removal | Differences between consecutive supports; `origin` stays in the source step record |
| Current equation | `path[].equations[0].basis_indices` and `.coefficients`, formatted to three significant digits |
| Candidate association | `path[].candidate_id` matched to `candidates[].row.candidate_id` |
| Simulated line | `candidates[].curves.t` and `.curves.model[][0]`, with no integration or resampling |
| Final selection | `live.featured[0].chosen`, matched to the recorded path |
| Measurements | `live.teaching.t` and `.observed`, the same measurements used by page 2 |

All are existing exported fields; the only derived presentation fields are
support differences and playback state. No scientific fields were added.
The real run is `sys0003_ic1_s0.03_r0_n1`. Its third step swaps 1 for u;
its fourth swaps u³ for u². Selection returns to `path_004`, step 4.
The DOM tests check each of the eight equations and candidate arrays against
these real records and check every step's translated support-difference narration.

## Timing and lifecycle

Eight path steps take 2,500 ms each. Choice takes 6,000 ms, then loops to step 1:
26 seconds per complete cycle, subject to animation-frame scheduling. During the
first 900 ms of choice all eight exported candidate curves are thin; afterward
only the selected curve is thick. This short reveal also completes when choice
is selected manually, while automatic step advancement remains paused.

Page navigation and document visibility suspend playback and preserve elapsed
time. Manual next, track selection and restart pause autoplay; restart returns
to step 1. Reduced motion initializes at choice with the selected curve visible
and autoplay disabled; controls remain usable.

## Final non-browser acceptance

Command: `python outputs/wisp_x8/validate.py`

- Both builds: exit 0; byte-identical.
- Complete explainer suite, including the real-record swap test: **46 passed**.
- `check_wisp_explainer_js.py`: exit 0; all six cases pass, largest reported
  relative coefficient error 5.82e-13.
- `check_wisp_explainer_x2.py`: exit 0, including the three significance checks.
- HTML: **11,355,044 bytes**, below 14,000,000 bytes.
- SHA-256: `55b0da1cd219cf20d2c2667c6af6da9434afc7f43db4f4714795b0a9d5c3f263`.
- Test warnings: existing NumPy `trapz` deprecation warnings (15,174).

Evidence: `outputs/wisp_x8/validation.json`, `tests.txt`, `build_first.txt`,
`build_second.txt`, `check_wisp_explainer_js.txt`, `check_wisp_explainer_x2.txt`.
The numerical core and all scientific data files were not edited. No Git
operations, campaign runs, cluster jobs or new scientific exports were performed.

## Open browser acceptance — environment, not the task

Final command: `python analysis/scripts/explainer/check_wisp_explainer_fit.py`.
Exit **2**: Playwright fails with `[WinError 5] Access is denied`; Edge fallback
also fails to launch (`Access is denied`, native exit 2147483651). There are
**0 viewport checks and 0 screenshots**. Evidence: `outputs/wisp_x8/fit.txt` and
`outputs/wisp_explainer_checks/wp_x6_fit.json` / `wp_x6_edge_fit.json`.

The fit measurement now includes both eye states and all nine work-page states
in `pages[].variants`; their results contribute to each page's overall `ok`.
The choice screenshot follows the final recorded step. Claude must run the
command outside this sandbox to verify 1366 × 657 and 1366 × 768 in EN/DE,
including flush challenge columns, all formula/narration states and screenshots.
Phone overflow and visual quality are likewise not claimed as browser-verified.

Status: **blocked — browser not runnable here — environment, not the task**
(Umgebung, nicht Sache). All implementation files remain uncommitted.
