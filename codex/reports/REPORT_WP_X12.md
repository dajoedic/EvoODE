# REPORT WP-X12 — chapter-one scroll story

Implementation is complete and remains uncommitted. Final acceptance is **blocked by the environment**: `browser not runnable here — environment, not the task`. The required Edge/Playwright pixel and viewport checks need to run outside this sandbox.

## Architecture

Introduction content and hidden later-chapter sections are retained. Thirteen pages are visible: two introduction pages and eleven chapter-one steps. All page transitions use the existing 720 ms vertical scroll tween. Down, PageDown and Space advance one page; Up and PageUp return one page. Left/right have no page-navigation action. The existing input, drag, modal, native-scroll and wheel-inertia guards remain. Sub-step dots are a vertical column on the right.

`app.js` creates one persistent `#c1-stage` SVG outside the scrolling sections. Each chapter section declares `data-stage`. `pages.js` passes the active state to `WispChapterStory.enter`. The desktop stage occupies the right side, with text on the left; the phone fallback places the stage below the text. Existing controls for measurement/change toggles, window length, noise centre and block selection are removed. Only S7's optional coefficient slider remains, revealed after its animation.

The SVG has a fixed primitive topology. Numeric coordinates and opacities interpolate with a smoothstep easing over 900 ms, preserving nodes across states. Paths retain fixed vertex counts. Sequences use requestAnimationFrame; `window.WispStoryClock` can inject `now`, `request` and `cancel`. The DOM harness installs this clock and steps time. Entry replays a sequence; leaving finishes it and cancels its frame before moving on. Reduced motion renders the final state immediately. There are no random animation inputs. Error-curve samples and block minima are computed once rather than recomputed every frame.

## State and timing

Times include the 900 ms transition into the state.

| Step / state | Total | Final state / sequence |
| --- | ---: | --- |
| S1 `data` | 900 ms | 512 observed dots over t = 0 to 10 |
| S2 `noise-visible` | 2300 ms | Clean curve draws over 900 ms, then all observed-to-clean sticks appear over 500 ms |
| S3 `slope` | 3800 ms | Marker and tangent traverse the clean curve over 2900 ms, with numeric slope readout |
| S4 `secants` | 3900 ms | 511 neighbour slopes fill a lower panel in 3000 ms; triangles shown for every eighth pair; dots fall into the lower panel |
| S5 `windows` | 6100 ms | Zoom into the stretch starting at t >= 2; neighbour secant, then lengths 2, 4, 8, 16; five slope dots; zoom out and show 31 non-overlapping longest-window slopes |
| S6 `error-empty` | 2900 ms | 31 displayed change residuals build over 2000 ms; zero prediction and 100% error |
| S7 `fit` | 3400 ms | Constant coefficient approaches its least-squares optimum over 2500 ms; residuals, error curve and marker update; optional slider appears |
| S8 `every` | 6500 ms | Six blocks in catalogue order at 800 ms each; predictions blend across block changes, values fly into slots; 800 ms rank sort and transition to the winner |
| S9 `noise-estimate` | 7300 ms | Zoom in; five consecutive 9-point cubic fits and deviations; zoom out; estimated +/- sqrt(variance) band |
| S10 `percent` | 900 ms | Winner's stacked noise / explained / remaining bar, six shares, original explanatory content and fallback |
| S11 `solution` | 900 ms | Winner's prediction, large computed equation, original next-chapter content |

All coefficients, error values and shares use the existing full design and first-step model. The existing recorded-first-support assertion remains a build gate. The design includes lengths 1, 2, 4, 8, 16 and 2529 windows; the illustration shows 31 non-overlapping windows at length 16. S5 first shows the neighbour baseline separately, then the four longer lengths. This avoids accidentally repeating length 1 and skipping length 16 before zooming out.

## S9 values and provenance

No scientific data or `compute.js` was edited. Values were read/computed from the real teaching cell:

| Quantity | Fraction | Display |
| --- | ---: | ---: |
| Mean estimated relative noise | 0.029342693219205268 | 2.9% |
| Added relative noise | 0.03 | 3.0% |
| Estimated empty-support noise floor | 0.7155645372738232 | 71.6% |
| Presentation-only actual noise floor | 0.7687703353548505 | 76.9% |

Field inventory: times are `live.teaching.t`; measurements are `live.teaching.observed`; the clean reference is `live.teaching.truth`; added noise is `live.teaching.sigma`; design lengths are `live.windows`. These are existing exported fields. Variance comes from the unchanged `WispCompute.noiseVariance`. The relative estimate is the mean of sqrt(variance[i]) / abs(observed[i]). The estimated floor uses the existing `noiseFloor` and full-design target norm. The actual floor is a new presentation calculation: sum over every design window of (noise[end] - noise[start]) squared, divided by the squared norm of b, where noise = observed - clean. It is labelled as a presentation calculation in both languages.

The local cubic presentation reuses the former noise-page implementation with the scaled degree-three basis and existing `leastSquares`; it matches `noiseVariance`'s local fit. The harness independently compares it against NumPy least-squares cubics at both boundaries and at all five demonstrated centres. Example centres are zero-based indices 171–175 (points 172–176); their signed deviations are 0.642113971404271, -1.0000096251406632, -0.029117220952123546, 0.05981389828190942 and 1.2237145226625827. The sequence appends the corresponding computed values to the SVG list.

## Validation

- Build: exit 0. Two sequential builds after the final test suite are byte-identical: 11,394,522 bytes (budget 14,000,000); SHA-256 `4656285fb4d7a80c20c31d792babf5437c5473811958299519a2d173e2b37f95`. Evidence: `outputs/wisp_explainer_checks/x12_rebuild.json`.
- Presentation tests: `python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp --tb=short` exited 0: **51 passed, 333 deselected**, 132.08 s. The 15,174 NumPy `trapz` deprecation warnings are from the existing analysis implementation. Output: `outputs/wisp_explainer_checks/x12_tests.txt`.
- `check_wisp_explainer_js.py`: exit 0, all six illustration/reference paths checked; maximum relative coefficient error 5.82e-13.
- `check_wisp_explainer_x2.py`: exit 0, including all three significance-rule references.
- DOM assertions cover bilingual state order, hidden-page links, a keyboard-only walk to S11, vertical wheel/keys, inert horizontal keys, one persistent SVG, all 512 noise sticks and rendered endpoints, all 511 neighbour slopes and rendered coordinates, all 31 longest-window slopes and rendered coordinates, S6's full error bar, S7 coefficient/error minimum and optional slider, six S8 minima/ranks/recorded winner, S9 independent cubics/variance/estimate/floor/actual/deviation labels, reverse entry, reduced motion, interruption, replay and intermediate movement. Intermediate S5 explicitly checks the length-16 secant and all five slope examples.
- Fit checker: exit 2. Playwright fails with `[WinError 5] Access is denied`; Edge fallback also exits 2 (2147483651 on its viewport probe). It produced **0 viewport checks and 0 screenshots**, so no pixel fit is claimed. Evidence: `wp_x12_fit.json`, `wp_x12_edge_fit.json` and `x12_fit_console.txt` under `outputs/wisp_explainer_checks/`.

Run the remaining acceptance outside the sandbox:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

This checks the actual delivered inventory in DE/EN at 1366 x 657 and 1366 x 768, captures each visible page, retains the page-two column checks, and exercises the keyboard-only story plus phone stage fit. `CURRENT_TASK.md` was not edited; no Git operations were performed.
