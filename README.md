# EvoODE — Evolutionary ODE Discovery

A Julia research framework for **data-driven discovery of interpretable ODE systems** from
time-series data, with a focus on coupled multi-dimensional systems.

Instead of fitting a fixed library like SINDy, or searching globally from large random structures
like genetic programming, EvoODE starts from minimal models and grows structure incrementally —
only when simpler structures are demonstrably insufficient.

> **Core idea:** structured, iterative growth instead of global search.

This is an active PhD research project. Scientific correctness, reproducibility and interpretability
take precedence over speed and feature count.

---

## 🛰️ Live status — [Phase C auf Orion](https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx)

**What is computing right now, how far it has come, and what happens next.** The Phase C campaign —
the canonical evaluation this project's first paper rests on — runs on the Orion cluster. The status
page carries the current cell counts, the cost-based progress that the cell counter misrepresents,
the open risk to Claim B, and the ordered plan. It is republished whenever the state changes.

---

## Scientific position

| Method | Search space | Growth strategy | Complexity control |
|---|---|---|---|
| SINDy | restricted: fixed linear library | none (direct regression) | L1 sparsity |
| GP | unrestricted | global: starts large, random | parsimony pressure |
| **EvoODE** | **unrestricted** | **incremental: starts minimal, grows** | **staged grammar + stopping criterion** |

Claims under investigation:

1. Starting small and growing incrementally can be more efficient than global search.
2. Grammar-staged complexity unlocking can reduce wasted computation.
3. The stopping and promotion criterion can serve as a principled complexity-control mechanism.

---

## Status

**The method.** The final variant is `evogrow_v2_2_stage_capped`: stage-local progression plus a
per-equation **look-ahead stage cap** derived from the trajectory and basis *before* the search
starts. Because the cap reads only data and basis, it is search-independent.

Two earlier designs are retained as documented failure analysis rather than being quietly dropped:
stage-local progression alone (fails its gate, 2026-05-30) and a derivative-residual promotion
signal (fails its gate, 2026-07-31). The second failed for an instructive reason — its promotion
threshold is unreachable on coupled systems, where the error floor sits five orders of magnitude
above it.

**The evidence, and which run carries it.** The paper rests on **Phase C**, the canonical
evaluation, which is **running now** — see the live status page above. Its plan, with a claim,
an arm, a script and a pass criterion for each question, is `docs/paper1_phaseC_benchmark_plan.md`.

An earlier campaign, **Phase B**, finished on 2026-09-04: all 63 ODEBench systems, two pretuning
conditions, three seeds, both initial-condition sets — 756 of 756 cells, no errors, one git hash and
one identity triple across every record, 5,248 core hours. It was **demoted to diagnostics on
2026-09-09** and is not the benchmark: it was computed before the methodological review below closed,
and carries four defects a final benchmark cannot have — no constant term in the basis, no stored
coefficients, both initial-condition sets used as training, and no uncapped arm to compare against.
**Phase B and Phase C numbers never appear in the same table.** Phase B remains a good source of
ablations, runtime analysis and failure cases; its registry, heartbeat history and descriptive tables
are tracked under `experiments/paper1_phaseB_v1/` and `analysis/tables/paper1_phaseB_v1/`. An even
earlier 300-run study is frozen and **explicitly not used for final claims**; see
`docs/paper1_freeze_memo_phaseA.md`.

**Where the project stands, stated plainly.** A review in September 2026 found four gaps that the
campaign had not been designed to close, and closing them changed the picture more than the campaign
did:

- **The basis has no constant term.** It represents 20 of 63 systems exactly; SINDy's plain
  polynomial library represents 40. Adding the constant is not a free improvement — it roughly
  halves structure recovery on dimension 1 (83 % → 39 %, the constant is a false-positive magnet)
  while markedly improving generalization (73 % → 88 %). Which basis is right depends on which
  metric counts, and that is a question about the method's purpose.
- **No held-out evaluation existed.** Both initial-condition sets were training data. Measured for
  the first time in September 2026: the share of predictions with R² > 0.9 falls from **95.5 %
  reconstruction to 68.2 % generalization** — qualitatively the drop ODEFormer reports.
