# PAPER_1.md — EvoODE Paper 1: Execution Roadmap and Working Plan

This document is the authoritative execution plan for EvoODE Paper 1.
It replaces the previous narrative roadmap and defines all phases, work packages,
go/no-go criteria, risks, and design decisions.

For the scientific narrative, positioning, and experimental protocol, see:
- `CLAUDE.md` — architecture, reproducibility protocol, algorithm design
- `docs/paper1_study_protocol.md` — formal hypothesis definitions and metric specs

For frozen Phase A results, see:
- `docs/paper1_freeze_memo_phaseA.md` — frozen verdicts for H1–H4

---

## Current Status (as of 2026-05-11)

| Item | Status |
|------|--------|
| paper1_phaseA_v1 | 300/300 runs complete, all success=true |
| H1 (Stage Overshoot) | PARTIAL — 1/6 systems (System 54 only) |
| H2 (Recovery Quality) | SUPPORTED — 7/8 systems |
| H3 (Wasted Levels) | PARTIAL — 2/6 systems (11, 54) |
| H4 (Usage Policy) | SUPPORTED vacuously — all exact_match=0 on high-stage systems |
| Freeze Memo | Written, evidence frozen |
| ODEBench ICs | Verified: all 8 exact systems use official ODEBench initial conditions |
| R² metric | Missing — must be added to analysis pipeline |
| EvoGrow v3 | Not started |
| Cluster runner | Not implemented |

**Active phase: Phase 0 (Baseline freeze) + Phase 1 (ODEBench evaluation)**

---

## Phase Overview

| Phase | Goal | Precondition | Output |
|-------|------|-------------|--------|
| **Phase 0** | Freeze and document Phase A baseline | paper1_phaseA_v1 complete | Freeze memo, corrected diagnostics |
| **Phase 1** | ODEBench-compatible evaluation of existing results | Phase 0 complete | R² table, ODEBench comparison |
| **Phase 2** | Parameter fitting stability improvements | Phase 1 complete | Better pretune, multi-start option |
| **Phase 3** | EvoGrow v3: equation-wise staged progression | Phase 2 complete | New algorithm variant, validated |
| **Phase 4** | Full paper1_phaseB experiment on ODEBench subset | Phase 3 complete | Main paper experiment |
| **Phase 5** | Paper writing and submission | Phase 4 complete | Paper draft |

---

## Phase 0 — Baseline Freeze

### Goal
Ensure the Phase A baseline is complete, correct, and fully documented before any new
experiments or algorithm changes are introduced.

### Go Criteria
- `docs/paper1_freeze_memo_phaseA.md` exists and contains all three blocks
- H4 "Allowed paper claim" corrected to reflect vacuous result
- `h1_h4_diagnostics.json` is valid and consistent with the freeze memo
- `evaluate_hypotheses.py` generalization path updated to point at actual data location

### No-Go Conditions
- Any modification to `paper1_phaseA_v1` run data
- Any new runs added to Phase A
- Any metric redefinition that changes Phase A verdicts retroactively

### Work Packages

#### WP-0.1 — Fix H4 claim in freeze memo
**Language:** Python
**What:** Change the H4 "Allowed paper claim" in `evaluate_hypotheses.py` from a positive
claim to: "C3 cannot be evaluated — all usage-policy variants achieve exact_match_rate = 0
on all high-stage systems. The expected ordering holds vacuously through ties only."
Regenerate `docs/paper1_freeze_memo_phaseA.md` and `h1_h4_diagnostics.json`.
**Hypothesis / Requirement:** Scientific integrity. Freeze memo must not overstate results.
**Scope:** 1 small edit in `evaluate_hypotheses.py`, regenerate outputs.

#### WP-0.2 — Fix generalization data path
**Language:** Python
**What:** Update `evaluate_hypotheses.py` (and/or `analysis/configs/paper1_phaseA_v1.json`)
to point at the actual generalization data location: `debug_results/generalization_summary.csv`.
Re-run the script and verify the OMIT verdict is reproduced correctly.
**Hypothesis / Requirement:** Reproducibility. The script must be runnable end-to-end.
**Scope:** Config path edit + verification run.

---

## Phase 1 — ODEBench-Compatible Evaluation

### Goal
Compute R²-based accuracy scores from existing Phase A runs and produce a comparison
table against published ODEBench baseline numbers (SINDy, PySR, GP variants).

No new EvoODE experiments in this phase. Only analysis.

### Go Criteria
- R² score computable from existing `result.json` trajectory predictions
- Comparison table produced: EvoGrow-v2.2 vs. SINDy (poly) vs. PySR on 8 overlap systems
- Table uses % Accuracy (R² > 0.9) as primary metric, consistent with ODEBench paper
- Published numbers for baselines cited from d'Ascoli et al. 2023 (ODEBench paper)

