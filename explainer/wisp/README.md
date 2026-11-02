# WISP explainer

Open `dist/wisp_explainer.html` directly. CSS, application code and evidence are inline; the sole external resource is pinned KaTeX 0.16.11, rendering native MathML. Browser/layout review belongs to Claude.

From the repository root:

```text
python analysis/scripts/explainer/build_wisp_explainer_data.py
python analysis/scripts/explainer/build_wisp_explainer.py
python analysis/scripts/explainer/check_wisp_explainer_js.py
python -m pytest analysis/tests/test_wisp_explainer.py -q -p no:cacheprovider
```

The exporter reads Q5 rates, selected units, run metadata, paths and benchmark equations/ICs. Observations come only from `outputs/phase_c_c6_data_conditions_5dd1df8/`, resolving `export.cell_dir` plus `time_path`/`state_path` for cells named by Q5 paths. Every binary must match the recorded SHA-256 before use. There is no directory scan or hash-based substitute. Clean reconstruction and opposite-IC generalization targets are the clean cells from that same export, exactly as loaded by `sideproject_q5_noise_fits.jl` and reported by the Q5 aggregation. Benchmark stored solutions are never evaluation targets.

Both arithmetic and variance-weighted R? must reproduce both stored reconstruction and generalization scores within absolute 1e-6. Missing scores/inputs are withheld; nonfinite integrations or score mismatches fail. Only a cell passing all four comparisons exports curves. `manifest.json` records one check per cell, counts, reasons, recomputed scores, input hashes and reference cells. `results.json` keeps the complete chosen CSV row unchanged. Re-simulation evaluates stored coefficients and does not fit models. Verification follows Q5's `q4_evaluate` / `simulate`: rtol=atol=1e-6, the complete clean binary time grid, its first state as initial condition, and coefficients clamped to [-10,10]. Julia uses Tsit5; SciPy RK45 (Dormand-Prince 5(4)) substitutes the available explicit fifth-order embedded Runge-Kutta method, with its own error controller and dense interpolation. It is not numerically identical. The existing deterministic ceiling of 50,000 RHS evaluations per target remains (Julia allows 1,000,000 steps). Every failed cell is reintegrated with rtol=atol=1e-7: a movement above 1e-6 in any of the four R2 values is classified as integrator sensitivity, otherwise stable disagreement. No tightened solution replaces the primary check. The JS playground uses RK4. `compute.js` is shared by page and strict Node checker (unit scaling, Householder QR and Jacobi SVD, actual-time trapezoidal windows, frozen growth and FoBa policy).

The hook, noise and weak-form figures use the real System 3 cell in `live.teaching`. At its recorded ? the original observations are used exactly. Other ? settings rescale those same disturbances and are explicitly labelled illustrations. The separate logistic and predator?prey playgrounds remain illustrations. The real FoBa removal case can be selected for a live replay from its original samples.

Q5 baseline labels are SINDy, Weak-SINDy (pysindy, fixed threshold), and E-SINDy, with exact configuration names. Their source is WP-N47, `outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv`; this file is identified, never opened by this exporter. Original MATLAB WSINDy is separate. `comparison` reserves its result slot. When the single authorized future file `analysis/data/sideproject_residual_growth/q7_q5w_comparison.csv` exists, the exporter copies its rows without calculating rates. Until then the page shows the pending-comparison sentence. No other Q7/Q8 source is read.

## Results schema contract (version 2)

A replacement `data/results.json` requires no presentation-code change. Run the assembler after replacement. JSON numbers or numeric CSV strings are accepted for numbers; unknown extension fields are retained. All scientific values come from aggregation, never editorial literals.

Required top-level fields:

| Field | Contract |
| --- | --- |
| `schema_version` | Integer `2`. |
| `provenance` | Object requiring string `protocol` and `status`; status is `interim`, `final`, or `synthetic` (test only). Additional source paths, SHA-256, commit, campaign, baseline and population notes appear verbatim in the provenance panel. |
| `primary_method` | Method identifier for WISP (currently `Q5`); arbitrary nonempty string. |
| `score_threshold` | Finite numeric threshold for curve-hit metrics. |
| `exclude_clean_controls` | Boolean; excludes cells with ?=?=0 from drill-down rate populations. |
| `rates` | Array of rate rows described below. |
| `cells` | Array of cell objects described below; may be empty for rate-only releases. |

