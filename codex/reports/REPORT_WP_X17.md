# WP-X17 — true round order and chapter four: stopping

## Implementation

- Chapter two now has five pages and ends after round two at separate model blocks `1`, `u³`. Removed `c2-all`, its scene and timing, its bilingual `x16_` strings, and all navigation/fit samples for it. The closing sentence now belongs to the remaining solution page. Its six paragraphs across five pages remain populated.
- The only forward-only continuation is chapter three's explicitly labelled counterfactual: “Ohne Aufräumen – so geht WISP nicht vor” / “Without clean-up – not what WISP does”. It is calculated only for that comparison, through round four.
- Chapter four has five delivered pages: shrinking gains and a reminder of the existing noise band; actual gain versus noise expectation; ratios and the stop threshold; the live test → add → clean-up replay; four candidate rows of separate chips with their addition/removal origins. Later chapters remain hidden. The closing question leads to simulating candidates, with no trajectory fit or BIC in chapter four.
- `fourthModel` calls unchanged `W.significancePath` on `live.teaching`. Its supports and step count are guarded against the actual stop reference, and its first four supports against chapter three. It exposes every open block's gain in residual units, noise expectation, ratio and decision. `window.WispChapterFour` exposes that presentation model.
- The replay tests before adding, uses the actual largest-gain winner and the existing repeated removal probes, and ends round five after its test. Add and clean-up panels are greyed and labelled “Ende” / “End”. The forward ratio and backward cost charts have equal dimensions and styling, their own axes and threshold lines, and magnifier insets when the decision would otherwise lie near zero. The paired gain/noise chart also prints both values and magnifies the small noise comparison.
- All chapter-four nodes are mounted once. The existing story clock provides deterministic seek, a three-second final hold, looping and reduced-motion end states. Label alignment is initialized for all nodes, including unused ones, so replay cannot change hidden-node attributes. All interpretation text is marked `data-claim="review"`; chapter-four scientific prose uses substitutions, not numeric literals.
- Updated the fit checker inventory, chapter-four masthead/dots and sample table, including phase boundaries of every replay round. Browser text-bound/overlap measurement is assigned to Claude by the task and was not run here.

## Field provenance (checked against the real live export)

| Input / exposed field | Origin |
|---|---|
| `live.teaching.t`, `.observed` | Existing observation arrays in `data/live.json` |
| `live.featured[0].stop_reference.threshold` | Existing record field; the only source of the displayed stopping threshold |
| `.stop_reference.supports`, `.stop_reference.stop_step` | Existing record fields; zero-based supports and count, checked at build time |
| `live.featured[0].path[*].active_idxs` | Existing record fields; one-based supports used by chapter three's guard |
| `live.windows`, `live.backward_fraction` | Existing configuration for weak rows and clean-up |
| `variance` | Existing numerical function `W.noiseVariance(t,x)`; local cubic projection, leverage correction and smoothing |
| `gain` | New presentation field: fitted SSE before addition minus fitted SSE after joint refit, in residual units |
| `noise` | New presentation field: `W.noiseFloor(D,S,variance) − W.noiseFloor(D,S+g,variance)` |
| `ratio`, `passes` | New presentation fields: gain/noise and comparison to the recorded threshold; nonpositive noise preserves the core's significant convention |
| `cleanup.probes`, removal costs | Existing chapter-three presentation audit; displayed on the residual scale by undoing its explainable-share normalization |

No scientific input, results contract or numerical-core file was edited. No new record field or export was introduced. Fixtures and numerical tests read the real shipped observation arrays and record fields.

## Live per-round table

Values below come from the final successful check's `outputs/wp_x17/live_numbers.json`. Gain and noise expectation are unnormalized residual units. “Block passes” compares that block's ratio with the recorded threshold; the round passes if any block passes. The chosen addition remains the largest **gain**, independently of which block has the largest ratio.

Recorded threshold: **6.635**. Supports: `1` → `1, u³` → `u, u³` → `u, u²`.

