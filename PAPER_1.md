# PAPER_1.md — EvoODE Paper 1: Execution Roadmap and Working Plan

This document is the **authoritative execution plan** for EvoODE Paper 1. It defines the paper
scope, the diagnostic gates and their decisions, the work phases, go/no-go criteria, risks and
frozen elements.

*Revised 2026-08-21 and promoted from `docs/PAPER_1_draft.md`. The previous body was dated
2026-05-17, planned around EvoGrow v3 and did not mention the stage cap — the variant that is the
contribution. With this revision the precedence rule at the top of `CLAUDE.md` holds again: where
this document and `CLAUDE.md` drift, this document decides.*

| Where to look | For |
|---|---|
| `CLAUDE.md` | project orientation, architecture position, current priorities |
| `DIARY.md` | chronology — measurements, decisions, bug history, commit hashes |
| `docs/architecture.md` | component reference |
| `docs/paper1_odebench_protocol_alignment.md` | Phase B sampling protocol and the comparability audit |
| `docs/hpc_requirements.md` | measured Phase B cost model and resource profile |
| `docs/paper1_freeze_memo_phaseA.md` | frozen Phase A results (historical, no paper claims) |
| `docs/wp_c1_stage_cap_horizon_audit.md`, `docs/wp_c2_stage_cap_failure_diagnosis.md`, `docs/WP-V1.md`, `docs/WP-C5.md` | the stage-cap evidence chain |
| `docs/WP-B1.md` | the wasted-search-level measurement |

---

## Critical Scope Decision (2026-08-03)

Paper 1 is not a pretuning study and is not planned around EvoGrow v3.

The core contribution of Paper 1 is the **look-ahead stage cap** as a data-driven, per-equation
search-space controller on the `evogrow_v2_2_stage_capped` substrate:

```text
v2.2 substrate + per-equation look-ahead stage cap derived from trajectory and basis
```

The cap is computed **before** the search starts. It reads the trajectory and the basis, never the
evolving population, so it is search-independent and combines with the v2.2 substrate rather than
requiring the rejected v3 substrate.

The guiding research question:

> Can a data-derived, per-equation stage cap control the ODE hypothesis space before search, and
> where does that control help, fail, or become unauditable?

The central story is the documented failure-analysis chain:

```text
v2.2 -> v3 -> capped
```

v3 is a result, not the contribution. It failed Gate 2 because its promotion condition
`r_k > loss_tol = 1e-8` is unreachable on coupled systems with an error floor around `1e-3`, and
because `r_k` is contaminated by derivative-estimation error. The cap is the resulting controller:
it bounds how far each equation may grow, where the data give **positive** evidence about the
useful stage boundary.

---

## Explicit Non-Goals for Paper 1

Paper 1 does **not** run new in-house baselines for GP, PySR, SINDy, ODEFormer, GODE, Operon or any
other external symbolic-regression tool.

Paper 1 makes **no quantitative cross-method performance claim** (decided 2026-08-22). Not a
cautious one, not an approximate one — none. Permitted are statements about *protocols*: that
ODEBench has been used by several methods, that their search spaces and evaluation protocols differ,
that published numbers are therefore not treated as directly comparable, and that the broad
comparison is deliberately deferred. Not permitted: "better than", "competitive with", "comparable
performance to", "exceeds published results".

The reason is scope, not modesty. Paper 1 asks whether controlled, data-adaptive growth of the
search space pays off — an internal methodical question. A cross-method comparison opens a second
question and a second attack surface without adding anything to the first.

Paper 1 does **not** use pretuning as the scientific contribution. Phase B carries `pretune_on` and
`pretune_off` as its two conditions; any effect is a condition effect around the same controller.

Paper 1 does **not** claim structural recovery on surrogate systems. The 43 surrogate systems have
no true support in the current basis and are evaluated through R², reached stage and stability
observations.

Paper 1 does **not** derive claims from Phase A exploratory results, and does **not** report Phase B
results before campaign records exist. Result sections below are explicit placeholders.

Paper 1 does **not** introduce a stopping rule or level budget. That decision was taken on the
evidence and is recorded in Phase 6.

---

## Pretuning Decision

