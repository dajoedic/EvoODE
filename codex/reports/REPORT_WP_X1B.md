# WP-X1b - WISP explainer acceptance

Status: **done**. All WP-X1b acceptance items are met. Files remain uncommitted. No Git command, Julia process, campaign, regression/probing job, browser test, or prohibited scientific result source was used. Existing aggregation scripts and scientific outputs were not changed.

## Delivered changes

- `build_wisp_explainer_data.py`: targeted original-observation loading, path containment and SHA-256 gates; clean reconstruction and opposite-IC generalization verification for every selected cell; real System 3 teaching data; corrected baseline provenance and future comparison slot.
- `explainer/wisp/src/app.js` and `index.html`: real hook/noise/weak-form measurements; explicit illustration labels away from the recorded sigma; working real FoBa replay; corrected baseline names; generic extra-axis and configuration rendering; surrogate structure panels omitted; interpretation markers.
- `explainer/wisp/README.md`: versioned results contract, required/optional fields, allowed values, conditions/strata/method/configuration/metric semantics, realization and variant axes, surrogate restrictions, future comparison ingestion, and claim-review instructions.
- `analysis/tests/test_wisp_explainer.py`: all eight existing checks retained, with the DOM harness reading the assembled HTML; richer swap test and real-record hash/path failure test added.
- Rebuilt `data/results.json`, `live.json`, `manifest.json` and the single-file HTML. Build evidence is in `outputs/wisp_explainer_checks/verification.json`.

## Source and field audit

The 3,672 rate rows retain all thirteen original CSV fields byte-for-value as strings: stratum, sigma, rho, n_units, n_cells, method, configuration, metric, numerator, denominator, rate, min_rate, max_rate. The equality test compares complete rows. Each of the 1,632 chosen `size_rule=c` rows is likewise preserved unchanged from `q5_units.csv`.

Existing aggregation columns used by the page remain cell_id, unit_id, system_id, initial_condition_set, stratum, sigma, rho, realization, active_idxs, params, raw_exact, pruned_exact and both reconstruction/generalization R2 weightings. These are aggregation fields, not invented fit-record fields. Path metadata supplies existing cell_id/dim/candidates/export fields and export.cell_dir, time_path/state_path, time_shape/state_shape and their SHA-256 values. Observed arrays, verified curves, teaching data, method display labels, comparison status, optional axes and verification checks are new presentation/export fields. The synthetic variant field exists only in the temporary swap fixture.

The only newly read scientific directory is `outputs/phase_c_c6_data_conditions_5dd1df8/`. No scan is performed: only files named by cells in the Q5 path payload are opened. Each path is resolved inside that directory and each binary is accepted only on its recorded hash. A mismatch is withheld without searching for a replacement. The failure test starts from a real cell, corrupts its recorded hash, then tests an escaping path.

Clean targets follow the Q5 aggregation back to `sideproject_q5_noise_fits.jl`: its reconstruction loader uses `(sid, ic, 0, 0, 1)` and generalization uses `(sid, 3-ic, 0, 0, 1)` in the same export. Both clean cells are already in Q5 paths. No additional scientific source was needed. Benchmark equations/constants/ICs remain the source for explicit playground illustrations, never benchmark stored solutions.

Final manifest: **3,269 hashed input files**, including **3,264 binary files**; **1,632/1,632 observations available**, **0 observation errors**, **0 missing reference cells**. No EvoGrow result, C-6 method record, Q7/Q8 data or baseline details file was opened. The absent future Q7 comparison file was checked for existence only.

## Numerical acceptance

Strict checker, final data: exit **0**. Added terms, removed terms, supports and coefficients agree with Python and the stored Q5 paths.

| Real reference cell | Steps | Maximum relative coefficient error |
| --- | ---: | ---: |
| sys0003_ic1_s0.03_r0_n1 | 8 | 5.82e-13 |
| sys0001_ic1_s0.01_r0_n1 | 8 | 4.39e-14 |
| sys0001_ic1_s0_r0_n1 | 2 | 1.83e-14 |

Coefficient tolerance is relative 1e-8, with no absolute slack. The three retained development illustration comparisons also pass (8 steps each; errors 3.14e-13, 7.41e-14 and 3.12e-13).

The real FoBa replay uses hash-verified observations of sys0001_ic1_s0.01_r0_n1. At step 6 it adds catalogue index 6 (cos u), removes indices 1 and 5 (constant and sin u), and leaves u, u-squared, u-cubed and cos u. The Node DOM test selects this case and executes the live replay. The hook and noise/weak figures use sys0003_ic1_s0.03_r0_n1. At recorded sigma=0.03 they use the exact observed array; other slider settings rescale its disturbances and display an illustration notice.

