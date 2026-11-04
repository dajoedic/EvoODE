# WP-X13 — Chapter two

Implementation complete and uncommitted. Acceptance is **blocked only for browser layout: Umgebung, nicht Sache**. Playwright fails with `[WinError 5] Access is denied`; Edge fallback exits 2147483651. No browser layout pass is claimed.

Six German/English pages follow `p-c1-solution`; chapter `two` has its own masthead, progress and six dots. The existing persistent SVG, fixed-topology renderer, clock, window selection and share helpers serve both chapters. The first entry frame preserves chapter one's final geometry; the transition converts weak window changes into slopes and introduces the share bar. Chapter-one scenes, prose and original durations are retained.

Chapter two draws residuals and the estimated slope-noise band, jointly refits the constant with `u`, cycles through the five remaining catalogue terms, highlights the greatest gain, and shows the recorded second weak equation. Its closing question is the only correctness question. No true equation or later block replacement is revealed.

Field origins (actual `data/live.json`, teaching cell `sys0003_ic1_s0.03_r0_n1`; no invented fixtures):

| Value | Origin |
| --- | --- |
| Time, observations | Existing `teaching.t`, `teaching.observed` |
| Window lengths | Existing `windows`; displayed non-overlapping longest rows from the existing solo model |
| Second support | Live `W.path(...).steps[1].support`, checked against existing `featured[0].path[1].active_idxs[0]` |
| Candidate gains | Live `W.path(...).steps[1].gains`; joint least squares over all windows of all lengths |
| Candidate coefficients/errors | Existing compressed design and `W.leastSquares`, refitting both numbers |
| Final equation coefficients | Existing `featured[0].path[1].equations[0].coefficients` |
| Noise band | Frozen `W.noiseVariance`; endpoint variances summed, square-rooted and divided by each window duration |
| Shares | Existing solo noise floor/explainable denominator; cumulative explained gain divided by that denominator |
| Maximum displayed block value | Maximum of live `W.basis(observation)[winner]` |

Numeric evidence: `outputs/wisp_x13/numbers.json`. The constant is 6.8542379170; its explained share is 52.8943138184%. The joint `u` example changes the constant to 15.0745929738 and the `u` coefficient to −0.1559275052; its share is 66.5375905043%. The winning support is `[0,3]`, its gain is 0.06048166199 of the no-block error, and its share is 74.1580695438%. Its recorded coefficients are 12.8387660335 and −0.0000274664285333. Noise fraction stays 0.7155645373. The observed maximum of `u³` is 533533.7575, so the localized prose derives its rounded value live.

Validation on the final implementation:

- `python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp --tb=short`: **exit 0; 54 passed, 333 deselected**, 110.51 s. Existing NumPy warnings: 15174. Log: `outputs/wisp_x13/tests.txt`. Existing chapter-one geometry, replay and timing assertions remain; page inventories now include six additional pages.
- `python analysis/scripts/explainer/check_wisp_explainer_js.py`: **exit 0**. Log: `outputs/wisp_x13/strict_js.txt`.
- `python analysis/scripts/explainer/check_wisp_explainer_x2.py`: **exit 0**. Log: `outputs/wisp_x13/strict_x2.txt`.
- Two final `python analysis/scripts/explainer/build_wisp_explainer_html_x2.py` runs: **exit 0/0, byte-identical**, 11433075 bytes. SHA-256: `78e11d2ec2db39b4aa59126a7ef81cdde4a7aa63ad724413ba5d77e56984e3c8`. Evidence: `outputs/wisp_x13/rebuild.json`.
- Build gate independently checks all five joint fits against full-design least squares and exercises the mismatched-support failure. DOM checks cover both moving coefficients, candidate order/shares, actual SVG band geometry, recorded equation formatting, first-frame continuity, backwards replay and reduced motion.
- `python analysis/scripts/explainer/check_wisp_explainer_fit.py`: **exit 2; 0 viewport checks, 0 screenshots**. Evidence: `outputs/wisp_x13/fit_console.txt`, `fit.json`, `edge_fit.json`. Measurement now samples every chapter-two stage, including candidate transitions, text/data intersections and bar-row intersections. Browser interaction inventory includes both chapters.

Claude must run the fit command above outside the restricted environment for DE/EN at 1366×657 and 1366×768, including chapter-one and chapter-two samples. Scientific inputs, `compute.js`, results contract and `CURRENT_TASK.md` were not edited. No Git operations or scientific campaign jobs were performed.
