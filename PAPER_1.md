# PAPER_1.md — EvoODE Paper 1: Execution Roadmap and Working Plan

This document is the **authoritative execution plan** for EvoODE Paper 1. It defines the paper
scope, the diagnostic gates and their decisions, the work phases, go/no-go criteria, risks and
frozen elements.

*Revised 2026-09-09: the paper scope changed from a mechanistic stage-cap study to a method paper.
See "Critical Scope Decision" below. The previous scope decision of 2026-08-03 is retained further
down as the historical record of how the cap became the contribution, because Phases 1 to 5 were
executed under it.*

| Where to look | For |
|---|---|
| `CLAUDE.md` | project orientation, architecture position, current priorities |
| `DIARY.md` | chronology — measurements, decisions, bug history, commit hashes |
| `docs/paper1_phaseC_benchmark_plan.md` | **the frozen Phase C claim → experiment → metric → output matrix** |
| `docs/architecture.md` | component reference |
| `docs/status_2026-09-09.md` | frozen status snapshot written before the scope decision |
| `docs/paper1_odebench_protocol_alignment.md` | Phase B sampling protocol and the comparability audit |
| `docs/hpc_requirements.md` | measured Phase B cost model and resource profile |
| `docs/paper1_freeze_memo_phaseA.md` | frozen Phase A results (historical, no paper claims) |
| `docs/wp_c1_stage_cap_horizon_audit.md`, `docs/wp_c2_stage_cap_failure_diagnosis.md`, `docs/WP-V1.md`, `docs/WP-C5.md` | the stage-cap evidence chain |
| `docs/WP-B1.md` | the wasted-search-level measurement |
| `docs/WP-N4.md` | the restart budget of the parameter fit |
| `docs/WP-N6.md` | the SINDy baseline on identical trajectories |

---

## Critical Scope Decision (2026-09-09) — Paper 1 is a method paper

**Paper 1 establishes EvoGrow as a method.** It is not a failure analysis, and it is not a
characterisation study of where incremental growth breaks.

> We introduce EvoGrow, an incremental structure-growth method for interpretable ODE discovery.
> EvoGrow progressively expands the admissible functional space instead of exposing the full search
> space at once. A trajectory-informed stage cap controls how far this expansion proceeds. We
> evaluate structural recovery, trajectory reconstruction, generalization and computational cost on
> ODEBench and compare EvoGrow against an established sparse-regression baseline.

Four things follow, and they are binding.

**1. EvoGrow is the object, not the stage cap.** EvoGrow is the whole incremental structure-discovery
strategy: incremental opening of the search space, staged function classes, growth instead of
enumeration, parameter optimization over integrated trajectories, selection, pruning, stage
progression, the stage cap, termination. The central idea is *don't expose the entire search space
at once — grow it.* The cap is a **mechanism inside** EvoGrow that controls how far the expansion
proceeds, and it gets its own ablation. It is not the paper's single innovation.

**2. Bad results keep their place, and it is not the headline.** The dim-3/4 structural collapse, the
add-only path dependence, the silent search levels and the optimizer failures are reported as
**evaluation results and limitations of EvoGrow v1**, in a Failure Modes section. They are not the
thesis, and they are not in the title.

**3. The 756-cell campaign is not automatically the final benchmark.** It was computed before the
methodological audit of 2026-09-07 closed, and it carries four defects that a final method benchmark
cannot have: no constant term in the basis, no persisted coefficients, both IC sets used as training,
and no uncapped arm. It remains valuable as exploration, diagnostics, ablation source, runtime
analysis and failure-case collection. It is **not** the source of the paper's main tables.

**4. The 5,248 core hours are sunk cost.** They must not shape the paper's scope. We do not fit the
paper to the campaign; we define the paper and then compute exactly the experiments it needs.

### What this decision replaces

The scope decision of 2026-08-03 made the look-ahead stage cap the contribution and the
`v2.2 → v3 → capped` failure chain the central story. That framing produced Phases 1 to 5 and is
retained below as the historical record. It is **superseded**: the failure chain becomes design
justification inside the Method section, not the paper's argument.

---

## Explicit Non-Goals for Paper 1

**Superseded non-goals (2026-09-09).** Two prohibitions decided on 2026-08-22 are lifted, because
Claim D now requires exactly what they forbade:

- ~~"Paper 1 does not run new in-house baselines for GP, PySR, SINDy…"~~ — **SINDy is now a main-table
  baseline**, computed in-house on identical trajectories (WP-N6, extended in Phase C). GP, PySR,
  ODEFormer, GODE and Operon stay out.
- ~~"Paper 1 makes no quantitative cross-method performance claim. Not a cautious one, not an
  approximate one — none."~~ — **Quantitative EvoGrow-versus-SINDy comparison is now in scope**, under
  the fairness conditions of Claim D: identical trajectories, identical train/test ICs, all SINDy
  configurations reported, no undeclared cherry-picking, and cost reported beside every quality
  number.

The remaining non-goals stand:

Paper 1 does **not** claim to beat SINDy. The comparison answers *where does EvoGrow stand relative
to an established sparse-regression baseline*, and the honest current answer includes a compute
disadvantage of roughly two orders of magnitude.

Paper 1 does **not** use pretuning as a headline mechanism, and no longer carries it as a
co-equal main variant. There is **one canonical EvoGrow configuration**; pretuning on/off is an
ablation. See "Pretuning Decision".

Paper 1 does **not** claim structural recovery on systems whose ground truth is not representable in
the frozen basis. Representability is declared per system and per equation, and structural metrics
are only ever interpreted together with it.

Paper 1 does **not** derive claims from Phase A, and does **not** derive its main tables from
Phase B. Phase B supplies diagnostics, ablations and failure analysis under an explicitly declared,
differently configured predecessor.

Paper 1 does **not** introduce a stopping rule or level budget. That decision was taken on the
evidence and is recorded in Phase 6.

Paper 1 does **not** tune hyperparameters on benchmark results. Once Phase C starts, the
configuration is frozen; any later change produces a new, fully declared experiment identifier.

---

## Pretuning Decision (revised 2026-09-09)

**The canonical EvoGrow configuration runs `pretuning = false`.** Pretuning becomes an ablation arm,
not a second main version.

The evidence is one-directional. Grouped by system, IC set and condition — 126 pairs per condition
over 63 systems — pretuning collapses seed diversity on all three targets: support pattern 96/126
against 61/126, R² 96/126 against 35/126, loss 96/126 against 14/126, with cluster-robust
p = 1.0e-5 and **not one pair in the reverse direction** (WP-A7). The collapse shows on the
*discovered support pattern*, not only on a number: the OLS warm start pulls the search into the
same structure regardless of seed. That is the anchoring risk the project has recorded since
population carry-over was introduced, measured for the first time.

**One condition attaches to this decision, and it produced its own frozen parameter.** Under
`pretuning = false` every parameter fit draws `0.1 .* randn` (`src/optimize/bfgs.jl:269`). What that
gives today is **not** a controlled multistart: each candidate structure gets exactly one fit, and a
structure is only re-started if the search happens to generate it again — so the effective restart
count is the **`StructureSpec` duplicate rate, which has never been measured**. The canonical k is
therefore 1 with uncontrolled repetition, which is not a describable method.

That matters beyond bookkeeping. WP-N4 measured, with the *true* structure supplied, that a single
fit hits the sentinel loss `1e6` in **15 of 102 cells**, 13 at k = 2 and **zero at k = 3**. Carried
into the search, this is a **search-quality** problem, not an optimizer footnote: roughly one in
seven correct candidate structures is discarded because its fit failed, not because the structure
was wrong.

