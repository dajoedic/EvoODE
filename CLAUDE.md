# CLAUDE.md — EvoODE

This file is the orientation document: what the project is, where it stands, what is decided, and
what to work on next. It is deliberately kept short. Detail lives in dedicated documents:

| Document | Holds |
|---|---|
| `DIARY.md` | chronology — design decisions, measurements, bug history, commit hashes |
| `docs/architecture.md` | component reference — types, pipeline, search algorithms, bases, optimizers, experiment infrastructure |
| `SCRIPTS.md` | runbook — exact commands for every script |
| `PAPER_1.md` | authoritative Paper 1 execution plan; takes precedence over this file if the two drift |
| `docs/paper1_phaseC_benchmark_plan.md` | **the Phase C claim → experiment → metric → output matrix, freeze list and blocking prerequisites** |
| `docs/status_2026-09-09.md` | frozen status snapshot, written before the scope decision |
| `docs/paper1_study_protocol.md` | frozen Phase A protocol — claims, hypotheses, evidence rules (historical) |
| `docs/paper1_phaseA_reproducibility.md` | frozen Phase A configuration — systems, hyperparameters, seeds, metrics (historical) |
| `docs/paper1_odebench_protocol_alignment.md` | Phase B sampling protocol and the comparability audit |
| `docs/hpc_requirements.md` | Phase B resource profile, cost derivation and its uncertainty |
| `docs/hpc_deployment_guide.md` | how code reaches the Orion cluster — CI, image, manifests, glossary, failure modes (German, for newcomers) |
| `docs/phd_thesis_arc.md` | draft: the three-paper thesis arc that `PAPER_1.md` hangs under |
| `docs/WP-N4.md` | the restart budget of the parameter fit, and its placement against SINDy/PySR/ODEFormer/ProGED |
| `docs/WP-N6.md` | the first baseline: EvoODE against SINDy on identical trajectories, with the cost line and the caveats |
| `READ_THIS_FIRST.md` | **volatile session handover** — what is running, what is uncommitted, what decision is pending. Overwritten wholesale, never appended; nothing durable belongs there |
| `codex/CURRENT_TASK.md` | the one active task spec for an AI coding assistant |

Do not start a second planning document. Planning and status belong here; everything else belongs
in one of the files above.

## Collaboration

All communication with the user happens in **German**.
Code, comments, docstrings, and commit messages remain in **English**.

## What This Project Is

EvoODE is a Julia research framework for data-driven discovery of interpretable ODE systems from
time-series data. It supports scalar (1D) and coupled multi-dimensional systems, with a research
focus on coupled systems.

The core idea: instead of fitting a fixed library like SINDy or searching globally from large
random structures like GP, EvoODE starts small and grows model structure incrementally, only
increasing complexity when simpler structures are not sufficient.

```text
Data -> Structure -> Parameters -> Simulation -> Evaluation -> Iteration
```

Key principle: **structured, iterative growth instead of global search.**

This is a PhD research project. Scientific correctness, reproducibility and research clarity matter
more than speed or feature volume. Every architectural decision must be defensible as part of a
research contribution.

**PhD focus:** efficient and robust search strategies for interpretable discovery of coupled ODE
systems.

## Scientific Position

| Method | Search space | Growth strategy | Complexity control |
|--------|-------------|-----------------|-------------------|
| SINDy | restricted: fixed linear library | none (direct regression) | L1 sparsity |
| GP | unrestricted | global: starts large, random | parsimony pressure |
| EvoODE | unrestricted | incremental: starts minimal, grows | staged grammar + stopping criterion |

Core claims:

1. Starting small and growing incrementally can be more efficient than global search.
2. Grammar-staged complexity unlocking can reduce wasted computation.
3. The stopping and promotion criterion can serve as a principled complexity-control mechanism.

Open research questions: what the best stopping and promotion criterion is; how structure should
grow (term-wise, equation-wise, staged, coupling-aware, error-guided); how structure search and
parameter optimization should be coupled; how coupled systems should be handled specifically; how
discovered models should be evaluated; how performance scales with noise, sample size, coupling
strength and dimensionality.

## Repository Map

```text
src/        core/ structure/ basis/ loss/ optimize/ simulate/ plotting/ utils/
benchmarks/ exploratory, direct-execution scripts + strogatz_extended.json
experiments/ formal, manifest-based Paper 1 runs
studies/    direct-execution study scripts (debug, lookahead, regression, numerics, generalization, profiling)
analysis/   Python analysis pipeline (see analysis/CONVENTIONS.md)
test/       Julia tests, run per file — there is no runtests.jl and no [targets] in Project.toml
outputs/    gitignored; every script writes to its own subfolder
docs/       design notes, reports, protocols
paper/      Paper 1 manuscript sections, one file per section
codex/      CURRENT_TASK.md — the single active task spec, plus the work-package reports
containers/ Dockerfile for the campaign image, built by GitLab CI
k8s/        Kubernetes Job manifests for the Orion cluster (bootstrap + indexed cells)
```

**What is tracked and what is not.** Run registries, campaign histories and the derived tables the
documents cite by name are **in the repository** since 2026-09-09; only the per-run scratch
directories under `experiments/*/runs/` stay out, because they are reproducible from the registry
plus the image while the registry is not reproducible at all. The rule is not
"generated versus handwritten" — it is what a result can be checked against. `.gitignore` states it.

`benchmarks/` vs `experiments/` are distinct and must not be conflated: `benchmarks/` is
exploratory and qualitative with best-effort reproducibility; `experiments/` is formal and
paper-grade with atomic writes, per-run status tracking and a derived `run_registry.csv`.

The module structure is intentionally extensible. New structure searches, bases, losses and
optimizers are added through the relevant interface layer and registered in `src/EvoODE.jl`.
**Do not hardcode algorithm-specific logic into `discover()`.** Details in `docs/architecture.md`.

### codex/ convention

One single task file for all work: `codex/CURRENT_TASK.md`, always overwritten, never appended.
The second line of every task spec declares the language: `**Language: Python**` or
`**Language: Julia**`. Contains "Kein aktiver Task" when no work is pending.

**Where a report belongs.** `codex/reports/REPORT_WP_<id>.md` is the finishing report of a work package,
written once and not maintained afterwards — provenance, not documentation. `docs/WP-<id>.md` is a
report **promoted** because a decision rests on it and someone outside the work package needs to
read it; it is linked from this file or from `PAPER_1.md` and kept correct. A report never lives in
both places. Older files under `docs/wp_<id>_<description>.md` predate the rule and are not renamed,
because `DIARY.md` cites them by path.

**Two-file handshake, one writer each.** `codex/CURRENT_TASK.md` is written only by Claude and read
only by Codex; `codex/STATUS.md` is written only by Codex and read only by Claude. No file has two
writers, so the two sides cannot clobber each other. The standing operating instruction for Codex
lives in `codex/CODEX_PROTOCOL.md`; it does not change between tasks.

**Claude launches Codex (since 2026-08-21).** After writing a task spec, Claude starts the session
itself with `codex exec` from the repository root, backgrounded, pointing at
`codex/CURRENT_TASK.md`. There is no polling interval any more: a session begins with one work
package and ends with its `STATUS.md` entry. A spec that is merely written and left lying is not
handed over. Codex reports
`status: working | done | blocked` plus the WP identifier and the report path. `done` means the files are in the working tree
and **uncommitted** — Claude commits after checking. `blocked` means the acceptance criterion is
out of reach; Claude then stops rather than iterating on the science alone. The working tree is the
ground truth, `STATUS.md` only the fast signal: a poll checks both.

