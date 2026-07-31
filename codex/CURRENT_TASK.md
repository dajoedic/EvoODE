# CURRENT TASK

**Language: Julia**

## WP-L3 — Floor-gated firing rule, identifiability, and the sampling limit (diagnostic)

### 1. Where WP-L2 left the question

WP-L2 answered the core question positively. With a smoothing-based derivative estimator
(`local_poly`, median RMS derivative error 1.78e-3 against 1.75e-2 for the central
difference; note that the higher-order finite difference `fd4` at 1.24e-2 is *not* the
lever), the stage-potential probe separates the two counterexamples cleanly:

- System 26 equation 2 drops to 5.24e-13 at stage 3 — its true stage, exactly
  representable — and gets *worse* at stages 4 and 5. In WP-L1 the same number was
  3.65e-3, ten orders of magnitude higher.
- System 11 drops to 7.60e-12 at stage 4 after sitting at 4.53e-5 through stages 2 and 3
  (stage 3 correctly detected as empty), and gets worse at stage 5.
- System 3 keeps its correct verdict.

Three defects remain, and this work package addresses them. None of them is a reason to
doubt the result above; all three concern how the verdict is derived from the profile.

### 2. Scope limits (unchanged from WP-L2)

No modification anywhere under `src/`. In particular `estimate_derivatives` stays as it
is — it feeds the pretuning warm start and the v3 promotion signal. No ODE simulation
inside the probe beyond generating trajectories, no BFGS, no EvoGrow population, no
structure search, no RNG, no new package dependencies. Nothing written to
`studies/regression/history.jsonl`. No integration into the algorithm.

Keep WP-L1 and WP-L2 outputs intact; use a new script slug and output subfolder. Reuse
the WP-L2 estimator and split machinery rather than reimplementing it; `local_poly` is
the default estimator from here on, with the central difference retained as reference.

### 3. Part 1 — The firing rule must consult the noise floor

WP-L2 computes a Richardson-based noise floor per equation and split but the firing rule
ignores it, and that is the direct cause of the three remaining overshoots, all on
System 54. For equation 1 of System 54 the floor is 8.0e-4 while every residual from
stage 1 onward lies at 5.9e-6 or below: the entire profile sits under the floor, so every
"gain" the rule fires on is noise.

Implement a floor-gated verdict as an additional rule variant, evaluated side by side
with the current threshold-only rule so the difference is attributable:

- a gain may only count if both the gain and the residual level it leads to are above the
  local noise floor;
- if the checkpoint residual is already at or below the floor, no further stage can be
  justified and the verdict is to stop.

Report the confusion matrix under both rules, per estimator and per weighting.

Do not present the floor-gated rule as a free improvement. On System 54 equations 2 and 3
the residual falls below the floor already at stage 2 (6.2e-4 against a floor of 1.55e-3,
and 1.71e-3 against 2.62e-3), so a floor-gated rule will *undershoot* there — stage 2
instead of the true stage 3. Both failure directions must be reported explicitly. The
honest reading, which the report must state, is that on Lorenz the derivative estimate
does not resolve the stage-3 cross terms at the given sampling.

### 4. Part 2 — Rank deficiency is a result, not a reason to drop equations

WP-L2 excluded all four equations of System 63 because stages 3 and above exceed the
condition cap, shrinking the confusion matrix from 16 equations to 12. That silently
removed the hardest cases and makes the WP-L2 matrix not comparable to the WP-L1 one.

The cause is structural, not numerical: the SEIR states sum to a constant, so there is an
exact linear dependency among the state variables and the higher-stage libraries are
rank-deficient along the trajectory. Consistent with that, equation 1 of System 63 already
reaches a holdout residual of 1.2e-14 at stage 2 although its true right-hand side
`-0.28·u1·u3` needs a stage-3 cross term — along this trajectory the cross term is not
identifiable.

Required changes:

- Introduce an explicit third verdict `not_identifiable`, distinct from
  `invalid_or_inconclusive`, triggered by rank deficiency or a condition cap breach.
  Equations carrying it stay in the reported population and are counted in their own
  category; they must never be silently dropped from the confusion matrix.
- Add a regularised fit variant (ridge or truncated SVD) so that a verdict can still be
  produced under collinearity, reported alongside the unregularised result rather than
  replacing it.
- Report across the whole suite how many equations are non-identifiable along their own
  trajectory in the sense above: their true stage is `s`, yet a lower-stage library
  already explains the derivative down to the noise floor.

That last number is a finding in its own right and must be stated prominently. It bounds
what *any* derivative-space method can decide from a single trajectory, and it is
relevant well beyond this probe.

### 5. Part 3 — Is System 54 estimator-limited or excitation-limited?

These two explanations are currently confounded, and they have opposite consequences. If
the derivative estimate is the limit, better estimation or denser sampling fixes it. If
the trajectory does not excite the term, no estimator will ever see it and the limit is a
property of the data.

The trajectories are generated in-house, so this is directly testable: regenerate the
affected systems at increased sampling density — for example two, four, and eight times
the benchmark `T`, with `u0` and `tspan` unchanged — and re-run the stage profile. Report
whether the stage-3 cliff on System 54 emerges as the derivative error falls, and at
which density.

Label this explicitly as a sampling-sensitivity study. It deliberately departs from the
frozen benchmark configuration and its results must never be mixed into the main
confusion matrix, which stays at the benchmark sampling.

Run the same density sweep on System 63 to separate its rank deficiency, which is a
conservation-law property and must *not* disappear with denser sampling, from ordinary
numerical ill-conditioning, which would.

### 6. Part 4 — Document the splits

WP-L2 introduced a fourth split D without describing it anywhere in the report. Document
the full split set: how each is constructed, what it is for, and the validity criterion
applied. Report per split how many equation-stage cells it contributes and how many it
loses to the validity criterion.

### 7. Pre-registered predictions

State these in the script header and confront them explicitly, including where they fail:

1. The floor-gated rule removes all three System-54 overshoots and introduces at most two
   undershoots, both on System 54.
2. Systems 3, 11, and 26 keep their correct verdicts under the floor-gated rule.
3. On System 54, increased sampling density lowers the derivative error enough for a
   stage-3 cliff to appear.
4. On System 63, the rank deficiency persists at every sampling density.

If prediction 3 fails, System 54 is excitation-limited rather than estimator-limited, and
that is the more interesting outcome — report it as such rather than treating it as a
shortfall.

### 8. Outputs

CSVs for the stage profiles under both rules, the identifiability classification per
equation, and the density sweep, plus a human-readable report answering in prose with the
numbers attached: the confusion matrix under both rules over the full 16 exact equations
with `not_identifiable` shown as its own category; how many equations are non-identifiable
along their trajectory; whether System 54 is estimator- or excitation-limited; and whether
System 63's rank deficiency is structural.

Write results incrementally per system so an abort costs at most the current system.

### 9. Tests

Unit tests on synthetic data: the floor-gated rule must reject a gain that lies below a
supplied floor and accept one above it; the rank-deficiency detection must fire on a
deliberately collinear design matrix and not on a well-conditioned one; the regularised
fit must reduce to the unregularised one as the regularisation goes to zero; the density
sweep must reproduce the benchmark result at the benchmark density.

### 10. Execution

Cheap as before, though the density sweep multiplies the work: no ODE simulation inside
the probe, no BFGS, no search. Run it and report the actual numbers. If it has not
finished within roughly 30 minutes, stop and report that.

Do not modify `src/`. Do not touch `studies/regression/`. Do not commit `outputs/`.