**Decided 2026-09-09 — retry-on-failure, up to k = 3, canonical and declared.** One fit per
candidate structure; a restart is drawn **only** when the fit fails (sentinel loss, non-success
termination). This captures essentially the whole WP-N4 effect at an overhead of roughly the failure
rate — about 15 % — instead of the ~200 % a true per-structure multistart at k = 3 would cost, which
on a full-mirror Phase C would mean 25,000–35,000 core hours and would further damage the very cost
comparison Claim D has to report honestly.

**This must be named precisely in the paper: it is retry-on-failure, not a multistart.** The two are
different mechanisms and only one of them was measured by WP-N4 in its original form. The value
k = 3 is taken from an **oracle diagnostic**, never from benchmark performance — that is what keeps
it out of the "hyperparameter tuned on the benchmark" category.

The restart dependence itself becomes a **subset ablation with a cost axis**: recovery against
*fits*, never against k, plus the `StructureSpec` duplicate-rate measurement, without which the
k = 1 reference point is not even defined.

The earlier caveat still holds and is unchanged: pretuning's effect on cost is strongly
system-dependent and points in different directions within a single dimension class — runtime
factors 0.30, 0.92 and 0.97 on three chaotic 3D systems (probe, 2026-08-20). Any pretuning statement
is per-system or per-class, never a single global factor.

**Retracted, and it must stay retracted.** The Phase B structural difference between conditions
(60/120 against 50/120 support hits) is **not a reportable finding**: the cluster-robust permutation
test that swaps the condition label per system gives p = 0.218 against 20 effective systems.
Additionally, `pretune_off` has two seed-dependent sources (structure search *and* parameter start)
where `pretune_on` has one, so part of its apparent advantage follows from the design. It survives
as an ablation about the implicit multistart, not as a discovery.

---

## Current Status (as of 2026-09-09)

| Item | Status |
|------|--------|
| Paper scope | **method paper, decided 2026-09-09.** EvoGrow is the object; the cap is a component with its own ablation |
| Phase C | **defined, not started.** `docs/paper1_phaseC_benchmark_plan.md` |
| `paper1_phaseA_v1` | frozen exploratory set, 300/300 runs. Not used for final claims |
| `paper1_phaseB_v1` | **complete, demoted from main benchmark to diagnostics/ablation source** (2026-09-09) |
| Gate 1 | decided 2026-05-30: v2.2 fails |
| Gate 2 | decided 2026-07-31: v3 fails |
| Final variant substrate | `evogrow_v2_2_stage_capped`, settled 2026-08-03 |
| Stage-cap defect | **solved** (WP-C1 to WP-C5, 2026-08-20): 0 truncated equation rows of 80, 48 finite caps |
| Regression evidence | 120 records, 30 cells, loss bit-identical 30/30, −25.4 % loss evaluations. **Superseded as Claim B evidence by the Phase C uncapped arm** |
| Level budget | **decided against** (WP-B1, 2026-08-21): 30 levels stay, the waste is reported as a result |
| Canonical basis | **frozen 2026-09-13: `staged_polynomial_basis_with_constant`.** Probe **complete 336/336 since 2026-09-14** (335/336 at the decision, evaluated by WP-N15); decided on representability *against* its recovery numbers |
| Canonical pretuning | **decided 2026-09-09: `pretuning = false`**, with the restart count made explicit |
| Uncapped-arm scope | **decided 2026-09-09: full mirror of the canonical arm** — 63 systems, 3 seeds, both IC sets = 378 paired cells |
| Restart policy | **decided 2026-09-09: retry-on-failure, up to k = 3.** Canonical, explicit, declared. Restart dependence is a subset ablation with a cost axis |
| Phase C cost estimate | **~12,300–15,900 core hours, 5–7 weeks on Orion (2026-09-13)**, after the basis freeze added ~20 % to the counting quantities. The uncapped arm carries the majority |
| Structural F1 / precision / recall | **does not exist anywhere in the codebase.** Must be built before Phase C |
| Phase B fingerprint | `604e79733b22d64d` — 756/756 records, `git 91f88c4` clean, complete 2026-09-04 |
| Stage-cap behaviour fingerprint | `ffb0266c7913352c` (probe version 2) |
| Campaign analysis | complete (WP-A5 to WP-A9, 2026-09-07): tables T1–T5, pretuning contrast, seed-collapse, level waste, per-system table |
| Coefficient persistence | **added** (WP-N1, 2026-09-08). The 756 campaign cells predate it and carry no coefficients |
| Held-out evaluation | **exists** (WP-N5, 2026-09-09): R² > 0.9 falls from 95.5 % reconstruction to 68.2 % generalization on the dim-1 probe |
| Baseline | **exists** (WP-N6, 2026-09-09): SINDy on identical trajectories. `docs/WP-N6.md` |
| Evidence in the repository | run registries, campaign history and the descriptive tables are tracked since 2026-09-09 |

---

## Paper Strategy in One Sentence

> Paper 1 introduces EvoGrow as an incremental structure-discovery method for interpretable ODE
> models, evaluates it on ODEBench for structural recovery, reconstruction, generalization and
> computational cost against a SINDy baseline, ablates the stage cap and the warm start, and reports
> the path dependence of add-only growth as the limitation that motivates the follow-up work.

---

## Main Claim Strategy (revised 2026-09-09)

Four claims, each with a defined experiment, comparison, metric and output. The full matrix — and
the rule that nothing is computed before the matrix is complete — is
`docs/paper1_phaseC_benchmark_plan.md`.

**Renumbering warning.** These labels replace the previous Claim A/B/C of this document. `DIARY.md`
and the WP reports cite the old labels; the old ones are preserved verbatim under "Superseded Claim
Labels" below so a citation can still be resolved. Never mix the two sets.

### Claim A — EvoGrow discovers interpretable ODE structure

> EvoGrow recovers the governing structure of dynamical systems from trajectory data, at a rate that
> depends on dimensionality, coupling and the representability of the ground truth in the frozen
> basis.

Reported metrics: exact structural recovery, term precision, term recall, structural F1, coefficient
error, reconstruction R², trajectory MSE.

**Representability is a precondition, not a footnote.** A method is not credited with a search
failure when the ground truth is not expressible in its search space. Every system is classified as
**fully representable**, **partially representable** or **non-representable**, and structural metrics
are only interpreted together with that class. The original basis represented 20 of 63 systems where
SINDy's plain polynomial library represented 40 — that is the reason the rule exists.

### Claim B — Stage capping controls search effort

> Stage capping substantially reduces the explored search space while preserving most of the
> resulting model quality.

**This claim is not currently supported and requires the Phase C uncapped arm.** Both Phase B arms
are capped, so the campaign has no counterpart; the existing difference evidence is the 30-cell,
5-system regression grid. The Phase C comparison is `EvoGrow capped` against `EvoGrow uncapped` with
everything else identical: systems, trajectories, ICs, seeds, basis, optimizer, initialisation,
restart policy, parameter budgets, search operators, integration settings, maximum reachable search
space. The uncapped arm is a **full mirror** of the canonical arm — 63 systems, 3 seeds, both IC
sets, 378 paired cells — and it is the single most expensive experiment in the project, because it
executes the full 30 levels where the capped arm stops early.

The intended main figure is the paired trade-off plot: computational saving on the x-axis, quality
difference `capped − uncapped` on the y-axis. Points far to the right and close to `y = 0` are the
visual form of this claim.

Reported: explored stages, explored levels, nonlinear fits, ODE integrations, core hours, final loss,
structural F1, exact recovery, reconstruction and generalization quality.

**Do not overstate.** "Without loss of quality" may be written only if that is what the paired data
show. The default formulation is *substantially reduces … while preserving most of*. Counts are the
evidence; core hours are capacity context and are labelled as such (Design Principle 7).

Half of the claim is already corroborated at campaign scale and can be cited as behaviour: 690 of
756 cells execute fewer than the 30 configured levels, and the executed count tracks the reached
stage. That shows the cap *restricts growth*; it does not show the restriction is free.

### Claim C — EvoGrow generalizes to unseen trajectories

