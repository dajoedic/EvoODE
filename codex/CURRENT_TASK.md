# CURRENT TASK: WP-v3.1 — Design Note: Per-Equation Progress Signal and Promotion Rule

**Language: Julia**

## Context

Gate 1 (2026-05-30) decided that EvoGrow v2.2 is not paper-ready for coupled systems.
Diagnosed failure mode: system-wide staged progression forces all equations to escalate together
when one equation's progress stalls, wasting search budget on higher-stage terms irrelevant to
other equations (confirmed on Systems 26 and 63).

EvoGrow v3 replaces the global stage state with per-equation stage states so that each equation
can promote independently based on its own residual signal.

This task produces a design document that freezes all key decisions for the v3 implementation
before any code is written.

## Goal

Write `docs/evogrow_v3_design.md` — a complete design specification for EvoGrow v3.
No Julia code is produced in this task. The document is the deliverable.

## Output

**File:** `docs/evogrow_v3_design.md`

The document must contain exactly the sections described below.

---

## Required Sections and Content

### 1. Motivation

Two paragraphs:

- Paragraph 1: Describe the v2.2 failure mode (system-wide staging, escalation without
  targeted improvement, confirmed on Systems 26 and 63 in Gate 1 diagnostic).
- Paragraph 2: State the v3 hypothesis: per-equation staged progression allows each equation
  to promote only when its own residual stagnates, concentrating search budget where it is
  needed and preventing unnecessary escalation in already-explained equations.

### 2. State Representation

Describe the change from v2.2 to v3.

v2.2 global stage state (to be replaced):
```
current_stage::Int
levels_in_current_stage::Int
plateau_history::Vector{Float64}
```

v3 per-equation stage state (one entry per equation k = 1..dim):
```
eq_stages::Vector{Int}              # current stage per equation
eq_levels_in_stage::Vector{Int}     # levels spent in current stage per equation
eq_plateau_histories::Vector{Vector{Float64}}  # plateau window per equation
```

Each equation independently tracks its own stage, budget, and plateau history.

The single global `current_stage` is still tracked as `maximum(eq_stages)` for compatibility
with the basis: an equation can only use terms up to its own `eq_stages[k]`, but cross-terms
between equations i and j require `min(eq_stages[i], eq_stages[j]) >= required_stage`.

### 3. Per-Equation Progress Signal

#### Signal definition

For equation k, the progress signal is the derivative residual:

```
r_k = mean_t ( dx_k/dt_estimated - f_k(x(t); params) )²
```

where:
- `dx_k/dt_estimated` is obtained by finite differences on the observed trajectory,
  consistent with the derivative estimation already used in `src/optimize/pretune.jl`,
- `f_k(x(t); params)` is evaluated on the observed trajectory (not the simulated one),
- the mean is taken over all time points.

This signal measures how well the current best individual explains equation k on the
observed data, independent of ODE solve quality.

#### Why derivative residual

The derivative residual is more sensitive to structural misfit than trajectory MSE:
trajectory MSE accumulates simulation error which can obscure per-equation structural
information, especially in coupled systems where one equation's error propagates to others.
The derivative residual isolates each equation's fit quality at the data level.

#### Fallback

If derivative estimation fails numerically (e.g. insufficient time resolution), fall back
to the per-dimension trajectory residual:

```
r_k = mean_t ( x_k(t)_simulated - x_k(t)_observed )²
```

This fallback must be flagged in the result metadata.

### 4. Per-Equation Promotion Rule

Equation k promotes from stage s to s+1 when all three conditions hold:

1. **Minimum stage budget:** `eq_levels_in_stage[k] >= effective_min_per_stage`
   where `effective_min_per_stage = max(min_levels_per_stage, plateau_window + 1)`

2. **Per-equation plateau:** the last `plateau_window` values of `r_k` satisfy
   `max(r_k_window) - min(r_k_window) < plateau_tol`
   (same absolute plateau criterion as in v2.2, applied per-equation)

3. **Per-equation residual above target:** `r_k > loss_tol`
   (equation-local tolerance; if r_k is already near zero, no promotion needed)

When condition 3 is false (equation k already well-explained), equation k stays at its
current stage even if conditions 1 and 2 hold.

**Who triggers promotion:** At the end of each level, each equation evaluates its own
promotion condition independently. Multiple equations can promote in the same level.

### 5. Global Termination

Global termination conditions (unchanged from v2.2):

