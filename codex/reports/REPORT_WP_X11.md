# WP-X11 — tests and fit checker

Implemented the chapter-1 test/checker updates without editing `src/`, `compute.js`, or data. Rebuilt `explainer/wisp/dist/wisp_explainer.html` with the README's HTML builder. Changes remain uncommitted; no Git operations were performed.

- Updated source inventory assertions to 27 sections and the complete first-ten section order, including `p-c1-noise`.
- Updated delivered DOM/browser inventory to 10 pages, eight sub-step dots and eight eyebrow totals. Arrow events now test linear left/right navigation and chapter up/down navigation, including up from every chapter-1 page and input arrow protection.
- Adapted the animation harness to horizontal sub-step animations in both directions, retaining intermediate eased vertical scrolling at chapter boundaries and the gesture lock checks.
- Added four parameterized cases: morph and noise, each in EN/DE. Morph checks all 512 dot coordinates against actual neighbour differences/midpoint times and original observations, the final hidden dot, pressed states, notes, axis labels, animation progress, reverse animation and immediate reduced-motion changes. Noise checks the entire variance array against `noiseVariance`, mean relative noise, formatted estimate/sigma/floor, agreement with the 1f floor, nine highlighted points and slider redraw. Local cubics are compared with independent NumPy least-squares references at centres 0, 171 and 511, with 17 evaluation times per centre.

## Data provenance

The DOM fixture is derived from the assembled real HTML and its embedded data. `live.teaching.t`, `live.teaching.observed`, and `live.teaching.sigma` are existing fields from `explainer/wisp/data/live.json`; no record fields were invented. The floor comes from the existing `WispChapterOne.model.floor` / `WispSolo` calculation and is compared with the rendered `c1-text-5`. The fixture-only `cubic` references are calculated by NumPy from those same real teaching observations; they are not record fields or delivered data.

## Executed validation

| Command/check | Result |
|---|---|
| `python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp` | Exit 0: **55 passed**, 333 deselected, 63.20 s; 15,174 existing `np.trapz` deprecation warnings |
| `python -m pytest analysis/tests/test_wisp_explainer_x3.py -q -p no:cacheprovider` after final assertion refinements | Exit 0: **11 passed**, 16.47 s |
| `python analysis/scripts/explainer/check_wisp_explainer_x2.py` | Exit 0: all six illustration/reference paths and three significance-rule cases passed; maximum reported relative coefficient error 5.82e-13 |
| `python analysis/scripts/explainer/build_wisp_explainer_html_x2.py` | Exit 0; first-step numerical gate passed |
| Two HTML assemblies in `test_assembly_rebuild_is_byte_identical` | Byte-identical; evidence in `outputs/wisp_x4/rebuild.json` |
| HTML size | 11,390,000 / 14,000,000 bytes |
| Data size | 14,308,875 / 17,000,000 bytes |

HTML SHA-256: `5921ddc81cb89b81ca5bfc197db133f54ba2cf4cb656d64c51c75c98a23a6ebc`.

## Remaining browser acceptance

`python analysis/scripts/explainer/check_wisp_explainer_fit.py` was executed and failed before page execution. Playwright could not create its transport (`PermissionError: [WinError 5] Access is denied`). The Edge CLI fallback failed its viewport probe (process exit 2147483651). The checker evidence records exit 2 / fallback exit 2, **0 fit checks and 0 screenshots**, in `outputs/wisp_explainer_checks/wp_x6_fit.json` and `wp_x6_edge_fit.json`; the shell command returned 1. No layout pass is claimed.

Status: **blocked — browser not runnable here — environment, not the task**. Claude must run the same fit-check command outside this sandbox to complete acceptance at both desktop heights and in both languages.