> A model discovered on one initial condition describes an unseen trajectory of the same system, at
> a measurably lower rate than it describes the trajectory it was identified on.

Design, both directions, no averaging across them:

```text
train on IC1 -> reconstruction on IC1, generalization on IC2
train on IC2 -> reconstruction on IC2, generalization on IC1
```

This requires structure, coefficients and full model state to be persisted — impossible in Phase B,
available since WP-N1. The dim-1 probe already shows the metric carries: R² > 0.9 falls from 95.5 %
to 68.2 %, qualitatively the drop ODEFormer reports, and direction matters (IC2 → IC1 is worse in
both bases).

This block is what prevents EvoGrow from being read as an expensive trajectory fitter.

### Claim D — Where EvoGrow stands against an established baseline

> EvoGrow provides an alternative incremental trajectory-based structure-search mechanism with
> different algorithmic properties, comparable performance on simple system classes, higher current
> computational cost, and specific failure modes that motivate subsequent methodological work.

SINDy on identical trajectories, identical train/test ICs, comparable libraries where meaningful,
**all** configurations reported. The current SINDy figure is the maximum over ten configurations,
which is deliberately favourable to SINDy and is declared as such.

Cost belongs beside every quality number: SINDy solves one linear regression per equation; EvoGrow
runs a median of 410 nonlinear fits per cell, each with ODE integrations.

### Superseded Claim Labels (pre-2026-09-09, for resolving older citations)

- **Old Claim A — Fit-Quality Claim.** Phase B fit-quality outcomes on the 63-system protocol.
  Content survives inside new Claim A.
- **Old Claim B — Search-Space-Control Claim.** The cap restricts growth at an unchanged result.
  Content survives as new Claim B; its retracted second half is the reason the uncapped arm exists.
- **Old Claim C — Primary Mechanistic Claim.** The `v2.2 → v3 → capped` sequence and the
  non-selectable threshold. **No longer a paper claim**; it becomes design justification in the
  Method section and a Limitations item. The WP-V1 negative result is not softened by the move.

---
## Phase Overview

| Phase | Goal | Status |
|-------|------|--------|
| **Phase 0** | archive and correct Phase A diagnostics | done |
| **Phase 1** | repair structural metrics, re-diagnose v2.2 | done |
| **Gate 1** | is v2.2 paper-ready? | decided 2026-05-30 — no |
| **Phase 2** | EvoGrow v3 design and validation | done |
| **Gate 2** | is v3 paper-ready? | decided 2026-07-31 — no |
| **Phase 2b** | stage-cap design, audits, failure diagnosis | closed 2026-08-20 |
| **Phase 3** | ODEBench protocol and literature alignment | protocol done; external audit columns open |
| **Phase 4** | cluster, schema and cost validation | done |
| **Phase 5** | full ODEBench Phase B campaign | done 2026-09-04, 756/756 — **demoted to diagnostics** |
| **Phase 6** | Phase B analysis | done 2026-09-07 (WP-A5 to WP-A9) |
| **Phase C** | **canonical EvoGrow evaluation — the active phase** | **defined, not started** |

**Everything from Phase 0 to Phase 6 below is the historical execution record**, written and executed
under the 2026-08-03 scope in which the stage cap was the contribution. It is kept because it
documents how the method reached its current form and because Gate 1, Gate 2 and the cap audits are
cited by `DIARY.md` and the WP reports. It is **not** the plan for the paper's main results — that is
Phase C.

---

## Phase C — Canonical EvoGrow Evaluation

The frozen, pre-registered evaluation from which Paper 1's main tables and figures come. The full
claim → experiment → comparison → metric → output matrix is
`docs/paper1_phaseC_benchmark_plan.md`; that document is the operational authority for Phase C and
this section is its summary.

**The governing rule: nothing long-running starts until the matrix is complete and the configuration
is frozen.** Not the other way round. The reason this rule exists is Phase B, which was computed
before the methodological audit closed and therefore cannot serve as the main benchmark.

### The four arms

| Arm | Function | Scope |
|---|---|---|
| **EvoGrow capped** | the proposed final method | 63 systems × 3 seeds × 2 IC sets = 378 cells |
| **EvoGrow uncapped** | stage-cap ablation, Claim B | full mirror, 378 paired cells |
| **SINDy** | external baseline, Claim D | all configurations reported, identical trajectories |
| **Oracle-structure fit** | search-versus-optimizer diagnostic | true structure supplied, parameters fitted only |

The **oracle arm** separates two error classes that Phase B could not tell apart: a *search failure*
(the right structure was never found) and an *optimization failure* (the right structure is known and
the nonlinear trajectory fit still finds no good parameters). WP-N4 already showed the second class
is real — 15 of 102 cells at a single fit. It is cheap, because it runs no structure search, and it
may live in the appendix; the interpretation of every EvoGrow number depends on it.

### Blocking prerequisites — none of these may be skipped

1. ~~The canonical basis is not yet decided.~~ **Decided and frozen 2026-09-13: the canonical basis
   is `staged_polynomial_basis_with_constant`.** The dim-2 probe ran on Orion (335 of 336 cells at
   the time of the decision, **complete at 336/336 on 2026-09-14**, 0 errors, one identity triple
   `ec3b6bd` / `0290b75a28791195` / `ffb0266c7913352c` over every record), and it was evaluated by
   WP-N15. The re-evaluation on the complete set confirms what the plan predicted of the missing
   cell: it is a surrogate (system 44, seed 42, IC 2, constant basis, R² = 0.808) and moves only the
   constant arm's surrogate R² > 0.9 rate, from 90.7 % to 89.8 %; **no decision-bearing number
   changed.** **The decision was taken against the probe's
   own recovery numbers, not with them**, and that is the honest way to report it: on the nine dim-2
   systems exact under both bases the constant costs structure recovery (pruned 55.6 % → 35.2 %, raw
   13.0 % → 7.4 %) at an unchanged R² > 0.9 rate (94.4 % in both arms). It is decisive anyway,
   because representability is not a tuning parameter: without the constant the basis represents
   **20 of 63** systems where SINDy's plain polynomial library represents 40, and ten systems fail on
   the constant alone. A method paper cannot claim a search-strategy contribution while searching
   half the space of the baseline it compares against. The `git_hash = "not_collected"` defect was
   repaired by WP-N8 before the run.

   Two consequences are declared, not hidden. **The cost figures rise** — see the cost note in
   `docs/paper1_phaseC_benchmark_plan.md` §2. And **the paper's structure-recovery numbers will be
   lower than Phase B's**, because Phase B ran on the old basis; the two are never tabulated
   together anyway.
2. **Structural F1, term precision, term recall and coefficient error do not exist.** They appear
   nowhere in `src/`, `analysis/`, `experiments/` or `studies/` — the pipeline can only do exact
   support match today. Claim A cannot be reported without them.
3. **Three-way representability classification.** Fully / partially / non-representable, derived from
   `system_classification.csv` (`unmatched_terms`, `gap_reason`) and
   `representational_adequacy.csv`. Structural metrics are never reported without it.
4. **The restart policy must be implemented as declared** — retry-on-failure up to k = 3 — and the
   `StructureSpec` duplicate rate measured, because it defines the k = 1 reference point.
5. **A smoke test on a small system** before any cluster submission, per the standing rule for
   multi-hour runs.

### Cost

| Item | Estimate |
|---|---|
| capped canonical arm, 378 cells | ~2,600 core hours |
| uncapped mirror, 378 cells | ~5,200–7,900 core hours |
| oracle arm | < 20 core hours |
| SINDy | minutes |
| **Phase C total** | **~8,000–11,000 core hours, 3–5 weeks on Orion** |

