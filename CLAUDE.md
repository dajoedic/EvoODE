# CLAUDE.md — EvoODE

This file is the orientation document: what the project is, where it stands, what is decided, and
what to work on next. It is deliberately kept short. Detail lives in dedicated documents:

| Document | Holds |
|---|---|
| `DIARY.md` | chronology — design decisions, measurements, bug history, commit hashes |
| `docs/architecture.md` | component reference — types, pipeline, search algorithms, bases, optimizers, experiment infrastructure |
| `SCRIPTS.md` | runbook — exact commands for every script |
| `PAPER_1.md` | authoritative Paper 1 execution plan; takes precedence over this file if the two drift |
| `docs/paper1_study_protocol.md` | frozen Phase A protocol — claims, hypotheses, evidence rules (historical) |
| `docs/paper1_phaseA_reproducibility.md` | frozen Phase A configuration — systems, hyperparameters, seeds, metrics (historical) |
| `docs/paper1_odebench_protocol_alignment.md` | Phase B sampling protocol and the comparability audit |
| `docs/hpc_requirements.md` | Phase B resource profile, cost derivation and its uncertainty |
| `docs/hpc_deployment_guide.md` | how code reaches the Orion cluster — CI, image, manifests, glossary, failure modes (German, for newcomers) |
| `docs/phd_thesis_arc.md` | draft: the three-paper thesis arc that `PAPER_1.md` hangs under |
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
outputs/    gitignored; every script writes to its own subfolder
docs/       design notes, reports, protocols
codex/      CURRENT_TASK.md — the single active task spec
containers/ Dockerfile for the campaign image, built by GitLab CI
k8s/        Kubernetes Job manifests for the Orion cluster (bootstrap + indexed cells)
```

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
| 4 — Paper 1 | **Phase B campaign running since 2026-08-22** (`git 91f88c4`, 756 cells, `parallelism: 16`, ~9 days). Phase A frozen; stage-cap defect solved (WP-C1 to WP-C5); regression recomputed under the final identity triple (120 cells, 30/30 bit-identical, −25.4 % loss evaluations); `pretune_off` probe complete; level budget decided against (WP-B1) |
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

## Active Studies (as of 2026-08-22)

| Artifact | Status | Note |
|----------|--------|------|
| `paper1_phaseA_v1` | **frozen** (300/300) | H1 partial, H2 supported, H3 partial, H4 vacuous. Not used for final claims. `docs/paper1_freeze_memo_phaseA.md` |
| `studies/lookahead/` | WP-L1–L5d, WP-G1/G1b done | Stage-firing look-ahead — **promoted from diagnostic to the paper's contribution** |
| `studies/regression/` | 120 records on Orion, recomputed 2026-08-20 | Capped vs v2.2 over 30 cells on systems 3, 11, 26, 31, 63 under `git f6143eb` / `17fe7d9cfb8f1be3` / `ffb0266c7913352c`: loss **bit-identical 30/30**, `pruned_match` unchanged, **−25.4 %** loss evaluations, **no cell more expensive** |
| `studies/numerics/` | done (WP-T2) | Overshoot on System 26 is algorithmic, not numerical; screening is performance-only |
| `studies/generalization/` | closed | Auxiliary only; insufficient cells for supplementary inclusion |
| `studies/profiling/` | data available | Methods / Discussion only; not evidence for H1–H4 |

## Current Priorities

State as of 2026-08-22. `DIARY.md` holds the measurements; this section keeps only what still
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

1. **The Phase B campaign is running.** Started 2026-08-22 under
   `git 91f88c46063fa368101326cbfe1abcdfc9d857fc` on Orion, Job `evoode-phase-b-campaign`,
   `completions: 756`, `parallelism: 16`. The bootstrap confirmed the identity on the cluster:
   `604e79733b22d64d`, 756 rows, 756 unique identities, 20 exact / 43 surrogate. Cells start in
   cost-descending order (`indices_cost_desc.txt`, WP-H7) so the 68 h cell runs in the shadow of the
   field rather than after it; expect roughly nine days, floor 68 h. Cost model and its blind spots:
   `docs/hpc_requirements.md`. **Nothing about the campaign path may be touched while it runs.**
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
   unbounded since WP-B3. Deliberate backlog, listed in `codex/REPORT_WP_D3.md`.
5. **Fingerprint boundary.** The v2.2 arm sits on Baseline v0 (`0c739d4e36ee6498`), all v3 and
   capped runs on `df5db7763bcd2449`. The comparison is sound but crosses a boundary and must be
   labelled as such wherever it is reported.

   **Campaign identity is three fields since WP-P1.** The config fingerprints hash configuration
   constants only, so the WP-C3 and WP-C4 cap-logic changes left them standing — two records could
   share a fingerprint and come from differently deciding code.
   `stage_cap_behavior_fingerprint()` closes that for the cap: it hashes the decisions a frozen
   five-case probe draws out of `_cap_split_decision`. Publishability requires one git hash, one
   config/Phase B fingerprint **and** one behaviour fingerprint.

   **Current values:** Phase B `604e79733b22d64d` — now carrying campaign records for the first
   time, under `git 91f88c4`. Regression `17fe7d9cfb8f1be3` with 120 records under `git f6143eb`.
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
  with retcode `Success` — untouched cost and robustness levers. Since WP-D2 a budget stop is at
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
- **Growth-only search**: `_expand` only adds terms, and every line starts from one random term, so
  a wrong term can never leave a line — selection is the only corrective. This is the structural
  reason `pruned_match = false` persists on coupled systems even at very low loss, and it must be
  stated as a limitation of the search operators. A remove/replace operator belongs to "search power
  within a stage" and stays out of Paper 1.

## Known Gaps

- **structural recovery on coupled systems is unsolved**: `pruned_match = false` on every coupled
  regression cell, including ones with a loss of 6.8e-11 and the true structure available at the
  active stage
- the stage cap is not stable across initial conditions where the trajectory carries little
  dynamics (System 31, IC set 2)
- Phase B needs a machine: 756 runs, ~1e9 ODE solves; not a laptop workload
- no train/validation split in discovery; no noise injection utilities
- no systematic comparison against ODEBench baselines (SINDy, PySR) yet — Phase 5
- expression trees are not implemented
- `utils/checks.jl` is effectively a placeholder; `simulate()` still returns NaNs on failed solves
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
