# PAPER_1.md Draft Revision -- EvoODE Paper 1: Execution Roadmap and Working Plan

> **Draft created 2026-08-17.**
>
> This is a proposed replacement for `PAPER_1.md`, not the authoritative document. Until this
> draft is accepted and copied over, `CLAUDE.md` and `DIARY.md` carry the current state of Paper 1.
> The existing `PAPER_1.md` remains untouched.

This document defines the current Paper 1 scope, diagnostic gates, work phases, go/no-go criteria,
risks, and design decisions.

For architecture and algorithm design, see `CLAUDE.md`.
For chronology, measurements, bug history, and commit hashes, see `DIARY.md`.
For the Phase B sampling protocol and comparability audit, see
`docs/paper1_odebench_protocol_alignment.md`.
For the stage-cap evidence chain, see `docs/wp_c1_stage_cap_horizon_audit.md`,
`docs/wp_c2_stage_cap_failure_diagnosis.md`, and `docs/wp_c4_stage_cap_doubt_band.md`.

---

## Critical Scope Decision (2026-08-03)

Paper 1 is no longer framed as a pretuning study, and it is no longer planned around EvoGrow v3.

The core contribution of Paper 1 is the **look-ahead stage cap** as a data-driven, per-equation
search-space controller on the `evogrow_v2_2_stage_capped` substrate:

```text
v2.2 substrate + per-equation look-ahead stage cap derived from trajectory and basis
```

The cap is computed before search starts. It reads the trajectory and basis, not the evolving
population, so it is search-independent and can be combined with the v2.2 substrate. It is not a
v3 mechanism.

The guiding research question is:

> Can a data-derived, per-equation stage cap control the ODE hypothesis space before search, and
> where does that control help, fail, or become unauditable?

The paper's central story is the documented failure-analysis chain:

```text
v2.2 -> v3 -> capped
```

v3 is a result, not the contribution. It failed Gate 2 because the promotion condition
`r_k > loss_tol = 1e-8` is unreachable on coupled systems with an error floor around `1e-3`, and
because `r_k` is contaminated by derivative-estimation error. The cap is the resulting controller:
it limits how far each equation may grow when the data give positive evidence about the useful
stage boundary.

---

## Explicit Non-Goals for Paper 1

Paper 1 does **not** run new in-house baselines for:

- GP
- PySR
- SINDy
- ODEFormer
- GODE
- Operon or other external symbolic-regression tools

Paper 1 does **not** make direct victory or defeat claims against SINDy, PySR, or other published
methods until the external protocol columns in `docs/paper1_odebench_protocol_alignment.md` are
filled. The current comparability verdict is not established; published numbers are contextual
only.

Paper 1 does **not** use pretuning as the main scientific contribution. Phase B contains
`pretune_on` and `pretune_off` as the two experimental conditions, but the contribution is the
stage cap.

Paper 1 does **not** claim structural recovery on surrogate systems. The 43 surrogate systems have
no true support in the current basis, so they are evaluated through fit quality via R^2, reached
stage, and stability observations.

Paper 1 does **not** make paper claims from Phase A exploratory results.

Paper 1 does **not** report Phase B results until campaign records exist. Result tables and result
claims below contain explicit placeholders.

---

## Pretuning Decision

Pretuning is not the main Paper 1 contribution.

For Phase B, pretuning is retained as an experimental condition because the frozen full-suite scope
contains exactly two conditions:

```text
pretune_on
pretune_off
```

Both conditions are run for all 63 systems, 3 seeds, and both initial-condition sets. Any
pretuning effect is interpreted as a condition effect around the same capped search-space
controller, not as the headline mechanism.

---

## Current Status (as of 2026-08-17)

