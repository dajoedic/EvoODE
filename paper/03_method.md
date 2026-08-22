# 3 Method

## 3.1 Problem setting

We observe a single trajectory of a dynamical system: states `x(t_1), …, x(t_T)` sampled on a
uniform grid, with `x(t) ∈ R^d`. We seek an interpretable system of ordinary differential equations

```text
du_k/dt = f_k(u),    k = 1, …, d
```

that reproduces the observed trajectory when integrated from the observed initial condition. The
target is not only predictive accuracy but a readable right-hand side, so `f_k` is restricted to a
form a modeller can inspect term by term.

## 3.2 Model representation: an additive staged basis

Each equation is an additive combination of basis functions with free coefficients,

```text
du_k/dt = Σ_{i ∈ S_k} p_i · φ_i(u),
```

where `S_k` is the *support* of equation `k` — the set of active terms — and `p` the coefficient
vector. Structure discovery is the search for the supports `S_1, …, S_d`; parameter estimation is
the fit of `p` given them.

The basis is **staged**: its terms are partitioned into ordered groups that are unlocked one after
another rather than offered all at once. The staged polynomial basis used throughout this work has
five stages,

| Stage | Terms | Count for dimension `d` |
|---|---|---|
| 1 | linear, `u_i` | `d` |
| 2 | self-quadratic, `u_i²` | `d` |
| 3 | pairwise products, `u_i·u_j`, `i < j` | `d(d−1)/2` |
| 4 | self-cubic, `u_i³` | `d` |
| 5 | trigonometric, `sin(u_i)`, `cos(u_i)` | `2d` |

The staging is by degree, not by parity. This has a consequence that recurs throughout the paper:
an odd nonlinearity that a system genuinely needs may only become approximable two stages after the
stage at which its degree would suggest, because the intervening stage contributes terms of the
wrong symmetry.

*Representational scope.* This basis represents 20 of the 63 ODEBench systems exactly. The remaining
43 contain terms outside it — constant offsets, saturating (rational) responses, mixed monomials of
degree three and above, and trigonometric terms with a scaled argument. Those systems are therefore
evaluated on approximation quality rather than on support recovery (§3.6), and the boundary is
reported rather than hidden: no claim about structural recovery in this paper extends to them.

## 3.3 Search: incremental growth under stage-local progression

The search proceeds in **levels**. A level evaluates a population of candidate structures, fits
their parameters, scores them by simulation loss, and generates the next population by *expanding*
the survivors — adding one term drawn from the currently unlocked stages. The search starts from
minimal structures: one randomly chosen term per equation.

Two policies govern the stages, and they are deliberately kept apart:

- **Stage progression policy** decides when a stage is kept, promoted or terminated. The substrate
  used here, `evogrow_v2_2_stage_local`, detects a plateau *within* the current stage and requires a
  minimum number of levels per stage before promotion is possible.
- **Stage usage policy** decides how strongly newly unlocked terms are encouraged once a stage
  opens.

Collapsing the two into one mechanism was tried and abandoned (§4). On promotion the population is
carried over unchanged — a deliberate warm start whose accepted risk is anchoring on structures
found under the narrower stage; the usage policy is the counter-measure.

The search operators are **additive only**: expansion adds terms and never removes them. Section 4.4
returns to what this costs.

## 3.4 Parameter estimation

Given a structure, coefficients are fitted by BFGS against the simulation loss — mean squared error
between the integrated candidate and the observed trajectory. Because the loss requires an ODE solve
per evaluation, this dominates the cost of the whole method.

Two devices make it affordable. First, an optional **warm start** ("pretuning"): derivatives are
estimated from the observed trajectory by finite differences, and the coefficients are initialised
by ordinary least squares on the resulting algebraic problem. Because the model is linear in its
coefficients, that problem has a closed-form solution. Second, a **deterministic evaluation budget**
of 20,000 loss evaluations per parameter fit. The budget is a count, not a wall-clock limit, so
results do not depend on machine speed — a precondition for reproducibility across heterogeneous
cluster nodes. Its value is not extrapolated: across dimensions 1 to 3 and parameter counts 1 to 18,
the latest observed first arrival at the best loss was evaluation 5,760, so the budget carries a
3.5x margin over the measured worst case.

## 3.5 The look-ahead stage cap

The contribution of this paper is a **per-equation upper bound on useful staged growth, derived from
the data before the search starts.** The cap reads only the observed trajectory and the basis. It
never inspects the evolving population, which is why it is search-independent and composes with the
progression policy of §3.3 rather than replacing it.

The construction is, for each equation `k` independently:

