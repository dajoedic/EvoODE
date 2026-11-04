# WP-X15 — implementation complete; browser acceptance blocked

Implemented in the source and rebuilt standalone HTML, without staging or committing.

- All 16 delivered chapter-one/two steps replay after a 3,000 ms end hold. Reduced motion renders the end state. Deterministic `seek` also accepts cycle offsets, including restart samples.
- Removed the chapter-one hands-on slider, its handler, styling and translation. Tests now assert its absence.
- Step 5 shows only the current length cloud, with a fixed slope scale, green reference and persistent RMS bars. Lengths are selected from `LIVE.windows`; RMS compares measured and true changes across identical sections. The chart states that it uses the true curve for this illustration.
- Step 8 shows the changing coefficient in a large equation and settles each fit at its existing optimum before setting its bar. Both chapters animate the ranking after each completed candidate; the final winner is highlighted.
- Both merged steps show their paragraphs together. Chapter two runs the initial `u` fit first, followed by the other candidates, without the former reading pause.
- Noise phases: A (0–7,500 ms) turns each deviation into its square and drops a rectangular contribution onto a stacked sum; B starts at 7,500 ms and displays the arithmetic mean plus the separate corrected noise estimate and band; C starts at 10,000 ms and fills the endpoint-noise floor. All results remain in the final state at 12,500 ms.

## Arithmetic and provenance

Existing real inputs are `live.json` → `teaching.t`, `teaching.observed`, `teaching.truth`, and `windows`. Existing single/joint fits, design rows, explained shares and noise floor are reused. No scientific input, exporter, results contract or frozen computation was edited.

The new presentation-only `squarePrefix` is the running sum of `(observed[i] - local_cubic_prediction[i])²`; it contains every point once. Its sum divided by the point count is explicitly labelled as that mean, **not** as the frozen variance. `W.noiseVariance` instead divides each squared residual by `1-h` (local cubic leverage), then averages neighbouring corrected values over up to 21 points. The existing `relative` is the mean of `sqrt(variance[i]) / abs(observed[i])`. The page describes the correction before showing that estimate. The endpoint floor still comes from the existing model.

The real-record DOM checks cover 512 points and 2,529 design windows; the floor is 0.7155645372738232. Independent checks recompute section RMS values, cubic predictions and the displayed raw sum from the real record. No invented record fields or substitute fixtures were introduced.

## Final validation

- HTML build: exit 0. Rebuild: byte-identical, 11,438,795 bytes. SHA-256: `ce7bd8d012209373b03c294156eac95088e83f504c78cad51f860140e2c7b862`.
- Fast presentation tests, excluding `test_wisp_explainer_x2.py`: **33 passed in 154.46 s**. Includes both languages, live equations, per-candidate rankings, RMS values, raw arithmetic, all delivered loop restarts, reduced motion and persistent SVG geometry.
- `check_wisp_explainer_js.py`: exit 0, six cases; maximum relative coefficient error 5.82e-13.
- Fit checker: **exit 2, blocked by environment**. Playwright fails with `[WinError 5] Access is denied`; Edge fallback also fails before page initialization (`Access is denied`). Zero browser checks and zero screenshots; label overlap, viewport fit and visual acceptance remain unverified.
- Fit sample tables now include each length and final bars, live-fit sweeps, per-candidate mid-sorts, noise phases A/B/C and a restart. Delivered inventory remains 18 pages, with 11 chapter-one and 5 chapter-two dots.

Evidence: `outputs/wisp_explainer_checks/wp_x15_rebuild.json`, `wp_x15_js.log`, `wp_x15_fit.log`, `wp_x12_fit.json`, `wp_x12_edge_fit.json`, `x12c_story_numbers.json`.

Browser acceptance for Claude, outside the sandbox:

```powershell
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

No full `-k wisp` suite, exports, reintegration, cluster jobs or campaign runs were started.
