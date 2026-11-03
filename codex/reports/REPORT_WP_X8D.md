# WP-X8d — page 3 review fixes

Status: implementation complete; browser acceptance blocked by the environment.

## Changes

Page 3 now renders constant coefficients alone (`10`, never `101`). Its equations use three significant digits, plain decimal notation, locale separators and a proper minus. Individual terms wrap at full font size, including the six-block equation. The stored true equation uses the same 18 px size as the selected equation (17 px at the smaller desktop height). A late KaTeX load skips these already rendered equations; the DOM harness explicitly tests that lifecycle case. Other pages retain their equation renderer.

The remaining-error bars in phases ① and ③ have a dashed noise marker and the requested translated label. The marker uses the existing `noiseVariance(teaching.t, teaching.observed)` and `noiseFloor(D, support, variance) / dot(D.b, D.b)` functions. The support is the one actually displayed: before addition in ①, after addition in ③. Phase ② also gives each gain as a share of `remainingBefore - floorBefore`.

The window plot selects the longest design window (16 sample intervals), and both captions omit “short”. All eight stage columns share a fixed 0–1 scale: 110 px per unit R² at 768 height and 80 px at 657 height. A separate fixed-height track aligns the baseline; negative R² is clamped to zero height while its number remains visible. Singular stage labels, equal-width padded chips, and “chosen: stage {k}” / “gewählt: Stufe {k}” are implemented.

No changes were made to compute.js or the three scientific data files. No scientific export, campaign, cluster job or Git operation was run. CURRENT_TASK.md was not modified.

## Data and computed noise floor

Inputs come from the same real export used by WP-X8c: `live.teaching.t`, `live.teaching.observed`, `live.windows`, `featured[0].path[].active_idxs`, and the candidates' `row.params` and reconstruction curves. Truth comes from the corresponding existing `results.cells[].truth`. The floors, gains and remaining fractions are presentation-derived quantities; no new exported field is assumed or added. The independently recomputed marker values are checked against compute.js on the full design, not a fixture with invented fields.

All following values are percentages of ‖b‖². “Before” is the state used for testing missing blocks; “after” is the recorded support after removal. Exact intermediate post-addition floors are also stored in `outputs/wisp_x8d/numerical.json` and checked in the DOM.

| Stage | Remaining before (%) | Floor before (%) | Remaining after (%) | Floor after (%) |
|---|---:|---:|---:|---:|
| 1 | 100.000000000 | 71.556453727 | 84.954981373 | 71.554837976 |
| 2 | 84.954981373 | 71.554837976 | 78.906815174 | 71.552139277 |
| 3 | 78.906815174 | 71.552139277 | 77.404343035 | 71.551268849 |
| 4 | 77.404343035 | 71.551268849 | 76.940372507 | 71.551937065 |
| 5 | 76.940372507 | 71.551937065 | 76.856100219 | 71.515554053 |
| 6 | 76.856100219 | 71.515554053 | 76.849744057 | 71.511815575 |
| 7 | 76.849744057 | 71.511815575 | 76.836625887 | 71.509316454 |
| 8 | 76.836625887 | 71.509316454 | 76.832663714 | 71.463868337 |

At stage 4 after removal, `(remaining - floor) / floor = 7.530803026 %`, within 10 %. The requested “almost only noise” sentence is therefore enabled. It appears in phase ① of stage 4, whose displayed pre-addition remaining is 77.404343035 % and floor 71.551268849 % (also within 10 %). Stages 1–3 do not qualify in phase ①. Stages 5–8 use combined views without phase ①, so the sentence is not added there. No numerical settings were adjusted.

## Acceptance

Final non-browser validation (`outputs/wisp_x8d/validate.py`):

- 51 tests passed in 95.48 s. The existing analysis code emitted 15,174 NumPy `trapz` deprecation warnings.
- Strict numerical checks: exit 0 (`strict.log`); maximum reported relative coefficient error 5.82e-13.
- Recorded-support and independent full-design gain/removal/noise-floor checks: exit 0 (`trace.log`, `numerical.json`).
- Both builds exited 0 and were byte-identical: 11,372,022 bytes, below the 14,000,000-byte HTML budget; the data budget also passed. SHA-256: `0d0ffb88ab55441f7e85adad3b8a16a0456720d6111759e520bade06dbcb0f33`.
- Frozen compute/data hashes were unchanged across validation; recorded in `outputs/wisp_x8d/acceptance.json`.

The bilingual no-layout DOM harness walks all 31 frames and the timed combined subviews. It checks constants, absence of scientific notation, wrapping term boundaries including six-block supports, gain labels, actual-support noise markers, the sentence condition, stage singular/plural, chosen legend, proportional R² height percentages, and late KaTeX loading. Existing numerical-path, removal, interaction and frozen-data checks remain in force.

Actual equation widths cannot be measured by this DOM harness, which intentionally has no layout engine. The real browser checker now measures each equation and term against its column in every frame, including the six-block case, in addition to the existing viewport overflow gates. That pixel assertion and the requested 1366 × 657 / 768 screenshot checks remain open.

Browser fit checker on the final build: exit 2, blocked before rendering. Playwright cannot create its transport (`PermissionError [WinError 5] Access is denied`). Edge fallback exits 2147483651 with Crashpad / Mojo `Access is denied (0x5)`. No screenshot or pixel-fit pass is claimed. Evidence is in `outputs/wisp_x8d/fit.log` and `outputs/wisp_explainer_checks/`.

**browser not runnable here — environment, not the task. Umgebung, nicht Sache.** Claude must run the fit checker for the outstanding browser acceptance.

## Reproduction

```text
python outputs/wisp_x8d/validate.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The validation helper limits BLAS/OpenMP to one thread for its short checks and writes only to its own output directory. Presentation test helpers retain their existing output locations. All deliverables remain uncommitted.
