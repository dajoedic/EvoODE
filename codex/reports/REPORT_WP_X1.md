# WP-X1 — WISP explainer foundation

Status: **blocked**. The local foundation is implemented, but acceptance is not complete. No Git command, Julia process, model fit, campaign, cluster job, or prohibited result source was used. All new work remains uncommitted.

## Deliverables

- `analysis/scripts/explainer/build_wisp_explainer_data.py`: deterministic evidence export and manifest; missing inputs remain explicit.
- `analysis/scripts/explainer/build_wisp_explainer.py`: deterministic single-file assembly.
- `analysis/scripts/explainer/check_wisp_explainer_js.py`: Python/Node numerical comparison, with a failing strict Q5 gate when observation bytes are absent.
- `analysis/tests/test_wisp_explainer.py`: eight data, reproducibility and execution checks against actual repository records.
- `explainer/wisp/src/index.html`, `style.css`, `compute.js`, `app.js`: authored source.
- `explainer/wisp/data/results.json`, `live.json`, `manifest.json`: generated evidence and provenance.
- `explainer/wisp/dist/wisp_explainer.html`: assembled page, 4,141,913 bytes. SHA-256: 43e243036a04fdb0a50d69b3bfea96acb39f6d6ef802771fd582728779c9ce59.
- `explainer/wisp/README.md`: build/check instructions, schema and limitations.

The Distill reference was opened and read before implementation. Its progressive explanation and manipulable figures inform the design; no text was copied. This is a local-only deliverable. Nothing was registered or published through Sites.

## Sections

The page has the requested order: hook and prediction buttons; differential equations with logistic sliders and predator–prey time/phase views; scalar term playground and catalogue-size explorer; multiplicative noise and finite differences; draggable integration windows, term areas and a stacked matrix; FROLS/FoBa step-through and a recorded real removal; three headed placeholders for stopping, selection/BIC, and generalization/failure; the results explorer; glossary and component origins.

The palette assigns persistent roles to measurements, truth, model and residual. CSS supplies light/dark schemes and stacked narrow layouts, with native labelled controls and keyboard focus indicators. KaTeX 0.16.11 is the sole external resource. It emits native MathML, avoiding external CSS/fonts. CSS, application code and all evidence are inline. Responsive layout and actual mathematical rendering have **not** been visually verified in a browser.

## Actual inputs and field audit

The export reads exactly five scientific input files; each path and its SHA-256 are in the manifest:

| Input | Use |
| --- | --- |
| `analysis/data/sideproject_residual_growth/q5_grid/q5_rates.csv` | All 3,672 source rows, preserving every field as its original CSV string |
| `analysis/data/sideproject_residual_growth/q5_grid/q5_units.csv` | All 1,632 trajectory-BIC choices and their stored equations/scores |
| `analysis/data/sideproject_residual_growth/q5_grid/q5_run_metadata.json` | Frozen protocol identifier and baseline reference hash |
| `outputs/sideproject_q5_inputs/q5_grid_paths.json` | Actual paths, weak coefficients, observation hashes, catalogue dimensions and real removal states |
| `benchmarks/data/strogatz_extended.json` | True equations, descriptions, constants and initial conditions only; stored solutions are not used |

The export scans only the two whitelisted Q5 output trees for binary observations and finds **zero** binary files. It never follows the paths into a different campaign folder. The cookbook supplies pedagogical ideas; no cookbook result tables are exported. Q7/Q8 data and C-6 method results were not read.

Every rate field was checked against an actual CSV row: stratum, sigma, rho, n_units, n_cells, method, configuration, metric, numerator, denominator, rate, min_rate and max_rate. All thirteen fields are copied without recomputation; the row-by-row test covers all 3,672 rows.

The cell adapter uses actual q5_units columns: cell_id, unit_id, system_id, initial_condition_set, stratum, sigma, rho, realization, size_rule, active_idxs, params, raw_exact, pruned_exact, reconstruction_r2_variance_weighted, reconstruction_r2_arithmetic, generalization_r2_variance_weighted and generalization_r2_arithmetic. Each is an existing aggregation column, not a newly invented per-fit record field. The complete chosen CSV row is preserved and tested for equality. All 1,632 choices have populated active_idxs, params and candidate_id. Reconstruction variance-weighted scores are empty in 29 rows; generalization variance-weighted scores are empty in 131 rows. Empty scores display as unavailable, including a test using one of these actual cells.

The path input supplies actual cell_id, dim, candidates and export metadata. Candidate active_idxs, origin, step, equations, term_names and coefficients are existing path fields. Available, observed, curves, unavailable, and the verification summaries are new export fields. System truth and description are derived from benchmark substituted equations and eq_description. No fixture adds fields to a scientific record.

The manifest records repository identity 650c3e693528e958fb4d7c8dfab5331d970fd9ed by reading HEAD/ref metadata, without invoking Git. Protocol identifier is f737939. The exported provenance includes campaign, interim status and baseline reference fingerprint. The explorer keeps 11 dim-one, 10 dim-two, 2 feasible dim-three and 1 dim-four systems separate. Fully clean controls are excluded from rate populations, matching report_tables; sigma zero in the rate table is the subsampling-only condition. Counts for every rate population were checked against the actual cells and initial-condition units. Systems are shown separately from repeated cells; no cell-based uncertainty claims are made.

