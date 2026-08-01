# PAPER_1.md — EvoODE Paper 1: Execution Roadmap and Working Plan

This document is the authoritative execution plan for EvoODE Paper 1.
It defines the current paper scope, diagnostic gates, work phases, go/no-go criteria, risks, and design decisions.

For architecture and algorithm design, see `CLAUDE.md`.
For frozen Phase A results, see `docs/paper1_freeze_memo_phaseA.md`.

---

## Critical Scope Decision (2026-05-17)

Paper 1 is no longer framed as a pretuning study.

The core contribution of Paper 1 is the scientific evaluation of **EvoGrow as a staged, incremental search mechanism for interpretable ODE discovery**.

The guiding research question is:

> Is incremental, staged growth of the ODE hypothesis space an effective search mechanism for interpretable ODE discovery, and where does it help or fail?

The primary paper target is not a broad in-house benchmark against multiple external methods. The project currently has one implemented method family: **EvoGrow / EvoODE**. Therefore, Paper 1 will focus on diagnosing, stabilizing, and evaluating the final EvoGrow variant. External results from ODEBench-related papers may be used as published reference context, but no new SINDy, PySR, GP, or ODEFormer runs are planned inside this project.

---

## Explicit Non-Goals for Paper 1

Paper 1 does **not** run new in-house baselines for:

- GP
- PySR
- SINDy
- ODEFormer
- GODE
- Operon or other external symbolic-regression tools

Paper 1 does **not** use pretuning as the main experimental variable.

Paper 1 does **not** claim to be the first symbolic-regression-based ODE discovery method.

Paper 1 does **not** make paper claims from Phase A exploratory results.

---

## Pretuning Decision

Pretuning is removed from the main Paper 1 scope.

Pretuning may become a separate follow-up study, conference paper, or ablation paper if results show a strong effect.

For Paper 1:

- pretuning is not the main contribution,
- pretuning is not the main comparison axis,
- final Paper 1 runs should use one fixed fitting configuration,
- if pretuning is used internally in the final method, it must be treated as a fixed implementation detail, not as the central experimental variable,
- if pretuning is not required for the final method, it should be disabled for Paper 1 and reserved for future work.

This decision prevents Paper 1 from becoming a warm-start/optimizer paper and keeps the focus on staged structural growth.

---

## Current Status (as of 2026-05-17)

| Item | Status |
|------|--------|
| `paper1_phaseA_v1` | Archived exploratory run set: 10 ODEBench systems × 6 EvoGrow variants × 5 seeds = 300 runs, all successful |
| Phase A result interpretation | Frozen as exploratory evidence only |
| Main Phase A observation | Fit quality is promising, but staged-growth economy metrics are weaker than expected |
| Support matching | Known issue: growth-without-pruning makes raw `exact_support_match` too strict |
| Pretuning | Removed from Paper 1 main scope; possible future follow-up |
| Final EvoGrow variant | Not yet frozen |
| EvoGrow v2.2 | Failed Gate 1 on 2026-05-30; still the fallback candidate |
| EvoGrow v3 | Implemented and **failed Gate 2 on 2026-07-31**; not the final variant |
| ODEBench full evaluation | Planned only after final EvoGrow variant is selected |

**Active phase:** Phase 2 closed with a negative Gate 2. Scope decision open — see
"Open scope decision after Gate 2".

---

## Paper Strategy in One Sentence

> First evaluate whether EvoGrow v2.2 is already paper-ready once structural metrics are corrected; if not, develop EvoGrow v3 only if the diagnosed failure mode is genuinely caused by system-wide staged progression; then run the final selected EvoGrow variant on the full ODEBench suite and analyze fit, structure, search economy, robustness, and failure modes.

---

## Main Claim Strategy

The primary claim target is **Claim C**:

> EvoGrow is competitive in fit quality while exposing when and why incremental staged complexity control helps or fails.

Two stronger claims are tracked but not assumed:

### Claim A — Performance Claim

> EvoGrow outperforms or matches published reference methods on selected ODEBench regimes.

This claim may only be used if supported by final results and protocol alignment.

### Claim B — Complexity-Control Claim

> EvoGrow provides a more interpretable and controlled search trajectory, reducing unnecessary complexity in regimes where staged structure is appropriate.

This claim may only be used if supported by stage, overshoot, wasted-level, and structure metrics.