- **No baseline had ever been run.** EvoGrow had only been compared against earlier EvoGrow
  variants. On identical trajectories and dimension 1, the best of ten SINDy configurations reaches
  95.7 % reconstruction and 60.9 % generalization against EvoODE's 95.5 % and 68.2 % — **a draw on
  reconstruction, EvoODE ahead on generalization, at roughly two orders of magnitude more compute.**
  SINDy runs one linear regression per equation; EvoODE runs a median of 410 nonlinear fits per cell.
- **Fitted coefficients were not persisted** and now are. The 756 campaign cells predate that change,
  so their generalization is reachable only through a re-run.

The consequence is stated rather than argued away: on the easiest system class the method is level
with a far cheaper baseline. Its value has to show somewhere else — under noise, on coupled systems,
or in the interpretability of the search path. See `CLAUDE.md` (Active 0) and `PAPER_1.md`.

**Known limitations.** Structure recovery on coupled systems is unsolved: **0 of 50 exact
dimension-3/4 cells** recover the support, against 60 of 120 over all exact cells. The search
operators only add terms — a wrong term can never leave a candidate line, and selection is the sole
corrective. Parameter fitting minimises MSE on the *integrated* trajectory, which is badly
conditioned; a single start hits the failure sentinel in 15 of 102 cells even when handed the true
structure. SINDy has no analogous failure mode because it fits in derivative space. These are stated
as limitations, not worked around.

---

## Quick start

Requires Julia **1.12.6** (pinned; `Manifest.toml` is committed).

```bash
git clone https://github.com/dajoedic/EvoODE.git
cd EvoODE
julia --project=. -e 'import Pkg; Pkg.instantiate()'
```

Run the exploratory benchmark:

```bash
julia --project=. benchmarks/benchmark_evogrow.jl
```

`SCRIPTS.md` documents every runnable script with its exact invocation, flags and environment
variables.

---

## How it works

### The pipeline

```text
discover(traj; structure, optimizer, basis, loss, options)
    │
    ├─ 1. search_structure(...)  →  structure + parameters + loss + metadata
    ├─ 2. build_rhs(...)         →  f!(du, u, p, t)
    ├─ 3. simulate(...)          →  Ŷ  (T × dim)
    └─ 4. evaluate_loss(...)     →  DiscoveryResult
```

Each component sits behind an abstract interface and is swappable. New structure searches, bases,
losses and optimizers are registered in `src/EvoODE.jl`; algorithm-specific logic never enters
`discover()` itself.

### The staged basis

The default basis exposes five complexity stages:

| Stage | Terms |
|---|---|
| 1 | linear: `u1`, `u2`, … |
| 2 | self-quadratic: `u1²`, … |
| 3 | pairwise cross terms: `u1·u2`, … |
| 4 | self-cubic: `u1³`, … |
| 5 | trigonometric: `sin(u1)`, `cos(u1)`, … |

The search unlocks stages one at a time. The stage cap decides, before the search begins, which
stages are worth unlocking at all for a given system and equation.

Note what is **not** in the table: a constant term. `staged_polynomial_basis_with_constant` adds
`1` to stage 1 and is verified bit-identical to the table above on 66 of 66 control cells. Since
2026-09-13 it is the **canonical basis for Phase C**: 20 of 63 systems exactly representable is not
a defensible search space when SINDy's plain polynomial library reaches 40. The decision was taken
*against* the recovery numbers, not with them — the constant is a false-positive magnet and lowers
structure recovery — so representability and searchability genuinely pull against each other, and
that tension is a finding rather than a settled trade. The basis in the table remains available and
is what every Phase B result was computed on.

### Two design axes, deliberately separate

**Stage progression** governs when a stage is kept, promoted or terminated. **Stage usage** governs
how strongly newly unlocked terms are encouraged. Collapsing them into one mechanism has been tried
and is not to be repeated; on promotion the population is carried over unchanged, and the usage
policy is the counter-measure against anchoring.

---

## Repository layout

```text
src/          core/ structure/ basis/ loss/ optimize/ simulate/ plotting/ utils/
benchmarks/   exploratory, direct-execution scripts + the ODEBench dataset
experiments/  formal, manifest-based runs with atomic writes and per-run status
studies/      direct-execution studies; most are closed and kept for provenance
analysis/     Python analysis pipeline
baselines/    foreign discovery methods run on our own exported trajectories
containers/   Dockerfile for the campaign image
k8s/          Kubernetes Job manifests for the compute cluster
codex/        the active task spec and the work-package reports of an AI coding assistant
docs/         protocols, design notes, reports
paper/        Paper 1 manuscript sections, one file per section
test/         Julia tests (per-file, run directly)
outputs/      gitignored; every script writes to its own subfolder
```

