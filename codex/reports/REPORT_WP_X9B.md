# WP-X9b — page 3 display fixes

Page 3 displays **31** consecutive windows, each **16 sample intervals** long, starting at sample 0; adjacent windows share only their endpoint. Previously it displayed 496 overlapping longest-length windows. Measured dots and every selected prediction use exactly these same 31 rows and their time centres. All fits still use the full design. Dots have radius 5.5 SVG units (approximately 4 screen pixels at the desktop chart size) and full opacity.

The eyebrow is visible above the headline in snapped mode. The y-axis label is horizontal above the axis, translated as “Änderung von u” / “change of u”. The time domain is the complete measured range 0–10, giving ticks 0, 2.5, 5, 7.5, 10 with language-specific formatting. The requested DE/EN explanation of displayed versus computed windows appears below the chart. Shared chart options retain their prior defaults; only page 3 enables the new options.

## Acceptance evidence

- Final validation: **49 tests passed in 53.88 s**; 15,174 existing dependency warnings. The actual-record bilingual DOM harness checks all six selections, exact consecutive longest-window endpoints, measured values, prediction values, dot radius, horizontal label and round ticks. Translation and eyebrow CSS contracts also pass.
- Build twice: **exit 0**, byte-identical, **11,354,493 bytes**. SHA-256: `e06ffb09a78e4a0fc8e33d3299dbb2a18a52b1c072ab72a524e3a164abf0ab98`.
- Strict numerical checker: **exit 0**, including significance checks; maximum reported relative coefficient error **5.82e-13**.
- Gains, coefficients, normalized shares, noise floor and winner compare **exactly equal** against both the pre-edit snapshot and WP-X9a's numerical.json. Maximum absolute change: **0**. Displayed bar percentages remain **52.9, 27.6, 15.5, 10.1, 3.9, 0.1** in the existing order. Winner coefficient remains **6.8542379170198435**.
- SHA-256 checks confirm unchanged compute.js and all three data files. The other **18** section markups are byte-identical to the starting state. Existing fields used are teaching.t, teaching.observed and windows from the actual live.json; no data fields were added.
- Final fit checker: **exit 2**, **0 rendered checks, 0 screenshots**. Playwright transport creation fails with **WinError 5**, and Edge fallback exits **2147483651**. **Umgebung, nicht Sache.** Claude must run the fit checker to establish desktop fit, eyebrow visibility and phone overflow in a rendered browser.

Reproduce:

```text
python outputs/wisp_x9b/validate.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

Logs, frozen input hashes, before/after numerical values and deterministic-build evidence are in outputs/wisp_x9b/. No Git operation, scientific export, campaign or cluster run was performed. CURRENT_TASK.md was not changed. Deliverables remain uncommitted. Status is blocked solely on the rendered fit acceptance.