### Claim C — Primary Mechanistic Claim

> EvoGrow provides a controlled staged search process whose success and failure modes can be analyzed across ODEBench in terms of fit, structural recovery, complexity allocation, solver stability, and basis mismatch.

This is the safest and most defensible core framing.

---

## Phase Overview

| Phase | Goal | Output |
|-------|------|--------|
| **Phase 0** | Archive and correct Phase A diagnostics | Corrected freeze memo and diagnostic files |
| **Phase 1** | Repair structural metrics and re-diagnose v2.2 | Fair v2.2 diagnostic report and Gate 1 decision |
| **Gate 1** | Decide whether v2.2 is paper-ready | v2.2 selected, or v3 triggered |
| **Phase 2** | Conditional EvoGrow v3 design and validation | v3 validation report and Gate 2 decision |
| **Gate 2** | Decide whether v3 is paper-ready | final EvoGrow variant selected, or fallback decision |
| **Phase 3** | ODEBench protocol and literature reference alignment | system classification, metrics, protocol-audit document |
| **Phase 4** | Small validation run | schema/runtime/metric validation, no paper claims |
| **Phase 5** | Full ODEBench cluster run | final experiment results |
| **Phase 6** | Analysis and paper writing | paper draft |

---

## Phase 0 — Archive and Correct Phase A

### Goal

Correct known diagnostic issues in Phase A without changing the original run data.

Phase A remains exploratory. It is used to guide algorithmic diagnosis, not to support final Paper 1 claims.

### Required Corrections

1. Correct the H4 claim in the freeze memo.
2. Fix the generalization data path.
3. Preserve all original Phase A run data unchanged.

### Go Criteria

- `docs/paper1_freeze_memo_phaseA.md` contains the corrected H4 claim.
- `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` is consistent with the corrected memo.
- `evaluate_hypotheses.py` points to the correct generalization data path.
- No new runs are added to `paper1_phaseA_v1`.

### Work Packages

#### WP-0.1 — Correct H4 claim in freeze memo ✓ 2026-05-17

**Language:** Python

**What:** Change the H4 “Allowed paper claim” in `evaluate_hypotheses.py` to reflect that H4 is vacuous: all usage-policy variants achieved `exact_match_rate = 0` on high-stage systems, so the expected ordering holds only through ties.

**Output:** Regenerated `docs/paper1_freeze_memo_phaseA.md` and `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`.

**Done:** H4 verdict corrected to `VACUOUS`, `”vacuous”: true` in diagnostics JSON, claim text updated. H1/H2/H3 unchanged.

#### WP-0.2 — Fix generalization data path ✓ 2026-05-17

**Language:** Python / config

**What:** Update `analysis/configs/paper1_phaseA_v1.json` to point at the actual generalization summary location. Verify that the OMIT verdict is reproduced.

**Done:** Config path corrected to `debug_results/generalization_summary.csv`. Files verified present.

---

## Phase 1 — Metric Repair and v2.2 Diagnostic Re-Analysis

### Goal

Before developing a new algorithm variant, evaluate whether EvoGrow v2.2 is already stronger than Phase A suggested once metrics are corrected.

The main concern is that `exact_support_match` was too strict because EvoGrow grows structures but does not prune near-zero terms. A discovered model such as

```text
 dx/dt = 0.000002 u + 1.000043 u²
```

should be recognized as structurally correct for a true equation

```text
 dx/dt = u²
```

if the extra term has effectively zero coefficient.

### Key Issue: Growth Without Pruning

EvoGrow may retain terms with coefficients close to zero. These terms remain in the raw discovered structure and can make `exact_support_match = false` even when the effective model is correct.

Therefore, structural recovery must distinguish between:

- **raw discovered structure**, and
- **effective pruned structure used for support evaluation**.

### Support-Pruning Rule

For support-matching evaluation only, a term is pruned from equation `k` if:

```text
 |coeff| < max(1e-6, 1e-3 × max_abs_coeff_in_equation_k)
```

This pruning:

- is applied only for evaluation,
- does not change the search process,
- does not change parameter optimization,
- does not modify population state,
- must be documented and frozen before Phase 4.

### Required Metrics

For exact systems, store both:

- `exact_support_match_raw`
- `exact_support_match_pruned`

The paper may use the pruned metric as the main structural recovery metric, but the raw metric must remain available for transparency.