`benchmarks/` and `experiments/` are not interchangeable: the former is exploratory and qualitative,
the latter is paper-grade with atomic writes, per-run status tracking and a derived registry.

Work-package reports live in two places by rule, not by accident: `codex/reports/REPORT_WP_*.md` is what the
assistant wrote when it finished the package, `docs/WP-*.md` is a report promoted to a reference
someone else is expected to read. See "Documentation" below.

---

## Benchmark dataset

`benchmarks/data/strogatz_extended.json` — the extended Strogatz/ODEBench catalogue:

- **63 systems**: 23 scalar (1D), 28 coupled 2D, 10 coupled 3D, 2 coupled 4D
- **exact** means the true right-hand side is exactly representable in the basis, and the count
  therefore depends on which basis: **20 of 63** without a constant term, **30 of 63** under the
  canonical Phase C basis, which adds one
- the remainder are **surrogate** — scored on fit quality, never on support recovery

The exact/surrogate split is **derived**, not hand-maintained: the true support is reconstructed from
the dataset's right-hand sides and must be both exact to 1e-9 and minimal. An earlier hand-written
classification called three systems exact that are not.

Trajectories are integrated by this project rather than taken from the dataset's shipped values, at
`abstol = reltol = 1e-9`; see `docs/paper1_odebench_protocol_alignment.md` for the protocol and the
comparability audit.

---

## Reproducibility

The properties below are enforced, not aspirational.

- **Deterministic given a seed.** All stochastic behaviour goes through `DiscoveryOptions.rng_seed`.
  The optimizer's safety brake is a deterministic evaluation-count budget, never a wall-clock limit,
  so results do not depend on machine speed.
- **Configuration fingerprints.** Every result carries a hash over the full experimental
  configuration, including the derived support table and the metric definitions. Runs with different
  fingerprints are not silently comparable.
- **Frozen environment.** Julia 1.12.6 with a committed `Manifest.toml`. The cluster image records
  the version and the dependency hashes at build time, and is tagged with the commit it was built
  from.
- **Wall-clock is never evidence.** Cost claims rest on counts — parameter fits, loss evaluations,
  ODE solves, levels, stages. Timings are recorded as context and labelled as such.
- **The evidence is in the repository.** Run registries, campaign histories and the tables the
  documents cite are tracked; only the per-run scratch directories are not, because they are
  reproducible from the registry and the image while the registry is not reproducible at all.

---

## Documentation

| File | Contents |
|---|---|
| `CLAUDE.md` | orientation: what the project is, what is decided, what to work on next |
| `PAPER_1.md` | authoritative execution plan for the first paper |
| `docs/paper1_phaseC_benchmark_plan.md` | the Phase C claim → experiment → metric → output matrix, and the frozen decisions |
| `READ_THIS_FIRST.md` | volatile session handover — what is running, what is uncommitted, what decision is pending |
| `DIARY.md` | chronology — decisions, measurements, bug history, commit hashes |
| `SCRIPTS.md` | runbook — every script, with exact commands |
| `docs/architecture.md` | component reference — types, pipeline, search algorithms, bases, optimizers |
| `docs/paper1_odebench_protocol_alignment.md` | ODEBench sampling protocol and the comparability audit |
| `docs/diskussion_repraesentationsraum.md` | what the basis can and cannot represent, and what that costs |
| `docs/hpc_deployment_guide.md` | how code reaches the compute cluster (German, for newcomers) |
| `analysis/CONVENTIONS.md` | rules for the Python analysis pipeline |

Start with `CLAUDE.md`. Where it and `PAPER_1.md` disagree, `PAPER_1.md` wins.

**Where a report belongs.** `codex/reports/REPORT_WP_<id>.md` is the finishing report of a work package,
written once and not maintained afterwards — provenance, not documentation. `docs/WP-<id>.md` is a
report promoted because a decision rests on it and someone outside the work package needs to read
it; it is linked from `CLAUDE.md` or `PAPER_1.md` and kept correct. A report never exists in both
places. Older files under `docs/wp_<id>_<description>.md` predate the rule and are not renamed,
because `DIARY.md` cites them by path.

---

*PhD research project, Software Competence Center Hagenberg (SCCH).*