| Item | Status |
|------|--------|
| `paper1_phaseA_v1` | Frozen exploratory run set: 300/300 runs. Not used for final claims |
| Gate 1 | Decided 2026-05-30: v2.2 fails |
| Gate 2 | Decided 2026-07-31: v3 fails |
| Final variant | `evogrow_v2_2_stage_capped`, settled 2026-08-03 |
| Phase B protocol | Decided 2026-08-03: 63 systems, 2 pretuning conditions, 3 seeds, 2 IC sets |
| Phase B run count | 63 x 2 x 3 x 2 = 756 runs |
| Sampling | 512 points over `t in [0, 10]`, both endpoints included |
| Trajectory generation | Self-integrated with `Tsit5`, `abstol = reltol = 1e-9` |
| Phase B records | **Placeholder: no final Phase B campaign records yet** |
| Campaign identity | Git hash, config or Phase B fingerprint, and `stage_cap_behavior_fingerprint` |
| Current Phase B fingerprint | `e361a2af49366670`, no campaign records yet |
| Current regression fingerprint | `1d0ccf8d53c6576d`, no campaign records yet |
| Current stage-cap behavior fingerprint | `61b6548ef0014593`, no campaign records yet |
| Campaign status | Blocked on remaining stage-cap and cost/fingerprint decisions in `CLAUDE.md` |

---

## Paper Strategy in One Sentence

> Paper 1 evaluates a data-driven per-equation stage cap as a search-space controller for
> incremental ODE discovery, while reporting the v2.2 and v3 failures that led to it and keeping
> structural recovery, surrogate fit, and compute-cost evidence separate.

---

## Main Claim Strategy

The primary claim target is **Claim C**, reframed around the cap:

> EvoODE can derive a per-equation upper bound on useful staged grammar growth from the observed
> trajectory and basis before search, reducing avoidable stage escalation where the data give
> positive evidence and exposing where such control is unsafe or unauditable.

Two narrower claims are tracked but not assumed:

### Claim A -- Fit-Quality Claim

> EvoODE achieves the reported Phase B fit-quality outcomes on the 63-system ODEBench protocol.

This claim may only be filled after Phase B records exist.

**Placeholder for Phase B results:** no campaign records exist yet.

### Claim B -- Search-Space-Control Claim

> The stage cap restricts unnecessary staged growth on exact systems where its evidence is
> auditable, while preserving the distinction between capped, uncapped, and abstained equations.

This claim must be supported by stage metrics, cap decisions, support availability on exact
systems, and counters. Wall-clock time is not evidence for it.

### Claim C -- Primary Mechanistic Claim

> The v2.2 -> v3 -> capped sequence shows that staged growth needs not only a progression rule, but
> a data-derived boundary on the useful search space; the cap supplies such a boundary when the
> derivative evidence is resolved, and abstains when it is not.

This is the safest core framing because it includes the negative results as part of the mechanism.

---

## Phase Overview

| Phase | Goal | Output |
|-------|------|--------|
| **Phase 0** | Archive and correct Phase A diagnostics | Corrected freeze memo and diagnostic files |
| **Phase 1** | Repair structural metrics and re-diagnose v2.2 | Fair v2.2 diagnostic report and Gate 1 decision |
| **Gate 1** | Decide whether v2.2 is paper-ready | v2.2 rejected, v3 triggered |
| **Phase 2** | EvoGrow v3 design and validation | v3 validation report and Gate 2 decision |
| **Gate 2** | Decide whether v3 is paper-ready | v3 rejected |
| **Phase 2b** | Stage-cap design, audits, and failure diagnosis | Final capped variant and cap limitations |
| **Phase 3** | ODEBench protocol and literature reference alignment | System classification, metrics, protocol-audit document |
| **Phase 4** | Cluster and schema validation | Runtime/schema/metric validation, no paper claims |
| **Phase 5** | Full ODEBench Phase B campaign | Final experiment records |
| **Phase 6** | Analysis and paper writing | Paper draft with result placeholders filled |

---

## Phase 0 -- Archive and Correct Phase A

### Goal

Correct known diagnostic issues in Phase A without changing the original run data.

Phase A remains exploratory. It is used to guide algorithmic diagnosis, not to support final Paper 1
claims.

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

#### WP-0.1 -- Correct H4 claim in freeze memo -- done 2026-05-17

H4 is vacuous: all usage-policy variants achieved `exact_match_rate = 0` on high-stage systems, so
the expected ordering holds only through ties.

#### WP-0.2 -- Fix generalization data path -- done 2026-05-17

The config path was corrected and the OMIT verdict reproduced.

---

## Phase 1 -- Metric Repair and v2.2 Diagnostic Re-Analysis

### Goal

Evaluate v2.2 after repairing structural metrics, and determine whether its failures are metric
artifacts or genuine search failures.

### Key Issue: Growth Without Pruning