Derived from Phase B's measured 5,248 core hours over 756 cells. The uncapped arm dominates because
it executes the full 30 levels where the capped arm stops early — Phase B cells averaged about 19.7
executed levels, and the late levels are the expensive ones. **The experiment that must show the cap
saves compute is itself the most expensive thing in the project.** That irony is worth stating in
the paper.

The uncapped arm keeps all 63 systems deliberately. dim 3 carries 75.6 % of Phase B's compute, so it
is where the saving is largest; a cap demonstration that omits the expensive class is the first thing
a reviewer attacks.

### Freeze discipline

Once Phase C starts, this configuration does not change on the basis of observed benchmark results:
basis, stage definitions, stage cap, pruning, expansion, selection, optimization, restart policy,
termination, seed handling, integration, preprocessing. A necessary later change produces a **new,
fully declared experiment identifier** — never an edit to a running configuration, and never a
version-drift chain (`v4`, `v4-paper`, `v4-paper-final`).

Two specific prohibitions, both of which the project has already violated once and diagnosed:

- **No pruning threshold chosen after seeing results.** WP-V1 is that mistake; WP-N2 additionally
  showed a 24-rule grid holds hits + deleted-true-term + surviving-extra-term constant at 45, so
  there is no better threshold to find.
- **No library component removed because it produces false positives.** That is the constant-term
  question, and it is decided before the freeze on probe evidence, not after the benchmark on
  benchmark evidence.

### What Phase B still supplies

Diagnostics (dimension and coupling effects, path dependence, failure cases), efficiency analysis
(runtime, fit counts, silent levels, cost distribution), the pretuning ablation (seed diversity,
anchoring), stage-cap behaviour (690 of 756 cells below 30 levels), and the failure-analysis material
(dim-3/4 collapse, Lorenz cases, identifiability, wasted effort).

**One caveat travels with all of it.** If Phase C freezes a different basis, Phase B ran a
differently configured method, and its failure analysis cannot be reported as the canonical method's.
Where Phase C covers the same ground — and for the failure analysis it does, with 378 capped cells
over all 63 systems and all dimensions — the Phase C numbers are the ones reported, and Phase B is
cited only for what Phase C does not cover.

---
## Phase 0 — Archive and Correct Phase A

Phase A remains exploratory: it guides algorithmic diagnosis and supports no final claim. The
original run data are unchanged.

- **WP-0.1** — corrected the H4 claim in the freeze memo (2026-05-17). H4 is vacuous: all
  usage-policy variants reached `exact_match_rate = 0` on high-stage systems, so the expected
  ordering holds only through ties.
- **WP-0.2** — corrected the generalization data path and reproduced the OMIT verdict (2026-05-17).

No runs were added to `paper1_phaseA_v1`, and WP-E2 later made a Phase A run *verify* the frozen
artefacts instead of rewriting them.

---

## Phase 1 — Metric Repair and v2.2 Diagnostic Re-Analysis

### Support-Pruning Rule (frozen)

For support-matching evaluation only, a term is pruned from equation `k` if

```text
|coeff| < max(1e-6, 1e-3 × max_abs_coeff_in_equation_k)
```

This applies to evaluation only. It never changes search, parameter optimization or population
state. Both `exact_support_match_raw` and `exact_support_match_pruned` are stored; the pruned metric
is the main structural-recovery metric, the raw one stays available for transparency.

### Gate 1 Decision — 2026-05-30: v2.2 fails

v2.2 established the substrate but did not solve structural recovery on coupled systems. The failure
is not a metric artefact: `pruned_match = false` persists on coupled cells, including cells with
very low loss and with the true structure available at the active stage.

The diagnosed cause stays in the paper as a limitation:

> The search is growth-only. `_expand` only adds terms, and every equation line starts from one
> random term. Once a wrong term enters a line it can never leave; selection is the only corrective.
> A line can therefore exhaust `MAX_TERMS = 6` with a mixture of true and false terms.

A remove/replace operator or a beam-style search belongs to "search power within a stage" and is
future work, deliberately outside Paper 1.

---

## Phase 2 — EvoGrow v3 Design and Validation

v3 replaced the single global stage state with per-equation stage state and promoted on an
equation-local derivative-residual signal `r_k`.

### Gate 2 Decision — 2026-07-31: v3 fails

Pre-registered decision cell:

| Criterion | Target | Observed | Verdict |
|-----------|--------|----------|---------|
| `eq_final_stages[1]` | 3 | 5 | failed |
| `du1` support | exactly `{u1, u1², u1·u2}` | extra `u2` term | failed |
| loss | ≤ `1.391623174905009e-3` | `2.5195575964774715e-4` | met |

Two mechanisms explain the failure. The promotion condition `r_k > loss_tol = 1e-8` is unreachable
on coupled systems whose residual floor is around `1e-3`, so it cannot distinguish under-modelling
from an irreducible floor. And WP-L2 showed `r_k` is contaminated by derivative-estimation error,
with the capacity to absorb that error growing with term count — biasing the signal toward "more
terms help". Downstream confirmation: on System 31 seed 42 the v3 substrate alone loses about six
orders of magnitude against v2.2.

v3 is retained as documented failure analysis:

> v3 changed **who** decides, not **what evidence** justifies a promotion.

---

## Phase 2b — The Look-Ahead Stage Cap

The cap is the contribution: a per-equation upper bound on useful staged growth, derived before
search from trajectory and basis. It is a search-space controller, not a structural-recovery fix.

### Design Rule 1 — positive evidence, never the absence of evidence

**Bought with:** the System 63 defect.

Missing evidence is not evidence for a cap. A cap must rest on a positive residual drop or a
resolved floor. System 63 consequently caps at `nothing` everywhere and is the **identifiability
boundary** of the method, not a capped Phase B comparison cell.

### Design Rule 2 — look ahead as far as the basis creates structural gaps

**Bought with:** the WP-C1 horizon audit (all 20 exact systems, both IC sets, horizons 2–5,
80 equation rows).

The basis stages by **degree, not parity**, so odd nonlinearities first become approximable two
stages later and a horizon of 2 never reaches them. Six rows move when the horizon is raised, and
every new cap lands exactly on the required stage — System 28 eq 2 from 1 to 5, System 32 eq 2 from
1 to 4, System 38 eq 1 from `nothing` to 4, the last one *tightening* a previously uncapped equation
onto the cubic term it needs.

Horizons 3, 4 and 5 are cap-identical on all 80 rows, so the parameter is inert above 3. The shipped
value is **`lookahead_horizon = 5` = the number of basis stages**, chosen so the paper reports "look
to the end of the basis" rather than a tuned constant.

### Design Rule 3 — credit a mechanism only through an experiment that isolates it

**Bought with:** WP-C4, and it is the most expensive of the three rules.

WP-C4 had introduced a third decision outcome — abstain inside an ambiguous band, issue no cap at
all — and was credited with repairing the Lorenz rows. WP-V1 measured the band over all 80 rows:

| Measured over 80 equation rows | Result |
|---|---|
| caps correct | 77 |
| caps wrong | 0 |
| wrong caps prevented by the band | **0** |
| correct caps surrendered to the band | **3** |

And all four Lorenz rows return cap 3 under the binary decision as well: the repair came from the
**reopen branch**, not from the band. WP-C5 removed the band. Finite caps rose 45 → 48, exactly the
three rows WP-V1 predicted (12 / IC 1, 31 / IC 1, 55 / IC 2 eq 2).

### The mechanism as shipped

The walk over stages is binary again. A later stage that drops the residual to ≤ `0.35` of the floor
**reopens** the walk; otherwise the walk caps at this stage. All conditions are **relative**: no
stage index and no system identity enters the rule — WP-C3 was rejected for exactly that.

Two constants are load-bearing, and both sit inside `config_fingerprint` since WP-C5, so moving
either moves the campaign identity:

| Constant | Value | Status |
|---|---|---|
| `post_floor_significant_drop_ratio` | 0.35 | **not selectable from data** — see below |
| `post_floor_min_floor_ratio` | 0.1 | separates control 61 / IC 1 (floor ratios 0.03–0.07) from the targets (0.30–0.85) by a factor of four — a verified **margin**, not a derivation |

### The negative result — the threshold cannot be selected from the data

Leave-one-system-out over the 20 exact systems puts the reopen threshold between **0.044 and
0.278**, while the shipped value is **0.35**; at every selected value Lorenz truncates again. The
margin between 0.35 and Lorenz's worst ratio of 0.315 is **11 %**, and it is a human choice.

This was the intended weak point of the paper and became one of its results. It must be reported as
a limit of the method, not smoothed over.

### Cap evidence to report

- **0 truncated equation rows of 80**, 48 finite caps, on all 20 exact systems and both IC sets.
- Verified per-system caps on the diagnostic grid: 3 → `[2]`, 11 → `[4]`, 26 → `[3,3]`, 31 → `[3,3]`,
  54 → `[nothing,2,2]`, 63 → all `nothing`.
- Counter-check: System 61 (Chen-Lee) caps correctly at `[3,3,3]` — the defect was selective, never
  general.
- Regression, 120 records under one identity triple (`git f6143eb`, `17fe7d9cfb8f1be3`,
  `ffb0266c7913352c`), 30 shared cells on systems 3, 11, 26, 31, 63:

  | | capped | v2.2 |
  |---|---|---|
  | loss | bit-identical in 30/30 cells | — |
  | `pruned_match` | unchanged in 30/30 | — |
  | loss evaluations | 12,002,255 | 16,087,320 |
  | difference | **−25.4 %** | — |
  | cells made more expensive | **0** | — |

- The strongest single cell: System 3 seed 7, where v2.2 burns **12 of 30 levels** on stage
  escalation and the capped run returns the bit-identical loss.
- The measured price of an abstention, before the band was removed: System 31 / IC 1 cost **+16 %**
  evaluations at a bit-identical loss — compute, never the solution. It is the empirical basis for
  the safety/economy framing and survives as evidence even though the band does not.

### Cap limitations to report, without minimization

1. `pruned_match = false` persists on coupled systems even at very low loss. The cause is the
   additive search operator, not the cap.
2. The cap is auditable **only on the 20 exact systems**. The 43 surrogates have no ground-truth
   support, so controller safety is unverifiable there by construction. The pilot shows several
   surrogates carrying an equation capped at stage 1 (systems 33, 34, 40, 44, 50); they are scored
   on R², so this is a fit-quality risk rather than a support error — but it must be stated.
3. The reopen threshold 0.35 is not data-selectable (above), and the floor-depth guard 0.1 is a
   verified margin.
4. **Aggregation robustness is open.** Rows flip through **split majority voting** rather than clear
   detection; at 12 / IC 1 a single split changed the outcome.
5. The behaviour fingerprint covers `_cap_split_decision` only. Derivative estimation, floor
   computation, split aggregation and the search loop remain unobserved by it.
6. System 63 is the identifiability boundary, not a capped comparison cell.
7. System 31 / IC 2 remains a low-dynamics boundary case: where the trajectory carries little
   dynamics, the cap is not stable across initial conditions.

---

## Phase 3 — ODEBench Protocol and Literature Alignment

No external baselines are run in this project. Published results may be used as reference context
only, unless protocol equivalence is established.

### Phase B Sampling Protocol — decided 2026-08-03 (frozen)

*Provenance, established 2026-08-22:* the grid below is the artefact's own. Our
`strogatz_extended.json` is byte-identical to the upstream file in `sdascoli/odeformer`
(`odeformer/odebench/`, upstream commit `32dd990`), unchanged since our first commit. Note that the
repository ships **two** samplings: 512 points in the committed JSON and 150 points from the
regeneration script, which writes to a file no evaluation path reads. The benchmark's own released
evaluation code reads the committed 512-point solutions, i.e. **the same grid as ours**; a
subsequent study took the 150-point script as the protocol instead. Which of the two a given
published run used must therefore be checked per source — the difference is 3.4x in density, on the
axis that governs whether derivative-space objectives mislead.
`docs/paper1_odebench_protocol_alignment.md` §2.4, §2.6, §2.7.

| Component | Decision |
|---|---|
| Systems | all 63 ODEBench systems |
| Time span | `t ∈ [0, 10]`, as shipped |
| Sampling | 512 uniform points, both endpoints included |
| Initial conditions | both sets per system |
| Trajectory source | self-integration with `Tsit5`, `abstol = reltol = 1e-9` |
| Noise | none |
| Cells | 63 × 2 conditions × 3 seeds × 2 IC sets = 756 |

The shipped trajectories are **not** adopted: their solver accuracy would impose MSE floors from
`2.5e-2` to `6.1e-10`, putting current EvoODE results out of reach. Grid density is what matters,
and at 512 points System 54's two safety violations disappear.

**Declared deviation:** if published numbers were computed on the shipped trajectories, EvoODE works
on cleaner data than the comparison does. This is a deviation in our favour and must be declared as
such until the publications are checked.

### Required Protocol Audit — two sources, decided 2026-08-22

`docs/paper1_odebench_protocol_alignment.md` records, per published reference source: systems used,
initial conditions, tspan, sampling grid, noise setting, metric definition, aggregation — each with
a match status of exact / partial / mismatch, plus the representation dimensions below.

Two sources are in scope for Paper 1, and only two:

1. **ODEFormer / ODEBench** — the benchmark source. Mandatory, because our systems, initial
   conditions and sampling grid come from there, and because it reports several method families on
   the same benchmark, which makes part of the representation audit fillable from one place.
2. **Tonda et al. 2025**, *When Data Transformations Mislead Symbolic Regression: Deceptive Search
   Spaces in System Identification* — **not** a performance reference but methodological evidence.
   It shows that turning a dynamical problem into an algebraic derivative problem can produce
   deceptive search landscapes, in which a good derivative-space objective does not preserve the
   ranking of dynamical models. This touches the warm start of §3.4 and the search-free reference of
   the representation analysis, both of which live in derivative space. Our own measurements
   reproduce the phenomenon independently: 13 of 126 full-basis reference fits diverge on
   integration despite near-perfect derivative fits.

**Representational adequacy is audited in three dimensions**, not one:

| Dimension | Question | For external methods |
|---|---|---|
| in principle representable | can the model class express the truth at all? | yes / no / unclear |
| representable under the evaluated protocol | was it reachable given the operators, library and complexity limits actually used? | yes / no / unclear / not reported |
| best attainable functional fit | how well can that space fit the dynamics irrespective of search error? | **optional**, where available |

The third is available for EvoODE and will be unavailable for most published runs. It must stay
optional: an audit may not impose a requirement only the authors' own method can meet. *Not
reported* is a finding, not a gap.

**The external columns are unfilled at the time of writing.**

### System Classification

All 63 systems split into **20 exact** systems (exactly representable in the current staged basis)
and **43 surrogate** systems (not representable). For exact systems record expected stage, true
support, dimensionality and term types; for surrogates record the basis-gap reason.
`expected_stage` is derived, not hand-maintained (WP-M1).

### Core Metrics

**Exact systems:** raw and pruned support equality, reached stage, stage overshoot, wasted levels,
stability observations.

**Surrogate systems:** R², loss, reached stage, stability observations.

Exact and surrogate systems are **never** mixed into one structure-correctness metric
(Design Principle 8).

**Cost and efficiency:** `total_parameter_fits`, `total_loss_evals`, `total_ode_solves`, levels,
stages. `elapsed_s` is context only.

### Valid-Run Rule

A run is valid if `status = finished`, `loss` is finite and non-NaN, and a predicted trajectory
exists. Poor results remain valid. Invalid are only NaN loss, missing prediction, timeout, crash or
failed run.

### Failure and Logging Policy