### v2.2 Diagnostic Targets

Re-analyze v2.2 on:

- Phase A systems,
- known problem systems such as 26, 31, and 63,
- at least one simple control system,
- at least one system where EvoGrow already performed well.

Questions to answer:

1. Was the apparent structural failure actually a metric problem?
2. Does pruned support matching recover correct structures that raw matching missed?
3. Are stage overshoot and wasted levels still weak after metric repair?
4. Do systems 26, 31, and 63 indicate a real algorithmic failure?
5. Is the failure caused by system-wide staged progression, parameter fitting, basis mismatch, or something else?

### Phase 1 Work Packages

#### WP-1.1 — Add exact_support_match_raw and exact_support_match_pruned metrics ✓ 2026-05-11

**Language:** Julia

**What:** Implement coefficient-threshold pruning rule in `experiments/run_experiment.jl` and store both raw and pruned support-match metrics per run.

#### WP-1.2 — Phase A metric artifact vs. structural failure diagnostic ✓ 2026-05-11

**Language:** Python / analysis

**What:** Classify each Phase A failure as metric artifact or genuine structural failure. Identified System 11 as metric artifact (loss ~4e-15 but raw match = 0), confirmed genuine failures on Systems 26, 31, 63.

#### WP-1.3 — Phase 1 diagnostic run on problem systems ✓ 2026-05-30

**Language:** Julia

**What:** Run EvoGrow v2.2 stage_local with Paper 1 configuration (pretuning=false, n_levels=30) on Systems 3, 11, 26, 31, 63 with 3 seeds each.

**Result:** 15/15 runs completed. System 11 pruning fix confirmed. Systems 26 and 63 show genuine algorithmic failure (system-wide staging escalates to Stage 5 without finding correct cross-terms). System 31 seed 42 achieves near-perfect fit but spurious term survives pruning threshold.

---

### Phase 1 Hyperparameter Defaults for Diagnosis

The diagnostic configuration should include:

```text
n_levels = 30
```

Rationale: with 5 stages and a minimum budget per stage, `n_levels = 20` leaves little or no search slack in Stage 5. `n_levels = 30` gives high-stage systems meaningful search budget.

`loss_tol` remains as a safety-level early stopping condition, but it is not treated as the main control mechanism. The primary stopping mechanisms are plateau detection and max levels.

### Gate 1 — Is v2.2 Paper-Ready?

After Phase 1, decide whether v2.2 is good enough to become the final Paper 1 variant.

v2.2 is paper-ready if:

- fit quality is strong on important exact systems,
- pruned support recovery is meaningful,
- stage overshoot is explainable and not dominant,
- wasted-level behavior is not fatal to the main story,
- runtime is acceptable,
- solver failures are limited and analyzable,
- known problem systems are either solved or clearly understood.

If v2.2 passes Gate 1:

> Select v2.2 as final Paper 1 variant and skip EvoGrow v3 for Paper 1.

If v2.2 fails Gate 1:

> Proceed to Phase 2 and develop EvoGrow v3 only if the diagnosis indicates that system-wide staged progression is the relevant failure mode.

### Gate 1 Decision — 2026-05-30

**Decision: v2.2 fails Gate 1. Phase 2 (EvoGrow v3) is triggered.**

Evidence from `studies/phase1_diag/` (15 runs, EvoGrow v2.2 stage_local, pretuning=false, n_levels=30, seeds 42/123/7):

| System | pruned_match | Final stage | Loss | Verdict |
|--------|-------------|-------------|------|---------|
| 3 (Logistic) | all true ✓ | 2–5 / 2 | ~7e-10 | Fit good, minor overshoot |
| 11 (Cubic) | all true ✓ | 4/4 | ~4e-15 | Metric artifact healed |
| 26 (Lotka-Volterra) | all false ✗ | 5/3 | ~5e-4–1.4e-3 | Genuine structural failure |
| 31 (SIR) | all false ✗ | 3–5 / 3 | ~7e-11 – 1e-4 | Seed 42 near-perfect fit but spurious term; seeds 123/7 fail |
| 63 (SEIR) | all false ✗ | 5/3 | ~9e-4–1.8e-3 | Consistent failure, 11000–31000s |

