# WP-X5 report

Status: blocked ? browser not runnable here ? environment, not the task.

## Delivered presentation

The 19-page plan remains intact: problem, solution, headline are the first three pages, with the guessing exercise on its existing page. This uses the task's explicit permission to retain WP-X4's separate solution/headline pages. Page 1's chart has a viewport-relative 50vh height and full content width; the solution chart is 290px high. The three guessing curves have their own end labels, colours and dash patterns. No entrance animation definitions remain. Data samples are actual SVG dots, clean references are thin dashed lines, and models are thick solid lines in the step colour, drawn after data so they remain visible. The analytical noise-floor series retains its dashed line.

Headline and explorer Overview share `rateChart`: one structure chart and separate arithmetic/variance-weighted generalization charts, with fixed method colours. Structure includes light raw marks alongside pruned bars/endpoints. Each endpoint references an actual exported row, with its original configuration, numerator and denominator in keyboard-focus labels, hover titles and a collapsible table. Surrogate strata never acquire structure metrics. Explorer follows sigma/rho and extra-axis filters; each stratum and extra-axis combination has its own card. Internal metric field names are translated before rendering; provenance remains available separately.

Wheel navigation no longer tests whether the pointer merely hovers over a control, figure or panel. It checks an active range/window drag, select-open state, and computed directional scroll room in ancestor scrollers. The existing gesture/inertia gate remains. More drawers and explorer/table scrollers consume wheel events while they have room; at their directional boundary the page can advance.

All four exported featured examples are accessible through a single-story switcher (one visible at a time), retaining the running example and failure examples. For multidimensional available trajectories, a component switcher keeps one component visible in each reconstruction/generalization panel; unavailable-curve notices are not treated as components. Their charts have a 260px presentation height, negative generalization R? receives the requested mean-prediction explanation, and the page has exactly one More button. Detailed story evidence and secondary weak-form/FROLS/test prose are in the existing drawers. Catalogue spacing and headline layouts are condensed for the short viewport. These are implementation dimensions, not a claim that pixel-fit acceptance passed.

## Defect 4: what was actually shown

The existing panel selected configuration rows and excluded `all_ten`; it did not show the summary row. At sigma=0.03/rho=0, for each of dim1/dim2 and each of the four headline metrics, Q5 exports exactly **one** individually reported configuration per baseline method. Consequently there are **32** selected headline rows: 2 strata ? 4 methods ? 4 metrics. For dim1 pruned structure, the source rows are SINDy 2/66, Weak-SINDy 5/66, and E-SINDy 1/66. Configuration names end in `poly_deg3_sin_cos_stlsq_0.1` with their method prefix.

Weak-SINDy also has an `all_ten` summary. Its dim1 pruned minimum and maximum are 0.015151515151515152 and 0.2727272727272727, but its numerator is empty and there are no endpoint configuration rows/counts in this frozen export. Inventing endpoint counts or reading another results source would violate the task. The explicitly allowed banner correction is therefore used: it states that each baseline shows its one individually exported configuration and that `all_ten` is excluded. A singleton is a point/cap; where multiple configurations are supplied (including the richer-schema swap), the chart uses source-row min/max endpoints. The explorer explains this convention without claiming its filter is the fixed headline condition.

Evidence: `outputs/wisp_x5/headline_rows.json`; the existing CSV-equality test compares every selected field against `analysis/data/sideproject_residual_growth/q5_grid/q5_rates.csv`.

## Encoding and names

Four literal question marks inside German words were found in source i18n entries: `h014` (m?gliche), `h055` (ver?ndern), `j322` (zur?ckgehalten), and `recorded_step` (hinzugef?gt). They are corrected in the source tables. No U+FFFD was found in presentation sources or the final assembled HTML: final count **0**. The UTF-8 assembler was already explicit and remains unchanged. A source for the previously observed replacement characters in Playwright console text could not be reproduced in the HTML. Windows console decoding can corrupt diagnostics despite correct file bytes; fit-check summary output now uses ASCII-escaped JSON while evidence files remain explicit UTF-8. No claim is made that this proves the cause of the earlier observation.