Optional top-level fields:

| Field | Contract |
| --- | --- |
| `method_labels` | Object mapping arbitrary method IDs to display names. Unknown IDs display verbatim. Includes WSINDy W1 and W1-interp when supplied by an approved aggregation. |
| `selected_configuration_methods` | Optional array of method IDs whose aggregation selects one configuration per metric. Only these methods group selected configurations together; each metric still displays its exact configuration. All other method/configuration pairs render separately. |
| `axes` | Array of `{key, label, values}`. Unique `key` names an extra scalar field in rate rows and `cell.row`; `values` is an array of distinct strings. Examples: realization (`1`, `2`, ...), variant (`initial_state_on`, `initial_state_off`), library. `all` is reserved for the selector. Missing axes mean no extra filters. All-axis display preserves separate groups and never averages rows. |
| `comparison` | `{status: "pending" or "available", source: relative path, rates: [...]}`. Available rates use the same rate contract. Q7 adapter also accepts `comparison` in place of `configuration` and `denominator` in place of `n_cells`, preserving original columns. The page includes all strata/conditions from this slot. |

Each rate row requires `stratum` (nonempty opaque string, e.g. `dim1`, `dim2`, `dim3_feasible`, `dim4`, `surrogate`), nonnegative numeric `sigma`, `rho` (numeric in [0,1], or `pooled` for aggregation-supplied pooled sampling), `method`, `configuration`, `metric`, `rate`, `denominator`, `n_units`, `n_cells`. `numerator` is required for a simple rate; it may be empty for the `all_ten` configuration summary, which instead supplies `min_rate` and `max_rate`. Rates and bounds are in [0,1]; counts are nonnegative integers. The exporter copies the original CSV representation, including empty summary numerators. No rates are recomputed in the adapter.

Allowed metrics are `raw_exact`, `pruned_exact`, `reconstruction_arithmetic_hit`, `reconstruction_variance_weighted_hit`, `generalization_arithmetic_hit`, and `generalization_variance_weighted_hit`. Structure metrics are legal only for exact-system strata. Surrogates supply only R? metrics; omitted structure metrics render no structure panel. Both structure and curve metrics remain side by side for exact systems. The unique rate key is `(stratum, sigma, rho, method, configuration, metric, extra axes...)`. Selected baseline configurations can differ per metric; the exact name is shown beneath each metric. Extra axes distinguish groups even when the selector is `all`. Strata are never pooled by the page. A release can supply any number of conditions, including eleven, and dimensions three/four without source changes.

Each cell requires `row`, numeric `system_id`, `description`, boolean `exact`, `terms`, `truth` (array of equation strings, empty for surrogates), `observed`, `curves`, `unavailable`. `row` requires unique `cell_id`, `unit_id`, `stratum`, `sigma`, `rho`; optional axes appear here too. For an equation drill-down it includes JSON-encoded `active_idxs` (one-based catalogue indices per equation) and flattened JSON-encoded `params`, plus stored `reconstruction_r2_arithmetic`, `reconstruction_r2_variance_weighted`, `generalization_r2_arithmetic`, `generalization_r2_variance_weighted`. Missing/empty scores display unavailable. Exact cells include `raw_exact`/`pruned_exact`; surrogate cells omit those fields. `terms` lists the catalogue in index order. `observed` is null or `{t, x}` with time-by-dimension states. `curves` is null or `{t, truth, model, generalization: {t, truth, model}}` after verification of both targets and both weights. `unavailable` is null on success or a reason string when withheld. The source Q5 CSV row remains unmodified; derived fields live outside it.

## Reviewing interpretation after a data swap

Every static paragraph, caption and aside, plus dynamically created prose, carries `data-claim="review"`. Dynamic interpretation containers also carry this attribute. This intentionally marks more than numerical claims to avoid missing an interpretation. Search with `rg -n 'data-claim' explainer/wisp/src` or inspect `document.querySelectorAll('[data-claim]')` after changing data. Re-read marked statements against the new provenance, populations, and rates. Numbers and equations alone are not interpretations.