### No-Go Conditions
- Running SINDy, PySR, or ODEFormer ourselves (not in scope for Phase 1)
- Reporting EvoODE on systems where ICs differ from ODEBench
- Mixing surrogate systems (23, 37) into the R²-accuracy table

### Work Packages

#### WP-1.1 — R² metric from existing run results
**Language:** Python
**What:** Write `analysis/scripts/aggregate/compute_r2_scores.py`. For each run in
`paper1_phaseA_v1`, load the predicted trajectory from `result.json` and the ground-truth
from the trajectory generator. Compute R² per run. Aggregate: mean R², % Accuracy (R² > 0.9).
Write `analysis/data/paper1_phaseA_v1/r2_scores.csv`.
**Hypothesis / Requirement:** ODEBench-compatible evaluation (H2 restatement).
**Scope:** 1 script. No Julia changes. Ground-truth trajectories re-generated from system
definitions in `strogatz_extended.json` using same ICs and tspan as in run config.

#### WP-1.2 — ODEBench comparison table
**Language:** Python
**What:** Write `analysis/scripts/plot/table_odebench_comparison.py`. Produce a LaTeX table:
rows = 8 exact systems, columns = EvoGrow-v2.2 (R²%), SINDy-poly (from paper), PySR (from paper).
Cite ODEBench paper numbers explicitly. Note that EvoODE uses σ=0, ρ=0 (clean data),
matching the leftmost panel of Figure 4 in d'Ascoli et al.
**Hypothesis / Requirement:** H2 Competitive Recovery Quality, ODEBench-compatible.
**Scope:** 1 script, 1 LaTeX table, 1 CSV. No new experiments.

#### WP-1.3 — Update analysis config with ODEBench reference
**Language:** Python / config
**What:** Add `odebench_reference_paper` field to `analysis/configs/paper1_phaseA_v1.json`
with citation key and the specific figure/table from which baseline numbers are taken.
This ensures the comparison is traceable.
**Hypothesis / Requirement:** Reproducibility, citation traceability.
**Scope:** Config edit only.

---

## Phase 2 — Parameter Fitting Stability

### Goal
Improve robustness of parameter estimation without changing algorithm structure.
Two improvements are in scope: (1) better derivative estimation in `pretune.jl`,
(2) optional multi-start BFGS for difficult systems.

Global staged EvoGrow (v2.2) remains the unchanged baseline throughout.

### Go Criteria
- On System 11 (cubic): loss variance over seeds reduced vs. Phase A baseline
- On System 54 (Lorenz): mean loss not degraded vs. Phase A baseline
- All Phase A metric definitions remain valid for Phase B comparison
- New pretune produces valid p0 (no NaN, norm ≤ 1e6) on all 10 systems

### No-Go Conditions
- Changes to `StageProgressionPolicy`, `StageUsagePolicy`, or main EvoGrow loop
- Changes to metric definitions or aggregation logic
- Multi-start active by default in Phase B experiment (must remain opt-in)

### Work Packages (to be detailed when Phase 1 is complete)

#### WP-2.1 — Smoothed derivative estimation in pretune
**Language:** Julia
**What:** Add optional Savitzky-Golay smoothing before finite-difference derivative
estimation in `pretune_parameters`. Controlled by a new `smooth_derivatives::Bool` flag
in `EvoGrow` (default: false for backward compat). Validate on System 11 and 54.
**Hypothesis / Requirement:** Fitting stability. Directly supports recovery quality claims.

#### WP-2.2 — Multi-start BFGS wrapper
**Language:** Julia
**What:** Add `n_restarts::Int = 1` field to `BFGSOptimizer`. When > 1, run BFGS from
`n_restarts` different initializations (pretune + random perturbations) and return the best.
Default stays 1 to preserve Phase A behavior exactly.
**Hypothesis / Requirement:** Reduces false negatives on difficult systems (System 11, 54).

#### WP-2.3 — Phase A regression test
**Language:** Julia / shell
**What:** Simple script that re-runs 1 seed per system with Phase A hyperparameters and
asserts that loss is within 10× of Phase A mean. Confirms no regression from Phase 2 changes.
**Hypothesis / Requirement:** Reproducibility baseline integrity.

---

## Phase 3 — EvoGrow v3: Equation-wise Staged Progression

### Scientific Motivation
In Phase A, stage progression is decided globally: if any equation still needs higher-stage
terms, the entire system promotes. This is inefficient for coupled systems where some
equations are already well-explained by low-stage terms.

**EvoGrow v3 hypothesis:** Allowing each equation to progress independently reduces
wasted complexity exploration and produces sparser, more interpretable discovered structures.

This is a new algorithmic contribution, not a replacement of v2.2.
v2.2 (global staged) remains the baseline for all comparisons.

### Design Specification