**Derivative estimate and its error scale.** Derivatives are estimated by a local polynomial fit
(half-width 4, degree 3). The estimation error is then itself estimated by Richardson extrapolation:
the same estimator is applied to a coarsened version of the trajectory, interpolated back to the
full grid, and the pointwise absolute difference is taken as the local error scale. This quantity
does double duty — it weights the least-squares fits below, and it defines the noise floor against
which residuals are judged.

**Stage residuals under cross-validation.** The time points are partitioned into several
deterministic fit/holdout splits. For every stage `s`, the design matrix over the *cumulative* basis
terms up to stage `s` is formed, a weighted least-squares fit is computed on the fit points, and the
residual is evaluated on the held-out points. A conditioning test marks stages whose design matrix is
too ill-conditioned or whose excitation is too low as unusable. The **floor** for a stage is the mean
squared Richardson error on the same held-out points — the residual level that derivative-estimation
error alone would produce.

**The walk.** Starting at the first stage that contributes terms, the procedure walks forward:

- If the residual at the current stage is still **above** the floor, it looks ahead up to
  `lookahead_horizon` stages for a stage whose residual drop counts as a genuine gain, relative to
  the current residual and the floor. If it finds one, it jumps there and records that a gain has
  been observed. If it finds none within the horizon, the walk **caps at the current stage** —
  provided a gain was observed earlier, and provided a successor stage is evaluable at all.
- If the residual has **reached the floor**, the question becomes whether anything later still
  helps. A later stage that drops the residual to at most 0.35 of the floor **reopens** the walk;
  otherwise the walk caps here.
- Where the evidence does not support either conclusion — no gain ever observed and residuals
  uninformative, or a stage that cannot be evaluated — the equation returns **no cap**.

**Aggregation.** Each split yields one decision; the per-equation cap is their majority, under a rule
that refuses a cap when an undecided decision sits at or below the candidate stage.

Three properties of this construction matter for the claims of the paper.

1. **A cap requires positive evidence.** The absence of a later gain is never by itself sufficient;
   a gain must have been observed before a cap is issued. This rule was bought with a defect (§4.3).
2. **All conditions are relative.** Thresholds compare residuals to each other and to the floor. No
   stage index and no system identity enters the rule.
3. **The horizon is the basis, not a tuning parameter.** `lookahead_horizon = 5` equals the number of
   basis stages, i.e. the walk looks to the end of the basis. Horizons 3, 4 and 5 produce identical
   caps on all 80 equation rows of the exact systems, so the parameter is inert above 3; the shipped
   value is chosen so that no tuned constant enters the method.

Two constants remain, and the paper reports them as constants rather than derivations: the reopen
ratio 0.35 and a floor-depth guard of 0.1 that prevents the reopen branch from firing on a floor so
shallow that the "improvement" is noise. Section 4.3 gives their status, including the measurement
showing that the first of them cannot be selected from the data.

## 3.6 Evaluation

**Exact and surrogate systems are never mixed into one structure-correctness metric.** A system is
*exact* if every one of its equations is representable in the basis; 20 of the 63 are.

*Exact systems* are scored on **support recovery**. Because the search may retain terms with
near-zero coefficients, support is compared after pruning: for evaluation only, a term is dropped
from equation `k` if

```text
|p_i| < max(1e-6, 1e-3 · max_j |p_j| in equation k).
```

Both the raw and the pruned match are recorded; the pruned match is the reported metric. Pruning
never affects search, fitting or population state.

*Surrogate systems* are scored on **R²** of the simulated trajectory, averaged over state
dimensions, together with the reached stage and stability observations.

*Search cost* is measured in counts — parameter fits, loss evaluations, ODE solves, levels and
stages. Wall-clock time is recorded as context and is never used as evidence for a method claim. The
reason is not fastidiousness: on this project's own measurements, evaluation counts and runtime
decouple by more than a factor of two within a single dimension class, so a cost claim derived from
counts alone would be wrong by that factor if read as time, and vice versa.

## 3.7 Reproducibility and record identity

Every run is deterministic given its seed. Each record carries three identity fields, and a set of
records is publishable only if all three are uniform across it:

1. the git commit hash of the code that produced it,
2. a configuration fingerprint over the experiment's constants,
3. a **behaviour fingerprint** of the cap decision function.

The third exists because the first two are insufficient. Configuration fingerprints hash constants;
a change to the cap's decision logic leaves them standing, so two records could share a fingerprint
and originate from differently deciding code. The behaviour fingerprint hashes the decisions that a
frozen probe of fixed cases draws out of the decision function. Its coverage is stated honestly in
§4.4: it observes the decision function only, not derivative estimation, floor computation, split
aggregation, or the search loop.
