# ROADMAP.md — EvoODE Paper 1 Execution Roadmap

## Purpose

This document defines the scientific and operational roadmap for Paper 1 of the EvoODE project.

Its purpose is to:

* stabilize the scientific direction of Paper 1
* define the role of all current experiments
* prevent scope creep
* ensure that all subsequent work supports a coherent publication

This document is intentionally limited to Paper 1 only.

It is NOT:

* a general EvoODE roadmap
* a long-term PhD vision document
* an implementation plan
* a task backlog

Detailed experiment definitions belong in:

* `docs/paper1_study_protocol.md`
* `CLAUDE.md`

---

# 1. Core Scientific Narrative

The central problem of data-driven ODE discovery is the trade-off between:

* expressive search spaces
* computational tractability
* structural interpretability

Existing approaches typically occupy opposite ends of this trade-off.

## SINDy

SINDy operates on a highly constrained search space:

* efficient
* interpretable
* computationally cheap

However:

* expressivity is limited
* search flexibility is low
* discovery quality strongly depends on the predefined basis and sparsity assumptions

## Genetic Programming (GP)

GP explores a highly expressive symbolic search space:

* flexible
* potentially highly expressive

However:

* search is weakly structured
* computational cost is high
* optimization instability is common

## EvoGrow

EvoGrow is positioned between these extremes.

Core idea:

> Complexity should not be searched globally from the beginning.
> Instead, complexity should grow progressively and only when justified by the search dynamics.

EvoGrow therefore explores:

* a broader search space than SINDy
* but a more structured and progressively expanding space than GP

The central scientific question of Paper 1 is:

> Can staged complexity growth improve search efficiency and interpretability without collapsing recovery quality?

---

# 2. Scientific Goal of Paper 1

Paper 1 is a mechanism and search-strategy study.

The goal is NOT to prove:

* universal superiority over GP
* globally optimal symbolic recovery
* runtime optimality
* state-of-the-art performance on all systems

The goal IS to evaluate whether:

> staged growth provides a scientifically meaningful and computationally disciplined search strategy for ODE discovery.

The paper focuses on:

* controlled complexity growth
* search-space structuring
* recovery behavior under progressive expansion

---

# 3. Core Hypothesis Structure

The detailed formal hypotheses are defined in:

* `docs/paper1_study_protocol.md`

At a high level, Paper 1 investigates four questions:

## H1 — Controlled Complexity Growth

Does EvoGrow remain in low-complexity stages for simple systems and only increase complexity when necessary?

## H2 — Competitive Recovery Quality

Can EvoGrow maintain recovery quality comparable to GP while using a more structured search process?

## H3 — Complexity Efficiency

Does staged growth reduce unnecessary exploration of higher-complexity regions?

## H4 — Usage Policy Effect (Secondary)

Among EvoGrow v2.2 variants, does the usage policy after stage unlock (hard / soft / passive)
have a measurable effect on exact_match_rate on systems requiring stage ≥ 3?

This hypothesis is secondary. If results are ambiguous, C3 is weakened but H1–H3 remain unaffected.

---

# 4. Evidence Hierarchy

Not all experiments have equal scientific weight.

The following hierarchy is fixed for Paper 1.

| Experiment                | Role                             |
| ------------------------- | -------------------------------- |
| `paper1_phaseA_v1`        | Main Evidence                    |
| `generalization_study.jl` | Auxiliary Evidence               |
| `profile_init.jl`         | Mechanistic / Discussion Support |
| `benchmark_evogrow.jl`    | Exploratory Cross-Check          |

## Main Evidence

The formal experiment infrastructure under:

```text
experiments/run_experiment.jl
```

is the authoritative evidence source for Paper 1.

Only this experiment family is allowed to:

* support primary claims
* produce final paper tables
* produce quantitative paper comparisons

## Auxiliary Evidence

Generalization studies may:

* support interpretation
* strengthen structural arguments

They must NOT:

* override primary evidence
* become the central contribution

## Exploratory Evidence

Exploratory benchmarks and profiling studies:

* may guide interpretation
* may identify future directions
* may support discussion sections

They are not primary scientific evidence.

### Placement constraints for profile_init.jl

`profile_init.jl` results may appear in:

* the Methods section as an implementation or numerical stability detail
* a short Discussion paragraph as mechanistic context or future-work motivation

`profile_init.jl` must NOT:

* be used as primary or auxiliary evidence for H1–H4
* generate main-paper figures or tables
* be framed as an algorithmic contribution of Paper 1

---

# 5. Current Project Status

The following experiment groups currently exist.

## Completed

### Paper 1 Main Experiment

`paper1_phaseA_v1`

* 10 systems
* 6 variants
* 5 seeds
* 300 total runs
* full experiment infrastructure
* aggregated outputs available

Note on `run_type`: per-run config files carry `run_type = exploratory`. This reflects the
internal phase labeling scheme of the research project, not the scientific status of the
results. Phase A results are final. The `run_type` field must not be used to qualify
or discount Phase A evidence.

### Exploratory Benchmark

`benchmark_evogrow.jl`

* qualitative cross-check benchmark
* same systems and variants
* exploratory only

### Initialization Profiling Study

`profile_init.jl`

* compares random initialization vs OLS warm-start
* supports optimization discussion
* not part of primary claims

### Generalization Study

`generalization_study.jl`

* evaluates structure reuse across parameter regimes
* auxiliary evidence only

---

