# WP-X16 ? chapter three: cleaning up

Implemented the seven-step German/English scroll story on the existing persistent SVG stage. Later chapters remain hidden. Source and rebuilt HTML remain uncommitted; no Git operations, exports, Julia runs or cluster work were performed.

## Delivered scenes

1. `c3-standing`: catalogue-ordered chips for the second-round model, its live explained share and the question whether every block still contributes.
2. `c3-probe`: omit each block in turn, fade its chip, refit the remainder using the existing weak-rate rows, and grow its removal-cost bar. No threshold is visible.
3. `c3-threshold`: show the dashed half-gain threshold and both staying blocks. The short explanation and existing More dialog use the Kochbuch FoBa text. The factor is read from the live configuration.
4. `c3-linear`: animate the new linear block and its gain, probe all three blocks, fade/move out the constant while refitting, compact the remaining chips, and probe both remaining blocks again.
5. `c3-quadratic`: perform the corresponding quadratic addition and cubic removal. The tiny cubic cost has a three-significant-digit annotation, rather than rounding to zero. Probe both survivors again.
6. `c3-compare`: show four forward-only models beside four FoBa models, then reveal the true equation, weak-fit equation and coefficient comparisons. Truth coefficients come from the existing matching system's logistic constants, not the result row's fitted `params` field. The EvoGrow sentence is included.
7. `c3-next`: four candidate boxes, no candidate IDs, and the next gain on an unmagnified explained-share scale. The closing question leaves the choice and stopping decision open; no BIC, trajectory fit or stop rule appears.

All scenes use mounted fixed-topology geometry, the shared endless replay with a three-second end hold, deterministic `seek`, and end states for reduced motion. The two removal scenes keep a fixed cost-axis range across both probes. Interpretations carry `data-claim="review"`. Scientific values in chapter-three strings are live substitutions.

Chapter three is enabled, including its masthead and seven navigation dots. `src/gates.json` now sets `stop` to `significance`; the other two gates remain `pending`.

## Data provenance and build guard

The real source record is `live.teaching` for `sys0003_ic1_s0.03_r0_n1`: fields `t` and `observed` supply observations. Existing live configuration fields `cap`, `sse_stop`, `backward_fraction` and `windows` are passed unchanged to `W.path`. No changes were made to `compute.js` or `path`.

Existing `W.path` fields supply additions, removals, gains and supports. The presentation helper `thirdModel` audits every removal pass with `W.leastSquares` and the existing compression adapter (already checked verbatim against the numerical core). Costs, before/after models and the next gain are derived presentation quantities, not new record fields or exports. Every change is divided by the same `model.explainable` denominator used in chapter two.

Stored supports come from `live.featured[0].path[*].active_idxs[0]`, converted from one-based indices; candidate IDs and origins are verified against `path_001` through `path_004` and addition/addition/removal/removal. Truth support comes from `live.featured[0].truth_support[0]`. Both the build's Node guard and tests reject support/truth drift. The independent numerical test reconstructs all weak windows from the actual observation arrays and solves the full design with NumPy SVD, separately from the page's compressed JS solves.

True coefficient inputs are existing `live.illustrations[*].constants` selected by the matching results cell's `system_id`. The true values are 0.79 and -0.01063257065948856; the final weak fit gives 0.7849282623265948 and -0.010525641345774649.

## Live numbers

All gains, thresholds, removal costs and explained shares below are percentages of the explainable part above the frozen noise floor, exactly chapter two's scale. Thus losses and gains are percentage points on that scale. The normalized noise floor is 0.7155645372738232; the denominator is 0.2844354627261768.

| Round | Added | Gain | Threshold | First-probe costs | Final support | Explained share |
|---|---|---:|---:|---|---|---:|
| 1 | 1 | 52.894313818 | 26.447156909 | 1: 52.894313818 | 1 | 52.894313818 |
| 2 | u? | 21.263755725 | 10.631877863 | 1: 64.075412268; u?: 21.263755725 | 1, u? | 74.158069544 |
| 3 | u | 6.453750885 | 3.226875442 | 1: 1.171455475; u: 6.453750885; u?: 14.074229924 | u, u? | 79.440364953 |
| 4 | u? | 1.656528782 | 0.828264391 | u: 11.579463532; u?: 1.656528782; u?: 0.025330885 | u, u? | 81.071562850 |

- Round 3, repeated probe after removal: u: 69.357707678; u?: 51.806778122. Both exceed the unchanged threshold.
- Round 4, repeated probe after removal: u: 65.554590738; u?: 53.437976019. Both exceed the unchanged threshold.

The measured constant-removal cost is 18.151544682% of the linear newcomer's gain, rather than the approximate third mentioned in the task's informal expectation. It is below the required half-gain threshold. No page value was taken from that expectation.

The next best term is `sin u`: gain 0.296279119 percentage points. The page does not infer a stopping decision from it.

Raw computed values: `outputs/wp_x16/live_numbers.json`; independent-check output: `outputs/wp_x16/unit_numbers.json`.

## Verification

- Final allowed presentation suite: **35 passed in 72.50 s**. This includes the bilingual full-app DOM harness, all seven chapter-three supports, live bar values and thresholds, repeated probes, fixed SVG identity, actual replay through the injected clock, deterministic cycle seeking and reduced motion. Command (PowerShell):
  ```powershell
  $tests = @(rg --files analysis/tests | Where-Object { $_ -match 'test_wisp_explainer_x.*\.py$' -and $_ -notmatch 'test_wisp_explainer_x2\.py$' })
  python -m pytest $tests -q -p no:cacheprovider
  ```
- `python analysis/scripts/explainer/check_wisp_explainer_js.py`: all six illustration/reference cases pass; largest reported relative coefficient error is 5.82e-13.
- `node analysis/scripts/explainer/check_wisp_work.cjs explainer/wisp outputs/wp_x16/live_numbers.json`: single-block, joint-fit and four-step FoBa/truth guards pass, including intentional mismatch rejection.
- `python analysis/scripts/explainer/build_wisp_explainer_html_x2.py`: final HTML built; immediate rebuild is byte-identical.
- Final HTML size: 11468837 bytes.
- SHA-256: `c5f0520710d6c0f334948a731b7222ac9f0d16cb26454044f62a8411a8851b0f`.
- Rebuild evidence: `outputs/wp_x16/rebuild.json`.

The browser fit checker is intentionally left for Claude, as assigned in CURRENT_TASK. It was not attempted here; this report makes no browser pixel or label-overlap acceptance claim. Its delivered page inventory and seven-dot/masthead checks are updated; `pages.js` supplies chapter-three label/dot checks and scene-specific sample tables for both removal passes and the reveal scenes. Claude's command:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

No full `-k wisp` suite or excluded `test_wisp_explainer_x2.py` was run.
