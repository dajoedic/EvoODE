# WP-X16b — chapter-three review fixes

Implementation and allowed non-browser checks are complete. **Acceptance remains blocked: environment, not implementation** (Umgebung, nicht Sache). The required browser result of zero label overlaps could not be measured: Playwright fails before launch with `PermissionError: [WinError 5] Access is denied`; the Edge fallback exits 2147483651. No screenshot or pixel-fit success is claimed.

## Changes

- Addition now moves existing chips into their slots during the first 900 ms, then fades in the newcomer over the next 900 ms. This also fixes overlaps at the early replay offset that previously appeared at 15300 ms. Removal fades the leaving chip completely during 600 ms, compacts survivors during the following 600 ms, then holds the completed removal for 2000 ms before probing again.
- Both removal scenes now last 16000 ms. The first probe starts at 1800 ms; the removal decision starts at 7200 ms; survivors finish moving at 8400 ms; the repeated probe starts at 10400 ms and finishes at 14000 ms. The common 3000 ms replay hold remains. The first probe's complete bars remain readable through the decision hold.
- The magnifier is driven by the general condition `threshold < 0.1 * maximum` and appears from probe start through the decision and repeated probe. It uses [0, 2.5 × threshold], its own axes and titles, the same live costs, clipped bar heights with cut marks, the dashed threshold and the nearest bar's numerical value. Both probes retain the same full-chart axis and inset range, so neither requires a discontinuous rescale.
- Candidate rows in both comparison and next-step scenes use comma-separated blocks. Equation multiplication between coefficients and terms remains mathematically appropriate.
- The live refit panel now uses chapter two's identical `x12_axis_slope` and `j157` titles: the dots are observed weak-window rates, the curve is the weak-fit predicted rate, both against window midpoint time. Chapter two already has those titles.
- Step seven now shows gains for additions in rounds one through four plus the next best block, `sin u`, on the same explained-share normalization. The fifth bar is outlined and labelled “noch nicht genommen” / “not taken yet”. The y-range is zero to the greatest live gain. No dashed line or stopping rule appears.
- Updated the requested teaching-system wording in German and English.
- Fixed persistent scene styling so revisiting chapter three from chapter two and reduced-motion end states remains deterministic.

Changed sources: `explainer/wisp/src/app.js`, `pages.js`, `pages.css`, both `i18n/*.json`; rebuilt `explainer/wisp/dist/wisp_explainer.html`. Tests are extended in `analysis/tests/wisp_slides_dom.cjs`. The browser fit checker uses the updated `pages.js` sample tables and now also checks magnifier conditions/costs, removal hold, model separators and the five live gains. Samples include 300/600/899 ms during addition, 7500/7799/8100 ms during removal, 9400/10399 ms during the hold, 10400 ms at the repeated probe, 15300 ms and the replay offset.

## Data and numerical evidence

No new record fields or numerical algorithms were introduced. Fixtures continue to use the real teaching export. Existing record fields are `live.teaching.t` and `observed`, `live.featured[0].path[*].active_idxs[0]`, and `truth_support[0]`. Existing configuration supplies `windows` and `backward_fraction`. Presentation-derived `thirdModel.rounds[*].addition`, `gain`, `threshold`, `probes[*].costs` and `next.gain` supply every chart value; these are analysis/presentation quantities, not raw record columns. The numerical core and fitting denominator are unchanged.

All values below are percentage points on chapter two's explained-share scale. Term indices are zero-based catalogue indices. The last column is the inset upper bound when an inset is needed.

| Round | Added term index | Gain | Threshold | Inset upper bound |
|---|---:|---:|---:|---:|
| 1 | 0 | 52.894313818 | 26.447156909 | 66.117892273 |
| 2 | 3 | 21.263755725 | 10.631877863 | 26.579694657 |
| 3 | 1 | 6.453750885 | 3.226875442 | 8.067188606 |
| 4 | 2 | 1.656528782 | 0.828264391 | 2.070660978 |

The next best gain is 0.296279119 percentage points, term index 4. Raw numbers from the final successful presentation suite are retained in `outputs/wp_x16b/live_numbers.json`.

## Verification

- Final allowed presentation suite: **35 passed in 98.45 s**. Evidence: `outputs/wp_x16b/presentation_tests.txt`. Includes English/German real-export scene execution, live inset costs and clipping, condition/visibility, both probes and the removal hold, 50-ms chip-spacing checks during addition/removal, model separators, five live gain heights, shared fit-axis wording, replay, persistent SVG and reduced motion.
- `python analysis/scripts/explainer/check_wisp_explainer_js.py`: **6 reference cases pass**, greatest relative coefficient error **5.82e-13**. Evidence: `outputs/wp_x16b/numerical_checks.txt`.
- Build guards pass: six single-block fits, five joint refits, four FoBa supports/repeated probes/truth.
- `node --check` passes for `app.js`, `pages.js` and `wisp_slides_dom.cjs`.
- Immediate rebuild: **byte-identical**, 11475033 bytes. SHA-256: `b9fdbc8c3002603040a7dc089e4c7c1f970e2ed41bb244649208d52d3d99337e`. Evidence: `outputs/wp_x16b/rebuild.json`.
- Browser fit checker: **blocked before measurement**. Evidence: `outputs/wp_x16b/wp_x12_fit.json` (exit 2, zero checks/screenshots) and `wp_x12_edge_fit.json`. Browser geometry and zero text overlaps remain the sole open acceptance point.

Reproduce the allowed suite in PowerShell:

```powershell
$tests = @(rg --files analysis/tests | Where-Object { $_ -match 'test_wisp_explainer_x.*\.py$' -and $_ -notmatch 'test_wisp_explainer_x2\.py$' })
python -m pytest $tests -q -p no:cacheprovider
python analysis/scripts/explainer/check_wisp_explainer_js.py
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
```

Outstanding browser acceptance, in an environment where Edge/Playwright can launch:

```powershell
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

No Git operations, commits, exports, Julia execution, cluster jobs or full `-k wisp` suite. `CURRENT_TASK.md` was not modified.