# 6. Immediate Execution Roadmap

The next steps are fixed in the following order.

---

## Step 1 — Aggregation Integrity Verification

Goals:

* verify all metrics
* verify exclusions
* verify aggregation consistency
* ensure protocol compliance

Required outputs:

* `run_registry.csv`
* `aggregate_by_variant_system.csv`

No interpretation occurs in this step.

---

## Step 2 — Primary Metric Analysis

Goals:

* evaluate H1–H4
* determine whether claims hold
* identify failure modes
* assess evidence strength

Output:

* internal hypothesis assessment memo

The memo must be structured in three separate blocks:

**Block 1 — Primary claims (H1–H3)**
One entry per hypothesis. Each entry states:
- supported / ambiguous / falsified
- the systems and seeds on which the pattern holds or fails
- allowed paper claim (exact wording)

**Block 2 — Secondary claim (H4)**
One entry for H4 (usage policy effect). Same structure as Block 1.
H4 must not appear on equal footing with H1–H3.
If H4 is ambiguous, C3 is weakened; H1–H3 are unaffected.

**Block 3 — Auxiliary evidence**
One entry per auxiliary study (generalization, profile_init).
States whether to include in supplementary material or omit.
Auxiliary evidence must not affect the claim statements in Blocks 1 and 2.

No new experiments may be initiated based on Step 2 findings unless:
- a data-integrity problem is identified
- a Phase B trigger condition (n_valid = 0 cell) is met
- an implementation error in a metric is confirmed

This is the most important analysis phase.

No figures are created before this step is complete.

---

## Step 3 — Evidence Freeze

After H1–H4 evaluation:

* evidence scope is frozen
* no new experiments may be added to support claims
* no retrospective cherry-picking allowed

The freeze memo from Step 2 defines what the paper is allowed to claim.
Nothing beyond the memo may appear in the paper.

Only after this freeze may figures, tables, and writing begin.

---

## Step 4 — Figure and Table Generation

Generate only:

* protocol-approved figures
* protocol-approved tables

No exploratory visuals are allowed in the paper draft.

---

## Step 5 — Auxiliary Evidence Evaluation

Goals:

* evaluate whether auxiliary studies strengthen the narrative
* assess whether generalization evidence is stable
* interpret profiling behavior

Possible outcomes:

* include in supplementary material
* omit entirely

Auxiliary evidence must not appear in the main paper body.
The generalization study, if included, is placed in supplementary material only.

---

## Step 6 — Paper Writing

Writing begins only after:

* evidence freeze
* claim evaluation
* figure and table generation
* auxiliary evidence evaluation

---

## Step 7 — Final Traceability Validation

Before submission:

Verify that every result in the paper draft traces to:

* a hypothesis defined in `docs/paper1_study_protocol.md`
* an experiment in Phase A (or Phase B if applicable)
* a metric defined in Section 4 of the study protocol

If any result cannot be traced → remove it from the paper.

This step is mandatory and must not be skipped.

---

# 7. Decision Gates

The following decision gates are mandatory.

## Gate 1 — Do H1–H3 hold?

A hypothesis is considered supported if the stated directional pattern holds across
the majority of relevant systems and seeds. A claim is falsified if the stated
direction does not hold across the majority of systems and seeds.

Definitions:
* **YES**: directional pattern holds across the majority of relevant systems
* **PARTIAL**: directional pattern holds for ≥ 1 system but not the majority
* **NO**: directional pattern does not hold for any relevant system

Possible outcomes:

### YES

Proceed with planned narrative.

### PARTIAL

Narrow the affected claim to the systems and conditions where it holds.
State the boundary conditions explicitly. Do not generalize beyond what the data supports.

### NO

The affected claim must be removed or fundamentally reframed before publication.
This is a scientific result, not a reason to run new experiments for Paper 1.

---

### exact_match=0 collapse scenario

If `exact_match_rate = 0` for all methods across the majority of exact systems with
expected_stage ≥ 3, the primary recovery comparison (H2) cannot be evaluated on exact
structure recovery alone.

In this case, the following adjustment is permitted and must be documented in the
freeze memo:

* H2 shifts from an exact_match_rate comparison to a loss-based recovery comparison
* `mean_loss` becomes the operative recovery metric for affected systems
* This shift must be stated explicitly in the paper and justified by the data
* The exact_match_rate results (all zero) are still reported in full — they are a
  scientific finding, not a reporting failure

This adjustment does not affect H1 or H3 (complexity efficiency metrics are
independent of exact_match_rate).

---

## Gate 2 — Does auxiliary evidence support the story?

Possible outcomes:

### YES

Include in supplementary material.

### UNCLEAR

Include in supplementary material with explicit statement of uncertainty.

### NO

Exclude from Paper 1.

---

# 8. Explicit Non-Goals

Paper 1 is NOT:

* a runtime optimization paper
* a universal GP replacement
* a large-scale benchmark arms race
* a symbolic regression framework paper
* a pretuning contribution paper
* an HPC scaling paper
* a production software paper

Advanced optimization engineering:

* pretuning
* adaptive policies
* learned progression
* advanced runtime control

may become future work,
but are not core Paper 1 contributions.

---

# 9. Guiding Principle

All work performed after this roadmap freeze must support the following question:

> Does this strengthen or clarify the staged-growth hypothesis?

If not:

* it is exploratory only
* or it does not belong in Paper 1.

Scientific discipline is prioritized over feature expansion.