**Diagnosed failure mode:** On Systems 26 and 63, loss stagnates in Stage 3 above target. The system-wide plateau trigger then promotes all equations to Stage 4 (cubic) and Stage 5 (trig), none of which are structurally needed. The correct cross-terms (Stage 3) are never found because the global promotion removes search pressure rather than concentrating it on the failing equations.

This failure mode is consistent with the v3 hypothesis: per-equation staged progression would allow each equation to promote only when its own residual stagnates, preventing unnecessary escalation in equations that are already explained.

**Triggering condition met:** the diagnosed failure mode is system-wide staged progression. Phase 2 is triggered.

---

## Phase 2 — Conditional EvoGrow v3 Design and Validation

### Status

EvoGrow v3 is conditional. It is not automatically part of Paper 1.

v3 is developed only if Phase 1 shows that v2.2 is not paper-ready and that the likely issue is system-wide staged progression.

### Scientific Motivation

In v2.2, stage progression is system-wide. If one equation needs higher-stage terms, all equations promote together. In coupled multi-dimensional systems, this can waste search budget and introduce unnecessary terms into equations that were already well explained at lower stages.

v3 hypothesis:

> Equation-wise staged progression improves complexity allocation by allowing each equation to grow only when its own progress signal indicates that more complexity is needed.

### Core Design

Replace the single global stage state:

```text
current_stage::Int
```

with equation-wise stage state:

```text
eq_stages::Vector{Int}
```

Each equation independently tracks:

- current stage,
- levels spent in current stage,
- plateau history,
- promotion decision.

### Per-Equation Progress Signal

The preferred signal is an equation-local derivative residual:

```text
mean_t ( dx_k/dt - f_k(x(t)) )²
```

computed on the observed trajectory. Derivative estimation should be consistent with the derivative estimation already used in the project, unless explicitly justified.

A hybrid criterion may also be considered:

```text
derivative residual plateau AND trajectory residual above tolerance
```

Parameter-magnitude or coefficient-variance proxies may only be used as fallback if residual-based options fail and this decision is explicitly justified.

### v3 Work Packages

| WP | What | Status |
|----|------|--------|
| WP-v3.1 | Design note: per-equation progress signal and promotion rule | done 2026-07-20 |
| WP-v3.2 | `EvoGrowV3` struct and equation-wise stage state | done 2026-07-20 |
| WP-v3.3 | Equation-aware child generation | done 2026-07-29 |
| WP-v3.4 | Per-equation plateau detection and promotion | done 2026-07-29 |
| WP-v3.5 | New v3 metrics in `result.json` | done 2026-07-30 |
| WP-v3.6 | Validation run comparing v3 against v2.2 on 3–5 diagnostic systems | replaced by WP-G2.1 do-or-die cell, run 2026-07-31 |

The planned 45-run validation matrix was replaced by a single pre-registered decision
cell (System 26, seed 42) because the v2.2 arm was already frozen and bit-exactly
reproduced by WP-T2, so only one fresh v3 run was needed to decide. See the Gate 2
decision below.

### Gate 2 — Is v3 Paper-Ready?

v3 is paper-ready if it shows:

- at least comparable fit quality to v2.2,
- better or more interpretable equation-wise complexity allocation,
- reduced wasted complexity on relevant multi-dimensional systems,
- no major new solver or runtime instability,
- meaningful per-equation stage histories.

If v3 passes Gate 2:

> Select v3 as final Paper 1 variant.

If v3 fails Gate 2:

> Do not force v3 into Paper 1. Either use v2.2 with an honest limitation/failure analysis or revise the paper plan.

### Gate 2 Decision — 2026-07-31

**Decision: v3 fails Gate 2. v3 is not the final Paper 1 variant.**

Evidence from the pre-registered decision cell (System 26, seed 42, 30 levels,
`evogrow_v3`, config fingerprint `1f9c5f807d609548`, git hash `e82715b`, 3.6 h):

| Criterion | Target | Observed | Verdict |
|-----------|--------|----------|---------|
| (a) `eq_final_stages[1]` | 3 | 5 | failed |
| (b) `du1` support | exactly `{u1, u1^2, u1*u2}` | extra `u2` term | failed |
| (c) loss | ≤ 0.001391623174905009 | 2.5195575964774715e-4 | met |

`eq_final_stages = [5,5]`, `eq_overshoot = [2,2]`. No detectable decoupling.

Criterion (c) is worth recording: the loss is 5.5× better than the frozen v2.2 anchor.
Fit quality was never the problem. What failed is complexity allocation — precisely what
v3 was built for.

