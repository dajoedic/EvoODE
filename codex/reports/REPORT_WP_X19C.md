# WP-X19c - browser acceptance fixes for chapters 6-8

## Cause of the reported text failures

The supplied `outputs/wisp_explainer_checks/wp_x12_fit.json` contains 592 chapter 6-8 samples across both languages and both viewports. **0 have `exponent: true`; 0 have `rawNames: true`.** These fields are violation flags, and the existing `ok` expression correctly requires `!exponent && !rawNames`. Treating their `false` values as failed checks inverted their meaning outside the in-page checker. Neither predicate was weakened or inverted. The supplied browser evidence already rules out these two predicates as causes of the failing pages; there is no data/exporter defect to fix.

The actual overlap failures are 164/212 samples for c6-rounds, 136/172 for c7-rounds, and 16/16 for c6-stop (316 total). The remaining samples on the two round pages pass. The axis title overlaps ticks, adjacent 20-unit rows overlap, and the last rows can collide with the fixed footer. The same evidence identifies two other failures that the task summary attributed to the text flags: c6-system and c6-orbit each have 16/16 samples with a left-overflowing y-axis label (`x`, `Prey x` / `Beute x`); c8-comparison and c8-close each have 16/16 samples with undersized table text. The generic table-cell rule specifies 11 px even though the table parent specifies 17 px.

The complete per-page/language/viewport audit is `outputs/wp_x19c/input_fit_audit.json`, derived from the existing browser JSON without overwriting it.

## Changes

- Ratio/cost lists now use 25 SVG units of row pitch with 17-unit text (1.47 em). One shared axis title sits at y=24; tick labels sit at y=60. Bar rows begin at y=78, with label baselines at y=93 and increments of 25. The footer is 37 units below the last row label in the longest column. SVG height follows the longest column instead of reserving a full-height panel for short clean-up lists. The ratio SVG's 330 px height cap is removed so it cannot compress the text below the intended size.
- Both replay status text and ratio threshold footers use chapter four's existing `thresholdNumber`: German 6,635 / English 6.635. Clean-up costs retain their separate gain formatter. The final failed-test hold continues to show test ratios and their threshold, including during what would otherwise be the clean-up time interval; there is no clean-up round after stopping.
- Wide-label chart y-axis titles move from x=14 to x=28 to contain the enlarged labels. Chapter 6-8 table cells explicitly use 17 px on desktop.
- `WispSlides.exampleLabels`, `exampleTextIssues`, and `exampleSamples` are shared by the in-page fit checker and the existing Node DOM harness. They preserve the original selectors, predicates, violation-flag semantics, and sampling schedule. No acceptance criterion was relaxed.
- The Node harness reflects the `.hidden` property into the HTML attribute, as a browser does. Without that reflection, panels moved from their initially hidden markup could be incorrectly excluded by `[hidden]`. Positive controls caught this harness issue. Tests inject a mounted exponent/raw-name label and require both violation flags to become true, then move it under a hidden ancestor and require both to become false. Locale numbers and x·y are negative controls.
- The harness enters all 15 actual chapter 6-8 pages and checks their mounted text at 148 samples per language (296 total). It also checks row/title/footer spacing in SVG coordinates and threshold captions. These coordinate checks do not replace browser text bounds.

Only presentation source, the existing harness, the rebuilt HTML, this report and STATUS.md were changed for this work package. Scientific data and exporter source were not edited. No Julia, browser, Git operation, cluster job, campaign or numerical regression run was invoked. CURRENT_TASK.md was not edited. Changes remain uncommitted.

## Validation

- Final HTML build: exit 0, 6.328 seconds; `outputs/wp_x19c/build.log` and `build.json`.
- Final direct Node acceptance runs: exit 0 in English (4.485 seconds) and German (4.516 seconds), 15 scenes / 148 samples each; `outputs/wp_x19c/node_en.log`, `node_de.log` and their JSON run records.
- Iterative presentation-only pytest selection: 3 passed, 6 deselected in 25.12 seconds; `outputs/wp_x19c/fast_tests.log`. The subsequent final direct Node runs and full suite include the final code.
- Full suite, run once at the end: `python -X utf8 -m pytest analysis/tests -k wisp -q -p no:cacheprovider`: **71 passed, 333 deselected, 30,348 warnings in 331.48 seconds**. Wrapper exit 0, 334.266 seconds. Full output: `outputs/wp_x19c/full_wisp.log`; command/exit/timing: `outputs/wp_x19c/full_wisp.json`. Existing warnings are retained in the log.
- Final assembly verification: all three changed presentation sources are present verbatim in the shipped HTML. No browser execution was attempted.

## Browser handoff

As explicitly assigned in CURRENT_TASK.md, Claude reruns the geometric fit checker. No fresh browser result or screenshot was produced in this session, so zero pixel overlaps / final viewport fit are not asserted. Recheck both 1366x768 and 1366x657 in both languages, including the three bar pages and the four additional pages identified above:

```powershell
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The final HTML is 12,921,377 bytes, SHA-256 `8652c7a00ace0f84797fb7906772f96d9b19bc0045ea5f8c7550370cf15e05dc`. It contains the current app.js, pages.js and pages.css verbatim; artifact hashes are in `outputs/wp_x19c/final_artifacts.json`.
