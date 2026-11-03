# WP-X7d report

Status: **blocked ? browser not runnable here ? environment, not the task** (Umgebung, nicht Sache).

## Changes and scope

Removed the page 1 media element, its dashed-box styling and both `x7c_media` translations. The illustration now occupies the full figure width, with its caption directly below. Retained the X7c headline/deck/figure/history spacing and all five history entries.

Desktop SVG viewBox: **1020 ? 260**; height: **310 px**, reduced proportionally to **210 px** at desktop heights ?700 px. The dish's geometric diameter at the configured 1200 px content width is **250.94 px** (`2 ? 79 ? 1.35 ? min(1200/1020, 310/260)`). This is a configuration calculation, not a browser measurement. The curve extends beside it across the freed width. The time label baseline remains **y=246.9**, inside the 260-unit drawing area. Mobile geometry and animation logic are unchanged.

Source changes: `index.html`, hook-only rules in `pages.css`, hook SVG geometry in `app.js`, and the two translation deletions. Updated README, adapted one existing test and added the requested no-video/no-placeholder test; rebuilt `dist/wisp_explainer.html`.

`outputs/wisp_x7d/scope.json` records **5 passing scope comparisons** against retained pre-edit source: all other page sections (including pages 2 and 3) are identical; both translation tables differ only by the deleted key; JavaScript differs only in hook geometry; CSS outside the hook illustration selectors is identical. No scientific data or numerical implementation changed. Existing frozen input fingerprint acceptance passes.

## Final validation

Commands:

```text
python outputs/wisp_x7d/validate.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

- Validation runner: **exit 0**.
- Tests: **45 passed, 15174 warnings in 42.37 s**. Warnings are existing NumPy trapz deprecations.
- Both strict numerical checkers: **exit 0**; six coefficient comparisons, maximum relative error **5.82e-13**; significance stops **4, 3, 2**.
- Both final builds: **exit 0**, **byte-identical**.
- HTML: **11,347,666 bytes**, below **14,000,000**; scientific data: **14,308,875 bytes**.
- HTML SHA-256: `cb4975aad571c8b66bfa1959dc10763d3ab1604fa84815c0ea5d66928f3939e3`.

Evidence: `outputs/wisp_x7d/validation.json`, `tests.log`, `build_0.log`, `build_1.log`, `numerical.log`, `numerical_x2.log`, `input_hashes.json`, `scope.json`, `fit.log`, `fit.json`, `edge_fit.json` and pre-edit source in `before/`.

## Open acceptance

Fit checker: **process exit 2**, **0 viewport checks**, **0 screenshots**. Playwright failed with **[WinError 5] Access is denied**; Edge fallback exited **2147483651** with Access is denied (0x5). Claude must run the same fit command outside the sandbox. Actual diameter, full time-label visibility and scroll-free fit at **1366 ? 657** and **1366 ? 768**, in both languages, remain unverified. No browser-fit success is claimed.

All work remains uncommitted. CURRENT_TASK.md was not edited. No Git operations, data regeneration, cluster jobs, campaigns, regression/survey runs or manifests were performed.