**Diagnosis.** The v3 promotion rule asks three questions per equation: sufficient stage
budget, `r_k` plateau, and `r_k > loss_tol = 1e-8`. The third condition is unreachable on
coupled systems, where the error floor is around 1e-3 to 1e-4. For an already correctly
modelled equation all three conditions therefore hold permanently, and the rule cannot
distinguish under-modelling from an irreducible error floor: both look like a flat
residual above 1e-8. Independent per-equation controllers consequently escalate exactly
as the global one did.

> **v3 changed who decides, but not what evidence justifies a promotion.**

This is a clean negative result and is reportable as such.

**Second, independent cause — found after the gate (WP-L2, 2026-07-31).** The `r_k`
signal itself is contaminated. On System 26 the derivative residual of the *true*
structure with *true* parameters is [1.808, 0.520], while the fitted full-stage-3 `r_k`
is [0.142, 0.0394] — the floor lies a factor of 13 *above* the fitted value. `r_k`
therefore does not measure structural adequacy; it measures how much finite-difference
derivative error a model can absorb, and that capacity grows with the number of terms.
The signal is systematically biased toward "more terms help". A smoothing-based
derivative estimator reduces the floor by a factor of ~4.5 but does not remove it.

### Open scope decision after Gate 2

Both branches allowed above remain open and the choice is **not yet made**:

1. v2.2 as the final variant, with an honest failure analysis of v3 as a contribution.
2. Revise the paper plan around the stage-firing look-ahead (effectively a v4).

Evidence bearing on branch 2 was collected in `studies/lookahead/` (WP-L1 to WP-L3,
diagnostic only, no algorithm change). Summary as of 2026-07-31:

- A cheap derivative-space look-ahead separates the two decisive counterexamples once the
  derivative estimate is adequate — a smoothing estimator matters, higher-order finite
  differences do not.
- With a noise-floor-gated firing rule the probe reaches 10 exact / 0 overshoot /
  2 undershoot / 4 not-identifiable over the 16 exact benchmark equations.
- Both remaining failure classes are characterised rather than assumed: the undershoots
  are a sampling-density limit that disappears at 2x density, and the non-identifiable
  equations stem from a conservation law that no sampling density removes.

Two things this evidence does **not** establish, and both bear directly on the choice:

1. The probe has only ever run offline, on systems with known ground truth, with the full
   term library as the checkpoint. It has never been tested as a discovery mechanism.
2. It addresses complexity allocation (Claim B), not structural recovery. On System 26,
   `du2` was already wrong at stage 3 with every needed term available; a perfect firing
   gate stops the escalation and still leaves `du2` wrong.

**Recommended decisive step before choosing:** integrate the gate as a per-equation stage
cap and re-run the frozen do-or-die cell (System 26, seed 42) against the v2.2 anchor and
the v3 result. No speculative unlock, checkpoint, or rollback machinery is needed — the
gate depends only on trajectory, basis, equation and stage, so `max_useful_stage_k` can be
precomputed once per run. That is a small, cheap change and the first genuine test of the
mechanism.

### Result of the decisive step — 2026-08-01

| | v2.2 anchor | v3 Gate 2 | capped |
|---|---|---|---|
| loss | 1.391623174905009e-3 | 2.5195575964774715e-4 | **2.5195575964774715e-4** |
| `eq_final_stages` | 5 | [5, 5] | **[3, 3]** |
| `eq_overshoot` | 2 | [2, 2] | **[0, 0]** |
| `eq_wasted_levels` | 8 | — | **[0, 0]** |
| `du1` support | {u1, u1², u1·u2} | — | {u1, **u2**, u1², u1·u2} |
| `du2` support | {u1, u1²} | — | **{u1, u1²}** |

Two findings, pointing in opposite directions.

**Complexity allocation is solved, at no cost.** Overshoot 2 → 0, wasted levels 8 → 0, and
the loss is bit-identical to the uncapped v3 run. Stages 4 and 5 contributed literally
nothing there; the escalation was pure waste and the cap removes it without any loss of fit
quality. Parameter fits drop from 530 to 390.

**Structural recovery is unchanged — not even moved.** `du2` is exactly what v2.2 found
three method generations ago, and the true `2·u2 − u1·u2 − u2²` was inside the cap on stage
3 the whole time. `du1` keeps a spurious `u2` term.

