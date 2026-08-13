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
threshold is unreachable on coupled systems, where the error floor sits four orders of magnitude
above it.

**The evidence.** An earlier 300-run study is frozen and **explicitly not used for final claims**;
see `docs/paper1_freeze_memo_phaseA.md`. The campaign that will carry the claims covers all 63
ODEBench systems and has not been run yet.

**Known limitation.** Structure recovery on coupled systems succeeds on some systems and not on
others, and the discriminator appears to be the achieved loss rather than the dimension. The search
operators only add terms — a wrong term can never leave a candidate line, and selection is the sole
corrective. This is stated as a limitation, not worked around.

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
containers/   Dockerfile for the campaign image
k8s/          Kubernetes Job manifests for the compute cluster
codex/        the single active task spec for an AI coding assistant
docs/         protocols, design notes, reports
outputs/      gitignored; every script writes to its own subfolder
```

`benchmarks/` and `experiments/` are not interchangeable: the former is exploratory and qualitative,
the latter is paper-grade with atomic writes, per-run status tracking and a derived registry.

---

## Benchmark dataset

`benchmarks/data/strogatz_extended.json` — the extended Strogatz/ODEBench catalogue:

- **63 systems**: 23 scalar (1D), 28 coupled 2D, 10 coupled 3D, 2 coupled 4D
- **20 exact**, meaning the true right-hand side is exactly representable in the staged basis
- **43 surrogate**, meaning it is not — these are scored on fit quality, never on support recovery

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

---

## Documentation

| File | Contents |
|---|---|
| `CLAUDE.md` | orientation: what the project is, what is decided, what to work on next |
| `PAPER_1.md` | authoritative execution plan for the first paper |
| `DIARY.md` | chronology — decisions, measurements, bug history, commit hashes |
| `SCRIPTS.md` | runbook — every script, with exact commands |
| `docs/architecture.md` | component reference |
| `docs/hpc_deployment_guide.md` | how code reaches the compute cluster (German, for newcomers) |

Start with `CLAUDE.md`. Where it and `PAPER_1.md` disagree, `PAPER_1.md` wins.

---

*PhD research project, Software Competence Center Hagenberg (SCCH).*
