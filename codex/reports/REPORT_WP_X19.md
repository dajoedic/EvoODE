# WP-X19 — named Q7 examples and generalization

Status: implementation supplied; Julia 1.12.6 evaluation and subsequent full acceptance remain pending. Julia was deliberately not invoked, as instructed. The new example curves are withheld until the separate Q7 JSONL exists and passes validation. No Git operations, optimization, campaign, regression or cluster runs were performed.

## Delivered behavior

The presentation has chapters 6 (six steps), 7 (five), and 8 (four), with bilingual titles, chapter navigation membership and dots. Results remain hidden. A sixteenth new page, “Was bleibt”, closes chapter 4. This placement uses the task's explicit alternative: the noise estimate and final significance-ended path are both established there; presenting the final residual in chapter 1 would anticipate later decisions. Its stacked bar uses the same squared weak-target normalization as chapter 2: initial noise floor, explained share of the final weak model, and residual above that floor. It does not mix trajectory MSE with weak-space error.

The new Q7 evidence is isolated in `live.examples`; `results.json` keeps its existing contract. The existing scientific exporters and numerical `compute.js` are unchanged. The failure path runs through `W.significancePath` and its live gains/noise tests; its supports are guarded against Q7. LV rounds use the Q7 builder's joint path and retain equation selection, normalized gains and every backward check. Both replays display test → add → clean-up, followed by the stop test; candidate fitting/BIC appears on subsequent pages. Replays loop after a three-second end hold, accept deterministic seek and use the final state for reduced motion. Tiny gains retain their original scale and receive a labelled magnifier only when the largest remaining bar would be below two pixels on the nominal track.

## Field inventory and provenance

No CSV field names were inferred from prose. The exporter reads actual Q7 candidate/unit rows and keeps each candidate's original string-valued `row` intact.

| New field | Origin / computation |
|---|---|
| `cell_id`, `system_id`, `dim`, `sigma` | Existing named Q5 input-cell metadata; Q7 candidate/unit identities cross-checked against it |
| `terms` | Existing `live.catalogues` for the cell dimension |
| `observed.t`, `observed.x` | C-6 time/state binaries named in the Q5 input cell; `legacy.read_observations` checks both SHA-256 values, shape, and approved-directory containment |
| `clean.reconstruction`, `clean.generalization` | The named sigma-zero training IC / opposite IC from the same input index, loaded by the same hash-checking function |
| `truth.equations`, `constants`, `initial`, `other_initial` | Existing benchmark `strogatz_extended.json`: `substituted[0]`, `consts[0]`, and the two `init` entries |
| `truth.support` | Existing `phase_c_support.json` exact `support_idxs` |
| `truth.coefficients` | Existing `true_coefficients_for_phasec_terms`, applied to benchmark equations and registered support labels; signed coefficients, no duplicate symbolic derivation |
| `path.step`, `addition`, `gains`, `backward_checks`, `support` | Existing `growth_path_with_end` with Q7 `significance_end`; normalized gain divides by the receiving equation's squared weak target norm; every resulting support must equal its Q7 CSV candidate |
| `path.before`, `path.tests` | Previous joint support and per-equation gain/noise tests from the same `WeakFit`, `projected_noise_floor`, weak designs and estimated-noise operators used by Q7 |
| `stop.threshold`, `equations`, `ends` | Q7 `THRESHOLDS['chi2_0.01']`, terminal per-equation tests, and builder end diagnostics; `ratio=null` means nonpositive noise, which always passes, not a numeric infinity |
| `candidates[].row` | Existing `q7_candidates.csv` row, excluding `upper_subset` from the actual Q7 path |
| `active_idxs`, `params`, `N`, `k`, `mse` | Parsed existing `active_idxs`, `params`, `n_samples`, `k`, `mse` CSV fields |
| `bic`, `penalty`, `chosen` | `N*log(mse)+k*log(N)`, `k*log(N)`, argmin; checked against the actual size-rule-c `q7_units.csv` winner |
| Both R² weightings and raw/pruned exactness | Existing `row.reconstruction_r2_{arithmetic,variance_weighted}`, `generalization_r2_{arithmetic,variance_weighted}`, `raw_exact`, `pruned_exact` |
| `curves`, `true_initial`, `curve_errors` | New Julia display schema only; full arrays retained. Source CSV hashes, grids, truths, shapes, finiteness, starts, all four reported AND independently recomputed R² scores, and both start-loss diagnostics are checked before exposure |
| `unavailable` | Explicit missing/export-failure/hash/array/score/error reason; no substitute simulation |
| `seen_range` | Exact min/max over the actual noisy observations; supplies the failure RHS shading |
| `manifest.x19_inputs`, `x19_sources`, `x19_display` | File paths and SHA-256 hashes of named binaries, Q7 tables, benchmark, support registry, input payload and extension sources; separate Q7 display presence/hash |