## Current Status

| Phase | Status |
|---|---|
| 1 — stable core | DONE (2026-04-20) |
| 2 — EvoGrow variants | **CLOSED 2026-08-03** |
| 3 — benchmarking | infrastructure done; Phase B protocol decided and implemented. Planned next axes: noise, sampling density, coupling strength, dimensionality |
| 4 — Paper 1 | **Scope decided 2026-09-09: method paper.** Phase B campaign complete and **demoted to diagnostics** (756/756, 5,248 core hours, analysis done WP-A5–A9). **Phase C — canonical evaluation — defined, not started**: `docs/paper1_phaseC_benchmark_plan.md` |
| 5 — advanced methods | not started |

### Phase 2 outcome

The variant chain and its verdicts, in order:

- **v1** flat growth, **v2.1** staged release, **v2.2** stage-local progression + usage policy — all
  implemented. v2.2 **fails Gate 1** (2026-05-30).
- **v3** per-equation staging with a derivative-residual promotion signal `r_k` — implemented,
  **fails Gate 2** (2026-07-31). Kept as documented failure analysis, not as the contribution.
- **`evogrow_v2_2_stage_capped`** — v2.2 substrate plus a per-equation **look-ahead stage cap**
  derived from the data before the search starts. **The final Paper 1 variant** (settled
  2026-08-03).
- **v4** coupling-aware — not started.

The cap reads only trajectory and basis, so it is search-independent; that is why it combines with
the v2.2 substrate rather than requiring v3.

Two design axes must be kept separate and must not be collapsed into one mechanism again:
**stage progression policy** (when a stage is kept, promoted or terminated) and **stage usage
policy** (how strongly newly unlocked terms are encouraged). On promotion the population is carried
over unchanged — a deliberate warm start; the accepted risk is anchoring, and the usage policy is
the counter-measure. A population reset on promotion is future work and **must not be implemented
in the current phase.**

## Active Studies (as of 2026-09-07)

| Artifact | Status | Note |
|----------|--------|------|
| `paper1_phaseB_v1` | **complete** (756/756) | Campaign records under `git 91f88c4` / `604e79733b22d64d` / `ffb0266c7913352c`, 0 errors, 756 unique identities. Analysis not yet run |
| `paper1_phaseA_v1` | **frozen** (300/300) | H1 partial, H2 supported, H3 partial, H4 vacuous. Not used for final claims. `docs/paper1_freeze_memo_phaseA.md` |
| `studies/lookahead/` | WP-L1–L5d, WP-G1/G1b done | Stage-firing look-ahead — **promoted from diagnostic to the paper's contribution** |
| `studies/regression/` | 120 records on Orion, recomputed 2026-08-20 | Capped vs v2.2 over 30 cells on systems 3, 11, 26, 31, 63 under `git f6143eb` / `17fe7d9cfb8f1be3` / `ffb0266c7913352c`: loss **bit-identical 30/30**, `pruned_match` unchanged, **−25.4 %** loss evaluations, **no cell more expensive** |
| `studies/numerics/` | done (WP-T2) | Overshoot on System 26 is algorithmic, not numerical; screening is performance-only |
| `studies/generalization/` | closed | Auxiliary only; insufficient cells for supplementary inclusion |
| `studies/profiling/` | data available | Methods / Discussion only; not evidence for H1–H4 |

## Current Priorities

State as of 2026-09-07. `DIARY.md` holds the measurements; this section keeps only what still
constrains a decision.

### Settled — do not re-open

**Why v3 failed.** The promotion condition `r_k > loss_tol = 1e-8` is unreachable on coupled
systems (error floor ~1e-3), so it cannot distinguish under-modelling from an irreducible floor.
WP-L2 additionally showed `r_k` is derivative-error contaminated, and its capacity to absorb that
error grows with term count — biasing the signal toward "more terms help". Downstream confirmation:
on System 31 seed 42 the v3 substrate alone loses ~6 orders against v2.2.

**The stage cap — design rules only; the parameter is *not* settled, see Active 0.** Safe wherever
the derivative estimate resolves the structure, unsafe exactly where it does not. Design rule from
the System 63 defect: **the cap must rest on positive evidence, never on the absence of evidence.**
Second design rule, from the 2026-08-14 defect: **the look-ahead must reach as far as the basis
creates structural gaps** — with a degree-staged basis and odd nonlinearities that gap is two
stages. Verified caps on the per-system grid: 3 → `[2]`, 11 → `[4]`, 26 → `[3,3]`, 31 → `[3,3]`,
54 → `[nothing,2,2]`, 63 → all `nothing`.

**The final variant, ten cells on four systems.** `eq_overshoot = 0` in all ten. Against v2.2:
eight bit-identical losses, one identical to 11 digits, one 50x worse — that one with *identical*
support, i.e. a lost parameter optimum, not an unreachable truth. `pruned_match` unchanged in all
ten. Strongest cell: System 3 seed 7, where v2.2 burns **12 of 30 levels** and the capped run
returns the bit-identical loss. Stage escalation on these systems is provably pure waste.

**Phase B sampling protocol** (`docs/paper1_odebench_protocol_alignment.md` §3): adopt the
dataset's sampling — 512 points over t ∈ [0,10], **both** initial-condition sets — but **integrate
the trajectories ourselves** at `abstol = reltol = 1e-9`. Grid density is what matters (System 54's
two safety violations disappear); the shipped trajectories would impose MSE floors of 2.5e-2 to
6.1e-10, putting current results out of reach.

**No level budget before the campaign (WP-B1, 2026-08-21).** Measured over 287 cells and 599.6 h
of recorded runtime, a global “stop after k silent levels” is a bad trade at every threshold:
k = 3 saves 94 % but costs 152 of 287 cells a better result, 138 of them by more than 50 %; k = 5
saves 37 % against 23 substantially damaged cells; k = 8 saves 15 %. A conjecture was tested and
refused: the missed improvements are **not** noise. Any k would also have been a second constant
that does not follow from the data — the WP-C4 mistake. The waste is real and unevenly distributed
(dim 1: 10 % of the time in silent levels, dim 2: 50 %, dim 3: 44 %, dim 4: 96 %), and a whole class
of pilot cells improves last at level 1 and then computes nineteen silent levels. That is an
argument for a **structured stopping criterion as its own research question**, not for a
configuration constant. The campaign therefore runs at 30 levels and reports the waste as a result.
`docs/WP-B1.md`.

**The stage cap defect, closed (WP-C1 to WP-C5, 2026-08-20).** The audit over all 20 exact systems,
both IC sets and horizons 2–5 put truncation at 9 equation rows on 5 systems at the shipped
`lookahead_horizon = 2`. Final state: **0 truncated rows of 80, 48 finite caps.** Two mechanisms
were responsible. The horizon: the basis stages by degree, not parity, so odd nonlinearities first
become approximable at stage 4/5; horizons 3, 4 and 5 are cap-identical on all 80 rows, and the
shipped value is **5 = the number of basis stages**, i.e. no horizon rather than a tuned constant.
The second mechanism was derivative-driven — analytic derivatives repair all five survivors, and a
5×5 threshold sweep over four orders of magnitude repairs none. What repairs them is the **reopen
branch**: a later stage dropping the residual to ≤ 0.35 reopens the walk, otherwise the walk caps.
All conditions are relative; no stage index, no system identity (WP-C3 was rejected for exactly
that). WP-C4's doubt band was removed again after WP-V1 measured it: 77 caps correct, 0 wrong,
**0 wrong caps prevented, 3 correct caps surrendered** — and the Lorenz repair it was credited with
comes from the reopen branch. Counter-check: System 61 caps correctly at `[3,3,3]`; the defect was
selective, never general. Two constants remain load-bearing and sit inside `config_fingerprint`:
`post_floor_significant_drop_ratio = 0.35` and `post_floor_min_floor_ratio = 0.1`. Aggregation
robustness stays open — rows flip through split majority voting, and at 12 / IC 1 a single split
changed the outcome. **Limitation to declare regardless:** the cap is auditable only on the 20 exact
systems; several surrogates carry an equation capped at stage 1 (33, 34, 40, 44, 50), a fit-quality
risk rather than a support error.

