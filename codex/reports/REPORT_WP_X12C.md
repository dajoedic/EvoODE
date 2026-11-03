# REPORT WP-X12C

Implemented the second chapter-one review round. Work remains uncommitted. Final acceptance is **blocked: browser not runnable here — environment, not the task**.

The masthead now contains the clickable chapter indicator; the second navigation bar is removed. A 3 px line tracks chapter position. DE/EN each contain 12 chapter steps, including `noise-why`. Step numbers appear only in the eyebrow. The stage, injected clock, deterministic replay and reduced-motion end states are retained.

Timings (milliseconds, including the existing 900 ms scene transition):

| Step | State | Total | Sequence after transition |
|---|---|---:|---|
| 1 | data | 900 | Measurements |
| 2 | noise-visible | 2300 | Curve 900; residuals 500 |
| 3 | slope | 3800 | Moving tangent 2900; backward entry reverses the zoom over 2200 |
| 4 | secants | 16100 | Highlight 400; hold 200; zoom 1600; 8 pairs × 1200; zoom out 800; sweep 2600 |
| 5 | windows | 9100 | Lengths 2/4/8/16 × 1200; zoom out 800; full-view display |
| 6 | error-empty | 2900 | Residual construction 2000 |
| 7 | fit | 4900 | Continuous 0 → 2c* sweep 4000; optimum first appears at sweep time 2000 |
| 8 | every | 16900 | 6 blocks × 2500 (appearance 400, sweep 1400, flight 700); sort 1000 |
| 9 | noise-why | 900 | Winner prediction, residuals, remaining-error bar and question |
| 10 | noise-estimate | 11600 | Zoom 700; 5 examples × 900; zoom out 1000; all-point sweep 2500; endpoint-variance sum 2000 |
| 11 | percent | 900 | Same noise segment width and styling as step 10 |
| 12 | solution | 900 | Winner equation |

S4 pairs draw their triangle, reveal Δt/Δu and the numerical slope, then drop the slope marker. S5 retains eight faded orange constructions and uses blue for its triangles, labels and 31 final long-window dots. New readouts occupy reserved space outside data plots. S7 retains the green optimum while the orange sweep continues and while the optional slider moves. S10 replaces its plot with the sum display after the all-point sweep.

Scientific provenance: existing `live.teaching.t`, `observed`, `truth`, `sigma`, and `live.windows`; existing single-block design and least-squares coefficients. Endpoint contributions are `(variance[a] + variance[b]) / dot(b,b)` for each actual design window, using unchanged `WispCompute.noiseVariance`. No scientific data or `compute.js` edits. Real-record DOM evidence: 512 points, 2529 design windows, c* = 6.8542379170200505, sweep endpoint = 13.708475834040101, winner remaining error = 0.8495498137346918, noise floor = 0.7155645372738232. The counter reaches 512; the sum is checked against the endpoint contributions and the next step's rendered segment width.

Validation:

- `python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp --tb=short`: exit 0, **51 passed, 333 deselected**, 266.15 s; 15174 existing NumPy `trapz` deprecation warnings. Log: `outputs/wisp_explainer_checks/x12c_tests.txt`.
- Final rebuilt-page DOM/navigation/source checks: `python -m pytest analysis/tests/test_wisp_explainer_x3.py -q -p no:cacheprovider --tb=short`: exit 0, **7 passed**, 43.46 s. Log: `outputs/wisp_explainer_checks/x12c_final_dom.txt`. Checks include eight labelled pairs and drops, blue 2/4/8/16 constructions, 31 final long-window slopes, the independent dot-product least-squares coefficient, the exact optimum crossing, continued sweep, manual-slider isolation, the 512-point counter, intermediate endpoint-variance sums, identical floor-bar widths, reverse replay and reduced motion. Numbers above are from this run: `x12c_story_numbers.json` in the same output directory.
- Both strict checks exit 0: `check_wisp_explainer_js.py` and `check_wisp_explainer_x2.py`. Maximum reported relative coefficient error: 5.82e-13. Logs: `outputs/wisp_explainer_checks/x12c_strict_js.txt` and `x12c_strict_x2.txt`.
- Two sequential final builds: exit 0/0, byte-identical, **11412226 bytes**, budget 14000000. SHA-256: `96c348a868b36f13fc2f237f9dde1cd3f4007fd2c1ad2a37a4495c4d82b6a9cd`. Evidence: `outputs/wisp_explainer_checks/x12c_rebuild.json`.
- Final fit-check command: exit **2**. Evidence: `outputs/wisp_explainer_checks/x12c_fit_console.txt`, `wp_x12_fit.json`, and `wp_x12_edge_fit.json`.

The fit checker now samples intermediate highlight, zoom, pair, long-window, coefficient, noise-sweep and sum phases, including actual SVG text bounds and new annotation-versus-data-dot bounds. Browser launch failed with Playwright `[WinError 5] Access is denied`; Edge fallback exited 2147483651. Zero viewport checks and zero screenshots were produced. No visual fit or non-overlap pass is claimed.

Remaining external acceptance:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

This must pass DE/EN at 1366 × 657 and 1366 × 768, including sampled animation phases. `CURRENT_TASK.md` was not edited; no Git operations, campaigns or cluster runs were performed.
