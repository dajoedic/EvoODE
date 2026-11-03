# REPORT WP-X12D

All five chapter-1 changes implemented; work remains uncommitted. Acceptance is **blocked: browser unavailable (environment, not the task)**.

- S4: six time intervals across the plot (506/6 = 84.33 SVG units each), seven points across the window, radius 8, non-scaling 3 px triangle strokes and delta-t/delta-u labels on the legs. The window pans between eight pairs. Later zoom-out and sweep remain.
- S3 to S4: single panel shrinks during 0-450 ms, lower curve fades during 450-900 ms, lower axes appear at 900 ms. Upper ticks follow the shrinking frame. One scene renders directly during this transition.
- S10: all 512 measurements and the estimated band persist through the sum and at the end. Plot bottom y=302; sum bar y=415; deviation list remains beside the plot. S10/S11 use the same 708-unit bar width and noise segment.
- S11: full-width stacked bar y=42, one legend line y=102, six share rows from y=155 with 48-unit spacing.
- S7: 280 by 140 SVG-unit error chart, c ticks 0/c*/2c*, localized error-in-percent axis, orange sweep and green optimum. Chart labels end at y=201; residual plot starts at y=240.

Browser fit variants now check S10 end-state data bounding boxes (>=500 intersecting the plot, plus visible band), S11 text boxes against every other share row, and S4 neighbour-leg width >=60 CSS px. Transition samples include 0/300/600/899/900 ms. Synthetic DOM assertions cover all eight enlarged pairs, lower-axis timing, 512 retained points, band visibility, replay and reduced motion. No browser layout pass is claimed.

Validation (evidence under `outputs/wisp_explainer_checks/`):

- `python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp --tb=short`: exit 0; **51 passed, 333 deselected**, 198.51 s, 15174 existing NumPy deprecation warnings. Log: `x12d_tests.txt`.
- Final page: `python -m pytest analysis/tests/test_wisp_explainer_x3.py -q -p no:cacheprovider --tb=short`: exit 0; **7 passed**, 60.11 s. Log: `x12d_final_dom.txt`.
- `check_wisp_explainer_js.py` and `check_wisp_explainer_x2.py`: exit 0/0. Logs: `x12d_strict_js_console.txt`, `x12d_strict_x2_console.txt`.
- Two `python analysis/scripts/explainer/build_wisp_explainer_html_x2.py` builds: exit 0/0, byte-identical, **11415934 bytes**, below 14000000. SHA-256: `d0a148fac525a3fcbf9d8d28da57ae096712f534b3cfd30f89c0f58b1324748e`. Evidence: `x12d_rebuild.json`; hash verified after tests.
- `python analysis/scripts/explainer/check_wisp_explainer_fit.py`: exit **2**; Playwright `[WinError 5] Access is denied`, Edge fallback exit 2147483651. **0 viewport checks, 0 screenshots**. Evidence: `x12d_fit_console.txt`, `wp_x12_fit.json`, `wp_x12_edge_fit.json`.

Claude must run the fit command above for DE/EN at 1366 x 657 and 1366 x 768, including the bounding-box variants. Scientific inputs and compute.js are unchanged. CURRENT_TASK.md was not edited; no Git operations, cluster jobs or campaigns were performed.
