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
lives in `codex/CODEX_PROTOCOL.md`; it does not change between tasks. Codex reports
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
| 4 — Paper 1 | Phase A frozen; Phase B ported to Kubernetes and verified end to end on the cluster; **pilot finished 2026-08-17**; campaign blocked on the stage-cap defect (Active 0) |
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

## Active Studies (as of 2026-08-03)

| Artifact | Status | Note |
|----------|--------|------|
| `paper1_phaseA_v1` | **frozen** (300/300) | H1 partial, H2 supported, H3 partial, H4 vacuous. Not used for final claims. `docs/paper1_freeze_memo_phaseA.md` |
| `studies/lookahead/` | WP-L1–L5d, WP-G1/G1b done | Stage-firing look-ahead — **promoted from diagnostic to the paper's contribution** |
| `studies/regression/` | 42 records, 4 fingerprints | Final variant covers 10 cells on systems 3, 11, 26, 31 — all on the **old** grid. Batch path (manifest / one cell per process / merge) in place; no record yet on `7acd3ebf3f60b974` |
| `studies/numerics/` | done (WP-T2) | Overshoot on System 26 is algorithmic, not numerical; screening is performance-only |
| `studies/generalization/` | closed | Auxiliary only; insufficient cells for supplementary inclusion |
| `studies/profiling/` | data available | Methods / Discussion only; not evidence for H1–H4 |

## Current Priorities

State as of 2026-08-03. `DIARY.md` holds the measurements; this section keeps only what still
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

**Cost and numerics, closed.** Screening is a performance optimization only, never a
discovery-quality lever. Overshoot on System 26 is tolerance-invariant, therefore algorithmic. On
the coupled search path 1e-6 is the cheaper, behaviour-equal tolerance; the System 11 loss of
4.402e-15 is numerical noise.

### Active

0. **CAMPAIGN BLOCKER — the stage cap truncates true structures. Half solved (WP-C1, 2026-08-17).**
   The audit over all 20 exact systems, both IC sets, horizons 2–5 (`docs/wp_c1_stage_cap_horizon_audit.md`)
   put the rate at **9 equation rows on 5 of 20 systems** at the shipped `lookahead_horizon = 2`.

   **Solved: the horizon.** The basis stages by degree, not parity, so odd nonlinearities first
   become approximable at stage 4/5 and a horizon of 2 never reaches them. Raising it moves six
   rows and every new cap lands *exactly* on the required stage — 28 eq2 1→5, 32 eq2 1→4, and
   38 eq1 `nothing`→4, the last one tightening a previously uncapped equation onto the cubic term
   it needs. Horizons 3, 4 and 5 are cap-identical on all 80 equation rows, so the parameter is
   inert above 3; WP-C2 sets it to **5 = the number of basis stages**, i.e. no horizon, rather than
   leave a tuned constant in the paper.

   **Open: a second, different mechanism.** Five rows survive every horizon — Lorenz equation 3 on
   Systems 55 and 56 (cap 2, required 3, both IC sets) and System 31 equation 1 on IC set 2 (cap 1,
   required 3). At Lorenz the cross term `u1*u2` is already inside the horizon at 2, so it is seen
   and not counted as a gain. Prime suspect: derivative estimation on chaotic trajectories, the
   same ground v3 failed on (WP-L2). WP-C2 diagnoses it; the decisive test is re-running the cap
   with analytic derivatives. **The campaign stays blocked on these five rows.**

   **Counter-check held:** System 61 (Chen-Lee) caps correctly at `[3,3,3]`. The defect is
   selective, not general.

   **Consequence for the 40 % recovery figure:** several of the six failures are controller errors,
   not search errors, and must be counted separately.

   **Limitation to declare regardless of outcome:** the cap is auditable only on the 20 exact
   systems. The 43 surrogates have no ground-truth support, so controller safety is unverifiable
   there by construction — and the pilot shows several surrogates carrying an equation capped at
   stage 1 (33, 34, 40, 44, 50). They are scored on R², so it is a fit-quality risk rather than a
   support error.