**Analysis downstream, closed (WP-A4/A4b, 2026-08-21).** The system axis comes from
`system_classification.csv` instead of hard-coded id lists, `r2` reaches the analysis at all for the
first time — it is the metric for 43 of 63 systems — the two IC sets are no longer averaged away,
and an empty selection aborts instead of reporting success. Phase A stays byte-identical. Still
carried but not aggregated: `r2_by_dim` and `stage_cap_behavior_fingerprint`.

**Cost and numerics, closed.** Screening is a performance optimization only, never a
discovery-quality lever. Overshoot on System 26 is tolerance-invariant, therefore algorithmic. On
the coupled search path 1e-6 is the cheaper, behaviour-equal tolerance; the System 11 loss of
4.402e-15 is numerical noise.

### Active

0. **Reset 2026-09-07: four foundational gaps outrank everything below.** Full reasoning in
   `DIARY.md`, entry "Kassasturz".

   **(a) The basis has no constant term.** `src/basis/staged_polynomial.jl` carries `u1`, `u1^2`,
   `u1*u2`, `u1^3`, `sin`, `cos` — no `1`. Representability: **EvoODE 20 of 63 systems, SINDy's
   plain polynomial library 40, ProGED's rational grammar 53.** Ten systems fail on the constant
   **alone** (1, 5, 9, 17, 23, 43, 52, 57, 58, 59), 15 more have it as a component — 25 of the 43
   non-representable systems. System 1 is the RC circuit. Recorded since 2026-08-24 in
   `analysis/data/paper1_phaseB_v1/representational_adequacy.csv` and never acted on. Our search
   space is half the nearest relative's default.

   **(b) The fitted coefficients are never stored.** `run_regression.jl:831` writes only term names
   via `active_term_names(...)`; `result.params` is dropped. No model from the 5,248 core hours can
   be rebuilt, re-simulated, or applied to other initial conditions. Violates Design Principle 6.

   **(c) Both IC sets were trained, never tested.** The protocol adopted both sets; why they are two
   separate training problems rather than train/test is nowhere justified — the question was never
   asked. ODEBench ships the second IC *to evaluate generalization*, which the audit itself quotes.
   **The project has no evaluation on held-out data at all**; every number, R² included, is
   in-sample on the final simulated trajectory.

   **(d) The literature metric is a thresholded rate, and we can compute only half of it.**
   ODEFormer (ICLR 2024) reports **the share of predictions with R² > 0.9**, reconstruction and
   generalization separately, and deliberately does not report mean R². Our reconstruction-side
   number from existing data: **80.7 %** over 756 cells (dim 1 96.7 %, dim 2 89.6 %, dim 3 25.8 %).
   The generalization side needs the coefficients. **The published per-method ODEBench numbers are
   not in our hands** — they are bar charts in Figures 4 and 5, and the repository ships no result
   files. Whether 80.7 % is good or bad is **open** and must not be asserted either way.

   **The step order was wrong.** v1 → v2.1 → v2.2 → Gate 1 → v3 → Gate 2 → cap → campaign, and at no
   point was it tested whether the base method is competitive. EvoGrow has only ever been measured
   against itself; no baseline run exists.

   **(1) is done, and the answer is two-sided (WP-N1, 2026-09-08).** `staged_polynomial_basis_with_constant`
   adds `"1"` to stage 1; the old basis is untouched and verified **bit-identical on 66 of 66 cells**
   against the campaign. The dim-1 probe over 132 cells says: on the six systems that never needed
   the constant, recovery **falls from 30/36 (83.3 %) to 14/36 (38.9 %)**; on the five systems that
   failed on the constant alone, it reaches **15/30 (50 %)** where no score existed before (system 1
   and 17 at 6/6). Cause: the constant is a false-positive magnet — it appears in 31 of 37 missed
   cells, unexpected in 22 of them. The newly stored coefficients separate two failure modes: on
   system 3 the spurious constant is ~1e-3 of the largest coefficient and survives the pruning rule
   `max(1e-6, 1e-3*max_abs)` by a factor of 1.27, i.e. the structure is effectively right; on system
   6 it is **4.2× larger** than everything else, i.e. a genuinely wrong model. **No threshold change
   is implied** — picking a threshold after seeing the data is the WP-V1 mistake. The constant
   therefore **cannot simply move into the default basis**; representability and searchability pull
   against each other, and that tension is the finding. Open: the comparison gives both bases the
   same level budget although the new one searches a larger space — an equal-effort comparison would
   be the fairer measurement.

   **Plan (1)–(5) is complete.** (1) constant-term basis, (2) coefficient persistence, (3)
   generalization, (4) SINDy baseline — all done, see below. **(5) is decided 2026-09-09: Paper 1 is
   a method paper**, and the uncapped arm is no longer deferred but is the second Phase C arm. See
   Active 0b.

   **(3) is done (WP-N5, 2026-09-09) and it reverses the constant-term verdict.** The model is
   rebuilt from the record and integrated from the *unseen* initial condition, parameters unchanged.
   Control: **132 of 132 reconstruction probes exact to zero**, so `model_terms` does its job.
   Result: R² > 0.9 falls from **95.5 % (reconstruction) to 68.2 % (generalization)** — 27 points,
   qualitatively the drop ODEFormer reports, and the first number in this project measured on
   held-out data. Direction matters (IC2 → IC1 is far worse in both bases). And the constant, which
   **halves** structure recovery (83.3 % → 38.9 %), **improves** generalization markedly (72.7 % →
   87.9 % and 45.5 % → 66.7 %), with all nine diverging integrations falling on the old basis and
   none on the new. "Should the constant be in the basis?" is therefore not a yes/no question but a
   question about which metric counts — a decision about the method's purpose, not its configuration.
   Design Principle 9 is what made this visible. **The campaign cannot be evaluated this way**: its
   756 cells carry no coefficients, so their generalization is reachable only through a re-run.

   **(4) is done (WP-N6, 2026-09-09): the first baseline in the project's history.** SINDy on
   **identical trajectories** (63 systems, both IC sets, self-integrated at 1e-9), ten configurations
   reported in full, none selected. Like-for-like on dimension 1, best SINDy configuration against
   EvoODE's WP-N5 numbers:

   | R² > 0.9 | SINDy | EvoODE |
   |---|---|---|
   | reconstruction | 44/46 = **95.7 %** | 126/132 = **95.5 %** |
   | generalization | 28/46 = **60.9 %** | 90/132 = **68.2 %** |

   **A draw on reconstruction, EvoODE ahead on generalization — at roughly two orders of magnitude
   more compute.** SINDy runs one linear regression per equation; EvoODE runs a median of 410
   nonlinear fits per cell, each with ODE integrations. For a method whose thesis is efficiency, that
   number belongs beside every recovery rate. Over all 63 systems SINDy reaches 68.3 %
   (reconstruction) and 47.6 % (generalization); our 80.7 % campaign figure is **not** a
   counterpart — different aggregation units, and our all-dimension generalization does not exist
   because the campaign cells carry no coefficients.

   **Caveats that travel with these numbers:** the system sets are not identical (our 132 dim-1 cells
   come from 11 selected systems × 3 seeds × 2 IC sets × 2 bases, SINDy's 46 from all 23 dim-1
   systems × 2 IC sets); SINDy's figure is the maximum over ten configurations, deliberately in its
   favour; SINDy needs derivatives (`FiniteDifference(order=2)`) and our noise-free data favour it,
   while the noisy case is unmeasured; and the trajectory check verified the grid against the
   *shipped* solutions rather than directly against ours.

   **The answer to "is 80.7 % good or embarrassing" is: neither.** On the easiest system class EvoODE
   is level with SINDy and somewhat better at generalization, for about a hundred times the compute.
   That shifts the burden of proof: the method must show its value somewhere else — under noise, on
   coupled systems, or in the interpretability of the search path.

   The campaign data is not discarded: 756 clean cells under one identity triple, protocol-conform,
   with a sharply named boundary. A good chapter, not a paper.