#### Core change
Replace the single `current_stage::Int` with `eq_stages::Vector{Int}` — one stage per equation.

Each equation has its own:
- `stage_level_count` (levels spent in current stage for this equation)
- `stage_history` (objective history for this equation)
- promotion decision (independent of other equations)

#### Allowed terms per individual
For an `Individual`, the allowed terms for equation `k` are determined by `eq_stages[k]`,
not by a single global stage. Child generation must be equation-aware.

#### Promotion logic per equation
An equation promotes if:
1. It has spent ≥ `min_levels_per_stage` levels in its current stage
2. Its per-equation plateau is detected (plateau in the best objective contribution of eq k)
3. Its per-equation loss contribution is above tolerance
4. It has not yet reached `max_stage`

**Open design question (to be resolved in WP-3.1):**
How to define "per-equation loss contribution" — either per-equation residual MSE, or
a proxy from the per-equation parameter magnitudes. This must be defined before implementation.

#### Metrics added for v3
- `eq_final_stages::Vector{Int}` — final stage per equation
- `eq_stage_overshoot::Vector{Int}` — per-equation overshoot
- `eq_wasted_levels::Vector{Int}` — per-equation wasted levels
- `eq_promotion_log` — per-equation promotion history

Global metrics (`final_stage`, `stage_overshoot`, `wasted_levels`) remain defined as
`maximum(eq_final_stages)` for backward compat with Phase A comparisons.

#### What does NOT change
- `StructureSpec` representation (index-based, per-equation term lists)
- `pretune_parameters` (equation-wise already)
- `BFGSOptimizer` (system-level, unchanged)
- `StagedPolynomialBasis` (shared stage definitions, unchanged)
- v2.2 code paths (separate struct `EvoGrowV3`, not a mode of `EvoGrow`)

### Go Criteria
- v3 implements equation-wise promotion correctly and reproducibly
- `eq_stage_overshoot` and `eq_wasted_levels` computable and consistent
- v3 validated on ≥ 3 systems from ODEBench overlap set
- v3 shows measurable difference from v2.2 in at least one metric on at least one system
- Global staged EvoGrow v2.2 untouched

### Work Packages (to be detailed when Phase 2 is complete)

#### WP-3.1 — Per-equation loss contribution definition
**Language:** analysis / design (no code)
**What:** Define formally how per-equation progression is decided without a clean
per-equation loss decomposition. Propose and document the chosen proxy metric.
Output: design note appended to this document before any implementation begins.

#### WP-3.2 — EvoGrowV3 struct and eq_stages state
**Language:** Julia
**What:** New struct `EvoGrowV3` in `src/structure/evogrow_v3.jl`. Mirrors `EvoGrow` but
replaces `current_stage::Int` with `eq_stages::Vector{Int}` in search state.
No promotion logic yet — just the data structure and initialization.

#### WP-3.3 — Equation-aware child generation
**Language:** Julia
**What:** New `_expand_eq_aware` function. For each child, the allowed terms for equation k
come from `eq_stages[k]`, not from a single global stage. Integrated into WP-3.2 struct.

#### WP-3.4 — Per-equation plateau detection and promotion
**Language:** Julia
**What:** Implement `_eq_stage_progression_decision` that runs per equation. Integrate into
the main search loop of `EvoGrowV3`. Unit-test on 1D systems where behavior is predictable.

#### WP-3.5 — Metric extraction for v3
**Language:** Julia
**What:** Extend `result.json` schema with `eq_final_stages`, `eq_stage_overshoot`,
`eq_wasted_levels`. Backward-compatible: fields absent for v1/v2.x runs.

#### WP-3.6 — Validation run: v3 vs. v2.2 on 3 systems
**Language:** Julia / shell
**What:** Run v3 and v2.2 on Systems 3 (1D logistic), 26 (2D Lotka-Volterra), 54 (3D Lorenz)
with 5 seeds each. Compare `eq_stage_overshoot`, `eq_wasted_levels`, `exact_match_rate`.
This is a validation run, not a paper experiment.

---

## Phase 4 — paper1_phaseB: Full ODEBench Experiment

### Goal
Run the full paper experiment: EvoGrow v2.2 (baseline) + EvoGrow v3 (new) + GP on
a curated subset of ODEBench systems. Cluster-compatible execution.

### System Selection Criteria
- Must be in ODEBench (strogatz_extended.json)
- Must be exactly representable in StagedPolynomialBasis (dim ≤ 3, polynomial/trig structure)
- Must have official ODEBench ICs
- At least 5 systems per dimensionality category (1D, 2D, 3D) where possible

Proposed target: 20–25 systems from the 63 ODEBench systems.
Final selection documented here before any runs start.