| Round | Before | Open block | Gain | Noise expectation | Ratio | Block passes | Round passes |
|---:|---|---|---:|---:|---:|---|---|
| 1 | empty | 1 | 3057.01835185 | 0.328306730849 | 9311.47023377 | yes | yes |
| 1 | empty | u | 1597.07870225 | 0.544674659759 | 2932.17000945 | yes | yes |
| 1 | empty | u² | 896.800905195 | 0.665498176162 | 1347.56328014 | yes | yes |
| 1 | empty | u³ | 582.725554067 | 0.759298017703 | 767.453016444 | yes | yes |
| 1 | empty | sin u | 5.09367325588 | 7.24439767687 | 0.703118945573 | no | yes |
| 1 | empty | cos u | 224.744245587 | 8.16716597499 | 27.5180210952 | yes | yes |
| 2 | 1 | u | 788.510979671 | 0.341822430064 | 2306.78536667 | yes | yes |
| 2 | 1 | u² | 1063.07575093 | 0.446701022949 | 2379.83728784 | yes | yes |
| 2 | 1 | u³ | 1228.93533897 | 0.548352486869 | 2241.14117907 | yes | yes |
| 2 | 1 | sin u | 2.65765867817 | 7.24704075583 | 0.366723296821 | no | yes |
| 2 | 1 | cos u | 5.3731680963 | 9.01766868657 | 0.595848914288 | no | yes |
| 3 | 1, u³ | u | 372.993493415 | 0.398911166729 | 935.028960142 | yes | yes |
| 3 | 1, u³ | u² | 325.215075524 | 0.577512603484 | 563.130698034 | yes | yes |
| 3 | 1, u³ | sin u | 6.14937300842 | 7.35151484664 | 0.836476989669 | no | yes |
| 3 | 1, u³ | cos u | 5.11094449623 | 9.01804902152 | 0.566746142545 | no | yes |
| 4 | u, u³ | 1 | 67.7040806173 | 0.222047638566 | 304.907906494 | yes | yes |
| 4 | u, u³ | u² | 95.7388142974 | 0.610182948712 | 156.901818544 | yes | yes |
| 4 | u, u³ | sin u | 16.7044511115 | 7.40819089348 | 2.25486240186 | no | yes |
| 4 | u, u³ | cos u | 3.5053497898 | 8.81709996099 | 0.397562668599 | no | yes |
| 5 | u, u² | 1 | 0.0951000265377 | 0.220529809671 | 0.43123433825 | no | no |
| 5 | u, u² | u³ | 1.4639944364 | 0.745958778049 | 1.96256747622 | no | no |
| 5 | u, u² | sin u | 17.1234039571 | 7.39271499311 | 2.3162537678 | no | no |
| 5 | u, u² | cos u | 0.523046935752 | 8.83464451798 | 0.0592040726356 | no | no |

| Round | Added | Removed | Candidate after clean-up |
|---:|---|---|---|
| 1 | 1 | none | 1 |
| 2 | u³ | none | 1, u³ |
| 3 | u | 1 | u, u³ |
| 4 | u² | u³ | u, u² |

Round five: the maximum ratio is **2.3162537678** for `sin u`, below **6.635**. There is no fifth candidate, addition or removal. The last candidate stays `u, u²`.

## Verification

- Allowed fast presentation suite: **38 passed in 95.63 seconds**. Evidence: `outputs/wp_x17/presentation_tests.txt`. Excludes `test_wisp_explainer_x2.py` and the base data suite. No full `-k wisp` run and no exports.
- New numerical test independently integrates the real arrays, solves refits using NumPy least squares, reconstructs local cubic/leverage-corrected/smoothed variance, propagates it through weak-row endpoint incidence and orthogonal projection, and checks every gain, noise expectation, ratio and decision. The threshold is independently checked against the squared two-sided standard-normal quantile. Rounds one through four pass, round five fails.
- The real-page DOM harness executes both shipped scripts in German and English. It checks all five new pages, masthead/dots, persistent SVG, test/add/clean-up phase boundaries, full replay, exact three-second end hold, deterministic seek and reduced-motion equivalence. The separate geometry harness checks finite/nonnegative geometry, actual removals, matched chart dimensions and both magnifiers.
- Build guards pass, including rejection of a corrupted stop count. Existing first-step, joint-refit and FoBa guards also pass.
- `check_wisp_explainer_js.py`: **six reference cases pass**, largest relative coefficient error **5.82e-13**. Evidence: `outputs/wp_x17/numerical_checks.txt`.
- `node --check` passes for `app.js`, `pages.js`, `wisp_slides_dom.cjs` and `check_wisp_stop_scene.cjs`.
- No browser layout claim is made: Claude runs the browser check, as requested. The fit checker measures chapter-four text overlaps and stage bounds at the new samples.

Reproduce in PowerShell:

```powershell
$tests = @(rg --files analysis/tests | Where-Object { $_ -match 'test_wisp_explainer_x.*\.py$' -and $_ -notmatch 'test_wisp_explainer_x2\.py$' })
python -m pytest $tests -q -p no:cacheprovider
python analysis/scripts/explainer/check_wisp_explainer_js.py
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The last command is for Claude's browser acceptance, not a command executed in this session.

## Rebuild

- Immediate rebuild: **byte-identical**, **11487274 bytes**.
- SHA-256: `5494dbba75338e1e37e1c4f5af4ef80cf0327106765c761def84b63b687312b9`.
- Evidence: `outputs/wp_x17/rebuild.json`.

Files remain uncommitted. No Git operations, Julia runs, cluster jobs or campaigns were performed.