0b. **Scope decided 2026-09-09: Paper 1 is a method paper, and Phase C is the campaign it needs.**
   Authority: `PAPER_1.md` and `docs/paper1_phaseC_benchmark_plan.md`. The short form:

   **EvoGrow is the object, not the stage cap.** The cap is a component with its own ablation. The
   failure analysis — dim-3/4 collapse, add-only path dependence, silent levels — is a Limitations
   section, not the thesis. The three candidate framings recorded here on 2026-09-07 are all shapes
   fitted to whichever data happened to exist; that move is rejected. **We define the paper, then
   compute what it needs.** The 5,248 core hours are sunk cost and must not shape the scope.

   **Phase B is demoted** from main benchmark to diagnostics, ablation source, runtime analysis and
   failure-case collection. It was computed before the methodological audit closed and carries four
   defects a final benchmark cannot have (no constant term, no coefficients, both IC sets as
   training, no uncapped arm). **Phase B and Phase C numbers never appear in the same table.**

   **Four claims:** A — EvoGrow discovers structure (with three-way representability, F1, precision,
   recall, coefficient error); B — stage capping controls search effort (capped vs uncapped, **full
   mirror, 378 paired cells**); C — generalization to unseen trajectories, both directions; D — where
   EvoGrow stands against SINDy, quality **and** cost. Plus an oracle-structure arm that separates
   search failure from optimization failure.

   **Decisions taken 2026-09-09, all frozen before the campaign:** canonical `pretuning = false`;
   restart policy **retry-on-failure up to k = 3** — named as retry-on-failure, *not* a multistart,
   with k taken from the WP-N4 oracle diagnostic and never from benchmark performance; uncapped arm
   as a full mirror; main tables from Phase C only. Two prohibitions the project has already violated
   once: no pruning threshold chosen after seeing results, no library component removed because it
   produces false positives.

   **Cost: ~11,500–15,100 core hours, 5–7 weeks on Orion (revised 2026-09-13).** The figure is
   **derived from the Phase B registry rather than estimated**: the canonical capped arm is the
   measured cost of Phase B's `pretune_off` arm, 3,249.3 h over the same 378 cells, which supersedes
   the "~2,600 h" estimate. Added since: a 120-cell pretuning confirmation arm at 1,331 h. The
   uncapped mirror still carries the majority, because it runs the full 30 levels where the capped
   arm stops early. The experiment that must show the cap saves compute is the most expensive thing
   in the project — state that in the paper.

   **The 2026-09-13 raise comes from the basis freeze, and it is a carry-over, not a measurement.**
   The Phase B registry measures the **old** basis; the canonical arm is now the constant basis.
   Over all 335 probe cells the constant costs **+19.8 %** `total_loss_evals` and +3.2 %
   `total_parameter_fits`, so +20 % is applied to C-1, C-2 and C-3. Three cautions: core hours are
   not readable off loss-eval counts (Design Principle 7); the premium is measured on **dim 2 only**
   while dim 3 carried 75.6 % of Phase B's compute; and on the nine paired exact systems the premium
   is about +60 %, so the aggregate is not a bound. The risk is one-sided — the total can be
   exceeded, and the uncapped mirror is where it would show first.

   **The matrix is complete (P8, 2026-09-10).** Every claim names an arm, a script, an output path
   and a pass criterion, and all five questions the plan left open are decided: SINDy compares over
   all 63 systems paired and stratified with no cross-stratum headline; the restart ablation runs
   through the oracle path so that k is isolated from the implicit multistart; the oracle uses the
   canonical basis only; the pretuning ablation gets a 120-cell confirmation arm rather than a
   citation across a basis boundary; and a 12-cell pilot with a five-part go criterion precedes
   submission, distinct from the smoke test.

   **P3 is closed: the canonical basis is `staged_polynomial_basis_with_constant` (2026-09-13).**
   The dim-2 probe ran (335/336 at decision time, 0 errors, one identity triple) and WP-N15
   evaluated it. **The decision was taken against the probe's recovery numbers, not with them** —
   on the nine dim-2 systems exact under both bases the constant costs recovery (pruned 55.6 % →
   35.2 %, raw 13.0 % → 7.4 %) at an identical R² > 0.9 rate of 94.4 %. Representability decides it
   anyway: 20 of 63 systems against SINDy's 40 is not a defensible search space for a method paper.
   Declared limitation: the constant's benefit is measured on dim 1 (generalization, 72.7 % →
   87.9 %) and its cost on dim 2 — **no run measures both on the same dimension**, and the dim-2
   probe is not re-run.

   **Blocking before the freeze, in order:** ~~run the dim-2 constant-term probe~~ **done**; build
   the remaining Phase C work packages listed in
   `docs/paper1_phaseC_benchmark_plan.md` §2a — including the declaration of the restart parameter in
   the **Phase C** fingerprint, which is the half of P6 that is still open; pilot; smoke-test. Done
   since: `git_hash` repair (WP-N8), structural metrics and three-way representability (WP-N7/N7b),
   duplicate counter (WP-N10), matrix completion (P8), restart policy implemented with a
   behaviour-neutral default (WP-N11).

   **An ordering defect of the plan, declared rather than hidden:** the restart policy must be
   implemented before the campaign starts, but the campaign is what measures the duplicate rate its
   premise depends on. See §8 of the Phase C plan.

   **Superseded by this decision:** `PAPER_1.md`'s two non-goals of 2026-08-22 (no in-house SINDy
   baseline, no quantitative cross-method claim) are **lifted** — Claim D requires exactly what they
   forbade, under declared fairness conditions. The old Claim A/B/C labels are retired and preserved
   in `PAPER_1.md` under "Superseded Claim Labels"; `DIARY.md` and the WP reports cite the old set,
   so the two must never be mixed.

