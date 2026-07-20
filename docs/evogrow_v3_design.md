# EvoGrow v3 Design Note: Per-Equation Progress Signal and Promotion Rule

## 1. Motivation

EvoGrow v2.2 uses system-wide staged progression: all equations share a single current stage, a single level counter within that stage, and a single plateau history. Gate 1 on 2026-05-30 determined that this design is not paper-ready for coupled systems. The diagnosed failure mode is that one stalled equation can force the entire system to escalate, spending search budget on higher-stage terms for equations that do not need them. This escalation without targeted improvement was confirmed in the Gate 1 diagnostic on Systems 26 and 63.

EvoGrow v3 replaces global staged progression with per-equation staged progression. The v3 hypothesis is that each equation should promote only when its own residual stagnates, concentrating search budget where structural capacity is needed while preventing unnecessary escalation in equations that are already explained. This preserves staged growth as the controlling mechanism, but makes the promotion signal equation-local rather than system-wide.

## 2. State Representation

EvoGrow v2.2 represents staged progression with one global state shared by all equations:

```text
current_stage::Int
levels_in_current_stage::Int
plateau_history::Vector{Float64}
```

EvoGrow v3 replaces this with per-equation state, with one entry for each equation `k = 1..dim`:

```text
eq_stages::Vector{Int}                         # current stage per equation
eq_levels_in_stage::Vector{Int}                # levels spent in current stage per equation
eq_plateau_histories::Vector{Vector{Float64}}  # plateau window per equation
```

Each equation independently tracks its own current stage, level budget within that stage, and plateau history. Promotion decisions are therefore local to each equation rather than synchronized across the full system.

For compatibility with the staged basis and existing aggregate analysis, the single global `current_stage` remains defined as `maximum(eq_stages)`. This value is an aggregate view, not the state that drives promotion. An equation may use terms up to its own `eq_stages[k]`. Cross-terms involving variables from equations `i` and `j` require `min(eq_stages[i], eq_stages[j]) >= required_stage`, where `required_stage` is the stage assigned to that cross-term by the staged basis.

## 3. Per-Equation Progress Signal

### Signal Definition

For equation `k`, the progress signal is the derivative residual:

```text
r_k = mean_t (dx_k/dt_estimated - f_k(x(t); params))^2
```

Here, `dx_k/dt_estimated` is obtained by finite differences on the observed trajectory, consistent with the derivative estimation already used in `src/optimize/pretune.jl`. The model right-hand side `f_k(x(t); params)` is evaluated on the observed trajectory, not on the simulated trajectory. The mean is taken over all time points.

This signal measures how well the current best individual explains equation `k` on the observed data, independent of ODE solve quality. The residual is computed per equation, so each equation receives its own progress signal for plateau detection and promotion.

### Why Derivative Residual

The derivative residual is more sensitive to structural misfit than trajectory mean squared error. Trajectory error accumulates simulation error, which can obscure equation-local structural information in coupled systems. In particular, a structural error in one equation can propagate through the simulated trajectory and appear as error in other equations.

The derivative residual isolates each equation's fit quality at the data level. Because `f_k(x(t); params)` is evaluated on the observed trajectory, the signal asks whether the current structure explains the observed derivative of equation `k`, rather than whether the full simulated system stayed close to the observed trajectory over time.

### Fallback

If derivative estimation fails numerically, for example because the time resolution is insufficient for stable finite differences, EvoGrow v3 falls back to the per-dimension trajectory residual:

```text
r_k = mean_t (x_k(t)_simulated - x_k(t)_observed)^2
```

This fallback is equation-local but depends on simulated trajectory quality. Any run that uses this fallback must flag it in the result metadata so downstream analysis can distinguish derivative-residual promotion from trajectory-residual promotion.

## 4. Per-Equation Promotion Rule

At the end of each level, each equation evaluates its own promotion condition independently. Multiple equations can promote in the same level, and equations that do not satisfy the rule remain at their current stage.

Equation `k` promotes from stage `s` to stage `s + 1` when all three conditions hold:

1. Minimum stage budget: `eq_levels_in_stage[k] >= effective_min_per_stage`, where `effective_min_per_stage = max(min_levels_per_stage, plateau_window + 1)`.
2. Per-equation plateau: the last `plateau_window` values of `r_k` satisfy `max(r_k_window) - min(r_k_window) < plateau_tol`. This is the same absolute plateau criterion used in v2.2, applied independently to each equation.
3. Per-equation residual above target: `r_k > loss_tol`. This is an equation-local tolerance check. If `r_k` is already near zero, additional structural capacity is unnecessary.