Orion imposes **no walltime limit**, so run-level timeouts are not part of the Phase B design and no
checkpointing is required. The only deterministic brake is the per-fit evaluation budget
`max_loss_evals = 20,000`, which is a count and therefore node-speed independent. A budget stop is
distinguishable from a failed solve in the metadata since WP-D2, but both still collapse to the
sentinel loss `1e6` in the loss itself — to be stated as a robustness limitation.

Every cell writes its record plus a heartbeat log with one event per level. Failed cells carry
`error != null`, count toward the cell total, do not count toward the valid total, are included in
robustness analysis, and are never silently deleted or silently re-run.

---

## Phase 4 — Cluster, Schema and Cost Validation

No paper claims come from this phase.

The compute path is verified end to end on SCCH **"Orion"**, an OpenShift/Kubernetes cluster:
container built by GitLab CI, `k8s/` Indexed Jobs, results on NFS, Julia 1.12.6 pinned, one core and
2 GB per cell. Mechanics in `docs/hpc_deployment_guide.md`.

The cost model is measured, not estimated (`docs/hpc_requirements.md`): **2,000–3,400 core-hours**
for the 756 Phase B cells, roughly 9 days at the agreed `parallelism: 16`, with a makespan floor of
68 h set by the longest single cell.

One methodological result of this phase belongs in the paper's Methods section: **evaluation counts
do not convert into compute time.** On System 56 the loss evaluations fall 44 % while runtime falls
3 %; cost per evaluation varies by more than a factor of two within one dimension class. Counts
remain the correct evidence for **search effort** and are demonstrably unusable as a proxy for
**compute time**.

### Go criteria (met)

- validation cells finish, fail cleanly, or are cleanly abandoned
- schema validation passes; R² and support metrics computable
- logs, heartbeats and outputs complete and readable from outside the container
- all three identity fields recorded per record
- no aggregate metric pipeline produces unexplained NaNs

---

## Phase 5 — The Phase B Campaign

```text
63 systems × 2 pretuning conditions × 3 seeds × 2 IC sets = 756 cells
```

No GP baseline, no v1, no v2.1. Search depth stays at **30 levels** (see Phase 6).

### Provenance — three fields, not two

Every final record is identified by:

1. git commit hash
2. `config_fingerprint` (Phase B variant)
3. `stage_cap_behavior_fingerprint`

The third field exists because the config fingerprints hash configuration constants only: the WP-C3
and WP-C4 cap-logic changes left them standing, so two records could share a fingerprint and come
from differently deciding code. `stage_cap_behavior_fingerprint()` hashes the decisions a frozen
five-case probe draws out of `_cap_split_decision`.

| Field | Value | Records |
|---|---|---|
| Phase B fingerprint | `604e79733b22d64d` | 756, `git 91f88c4` clean — verified over every record at campaign end |
| Regression fingerprint | `17fe7d9cfb8f1be3` | 120, `git f6143eb` |
| Behaviour fingerprint | `ffb0266c7913352c` | as above |

A campaign with mixed identity is not publishable and must be re-run. This has already cost one
regression suite; the pilot and probe records predate the current identity by construction and must
never be merged into campaign data.

### Representational scope — a limitation to state, not to fix here

The staged basis represents **20 of the 63 systems exactly**. Four motif families would take that to
58, and the remaining five need one family each — the closure curve and the reasoning are in
`docs/diskussion_repraesentationsraum.md`. The expansion is deliberately **not** part of Paper 1: it
moves `config_fingerprint`, invalidates the regression block and reopens design rule 2, which derives
the look-ahead from where the basis creates structural gaps. It is scheduled as a bridge between
Paper 2 and Paper 3.

For Paper 1 this means two things. The limitation is reported with its numbers rather than
apologised for. And the claim "the space is not the cause of failed recovery" holds **for the 20
exact systems only** — on the other 43 the space *is* the cause, and no sentence may blur that.

### Result placeholders

**All result placeholders are filled as of 2026-09-07** (WP-A5 to WP-A9). Fit quality, support
recovery, surrogate R², stage-cap economy, the `pretune_on` / `pretune_off` contrast, robustness and
failure modes, the level-waste measure and the per-system table are produced by scripts under
`analysis/scripts/` into `analysis/tables/paper1_phaseB_v1/` and `analysis/data/paper1_phaseB_v1/`.

Three results constrain how they may be written up:

1. **The pretuning contrast is not a comparative result.** Its structural difference (60/120 against
   50/120) dies under clustering — cluster-robust p = 0.218 against a naive McNemar p = 0.021, on
   120 pairs from only 20 systems. What the campaign supports instead is mechanistic: pretuning
   collapses seed diversity, on the **discovered support pattern** as well as on the numbers
   (96/126 groups against 61/126, all 35 discordant pairs one-sided, cluster p = 1e-5).
1b. **The seed-collapse finding is an ablation, not a mechanism (retracted 2026-09-07).** Without
   pretuning the parameter start is random (`bfgs.jl:269`); with pretuning it is deterministic. The
   higher repeat rate under pretuning largely follows from removing one of two random sources.
   Report it as an ablation with the system-8 example, not as a carrying result.
2. **Effect sizes are distributions, never a median.** The R² median paired difference is -8.2e-13
   and means nothing; the threshold grid shows the asymmetry sits in the small differences and
   vanishes toward the large ones. Report grids in full; never select a threshold after seeing the
   data.
3. **Two instrumentation facts must be stated.** `total_diverged_solves` and
   `total_solver_unstable_solves` are identical in all 756 cells — one quantity counted twice, not
   two independent robustness measures. And the optimizer retcode carries no quality signal in
   either direction: 18 cells reach losses to 1.9e-12 at R² ≈ 0.9999 with no `Success` retcode at
   all, alongside the long-known sentinel loss `1e6` at retcode `Success`.

---

## Phase 6 — Analysis and Paper

### Primary Analyses

**All systems:** R², simulation loss, valid-run rate, failure and solver-failure counts, reached
stages, stability observations.

**Exact systems:** `exact_support_match_raw`, `exact_support_match_pruned`, per-equation required
stage, per-equation cap, final stage, stage overshoot, wasted levels, cap correctness where true
support exists.

**Surrogate systems:** R² and loss, approximation behaviour, final stage, basis-mismatch effects,
stability and failure modes.

**Search economy:** the counters, never wall-clock. Timing may be reported for capacity planning
only, measured on dedicated hardware and labelled as such.

### Wasted search levels — a result, not a fix

Measured over 287 cells and 599.6 h of recorded runtime (WP-B1, `docs/WP-B1.md`):

| Dimension | Levels per cell | Silent levels | Share of runtime |
|---|---|---|---|
| 1 | 10.8 | 2.3 | 10 % |
| 2 | 17.9 | 7.1 | **50 %** |
| 3 | 25.3 | 8.6 | 44 % |
| 4 | 19.8 | 18.5 | **96 %** |

A global "stop after k silent levels" was evaluated and **rejected at every threshold**: k = 3 saves
94 % of the runtime and costs 152 of 287 cells a materially worse result (138 of them by more than
50 %); k = 5 saves 37 % against 23 damaged cells; k = 8 saves 15 % for one. A tempting counter-
hypothesis — that the missed improvements are sub-per-mille noise — was tested against the raw data
and refused.

The decision (2026-08-21) is therefore to run at 30 levels and **report the waste as a result**.
Introducing a constant that does not follow from the data would repeat the WP-C4 mistake that WP-V1
uncovered. A structured stopping criterion is an open research question of this project, not a
configuration constant, and it belongs to the next paper.

### Method Positioning — integration versus differentiation, stated honestly

The project's founding motivation was that candidate models are judged by integrated trajectories
rather than by pointwise derivative estimates, so that noisy differentiation never enters the
evaluation. That framing is no longer accurate as a blanket statement and must not be written that
way.