### Cluster Infrastructure Requirements
- Parallelization: multiple `run_experiment.jl` instances, each picking queued runs atomically
- Status: existing atomic write protocol already supports this — validate first
- Julia version pinned via `Manifest.toml`
- Estimated runtime: ~20 systems × 3 variants × 5 seeds = 300 runs, target ≤ 1 week on cluster

### Go Criteria
- Phase 3 complete (v3 validated)
- System selection finalized and documented
- Cluster runner tested on ≥ 10 runs without race conditions
- Phase A baseline reproduced on ≥ 3 systems as sanity check

### Work Packages (to be detailed when Phase 3 is complete)

- WP-4.1 — System selection for Phase B
- WP-4.2 — Cluster runner validation (parallel instances, atomic writes)
- WP-4.3 — Phase B experiment run
- WP-4.4 — Phase B aggregation and analysis

---

## Phase 5 — Paper Writing

### Planned paper structure (preliminary)
1. Introduction: ODE discovery, complexity control, staged growth
2. Related Work: SINDy, GP (PySR), ODEFormer — positioned honestly
3. Method: EvoGrow v2.2 (baseline), EvoGrow v3 (equation-wise)
4. Experiments: ODEBench evaluation, R²-accuracy, stage metrics
5. Analysis: when does equation-wise progression help, when not
6. Limitations and Future Work
7. Conclusion

### Allowed claims (based on Phase A freeze + Phase B results)
- H2 (Recovery Quality): supported, will be restated in ODEBench-compatible terms
- H1/H3 (Overshoot/Wasted Levels): PARTIAL for v2.2, stronger case expected for v3
- H4 (Usage Policy): only claimable if Phase B shows non-zero exact_match on high-stage systems

---

## Implementation Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| `pretune` produces unstable OLS on short/noisy trajectories | Medium | Savitzky-Golay smoothing (WP-2.1), existing NaN/norm fallback already in place |
| Multi-start BFGS increases runtime substantially | Medium | Off by default; only activated explicitly in Phase B config |
| EvoGrowV3 eq-wise state makes `DiscoveryOptions` and metrics incompatible with Phase A | High | V3 in separate file, new metric fields, backward-compat via absent fields |
| Parallel cluster runner: race condition on run acquisition | Low | Existing tmp→rename protocol already atomic; validate before Phase B |
| Phase B on cluster: Julia version / package drift | Medium | `Manifest.toml` frozen, Julia version logged in `config.json` |
| R² computation requires re-simulating ground truth trajectories | Low | ICs verified to match ODEBench exactly; ground truth reproducible from config |
| ODEBench baseline numbers (SINDy, PySR) from paper use σ=0,ρ=0 — ensure EvoODE matches | Low | EvoODE Phase A already uses clean trajectories; document explicitly in WP-1.2 |

---

## Scientific Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| EvoGrow v3 (equation-wise) not faster or better than v2.2 on most systems | Medium | Frame as "precision allocation" not efficiency; honest comparison is the contribution |
| Home-built GP baseline not comparable to PySR — reviewer will flag this | High | Explicitly label as "reference implementation"; cite PySR numbers from ODEBench paper for H2 |
| Wasted-levels metric not meaningful for v3 (different definition at equation level) | Medium | Define global wasted_levels as max(eq_wasted_levels), document both |
| R² > 0.9 threshold disadvantages MSE-optimized methods | Low | Report both: % R²>0.9 and mean R²; note that EvoODE optimizes MSE directly |
| Phase B systems not representative enough for general claims | Medium | Select systems across all dimensionalities; include known hard systems (Lorenz, SEIR) |
| EvoGrow v3 promotion decisions depend on per-equation loss proxy not yet defined | High | WP-3.1 must resolve this before any implementation; if no clean definition exists, v3 scope narrows |

---

## Frozen Elements (must not change)

The following are frozen after paper1_phaseA_v1 and must not be modified:

- System selection for Phase A (IDs: 2, 3, 11, 23, 24, 26, 31, 37, 54, 63)
- Initial conditions (all match ODEBench official ICs)
- Hyperparameters (pop_size=10, n_levels=20, seeds=[42,123,7,99,17])
- Metric definitions for H1–H4 as specified in `docs/paper1_study_protocol.md`
- H1–H4 verdicts as recorded in `docs/paper1_freeze_memo_phaseA.md`
- `paper1_phaseA_v1` run data in `experiments/paper1_phaseA_v1/`

EvoGrow v2.2 (`evogrow_v2_2_stage_local`) is the permanent baseline variant.
Any new variant (v3, future) is compared against v2.2, never replacing it.

---

## Document Maintenance

This document is updated at each phase transition:
- Mark completed WPs as done
- Add design notes for upcoming WPs
- Record go/no-go decisions with date
- Add Phase B system selection when finalized (Phase 4)
- Add v3 per-equation loss contribution definition when resolved (WP-3.1)

Last updated: 2026-05-11
Current phase: Phase 0 + Phase 1
