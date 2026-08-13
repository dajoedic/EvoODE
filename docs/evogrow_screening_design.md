# EvoGrow Screening Design Note: Derivative-Based Candidate Evaluation

> ## Status: closed — a performance optimization, never a quality lever
>
> Screening is settled and is **not** part of any scientific claim. It may make the search cheaper;
> it must never change what is discovered. Any result that depends on screening being on or off is a
> defect, not a finding.
>
> This note is the design record. `docs/architecture.md` marks the component accordingly.

## 1. Motivation and Measurement Status

The profiling result that motivates this note is narrow but strong: one cell,
System 26, seed 42, EvoGrow v2.2, 18 levels, with 370 parameter fits per case.
It is not yet a population-level conclusion across systems, seeds, or variants.

Measured in `outputs/studies/profiling/profile_eval_cost/summary.json`:

| Measure | Reference | Screening budgets |
|---|---:|---:|
| Runtime | 3222.6 s | 1189.8 s |
| ODE solves | 1,741,484 | 2,488,973 |
| Solve time | 3069.5 s | 1019.1 s |
| Cost per solve | 1.763 ms | 0.409 ms |
| Solve share of runtime | 95.3% | 85.7% |
| Non-solve overhead | 153.0 s | 166.0 s |
| Parameter fits | 370 | 370 |

Solver tuning already improved this cell by 2.71x. The remaining cost is still
dominated by repeated simulation: even after cheaper solver budgets, the solve
share is about 86%. Since the reference run spends only 153 s outside solver
time, a search-loop evaluation path that avoids integration entirely has an
upper bound near 21x on this cell (`3222.6 / 153.0`). That number is only an
upper bound: a derivative-screening implementation will add its own matrix
construction, linear algebra, ranking, and bookkeeping costs.

This is not merely a performance optimization. Replacing simulation loss during
candidate evaluation changes the criterion used for selection, plateau
detection, and stage promotion. It therefore changes the search process and must
be treated as a methodological variant.

## 2. The Screening Criterion

The proposed screening score is a derivative residual evaluated on the observed
trajectory:

```text
score(S) = mean over equations k and time points t_i of
           (dX_k/dt_estimated(t_i) - f_k(X(t_i); p_hat, S))^2
```

For each candidate structure `S`, the observed trajectory `X(t_i)` is kept
fixed. Derivatives `dX/dt_estimated` are estimated from the data, initially with
the same finite-difference scheme used in `src/optimize/pretune.jl`:

- forward difference at the first point,
- central difference for interior points,
- backward difference at the last point.

For each equation `k`, the active basis terms define a design matrix `Phi_k`.
Column `j` contains the value of active basis term `j` evaluated on the observed
state `X(t_i)` at each time point. Because EvoODE's current polynomial basis is
linear in the parameters, the best screening parameters for fixed structure are
available in closed form:

```text
p_hat_k = argmin_p ||Phi_k p - dX_k/dt_estimated||_2^2
```

This is the same least-squares problem already solved by
`pretune_parameters(...)`. Reusable pieces are:

- `estimate_derivatives(traj)`,
- `build_design_matrix(basis, active_idxs, X, t)`,
- the per-equation least-squares solve `Phi \ dX[:, k]`,
- the existing sanity fallback for non-finite or excessively large parameters.

What is missing is a first-class score function that returns a residual and
diagnostics rather than only a warm-start vector. The screening path would need
to expose the derivative residual, fitted screening parameters, rank/conditioning
diagnostics, and failure flags.

## 3. Two-Stage Evaluation

The design should be two-stage, not simulation-free.

Candidate generation and broad ranking should use the derivative residual.
Simulation remains necessary for calibrated validation of selected candidates.
The core open design choice is how often to simulate during the search:

1. Screen all candidates and simulate only the best `k` per level.
2. Screen all candidates during the search and simulate only the final best
   structure.

Recommended starting point: option 1. Simulating the best `k` candidates per
level preserves a simulation-loss anchor for stage progression and protects
against derivative residuals that look good but simulate poorly. It also lets
the implementation degrade toward today's behavior by increasing `k`.

The value of `k` is an open decision. Candidate rules include:

- fixed `k`, for example `k = pop_size`,
- fraction of candidates, for example top 25%,
- adaptive `k`, increased when derivative residual and simulation loss disagree,
- always include the current incumbent even if its screening rank is worse.

The final candidate must be simulated. A separate open decision is whether the
final structure is refitted on full simulation fidelity. Today, `discover()`
does not refit unless the returned parameter count differs from the built RHS.
For a derivative-screening variant, the final report must explicitly state
whether final parameters are derivative-fit parameters, simulation-refit
parameters, or both. The recommended scientific default is: screen for search,
then perform a final full-fidelity simulation-based refit and validation before
recording the final loss. This is a behavior change and therefore belongs in a
new variant/fingerprint.

## 4. Stop Logic, Plateau Detection, and Stage Promotion

This is the critical design point. Today, loss tolerance, plateau detection, and
stage promotion are driven by simulation loss/objective. If the search loop is
ranked by derivative residual, those decisions cannot silently continue to use
the old signal unless selected candidates are still simulated at every level.

Clear position: stage progression must remain anchored to simulated loss unless
a new derivative-based stopping rule is explicitly introduced and validated.
Derivative residual may rank candidates cheaply, but promotion and termination
are part of EvoODE's complexity-control claim and should not be moved to a new
scale without a separate hypothesis.

The v0 log adds a second issue. According to the 2026-07-22 diary entry, 13
cells ran beyond level 18, and in all 13 the loss at level 18 was already
identical to the final result. No later level improved loss. Nevertheless, the
search continued to levels 26-29 because plateau detection caused stage
promotion rather than termination. Those post-level-18 levels consumed 15.8 of
40.5 compute-hours.