1. **The Phase B campaign is complete, and the analysis is the open work.** Ran 2026-08-22 to
   2026-09-04 on Orion under `git 91f88c46063fa368101326cbfe1abcdfc9d857fc`; the Job has since
   removed itself from `scch-das`. **756/756 records, no `error`, 756 unique identities, one
   identity triple over every record** (`91f88c4` clean / `604e79733b22d64d` / `ffb0266c7913352c`),
   378 `pretune_on` against 378 `pretune_off`. Records live on the NFS share under
   `phase_b_campaign_91f88c46.../tasks` and are readable without cluster access.

   Raw numbers, ahead of the pipeline: 5,248 core hours, 1.418e9 loss evaluations. dim 3 is 120
   cells and **75.6 %** of the compute, dim 1 is 276 cells and 0.2 %; the five most expensive cells
   are all Lorenz (systems 55/56) with R² between 0.19 and 0.43, the costliest at 289.7 h. Support
   recovery on the 240 exact cells: `pretune_off` **60/120** against `pretune_on` **50/120**, the
   gap carried by dim 1 (30 vs 27) and dim 2 (30 vs 23), **0/50 on dim 3 and dim 4**. Surrogate R²
   is a dead heat — median 0.9937 (`pretune_on`) against 0.9941 (`pretune_off`), 213 vs 217 cells
   above 0.9.

   **The pretuning gap does not survive clustering (WP-A6, 2026-09-07).** Paired over system, seed
   and IC set — 378 complete pairs, 120 exact, 258 surrogate. The exact-support contingency is 47/57
   concordant against **13 `pretune_off`-only and 3 `pretune_on`-only**; exact McNemar gives
   p = 0.021, but the permutation test that swaps the condition label **per system** gives
   **p = 0.218** (independently reproduced at 0.219). The 120 pairs come from 20 systems, so the
   effective sample size is 20. **60 against 50 is not a reportable finding** and must not appear as
   one. The cluster-robust procedure is the primary one throughout.

   **RETRACTED 2026-09-07 (evening): the collapse is mostly an artefact of the setup.** Without
   pretuning the parameter start is drawn randomly (`bfgs.jl:269`, `0.1 .* randn(n_params)`); with
   pretuning it is computed deterministically from the data (`evogrow.jl:473`). `pretune_off`
   therefore has **two** seed-dependent sources — structure search and parameter start — and
   `pretune_on` only one. The higher repeat rate follows from the design, not from a discovery. It
   survives as an **ablation**: the random start acts as an implicit multistart, and replacing it
   with one very good start does not always land in the right basin (system 8: `pretune_off` finds
   the structure on all three seeds at loss 8.5e-06 to 2.9e-05, `pretune_on` misses it three times
   at loss 575). Counter-evidence against "pretuning is simply deterministic": 30 of the 126
   `pretune_on` groups do **not** collapse, because the structure search stays random. The numbers
   below are correct; only their weight was wrong. Appendix material, not a carrying finding.

   **What the campaign does show is mechanistic, and it is structural (WP-A7, 2026-09-07).**
   Pretuning collapses seed diversity — grouped by system, IC set and condition, three seeds each,
   126 groups per condition paired over 63 systems:

   | target | `pretune_on` | `pretune_off` | discordant on-yes/off-no | reverse | cluster p |
   |---|---|---|---|---|---|
   | support pattern | **96 / 126** | 61 / 126 | 35 | **0** | 1.0e-5 |
   | R² | 96 / 126 | 35 / 126 | 61 | **0** | 1.0e-5 |
   | loss | 96 / 126 | 14 / 126 | 82 | **0** | 1.0e-5 |

   Across all three targets and all 126 pairs there is **not one group** where `pretune_off`
   collapses and `pretune_on` spreads, and the finding survives clustering easily — unlike the
   structural difference, which did not. Crucially the collapse shows on the **discovered support
   pattern**, not only on a number: the OLS warm start pulls the search into the same structure
   regardless of seed. That is the anchoring risk this file records for population carry-over,
   measured for the first time and at a different site, and it is what makes the claim carry for
   Claim C. Support collapse is weaker than R² collapse (61 against 35 collapsed `pretune_off`
   groups) — expected, since same structure at different parameters is more common than both.

   **The median was a specification error, and not a small one — it would have made the campaign
   look resultless.** The threshold grid shows structure the median hid. For R² the asymmetry sits
   in the *small* differences and vanishes toward the large ones (1e-4: 46 vs 63 pairs; 1e-2: 30 vs
   36; 1e-1: 16 vs 13, slightly reversed). The sign test is clear (81 against 174, cluster-robust
   p = 5.4e-4) but measures the systematic *direction*, not the *size*, of an effect. Loss separates
   the two classes cleanly: on exact systems direction is a draw (52 vs 62, p = 0.67) while the
   magnitude is skewed (fold 10: 7 vs 21; fold 100: 4 vs 14); on surrogates the direction is
   systematic (74 vs 176, p = 9.0e-5) and the magnitudes are balanced. Two different phenomena that
   one median averaged to nothing.

   **Standing rule for all further analysis:** quantiles and threshold grids, never a mean or median
   as the effect size, and the threshold is **never** picked after seeing the data — the grid is
   reported in full.

   **The descriptive tables exist (WP-A8, 2026-09-07)** under `analysis/tables/paper1_phaseB_v1/`:
   fit quality for surrogates (T1) and exact systems (T2), support recovery (T3), stage economy (T4),
   robustness and failure modes (T5). All distributions as quantiles and threshold grids. The
   dimension boundary is sharp — support recovery per condition and IC set is 18/18 to 9/27 on
   dim 1–2 and **0 of 60 on dim 3–4 in all four combinations**; the median `log10` loss on exact
   systems falls from about −11 on dim 1 to **+1.8 on dim 3**. The IC set is a real axis: on dim 1
   `pretune_off` drops from 18/18 to 12/18 on the second IC set alone, which is what WP-A4b's
   no-averaging rule was for.

   **Two instrumentation findings nobody was looking for.** `total_diverged_solves` and
   `total_solver_unstable_solves` are **identical in all 756 cells** (756 equal, 0 unequal) — one
   measure counted twice, and they must never be reported as two independent robustness quantities.
   And **18 cells never saw a single optimizer `Success`** yet reach losses down to 1.9e-12 at
   R² ≈ 0.9999, their retcode sets consisting only of `Failure` and `MaxLossEvals`. Together with
   the long-known sentinel loss `1e6` at retcode `Success`, this settles it: **the optimizer retcode
   carries no statement about result quality in either direction.** All 18 are `pretune_on` with the
   three seeds identical per system — the WP-A7 collapse again, and mechanistically consistent: the
   warm start begins so close to the optimum that the budget is exhausted before anything improves.

   T5 confirms 756 cells with `success == True`, no `failure_reason`, and `total_nonfinite_solves`
   zero throughout — but the other counters are nonzero, so error-free means completed, not
   eventless.

   **RETRACTED 2026-09-07 (evening): the campaign does not corroborate Claim B.** Both arms are
   `evogrow_v2_2_stage_capped`, 756 of 756 — **there is no uncapped arm**, so the campaign has no
   counterpart to compare against. It shows the cap's *behaviour* (early termination tracking the
   stage), never that the cap saves effort **at an unchanged result**. That half of Claim B still
   rests on the regression grid alone: **30 cells, 5 systems** — the thinnest evidence in the paper,
   carrying its main claim.

   **The analysis is complete (WP-A9, 2026-09-07).** The level-waste measure and the 252-row
   per-system table close the last two items, and `PAPER_1.md`'s result placeholders are filled.

   Two findings from the heartbeat streams. First, **`n_levels` in the records is the constant
   `N_LEVELS = 30`** (`studies/regression/run_regression.jl:681`) — the configured budget, not an
   executed count; the level heartbeat fires once per completed level and is the measurement. **690
   of 756 cells execute fewer than 30 levels**, and the count tracks the reached stage (median 1
   level at stage 1, 5 at stage 2, 21 at stage 5). That is Claim B at campaign scale: where the cap
   binds, the search ends instead of spending the budget.

   Second, the waste itself — silent levels after the last `best_loss` improvement, defined for all
   63 systems unlike `wasted_levels`:

   | dim | cells | mean `silent_fraction` | silent / total levels | last improvement at level 1 |
   |---|---|---|---|---|
   | 1 | 276 | 0.385 | 1904 / 4378 | 42 (15.2 %) |
   | 2 | 336 | 0.346 | 2401 / 6804 | 68 (20.2 %) |
   | 3 | 120 | 0.381 | 1115 / 3143 | 4 (3.3 %) |
   | 4 | 24 | **0.811** | 436 / 550 | **12 (50.0 %)** |

   Against the WP-B1 pilot (time fractions, therefore **not** directly comparable, and time is not
   evidence): dim 3 and the dim-4 peak agree, dim 1 does not — 0.385 in levels against 10 % in time.
   Cheap early levels explain it, and it strengthens rather than weakens the decision against a
   global level budget: a k tuned for dim 4 would be expensive on dim 1.

   Waste and failure are **different phenomena** and need separate sections: surrogate systems 30
   and 36 waste 0.95 and 0.925 of their levels at R² 0.988 and 0.9994, while the poor fits sit
   elsewhere (system 9 at R² 0.291, 60 at 0.492, 53 at 0.629). System 63 leads both lists —
   `silent_fraction` 0.95, support rate 0 — which is the identifiability limit this file already
   excludes, now with numbers. `wasted_levels` in the records means levels above the expected stage, not
   waste after the last improvement — median 0, 370 of 7,200 levels — and it is defined on exact
   cells only; `eq_overshoot` is nonzero in all 516 surrogate cells purely because `expected_stage`
   is nominal there. Do not aggregate the two classes on either metric.