The swap test derives its cell field inventory from a real exported record, then explicitly changes it to fake values. It builds eleven synthetic conditions, five strata including surrogates, two realizations, two initial-state-estimation variants and six methods with two configurations each. Its temporary assembled HTML runs through the same Node DOM harness as the real page. No synthetic data are written into the delivered `data/` or `dist/`. The harness checks JS behavior, not browser rendering.

## Presentation sampling and size budget

Version 2 explicitly permits presentation-only sampled/rounded arrays in the existing compact `{t, x}` and `{t, truth, model}` bundles: one time vector shared across all variables, with time-by-dimension matrices. Curves and ordinary observations retain at most 48 uniformly spaced sample indices, including both endpoints; each value has five significant decimal digits. The 48-sample cap keeps the complete page below 12,000,000 bytes and the data directory below 15,000,000 bytes. Five-digit rounding has relative error at most 5e-5 for nonzero values. Full-resolution float64 integrations and targets determine verification before sampling; rates, CSV rows and scores are never rounded. The three reference cells retain full observations in both results and live data; all live inputs remain unchanged. Sampling can omit details between samples; it is exclusively a display copy.

Margin notes flow inline up to 1450 px, accounting for the wide figures. Every SVG chart has visible x/y titles; the FROLS bars use native HTML text and a shrinking middle column to preserve term/value readability at 360 px. The initial scalar playground uses only `0.23u`; its model display is capped at twice the target's maximum absolute population, with a visible clipping notice and unmodified mismatch computation. Browser layout review remains with Claude.
# WP-X2 additions

Use the presentation extension without changing the frozen scientific exporters:

```text
python analysis/scripts/explainer/build_wisp_explainer_x2.py
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python analysis/scripts/explainer/check_wisp_explainer_x2.py
python -m pytest analysis/tests/test_wisp_explainer.py analysis/tests/test_wisp_explainer_x2.py -q -p no:cacheprovider
python analysis/scripts/explainer/check_wisp_explainer_layout_x2.py
```

The X2 exporter first calls the unchanged X1c exporter, then adds deterministic featured-cell selection, Q7 rule references calculated from Q5 observations only, both string tables, gate status, and the Julia import. `--extend-only` is useful after editing strings; a full reproducibility check uses the command without that flag. All existing scientific scripts and outputs stay unchanged.

One HTML contains both languages. `?lang=de`, `?lang=en`, `#lang=de`, `#de` and their English equivalents select a language. Otherwise the remembered choice or browser language applies. The masthead switch reloads the same file with the selected language parameter. Both storage operations tolerate unavailable localStorage. All authored prose and accessibility labels are in `src/i18n/en.json` and `de.json`; terms, identifiers, mathematical expressions and source metadata are shared data. Numerical formatting follows the active locale.

Only result interpretations carry claim markers. The four keys `j336`, `j337`, `j338`, `j339` identify the featured result sentences in both tables. Search `document.querySelectorAll('[data-claim]')` after replacing evidence. Method explanations carry no marker. This supersedes the broad X1 claim policy above.

`live.gate_status` uses `stop: pending|cap|significance`, `initial_state: pending|estimated|observed`, `coefficient_bound: pending|10|1000`. Each status maps to a translated string. A gate decision changes data; no new renderer code is needed.

## Julia display format

`studies/explainer/export_wisp_display_trajectories.jl` is evaluation only; include the Q5 runner at top level, reuse `q4_evaluate`, then repeat that same simulate call to obtain its prediction. No optimizer is run. Julia 1.12.6 is mandatory.

The default file `outputs/wisp_explainer_julia/trajectories.jsonl` contains one JSON object per `(cell_id,candidate_id)`: source CSV hashes, `passed`, `reason`, `max_r2_error`, and `reconstruction` / `generalization`. Each target bundle has the full `t` vector, full time-by-dimension `truth` and `model` arrays, and `scores: {arithmetic, variance_weighted}`. JSON null represents missing/nonfinite values. The script checks every stored score to 1e-12; Python repeats that gate and checks the target grid/arrays before display thinning to 48 points and five significant digits. The Python R2 calculation is secondary, not a solver substitute.

