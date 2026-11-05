# WP-X18 — trajectory fit and BIC

Implemented chapter five with six delivered steps in both languages, after the stopped Q7 path. The delivered inventory is 36 pages: intro 2, chapter one 11, chapter two 5, chapter three 7, chapter four 5, chapter five 6. There are 53 source pages including the hidden later sections.

The shared SVG remains mounted. The weak-start curve is browser RK4 of stored `p0` on the observation time grid, initialized at the first noisy observation. Fitted predictions only interpolate the verified stored display curves onto that grid; they are never reintegrated. The fitting transition interpolates the two endpoint curves and coefficients, with an explicit schematic-frame label. Missing fitted curves display their stored reason.

The candidate panels share axes. BIC uses stored totals and penalties, a computed fit term and a common truncated axis with an explicitly labelled axis break. The winner is the argmin of the four Q7 candidates, marked in the final three-column comparison against truth and weak start. The recap reuses miniature observation, window, test, support and curve elements. Only its single stage highlight moves. All steps loop with the existing three-second end hold, deterministic seek and reduced-motion end state.

Fit settings come from gate strings and the presentation-only `src/fit_protocol.json` defaults, embedded by the HTML assembler as `live.fit_protocol`. Pending G2 defaults are bound 10 and initial state = first noisy observation. Decided gate strings override the defaults and remove the provisional note. No scientific data export or results schema was changed.

The existing results-swap test exposed an unguarded chapter-three lookup of the teaching cell in replaceable results. The shared truth source now falls back to the teaching candidate's existing `row.system_id` when that results cell is absent. The real-record synthetic swap test passes without weakening the contract.

## Field provenance checked against the actual record

| Display or calculation | Existing source / presentation derivation |
|---|---|
| Candidate order and support membership | `live.featured[0].stop_reference.supports`, zero-based; matched to JSON `candidate.row.active_idxs`, one-based, without positional selection |
| Weak coefficients | `live.featured[0].path[*].p0`, linked by `candidate_id` and support-checked |
| Fitted coefficients | JSON `candidate.row.params` |
| MSE, k, N | `candidate.row.mse`, `.k`, `.n_samples`; N checked against observation count times dimension |
| BIC, penalty | Existing top-level `candidate.bic`, `.penalty`; no replacement values written |
| Reconstruction R² | Existing `candidate.row.reconstruction_r2_arithmetic` and `.reconstruction_r2_variance_weighted` |
| Fit curves and withholding reason | Existing verified `candidate.curves.t/truth/model` and `candidate.unavailable` |
| Observation times, noisy values, initial state | `live.teaching.t`, `.observed`; feature/teaching cell IDs must agree |
| True equation | Same teaching-system illustration constants as chapter three; system ID from the results cell or the independent live candidate record |
| Bound and provisional note | `live.gate_status.coefficient_bound` / `.initial_state`; pending defaults in presentation protocol JSON, no new record fields |
| Extra-block MSE share | `1 - exp(-log(N)/N)` from stored N |
| Bound marks | Exact comparison of each fitted absolute coefficient with the active bound |
| Legacy comparison | Remaining stored candidates, best BIC computed rather than assumed |

## Actual candidate table

Teaching cell: `sys0003_ic1_s0.03_r0_n1`. R² columns are arithmetic / variance weighted. Supports use the exported teaching cell's catalogue. All parameter lists and scores below come from the current stored records.