Pretuning is retained as an experimental condition because the frozen Phase B scope contains exactly
two conditions, `pretune_on` and `pretune_off`, over all 63 systems, 3 seeds and both
initial-condition sets. It is a condition, never the headline mechanism.

One measured caveat belongs to this decision (probe, 2026-08-20): the effect of pretuning on cost is
strongly system-dependent and points in different directions within a single dimension class —
runtime factors 0.30, 0.92 and 0.97 on three chaotic 3D systems. Any pretuning statement in the
paper must be per-system or per-class, never a single global factor.

---

## Current Status (as of 2026-08-22)

| Item | Status |
|------|--------|
| `paper1_phaseA_v1` | frozen exploratory set, 300/300 runs. Not used for final claims |
| Gate 1 | decided 2026-05-30: v2.2 fails |
| Gate 2 | decided 2026-07-31: v3 fails |
| Final variant | `evogrow_v2_2_stage_capped`, settled 2026-08-03 |
| Stage-cap defect | **solved** (WP-C1 to WP-C5, 2026-08-20): 0 truncated equation rows of 80, 48 finite caps |
| Regression evidence | **complete** (2026-08-20): 120 records, 30 cells, loss bit-identical 30/30, −25.4 % loss evaluations, no cell more expensive |
| Cost model | **measured** (pilot + probe): 2,000–3,400 core-hours for Phase B, `docs/hpc_requirements.md` |
| Level budget | **decided against** (WP-B1, 2026-08-21): 30 levels stay, the waste is reported as a result |
| Phase B protocol | decided 2026-08-03: 63 systems, 2 conditions, 3 seeds, 2 IC sets = 756 cells |
| Sampling | 512 points over `t ∈ [0, 10]`, both endpoints, self-integrated with `Tsit5` at `abstol = reltol = 1e-9` |
| Phase B fingerprint | `604e79733b22d64d` — **campaign running since 2026-08-22**, `git 91f88c4` |
| Regression fingerprint | `17fe7d9cfb8f1be3` — 120 records under `git f6143eb` |
| Stage-cap behaviour fingerprint | `ffb0266c7913352c` (probe version 2) |
| Campaign status | **running** since 2026-08-22, 756 cells at `parallelism: 16`, cost-descending start order (WP-H7). Expect ~9 days, floor 68 h |

---

## Paper Strategy in One Sentence

> Paper 1 evaluates a data-driven per-equation stage cap as a search-space controller for
> incremental ODE discovery, reports the v2.2 and v3 failures that led to it, and keeps structural
> recovery, surrogate fit quality and compute cost as separate kinds of evidence.

---

## Main Claim Strategy

The primary claim target is **Claim C**.

### Claim A — Fit-Quality Claim

> EvoODE achieves the reported Phase B fit-quality outcomes on the 63-system ODEBench protocol.

Fillable only from campaign records. **Placeholder: no Phase B records exist.**

### Claim B — Search-Space-Control Claim

> The stage cap restricts staged growth wherever the data resolve the stage boundary, at an
> unchanged result: on the 30-cell regression grid it removes **25.4 %** of the loss evaluations
> with **bit-identical** losses in 30 of 30 cells, unchanged `pruned_match`, and not one cell made
> more expensive.

Supported by stage metrics, cap decisions, support availability on exact systems and evaluation
counters. **Wall-clock time is not evidence for this claim** (Design Principle 7).

### Claim C — Primary Mechanistic Claim

> The v2.2 → v3 → capped sequence shows that staged growth needs not only a progression rule but a
> data-derived boundary on the useful search space. The cap supplies that boundary exactly where the
> derivative estimate resolves the structural difference between stages — and the threshold that
> separates the safe from the unsafe region **cannot be selected from the data**.

This is the safest framing because it carries the negative results as part of the mechanism. The
second half of the claim is itself a result (WP-V1) and is not to be softened.

---

## Phase Overview

