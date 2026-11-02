# WP-X4 report

## Page plan (written before implementation)

| ID | EN | DE | Step | Content |
|---|---|---|---|---|
| p-hook | Which law made these data? | Welches Gesetz steckt in den Daten? |  | Problem, measurements, motivation |
| p-solution | An equation from measurements | Eine Gleichung aus Messungen |  | Stored model and true equation; verified model curve |
| p-headline | How well does it work? | Wie gut funktioniert es? |  | Fixed dim1/dim2 headline rows, both metrics and counts |
| p-guess | Which future? | Welche Zukunft? |  | Three visible guesses over measured samples |
| p-equation | A rule for right now | Eine Regel für jetzt |  | Logistic sliders; predator-prey in More |
| p-catalogue | Build an equation | Eine Gleichung bauen |  | Term playground; catalogue in More |
| p-noise | Noise changes everything | Rauschen verändert alles |  | Measurements versus derivatives |
| p-overview | WISP in one picture | WISP auf einen Blick |  | Eight-step overview |
| p-data-intro | Measurements in | Messungen hinein | data | Input and catalogue |
| p-weak-intro | Integrate instead of differentiate | Integrieren statt differenzieren | weak | Window figure; matrix and term integrals in More |
| p-frols-intro | Add the most useful term | Den nützlichsten Term ergänzen | frols | Selector and gain chart; residual in More |
| p-foba-intro | Remove what became redundant | Überflüssige Terme entfernen | foba | Recorded removal evidence |
| p-stop-intro | Know when to stop | Wissen, wann Schluss ist | stop | Stop chart and gate |
| p-fit-intro | Simulate every candidate | Jeden Kandidaten simulieren | fit | Candidate selector, equation and curves |
| p-bic-intro | Choose with a complexity penalty | Mit Komplexitätsstrafe wählen | bic | BIC figure |
| p-test-intro | A second starting point | Ein zweiter Anfang | test | Running example and two compact failure stories |
| p-recap | The complete journey | Der ganze Weg |  | Actual running-example outcome |
| p-results | Explore the results | Ergebnisse erkunden |  | Tabbed full-screen results explorer |
| p-glossary | Words and sources | Begriffe und Quellen |  | Definitions; extended glossary and credits in More |

## Implementation

- 19 source sections; no runtime page multiplication. Method headers include the translated input/output sentence and their figure on the same page. Secondary examples, weak matrix/integrals, path residuals, extended definitions and full featured evidence live in bounded native modal More dialogs. The second-start page retains the running-example generalization plot plus both compact failure narratives.
- Navigation moves the actual document over 720 ms with cubic easing. Wheel inertia gating, animation guards, controls, dragging, modal focus, history, URL language, deep links, small-screen/reduced-motion fallback and print are retained. Page fade/entry animations are disabled.
- Opening solution uses the existing selected result and verified curves. No solver, Julia importer, featured selection rule, data JSON, or compute.js was edited.
- Reader labels use exported `description` (sourced from benchmark `eq_description`) and conditions in words. Cell identifiers remain option values; their visible drill-down occurrence is inside explicitly marked provenance details. Displayed equation coefficients use four significant digits; truth expressions receive the same locale-aware formatting as fitted coefficients.
- All three guesses appear together with distinct colours, line styles and matching legend swatches. Slowing growth uses an unbounded logarithm; the limit curve uses the running example's clean trajectory. Guess curves are illustrations, not additional fitted models. The playground model is thick magenta and its reference data lighter/dotted.
- Explorer tabs show one major panel at a time. Main panel, caption and control text is at least 14 px. Both structure and curve metrics remain in each exact-system results group; surrogate structure is not constructed.

## Headline fields and provenance

32 complete rows are selected from the unchanged exported `results.rates`, independently compared against `analysis/data/sideproject_residual_growth/q5_grid/q5_rates.csv` by `test_wisp_explainer_x4.py`. Selection: dim1/dim2 separately, sigma=0.03, rho=0, WISP configuration c and the three named baseline families. `all_ten` is a separate aggregation summary rather than a configuration; baseline ranges use the actual configuration rows. For each metric the displayed endpoints retain that row's numerator/denominator. No rates or result counts are editorial constants.