Evaluation is trajectory-based: the loss is MSE between the integrated candidate trajectory and the
data (`src/loss/mse.jl`), and the selection objective is `loss + lambda * n_params`
(`src/structure/evogrow.jl`). No derivative estimate reaches the loss.

But the Paper 1 contribution itself is derivative-based. The look-ahead stage cap estimates
derivatives before the search starts — central differences or a local polynomial fit
(`_cap_estimate_derivatives`, `src/structure/stage_cap.jl`) — and decides the per-equation stage
boundary from residuals in derivative space. The OLS warm start (`src/optimize/pretune.jl`) uses
finite differences as well, and WP-R1's reference fit is a derivative-space argument.

The correct statement therefore separates two roles:

- **evaluation** is trajectory-based, with no derivative estimate in the objective;
- **structural pre-analysis** is derivative-based, and its estimate never has to carry the model
  quality, only the boundary of the search space.

This is a stronger position than the original one, because the project has measured what happens
when a derivative estimate is let into the evaluation loop: WP-L2 showed v3's promotion signal
`r_k` to be derivative-error contaminated, with its absorption capacity growing in term count, and
Gate 2 rejected v3. The separation of roles is thus an empirical finding of the failure analysis,
not a design preference.

Where this must appear: Method (section 3, when the cap is introduced), Failure Analysis
(section 4, as the v3 lesson), and Limitations (section 8 — cap quality is bounded by derivative
estimate quality, which is the documented mechanism behind the System 63 and low-dynamics IC
cases).

### Published Reference Context

**Superseded 2026-09-09.** This section forbade in-house SINDy comparison until the external protocol
audit was filled. Claim D replaces that with a stronger arrangement: SINDy is computed **in-house on
identical trajectories**, so comparability is established by construction rather than by auditing
someone else's protocol. The external audit columns remain open Phase 3 work and still govern how
*published* third-party numbers may be cited — and the published per-method ODEBench figures are bar
charts in Figures 4 and 5 of the ODEFormer paper with no result files shipped, so they are not in our
hands regardless.

### Planned Paper Structure (revised 2026-09-09 — method paper)

1. **Introduction** — the combinatorial structure space of equation discovery; fixed libraries and
   global search versus incremental growth. Contributions: EvoGrow, stage-wise expansion, the
   trajectory-informed stage cap, the ODEBench evaluation, the SINDy comparison, the ablations.
2. **Related Work** — SINDy, PySR/GP, ODEFormer, ProGED, staged search, search-space control
3. **Method: EvoGrow** — *the strongest section of the paper.* Problem formulation, structure
   representation, stage hierarchy, initialization, parameter optimization over integrated
   trajectories, structure expansion, selection, pruning, the stage cap, termination. With
   pseudocode, a process diagram, a worked example system, and a figure of the growing search space.
   The design justification includes the `v2.2 → v3 → capped` chain — as *why the method looks like
   this*, not as the paper's argument.
4. **Experimental Setup** — the fully frozen Phase C protocol
5. **Main Benchmark** — how EvoGrow performs; the EvoGrow-versus-SINDy table with cost, broken down
   by dimension, coupling and representability
6. **Stage-Cap Ablation** — capped versus uncapped; does progressive search-space control reduce
   unnecessary search?
7. **Generalization** — train on one IC, evaluate on another; both directions, never averaged
8. **Failure Modes and Limitations** — dim-3/4 structural collapse, add-only path dependence,
   wrong-term persistence, silent levels, optimization failures, identifiability, the non-selectable
   cap threshold, surrogate unauditability
9. **Discussion** — EvoGrow works as a concept; it is currently expensive; stage-wise search is
   sound but needs validation; add-only growth creates path dependence; generalization is harder than
   reconstruction; v1 is a starting point, not an end state
10. **Conclusion**

The ordering is deliberate and is the point of the revision: **method → evaluation → ablation →
generalization → limits.** Not: limits → and a method reverse-engineered from them.

### Allowed Claim Types (revised 2026-09-09)

Main-table claims come only from **Phase C** records. Phase B may support diagnostics, ablations and
failure-mode description, always labelled as a differently configured predecessor.

- **structural discovery** — exact recovery, term precision, term recall, structural F1 and
  coefficient error, always reported together with the three-way representability class
- **fit quality** — reconstruction R² and loss under the frozen protocol
- **generalization** — the same discovered model, unchanged, on an unseen initial condition of the
  same system; both directions reported separately
- **search-space control** — capped versus uncapped at identical settings; savings in counts, quality
  difference paired. Never "without loss of quality" unless the paired data show exactly that
- **baseline positioning** — where EvoGrow stands relative to SINDy on quality *and* cost, with all
  SINDy configurations reported. Never "better than" as an unqualified statement
- **diagnostic** — search failure versus optimization failure, separated by the oracle arm
- **robustness** — EvoGrow completes on the reported number of cells
- **failure mode** — failures are dominated by the reported categories, exact and surrogate separated

No claim may be derived from Phase A results. No main-table claim may be derived from Phase B.
Design Principle 9 binds every one of them: **structure recovery and the R² > 0.9 rate are always
reported together, never one alone.**

---

## Future Work / Separate Paper Ideas

Outside Paper 1 scope, deliberately:

- a **structured stopping criterion** — the direct successor to the WP-B1 measurement
- remove/replace operators for the growth-only search; beam or forward-stepwise search inside a stage
- search power within a stage: population size, child generation, parsimony pressure
- population reset on promotion (currently a deliberate warm start with anchoring as accepted risk)
- pretuning / OLS warm start as its own ablation — **and inseparable from it:** the number of
  parameter restarts. WP-N4 (2026-09-09) measured that a single fit on the *true* structure fails in
  15 of 102 cells and that k = 3 restarts remove every failure. `pretune_off` supplies a random start
  per fit, `pretune_on` one deterministic start per structure, so the two arms differ in restart
  **count** as well as start quality. A restart-budget study — recovery and cost against k — is a
  candidate for its own paper; see `docs/phd_thesis_arc.md` §3
- noise robustness, irregular sampling, extrapolation to unseen initial conditions
- in-house SINDy / PySR / GP implementations
- line-search cost control and candidate-level optimizer budgets
- canonical equality and hashing for `StructureSpec` as a precondition for deduplication — note that
  under `pretuning=false` duplicates act as implicit multistarts, so a cache would change the
  experimental condition rather than merely accelerate it
- adaptive basis redesign; alternative pruning and sparsification strategies
- **scored, error-guided term selection** — expansion is currently uniform random over allowed
  terms and equations (`_expand`, `src/structure/evogrow.jl`), with the usage policy the only
  non-uniformity; a candidate score over predicted improvement and term cost belongs to the
  within-stage search power question and is the mechanism the persistent `pruned_match = false`
  on coupled systems points at
- equation-wise v3 extensions beyond the rejected residual-promotion rule

---

## Implementation Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Growth-only search prevents structural recovery | High | report as limitation; defer remove/replace to future work |
| Cap safety is unauditable on surrogate systems | High | separate exact and surrogate metrics; claim no support safety on surrogates |
| The reopen threshold is a human choice | High | report the LOSO result and the 11 % margin as a finding, not a footnote |
| Split aggregation flips rows by majority vote | Medium | report as open robustness question with the 12 / IC 1 example |
| Behaviour fingerprint is too narrow | Medium | state that it covers `_cap_split_decision` only |
| Phase B records do not share provenance | High | require all three identity fields; verify before publishing |
| Wall-clock is overinterpreted | Medium | counters for cost claims; timing labelled as capacity planning |
| Analysis pipeline is Phase-A shaped | Closed | fixed by WP-A4 / WP-A4b (2026-08-21): classification-driven system axis, R² carried through, IC set as a grouping key, loud failure on an empty selection; Phase A byte-identical |
| Cost projection blind spots | Low | systems 1–23 rest on one measured system, 63 on none; a mis-projected class costs calendar days, not results |