| Phase | Goal | Status |
|-------|------|--------|
| **Phase 0** | archive and correct Phase A diagnostics | done |
| **Phase 1** | repair structural metrics, re-diagnose v2.2 | done |
| **Gate 1** | is v2.2 paper-ready? | decided 2026-05-30 — no |
| **Phase 2** | EvoGrow v3 design and validation | done |
| **Gate 2** | is v3 paper-ready? | decided 2026-07-31 — no |
| **Phase 2b** | stage-cap design, audits, failure diagnosis | **closed 2026-08-20** |
| **Phase 3** | ODEBench protocol and literature alignment | protocol done; external audit columns open |
| **Phase 4** | cluster, schema and cost validation | done |
| **Phase 5** | full ODEBench Phase B campaign | **running** since 2026-08-22 |
| **Phase 6** | analysis and paper | not started |

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
| Phase B fingerprint | `604e79733b22d64d` | campaign running, `git 91f88c4` |
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

The following remain placeholders until campaign records exist: fit quality over all 63 systems;
support recovery on the 20 exact systems; R² on the 43 surrogates; stage-cap economy counters;
`pretune_on` vs `pretune_off`; robustness, failures and stability.

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

### Published Reference Context

External numbers are cited as published context only until the protocol audit establishes
comparability. No SINDy or PySR comparison claims while the external columns are unfilled.

### Planned Paper Structure

1. Introduction — interpretable ODE discovery and the need for controlled structure search
2. Related Work — SINDy, PySR/GP, ODEFormer, staged search, search-space control
3. Method — EvoGrow staged basis expansion and the look-ahead stage cap
4. Failure Analysis — v2.2, v3, and the three cap design rules
5. Experimental Protocol — ODEBench Phase B, exact/surrogate split, sampling, provenance
6. Results — placeholder until campaign records exist
7. Analysis — where the cap controls complexity, where search still fails, and why
8. Limitations and Future Work — additive search, surrogate unauditability, the non-selectable
   threshold, baselines, noise, within-stage search power
9. Conclusion

### Allowed Claim Types

Claims are made only from final campaign records, and only in these shapes:

- **fit quality** — the reported R² or loss outcomes under the frozen protocol
- **structural recovery** — effective support on the reported subset of exact systems, under the
  frozen pruning rule
- **search-space control** — the cap limits staged growth according to the frozen decision rule, at
  the reported evaluation cost
- **mechanistic** — the v2.2 → v3 → capped sequence exposes why staged growth needs a data-derived
  boundary, and why the boundary's threshold is not data-selectable
- **robustness** — EvoODE completes on the reported number of cells
- **failure mode** — failures are dominated by the reported categories, exact and surrogate
  separated

No claim may be derived from Phase A results.

---

## Future Work / Separate Paper Ideas

Outside Paper 1 scope, deliberately:

- a **structured stopping criterion** — the direct successor to the WP-B1 measurement
- remove/replace operators for the growth-only search; beam or forward-stepwise search inside a stage
- search power within a stage: population size, child generation, parsimony pressure
- population reset on promotion (currently a deliberate warm start with anchoring as accepted risk)
- pretuning / OLS warm start as its own ablation
- noise robustness, irregular sampling, extrapolation to unseen initial conditions
- in-house SINDy / PySR / GP implementations
- line-search cost control and candidate-level optimizer budgets
- canonical equality and hashing for `StructureSpec` as a precondition for deduplication — note that
  under `pretuning=false` duplicates act as implicit multistarts, so a cache would change the
  experimental condition rather than merely accelerate it
- adaptive basis redesign; alternative pruning and sparsification strategies
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
| Structural recovery is low on exact coupled systems | High | frame the paper as a mechanistic search-space-control study; report the additive-search cause |
| The cap saves search space but not solutions | High | state the contribution as a controller, not a recovery fix; the 25.4 %/bit-identical result is exactly this shape |
| Surrogate performance is poor or unstable | Medium | report via R², loss, reached stage and stability only |
| Reviewers expect in-house baselines | Medium | state the non-goal and the protocol-audit status plainly |
| System 63 is misread as a failure cell | Medium | present it as the identifiability boundary |
| The waste finding invites "why no stopping rule?" | Medium | answer with the WP-B1 table: every threshold was measured and every one was a bad trade |

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
- fill result placeholders **only** from final Phase B campaign records
- add final claim decisions after the Phase B analysis

Last revision: 2026-08-21. Current phase: Phase B prepared, no campaign records.
