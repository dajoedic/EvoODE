# REPORT WP-X12B

Implemented chapter-one readability fixes; changes remain uncommitted. Final acceptance is blocked: **browser not runnable here — environment, not the task**.

- S2: model-colour noise sticks, 1.5 px at 70% opacity; truth curve 2.5 px. Y tick labels are right-aligned and the bottom tick is omitted to separate it from the x-axis origin.
- S3: tangent spans 25% of the plot width, with a labelled slope triangle and travelling numerical readout.
- S4: 12-point zoom; three consecutive labelled neighbour pairs, each with 1100 ms for explanation and a connecting drop. Then 800 ms zoom-out and a 2600 ms sweep. Total including entry: 7700 ms. Bottom axis has ticks, zero line and a shared fixed bound of 58.69529178519294 (4 times maximum absolute clean slope 14.673822946298236). Of 511 neighbour slopes, 265 exceed the bound and appear as edge triangles with a count caption. Sweep dots acquire their final coordinates before appearing.
- S5: same fixed slope scale and clean slope line; labelled 2 px window triangles and 31 final long-window slopes.
- S6-S8: error bar at SVG y=447, label baseline 477, below the time-label baseline 440.
- S9: solid 3 px cubic appears before the ring and 3 px deviation stick. Five indexed deviations occupy a separate box at x=590..785; the plot ends at x=570 and its geometry is clipped. The final filled translucent band follows local-cubic predictions plus/minus sqrt(variance), independently checked in the DOM harness. The shorter result paragraph remains hidden until completion and then fades in; reduced motion disables the fade.
- Non-overlapping-window caption is visible only on S5-S8. One persistent stage, clock injection, vertical navigation and replay/reduced-motion behaviour are retained.

Scientific field provenance: existing `live.teaching.t`, `observed`, `truth`, and `sigma`, plus existing `live.windows`. Clean slopes, clipping count and local fitted centres are presentation calculations; variance still uses unchanged `WispCompute.noiseVariance`. No scientific data or `compute.js` was edited. No staging, commits or pushes were performed; `CURRENT_TASK.md` was not edited.

Validation of the final implementation:

- `python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp --tb=short`: exit 0, **51 passed, 333 deselected**, 168.97 s. Existing NumPy trapz warnings: 15174. Evidence: `outputs/wisp_explainer_checks/x12b_tests.txt`.
- Both strict checks exit 0: `check_wisp_explainer_js.py` (six reference/illustration paths; maximum relative coefficient error 5.82e-13) and `check_wisp_explainer_x2.py` (including three significance-rule references). Their console logs are in `outputs/wisp_explainer_checks/x12b_check_wisp_explainer_*.py.txt`.
- Two sequential builds after tests: exits 0/0, byte-identical, **11401093 bytes**, budget 14000000. SHA-256: `34e3ad5bd5eebab2677fb34af368dc1cc3e1c23d4be947ed8336235396f92456`. Evidence: `outputs/wisp_explainer_checks/x12b_rebuild.json`.
- DOM harness checks the three zoomed pair indices/labels, fixed scale and clipped marker count, final rendered coordinates, independent local fits and both filled-band boundaries, delayed result paragraph, caption scope, replay and reduced motion.
- `check_wisp_explainer_fit.py`: exit 2; Playwright `[WinError 5] Access is denied`, Edge fallback exit 2147483651. **0 viewport checks and 0 screenshots**. Evidence: `outputs/wisp_explainer_checks/x12b_fit_console.txt`, `wp_x12_fit.json`, `wp_x12_edge_fit.json` in the same directory. Actual SVG text bounding-box overlap checks for S2-S9 and the S9 box-versus-plot check are wired into `pages.js` fitcheck variants, but could not execute here. No pixel or non-overlap pass is claimed.

Remaining acceptance outside this sandbox:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

This must verify DE/EN at 1366 x 657 and 1366 x 768, including final SVG label bounds and screenshots.