**Consequence for the scope decision.** Stage escalation was a symptom, not the cause.
Forcing the search onto the correct stage does not improve discovery by a single term, so
the look-ahead is a demonstrated mechanism for **Claim B** (complexity control) and
demonstrably not for structural recovery. Branch 2 — rebuilding the paper around the
look-ahead as the headline contribution — is therefore weaker than it appeared: the
mechanism works and its scope is measured, but it does not fix the failure that drove
Phase 2.

The evidence now supports branch 1, enriched: the final variant carries the cap, the paper
is the mechanistic Claim C study, and the v2.2 → v3 → capped sequence becomes a documented
failure analysis with a quantified positive result on complexity allocation. The remaining
open question — why the search fails to find an available stage-3 structure — concerns
search power *within* a stage (population size, child generation, parsimony pressure) and
is a different line of work, not a Phase 2 continuation.

---

## Phase 3 — ODEBench Protocol and Literature Reference Alignment

### Goal

Prepare the final full-suite evaluation and clarify how EvoGrow results can be compared to published ODEBench-related results.

No external baselines are run in this project.

Published results may be used from:

- ODEFormer / ODEBench,
- PySR and SINDy numbers reported in ODEBench-related work,
- GODE if protocol-relevant,
- FIM / Al-Khwarizmi / other ODEBench papers if relevant.

These are used as **published reference context**, not as in-house baselines.

### Required Protocol Audit

Create:

```text
docs/paper1_odebench_protocol_alignment.md
```

This document must record for each published reference source:

| Dimension | EvoGrow | Published source | Match status | Notes |
|----------|---------|------------------|--------------|-------|
| Systems used | all 63 ODEBench systems | [source-specific] | exact / partial / mismatch | |
| Initial conditions | from `strogatz_extended.json` | [source-specific] | exact / partial / mismatch | |
| tspan | from system JSON | [source-specific] | exact / partial / mismatch | |
| sampling grid | [TBD] | [source-specific] | exact / partial / mismatch | |
| noise setting | clean / σ=0 | [source-specific] | exact / partial / mismatch | |
| metric definition | R², loss, support metrics | [source-specific] | exact / partial / mismatch | |
| aggregation | across seeds/systems | [source-specific] | exact / partial / mismatch | |

The protocol audit determines whether published numbers may be described as:

- directly comparable,
- approximately comparable,
- contextual only.

If protocol equivalence is not established, do not frame external numbers as a direct benchmark defeat or victory.

### System Classification

Classify all 63 ODEBench systems into:

1. **Exact systems** — exactly representable in the current staged basis.
2. **Surrogate systems** — not exactly representable in the current staged basis.

For exact systems, record:

- expected stage,
- true support,
- dimensionality,
- term types.

For surrogate systems, record:

- basis gap reason,
- e.g. constant offset, fractional powers, non-supported nonlinearities, unsupported products, stiffness, or other mismatch.

Output:

```text
analysis/data/<experiment_id>/system_classification.csv
```

### Core Metrics

Per-run metrics:

| Metric | Definition |
|--------|------------|
| `loss` | Simulation MSE over all timesteps and dimensions |
| `r2` | R² coefficient, per dimension and averaged, following protocol audit |
| `r2_above_threshold` | Boolean, usually `r2 > 0.9` if aligned with ODEBench |
| `relative_l2` | Optional bridge metric to grammar-based ODE discovery papers |
| `exact_support_match_raw` | Raw support equality without pruning, exact systems only |
| `exact_support_match_pruned` | Support equality after coefficient-threshold pruning, exact systems only |
| `final_stage` | Final stage at termination |
| `stage_overshoot` | `final_stage - expected_stage`, exact systems only |
| `wasted_levels` | Levels spent above expected stage, exact systems only |
| `elapsed_s` | Wall time for full run |
| `solver_failures` | NaN-producing ODE solves during search |
| `status` | queued / running / finished / failed / timeout / interrupted |
| `failure_reason` | reason for non-finished run |
| `system_id` | ODEBench system ID |
| `seed` | RNG seed |
| `git_hash` | Git commit hash |

### Valid-Run Rule

A run is valid if:

- `status = finished`,
- `loss` is finite and non-NaN,
- predicted trajectory exists.

Poor results are still valid:

