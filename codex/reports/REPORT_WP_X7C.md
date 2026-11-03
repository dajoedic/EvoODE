# WP-X7c report

Status: **blocked — browser not runnable here — environment, not the task** (Umgebung, nicht Sache). Implementation and non-browser acceptance are complete. Pixel fit, screenshots and visual approval remain open.

## Changes

Only the presentation of pages 1–3 changed. The source files are `explainer/wisp/src/index.html`, `app.js`, `pages.css`, `i18n/de.json` and `i18n/en.json`; README, the delivered `dist/wisp_explainer.html`, the existing bilingual DOM harness and a new X7c contract test were updated. No compute.js or scientific data file changed. The four frozen WP-X4 input fingerprints pass the existing acceptance test.

Page 1: the desktop SVG viewBox is now 780 × 260 instead of 780 × 240. The transformed time label has baseline y=246.9, so it is contained in the drawing area. The illustration uses 210 px CSS height, or 190 px below 700 px viewport height. Margins between headline, deck, figure, caption and history are explicit, and the five timeline entries remain. A dashed, translated future-video slot occupies a separate column within the figure; no external media was added. The phone illustration keeps its stacked geometry. The deterministic endless growth/hold loop and visibility/reduced-motion behavior are unchanged and pass the existing harness.

Page 2: two equal-width columns replace the previous unequal columns. The punchline is inside the left parameter column immediately after reset/hint, with hints following it. An empty hints list consumes no height. The chart keeps 240 px CSS height. These are configured dimensions, not browser-measured fit results.

The buttons now use the following coarse increments, separately from the unchanged slider increments:

| Term | ± increment | Slider increment |
|---|---:|---:|
| 1 | 0.1 | 0.01 |
| u | 0.1 | 0.001 |
| u² | 0.001 | 0.00001 |
| u³ | 0.0001 | 0.000001 |
| sin u | 0.1 | 0.01 |
| cos u | 0.1 | 0.01 |

Button updates retain the existing decimal cleanup. Typed inputs use step=any, retain their finite value without rounding or range clamping, and thus accept finer and out-of-slider-range values. The slider retains its range and precision. The bilingual real-page harness checks every button scale, plus/minus, repeated additions without float noise, and fine/out-of-range typed values.

Page 3: a 1.7:1 grid gives the chart about 63% of the available column width. Chart CSS height is 360 px, or 330 px below 700 px viewport height. The right key combines names, matching SVG swatches, formulas and measurement-fit R² values in the requested order: Measurements / Messwerte, Your equation / Deine Gleichung, WISP, True equation / Wahre Gleichung. The noise description reads teaching.sigma. Both WISP and truth formulas begin with the derivative; scalar notation consistently uses u. The former chart legend and detached fit line are omitted on this page. A single translated note explains the measurement-fit scores. On phones the key follows the chart. Headline and idea translations were not changed.

WISP remains a thick 4.5 px solid accent line. Truth is painted last as a thin 1.4 px orange dashed line, above WISP. The reader line remains purple, 2.2 px, with a 7/3 dash pattern; observations remain blue dots. Key and chart share the page-scoped stroke/dot rules, including dark-mode colors. Other chart callers retain their previous drawing order and legends through default options.

## Field origins and score parity

Inspected the real running record `sys0003_ic1_s0.03_r0_n1`; retained evidence is `outputs/wisp_x7c/field_origins.json`.

| Key content | Origin | Real record check |
|---|---|---|
| Noise description | Existing live.teaching.sigma | 0.03 |
| Measurement dots and score target | Existing results.cells[].observed.t / observed.x component 0 | 512 samples; teaching observations match exactly |
| WISP formula | Existing row.active_idxs, row.params and cell.terms through storedEquation | Support [[2, 3]], parameters present |
| True formula | Existing cell.truth through displayTruth | One scalar RHS present; derivative added in presentation |
| WISP/truth curves | Existing cell.curves.t / model / truth | 48 display points |
| Reader formula and curve | Existing browser coefficients, equation and RK4 output | No new scientific record field |
| R² and key elements | Existing browser observationR2/interpolateCurve; new presentation DOM | No new exported field |

The WP-X7b score path is unchanged: full reader simulation before clipping; the same exported model/truth curves interpolated to observation times; the same observationR2 definition. Bilingual DOM checks compare the reader key score exactly with the playground score, and both model/truth scores exactly with the WP-X7b interpolation/R² calculation on the same real records and state. Known-value and invalid-time-grid checks also pass. No scientific result numbers were typed into the page.

## Final validation

Reproduction:

```text
python outputs/wisp_x7c/validate.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The final validation run exited **0**:

- **44 passed, 15174 warnings in 52.46 s**: 41 existing tests adapted/preserved and 3 added contract tests. New live step, precision, derivative, draw-order and score checks run inside the existing bilingual DOM tests. Warnings are the existing NumPy trapz deprecation.
- `check_wisp_explainer_js.py`: **exit 0**; six path comparisons, maximum relative coefficient error **5.82e-13**.
- `check_wisp_explainer_x2.py`: **exit 0**; significance stops at **4, 3, 2**.
- Two final builds: **exit 0**, byte-identical.
- HTML: **11,347,990 bytes**, below **14,000,000**. Scientific data: **14,308,875 bytes**.
- HTML SHA-256: `542b8574f432e640a78b72606c0b10adde7994181052cf057ab021f8138171e7`.

Retained evidence: `outputs/wisp_x7c/validation.json`, `tests.log`, `build_0.log`, `build_1.log`, `numerical.log`, `numerical_x2.log`, `input_hashes.json`, `field_origins.json`, `fit.log`, `fit.json` and `edge_fit.json`.

## Open browser acceptance

The fit checker was attempted. Playwright failed before browser launch with **[WinError 5] Access is denied**. Edge fallback exited **2147483651**, also Access is denied (0x5). Checker JSON: **exit 2**, **0 viewport checks**, **0 screenshots**. The shell exit was 1 with a trailing subprocess traceback. No pixel-fit success is claimed.

Claude must run the fit checker outside this sandbox for all 19 pages in DE/EN at **1366 × 657** and **1366 × 768**, the **76 screenshots**, and actual browser interaction checks. Phone stacking also requires visual inspection. The intended height reductions are implemented; fit at either desktop height remains unverified because the browser is not runnable here — environment, not the task.

All changes remain uncommitted. CURRENT_TASK.md was not edited. No Git operations, scientific-data regeneration, Julia runs, cluster jobs, campaigns, regression/survey runs or manifests were performed.