1b. **Parked operational debts (2026-09-09).** None blocks the scientific work; collected here so
   they are not only findable in diary prose.
   - ~~The **dim-2 probe of the constant basis** is prepared and unstarted.~~ **Ran on Orion
     2026-09-10 to 2026-09-13** through the campaign's indexed path (WP-N9 gave the script the
     sharding it lacked), 335 of 336 cells at decision time, 0 errors, one identity triple
     `ec3b6bd` / `0290b75a28791195` / `ffb0266c7913352c`. Evaluated by WP-N15
     (`analysis/data/wp_n1_dim2_probe/`), and it closed P3.
   - ~~`studies/regression/wp_n1_basis_probe.jl` writes `git_hash = "not_collected"`.~~ **Repaired by
     WP-N8** before the run; the real records carry a git hash.
   - **Codex cannot execute Julia in this environment** (`A specified logon session does not exist`);
     Python runs normally. Recorded in `codex/CODEX_PROTOCOL.md` — Julia work packages are written by
     Codex, reported as `blocked`, and executed by Claude.
   - The **756 campaign cells carry no coefficients**, so their generalization is reachable only
     through a re-run. Any all-dimension generalization figure requires that run.
2. **The external columns of the protocol audit** (`docs/paper1_odebench_protocol_alignment.md`) are
   the last substantive Phase 3 item. Two additions decided 2026-08-22: the audit needs
   **representational adequacy** as a dimension, split into *in principle representable* and
   *representable under the evaluated protocol* — a published SINDy run with polynomials to degree 3
   cannot express a saturating term whatever the method could carry in principle. Open question
   unchanged: if published numbers were computed on the shipped trajectories, we work on cleaner data
   than the comparison does, and that must be declared.
3. **Representation is decided but not built** (2026-08-22). The basis represents 20 of 63 systems
   exactly; four motif families would take that to 58, the remaining five need one family each. The
   expansion is a **bridge between Paper 2 and Paper 3**, not a fourth paper and not a Paper 1
   change. Steps A and B are paid for together, the tail stays out. Full reasoning and the four
   corrections to the first draft: `docs/diskussion_repraesentationsraum.md` §9,
   `docs/phd_thesis_arc.md` §5. Two consequences that bind earlier work: Paper 2's operators must be
   **catalogue-agnostic**, and the surrogate-R² analysis needs the search-free reference fit before
   it can attribute a low R² to a missing family rather than to a failed search.

   **That reference now exists, and it moves the decision (WP-R1, 2026-08-22).** The full basis
   approximates surrogate systems almost as well as exact ones in derivative space — median 0.999993
   against 0.999998 — so "not representable" is not "poorly approximable" on the observed range. And
   the ranking of the missing families is close to the inverse of their system count: **saturating
   interaction costs nothing in the median**, while mixed monomials of degree ≥ 3 (Van der Pol,
   Duffing) are the one family with a real approximation loss — and they need no inner parameters.
   Step A gains weight, Step B loses it. Three limits are recorded with the finding
   (`docs/diskussion_repraesentationsraum.md` §11): the attribution is associative, the full basis is
   not sparse, and 13 of 126 fitted models diverge when integrated.
4. **Unbudgeted call sites outside the campaign.** WP-D3 budgeted the two campaign runners; eleven
   scripts under `benchmarks/` and `studies/` still construct the optimizer without a budget and are
   unbounded since WP-B3. Deliberate backlog, listed in `codex/reports/REPORT_WP_D3.md`.
5. **Fingerprint boundary.** The v2.2 arm sits on Baseline v0 (`0c739d4e36ee6498`), all v3 and
   capped runs on `df5db7763bcd2449`. The comparison is sound but crosses a boundary and must be
   labelled as such wherever it is reported.

   **Campaign identity is three fields since WP-P1.** The config fingerprints hash configuration
   constants only, so the WP-C3 and WP-C4 cap-logic changes left them standing — two records could
   share a fingerprint and come from differently deciding code.
   `stage_cap_behavior_fingerprint()` closes that for the cap: it hashes the decisions a frozen
   five-case probe draws out of `_cap_split_decision`. Publishability requires one git hash, one
   config/Phase B fingerprint **and** one behaviour fingerprint.

   **Current values:** Phase B `604e79733b22d64d` — carrying all 756 campaign records under
   `git 91f88c4`, verified clean at campaign end. Regression `17fe7d9cfb8f1be3` with 120 records under `git f6143eb`.
   Behaviour `ffb0266c7913352c` (probe version 2). The 42 pilot records and the 3 probe cells
   predate all of it (`e361a2af49366670` / `61b6548ef0014593`, `git 88eaeb6`) and must never be
   merged into campaign data.

   **Still blind:** the behaviour probe covers `_cap_split_decision` only — derivative estimation,
   floor computation, split aggregation and the search loop remain unobserved.

   **The threshold is not selectable from data (WP-V1).** Leave-one-system-out puts the reopen
   threshold between 0.044 and 0.278 while the shipped value is 0.35, and at the selected values
   Lorenz truncates again. The 11 % margin between 0.35 and Lorenz's worst ratio of 0.315 is a
   human choice, and it must be reported as one.

### Excluded, deliberately

- **System 63 in capped cells** — its cap is `nothing` everywhere, so the capped variant is
  identical to v3 there; it belongs in the paper as the identifiability limit, not as a cell.
- **System 54 in the regression suite** — adding it changes `REGRESSION_SYSTEMS` and hence the
  fingerprint; its limit is already documented by WP-L3 and WP-G1.