| Candidate | Protocol | Support | p0 | params | MSE | k | N | BIC | penalty | Reconstruction R² |
|---|---|---|---|---|---|---|---|---|---|---|
| path_001 | Q7 | 1 | [6.854237917019977] | [10.0] | 141.0520431831231 | 1 | 512 | 2540.1923331328558 | 6.238324625039508 | 0.7320530786397965 / 0.7320530786397965 |
| path_002 | Q7 | 1, u1^3 | [12.838766033517986, -0.0000274664285332617] | [10.0, -0.000013231051317030672] | 29.81297214417565 | 2 | 512 | 1750.687775339986 | 12.476649250079015 | 0.948686252191979 / 0.948686252191979 |
| path_003 | Q7 | u1, u1^3 | [0.5204903781409852, -0.00009564192649233413] | [0.6102062137904685, -0.00011653906907485074] | 5.3125901721101885 | 2 | 512 | 867.5573571823252 | 12.476649250079015 | 0.9957790201776506 / 0.9957790201776506 |
| path_004 | Q7 | u1, u1^2 | [0.7849282623265934, -0.010525641345774626] | [0.7954005232437973, -0.01072152626966299] | 3.0364877249152373 | 2 | 512 | 581.1558140942572 | 12.476649250079015 | 0.999956494802444 / 0.999956494802444 |
| path_005 | superseded | u1, u1^2, sin(u1) | [0.7916528505217513, -0.010630413545501156, -1.580354404157878] | [0.8180502000492703, -0.010998051556551338, -1.629518624147943] | 3.301437144833985 | 3 | 512 | 630.2262043929069 | 18.714973875118524 | 0.9994604525363449 / 0.9994604525363449 |
| path_006 | superseded | u1, u1^2, u1^3, sin(u1) | [0.8246060827943852, -0.012006047491178524, 0.000012854231376275936, -1.5726244828916613] | [0.8027501237171295, -0.010810451618509211, -0.0000003636720109718534, -0.6482217821416272] | 3.0649238114037156 | 4 | 512 | 598.4049267687842 | 24.95329850015803 | 0.9998713432492894 / 0.9998713432492894 |
| path_007 | superseded | 1, u1, u1^2, u1^3, sin(u1) | [-1.8901285413234103, 0.9960588553726606, -0.016193397878806942, 0.00004300006055458005, -1.6100118719594585] | [-2.3964653476190563, 1.1016051708122132, -0.01902918391407131, 0.00006317310964167582, -1.2514663965318287] | 3.33765406028574 | 5 | 512 | 648.2889328448779 | 31.191623125197538 | 0.9992905061076595 / 0.9992905061076593 |
| path_008 | superseded | 1, u1, u1^2, u1^3, sin(u1), cos(u1) | [-2.0800902743525067, 1.0086657794338303, -0.01646433317132827, 0.000044732013860236524, -1.6147994718068377, -0.39756217808259253] | [-2.4786730946831526, 1.0621722256895976, -0.0175742096919539, 0.00005053342421569785, 0.12692706170508905, -1.293240810587387] | 3.112165992258495 | 6 | 512 | 618.7132472361034 | 37.42994775023705 | 0.999688531740756 / 0.9996885317407559 |

Q7 winner: `path_004`, BIC 581.1558140942572. Best superseded continuation: `path_006`, BIC 598.4049267687842, difference 17.249112674527055. Extra-block MSE reduction threshold: 1.211030063296581%. Maximum relative BIC identity error across all stored candidates: 0.0.

## Final acceptance

- Final presentation run: `53 passed in 143.16s (0:02:23)`. Log: `outputs/wp_x18/presentation.log`.
- Strict JS numerical checker: exit 0, six cases (three illustrations and three real references). Log: `outputs/wp_x18/js.log`.
- Two final sequential presentation-only rebuilds are byte-identical. HTML size: 11515706 bytes. SHA-256: `c615ba9c75253e31235925288856fde85ea0be757fb503dc797cd6c485cec111`. Evidence: `outputs/wp_x18/rebuild.json` and `.log`.
- Source and DOM tests cover both languages, support-order independence, real BIC/penalty identities, argmin selection, computed bound marks, weak `p0` and first-observation initialization, verified curve provenance/withholding, pending and synthetic decided gates, exponent-free displayed numbers, fixed topology, looping, deterministic seek and reduced motion.
- Fit checker inventory, six-step masthead/dots, sampling and chapter-five label-overlap checks are updated. Browser pixel/layout acceptance was not run: CURRENT_TASK explicitly assigns it to Claude. No browser pass is claimed.
- No Julia, exports, cluster jobs, campaign/regression runs or Git operations. All changes remain uncommitted.

Reproduce the exact authorized checks:

```text
python outputs/wp_x18/validate.py
```

Expanded final commands:

```text
C:\Users\joedicke\AppData\Local\Programs\Python\Python312\python.exe -m pytest analysis\tests\test_wisp_explainer.py analysis\tests\test_wisp_explainer_x13.py analysis\tests\test_wisp_explainer_x16.py analysis\tests\test_wisp_explainer_x17.py analysis\tests\test_wisp_explainer_x18.py analysis\tests\test_wisp_explainer_x3.py analysis\tests\test_wisp_explainer_x4.py analysis\tests\test_wisp_explainer_x5.py analysis\tests\test_wisp_explainer_x6.py analysis\tests\test_wisp_explainer_x7.py analysis\tests\test_wisp_explainer_x7b.py analysis\tests\test_wisp_explainer_x7c.py analysis\tests\test_wisp_explainer_x7e.py analysis\tests\test_wisp_explainer_x9a.py analysis\tests\test_wisp_explainer_x9b.py -q -p no:cacheprovider
```

```text
C:\Users\joedicke\AppData\Local\Programs\Python\Python312\python.exe analysis/scripts/explainer/check_wisp_explainer_js.py
```

```text
C:\Users\joedicke\AppData\Local\Programs\Python\Python312\python.exe outputs/wp_x18/rebuild.py
```

Claude's separate browser acceptance:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```
