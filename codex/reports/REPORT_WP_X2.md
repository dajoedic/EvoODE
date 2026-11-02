# WP-X2 — implementation record

## Selection rule (fixed before querying eligible rows)

Use rule (c) rows only. Keep the mandatory running example. For each additional role, restrict to sigma=0.03, rho=0, realization=1, then sort by numeric system_id, numeric initial_condition_set, and cell_id. Choose the first row satisfying: dim2 with raw_exact=True; dim1 with truth_on_path=False; dim1 with reconstruction_r2_variance_weighted >=0.99 and generalization_r2_variance_weighted <0.5. Roles may share a cell. The rule uses only Q5 rows; it makes no aggregate performance claim.

Status: **blocked — Julia not executable here; environment, not the task.** The implementation and Python/Node checks are complete. Julia numerical acceptance remains for Claude. Browser pixel/overflow inspection also could not execute in this environment; that separate limitation is recorded below. No Julia result is claimed.

## Built

The three placeholders now explain stopping, fitting every path candidate and selecting by trajectory BIC, and reconstruction versus generalization with two failure stories. The running examples use stored Q5 choices and candidate rows. The Q5 cap is explicitly described as twice the largest true equation size, derived from the answer. The live Q7 demonstration estimates noise from observations and tests the extra gain; it does not display Q7 rates. The second starting point is explicitly excluded from fitting and selection.

One HTML contains English and German, with **293 identical string-table keys**. German prose uses the cookbook's terms and short explanations. URL query/hash, remembered choice, browser language, unavailable storage, locale-aware numbers and the HTML language attribute are implemented. The EN/DE switch reloads the same file with its language parameter. This also redraws every numerical label in the selected locale. Source metadata, identifiers, method names and mathematics remain shared data.

Only four result-interpretation keys carry `data-claim`: `j336`, `j337`, `j338`, `j339`. Both tables contain them. Method explanations carry no marker. `src/gates.json` supplies the stop, initial-state-estimation and coefficient-bound statuses; their current values are all `pending`. Changing that source data selects the corresponding translated status without changing JS.

The step-zero residual plot now includes a visible starting point at 100%, and its y-axis begins at zero. Responsive wrapping and `hyphens:auto` follow the selected HTML language. The results contract remains version 2. The richer-schema swap test still passes. An absent featured cell in replacement results does not crash the candidate controls.

The new exporter wraps the frozen WP-X1c exporter. No existing scientific analysis/export script, existing scientific output, root `src/` file, Q4 runner or Q5 runner was edited. The existing explainer tests were adapted to the new assembler, the requested size budgets, explicit English test initialization, and authoritative Julia verification when that output is present. No Git operation, fitting, cluster job, campaign, regression or probing run was performed.

## Featured cells

The rule above was written before querying the eligible rows and is preserved verbatim in `manifest.featured_selection`. A test reruns it against the real `q5_units.csv`.

| Role | Cell | Path candidates | Chosen candidate | Raw / pruned exact | Truth on path |
| --- | --- | ---: | --- | --- | --- |
| Mandatory running example | `sys0003_ic1_s0.03_r0_n1` | 8 | `path_004` | True / True | True |
| First exact dim-2 choice | `sys0028_ic1_s0.03_r0_n1` | 15 | `path_002` | True / True | True |
| First dim-1 missing truth | `sys0001_ic2_s0.03_r0_n1` | 6 | `path_004` | False / False | False |
| First dim-1 generalization failure | `sys0006_ic2_s0.03_r0_n1` | 6 | `path_002` | False / False | False |

| Cell prefix | Reconstruction arithmetic / variance-weighted R² | Generalization arithmetic / variance-weighted R² |
| --- | --- | --- |
| sys0003_ic1 | 0.999956494802444 / 0.999956494802444 | 0.99996665644664 / 0.99996665644664 |
| sys0028_ic1 | 0.9999729007561773 / 0.9999751070830568 | 0.9999746124944987 / 0.999974605159348 |
| sys0001_ic2 | 0.9902371583217765 / 0.9902371583217765 | empty / empty |
| sys0006_ic2 | 0.9989446059067655 / 0.9989446059067655 | -18.81548771218846 / -18.81548771218846 |

These are stored CSV scores, not new Julia results. In particular, the missing-truth cell has no stored generalization score: its curves must remain withheld even after importing Julia data. The UI displays unavailable scores explicitly. The detailed source rows are indexed in [wp_x2_featured.json](../../outputs/wisp_explainer_checks/wp_x2_featured.json).

