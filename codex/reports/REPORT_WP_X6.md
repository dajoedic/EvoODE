# WP-X6 report

Status: blocked — browser not runnable here — environment, not the task.

## Delivered

The presentation still has 19 pages. Its opening is now problem → challenge → solution → headline. The old guessing page and its three invented future curves, direct end labels and styling are removed. No direct end-label logic is reused, so collision avoidance is unnecessary.

The challenge uses the same 512 real measurement times and observations as the opening chart: `live.teaching`, cell `sys0003_ic1_s0.03_r0_n1`, sigma 0.03. The tests compare these arrays directly with that real results record's `observed.t` and `observed.x`. Simulation starts at the first observation, rather than the clean initial condition. The existing presentation RK4 and `WispCompute.basis` are reused. No numerical search, FoBa, path or stop code changed.

Six term cards toggle the catalogue `1, u, u², u³, sin u, cos u`. Active cards provide a slider, numeric input and ± buttons. Keyboard range and numeric stepping use the same precision. Numeric typing preserves intermediate input, and clamps out-of-range finite values. The initial guess uses only u; reset restores that guess and does not reveal the answer.

The live equation and curve update with the controls. The meter reports R² against the noisy observations, using the full simulated trajectory rather than the display-clipped curve. Its visual bar clamps negative R² to zero, explicitly stated in its accessible label; the accompanying R² text retains negative values. Grades are far off, getting closer (R² ≥ 0.5), close (≥ 0.9), and very close (≥ 0.98). Non-finite simulations receive a divergence notice and an empty bar. Curves outside twice the largest absolute observation are omitted from the display and identified by the existing clipping notice. The page explicitly labels all this as an illustrative browser simulation, not WISP.

Reveal navigates to page 3. The reader's current equation is retained in page state and displayed in the same three-column comparison as the stored WISP equation and truth. The catalogue page now explains the building blocks and combinations, links back to the challenge, and retains its dimensional catalogue in More; it has no separate playground.

## Coefficient controls

| Term | Minimum | Maximum | Slider / fine step |
| --- | ---: | ---: | ---: |
| 1 | -10 | 10 | 0.01 |
| u | -2 | 2 | 0.001 |
| u² | -0.03 | 0.03 | 0.00001 |
| u³ | -0.001 | 0.001 | 0.000001 |
| sin u | -2 | 2 | 0.01 |
| cos u | -2 | 2 | 0.01 |

The linear range spans the running system's order-one growth coefficient. The quadratic range includes both signs with precision appropriate to an order-0.01 coefficient. Higher polynomial powers need smaller coefficients at this system's observed scale; the cubic control therefore has the smallest range and step. Constant and trigonometric terms retain room for alternative guesses. Direct entry supports finer values within each range. The bilingual DOM test derives the logistic coefficients from the existing exported illustration constants and verifies a measurement R² above 0.98, without exposing those numbers through hints or reset.

## Hint ladder

One click appends one hint; after three clicks the button is disabled. Further handler calls append nothing.

| Step | English | German |
| --- | --- | --- |
| 1 | Logistic growth needs two terms. | Logistisches Wachstum braucht zwei Terme. |
| 2 | Try u and u². | Versuche u und u². |
| 3 | The u² coefficient is small and negative. | Der Koeffizient von u² ist klein und negativ. |

## Polish

Solution and challenge model curves have an explicit accent stroke, width 4.5, and are drawn after the observations. The dots are smaller and lighter. Explorer labels use 1D, 2D, 3D (fittable/fittbar), 4D while preserving original stratum IDs in the data and filtering. Explorer Overview lays out its three charts with minimum widths inside the existing bordered internal scroller. The headline and FROLS page margins, panel padding and secondary text are condensed for the short viewport. These are implemented layout changes, not a claim of browser-measured fit.

## Validation

Final evidence: `outputs/wisp_x6/validation.json`, `tests.log`, `build_0.log`, `build_1.log`, `numerical.log`, `numerical_x2.log`, and `input_hashes.json`. Reproduce the non-browser checks with:

```text
python outputs/wisp_x6/validate.py
```

All 33 previous tests, adapted for the new opening, plus 2 additional WP-X6 tests pass: **35 passed, 15174 warnings in 35.83s**. Warnings are the existing NumPy trapz deprecation. The full real-page DOM harness executes in EN and DE and now checks term toggles, slider changes, direct entry, fine adjustment, equation/curve/score changes, the R² calculation from the first observation, visual meter agreement, reachable logistic coefficients, ordered hints, reveal navigation and equation preservation, reset and divergent guesses. Existing richer-schema swap, provenance/count, frozen-input, i18n, navigation, wheel, modal, fallback and story tests remain included.

Both strict numerical checkers exit 0. Six path comparisons pass, with maximum relative coefficient error **5.82e-13**. Three featured significance checks pass with stop steps **4, 3, 2**.

Two builds exit 0 and are byte-identical. Final HTML is **11,328,827 bytes**, below **14,000,000**. Data size remains **14,308,875 bytes**. HTML SHA-256:

```text
66b160d2a573627ee48b3b0abd0c90f56843a71bcde7a838f0359a588e327851
```

SHA-256 fingerprints for `compute.js`, `live.json`, `results.json`, and `manifest.json` exactly match the WP-X4 frozen-input evidence. All scientific field names are existing fields: `teaching.t`, `teaching.observed`, `teaching.sigma`, `teaching.cell_id`; matching cell `observed.t/x`; existing illustration constants for the test; existing stored equations and curve bundles for the solution. Coefficients, enabled flags, hints, translated labels and the illustrative R² are presentation state, not new result-record fields. No scientific data or Q7/Q8 results were added.

## Browser acceptance remains open

Command attempted:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The checker records exit **2**, **0** viewport checks and **0** screenshots. Playwright fails before launch with `[WinError 5] Access is denied`; Edge fallback exits **2147483651** with `platform_channel.cc ... Access is denied (0x5)`. Evidence: `outputs/wisp_explainer_checks/wp_x6_fit.json` and `wp_x6_edge_fit.json`. The checker now targets the headline by ID after its move to page 4 and writes WP-X6-specific evidence.

Acceptance item 3 is therefore unverified: EN/DE fit at 1366 × 768 and 1366 × 657, actual browser wheel navigation and screenshots still require Claude's run of the same command outside this sandbox. No pixel-fit or visual approval is claimed.

All changes remain uncommitted. CURRENT_TASK.md was not edited. No Git operations, cluster jobs, campaigns, regression/survey runs, Julia runs or new scientific manifests were performed.
