# WP-X17b — chapter-four review fixes

## Result

Implementation and rebuilt HTML are complete. Final presentation suite: **38 passed in 60.86 seconds**. Browser acceptance remains blocked by the environment: Playwright reports **[WinError 5] Access is denied** while creating its transport, and the Edge fallback exits **2147483651**. The browser checker reports **exit 2, zero checks and zero screenshots**. Actual text bounds and chip/label separation at **1366×768** and **1366×657** therefore remain unverified. No browser-fit success is claimed.

## Changes

- Replay uses a single model row above the chart panels, at SVG y=78–108. During Test it shows the pre-round support (including explicit empty/leer in round one); addition updates that row, and removal updates it during clean-up. The separate newcomer chip was removed. Threshold annotations remain at y=132.
- All presentation number adapters use the shared standard-notation locale formatter. German grouping uses spaces and decimal commas; English uses comma grouping. Chapter-four values display 9 311 / 9,311 and 2 932 / 2,932 without exponent notation. The other chart and equation adapters use the same formatter.
- Both chapter-four ratio charts use a common log10 domain derived from all real replay ratios and the recorded threshold: **0.01 to 10,000**, with **seven decade ticks**. There is no zero tick. The threshold line is dashed at **y = 278 − 98 × (log10(6.635) + 2) / 6**, approximately 231.9, on the 180–278 plot. Both languages name the logarithmic axis and explain it in step three. Ratio magnifiers are disabled; linear clean-up costs retain their magnifier.
- Prose and ratio-chart annotations format the same `four.threshold` using `thresholdNumber`, producing exactly **6,635 / 6.635**. Its source remains `live.featured[0].stop_reference.threshold`.
- Every passing round displays its first clean-up probe immediately after addition (3000 ms), then executes the clean-up phase from 5000 ms, including the all-stay probes in rounds one and two. Round five retains the grey End panels.
- The fit checker now samples **71 replay times**, including phase interiors and boundaries. It checks model supports during Test, presence of clean-up threshold lines after addition, logarithmic decade positions, the threshold position and string, absence of ratio magnifiers, exponent strings, and visible chip boxes against chart labels. Only each chip's own sibling text is exempted from box/label collision detection. The existing checker still requests both viewport heights in both languages.

## Files

- `explainer/wisp/src/app.js`
- `explainer/wisp/src/pages.js`
- `explainer/wisp/src/i18n/de.json`, `en.json`
- `explainer/wisp/dist/wisp_explainer.html`
- `analysis/scripts/explainer/check_wisp_stop_scene.cjs`
- `analysis/tests/wisp_slides_dom.cjs`
- `analysis/tests/test_wisp_explainer_x9a.py` (shared formatter dependency and locale-aware parsing)

## Verification

- Final allowed presentation suite: **38 passed in 60.86 seconds**; `outputs/wp_x17b/presentation_tests.txt`. Excludes the base data suite and `test_wisp_explainer_x2.py`; no full `-k wisp` run.
- Geometry harness passes in **both languages**: deterministic seek, finite/nonnegative geometry, equal plot sizes, removals, seven fixed decade ticks, logarithmic threshold position, no ratio zoom, visible clean-up probes, and actual visible model chips against the real pre-round supports at **110 test-phase samples** (22 in each of five rounds).
- Full DOM harness passes in **both delivered languages**. It inspects actual visible model chips at four test-phase times per round, probes at six times in every passing round, the exact threshold in chart and prose, and chart text without exponent strings. Existing replay, looping, end-hold and reduced-motion checks continue to pass. Fixtures remain derived from the shipped real teaching record.
- Numerical checker: **six reference cases pass**, largest relative coefficient error **5.82e-13**; `outputs/wp_x17b/numerical_checks.txt`.
- `node --check` passes for `app.js`, `pages.js`, `wisp_slides_dom.cjs`, and `check_wisp_stop_scene.cjs`.
- Build-time live-path guards pass. Immediate rebuild is **byte-identical**, **11,490,224 bytes**.
- SHA-256: **1ab3a28dcddf4270546f879074085eb8ce9ceb6c01bb13358e742a05f83ddc22**; `outputs/wp_x17b/rebuild.json`.
- Failed browser launch evidence: `outputs/wp_x17b/browser_fit.txt`. No layout measurements or screenshots were obtained in this session.

## Reproduce

```powershell
$tests = @(rg --files analysis/tests | Where-Object { $_ -match 'test_wisp_explainer_x.*\.py$' -and $_ -notmatch 'test_wisp_explainer_x2\.py$' })
python -m pytest $tests -q -p no:cacheprovider
node analysis/scripts/explainer/check_wisp_stop_scene.cjs
python analysis/scripts/explainer/check_wisp_explainer_js.py
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The last command must still run successfully in Claude's browser-capable environment to close acceptance. Scientific input files, numerical core, and CURRENT_TASK.md were not modified. No exports, Julia, cluster jobs, campaigns, Git operations, staging or commits were performed. Files remain in the working tree.
