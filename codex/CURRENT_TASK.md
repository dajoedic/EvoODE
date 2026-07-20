# CURRENT TASK: WP-v3.2 — EvoGrowV3 struct and equation-wise stage state

**Language: Julia**

## Context

Gate 1 (2026-05-30) decided that EvoGrow v2.2 is not paper-ready for coupled systems.
The diagnosed failure mode is system-wide staged progression: all equations share one
global stage, so when one equation stalls the whole system is promoted, wasting budget on
higher-stage terms that other equations do not need.

EvoGrow v3 replaces the global stage state with a per-equation stage state. The full v3
design is frozen in `docs/evogrow_v3_design.md` (WP-v3.1). This task implements the first
slice of that design: the new strategy type and the per-equation stage-state scaffolding.

This task does **not** implement equation-local promotion, the derivative-residual signal,
or equation-aware child generation. Those are WP-v3.3, WP-v3.4, WP-v3.5. See "Scope
boundary" below — respecting it is the central requirement of this task.

## Goal

Introduce a new structure-search strategy `EvoGrowV3` that carries per-equation stage state
through the search loop, while reproducing EvoGrow v2.2 (`:stage_local`) behavior exactly.

The value of this slice is twofold:
- it establishes the per-equation state representation that WP-v3.3/v3.4/v3.5 build on, and
- it is a **regression anchor**: because promotion still happens in lockstep across all
  equations, `EvoGrowV3` must produce results identical to the equivalent `EvoGrow` v2.2
  configuration. Any later divergence is then attributable to the equation-local mechanisms,
  not to the refactor.

## Files

- **New file:** `src/structure/evogrow_v3.jl`, holding `EvoGrowV3` and its
  `search_structure` method.
- **Modify:** `src/EvoODE.jl` — add `include("structure/evogrow_v3.jl")` after the existing
  `include("structure/evogrow.jl")`, and add `EvoGrowV3` to the public exports next to
  `EvoGrow`.
- **Do not modify** `src/structure/evogrow.jl` other than what is unavoidable to share
  helpers (see Constraints). `EvoGrow`, `StageProgressionPolicy`, and `StageUsagePolicy`
  behavior must remain byte-for-byte unchanged.

## Required Content

### 1. `EvoGrowV3` strategy struct

A `Base.@kwdef struct EvoGrowV3 <: AbstractStructureSearch` mirroring the `EvoGrow` fields
one-to-one (`pop_size`, `n_levels`, `children_per_parent`, `max_terms_per_eq`, `λ`,
`progression`, `usage`, `use_pretuning`, `level_callback`) with the same defaults. Reuse the
existing `StageProgressionPolicy` and `StageUsagePolicy` types unchanged.

Rationale: keeping the field set identical lets a v2.2 configuration be lifted to v3 by only
changing the constructor name, which is what the regression check below relies on.

### 2. Per-equation stage state

The `search_structure(::EvoGrowV3, ...)` method must represent the stage state per equation
`k = 1..dim` instead of as a single global scalar:

```text
eq_stages::Vector{Int}                         # current stage per equation, init all 1
eq_levels_in_stage::Vector{Int}                # levels spent in current stage per equation
eq_plateau_histories::Vector{Vector{Float64}}  # per-equation plateau/objective window
```

These vectors are initialized (length `dim`) and updated at each level. The single global
stage used for basis queries and aggregate reporting is defined as
`current_stage = maximum(eq_stages)` (locked decision from the design note §2).

### 3. Lockstep bridge behavior (this WP only)

Because equation-local promotion is out of scope here, all equations must move together:

- Promotion decision reuses the existing v2.2 stage-local logic
  (`_stage_progression_decision`) computed on the aggregate/global history, exactly as
  `EvoGrow` does in its `:stage_local` branch.
- When the decision is `:promote`, advance **every** equation's stage by one
  (`eq_stages[k] += 1` for all `k`), reset every `eq_levels_in_stage[k]` to 0, and reset the
  per-equation plateau histories consistently with how v2.2 resets its per-stage history.