Derivative screening alone does not solve this. It reduces the cost of the
extra levels, but it does not decide whether extra stages are scientifically
needed. If stage promotion still means "plateau and more stages remain", the
algorithm may keep escalating complexity after simulation loss has saturated.

Therefore the screening variant needs an explicit progression policy:

- Candidate selection may use derivative residual.
- Level-end reporting must keep simulated loss for at least the selected
  candidates.
- Promotion should require evidence that added stage capacity can improve the
  simulated validation signal, not merely that the current stage plateaued.
- If no simulation improvement occurs over the effective stage budget, the
  policy must be allowed to terminate rather than promote.

The exact termination/promotion rule is not decided in this note. It is an open
scientific decision because it changes H1/H3 metrics (`final_stage`,
`stage_overshoot`, `wasted_levels`). What is decided here is that silently
driving plateau and promotion from derivative residual alone is not acceptable
for Paper 1 comparability.

## 5. Where Simulation Remains Indispensable

Derivative residual evaluates `f(X(t); p)` on the observed trajectory. It does
not test whether the ODE, started from `x0`, produces a stable trajectory.
Simulation remains indispensable for:

- trajectory stability over the full time span,
- accumulated error and phase drift,
- divergence under the fitted RHS,
- stiffness and solver behavior induced by the candidate,
- validation loss used in final metrics,
- plots and exported predictions,
- deciding whether a model is usable as a dynamical system rather than only a
  local derivative fit.

The final result must therefore continue to report simulated loss. A
derivative-screening score may become an internal search objective, but it must
not replace `loss` in `DiscoveryResult` or the paper metrics without a separate
protocol change.

## 6. Weaknesses and Risks

Finite differences are noise-sensitive. A derivative residual can prefer
structures that fit numerical differentiation artifacts, especially on noisy or
sparsely sampled trajectories. It also depends on sampling density: with coarse
time grids, derivative estimates can be biased even when the simulated
trajectory is easy to fit.

The largest methodological risk is objective mismatch. A structure with low
derivative residual may simulate poorly, while a structure with slightly worse
derivative residual may have better long-horizon trajectory behavior. This is
particularly plausible in coupled systems where local derivative errors can
propagate nonlinearly.

The approach would be falsified if, on exact systems under the current benchmark
protocol, derivative-screened search systematically selects structures with
worse simulated loss, worse pruned support match, or higher stage overshoot than
the simulation-ranked baseline at comparable or moderately reduced cost. A
single disagreement is not enough; the falsifying observation is a repeated
pattern showing that derivative residual is a poor proxy for the simulated
objective that Paper 1 evaluates.

## 7. Relation to the Scientific Contribution

Derivative-based screening moves EvoODE's evaluation closer to SINDy, because
both use derivative information and linear least squares on a library of
candidate functions. This must be stated plainly.

The contribution can remain distinct if the paper frames screening as a cheap
evaluation backend inside EvoODE's structured incremental search, not as the
scientific core. EvoODE would still differ from SINDy in:

- staged grammar release rather than a fixed full library,
- incremental structure growth rather than one global regression over all terms,
- explicit complexity-control and promotion decisions,
- population-based candidate exploration,
- final validation by simulated trajectory loss.

Clear position for Paper 1: derivative screening is compatible with the EvoODE
claim only if staged incremental growth remains the object of study and
simulation loss remains the reported recovery metric. If the method becomes
"run derivative regression on the full basis and sparsify", the distinction from
SINDy collapses. That is not the proposed design.

## 8. Comparability and Migration Path

Baseline v0 remains valid as the simulation-ranked baseline under fingerprint
`0c739d4e36ee6498`. It must not be rewritten. A derivative-screening variant
changes metric-relevant configuration and search behavior, so it requires a new
fingerprint and new records.

Recommended migration path:

1. Keep the existing simulation path as a named baseline.
2. Implement derivative screening as an explicit variant, not a replacement.
3. First run cheap diagnostic cells: Systems 3 and 11, all seeds, v2.2-style
   staged growth.
4. Then run the costly diagnostic cells that motivated the work: Systems 26, 31,
   and 63, selected seeds.
5. Only after comparing simulated final loss, pruned match, final stage, wasted
   levels, and runtime should Paper 1 decide whether the screening variant
   enters Phase B.

If derivative screening changes structures, that is not a bug; it is the result
of a new objective. The comparison must therefore report quality and complexity,
not just speed.

## 9. Open Decisions

1. Should every level simulate the top `k` screened candidates, or should
   simulation happen only at the end?

2. What is the rule for choosing `k`: fixed count, fraction of candidates, or
   adaptive disagreement-triggered simulation?

3. Should the final selected structure be refitted with simulation loss before
   final validation, and if so with which optimizer budgets?

4. Which signal drives stage promotion: simulated loss only, derivative
   residual only, or a hybrid rule?

5. Should plateau termination be allowed when simulated loss has saturated even
   if higher stages remain?

6. Which derivative estimator is acceptable under noisy or sparse sampling:
   the current finite-difference estimator, smoothed derivatives, or a
   trajectory-fitting derivative estimate?

7. What diagnostics define objective disagreement between derivative residual
   and simulated loss, and how large must the disagreement be before `k` is
   increased or the variant is rejected?

8. Does derivative screening apply only to EvoGrow v2.2/v3, or also to GP and
   future baselines?

9. Which experiment gate decides adoption for Phase B: a small diagnostic
   matrix, the full 63-system protocol, or a staged gate between the two?