EvoGrow may retain near-zero terms. Structural recovery must distinguish between:

- raw discovered structure
- effective pruned structure used for support evaluation

### Support-Pruning Rule

For support-matching evaluation only, a term is pruned from equation `k` if:

```text
|coeff| < max(1e-6, 1e-3 x max_abs_coeff_in_equation_k)
```

This pruning is applied only for evaluation. It does not change search, parameter optimization, or
population state.

### Required Metrics

For exact systems, store both:

- `exact_support_match_raw`
- `exact_support_match_pruned`

The paper may use the pruned metric as the main structural recovery metric, but the raw metric must
remain available for transparency.

### Gate 1 Decision -- 2026-05-30

**Decision: v2.2 fails Gate 1. Phase 2 was triggered.**

v2.2 established the substrate, but did not solve coupled-system structural recovery. The failure
is not only a metric artifact: `pruned_match = false` persists on coupled systems, including cells
with very low loss and with the true structure available at the active stage.

The diagnosed structural limitation remains part of the paper:

> The search is growth-only. `_expand` only adds terms, and every equation line starts from one
> random term. Once a wrong term enters a line, it cannot leave. Selection is the only corrective
> mechanism, so a line can exhaust `MAX_TERMS = 6` with a mixture of true and false terms.

This limitation is not fixed in Paper 1. A remove/replace operator or beam-style search belongs to
future work on search power within a stage.

---

## Phase 2 -- EvoGrow v3 Design and Validation

### Scientific Motivation

v3 tested whether equation-wise stage progression could fix v2.2's system-wide promotion failure.
It replaced a single global stage state with per-equation stage state and used an equation-local
derivative-residual signal.

### Gate 2 Decision -- 2026-07-31

**Decision: v3 fails Gate 2. v3 is not the final Paper 1 variant.**

Evidence from the pre-registered decision cell showed better fit than v2.2 but no successful
complexity allocation:

| Criterion | Target | Observed | Verdict |
|-----------|--------|----------|---------|
| `eq_final_stages[1]` | 3 | 5 | failed |
| `du1` support | exactly `{u1, u1^2, u1*u2}` | extra `u2` term | failed |
| loss | <= `0.001391623174905009` | `2.5195575964774715e-4` | met |

The v3 promotion rule asks for `r_k > loss_tol = 1e-8`. On coupled systems, the residual floor is
around `1e-3`, so the rule cannot distinguish under-modelling from an irreducible floor. WP-L2 then
showed a second problem: `r_k` is contaminated by derivative-estimation error, and models with more
terms can absorb more of that error. The signal is biased toward "more terms help."

v3 is therefore retained as documented failure analysis:

> v3 changed who decides, but not what evidence justifies a promotion.

---

## Phase 2b -- Look-Ahead Stage Cap

### Goal

Add a per-equation upper bound on useful staged growth before search begins.

The cap is the Paper 1 contribution. It is a data-driven search-space controller, not a structural
recovery fix and not a v3 continuation.

### Design Rule 1 -- Positive Evidence, Not Absence of Evidence

**Defect source:** System 63.

The System 63 defect showed that missing evidence is not evidence for a cap. The cap must rest on a
positive residual drop or a resolved floor, never on the mere absence of later gain. System 63 is
therefore the identifiability boundary, not a Phase B cell for the capped comparison: its cap is
`nothing` everywhere, so the capped variant is identical to v3 there.

### Design Rule 2 -- Look Ahead As Far As The Basis Creates Structural Gaps

**Defect source:** WP-C1 horizon audit.

The basis stages by degree, not parity. Odd nonlinearities can first become approximable two stages
later, so a short horizon can miss the useful term. The audit covered the exact Phase B systems,
both initial-condition sets, horizons 2 to 5, and 320 equation-level rows. The adopted default is
`lookahead_horizon = 5`, matching the current staged polynomial basis depth.

The horizon evidence to carry into the paper:

- horizon 5 is row-wise cap-identical to horizon 3 across 80 `(system, ic_set, equation)` keys
- horizon 5 is used because it means looking to the basis end, not because 3 was tuned
- System 38 moves from `nothing` to cap 4 on both IC sets when the horizon is extended

### Design Rule 3 -- Abstain In The Doubt Band

**Defect source:** WP-C4.