Existing gate `live.gate_status.initial_state` controls the G2 text. Pending remains a proposed variant C, not a decision. The literature hit threshold comes from existing `RESULTS.score_threshold`.

### Initial-state semantics

The task's phrase “reconstruction from the noisy first observation” differs from the actual stored metric. `q5_fit` calls `q4_evaluate(..., clean, ...)` for reconstruction and `q4_evaluate(..., observed, ...)` for training. `simulate` takes its initial state from the first row of that trajectory. Therefore the recorded LV reconstruction R² already belongs to the **true-start** curve. The Kochbuch's explanation of this distinction is correct. The page explicitly labels noisy-start training versus true-start reconstruction. The extended Julia export returns `training` separately; `true_initial` is the reconstruction evaluation, with identical parameters and no optimizer call.

## Live tables from the Q7 records

### Lotka–Volterra — `sys0027_ic1_s0.03_r0_n1`

| Candidate | Support by equation (one-based) | k | MSE | BIC |
|---|---|---:|---:|---:|
| q7_001 | [6] / [] | 1 | 9.118082904967066 | 2270.2372757872054 |
| q7_002 | [6] / [6] | 2 | 14.29122286031444 | 2737.339999949251 |
| q7_003 | [6] / [3,6] | 3 | 6.058969277109379 | 1865.5710675300318 |
| q7_004 | [2,6] / [3,6] | 4 | 0.024220746185280147 | -3782.1129430531537 |

The four normalized additions are 0.6726982887184123 (equation 1, xy), 0.3968238132259028 (equation 2, xy), 0.5925198194526491 (equation 2, y), 0.31478886716423604 (equation 1, x). No removal occurs. Terminal maximum ratios are 3.4689504862403293 and 3.991247935819552, both below 6.635.

Winner q7_004: raw/pruned exact = True/True; fitted coefficients in equation/support order are 1.9551364063116041, -1.5209907497712989, -2.924987044695384, 1.5584337521358353. Signed truth is 1.84, -1.45, -3, 1.62. Reconstruction R² is 0.5226503312478904 arithmetic / 0.5225316301459066 variance-weighted; generalization is 0.819487692838153 / 0.821646811786373. N = 1024 scalar observations = 512 time points × two states. Noisy first observation is [8.883785523799594, 3.4806301930151693]; true initial state is [8.3, 3.4].

The stored noisy-start training MSE is 0.024220746185280147 and clean-start training MSE is 2.958621767608403. Their independent computation from display curves remains pending Julia; the page does not print these record values as if curves had already been verified.

### Logistic failure — `sys0003_ic2_s0.03_r0_n1`

| Candidate | Support (one-based) | k | MSE | BIC |
|---|---|---:|---:|---:|
| q7_001 | [1] | 1 | 148.52668799214942 | 2566.629830142822 |
| q7_002 | [1,4] | 2 | 54.83694224096271 | 2062.7110660519484 |
| q7_003 | [1,2,4] | 3 | 4.112673949122317 | 742.720561257335 |

No removal occurs. After each accepted state, maximum remaining gain/noise is 7208.00161194724, 49.993099725682, 0.025036820743469565. The truth support [2,3] never appears. Winner q7_003: raw/pruned exact = False/False; params = [8.967093849736727, 0.24111013629670158, -0.00006559792564812365]. Reconstruction R² = 0.9995847427259011 variance-weighted; generalization R² = 0.9639646780601635 variance-weighted. Both arithmetic values are separately retained in the candidate rows. Training truth starts at 21; the other IC starts at 7.3. Observed min/max = [20.490188335953174, 80.48406417739751].

## Kochbuch check

All cell-specific scalar statements, displayed candidate/round tables and benchmark constants were checked against the named records or algebraically against their RHS. Plot trajectories themselves await authoritative Julia evaluation.