- **Search power within a stage** — population size, child generation, parsimony pressure. This is
  what `pruned_match = false` on coupled systems points at, and it is outside Paper 1. Not to be
  started implicitly.

### Open, not scheduled

- Baseline v1 under a single fingerprint, once the final variant is regression-checked on the new
  grid.
- Pathological line-search (up to 39,933 loss evals at two parameters) and the sentinel-loss `1e6`
  with retcode `Success` — untouched cost and robustness levers. WP-A8 added the counter-direction:
  18 campaign cells reach excellent fits with no optimizer `Success` at all, so the retcode is
  uninformative in both directions. Since WP-D2 a budget stop is at
  least distinguishable from a failed solve in the metadata, but both still collapse to `1e6` in the
  loss itself.
- **WP-D4b, the discover-API cleanup, after the campaign**: the `isa BFGSOptimizer` branch and the
  simulation settings it pulls out of the optimizer, a typed structure-search result instead of an
  implicitly expected NamedTuple, `search_loss` / `search_objective` / `final_loss` naming, a central
  `test/runtests.jl`, a narrower export surface, local RNGs instead of the global seed, and
  `Trajectory` validation. Deferred deliberately: it touches the path every Phase B run goes through,
  for a purely architectural gain.
- **Canonical equality and hash for `StructureSpec`** — the precondition for candidate
  deduplication. Note that under `pretuning=false` duplicates double as implicit multistarts, so a
  cache would change the experimental condition rather than merely accelerate it. Measure the
  duplicate rate before deciding.
- **The multistart is load-bearing and unnamed (WP-N4, 2026-09-09).** Handed the *true* structure,
  a **single** parameter fit hits the sentinel loss `1e6` in **15 of 102** cells; at k = 2 it is 13,
  and at **k = 3 it is zero**, with no non-adaptable cell left at k = 10. R² > 0.9 on the reference
  fit rises from 71.6 % (k = 1) to 97.1 % (k = 10). Under `pretuning=false` every fit draws
  `0.1 .* randn` (`bfgs.jl:269`); under `pretuning=true` the start is deterministic per structure.
  **Corrected 2026-09-09:** the campaign runs a median of **410 parameter fits per cell** (dim 3: 570,
  max 610) — hundreds, not thousands — and those are spread over *different* candidate structures.
  The per-structure multistart therefore equals the rate at which the same structure is re-evaluated,
  and that **duplicate rate has never been measured** (it is already listed as open under
  "Canonical equality and hash for `StructureSpec`"). The direction holds; the magnitude is
  unsupported and must not be asserted. That is the
  measured mechanism behind the pretuning disadvantage — not a vague anchoring effect. Two
  consequences: the multistart must be named, measured and described rather than existing as a side
  effect of random initialisation; and **no pretuning comparison is interpretable without stating the
  number of starts**, because it varies start quality and start count at the same time.
