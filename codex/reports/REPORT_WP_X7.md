# WP-X7 report

Status: blocked — browser not runnable here — environment, not the task.

## Delivered

The presentation still contains **19 pages**. Page 1 (`p-hook`) now introduces differential equations through rates of change, a browser-generated dish beside its synchronised growth curve, five history stations, and a bridge to `p-challenge`. The old `problem-chart`, `x4_problem` and `x4_why` have been removed. This page contains neither a formula nor `data-tex`, and does not read scientific measurements for its illustration.

The opening illustration is inline SVG. An IntersectionObserver starts it on first visibility; it runs once for **6000 ms**. Replay restarts the same sequence. Reduced motion renders the final state immediately, including when the preference changes while animation is running. A browser without IntersectionObserver starts the illustration immediately. Narrow layouts use a vertical timeline with 16 px page gutters. The short-screen layout places the caption beside the dish/curve to retain room for all five stations. Actual pixel fit remains unverified because browser launch is blocked.

Page 2 retains the existing term catalogue, coefficients, simulation, meter, hint ladder, reset, punchline and reveal. Its new heading and deck explain structure and parameters, with both words emphasised. Each term card labels its checkbox as structure and its coefficient controls as parameter weight. The noise percentage comes from the existing `live.teaching.sigma` field through `pct(teaching.sigma)`; the real source is `live.teaching`, cell `sys0003_ic1_s0.03_r0_n1`, sigma **0.03**. The existing tests compare its times and observations with that real cell's `observed.t` and `observed.x`. No new scientific field or data file was introduced.

The README now identifies the hook as an illustration and the challenge, noise and weak-form figures as using the real System 3 teaching cell. All added explanatory prose carries `data-claim="review"`. No glossary credit or external resource was added. No wording changes against the supplied DE/EN table were made; the challenge deck is split into translated spans to preserve emphasis and insert its data-derived percentage.

Page 3 (`p-solution`) and all later pages retain their content and behavior. `compute.js`, `live.json`, `results.json` and `manifest.json` match the frozen WP-X4 SHA-256 fingerprints.

## Illustrative constants

The dish uses the closed-form logistic curve with normalised capacity **K = 1**, initial occupancy **0.012**, growth rate **10**, and illustrative time **0 to 1**. Time is mapped to **6 seconds**, with **160** curve intervals. No equation or constants are shown on page 1.

Cell positions use an LCG with seed **731**, multiplier **1664525**, increment **1013904223**, and unsigned 32-bit arithmetic. A disk of radius **72** uses a **9**-unit grid with up to **1.5** units of coordinate jitter; a seeded Fisher–Yates shuffle determines appearance order. Dot radius is **2.9**. Dish outline radius is **79**. The same instantaneous occupancy controls both visible dot count and curve endpoint. These are illustration constants, independent of all exported measurements and numerical WISP code.

## Validation

Evidence is retained in `outputs/wisp_x7/`: `validation.json`, `tests.log`, `build_0.log`, `build_1.log`, `numerical.log`, `numerical_x2.log`, `input_hashes.json`, `fit.json`, and `edge_fit.json`.

The full suite passes: **37 passed, 15174 warnings in 213.96s**. This comprises all **35** prior tests plus **2** new WP-X7 tests. Warnings are the existing NumPy `trapz` deprecation. The existing real-page EN/DE DOM harness additionally executes delayed first visibility, the midpoint and final animation states, increasing dot count, deterministic replay, deterministic reinitialisation, reduced-motion final-state equality, the data-derived noise percentage, and both per-card labels. Existing richer-schema swap, provenance/counts, frozen inputs, navigation, wheel routing, fallback and challenge behavior tests pass.

Both strict numerical checkers exit **0**. Six path comparisons pass with maximum relative coefficient error **5.82e-13**. Three significance-rule checks pass at stop steps **4, 3, 2**.

After the final scoped CSS fit adjustment, two final builds both exit **0** and produce byte-identical HTML of **11,338,828 bytes**, below **14,000,000 bytes**. Data size remains **14,308,875 bytes**. Final HTML SHA-256:

```text
c583466a881b50763aebf403fb7a2a538e116de3a9006cd3217f2f2c5d00b77b
```

Reproduce the non-browser acceptance with:

```text
python outputs/wisp_x7/validate.py
```

## Open browser acceptance

Attempted:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

Playwright fails before browser launch with **[WinError 5] Access is denied**. Edge fallback exits **2147483651**, including `platform_channel.cc ... Access is denied (0x5)`. The checker's JSON records exit **2**, **0** viewport checks and **0** screenshots; the shell process returned **1** with a trailing Playwright subprocess traceback. Its existing WP-X6-named JSON outputs were copied into the WP-X7 evidence directory as `fit.json` and `edge_fit.json` without changing the checker.

Claude must run the command outside this sandbox to verify EN/DE layout at **1366 × 768** and **1366 × 657**, actual browser wheel routing, screenshots, and narrow-screen rendering. No successful browser fit or visual approval is claimed. This is **Umgebung, nicht Sache**.

All changes remain uncommitted. `CURRENT_TASK.md` was not edited. No Git operations, Julia runs, cluster jobs, campaigns, regression/survey runs or scientific manifests were performed.