| Kochbuch statement | Checked evidence / outcome |
|---|---|
| LV system 27; two true terms/equation; 12 catalogue blocks/equation, 24 total | Benchmark, support registry and existing catalogue agree |
| LV 512 points; 3% noise; start (8.3,3.4) | 512×2 observations, sigma 0.03, benchmark IC agree |
| LV gains 67%,40%,59%,31%; four candidates, no removal | Rounded builder gains above agree |
| LV stops 3.5 and 4.0 below 6.6 | Rounding of 3.4689504862403293, 3.991247935819552, 6.635 agrees; UI uses full threshold |
| LV BIC -3782 vs +1866 for candidate three | Computed BIC -3782.1129430531537 vs 1865.5710675300318 agrees |
| LV fitted 1.96,-1.52,-2.92,1.56 and truth 1.84,-1.45,-3,1.62 | Rounded coefficient records agree |
| LV coefficients about 5% away | Relative absolute differences are approximately 6.26%,4.90%,2.50%,3.80%; this is an approximation, not a uniform 5% error |
| LV R² 0.52 reconstruction, 0.82 generalization; noisy start (8.88,3.48) | Rounded record scores/start agree |
| LV training MSE 0.024 vs 2.96, more than hundredfold | Existing observed_start_mse / clean_start_mse agree; curve-based verification still pending |
| Failure same equation/noise, starts 21 vs 7.3 | Benchmark ICs/sigma agree |
| Failure rounds 1, x³, x; next ratios 7210,50,0.03 | First value 7208.00161194724 rounds to 7210 at three significant figures; others agree |
| Failure winner 1,x,x³; pruned form constant+linear | Existing raw/pruned-exact flags both False; tiny cubic coefficient is retained in the plotted raw RHS |
| Failure params 8.97,0.241,-0.000066 and truth 0.79,-0.0106 | Rounded candidate params and benchmark coefficients agree |
| Failure R² 0.9996 and 0.964, both above 0.9 | Record scores agree |
| “Data saw x between 21 and 74” | **Mismatch for noisy observations**: actual min/max 20.490188335953174 / 80.48406417739751. Clean range is 21 / 74.23015073225298. UI shades actual observations |
| At x=7.3, truth 5.2 and model 10.7 | Algebraic RHS values 5.200390309555855 / 10.701679136460793 agree |
| “Largest difference is 1.5 at values up to 15” | **Mismatch**: absolute difference at x=15 is 2.9046812935097606; at x=0 it is 8.967093849736727. This statement is not copied |
| Divergence below 20; no data there | Observed min 20.490188335953174 supports the absence of observations below 20; no literal cutoff is inserted in the page |

Population-wide statements about approximately half of all noisy cases cannot be established from these two cells and are not inserted in these chapters.

## Commands for Claude, in order

From the repository root, Julia 1.12.6 only. The script has an explicit version guard. The smoke limits **cells**, so it evaluates the four LV candidates into a separate file. The full export evaluates all seven named Q7 candidates, without optimization.

```text
julia +1.12.6 --project=. studies/explainer/export_wisp_display_trajectories.jl --q7-examples --cells sys0027_ic1_s0.03_r0_n1,sys0003_ic2_s0.03_r0_n1 --limit 1 --output outputs/wisp_explainer_julia/q7_examples_smoke.jsonl
julia +1.12.6 --project=. studies/explainer/export_wisp_display_trajectories.jl --q7-examples --cells sys0027_ic1_s0.03_r0_n1,sys0003_ic2_s0.03_r0_n1 --output outputs/wisp_explainer_julia/q7_examples.jsonl
python analysis/scripts/explainer/build_wisp_explainer_x2.py
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The full WISP test suite is intentionally deferred until after this Julia run, per the task's test policy. The fit checker inventory includes all new pages, replay phase boundaries, hold/restart samples, text size, exponent notation and chart-label intersections. Browser pixel/layout acceptance is not claimed here.

## Verification

Final local test counts, rebuild hashes and remaining environment limitation are recorded below after the final validation run. Local reproduction: `python outputs/wp_x19/validate.py`.

### Final local results

- Full fast presentation selection: **45 passed in 157.07s**; `outputs/wp_x19/presentation.log`.
- After the last equation-formatting and shared DOM-check refactor: **6 passed in 23.72s** in `test_wisp_explainer_x19.py`, including both languages and replay lifecycle. These are focused checks, not an additional full WISP suite.
- Numerical JavaScript checker: exit 0, all six reference cases; `outputs/wp_x19/js.log`.
- Complete extension export/data rebuild identity: `outputs/wp_x19/rebuild.json`; final HTML-only consecutive identity after the last presentation edits: `outputs/wp_x19/final_acceptance.json`.
- Final HTML: 11740293 bytes; SHA-256 `29aa7a3a22480bd9c2a79eb4499a5e65c68fc2987c4d3479a20b482ec44ff155`. Delivered inventory: 52 visible pages; 69 including hidden legacy pages.
- `results.json` still has its historic SHA-256 `7fb7b8a5f96b5bf118471ea46486d352091a6ad3cf23763782587097c6bb5959`; existing numeric-core hash checks pass. Historic live/manifest hash assertions were scoped to immutable artifacts because X19 explicitly adds evidence and provenance; named Q7 hashes are separately checked.
- Seven Q7 candidates currently have no Q7 Julia display file, so their curves/errors remain null with explicit pending reasons. No Julia-derived result is claimed.
- **Blocked: Umgebung, nicht Sache.** Julia evaluation, its subsequent full WISP test suite and browser pixel/layout acceptance remain for Claude using the commands above. No other implementation blocker remains.