WP-C4 replaced a binary cap/continue decision with three outcomes:

| Later residual drop | Decision |
|---|---|
| `<= 0.35` | continue looking and allow a higher cap |
| `>= 0.62` | cap as before |
| between `0.35` and `0.62` | return `nothing` |

The rule is deliberately conservative: an unnecessary `nothing` costs compute, while a false cap
can remove the solution. WP-C4 reports 80 horizon-5 rows compared, finite caps reduced from 49 to
45, 8 total cap changes, 4 finite-to-finite changes, and 4 finite-to-nothing changes. No truncated
rows remain under that audit.

### Cap Evidence To Report

The cap must be reported as a controller with a measured safety/economy tradeoff:

- finite caps decreased from 49 to 45 on the exact equation rows
- the surrendered finite caps cost compute, not a known solution
- the behavior fingerprint covers `_cap_split_decision` and nothing else
- derivative estimation, floor computation, split aggregation, and the full search loop remain
outside that behavior fingerprint

### Cap Limitations To Report

These limitations must appear in the paper without minimization:

1. `pruned_match = false` persists on coupled systems, even at very low loss. The cause is the
   additive search operator: `_expand` only adds, every line starts from a random term, and a wrong
   term can never leave a line.
2. The cap is auditable only on the 20 exact systems. The 43 surrogate systems have no true support,
   so controller safety is not auditable there by construction.
3. The cap gives up sharpness for safety: finite caps fell from 49 to 45 on the exact equation rows.
4. The behavior fingerprint covers `_cap_split_decision` only.
5. System 63 is the identifiability boundary and not a capped Phase B cell.
6. System 31 IC set 2 remains a low-dynamics boundary case in the sampling protocol.
7. The floor-depth constant `0.1` is load-bearing and must be reported as such.
8. Split aggregation robustness remains open: rows 12 / IC 1 and 31 / IC 2 flip through split
   majority voting rather than a clear detection.

---

## Phase 3 -- ODEBench Protocol and Literature Reference Alignment

### Goal

Prepare the final full-suite evaluation and clarify how EvoODE results can be compared to
published ODEBench-related results.

No external baselines are run in this project. Published results may be used only as published
reference context unless protocol equivalence is established.

### Phase B Sampling Protocol -- decided 2026-08-03

Phase B adopts the dataset's sampling protocol but integrates trajectories internally:

| Component | Decision |
|---|---|
| Systems | all 63 ODEBench systems |
| Time span | `t in [0, 10]`, as shipped |
| Sampling | 512 uniform points, both endpoints included |
| Initial conditions | both sets per system |
| Trajectory source | self-integration with `Tsit5`, `abstol = reltol = 1e-9` |
| Noise | none |
| Run count | 63 systems x 2 conditions x 3 seeds x 2 IC sets = 756 |

The shipped trajectories are not adopted because their solver accuracy would impose MSE floors
from `2.5e-2` to `6.1e-10` on verified systems, putting some current EvoODE results out of reach.

If published numbers used the shipped trajectories, EvoODE works on cleaner data than the
comparison. This must be declared as a protocol deviation in EvoODE's favour until the publications
are checked.

### System Classification

All 63 systems are split into:

1. **Exact systems:** exactly representable in the current staged basis.
2. **Surrogate systems:** not exactly representable in the current staged basis.

The exact set contains 20 systems. The surrogate set contains 43 systems.

For exact systems, record expected stage, true support, dimensionality, and term types. For
surrogate systems, record the basis-gap reason.

### Core Metrics

Exact systems:

- support recovery through raw and pruned support equality
- reached stage
- stage overshoot
- wasted levels
- stability observations

Surrogate systems:

- R^2
- loss
- reached stage
- stability observations

Exact and surrogate systems are never mixed into one structure-correctness metric.

Cost and efficiency:

- use counters such as `total_parameter_fits`, `total_loss_evals`, `total_ode_solves`, levels, and
  stages
- treat `elapsed_s` as context only
- do not use wall-clock time as evidence for method quality or search efficiency

### Valid-Run Rule

A run is valid if:

- `status = finished`
- `loss` is finite and non-NaN
- predicted trajectory exists

Poor results remain valid. Invalid runs are only NaN loss, missing prediction, timeout, crash, or
failed run.

---

