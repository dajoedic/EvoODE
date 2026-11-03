# WP-X7e — challenge start and solution comparison

Status: **blocked**, solely because browser acceptance cannot run in this sandbox.
Implementation and all non-browser acceptance checks are complete.

## Changes

- Page 2 starts with six unchecked terms and disabled coefficient controls. Its equation is `du/dt = 0`, its RK4 curve is the constant first observation, and its measurement R² is calculated by the existing function. Reset restores this state; the untouched page-3 reader equation also remains zero. Existing per-term coefficient presets remain available after a term is enabled.
- Native number spinners are suppressed using `appearance`, `-moz-appearance`, and both WebKit spinner selectors. Typed inputs and the separate ± buttons retain their existing behavior.
- The challenge grid stretches both columns. The left column uses grid rows with the card grid consuming available space and the punchline following the icon-button group. There is no language-specific fixed column height.
- Page 3 places the chart above a bordered four-row legend. The legend contains only the four names and their exact SVG line/dot swatches; noise information remains outside it.
- The right side contains the six catalogue blocks in order and R², with rows True/WISP/You. Coefficients use three significant digits and locale formatting. Neutral truth chips, green ✓ chips, orange ✗ chips and dashed missing chips implement the comparison. Tooltips are translated; dark-theme colors are explicit. Negative R² remains visible while its bar clamps to zero.
- Three ordinary formulas follow the table, preserving the stored truth's product form. The requested short caption is present in both languages and marked `data-claim="review"`. At phone widths the chart and legend precede the comparison, which scrolls inside its own box.
- `pages.js` exports the challenge columns' top, bottom and height bounding rects in fit-check results. `check_wisp_explainer_fit.py` requires these measurements and checks both edges within 2 px. A failed column check also fails the overall result.

Page 1 and its illustration/animation were not changed. No Git operations, campaigns, cluster jobs or scientific exports were run.

## Truth coefficients and field provenance

The running cell is selected through the existing featured-running path; the real teaching cell is `sys0003_ic1_s0.03_r0_n1`.

The inspected real `results.json` cell has `truth`, `terms`, `row.active_idxs`, `row.params`, `observed` and `curves`. `truth` is an array of stored expressions, not structured true term coefficients. The benchmark file already read by the exporter has `eq`, `consts` and `substituted`, but no structured true block coefficients. The exporter supplies `truth` from `substituted`.

The running cell therefore uses **path (b)**, exposed as `data-truth-path="stored-polynomial-expansion"` on the table. A restricted recursive-descent parser expands the stored expression:

```text
0.79*x_0*(1 - 0.0134589502018843*x_0)
```

It produces the catalogue coefficients `[0, 0.79, -0.010632570659488598, 0, 0, 0]` at runtime. No true coefficients are supplied as presentation literals. The parser accepts numeric constants, the scalar state, sums, products, parentheses and nonnegative integer powers, with token/degree limits and no executable evaluation. Unrepresentable or unsupported expressions select **path (c)**, `stored-formula-only`: the true formula remains, its chip row is empty, and WISP/reader chips are neutral without support marks. Tests exercise that fallback.

WISP coefficients come from the existing one-based `row.active_idxs`, flattened `row.params` and `terms` catalogue. Reader coefficients come from the existing page-2 `enabled` and `coeff` arrays. These are existing fields/state, not new data fields. The three R² scores remain browser analysis derived from `observed`, `curves` and the reader RK4 output using the unchanged observation-fit/interpolation functions. No new exported data field was introduced.

## Executed validation

Final reproducible command:

```text
python outputs/wisp_x7e/validate.py
```

Evidence: `outputs/wisp_x7e/validation.json`, `tests.log`, `numerical.log`, `numerical_x2.log`, `build_0.log`, `build_1.log` and `input_hashes.json`.

| Check | Result |
| --- | --- |
| Presentation suite, including swap and bilingual real-page DOM harness | **48 passed**, exit 0, 63.99 s |
| Existing tests retained/adapted | 45 |
| New Python tests | 3 |
| Strict numerical JS check | exit 0 |
| Strict X2 numerical/significance check | exit 0 |
| Two final builds | both exit 0, byte-identical |
| HTML size | 11,357,633 bytes, below 14,000,000 |
| Data directory size | 14,308,875 bytes |
| Frozen inputs | all 4 hashes unchanged: `compute.js`, `live.json`, `manifest.json`, `results.json` |

Final HTML SHA-256: `d83e87b603da62e61b020192610a8ff0509d164cd49decbd5a47c000fe8189b0`.

The real-page DOM harness checks empty start/reset, constant initial trajectory, reader-score equality with the page-2 meter, negative-score bar clamping, catalogue and row order, a reader equation with correct/extra/missing blocks, locale coefficients, translated tooltips, real truth expansion to 1e-12 and formula-only fallback. The new parser test independently derives the expected expansion from the stored expression. Layout-contract tests exercise the 2 px boundary and rejection above it. The suite reports 15,174 existing NumPy `trapz` deprecation warnings.

## Outstanding browser acceptance

Attempted:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

Playwright failed with `[WinError 5] Access is denied` while creating its subprocess transport. The Edge CLI fallback also failed with access-denied diagnostics and process exit `2147483651`. The saved checker evidence records exit 2, fallback exit 2, zero viewport checks and zero screenshots; the invoking Python process returned 1 with the asynchronous permission traceback. Copies of the evidence are in `outputs/wisp_x7e/browser_fit.json` and `browser_edge_fit.json`; the original files remain under `outputs/wisp_explainer_checks/`.

**browser not runnable here — environment, not the task**. No pixel fit, theme contrast or phone rendering pass is claimed. Claude must run the command above outside this sandbox to verify EN and DE at 1366 × 768 and 1366 × 657, including the new column-edge check, existing interactions and all 76 screenshots.
