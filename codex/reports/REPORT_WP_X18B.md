# WP-X18b — chapter five review fixes

The recap's SVG rectangles were mounted after its labels and observation dots, covering their contents. Backgrounds now precede observations, chips, miniatures and text. Eight permanently mounted name/description/result triplets show measurements, weak sections, test, addition, cleanup, candidate list, trajectory fits and BIC selection. A bracket and loop arrow group the three repeated stages. Only the stage highlight changes during replay. Recap text uses 15 SVG pixels; browser acceptance additionally checks a rendered size of at least 14 CSS pixels.

The y-axis title now sits inside the top left of each plot, horizontally separated from its tick labels. Candidate scores and bound notes share a dedicated 338 × 42 readout rectangle, with space before the next row's support chips. The three winner equations each occupy one line at a common baseline in three columns. Both chapter-five mastheads now include the chapter number.

## Live field provenance

- Observation count: existing `live.teaching.t.length`; teaching cell `sys0003_ic1_s0.03_r0_n1`, 512 observations.
- Section and catalogue counts: existing shared weak-form model `m.rows.length` and teaching catalogue `terms.length`; 2,529 sections for window lengths 1, 2, 4, 8 and 16, and six catalogue terms.
- Passed and failed rounds: existing live chapter-four model `four.rounds[*].passes`; no editorial round count.
- Added and removed terms: existing chapter-three model `three.rounds[*].addition` and `.removed`, computed from the real teaching observations.
- Four candidate support chips: existing `live.featured[0].stop_reference.supports`, matched against `candidate.row.active_idxs` by the unchanged shared chapter-five adapter.
- Candidate reconstruction R²: existing `candidate.row.reconstruction_r2_arithmetic`; current values before locale formatting are 0.7320530786397965, 0.948686252191979, 0.9957790201776506 and 0.999956494802444.
- Winning support and BIC: existing chapter-five argmin of stored `candidate.bic`; current winner `path_004`, support `u, u²`, BIC 581.1558140942572.
- All live numeric recap values use the existing locale formatter. No scientific exports, data records or schema changed.

## Verification

Validation evidence:

- Presentation suite: **53 passed in 242.87 s**; `outputs/wp_x18b/presentation.log`.
- Strict JS numerical checker: **exit 0**, six cases, maximum relative coefficient error 5.82e-13; `outputs/wp_x18b/js.log`.
- Two sequential final presentation builds: **byte-identical**, 11,519,645 bytes, SHA-256 `182a8f80f047d01a87eaeed291a0062a39a933e8062da256b1cbf7bd42ae0afa`; `outputs/wp_x18b/rebuild.json`.
- Final targeted source/DOM run on the rebuilt HTML: **10 passed in 117.61 s**, including both delivered-language DOM cases; `outputs/wp_x18b/final_targeted.log`.
- Browser fit checker: **checker exit 2, fallback exit 2, zero checks and zero screenshots**. Playwright failed with `PermissionError: [WinError 5] Access is denied`; Edge fallback exited 2147483651 with `platform_channel.cc` reporting access denied. Evidence: `outputs/wp_x18b/fit.log`, `outputs/wisp_explainer_checks/wp_x12_fit.json` and `wp_x12_edge_fit.json`. No zero-overlap or pixel-layout pass is claimed.

**Status: blocked — environment, not implementation (Umgebung, nicht Sache).** The requested browser proof of zero overlaps and readable rendering at both viewport heights in both languages remains open. Claude must run the unchanged browser acceptance command outside the restricted environment and review chapter-five screenshots. The implementation, tests and rebuilt HTML are complete and uncommitted.

Reproduction commands:

```text
python outputs/wp_x18b/validate.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The presentation suite excludes the scientific exporter test `test_wisp_explainer_x2.py`, following WP-X18 policy. The bilingual DOM harness checks all eight triplets for visible nonempty text, live counts/R²/BIC, support chips, paint order, loop label and masthead, plus three one-line equations. Fit-check samples cover every recap highlight boundary, final hold and loop restart. Browser checks require all triplets to be readable, the equations to share one baseline and the bound notes to remain inside their own readout rectangle; the existing all-label overlap test remains active.

No Git operations, exports, Julia, cluster jobs or campaigns were performed. Changes remain uncommitted.