With no Julia file, results curves retain X1c behavior. When the file exists, only verified Julia records supply results curves; missing or failed records withhold them. Featured candidate curves await Julia. Failures and missing scores are enumerated in `manifest.julia_display.checks`. No Q7/Q8 result file is consumed. The prior Python diagnostics remain under `manifest.resimulation`.

```text
julia --project=. studies/explainer/export_wisp_display_trajectories.jl --limit 3 --output outputs/wisp_explainer_julia/smoke.jsonl
julia --project=. studies/explainer/export_wisp_display_trajectories.jl
```

The limited output is deliberately named separately: it cannot accidentally replace the complete display file. After the full Julia run, repeat the Python export and assembly.

X2 budgets are 14,000,000 HTML bytes and 17,000,000 data bytes. Current no-Julia output also fits the stricter X1c budgets. Schema version 2 of results is unchanged. Featured narratives are presentation data in `live.json`, independent of the results swap contract. A synthetic results swap simply leaves absent featured result cells undisplayed.

The X2 assembler interns repeated display time/target/model arrays losslessly inside the HTML only. `app.js` restores ordinary curve bundles before using them. On-disk `results.json` keeps the exact v2 contract; the transport round-trip test proves equality. This leaves headroom for Julia curves that were previously withheld, without reducing the 48-point display grid.

Gate source data are maintained in src/gates.json; the exporter copies them to live.gate_status.

## WP-X4 presentation and acceptance

The source now contains 19 self-contained sections. The first three show measurements, the stored selected equation beside the true equation, and the fixed Q5 comparison. A 720 ms cubic eased scroll moves the document; page fades are disabled. Wheel inertia and animation locks prevent one gesture from advancing multiple pages. Native modal More dialogs bound secondary content and preserve internal wheel/key scrolling. The results explorer uses Overview / By condition / Look inside a system tabs with 14 px minimum panel/control text.

Rebuild without changing scientific exports:

```text
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python -m pytest analysis/tests/test_wisp_explainer.py analysis/tests/test_wisp_explainer_x2.py analysis/tests/test_wisp_explainer_x3.py analysis/tests/test_wisp_explainer_x4.py -q -p no:cacheprovider
python analysis/scripts/explainer/check_wisp_explainer_x2.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The fit checker prefers Playwright with `channel="msedge"`, exact CSS viewports, and per-page screenshots at both heights in both languages. The Edge CLI fallback calibrates its window offset using a probe, verifies the resulting viewport, and retries missing fit results up to three times. CLI screenshots are deliberately excluded because deep-linked captures can be blank; fallback-only checks cannot satisfy the complete screenshot acceptance. Evidence: `outputs/wisp_explainer_checks/wp_x4_fit.json` and `wp_x4_edge_fit.json`. Browser execution is denied in the Codex sandbox; Claude must run the final pixel acceptance.


WP-X5 adds shared SVG rate charts (raw structure as light marks, pruned structure and both generalization weights), configuration endpoints with original counts, and a collapsible table alternative. Overview charts follow the noise, sampling and extra-axis filters, keeping strata and extra-axis groups separate. The frozen Q5 export supplies only one individually reported configuration per baseline method at the headline condition; its `all_ten` summary has no endpoint numerators and is excluded. The headline notice states this explicitly.

German system labels cover all 24 exported system IDs, with the exported English description as fallback for future IDs. Featured stories use one switcher and one More drawer. Wheel routing distinguishes active dragging, an open select and actual directional scroll room from hovering.

Run the complete presentation suite with `python -m pytest analysis/tests/test_wisp_explainer.py analysis/tests/test_wisp_explainer_x2.py analysis/tests/test_wisp_explainer_x3.py analysis/tests/test_wisp_explainer_x4.py analysis/tests/test_wisp_explainer_x5.py -q -p no:cacheprovider`. Run `python analysis/scripts/explainer/check_wisp_explainer_fit.py` outside the sandbox for the Edge wheel/arrival/reader-text tests and 76 screenshots. WP-X5 browser evidence is written to `outputs/wisp_explainer_checks/wp_x5_fit.json` and `wp_x5_edge_fit.json`. A blocked browser launch is not a layout pass.