- very large loss,
- negative R²,
- incorrect structure,
- unstable-looking but numerically completed trajectory.

Invalid runs are only:

- NaN loss,
- missing prediction,
- timeout,
- crash / failed run.

Do not filter out poor valid runs.

### Timeout Policy

Timeout applies at run level only.

One run is:

```text
system × final EvoGrow variant × seed
```

If the run-level timeout is reached:

- `status = timeout`,
- `failure_reason = timeout`,
- `loss = NaN`,
- `r2 = NaN`,
- `elapsed_s = observed wall time or configured timeout limit`.

Timeout runs:

- count toward `n_seeds`,
- do not count toward `n_valid`,
- are included in robustness and failure-rate analyses,
- must not be silently deleted or silently rerun.

### Logging Policy

Store more rather than less.

Each run folder must contain:

| File | Contents |
|------|----------|
| `config.json` | algorithm parameters, system definition, seed, git hash, Julia version, hostname |
| `metrics.json` | all per-run metrics, written atomically |
| `result.json` | final structure, final parameters, predicted trajectory, loss, R² |
| `log.txt` | append-only run log, including restart marker if rerun |
| `status.json` | current status and status transitions |

Additional fields where available:

- `stage_history`,
- `eq_stage_history` for v3,
- `solver_failures`,
- `elapsed_s`,
- `git_hash`,
- `julia_version`,
- `hostname`.

---

## Phase 4 — Small Validation Run

### Goal

Validate the selected final EvoGrow variant before launching the full ODEBench run.

No paper claims are derived from this phase.

### Scope

Run 3–5 systems locally with 3 seeds.

The validation set must include:

- one simple exact 1D system,
- one exact 2D system,
- one exact 3D system, e.g. Lorenz,
- one exact 4D system, e.g. SEIR / System 63,
- one surrogate system.

### Go Criteria

- all runs either finish, fail cleanly, or timeout cleanly,
- schema validation passes,
- R² and support metrics can be computed,
- run-level timeout works,
- logs and outputs are complete,
- runtime estimates are sufficient for cluster planning,
- no aggregate metric pipeline produces unexplained NaNs.

---

## Phase 5 — Full ODEBench Cluster Run

### Goal

Run the final selected EvoGrow variant on all 63 ODEBench systems.

This is the only source of final Paper 1 results.

### Runs

Minimum final run plan:

```text
63 systems × 1 final EvoGrow variant × 3 seeds = 189 runs
```

Additional seeds may be added later if runtime permits, but the default final plan is 3 seeds.

### Important

There is no pretuning on/off condition in Paper 1.

If the final method uses pretuning internally, it is a fixed part of the selected method and must be documented. If pretuning is not needed, it remains disabled and is reserved for future work.

### Cluster Requirements

- multiple parallel runners,
- atomic run acquisition,
- pinned Julia environment via `Manifest.toml`,
- git hash and Julia version logged per run,
- failed/time-out runs preserved,
- no silent reruns,
- no system removal due to difficulty or runtime.

### Go Criteria

- Phase 4 validation complete,
- final EvoGrow variant selected,
- system classification committed,
- protocol audit committed,
- run manifest generated and verified,
- cluster runner tested with parallel workers,
- all runs end in `finished`, `failed`, or `timeout` status.

---

## Phase 6 — Analysis and Paper

### Primary Analyses

Across all 63 systems:

- R² accuracy,
- mean R²,
- simulation loss,
- runtime,
- timeout rate,
- solver failure rate,
- valid-run rate,
- comparison against published reference numbers where protocol-appropriate.

Exact systems only:

- `exact_support_match_raw`,
- `exact_support_match_pruned`,
- stage overshoot,
- wasted levels,
- final stage distribution,
- stage-wise search behavior.

Surrogate systems only:

- R² and loss,
- approximation behavior,
- final stage reached,
- basis mismatch effects,
- stability and failure modes.

If v3 is selected:

- equation-wise final stages,
- equation-wise overshoot,
- equation-wise wasted levels,
- equation-wise stage histories,
- evidence of meaningful complexity allocation.

### Published Reference Context

External ODEBench-related numbers may be cited from the literature, but the paper must clearly label them as published reference results.

They may only be presented as direct comparisons if the protocol audit supports comparability.

Otherwise, they are contextual references.

### Planned Paper Structure