1. **Phase B compute — access obtained, path verified end to end (2026-08-13).** The target is SCCH
   **"Orion", an OpenShift/Kubernetes cluster**, not a Slurm site: `containers/Dockerfile` built by
   GitLab CI, `k8s/` Job manifests with `completionMode: Indexed`, results on NFS. The full chain
   from commit to finished record has been run and verified at every hand-off; see
   `docs/hpc_deployment_guide.md` for the mechanics and `DIARY.md` (WP-H2 to WP-H6) for the
   chronology. 846 jobs (756 Phase B + 90 regression), 1 core and 2 GB each, no GPU, Julia 1.12.6
   pinned.

   **Cost model — pilot finished 2026-08-17, the total holds.** 42 cells (systems 24–62, seed 42,
   IC set 1, `pretune_on` only) project to **3,384 core-hours** for the 756 Phase B cells against
   the ~3,900 estimated in `docs/hpc_requirements.md` §5 — 15 % low, not the "one to two orders of
   magnitude too high" previously recorded here; that earlier claim was drawn from the head of a
   very skewed distribution (dim 2: median 0.19 h, mean 2.90 h) and does not survive the full
   sweep. The per-class split *is* wrong: dim 4 overestimated 36x, **dim 3 underestimated 1.5x**.
   At `parallelism: 16` that is ~9 days wall; the makespan floor is the longest single cell at
   **68 h**, so no parallelism gets the campaign under 3 days. Still unmeasured, and therefore a
   lower bound: **`pretune_off`, i.e. half the campaign**; systems 1–23 rest on one measured system,
   63 on none; one seed, one IC set (System 62 varies 14x between seeds 42 and 123). Rewrite
   `docs/hpc_requirements.md` from these numbers. Capacity agreed with the site:
   **`parallelism: 16`** of 96 cluster cores, raise on request. No walltime limit, therefore no
   checkpointing needed.

   **Per-level cost is a trend, not an outlier — diagnosis revised 2026-08-17.** The heartbeat
   series shows per-level cost growing monotonically over three orders of magnitude with structure
   size (System 59: 49 s at level 1 → 42,372 s at level 30), not isolated pathological levels; in
   the most expensive cells the slowest single level is only 17–26 % of the cell. And the expensive
   half buys nothing: Systems 59, 61 and 56 (all chaotic) burn 40–68 h to end at losses of 1.5,
   63 and 45. System 59 spends 6.6e6 loss evals on 610 parameter fits — ~10,900 solves per fit,
   the line-search cost lever, quantified on dedicated hardware for the first time. Open decision:
   a dimension-dependent level budget or a no-improvement stop. Fingerprint-relevant, so it must
   land with the cap fix in **one** fingerprint step, not two.
2. **Unbudgeted call sites outside the campaign.** WP-D3 budgeted the two campaign runners; eleven
   scripts under `benchmarks/` and `studies/` still construct the optimizer without a budget and are
   unbounded since WP-B3. Deliberate backlog, listed in `codex/REPORT_WP_D3.md` — not to be fixed
   before the campaign.
4. **Fingerprint boundary.** The v2.2 arm sits on Baseline v0 (`0c739d4e36ee6498`), all v3 and
   capped runs on `df5db7763bcd2449`. The comparison is sound but crosses a boundary and must be
   labelled as such wherever it is reported. **Current fingerprints after WP-M1 (2026-08-13):**
   Phase B `ca02ea284d621f6d`, regression `0825cdc88d9264a0`. Both carry **no records yet** — the
   pilot data predates them and must never be merged with campaign records. All
   fingerprint-affecting changes must land before the first campaign record.
5. **Remaining Phase 3 items** (`PAPER_1.md`): filling the external columns of the protocol audit
   from the publications. Open question there: if published numbers were computed on the shipped
   trajectories, we work on cleaner data than the comparison works — a deviation in our favour that
   must be declared. *(The R² metric is done, WP-M1.)*
6. **`PAPER_1.md` is stale and it is the authoritative document.** Dated 2026-05-17, it plans in
   detail around v3 and does not mention the stage cap once — the variant that is the contribution.
   Until it is revised, `CLAUDE.md` and `DIARY.md` carry the current state, which inverts the
   precedence rule stated at the top of this file. This must be resolved before writing.
7. **Analysis downstream is Phase-A shaped.** WP-A1 built a bridge from campaign records into the
   Python pipeline, but `table_main_results.py` reindexes to a hard-coded Phase-A variant list and
   silently produces a near-empty table for campaign variants. Not a campaign blocker; a blocker for
   evaluating one.

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

**Current phase:** Phase 2 closed. Gate 1 decided 2026-05-30 (v2.2 fails, v3 triggered); Gate 2
decided 2026-07-31 (v3 fails). Paper scope decided 2026-08-01, final variant settled 2026-08-03:
the mechanistic Claim C study with `evogrow_v2_2_stage_capped`, and v2.2 → v3 → capped as a
documented failure analysis. Phase 3 in progress; Phase B blocked only on compute.

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