- Child generation, term availability, evaluation, selection, and stopping remain identical
  to the current `EvoGrow` `:stage_local` path. Reuse the shared helpers
  (`_allowed_terms`, `_current_stage_terms`, `_expand_with_usage_policy`, `_evaluate!`,
  `_init_population`, `should_stop` is not used on this path, etc.) via `current_stage`.

The net effect is that `EvoGrowV3` and `EvoGrow` (`:stage_local`, same usage policy) run the
identical algorithm; the only difference is that v3 additionally tracks `eq_stages` and
friends as vectors that happen to hold identical values across equations.

### 4. Meta output

The returned `meta` NamedTuple must keep **all** fields the current `EvoGrow` returns
(so existing analysis code and `discover()` keep working unchanged), and additionally expose
the per-equation state foundation:

| Field | Type | Definition |
|-------|------|------------|
| `eq_final_stages` | `Vector{Int}` | Final stage per equation at termination |
| `eq_stage_histories` | `Vector{Vector{Int}}` | Per-equation stage at each completed level |

The existing aggregate fields must stay consistent: `final_stage == maximum(eq_final_stages)`.

The remaining v3 metrics from the design note (`eq_overshoot`, `eq_wasted_levels`,
`eq_residual_log`, `eq_promotion_levels`) are **out of scope** here and belong to WP-v3.5.
Do not add placeholder residual logs, since the residual signal itself arrives in WP-v3.4.

### 5. Registration and export

Register the new file and export `EvoGrowV3` as described under "Files".

## Scope boundary (do not cross in this WP)

- No derivative-residual progress signal `r_k` (WP-v3.4).
- No per-equation / independent promotion — promotion stays lockstep-global (WP-v3.4).
- No equation-aware child generation that reads `eq_stages[k]` per equation (WP-v3.3).
- No new metrics beyond `eq_final_stages` / `eq_stage_histories` (WP-v3.5).

Leave clear seams where these plug in later: isolate the promotion decision and the
per-equation state update into their own small functions so WP-v3.4 can replace the lockstep
body without touching the main loop.

## Verification

1. The package loads with `using EvoODE` and `EvoGrowV3` is exported and constructible with
   default keyword arguments.
2. **Regression equivalence.** For at least System 3 (1D, `expected_stage=2`) and System 26
   (2D, `expected_stage=3`) — reuse the ground-truth RHS and trajectory setup from
   `studies/phase1_diag/run_phase1_diag.jl` — run both:
   - `EvoGrow` with `progression=:stage_local`, `usage=:hard`, `use_pretuning=false`, and
   - `EvoGrowV3` with the same configuration,
   using the same seed and the same `DiscoveryOptions`. The final `structure.active_idxs`
   must be identical and the final `loss` must match to within `1e-9` relative. Keep
   `n_levels` small (e.g. 8–12) so the check runs quickly.
3. `result.meta.structure.eq_final_stages` is a `Vector{Int}` of length `dim`, all entries
   equal (lockstep), and `maximum(eq_final_stages) == result.meta.structure.final_stage`.
4. `EvoGrow` results are unchanged: a quick before/after run of one existing benchmark or
   diagnostic system with `EvoGrow` gives the same loss as before this change.

Report the regression-equivalence outcome (identical / diverged, with the compared values)
explicitly when the task is done.

## Constraints

- Do not change `EvoGrow`, `StageProgressionPolicy`, `StageUsagePolicy`, or any existing
  behavior in `src/structure/evogrow.jl`. Shared helpers may be reused as-is; if a helper
  must be made accessible or slightly generalized, do it without altering the existing
  `EvoGrow` call path or its results.
- Reuse existing helpers (`Individual`, `_init_population`, `_allowed_terms`,
  `_current_stage_terms`, `_expand_with_usage_policy`, `_evaluate!`, `_plateau_reached`,
  `_stage_progression_decision`, `_validate_policy`) rather than duplicating them.
- Follow existing conventions: `Base.@kwdef` for the struct, in-place RHS untouched,
  `NamedTuple` meta, the existing logging pattern and verbosity levels.
- Keep the lockstep promotion faithful to v2.2 so the regression check in Verification 2
  actually passes; a divergence here means the refactor is wrong, not that v3 "works".