Both source and embedded string tables are checked, and actual reader DOM text is checked in EN/DE for U+FFFD and question marks between letters. The unused generic dashed/dotted translation was removed. Legends now describe each individual series' actual style.

German name coverage: **24/24 distinct exported system IDs**, covering every reachable drill-down record, every featured example and the running example. IDs: 1, 2, 3, 5, 6, 8, 9, 11, 12, 17, 23, 24, 25, 26, 27, 28, 29, 31, 32, 38, 43, 52, 61, 63. New `system_<id>` translation entries are presentation strings; an unknown future ID falls back to its exported English description. Default zero missingness and first starting point are omitted; a second starting point and half-missing observations have concise translated labels.

## Field inventory and unchanged inputs

All scientific fields already exist in the real frozen export. `rates` provides `stratum`, `sigma`, `rho`, `method`, `configuration`, `metric`, `rate`, `numerator`, `denominator`, and optional aggregation endpoints. `all_ten` is an aggregation value, not a configuration with endpoint counts. `cells` provides `system_id`, `description` (benchmark eq_description), `row.sigma`, `row.rho`, `row.cell_id`, stored raw/pruned flags and R? scores. Starting-point display is derived from the existing cell ID. `curves`, `observed`, `truth`, `terms`, `row.active_idxs` and `row.params` are existing verified equation/trajectory inputs. No scientific record field was introduced. Translation keys and chart endpoint selections belong only to presentation.

SHA-256 checks confirm byte-identical `compute.js`, `live.json`, `manifest.json`, and `results.json` against the WP-X4 fingerprints. Evidence: `outputs/wisp_x5/input_hashes.json`. No scientific export, numerical code, Q7/Q8 result, campaign, manifest, Julia job or Git operation was changed or performed.

## Final validation

Final combined run after presentation changes:

```text
python -m pytest analysis/tests/test_wisp_explainer.py analysis/tests/test_wisp_explainer_x2.py analysis/tests/test_wisp_explainer_x3.py analysis/tests/test_wisp_explainer_x4.py analysis/tests/test_wisp_explainer_x5.py -q -p no:cacheprovider
33 passed, 15174 warnings in 48.31s
```

This includes all 29 existing tests plus 4 new tests, the richer-schema results swap, real-page EN/DE DOM execution, endpoint/count preservation, encoding, name coverage, no internal metric fields outside provenance, hover-versus-drag wheel routing and the single-story/single-drawer contract, and component selection including the real unavailable-curve fallback. The DOM harness indexes real HTML IDs so actual measurement circles do not turn lookup into repeated full-tree scans. Warnings are the existing NumPy trapz deprecation.

`python analysis/scripts/explainer/check_wisp_explainer_x2.py` exited 0: six path comparisons passed; largest relative coefficient error **5.82e-13**; three featured significance-rule comparisons passed with stop steps **4, 3, 2**.

Assembly exited 0. Two assemblies in the final test run produced identical bytes. Final HTML: **11,323,738 bytes**, below **14,000,000**; data: **14,308,875 bytes**, unchanged. SHA-256: `865931c18215e0390c2e152b2592aa0b4f77a68724b26d5192e37ca08258094b`. Evidence: `outputs/wisp_x5/rebuild.json` and `validation.json`.

## Browser acceptance still open

The Edge checker was attempted with Playwright `channel='msedge'`. Playwright failed before browser launch with `[WinError 5] Access is denied`. The Edge fallback exited **2147483651** with `platform_channel.cc ... Access is denied (0x5)`. Checker evidence records exit **2**, **0** completed viewport checks and **0** screenshots. Files: `outputs/wisp_explainer_checks/wp_x5_fit.json` and `wp_x5_edge_fit.json`.

The checker now first executes **10** centre-pointer navigation cases: N=1..5 gestures, EN and DE, viewport 1366?768, and checks immediate headline visibility and reader DOM labels/encoding. It then measures all 19 pages in EN/DE at 1366?768 and 1366?657 and requests **76** screenshots. These browser assertions have not executed here. Actual fit, pixel dimensions, all tab/story states and visual quality remain unverified; no screenshot or browser pass is claimed.

Claude's remaining acceptance command, outside the sandbox:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

All delivered work remains uncommitted. CURRENT_TASK.md was not edited.