## Phase 4 -- Cluster and Schema Validation

### Goal

Validate the selected final capped variant before launching the full Phase B campaign.

No paper claims are derived from this phase.

### Scope

Use small validation and pilot runs only to validate schema, runtime mechanics, metrics, and cluster
handoffs.

The compute path has been verified end to end on SCCH "Orion", an OpenShift/Kubernetes cluster.
The campaign path uses a container built by GitLab CI, Kubernetes indexed jobs, and results on NFS.

### Go Criteria

- all validation runs either finish, fail cleanly, or timeout cleanly
- schema validation passes
- R^2 and support metrics can be computed
- logs and outputs are complete
- fingerprints are recorded
- no aggregate metric pipeline produces unexplained NaNs

---

## Phase 5 -- Full ODEBench Phase B Campaign

### Goal

Run the final selected capped EvoGrow variant on the full ODEBench protocol.

This is the only source of final Paper 1 results.

### Runs

```text
63 systems x 2 pretuning conditions x 3 seeds x 2 IC sets = 756 runs
```

No GP baseline, no v1, and no v2.1 are part of the Phase B scope.

### Provenance

Every final campaign record must be identified by three fields:

1. Git hash
2. Configuration fingerprint or Phase B fingerprint
3. `stage_cap_behavior_fingerprint`

The current values from `CLAUDE.md` are:

| Field | Value |
|---|---|
| Phase B fingerprint | `e361a2af49366670` |
| Regression fingerprint | `1d0ccf8d53c6576d` |
| Stage-cap behavior fingerprint | `61b6548ef0014593` |

These values carry no final Phase B campaign records yet.

### Result Placeholders

The following sections must remain placeholders until campaign records exist:

- **Fit quality on all 63 systems:** placeholder, no Phase B records yet.
- **Support recovery on the 20 exact systems:** placeholder, no Phase B records yet.
- **R^2 on the 43 surrogate systems:** placeholder, no Phase B records yet.
- **Stage-cap economy counters:** placeholder, no Phase B records yet.
- **Pretuning on/off comparison:** placeholder, no Phase B records yet.
- **Robustness, failures, and stability:** placeholder, no Phase B records yet.

---

## Phase 6 -- Analysis and Paper

### Primary Analyses

Across all 63 systems:

- R^2
- simulation loss
- valid-run rate
- failure and timeout counts
- solver-failure counts
- reached stages
- stability observations

Exact systems only:

- `exact_support_match_raw`
- `exact_support_match_pruned`
- per-equation required stage
- per-equation cap
- final stage
- stage overshoot
- wasted levels
- cap correctness where true support exists

Surrogate systems only:

- R^2 and loss
- approximation behavior
- final stage reached
- basis mismatch effects
- stability and failure modes

Search economy:

- `total_parameter_fits`
- `total_loss_evals`
- `total_ode_solves`
- levels
- stages

Wall-clock time is not evidence. Timing may be reported for capacity planning only when measured on
dedicated hardware and labelled as such.

### Published Reference Context

External ODEBench-related numbers may be cited from the literature only as published reference
context until the protocol audit establishes comparability.

No claims about SINDy or PySR comparisons are allowed while the external protocol columns remain
unfilled.

### Planned Paper Structure

1. Introduction: interpretable ODE discovery and the need for controlled structure search
2. Related Work: SINDy, PySR/GP, ODEFormer, staged search, and search-space control
3. Method: EvoGrow staged basis expansion and the look-ahead stage cap
4. Failure Analysis: v2.2, v3, and the three cap design rules
5. Experimental Protocol: ODEBench Phase B, exact/surrogate split, sampling, and provenance
6. Results: placeholder until Phase B campaign records exist
7. Analysis: where the cap controls complexity, where search still fails, and why
8. Limitations and Future Work: additive search, surrogate unauditability, baselines, noise,
   stronger within-stage search
9. Conclusion

### Allowed Claim Types

Claims are only made after final results are available.

Allowed claim templates:

- **Fit-quality claim:** EvoODE achieves the reported R^2 or loss outcomes under the frozen Phase B
  protocol.
- **Structural recovery claim:** EvoODE recovers effective support on the reported subset of exact
  systems under the frozen pruning rule.
- **Search-space-control claim:** the cap limits or abstains from staged growth according to the
  frozen decision rule.
