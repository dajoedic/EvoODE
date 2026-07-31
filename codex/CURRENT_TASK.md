# CURRENT TASK

**Language: Julia**

## WP-L2 — Derivative estimation as the binding constraint (diagnostic, no algorithm change)

### 1. Why this work package exists

WP-L1 delivered the stage potential probe and reported that no threshold grid point
separates System 26 ("stop at stage 3") from System 11 ("continue to stage 4"). That
headline is not trustworthy. The noise-floor rows required by WP-L1 show why:

- **System 26, equation 2, split A.** This equation is *exactly representable* in the
  stage-3 library, so the holdout residual of the full stage-3 library should sit at the
  noise floor of 4.3e-11. It sits at 3.7e-3 — eight orders of magnitude above. Fitting
  only the true support is worse still (5.7e-3).
- **System 11, equation 1, split A.** The analytic true right-hand side has a residual of
  4.606 on the fit block, while a least-squares fit of the very same true support reaches
  1.159 — the fit beats the truth by a factor of four. That is only possible if noise is
  being fitted. Consequently stage 4 (holdout 8.8e-2) looks *worse* than stage 2
  (5.1e-3): the cubic cliff is invisible.
- **System 3** behaves correctly throughout (analytic floor 8.2e-12, correct "stop at
  stage 2", no gain at stages 4/5).

The cause is the derivative estimate. `estimate_derivatives` in `src/optimize/pretune.jl`
is a plain central difference. System 11 starts at `du = -39.3` and System 26 equation 2
at `du = -31.4`, both sampled at `h = 0.05`. In those transients the finite-difference
error is of order 1 — larger than any signal the probe is meant to detect. The probe
works where the derivative estimate is accurate and fails where it is not.

A second, independent defect: **split B is structurally degenerate.** It fits on the
collapsed tail of the trajectory (train residuals around 1e-11, condition numbers up to
3.9e11) and extrapolates into the transient (holdout 1.8 up to 5.3e8). WP-L1 then took a
median across all three splits, mixing one usable split with one broken one, so the
"no separation" verdict is partly an aggregation artifact.

This work package establishes whether the look-ahead idea survives once the derivative
estimate is adequate — and measures a consequence that reaches beyond the probe.

### 2. Hard scope limits

Nothing under `src/` may be modified. In particular `estimate_derivatives` must stay
exactly as it is: it feeds the pretuning warm start and the v3 promotion signal, and
changing it would alter search behaviour and the config fingerprint. All alternative
estimators live inside the study code.

No ODE simulation inside the probe (generating each ground-truth trajectory once is of
course required), no BFGS, no EvoGrow population, no structure search, no RNG. No new
package dependencies. Nothing written to `studies/regression/history.jsonl`. No
integration into the algorithm — this remains a measurement.

Keep the WP-L1 outputs intact; write to a new script slug and its own output subfolder.

### 3. Part 1 — Which derivative estimator is good enough?

This part has a decisive ground truth available and must exploit it: the true right-hand
side of every system is known, so the *actual* pointwise error of any estimator can be
computed exactly.

Compare at least: the current central difference (mandatory, as the reference), a
higher-order finite-difference scheme, and a smoothing-based approach (spline or
Savitzky-Golay style). For each system, equation, and estimator, report the pointwise
error against the analytic derivative, summarised as RMS per time block and as a maximum,
so it is visible that the error concentrates in the transient.

Additionally implement a **Richardson-style error estimate**: compute derivatives on the
full grid and on a coarsened grid (every second point) and use their difference as a
data-only estimate of the local truncation error. This requires no knowledge of the truth
and is therefore usable inside a real algorithm. Validate it against the true pointwise
error computed above — report the correlation and whether it is a usable upper bound.
This validation is the point of Part 1: an error estimator that does not track the real
error is worthless downstream.

### 4. Part 2 — Re-run the probe with an adequate estimator

Repeat the WP-L1 stage-capacity measurement (same systems, same cumulative full-library
protocol, same per-equation expected stages, same design principle that both sides of
every comparison use the full library) under each estimator, side by side with the
baseline estimator, so every change in verdict is attributable.

Two additions:

- **Weighted least squares** as a separate variant, using the Richardson error estimate
  as per-point weights. Unweighted remains the reference; report both.
- **Per-point noise floor** instead of only a per-block one, derived from the Richardson
  estimate, so "gain" can be judged against the local error rather than a global average.

Keep the threshold sensitivity grid from WP-L1 rather than fixing constants.

### 5. Part 3 — Repair the splits

Do not aggregate across splits blindly. Define and apply an explicit validity criterion
for a split — for example a cap on the design-matrix condition number and a minimum
excitation requirement on the fit block — and report per split which systems and stages
fail it. Splits that fail must be excluded from any derived verdict and reported as
excluded, never silently averaged in. If split B is invalid on most systems, say so and
replace it with a better construction rather than keeping a broken column.

### 6. Part 4 — Is the v3 promotion signal contaminated?

This may matter more than the probe itself and must be reported separately.

WP-v3.4 uses `r_k`, the derivative residual on the observed trajectory, as the
per-equation promotion signal. If the finite-difference error on System 26 is of order 1,
then the plateau that drove v3's stage promotions was substantially a numerical artifact
rather than evidence of structural inadequacy — a second explanation for the Gate 2
failure, independent of the "wrong evidence" diagnosis.

Measure it. On System 26, for both equations, compute `r_k` under the baseline estimator
and under the best estimator from Part 1, for three concrete structures: the true
support, the support the search actually ended with according to WP-T2 (equation 2:
`{u1, u1^2}`; hardcode with a source comment), and the full stage-s libraries for
s = 1..5. Then report the **floor** of `r_k`: the residual that the true structure with
true parameters still produces purely because of derivative error.

The readout question, to be answered in prose: is that floor of the same order as the
`r_k` values on whose plateau v3 promoted? If yes, v3's promotion decisions on System 26
were driven by derivative error rather than by model inadequacy.

### 7. Pre-registered predictions

State these in the script header and confront them explicitly in the report, including
when they fail:

1. With an adequate estimator, System 3 keeps its correct verdict (stop at stage 2).
2. System 11 shows a large, split-stable holdout gain at stage 4.
3. System 26 equation 2 shows its stage-3 holdout residual dropping toward the analytic
   floor, and no relevant gain at stages 4 and 5.
4. The `r_k` floor on System 26 is of the same order as the observed `r_k` plateau.

If prediction 2 or 3 fails under every estimator, that is a genuine negative result: the
derivative space is then too weak on fast-transient systems to serve as a look-ahead
signal at all. Report that outcome as clearly as a positive one — do not soften it and do
not keep adding estimators until something works.

### 8. Outputs

A CSV of estimator errors (system, equation, estimator, block, RMS error, max error,
Richardson estimate, ratio of estimate to true error), a CSV of stage-capacity rows in
the WP-L1 schema extended by estimator and weighting columns, a CSV or JSON for the
Part-4 `r_k` measurement, plus a human-readable report that answers in prose, with the
numbers attached: which estimator is adequate and where the baseline fails; whether the
separation of Systems 26 and 11 now succeeds and under which thresholds; the confusion
matrix over all equations of the eight exact systems; which splits were excluded and why;
and the Part-4 verdict on `r_k` contamination.

Write results incrementally per system so an abort costs at most the current system.

### 9. Tests

Unit tests on synthetic data with an analytically known derivative: each estimator's
error must decrease at the expected order under grid refinement, the Richardson estimate
must track the true error on a function with a known third derivative, the weighting must
reduce to the unweighted case for constant weights, and the split validity criterion must
reject a deliberately degenerate block.

### 10. Execution

Still cheap: no ODE simulation inside the probe, no BFGS, no search. Run it and report
the actual numbers as part of the delivery. If it has not finished within roughly 20
minutes, stop and report that — it would mean something in the setup is wrong.

Do not modify `src/`. Do not touch `studies/regression/`. Do not commit `outputs/`.