## Baseline provenance conflict

The request assumes that these Q5 rows use MATLAB-original WSINDy by default. The actual `aggregate_sideproject_q5.py` has REFERENCE pointing at `outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv`. Its report_tables groups sindy, weak_sindy and e_sindy configurations. The exported CSV labels include weak_sindy_poly_deg3_sin_cos_stlsq_0.01 and weak_sindy_poly_deg3_sin_cos_stlsq_0.1, plus all_ten. This does not establish the requested MATLAB-original WSINDy provenance.

The page therefore preserves the source labels and discloses this limitation instead of certifying an unsupported source. No baseline data outside the whitelist were opened. An approved replacement aggregation or a clarified whitelist is required to meet that provenance requirement. Baseline thresholds can differ by metric; the explorer shows the exact selected configuration beside each rate. The all_ten median has no source numerator, so none is invented.

## Numerical implementation and FoBa case

The browser and Node load the same compute.js core. Its design uses the reference box-window lengths and actual-time trapezoidal quadrature. Subset fits use unit column scaling, augmented Householder QR and one-sided Jacobi SVD; normal equations are not used. Selection, tie order, normalization, backward fraction and the interim cap/SSE stop follow growth_path. Python reference construction reuses build_design, growth_path and weak_coefficients.

Catalogue counts verified through phasec_basis are **6 / 12 / 19 / 27** for dimensions one through four. These counts and the all-equation subset totals are exported, not hand-written result prose.

The real FoBa cell is **sys0001_ic1_s0.01_r0_n1**. At step **6**, the stored path adds cos(u) and removes the constant and sin(u), leaving u, u², u³ and cos(u). The page shows that recorded transition and its actual weak coefficients. The manifest stores the cell, removal events and post-removal states. Its live replay is unavailable because observation bytes are absent.

The required reference cells are sys0003_ic1_s0.03_r0_n1, sys0001_ic1_s0.01_r0_n1 and sys0001_ic1_s0_r0_n1. All three have actual stored Q5 paths, but **0 of 3** have observation bytes inside the whitelist. Their Python/JS comparison was not performed and is not claimed.

For development only, the exporter simulates the true logistic and predator–prey equations from their benchmark constants/ICs with DOP853. It supplies a fixed Gaussian noise vector for the explicitly labelled scalar illustration. Browser controls use those same draws. These are new illustrations, not reconstructed Q5 inputs. No model is fitted. RK4 is confined to forward illustration/playground curves.

## Checks and acceptance

| Acceptance/check | Observed result |
| --- | --- |
| Data export and HTML assembly | Both exit 0 from the repository root |
| Repeatability | A second complete data export and assembly produced identical bytes for all three JSON files and HTML; subsequent final HTML rebuilds were also identical |
| Numerical illustration comparison | 3 of 3 pass, each with 8 forward steps; selected supports, additions, removals and designs compared with Python |
| Relative coefficient errors, illustration sigma 0.01 / 0.03 / 0.05 | Maximum 3.14e-13 / 7.41e-14 / 3.12e-13 respectively |
| Strict Q5 numerical checker | **Exit 1**, explicitly listing the three missing reference inputs |
| Drill-down observation coverage | **0 of 1,632** cells have original observations available |
| Drill-down re-simulation | **0 attempted, 0 verified, 1,632 unavailable**; no reconstructed trajectory is exported or claimed verified |
| Rate equality | All 3,672 rows match all CSV fields exactly |
| Cell metadata/score equality | All 1,632 selected rows match the source CSV |
| Local tests, final source | **8 passed in 4.69 seconds**, cache provider disabled |
| JavaScript syntax | Node syntax checks of compute.js and app.js exit 0 |
| Application smoke execution | Node DOM harness initializes the real page data and executes noise, path selection, step, result filters, coefficient reset and catalogue controls; it is not a browser/layout test |
| Literal result prose check | All **33** static HTML prose paragraphs inspected by regex after assembly; **0** contain decimal digits. Dynamic numerical prose is populated through JavaScript from exported records/configuration. The application source was also reviewed for result literals |
| External resources/file loading | One pinned KaTeX script; no fetch calls, external data or stylesheet dependencies |
| Browser/file-console acceptance | **Unverified**: browser access host unavailable; native Firefox selection was rejected with “Computer Use was not approved to use firefox.” No console or screenshot claim is made |

All performed commands finished within seconds. No run approached the fifteen-minute ceiling.

## Remaining work

For WP-X1 acceptance, provide the original observation and clean evaluation binaries within the approved Q5 trees, or explicitly approve their actual source location. Hash matching is already implemented. Then rerun the strict numerical comparison and every exported reconstruction check. Missing or mismatched curves must continue to be withheld. Resolve the Q5/MATLAB-original baseline provenance conflict upstream. Finally, open the built file in an approved browser and verify console, controls, narrow layout, dark mode and MathML rendering.

WP-X2 can add stopping, simulation/refitting/BIC, a second starting point and the failure example in the existing placeholders. A later campaign replaces results.json while preserving its documented schema; provenance status and primary method identity are data-driven. The evidence layer and narrative layer need no restructuring. The present missing-data and provenance gates must be resolved independently of those added sections.