1. Introduction: interpretable ODE discovery and the need for controlled structure search
2. Related Work: SINDy, PySR/GP, ODEFormer, GODE, and prior SR-based ODE discovery
3. Method: EvoGrow staged basis expansion and final selected variant
4. Experimental Protocol: ODEBench full-suite evaluation and exact/surrogate split
5. Results: fit quality, structural recovery, search economy, runtime, and failures
6. Analysis: where staged growth helps, where it fails, and why
7. Limitations and Future Work: pretuning, stronger baselines, noise, larger systems
8. Conclusion

### Allowed Claim Types

Claims are only made after final results are available.

Allowed claim templates:

- **Accuracy claim:** EvoGrow achieves X% R² accuracy on all or selected ODEBench subsets.
- **Structural recovery claim:** EvoGrow recovers effective support on X% of exact systems under the frozen pruning rule.
- **Complexity-control claim:** EvoGrow limits or reveals unnecessary complexity through stage metrics.
- **Mechanistic claim:** EvoGrow exposes where staged incremental growth helps or fails.
- **Robustness claim:** EvoGrow completes successfully on N of 63 systems.
- **Failure-mode claim:** Failures are dominated by solver instability, basis mismatch, timeout, stage escalation, or fitting issues.

No claim may be derived from Phase A exploratory results.

---

## Future Work / Separate Paper Ideas

The following topics are explicitly outside the main Paper 1 scope but may become follow-up work:

- pretuning / OLS warm-start ablation,
- noise robustness,
- irregular sampling,
- extrapolation to unseen initial conditions,
- in-house SINDy / PySR / GP benchmark implementation,
- candidate-level optimizer timeouts,
- adaptive basis redesign,
- alternative pruning and sparsification strategies,
- equation-wise v3 extensions if not used in Paper 1.

---

## Implementation Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Raw support matching underestimates recovery | High | Use frozen coefficient-threshold pruning for evaluation and store raw/pruned metrics |
| v2.2 looks weak due to metric artifact | High | Re-diagnose with pruned support before developing v3 |
| v3 is developed without clear need | Medium | Only implement v3 if Gate 1 diagnosis justifies it |
| v3 per-equation progress signal is unstable | High | Resolve in WP-v3.1 before implementation |
| ODE solve failures on stiff/high-dimensional systems | Medium | Record failures and include in robustness analysis |
| Run-level timeout too short | Medium | Estimate runtime in validation run and adjust before full cluster run |
| Julia/package drift on cluster | Medium | Pin `Manifest.toml`, log Julia version and git hash |
| Protocol mismatch with published baselines | Medium | Use protocol audit; label external numbers as contextual if necessary |

---

## Scientific Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| EvoGrow does not outperform published methods | Medium | Frame paper as mechanistic staged-growth study, not SOTA benchmark |
| v2.2 is not strong enough and v3 does not fix it | High | Report honest failure analysis or revise paper scope |
| Stage metrics remain weak | Medium | Analyze when and why staged growth fails; do not overclaim |
| Full ODEBench performance is low | Medium | Use exact/surrogate split and failure-mode analysis |
| External reviewers expect in-house baselines | Medium | Clearly state scope; compare to published numbers only where protocol supports it |

---

## Frozen Elements

### Phase A

- `paper1_phaseA_v1` run data remains unchanged.
- Phase A is exploratory and not used for final claims.

### After Phase 1 / Gate 1

- v2.2 diagnostic decision is recorded.
- If v2.2 is selected, final v2.2 specification is frozen.
- If v3 is triggered, v3 design rationale is frozen before implementation.

### After Gate 2

- final EvoGrow variant is frozen.
- all hyperparameters are frozen.
- seed list is frozen.

### After Phase 3

- system classification is frozen.
- metrics are frozen.
- protocol-audit status is frozen.

### After Phase 5 begins

- full ODEBench manifest is frozen.
- no systems may be removed.
- no settings may be changed without creating a new experiment ID.

---

## Document Maintenance

This document is updated at each phase transition:

- mark completed WPs with date,
- record Gate 1 decision,
- record Gate 2 decision if v3 is triggered,
- fill final variant specification,
- update protocol-audit status,
- add final claim decisions after Phase 5 results.

Last updated: 2026-07-31
Current phase: Phase 2 closed — v3 failed Gate 2; scope decision open (v2.2 with failure
analysis, or paper plan revised around the stage-firing look-ahead)
