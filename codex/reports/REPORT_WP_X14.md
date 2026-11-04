# WP-X14 — Chapters one and two

Implementation complete; **blocked only on browser fit acceptance (environment, not implementation)**. All changes remain uncommitted. CURRENT_TASK.md and the results contract were not edited.

## Changes

- Chapter one now has 11 steps, ordered data → slope → visible noise → secants → lengths → empty error → fit → every candidate → combined noise explanation/estimate → shares → solution. Chapter two has 5 steps, with joint fitting and the remaining candidates on one page. Eyebrows, dots, progress, page anchors and tests follow these inventories.
- The green reference slope has a translated stage label and an explanation using the slope step's wording. Existing noise-free reference geometry is reused.
- Lengths come from LIVE.windows. At most four uniformly spaced indices of its sorted unique values are selected, including both endpoints (rule documented in code). The current real configuration selects 1, 2, 8 and 16 sampling intervals. Each cloud is drawn, held and retained with its own colour and translated legend. The final comparison holds before replay.
- The combined noise step holds its initial explanation from 900 to 4900 ms before starting the estimation phase. Its second paragraph becomes prominent at 4900 ms. One current deviation and one falling dot replace the list. The sum grows below the plot; the final state retains all 512 measurements, the estimated band and the full existing noise-floor sum.
- The joint example finishes at 3900 ms and holds until 7900 ms (4000 ms). Its second paragraph then becomes prominent; the four remaining candidates follow in catalogue order, with the example's bar retained. Both chapters finally sort by explained share, largest first, and highlight the winner. Text is hidden briefly while bars cross during sorting to avoid overlapping row labels.
- The persistent SVG topology, interrupted/reverse transitions, reduced-motion completion, bilingual strings and neutral chapter-two claims remain covered by the real-record DOM harness. Fit samples cover the new length cycle, both merged pauses, falling deviations and intermediate/final ranking states.

## Acceptance on the final source

Commands and complete logs are under `outputs/wisp_x14/`; `validate.py` reproduces this run.

| Check | Result |
| --- | --- |
| HTML assembler, twice | exit 0 both times; byte-identical |
| `python -m pytest analysis/tests -k wisp -q -p no:cacheprovider` | exit 0; 54 passed, 333 deselected |
| `python analysis/scripts/explainer/check_wisp_explainer_js.py` | exit 0; all illustration and real-record comparisons pass |
| `python analysis/scripts/explainer/check_wisp_explainer_fit.py` | exit 2; browser startup blocked |

HTML size: 11438140 bytes. SHA-256 of both builds: `bb07b940d5aa268ddf2f31e346fc4cc40eb1dffcf1cc43aeed2b042482bae60b`.

The test run reports 15174 existing NumPy `trapz` deprecation warnings. The largest relative coefficient discrepancy printed by the strict JS check is 5.82e-13 for the teaching record.

Playwright fails with `PermissionError: [WinError 5] Access is denied`; the Edge CLI fallback exits 2147483651 before producing fit measurements. See `outputs/wisp_x14/fit_acceptance.txt`. No viewport, SVG-label-overlap, annotation/data-overlap or screenshot pass is claimed. Claude must run the fit command above outside the sandbox to finish that acceptance point.

Numerical inputs remain the existing real teaching record (`teaching.t`, `observed`, `truth`, `sigma`), LIVE.windows and the recorded featured path's supports/equation coefficients. Noise variance, normalized endpoint contributions and joint fits reuse the existing computation functions.