- **Mechanistic claim:** the v2.2 -> v3 -> capped sequence exposes why staged incremental growth
  needs a data-derived search-space boundary.
- **Robustness claim:** EvoODE completes successfully on the reported number of Phase B cells.
- **Failure-mode claim:** failures are dominated by the reported categories, with exact and
  surrogate systems separated.

No claim may be derived from Phase A exploratory results.

---

## Future Work / Separate Paper Ideas

The following topics are outside the main Paper 1 scope:

- remove/replace operators for growth-only search
- beam search or forward-stepwise variants inside a stage
- search power within a stage: population size, child generation, parsimony pressure
- pretuning / OLS warm-start as a separate ablation
- noise robustness
- irregular sampling
- extrapolation to unseen initial conditions
- in-house SINDy / PySR / GP benchmark implementation
- candidate-level optimizer timeouts and line-search cost control
- adaptive basis redesign
- alternative pruning and sparsification strategies
- equation-wise v3 extensions beyond the rejected residual-promotion rule

---

## Implementation Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Growth-only search prevents structural recovery | High | Report as limitation; defer remove/replace or beam-style search to future work |
| Cap safety is unauditable on surrogate systems | High | Separate exact and surrogate metrics; do not claim support safety on surrogates |
| Cap loses sharpness by abstaining | Medium | Report finite caps 49 -> 45 and explain compute-vs-safety tradeoff |
| Behavior fingerprint is too narrow | Medium | State that it covers `_cap_split_decision` only |
| Published baseline protocols remain unverified | Medium | Treat published numbers as contextual only |
| Phase B records do not share provenance | High | Require Git hash, config or Phase B fingerprint, and behavior fingerprint |
| Wall-clock is overinterpreted | Medium | Use counters for cost claims; label timing as context or capacity planning |
| Analysis pipeline remains Phase-A shaped | Medium | Update downstream analysis before final result interpretation |

---

## Scientific Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Structural recovery is low on exact coupled systems | High | Frame paper as mechanistic search-space-control study and report additive-search cause |
| The cap saves search space but not solutions | High | State contribution as controller, not structural recovery fix |
| Surrogate performance is poor or unstable | Medium | Report via R^2, loss, reached stage, and stability observations only |
| External reviewers expect in-house baselines | Medium | State non-goal and protocol-audit status clearly |
| System 63 is misread as a failure cell | Medium | Present it as the identifiability boundary |

---

## Frozen Elements

### Phase A

- `paper1_phaseA_v1` run data remain unchanged.
- Phase A is exploratory and not used for final claims.

### After Gate 1

- v2.2 failed Gate 1 and is retained as substrate and failure evidence.

### After Gate 2

- v3 failed Gate 2 and is retained as failure analysis.

### After Cap Selection

- `evogrow_v2_2_stage_capped` is the final Paper 1 variant.
- The cap design rules and known limitations must be reported.

### After Phase 3

- Phase B sampling uses 512 points over `t in [0, 10]`, both IC sets, self-integrated with `Tsit5`
  at `abstol = reltol = 1e-9`.
- Exact and surrogate systems are evaluated separately.

### After Phase 5 Begins

- The full Phase B campaign manifest is frozen.
- No systems may be removed.
- No settings may be changed without creating a new experiment identifier.

---

## Document Maintenance

This document is updated at phase transitions:

- record Gate decisions and the evidence behind them
- record cap-rule changes and fingerprint consequences
- update protocol-audit status
- fill result placeholders only from final Phase B campaign records
- add final claim decisions after Phase B analysis

Last draft update: 2026-08-17.
Current phase: Phase B prepared but final campaign records do not exist yet.

---

## Change List Against The Existing `PAPER_1.md`

This list is intentionally explicit so the replacement diff is reviewable.