Field audit: cell/system/unit identifiers, stratum, noise/sampling/realization, chosen candidate, `truth_on_path`, raw/pruned exactness and the four R² columns are existing Q5 aggregation columns in `q5_units.csv`. Per-candidate support, parameters, step, k, MSE, sample count, sentinel/diverged flags and scores come from real `q5_candidates.csv` rows, filtered to candidate IDs in that cell's Q5 path payload. Path equations and weak starts come from the existing payload. True term indices are taken from an existing raw-exact candidate of the same system in the Q5 CSV, not invented or supplied to the live search. Display BIC and its penalty are derived as `N log(MSE) + k log(N)` and `k log(N)`, matching the existing selector; tests reproduce the stored choices. Roles, curve-import status, thinning and localization are presentation fields.

## Strict live rule checks

The unchanged FROLS/FoBa reference checks pass for all three existing cells. Maximum relative coefficient errors are 5.82e-13, 4.39e-14 and 1.83e-14, respectively. All three illustration checks pass.

`check_wisp_explainer_x2.py` additionally compares the same shipped JS used by the browser against Python's `significance_end` and `growth_path_with_end` on the three featured dim-1 observations. The stop steps match exactly: **4**, **3**, **2**, respectively for sys0003_ic1, sys0001_ic2 and sys0006_ic2. The entire support sequences also match. Noise-variance arrays agree at rtol=1e-9, atol=1e-16. A mismatch raises and exits nonzero. No Q7/Q8 result file was read or generated; these are rule demonstrations on whitelisted Q5 observations.

## Julia display export and static review

`studies/explainer/export_wisp_display_trajectories.jl` includes the frozen Q5 runner at top level; its program guard prevents fitting. It loads stored parameters, constructs the same `StructureSpec`, basis and RHS, and uses `build_reference_optimizer(max_fit_attempts=1)` and `build_options(Q3_SEED)`. It never calls the optimizer. Clean reconstruction and opposite-IC targets are loaded through `q5_read_cell`, hash checked and compared exactly with `build_trajectory`, as in Q5. Target caching avoids repeating those identical checks for every noisy cell.

For each target it calls `q4_evaluate` for the scores, then repeats exactly that function's `simulate` call to retain its prediction: Tsit5, abstol=reltol=1e-6, maxiters_solve and clamp/nonfinite/divergence settings from the same optimizer. All four recomputed scores must agree with stored scores to **1e-12 absolute**. Empty/nonfinite scores or mismatches record failure. Nonfinite values serialize as JSON null. No Python integrator substitutes for this gate.

The JSONL format is one record per `(cell_id,candidate_id)` at `outputs/wisp_explainer_julia/trajectories.jsonl`, with source CSV hashes, pass/reason/max-error fields, and reconstruction/generalization bundles. Each bundle contains full-resolution `t`, time-by-dimension `truth` and `model`, and arithmetic/variance-weighted `scores`. The final file is published from a same-directory temporary file. The output path must remain inside its own `outputs/wisp_explainer_julia/` directory. A separately named `--limit` output cannot replace the complete default accidentally.

Static review covered the complete include chain and call signatures, JSON3 array conversion via `collect`, parameter order/count, Set iteration, optional parse results, missing/empty CSV fields, nonfinite serialization, and use of top-level includes to avoid world-age issues. This is a source review, **not runtime verification**.

Count-based expected runtime: **1,632** selected cells plus **35** featured path candidates minus **4** already selected candidates = **1,663** evaluation records. Two targets, each with one `q4_evaluate` solve and one retained-prediction solve, give at most **6,652** model solves, plus **48** distinct clean-target integrations for control. At an assumed 10–100 ms per solve this is about 67–670 seconds, plus an unmeasured 1–3 minute compilation allowance: planning estimate **roughly 3–15 minutes**. This is not a benchmark. Difficult/diverging trajectories can exceed that estimate. No Julia execution was attempted in this session, as instructed by CODEX_PROTOCOL.

Commands for Claude (Julia **1.12.6**):

```text
julia --project=. studies/explainer/export_wisp_display_trajectories.jl --limit 3 --output outputs/wisp_explainer_julia/smoke.jsonl
julia --project=. studies/explainer/export_wisp_display_trajectories.jl
python analysis/scripts/explainer/build_wisp_explainer_x2.py
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
```

