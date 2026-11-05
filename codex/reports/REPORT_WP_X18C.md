# WP-X18c ? chapter five recap layout

Status: **blocked ? Umgebung, nicht Sache**. Source, tests and rebuilt HTML are complete. Browser acceptance remains unverified because both browser launch paths fail with access denied. No zero-overlap or rendered-size pass is claimed.

## Changes

The eight one-line descriptions now form a numbered HTML list in the page's left text column, using the unchanged bilingual translation keys. Matching numbers precede the eight stage names on the persistent SVG. Each box now has two lines: name and live result. The optional mini-graphics were removed.

The SVG name/result text, loop label and chip labels use 16 SVG pixels. Name and result baselines are separated by 23 SVG pixels. Eight 50-pixel-high boxes occupy y = 4, 58, 140, 192, 244, 306, 360 and 414 in the unchanged 800 ? 480 viewBox. Test/add/cleanup have a separate enclosing loop rectangle and the unchanged translated loop label. Four separate outlined support groups enclose the candidates' seven real term chips. Exactly one highlight walks through all eight stages.

The browser checker audits the HTML descriptions together with the SVG labels for intersections. It requires every visible recap label to render at >= 14 CSS pixels, checks all name/result bounds against their boxes, and checks candidate chip counts and containment inside their own group. The existing 17 recap sampling times, both heights (768/657) and both languages remain in place.

Files changed for this task:

- `explainer/wisp/src/index.html`: numbered translated descriptions.
- `explainer/wisp/src/app.js`: two-line boxes, numbering, grouped support chips, removed miniatures.
- `explainer/wisp/src/pages.css`: typography and description/group styling.
- `explainer/wisp/src/pages.js`: fit acceptance for the revised layout.
- `analysis/tests/wisp_slides_dom.cjs`: description mapping, integer section count, support grouping and all eight highlight positions.
- `explainer/wisp/dist/wisp_explainer.html`: rebuilt delivery.

## Live-field provenance

No new scientific fields, records, exports or schemas were introduced. All original results remain visible:

- Measurements: existing `live.teaching.t.length`, 512.
- Weak sections: existing `live.featured[0].path[0].equations[0].n_rows`, 2529, rendered as **2 529** in German / **2,529** in English. The record-based expression and integer formatting from Claude's edits are preserved. The test now checks this field instead of the separately derived `m.rows.length`.
- Catalogue: existing teaching term catalogue, six terms.
- Test results: existing chapter-four `four.rounds[*].passes`.
- Additions/removals: existing chapter-three `three.rounds[*].addition` and `.removed`.
- Candidate count/supports: existing chapter-five adapter over `live.featured[0].stop_reference.supports` and candidate `row.active_idxs`, four candidates and seven displayed chips.
- Reconstruction results: existing candidate `row.reconstruction_r2_arithmetic`, values 0.7320530786397965, 0.948686252191979, 0.9957790201776506, 0.999956494802444.
- Winner/support/BIC: unchanged argmin over existing candidate `bic`; winner `path_004`, support `u, u?`, BIC 581.1558140942572.

## Verification on final files

- Final presentation DOM suite: **7 passed in 71.20 s**, including EN/DE delivered cases; `outputs/wp_x18c/final_dom.log`.
- Other presentation tests, excluding the scientific exporter suite `test_wisp_explainer_x2.py`: **46 passed in 49.94 s**; `outputs/wp_x18c/final_remaining.log`. Exact file selection: `outputs/wp_x18c/remaining_command.json`.
- Combined final presentation coverage: **53 passed**.
- Strict JS numerical checker: **exit 0**, six cases, maximum relative coefficient error 5.82e-13; `outputs/wp_x18c/js.log`.
- Node syntax checks for `src/app.js`, `src/pages.js` and the DOM harness: **exit 0**.
- Two sequential final builds: **byte-identical**, 11,521,374 bytes; SHA-256 `e21d205db66a316897b0115ddbb1c73239909dc2b8acd8f46548cb05faf10eb5`. Evidence: `outputs/wp_x18c/rebuild.json` and `build_1.log` / `build_2.log`.
- Final browser checker command: process **exit 1**, before producing any checks, with `PermissionError: [WinError 5] Access is denied` in Playwright's Windows pipe creation; `outputs/wp_x18c/fit.log`.
- Explicit Edge fallback: checker **exit 2**, Edge **2147483651**, **zero checks and zero screenshots**; `platform_channel.cc` reports access denied. Evidence: `outputs/wp_x18c/edge_fit.log` and `edge_evidence.json`. The PowerShell wrapper's exit code does not replace the checker's JSON exit field.

The earlier combined run had one failing newly added assertion because native German locale formatting uses a period; this page intentionally uses a space. The independent integer expectation was corrected to the required space grouping, and both final test batches above passed afterward.

## Remaining acceptance

Run outside the restricted browser-launch environment:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

Acceptance still requires zero overlaps and `chapterFiveOk` for all 17 recap samples in each of the four language/height combinations (68 sample checks), plus browser screenshots. Neither the DOM harness nor static geometry proves this.

Rebuild and reproduce presentation checks:

```text
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python analysis/scripts/explainer/check_wisp_explainer_js.py
python -m pytest analysis/tests/ -q -p no:cacheprovider --ignore=analysis/tests/test_wisp_explainer_x2.py -k wisp
```

No Git operations, commits, staging, exports, Julia, cluster jobs, scientific regression runs or campaigns were performed. All edits remain uncommitted. `codex/CURRENT_TASK.md` was not modified.