| Existing section | Draft action | Reason |
|---|---|---|
| Top warning block | Replaced | The draft itself is now explicitly marked as non-authoritative until accepted |
| Critical Scope Decision | Replaced | The scope is no longer the 2026-05-17 staged-growth/v3 framing; the contribution is the stage cap |
| Explicit Non-Goals for Paper 1 | Replaced | Kept the no-baseline rule, added no direct SINDy/PySR claims and no Phase B result claims |
| Pretuning Decision | Replaced | Pretuning is not central, but Phase B now explicitly has `pretune_on` and `pretune_off` conditions |
| Current Status | Replaced | The old status predates the final capped variant, Phase B protocol, and behavior fingerprint |
| Paper Strategy in One Sentence | Replaced | The paper strategy now centers on search-space control and documented failure analysis |
| Main Claim Strategy | Replaced | Claim C is reframed around the cap; performance claims remain placeholders |
| Phase Overview | Replaced | Added Phase 2b for the cap and updated later phases to Phase B campaign status |
| Phase 0 -- Archive and Correct Phase A | Mostly unchanged | The Phase A correction logic still applies and remains historical context |
| Phase 1 -- Metric Repair and v2.2 Diagnostic Re-Analysis | Replaced | The section now records the Gate 1 outcome and the growth-only limitation |
| Phase 1 Hyperparameter Defaults for Diagnosis | Removed | It was a historical diagnostic detail, not part of the current execution plan |
| Gate 1 -- Is v2.2 Paper-Ready? | Replaced | The decision is already settled: v2.2 failed Gate 1 |
| Phase 2 -- Conditional EvoGrow v3 Design and Validation | Replaced | v3 is no longer conditional or forward-looking; it is a completed failed branch |
| Gate 2 -- Is v3 Paper-Ready? | Replaced | The decision is already settled and its failure mechanism must be reported |
| Scope decision after Gate 2 | Replaced | The old open decision is now settled in favour of the capped variant |
| Result of the decisive step | Replaced | The decisive-step details are folded into the cap and failure-analysis framing |
| Phase 3 -- ODEBench Protocol and Literature Reference Alignment | Replaced | The Phase B sampling protocol is now decided; external columns remain unfilled |
| Phase 4 -- Small Validation Run | Replaced | The cluster/schema validation context has moved beyond the old local-only framing |
| Phase 5 -- Full ODEBench Cluster Run | Replaced | The run plan is now 756 Phase B runs with two pretuning conditions, not 189 runs |
| Phase 6 -- Analysis and Paper | Replaced | Metrics now separate exact support, surrogate R^2, cap decisions, and cost counters |
| Published Reference Context | Replaced | Direct external comparisons remain prohibited until the audit is filled |
| Future Work / Separate Paper Ideas | Replaced | Added within-stage search power, remove/replace operators, and beam-style search |
| Implementation Risks | Replaced | Risks now reflect cap safety, surrogate unauditability, provenance, and analysis drift |
| Scientific Risks | Replaced | Risks now reflect the controller framing and unresolved structural recovery |
| Frozen Elements | Replaced | Frozen elements now include Gate 1, Gate 2, cap selection, and Phase B sampling |
| Document Maintenance | Replaced | Maintenance now requires filling placeholders only from final Phase B records |

---

## Open Contradictions And Source Inconsistencies

These are listed rather than resolved in this draft.

1. `CLAUDE.md` still says `PAPER_1.md` is authoritative and takes precedence if the files drift,
   while the current task and `CLAUDE.md` also state that `PAPER_1.md` is stale and that
   `CLAUDE.md` / `DIARY.md` carry the current state until revision.
2. The requested source name `docs/wp_c1_stage_cap_horizon_audit.md` exists, but the file title
   inside it is `WP-C2 Stage-Cap Horizon Audit`.
3. The task text says the WP-C1 audit found 9 truncated equation rows on 5 of 20 systems at
   `lookahead_horizon = 2`; the current `docs/wp_c1_stage_cap_horizon_audit.md` reports 4
   truncated rows on systems 28 and 32 at horizon 2. `CLAUDE.md` records the 9-row result as an
   earlier campaign blocker and then describes later fixes.
4. The old `PAPER_1.md` warning block records Phase B fingerprint `ca02ea284d621f6d` and regression
   fingerprint `0825cdc88d9264a0`, while `CLAUDE.md` records current values
   `e361a2af49366670`, `1d0ccf8d53c6576d`, and behavior fingerprint `61b6548ef0014593`.
5. `docs/paper1_odebench_protocol_alignment.md` is last updated 2026-08-03 and says System 31 IC
   set 2 yields cap 1 against true stage 3; later `CLAUDE.md` and WP-C4 report that the doubt-band
   rule makes System 31 / IC 2 return `nothing`.