Python checks the four Julia scores again and verifies the complete clean arrays and grid before thinning. Malformed/nonfinite predictions are withheld with reasons. The original Python simulation checks remain secondary diagnostics when Julia is present. When Julia is absent, the results exporter retains WP-X1c curve behavior exactly; the new candidate curves remain explicitly pending. The import tests use a temporary file, real Q5 row/target inventories and visibly altered fixture values; they do not claim a Julia run. They test successful import, 2e-12 mismatch, empty scores, target mismatch, duplicate records, absent-file preservation and failed-record withholding through the exporter itself.

There is currently **no Julia output**. The fallback has **922** verified curves, **565** mismatches and **145** cells with missing stored scores, unchanged from WP-X1c. All **35** featured candidate curves await Julia. [wp_x2_withheld.json](../../outputs/wisp_explainer_checks/wp_x2_withheld.json) lists all **745** fallback-failure/pending-candidate entries with their reasons; the manifest also retains every check. No missing value or failed check was relaxed into a displayed curve.

## Reproducibility, sizes and checks

Two complete export/assembly runs exited 0 and reproduced all three JSON files and HTML byte for byte in **70.860 s** and **149.453 s**. Two final assemblies after the last presentation adjustment also match byte for byte. Evidence: [wp_x2_rebuild.json](../../outputs/wisp_explainer_checks/wp_x2_rebuild.json).

| Artifact | Bytes | Final SHA-256 |
| --- | ---: | --- |
| live.json | 1,735,270 | 6fa6d13eadd5ff8a36ff270d0029eeace15eaaaf3a48a842a0b7fb1d59aa9c0e |
| results.json | 8,438,130 | ae5167427b7360b409ea3112aee7decab2dd2ea5e7292e5610cf31ce6f62a81c |
| manifest.json | 1,467,500 | 819ef3971b2b9821bda2bc4633959a20a92739dcca88d7b887bd1b714accc10e |
| wisp_explainer.html | 9,984,055 | fd1227074432a0ae8cd564a62de935de2b086c2583046d9b70f03ada107f44ca |

Data total: **11,640,900 bytes**, below 17,000,000. HTML is below 14,000,000. The assembler enforces both limits. It interns repeated display arrays losslessly inside the HTML and restores ordinary v2 curve bundles before rendering. The transport round-trip test proves equality with the on-disk contract. Display copies still use at most 48 points and five significant digits; full grids determine the numerical gates first.

Final combined test run: **21 passed in 27.24 s**, exit 0, including all 12 earlier tests and 9 X2 tests. Evidence: [wp_x2_tests.txt](../../outputs/wisp_explainer_checks/wp_x2_tests.txt). There are 15,174 deprecation warnings from the unchanged shared `np.trapz` implementation. Both Node syntax checks and Python compilation checks exit 0. The DOM tests initialize both languages, translate all static keys, reject raw keys, check claim markers and HTML lang, exercise all featured candidates and stopping controls, and tolerate unavailable localStorage. They test behavior, not pixels.

```text
python analysis/scripts/explainer/check_wisp_explainer_rebuild_x2.py
python analysis/scripts/explainer/check_wisp_explainer_x2.py
python -m pytest analysis/tests/test_wisp_explainer.py analysis/tests/test_wisp_explainer_x2.py -q -p no:cacheprovider --tb=short
node --check explainer/wisp/src/app.js
node --check explainer/wisp/src/compute.js
```

## Remaining environmental checks

The numerical Julia pass gate is unexecuted, so status is blocked under the protocol's prescribed Julia-environment rule. Claude must run the commands above; no numerical acceptance result is fabricated.

Actual browser layout inspection at **360 px** and **1280 px**, in both languages, also remains unverified. Chrome headless did not create DevToolsActivePort within 30 seconds. Edge headless exited **2147483651**, reporting `Access is denied (0x5)` in its Mojo platform channel and crashpad startup. The connected browser tool returned `The browser access host is unavailable`. Evidence: [wp_x2_layout_environment.json](../../outputs/wisp_explainer_checks/wp_x2_layout_environment.json). The ready-to-run checker measures all figure/panel/SVG bounds, detects empty translations, and captures narrative sections:

```text
python analysis/scripts/explainer/check_wisp_explainer_layout_x2.py
```

No claim of a successful pixel or overflow check is made. Optional recursive cleanup of isolated browser-test profiles was rejected by automatic approval review; those temporary profiles remain under `outputs/wisp_explainer_checks/`. This does not affect the shipped page or data budgets. All implementation files remain uncommitted.