Re-simulation checks **all 1,632 cells**, with both arithmetic and variance-weighted reconstruction AND generalization R2 compared to their stored values at absolute tolerance 1e-6:

| Stratum | Passed | Failed | Withheld | Total |
| --- | ---: | ---: | ---: | ---: |
| dim1 | 651 | 44 | 53 | 748 |
| dim2 | 503 | 112 | 65 | 680 |
| dim3_feasible | 27 | 90 | 19 | 136 |
| dim4 | 39 | 21 | 8 | 68 |
| Total | **1,220** | **267** | **145** | **1,632** |

The maximum error among passed cells is **9.939210827702993e-7**. All 267 failed cells have finite scores with discrepancies above tolerance, ranging from **1.0325038601877168e-6** to **25899.060970783234**. These discrepancies are reported without attributing them to an untested cause.

The 145 withheld cells lack at least one stored score: 29 lack both reconstruction weightings and 131 lack both generalization weightings, with 15 cells in both sets. Re-integration of these cells also has incomplete targets: 145 target integrations reach the solver's minimum step size, and 15 reach the deterministic 50,000-RHS-evaluation ceiling. These are target counts, not additional cells. Reasons and recomputed scores are retained per cell in the manifest.

Verification uses DOP853 with rtol=atol=1e-8. Stored coefficients are evaluated without refitting. Earlier development attempts were stopped while bounding verification cost; no results from those attempts are reported as final acceptance. The final repeated full export took **62.406 seconds**, below the fifteen-minute limit.

Only the **1,220 passed cells** export reconstruction/generalization curve bundles (covering **1,894 variable plots** for reconstruction). All **412 other cells** keep curves null. The test checks every non-null curve against its passed manifest record and maximum error; displayed curves therefore have passed all four score checks. Failed integrations are not substituted with another solver result or fabricated data.

## Provenance and swap readiness

Labels are **SINDy**, **Weak-SINDy (pysindy, fixed threshold)** and **E-SINDy**, preserving exact configuration strings. Source attribution is WP-N47, `outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv`; identifying that path does not read its contents. Pysindy Weak-SINDy is never labelled WSINDy.

The comparison block is pending with zero rows. The page shows exactly: "Comparison with WSINDy (original MATLAB code): follows with the next aggregation". The exporter will copy `analysis/data/sideproject_residual_growth/q7_q5w_comparison.csv` automatically when it exists. It computes no WSINDy rate. The DOM test asserts that no results label contains the exact spelling WSINDy while the comparison is pending; the required pending sentence and literature attribution are outside the results-label set.

The swap test builds **220 synthetic cells** and **14,784 synthetic rate rows** in a temporary directory only: five strata, eleven conditions, two realizations, two initial-state-estimation variants, six methods, two configurations per method, six metrics for exact systems and four for surrogates. Cell fixtures originate from actual exported records of each dimension; changed IDs/axes/scores are explicit, with synthetic provenance and deliberately fake values. The assembled temporary HTML uses unchanged presentation code and the same Node harness. Every condition/method/configuration and both extra axes render; all strata are inspectable; surrogate cards have no structure metric. Temporary synthetic files are removed and never enter delivered data/dist.

There are **44 static data-claim markers**; dynamically created prose receives the same marker. A source check finds no unmarked paragraph, figcaption or aside. The README documents source search and DOM inspection after a data swap.

## Final commands and reproducibility

```text
python analysis/scripts/explainer/build_wisp_explainer_data.py
python analysis/scripts/explainer/build_wisp_explainer.py
python analysis/scripts/explainer/check_wisp_explainer_js.py
python -m pytest analysis/tests/test_wisp_explainer.py -q -p no:cacheprovider --tb=short
node --check explainer/wisp/src/app.js
node --check explainer/wisp/src/compute.js
```

All commands exit **0**. Final complete test suite: **10 passed in 37.74 seconds**. JavaScript syntax checks pass. A subsequent full export and assembly reproduce all three JSON files and the HTML byte-for-byte; the strict checker passes again on these rebuilt files. No browser test was performed or required.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `explainer/wisp/data/results.json` | 138,769,882 | aaa0287af14f6e3bde16c08739169df2303f349c64ebda2ced0d7ec15d4c3e10 |
| `explainer/wisp/data/live.json` | 1,543,867 | cb08f08b9b930a7aa7b697365b5ebcef6a6e309e7088daed535ba6cd3497116a |
| `explainer/wisp/data/manifest.json` | 1,270,084 | a2555c0913abe1dc602663739483fd4e44b7f81f06650bbadb169bfe38efb3fa |
| `explainer/wisp/dist/wisp_explainer.html` | 141,639,443 | 7262ac09a596c6dc6caaf24bb2a7323a9771a659323da32bba1ee8972350cb93 |

No acceptance item remains open. Browser/layout review is reserved for Claude as requested.