1. `global_loss < loss_tol` — hard stop, evaluated on simulated trajectory
2. `total_levels >= max_levels` — hard level cap
3. All equations at maximum stage AND all equations have plateau — no further
   promotion possible

Condition 3 replaces the v2.2 "no more stages available" termination path.

### 6. Equation-Aware Child Generation

For individual i in the population, equation k may use basis terms up to stage `eq_stages[k]`.

Cross-term availability rule:
- A cross-term involving variables from equations i and j is available to equation k
  if `min(eq_stages[i], eq_stages[j]) >= required_stage_for_cross_term`
- The required stage for cross-terms is determined by the `StagedPolynomialBasis` stage
  assignment (unchanged)

After equation k promotes, child generation for equation k preferentially samples from
the newly unlocked terms, using the existing `StageUsagePolicy` logic applied per-equation.
The usage policy (`:hard`, `:soft`, `:passive`) is applied independently for each equation
that promoted in the current level.

### 7. Population Behavior on Promotion

When one or more equations promote, the current population is carried over without
modification (warm-start, same policy as v2.2). Individuals retain their full structure;
equation-specific expansion is driven by the child generation step in the next level.

A per-equation population reset is explicitly out of scope for v3 (same rationale as
for v2.2: reserved for a dedicated future variant).

### 8. New Metrics

The following metrics must be stored in `result.meta.structure` and written to per-run
output files:

| Field | Type | Definition |
|-------|------|------------|
| `eq_final_stages` | `Vector{Int}` | Final stage per equation at termination |
| `eq_stage_histories` | `Vector{Vector{Int}}` | Per-equation stage at each level |
| `eq_overshoot` | `Vector{Int}` | `max(0, eq_final_stages[k] - expected_stage)` per equation (requires expected_stage input) |
| `eq_wasted_levels` | `Vector{Int}` | Levels spent above expected_stage per equation |
| `eq_residual_log` | `Vector{Vector{Float64}}` | Per-equation derivative residual `r_k` at each level |
| `eq_promotion_levels` | `Vector{Vector{Int}}` | Level indices at which each equation promoted |

The existing global metrics (`final_stage`, `stage_overshoot`, `wasted_levels`) remain
defined as aggregates: `final_stage = maximum(eq_final_stages)`,
`stage_overshoot = maximum(eq_overshoot)` for compatible use in existing analysis code.

### 9. Open Questions (to resolve before WP-v3.2)

The following questions are not resolved by this design note and must be decided before
implementation begins. Annotate each with a recommended resolution:

1. **Derivative estimation granularity:** Should `r_k` be re-evaluated once per level
   (using the best individual) or once per candidate evaluation?
   *Recommended: once per level on the best individual — cheaper and sufficient for
   plateau detection.*

2. **Cross-term stage assignment when equations are at different stages:** If equation 1
   is at Stage 2 and equation 2 is at Stage 3, is the cross-term `u1*u2` (Stage 3)
   available to equation 1? Recommended: yes, cross-terms follow
   `min(eq_stages[i], eq_stages[j]) >= required_stage`.

3. **Basis stage query interface:** Does `StagedPolynomialBasis` need a new method
   `available_terms(basis, eq_stages::Vector{Int}, eq_idx::Int)` or is it sufficient
   to call the existing `available_terms(basis, stage)` with `eq_stages[eq_idx]`?
   *Recommended: the existing per-stage interface is sufficient; cross-term filtering
   is handled in child generation, not in the basis.*

4. **Gradient of r_k w.r.t. eq_stages:** r_k is a discrete signal evaluated at
   parameter-optimal structures; there is no gradient. Plateau detection is purely
   value-based. Confirm this is the intended design. *Confirmed: same as v2.2.*

---

## Verification

After writing the document, verify:
1. All 9 sections are present with the content described above.
2. Open Questions section contains at least the 4 questions above with recommended resolutions.
3. No Julia code appears in the document (this is a design note, not an implementation spec).
4. The document is self-contained: a reader who has not seen PAPER_1.md or CLAUDE.md
   can understand the v3 design from this document alone.

## Constraints

- Write only `docs/evogrow_v3_design.md` — do not modify `src/`, `experiments/`, or
  any existing file.
- The document is a design freeze artifact. Phrase all decisions as fixed, not tentative.
- Do not add Julia code blocks for implementation — pseudocode is allowed where helpful.