Every field in this panel is an existing aggregation CSV column: `stratum`, `sigma`, `rho`, `method`, `configuration`, `metric`, `rate`, `numerator`, `denominator`. `n_units`, `n_cells`, `min_rate`, `max_rate` also remain untouched in the selected rows. The panel uses `pruned_exact` with `raw_exact` beside it, plus both `generalization_arithmetic_hit` and `generalization_variance_weighted_hit`. Configuration endpoints can differ by metric; ranges are not paired model performances. The interim notice is claim-marked, and the WSINDy pending sentence remains explicit. No new scientific record field was introduced.

The name source is the existing results-cell `description`; condition values are the existing `row.sigma`, `row.rho`, with starting-point number parsed only for its readable label. Existing `truth`, `terms`, `row.active_idxs`, `row.params`, `curves`, `observed` supply the opening solution; full precision stays in the unchanged embedded/exported source records.

## Validation and remaining acceptance

The strict numerical command `python analysis/scripts/explainer/check_wisp_explainer_x2.py` exited 0 after the final presentation changes. Six path comparisons passed (2 or 8 steps); the largest reported relative coefficient error was 5.82e-13. All three featured significance-rule comparisons passed (4, 3, 2 steps). These are checks against existing references, not new experimental runs.

The browser checker was attempted. Playwright failed before launching its browser driver with `[WinError 5] Access is denied`. The calibrated Edge fallback failed while launching the probe, exit 2147483651, with `platform_channel.cc ... Access is denied (0x5)`. It produced 0 completed viewport checks and 0 screenshots. Evidence is in `outputs/wisp_explainer_checks/wp_x4_fit.json` and `wp_x4_edge_fit.json`.

**Remaining acceptance:** actual fit and screenshots at 1366 × 768 and 1366 × 657 in EN and DE, and visual confirmation of eased scrolling in Edge/Chrome. No pixel-fit result is claimed from the layout-free Node harness. Status is blocked: browser not runnable here — environment, not the task.

Run outside the sandbox:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The preferred runner uses Playwright Python `channel="msedge"` with exact viewports and 76 per-page screenshots (19 × 2 heights × 2 languages). Fallback uses a tiny inner-size probe, computed window offsets, 20,000 ms virtual-time budget and up to three initialization attempts, then verifies actual dimensions. It never treats a missing result as success, and never substitutes the unreliable CLI deep-link screenshots for Playwright screenshots.

## Final check results

Final combined run (after the last HTML/CSS/JS/string changes):

```text
python -m pytest analysis/tests/test_wisp_explainer.py analysis/tests/test_wisp_explainer_x2.py analysis/tests/test_wisp_explainer_x3.py analysis/tests/test_wisp_explainer_x4.py -q -p no:cacheprovider
29 passed, 15174 warnings in 66.05s
```

Warnings are the existing NumPy `trapz` deprecation. Existing rate/record/hash/trajectory gates, richer-schema results swap and transport round-trip pass. Adapted DOM tests execute both shipped scripts in both languages and check 19 pages, unique section membership, controls/drag/history/fallback, actual headline row equality, three distinct guess paths, reader-text identifier exclusion, modal key/wheel guards, intermediate scroll positions and one-page wheel inertia. The new CSV test checks all selected headline fields against the original file; source tests check both string tables for identifier leakage. The layout-free harness does not verify pixels.

Assembly exited 0 twice with identical bytes. Final HTML: **11,309,786 bytes** (budget 14,000,000); unchanged JSON data: **14,308,875 bytes** (existing data budget 17,000,000). SHA-256: `7ea1c80e5e95c5e4df514d46c493fb52ceb7222199071992ed4d704bde6d7256`. Evidence: `outputs/wisp_x4/rebuild.json`; scientific-input fingerprints: `outputs/wisp_x4/input_hashes.json`. This rebuild tests the assembler with frozen scientific exports; no data exporter or numerical-data regeneration was performed.

Delivered changes are confined to presentation source/strings, the fit checker, adapted/new tests, the assembled HTML, README, report and status. No Git operation, staging, commit, cluster job, campaign, regression run, exploratory run or Julia run was performed.
