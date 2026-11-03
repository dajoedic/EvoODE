# WP-X7b report

Status: blocked ? browser not runnable here ? environment, not the task. Implementation and non-browser acceptance are complete; pixel fit and screenshots remain open.

## Delivered changes

The presentation retains 19 pages. Page 1 uses a larger dish and growth curve side by side, a centred caption immediately below, and all five history stations. The SVG has a desktop viewBox of 780 ? 240 and a stacked phone viewBox of 400 ? 480. Desktop illustration height is 280 px, or 260 px below 700 px viewport height. These are configured sizes, not measured browser fit results.

The deterministic illustration uses the existing seed 731 and the existing illustrative logistic function. Each cycle grows for 6000 ms and holds the final state for 1500 ms, then resets to the initial state. Animation time advances only while the illustration is visible and the document is not hidden. IntersectionObserver stays connected for subsequent departures and arrivals; browsers without it use native scroll/resize visibility checks. Reduced motion renders the final state without scheduling animation. The replay button and its translation key x7_replay were removed.

Page 2 uses a three-column, two-row card grid on desktop and two columns on phones. The deck, card grid and chart have larger gaps. All six cards use the same layout classes, equal fractional grid rows, and permanently mounted coefficient controls. An inactive term disables the slider, numeric input and both increment buttons and lowers the controls' opacity; it removes no layout content. The two structure/parameter labels occur once in a shared legend. Reset and hint are small round inline-SVG buttons with translated title and aria-label attributes in DE and EN. Hints remain ordered and the bulb disables after the third hint. The reader equation continues to update page 3 on every change, including reset and the untouched initial state.

Page 3 draws the reader's current curve in purple with a dashed line, alongside the truth, observations and WISP model. WISP is drawn last and retains its dominant 4.5 px stroke; the reader stroke is 2.2 px. All three equation boxes remain. Three measurement-fit R? values are calculated at runtime below the chart, under the exact requested bilingual label.

Changed source files: src/index.html, src/app.js, src/pages.css, src/i18n/de.json and src/i18n/en.json under explainer/wisp; README updated; dist/wisp_explainer.html rebuilt. Existing tests and DOM harnesses were adapted and analysis/tests/test_wisp_explainer_x7b.py was added. No compute.js or scientific data file changed; all four frozen WP-X4 input SHA-256 fingerprints still match.

## Removed navigation links

1. p-hook ? p-challenge: the bridge ?Jahrhundertelang war das Handarbeit. Probier es selbst.?, class hook-bridge, translation key x7_bridge. The link and its DE/EN keys were removed.
2. p-challenge ? p-solution: ?Zeig mir, was WISP findet?, id challenge-reveal, translation key x6_reveal. The link and its DE/EN keys were removed.

These were the only static next-page-only links outside the pipeline maps. The results-explorer jump, catalogue return to the challenge, glossary return, pipeline maps, global page index and pipeline navigation remain. The DOM test inventories every page and rejects a static immediate-next-page link outside a pipeline map. The challenge-to-solution handoff is exercised through wheel navigation.

## R? definition and real field origins

The shared observationR2 function is the existing playground definition:

`R? = 1 - sum((prediction[i] - observation[i])?) / sum((observation[i] - mean(observation))?)`.

The playground and solution use this same function. The solution reuses the full reader simulation output, rather than running a second numerical implementation: existing RK4, initial value from the first observation, measurement time grid, existing divergence stopping, and the same display clipping at twice the maximum absolute observation. As before, the score uses the full prediction before display clipping. Nonfinite fits are unavailable, not clamped; only the playground meter's visual fill is clamped.

The source record was inspected before implementing the presentation fields. Evidence is in outputs/wisp_x7b/time_base.json:

| Presentation input | Existing source field | Verified real record |
|---|---|---|
| Reader time grid | live.teaching.t | 512 strictly increasing times, 0 to 10 |
| Reader start and target observations | live.teaching.observed | Exactly equal to observed.x component 0 in the running result cell |
| Solution observation times and values | results.cells[].observed.t and observed.x | Same 512 times and observations as teaching |
| WISP and truth display curves | results.cells[].curves.t, model and truth | 48 strictly increasing times, 0 to 10 |
| Running cell selection | live.featured[].roles and cell_id | sys0003_ic1_s0.03_r0_n1 |
| Reader fit/state | Browser presentation state | No new exported record field |

The exported WISP/truth display curves are linearly interpolated onto the 512 observation times. Exact grid hits retain their original value. No extrapolation is performed: missing, malformed, nonincreasing or out-of-range time grids produce an explicit unavailable-time-base message. Nonfinite/null curve values propagate as unavailable fit. The real running cell's time bases cover the same interval and can be compared.

These fits describe the exported display curves (48 points, already thinned/rounded by the existing exporter) and the reader's equation against the noisy measurements. They are presentation computations and do not replace, modify or reproduce the stored reconstruction/generalization scores. Those stored scores and both weighting metrics remain unchanged.

## Validation

Final complete run: **41 passed, 15174 warnings in 52.82 s**, comprising the 37 adapted existing tests plus 4 new tests. Warnings are the existing NumPy trapz deprecation. Evidence is from the final successful run, not an earlier partial run.

The bilingual real-page DOM harness exercises delayed animation visibility; growth and full-state hold; automatic restart; off-page and hidden-tab pause/resume; reduced-motion deterministic final-state equality; the no-IntersectionObserver visibility fallback; unchanged card layout and mounted disabled controls across toggles; both icon translations and SVGs; ordered hints and disabled bulb; scroll-preserved reader equation; the initial reader curve and subsequent updates; three solution scores; and reader page-3/page-2 R? equality for a fixed equation. Independent known-value tests check R? = 1, 0 and -3, interpolation and invalid/nonfinite grids/values. Existing richer-schema swap, i18n, provenance, whitelist, strata, both metrics and wheel-routing checks pass. Older minimal harnesses were extended with the browser APIs used by the illustration.

Both strict numerical checkers exit **0**. Six path comparisons pass; maximum relative coefficient error is **5.82e-13**. The three significance-rule checks stop at steps **4, 3, 2**.

Two final builds exit **0** and are byte-identical. Final HTML size: **11,343,240 bytes**, below **14,000,000**. Scientific data size: **14,308,875 bytes**. Final HTML SHA-256:

```text
8258782c770ad21b28bf1a15fe312823c404680dbb5e90af57ab6bfd22216d7f
```

Retained evidence in outputs/wisp_x7b/: validation.json, build_0.log, build_1.log, numerical.log, numerical_x2.log, tests.log, input_hashes.json, time_base.json, fit.log, fit.json and edge_fit.json.

Reproduce the successful non-browser acceptance:

```text
python outputs/wisp_x7b/validate.py
```

## Open browser acceptance

Attempted during this task:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

Playwright fails before browser launch with **[WinError 5] Access is denied**. Edge fallback exits **2147483651** with **Access is denied (0x5)**. The checker's JSON reports exit **2**, **0** viewport checks and **0** screenshots. The shell process returned **1** with a trailing Playwright subprocess traceback. The checker's existing WP-X6-named evidence files were copied into this task's evidence directory.

Claude must run the fit checker outside the sandbox for DE/EN fit at **1366 ? 657** and **1366 ? 768**, the 76 screenshots and actual browser interaction checks; phone stacking also requires visual inspection. No successful pixel fit or visual approval is claimed. This is **Umgebung, nicht Sache**.

All files remain uncommitted. CURRENT_TASK.md was not edited. No Git operations, scientific-data regeneration, Julia runs, cluster jobs, campaigns, regression/survey runs or scientific manifests were performed.