- **Three budget levels must be kept apart** (literature review, 2026-09-09) and currently are not:
  **structural search budget** (structures examined — PySR populations/iterations, ProGED candidates,
  ODEFormer beam size), **parameter optimization budget** (restarts k — PySR's `optimizer_nrestarts`,
  ProGED's differential-evolution population), and **run-level stochasticity** (whole seeds). Beam
  size is **not** our k: it varies *structures*, k varies *parameter starts*. Two consequences for
  the write-up: any recovery-versus-k curve needs a **cost axis** (recovery against *fits*, not
  against k) or it measures the wrong thing; and ODEFormer's constant optimizer — a learned warm
  start plus a **single** local run — is structurally our `pretune_on`, which raises an open question
  worth a contribution: is their warm start better than our OLS pretuning, or do they have the same
  15 % failure and not measure it?
- **The restart dependence is a symptom of our loss, not a universal necessity.** We optimise MSE on
  the *integrated* trajectory, which is badly conditioned; SINDy has no analogous failure mode
  because it fits in derivative space where the coefficient problem is linear. Honest framing is
  therefore not "everyone needs a budget, so do we" but **"our approach carries a failure class SINDy
  structurally cannot have"** — a limitation, and the direct continuation of the Method Positioning
  note (integration versus differentiation) of 2026-09-03.
- **Growth-only search**: `_expand` only adds terms, and every line starts from one random term, so
  a wrong term can never leave a line — selection is the only corrective. This is the structural
  reason `pruned_match = false` persists on coupled systems even at very low loss, and it must be
  stated as a limitation of the search operators. A remove/replace operator belongs to "search power
  within a stage" and stays out of Paper 1.

## Known Gaps

- **structural recovery on coupled systems is unsolved**: `pruned_match = false` on every coupled
  regression cell, including ones with a loss of 6.8e-11 and the true structure available at the
  active stage — and confirmed on campaign breadth: **0 of 50 exact dim-3/dim-4 cells** recover the
  support, against 60/120 (`pretune_off`) and 50/120 (`pretune_on`) over all exact cells
- the stage cap is not stable across initial conditions where the trajectory carries little
  dynamics (System 31, IC set 2)
- **the pruning threshold in `pruned_match` is a zero-sum dial (WP-N2, 2026-09-08).** Over a 24-rule
  grid, hits + deleted-true-term + surviving-extra-term stays constant at 45 (the subset ceiling);
  raising the threshold trades one error type for the other almost one-for-one, because spurious and
  genuine small coefficients overlap in magnitude. Best achievable over the whole grid is 30 of 66
  against today's 29 — **there is no better threshold to find.** The old basis scores 30/36 only by
  luck: at a relative threshold of 1e-1 it drops to 15/36. Report the rule dependence wherever
  `pruned_match` is used
- `wasted_levels` / `eq_wasted_levels` are computed only for `representability == "exact"`
  (`experiments/run_experiment.jl:385`), so they are `null` for 43 of 63 systems. The WP-B1 waste
  measure does not need the truth and is fully recoverable from the heartbeat `best_loss` stream —
  rebuild it in the analysis pipeline, never in the campaign path
- no train/validation split in discovery; no noise injection utilities
- no systematic comparison against ODEBench baselines (SINDy, PySR) yet — Phase 5
- expression trees are not implemented
- `utils/checks.jl` is effectively a placeholder; `simulate()` still returns NaNs on failed solves
- `total_diverged_solves` and `total_solver_unstable_solves` are identical in all 756 campaign
  cells — one quantity counted twice on the Julia side. Not a data defect, but they must not be
  reported as two independent robustness measures until the redundancy is understood
- ~~**no constant term in the basis**~~ — **closed 2026-09-13 by the P3 freeze**: the canonical
  Phase C basis is `staged_polynomial_basis_with_constant`. The gap it leaves behind is not
  representability but **searchability**: the constant is a false-positive magnet (dim 1: present in
  31 of 37 missed cells), and on dim 2 it lowers structure recovery. Expect a very low **raw**
  recovery rate in Phase C — on dim 2 the pruning rule already produces 77 % of the old basis's hits
  (30 pruned against 7 raw). Report raw and pruned everywhere; never retune the threshold
- **fitted coefficients are not persisted** — discovered models cannot be rebuilt or re-simulated
  (see Active 0b)
- **no held-out evaluation anywhere** — both IC sets are training data, every number is in-sample,
  the literature's generalization metric is unreachable without coefficients (see Active 0c)
- ~~no structural F1, term precision, term recall or coefficient error anywhere in the codebase~~ —
  **closed by WP-N7/N7b (2026-09-09)**; `analysis/utils/metrics.py` and
  `aggregate_phaseb_structure_metrics.py` supply them, and the three-way representability class
  exists. They are still hard-wired to `paper1_phaseB_v1` and need a campaign-id parameter for
  Phase C (work package B6)
- **36.4 % of the campaign's support hits exist only because of the pruning rule (WP-N7, 2026-09-09).**
  On the 240 exact Phase B cells: 119 carry every true term in the raw support, the reported
  (**pruned**) match is 110, the **raw** exact match is **70**, and **40 hits are owed entirely to
  pruning**. `exact_support_match` in the registry *is* `pruned_match`, verified 756/756;
  `support_terms` is the raw set. The containment is exact and one-way — `pruned_match == True`
  implies `missing == 0` in 110/110, never the reverse. Report raw **and** pruned wherever structure
  recovery appears; the pruned figure alone overstates recovery by roughly half. This is a reason to
  report the threshold dependence, **never** to retune the threshold.
  **The aggregate hides where it lives (WP-N7b):** dim 1 raw 51/72 → pruned 57/72, only 6 rescued;
  **dim 2 raw 19/108 (17,6 %) → pruned 53/108 (49,1 %), 34 rescued — 64 % of the dim-2 hits are
  produced by the threshold, not by the search.** dim 3/4 are 0 either way. The honest reading of
  dim-2 recovery is that the search almost never lands on the exact support, it lands on a superset
  and the threshold cleans it. The dim-2 constant-term probe must be read against a raw baseline of
  17,6 %, not 49,1 %
- **one column name, two definitions.** `experiments/run_experiment.jl:405` writes the **raw** match
  into `exact_support_match` (Phase A path, and it stores raw and pruned separately);
  `studies/regression/run_regression.jl` writes only `pruned_match`, which reaches the registry under
  the same name (Phase B path). **A join of Phase A and Phase B on that column compares different
  quantities.** Phase C records must name the definition
- **the `StructureSpec` duplicate rate is instrumented but not yet characterised.** The counter
  exists since WP-N10 (`22a9059`), canonical key plus per-run, per-stage and per-level counts, and
  it is verified bit-identical against the campaign. dim 1: system 3 at 110 fits over 2 unique
  structures (98.2 %), system 11 at 290 over 3 (99.0 %) — read as *the structure space is exhausted
  at low stages on dim 1*, *not* as *the search does not explore*. **First coupled cell (system 26,
  dim 2): 310 fits over 45 unique structures, 85.5 %** — the aggregate looks similar but the
  distribution does not: repeats per structure run from **1** through a median of **5** to 32,
  against 55–97 on dim 1. Structures receiving exactly one fit **do** occur on coupled systems, which
  is where an explicit retry bites — so the frozen `k = 3` is better founded than the dim-1 numbers
  suggested. **One cell shows the order of magnitude and decides nothing**; Phase C's C-1 arm
  supplies the distribution over 378 cells at no extra cost
- ~~the restart policy has no implementation~~ — **built 2026-09-10 (WP-N11, `4908b07`)**.
  `BFGSOptimizer.max_fit_attempts` defaults to **1**, so behaviour is unchanged and was verified
  bit-identical on a real regression cell across 84 fields. Attempt 1 uses the canonical start, later
  attempts fire only after the named predicate `fit_attempt_failed` and always draw a fresh random
  start. **Still open:** the parameter is deliberately outside the Phase B fingerprint and must enter
  the Phase C fingerprint (work package B1), where k = 3 is set — not in the optimizer default
- nothing runs the Python tests; there is no CI for tests, GitLab CI builds the campaign image only
- environment and test execution need cleanup and faster verification

## Design Principles

1. **Modular** — every component is swappable behind an abstract interface.
2. **Reproducible** — seed all stochastic behavior through `DiscoveryOptions.rng_seed`.
3. **Interpretable** — always preserve a human-readable structure description.
4. **Minimal** — do not add features without direct research motivation.
5. **Consistent logging** — route diagnostics through the common verbosity and logging pattern.
6. **Preserve metadata** — do not silently discard search or fit diagnostics.
7. **Wall-clock is never evidence.** Runs execute on a working laptop where concurrent load,
   suspend and throttling leave no trace in the data. Every cost, speedup or efficiency claim must
   rest on counts — `total_parameter_fits`, `total_loss_evals`, `total_ode_solves`, levels, stages.
   `elapsed_s` is recorded as context only and must be labelled as non-evidence wherever it is
   reported. If a claim genuinely requires timing, measure it on a dedicated machine.
8. **Exact and surrogate systems are never mixed** into one structure-correctness metric. Exact
   systems are scored on support recovery; surrogate systems on fit quality via R², reached stage
   and stability observations.
9. **Always report both metrics: structure recovery and the R² > 0.9 rate.** Every evaluation, every
   table, every claim carries both — never one alone. They measure different things and they
   disagree: on the WP-N1 dim-1 probe, structurally *wrong* cells still reach a median R² of 0.9997
   with **92 % of them above 0.9**, and a cell whose true term was destroyed by the pruning rule
   scores R² = 0.9999999996. The R² > 0.9 rate is also the metric the literature reports
   (ODEFormer/ODEBench), so it is what makes any external comparison possible at all; support
   recovery is the stricter criterion we can additionally offer. Reporting only R² hides structural
   failure; reporting only structure makes us incomparable.

## Coding Conventions

- Julia only, target Julia 1.12 series; the frozen environment is Julia 1.12.6
- public API is exported from `src/EvoODE.jl`
- `Base.@kwdef` for defaulted configuration structs
- ODE RHS functions in-place: `f!(du, u, params, t)`
- parameter vectors as `Vector{Float64}`; metadata as `NamedTuple`
- prefer modular interfaces over special-casing in orchestration

## Non-Goals

No GPU work in the current research phases. No UI. No PDE expansion. No premature optimization.
No unnecessary dependencies.

## Guiding Rule

Every change must support a research hypothesis. If you cannot state which research question a
change addresses, do not make it.

## Paper 1

`PAPER_1.md` is the authoritative execution plan (phases 0–5, Go/No-Go criteria, work packages,
risk register, frozen elements).

**Revised 2026-08-21** from `docs/PAPER_1_draft.md`, which was promoted and removed. The
precedence rule at the top of this file holds again: where the two documents drift, `PAPER_1.md`
decides.

**Current phase:** Phase 2 closed. Gate 1 decided 2026-05-30 (v2.2 fails, v3 triggered); Gate 2
decided 2026-07-31 (v3 fails). Paper scope decided 2026-08-01, final variant settled 2026-08-03:
the mechanistic Claim C study with `evogrow_v2_2_stage_capped`, and v2.2 → v3 → capped as a
documented failure analysis. Phase 2b closed 2026-08-20. Phase 3 open only in its external audit
columns; Phase B has no open scientific blocker.

**Final experiment scope** (`paper1_phaseB_v1`, all results from new runs):

- all 63 ODEBench systems (`benchmarks/data/strogatz_extended.json`)
- two conditions only: `evogrow_v2_2_stage_capped` with `pretuning=true` vs `false`
- no GP baseline, no v1, no v2.1
- sampling: 512 points over t ∈ [0,10], both IC sets, trajectories integrated by us with `Tsit5`
  at `abstol = reltol = 1e-9`
- 63 × 2 × 3 seeds × 2 IC sets = 756 runs

Before publishing: verify all runs share one git commit hash and one `config_fingerprint`; record
any discrepancy in the supplement. A change to system selection, hyperparameters, seed list,
variant definitions or metric definitions requires a new experiment identifier — frozen result
blocks are never overwritten.