---

## Scientific Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Structural recovery is low on exact coupled systems | High | report as a Failure Modes result of EvoGrow v1 with its mechanism (add-only path dependence), not as the paper's thesis |
| The cap saves search space but not solutions | High | Claim B is stated as *reduces search while preserving most quality*; the paired capped/uncapped data decide the wording, not the draft |
| Surrogate performance is poor or unstable | Medium | report via R², loss, reached stage and stability only |
| System 63 is misread as a failure cell | Medium | present it as the identifiability boundary |
| The waste finding invites "why no stopping rule?" | Medium | answer with the WP-B1 table: every threshold was measured and every one was a bad trade |
| **The compute gap to SINDy dominates the reception** | **High** | state it first and plainly, with counts; position EvoGrow on algorithmic properties and generalization, and name the harder regimes as the follow-up question rather than claiming them |
| **Phase C exceeds its cost envelope** | **High** | the uncapped mirror carries the majority; a smoke test and a pilot subset precede submission, and the cost model is re-derived before the full run |
| **Phase B and Phase C configurations differ** | **High** | never mix them in one table; label Phase B as a differently configured predecessor wherever it is cited |
| **New structural metrics are wrong on arrival** | **Medium** | F1/precision/recall are new code on the critical path; validate against the existing exact-support column, which must be reproducible from them |
| Reviewers ask why the constant term was added or omitted | Medium | report the measured two-sided trade-off and the probe evidence the decision rested on, with its date — never a post-hoc justification |

---

## Frozen Elements

**Phase A.** `paper1_phaseA_v1` run data unchanged; exploratory, no final claims.

**After Gate 1.** v2.2 failed; retained as substrate and as failure evidence.

**After Gate 2.** v3 failed; retained as failure analysis.

**After cap selection.** `evogrow_v2_2_stage_capped` is the final Paper 1 variant. The three design
rules, the two load-bearing constants and the known limitations are reported.

**After Phase 3.** Phase B sampling: 512 points over `t ∈ [0, 10]`, both IC sets, self-integrated
with `Tsit5` at `abstol = reltol = 1e-9`. Exact and surrogate systems evaluated separately.

**After WP-B1.** Search depth stays at 30 levels for the campaign; no level budget, no stopping rule.

**Once Phase 5 begins.** The campaign manifest is frozen. No system may be removed, and no setting
changed, without a new experiment identifier. Frozen result blocks are never overwritten.

**After the dim-2 basis probe (2026-09-13).** The canonical basis is
`staged_polynomial_basis_with_constant` — the staged polynomial basis **including the constant term
`1` in stage 1**. Every Phase C arm uses it. The trade-off is a reported result, not a footnote:
representability against searchability, with the constant reducing structure recovery on dim 2 and
improving generalization on dim 1. P3 is closed; the basis is no longer an open frozen parameter.

**Decided 2026-09-09, before the Phase C freeze.**

- **Paper scope** — method paper. EvoGrow is the object; the cap is a component with its own
  ablation; failure analysis is a Limitations section, not the thesis.
- **Canonical pretuning** — `pretuning = false`. Pretuning on/off is an ablation, never a second main
  version.
- **Restart policy** — retry-on-failure, up to k = 3, explicit and declared. The value comes from the
  WP-N4 oracle diagnostic, never from benchmark performance. It is named as retry-on-failure, not as
  a multistart.
- **Uncapped-arm scope** — full mirror of the canonical arm, 378 paired cells, all 63 systems, both
  IC sets.
- **Main-table provenance** — Phase C only. Phase B supplies diagnostics and ablations under an
  explicit predecessor label.

**Once Phase C begins.** The canonical configuration is frozen in full: basis, stage definitions,
stage cap, pruning, expansion, selection, optimization, restart policy, termination, seed handling,
integration, preprocessing. No hyperparameter is changed on the basis of observed benchmark results.
A necessary change produces a new, fully declared experiment identifier — never a version-drift
chain.

**Still open at the time of writing, and blocking the Phase C freeze.** The canonical basis: the
dim-2 constant-term probe decides it, and the probe's `git_hash` defect is repaired first.

**Deliberately excluded cells.** System 63 in capped comparison cells (cap is `nothing` everywhere);
System 54 in the regression suite (adding it changes `REGRESSION_SYSTEMS` and hence the fingerprint,
and its limit is already documented by WP-L3 and WP-G1).

---

## Open Items and Known Inconsistencies

1. **External protocol columns unfilled** in `docs/paper1_odebench_protocol_alignment.md` — the last
   substantive Phase 3 item.
2. **Analysis downstream is Phase-A shaped** — see the risk table.
3. `docs/wp_c1_stage_cap_horizon_audit.md` carries the internal title *WP-C2 Stage-Cap Horizon
   Audit*, and its truncation count (4 rows on systems 28 and 32 at horizon 2) is the audit's own
   horizon-2 view, while `CLAUDE.md` records the wider 9-row / 5-system figure from the full audit.
   Both are correct under their own scope; the paper must quote one scope explicitly.
4. `docs/paper1_odebench_protocol_alignment.md` is dated 2026-08-03 and still describes System 31 /
   IC 2 under the pre-WP-C5 cap logic. To be refreshed before it is cited.
5. **Unbudgeted call sites** — eleven scripts under `benchmarks/` and `studies/` construct the
   optimizer without a budget and are unbounded since WP-B3. Deliberate backlog, outside the
   campaign path.

---

## Document Maintenance

Updated at phase transitions:

- record gate decisions and the evidence behind them
- record cap-rule changes and their fingerprint consequences
- update protocol-audit status
- result placeholders filled 2026-09-07 from the final campaign records; regenerate via the scripts, never by hand
- add final claim decisions after the Phase B analysis

Last revision: 2026-09-09 (evening). Current phase: **Phase C, defined and not started.**

The four foundational gaps that outranked the write-up on 2026-09-07 are all measured:

| Gap | State |
|---|---|
| missing constant term in the basis | measured on dim 1, **decided by the pending dim-2 probe**. WP-N1/N5: it halves structure recovery and improves generalization — which basis is right depends on which metric counts |
| unpersisted coefficients | **closed** (WP-N1), not retroactive for the 756 campaign cells |
| no held-out evaluation | **closed** (WP-N5) |
| no baseline ever run | **closed** (WP-N6) |

**The scope question is answered.** The three candidate framings that stood here on 2026-09-07 —
the cap as controller, the campaign as characterisation, the restart budget as its own thesis — were
all shapes fitted to the data that happened to exist. The decision of 2026-09-09 rejects that whole
move: *we do not fit Paper 1 to the existing campaign; we define the paper and then compute exactly
the experiments it needs.* All three survive inside the method paper — the cap as Claim B's ablation,
the failure analysis as the Limitations section, the restart dependence as a subset ablation with a
cost axis — but none of them is the thesis. The thesis is EvoGrow.

The reading target for the finished paper:

> I know what EvoGrow is. I understand why the search space grows in stages. I understand the stage
> cap. I know how EvoGrow performs on ODEBench. I know how it compares to SINDy. I know how well the
> models generalize to unseen trajectories. I know what it costs. I know its current limits. And I
> can see which methodological questions come next.

**Next actions, in order.** Repair the probe's `git_hash`; run the dim-2 constant-term probe; decide
and freeze the canonical basis; build structural F1 / precision / recall / coefficient error and the
three-way representability class; implement and declare the retry-on-failure policy; measure the
`StructureSpec` duplicate rate; complete the Phase C matrix in
`docs/paper1_phaseC_benchmark_plan.md`; smoke-test; **then** freeze and submit the campaign.

See `docs/paper1_phaseC_benchmark_plan.md`, `CLAUDE.md` Active 0, and the `DIARY.md` entries of
2026-09-07 ("Kassasturz") and 2026-09-09.