When the third condition is false, equation `k` stays at its current stage even if the minimum budget and plateau conditions hold. A well-explained equation does not promote solely because its residual is flat.

## 5. Global Termination

Global termination keeps the v2.2 hard-stop semantics, with the stage-exhaustion condition updated for per-equation stages:

1. `global_loss < loss_tol`: hard stop, evaluated on the simulated trajectory.
2. `total_levels >= max_levels`: hard level cap.
3. All equations are at maximum stage and all equations have plateaued: no further promotion is possible.

The third condition replaces the v2.2 "no more stages available" termination path. Under v3, the run may continue while at least one equation can still promote or can still improve at its current stage.

## 6. Equation-Aware Child Generation

For individual `i` in the population, equation `k` may use basis terms up to stage `eq_stages[k]`. This means child generation is equation-aware: each equation's candidate right-hand side is expanded according to its own stage rather than the aggregate `current_stage`.

Cross-term availability follows a stricter pairwise rule. A cross-term involving variables from equations `i` and `j` is available to equation `k` only if `min(eq_stages[i], eq_stages[j]) >= required_stage_for_cross_term`. The required stage for a cross-term is determined by the `StagedPolynomialBasis` stage assignment, unchanged from v2.2.

After equation `k` promotes, child generation for equation `k` preferentially samples from the newly unlocked terms. The existing `StageUsagePolicy` logic is applied per equation. The `:hard`, `:soft`, and `:passive` policies retain their v2.2 meaning, but they are evaluated independently for each equation that promoted in the current level.

## 7. Population Behavior on Promotion

When one or more equations promote, the current population is carried over without modification. EvoGrow v3 uses the same warm-start policy as v2.2: individuals retain their full structure, fitted parameters, and accumulated search context across promotion events.

Equation-specific expansion is driven by child generation in the next level. A per-equation population reset is explicitly out of scope for v3. The rationale is the same as in v2.2: reset behavior changes the search dynamics enough that it should be reserved for a dedicated future variant rather than mixed into the first per-equation staging design.

## 8. New Metrics

The following metrics are stored in `result.meta.structure` and written to per-run output files:

| Field | Type | Definition |
|-------|------|------------|
| `eq_final_stages` | `Vector{Int}` | Final stage per equation at termination |
| `eq_stage_histories` | `Vector{Vector{Int}}` | Per-equation stage at each level |
| `eq_overshoot` | `Vector{Int}` | `max(0, eq_final_stages[k] - expected_stage)` per equation; requires expected-stage input |
| `eq_wasted_levels` | `Vector{Int}` | Levels spent above expected stage per equation |
| `eq_residual_log` | `Vector{Vector{Float64}}` | Per-equation derivative residual `r_k` at each level |
| `eq_promotion_levels` | `Vector{Vector{Int}}` | Level indices at which each equation promoted |

The existing global metrics remain defined as aggregates for compatibility with existing analysis code. `final_stage = maximum(eq_final_stages)`, and `stage_overshoot = maximum(eq_overshoot)`. The existing `wasted_levels` metric remains the global aggregate counterpart to `eq_wasted_levels`.

## 9. Open Questions

The following questions are not resolved by this design note and must be decided before WP-v3.2 implementation begins.

1. Derivative estimation granularity: Should `r_k` be re-evaluated once per level using the best individual, or once per candidate evaluation?

   Recommended resolution: evaluate `r_k` once per level on the best individual. This is cheaper than candidate-level residual logging and is sufficient for plateau detection because promotion is a level-end decision.

2. Cross-term stage assignment when equations are at different stages: If equation 1 is at Stage 2 and equation 2 is at Stage 3, is the cross-term `u1*u2` assigned to Stage 3 available to equation 1?

   Recommended resolution: yes, cross-terms follow `min(eq_stages[i], eq_stages[j]) >= required_stage`. The cross-term is available only when both participating equations have reached the required stage.

3. Basis stage query interface: Does `StagedPolynomialBasis` need a new method equivalent to `available_terms(basis, eq_stages, eq_idx)`, or is it sufficient to call the existing per-stage query with `eq_stages[eq_idx]`?

   Recommended resolution: the existing per-stage interface is sufficient. Cross-term filtering is handled in child generation, not in the basis.

4. Gradient of `r_k` with respect to `eq_stages`: Does the per-equation residual require a gradient with respect to the discrete stage state?

   Recommended resolution: no gradient is defined or needed. `r_k` is a discrete signal evaluated at parameter-optimal structures, and plateau detection is purely value-based. This matches the v2.2 staged-progression design.
