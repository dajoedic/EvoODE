# EvoODE MASTERPLAN

## Vision
EvoODE is a research platform for discovering interpretable, coupled dynamical systems from data through structured, iterative growth.

The goal is not merely to fit ODEs, but to study how model structures should be constructed, expanded, validated, and controlled.

---

## Core Idea
Data → Structure → Parameters → Simulation → Evaluation → Iteration

Key principle:  
Structured, iterative growth instead of global search.

---

## PhD Focus
Efficient and robust search strategies for interpretable discovery of coupled ODE systems.

---

## Key Research Questions
- How should structure grow?
- How to couple structure and parameter optimization?
- How to handle coupled systems?
- How to control complexity?
- How to evaluate discovered models?

---

## Growth Strategies
- Term-wise growth
- Equation-wise growth
- Complexity-tiered growth
- Coupling-aware growth
- Error-guided growth

---

## System Handling
- Full-system discovery
- Equation-wise with teacher forcing
- Sequential discovery
- Hybrid approaches

---

## Evaluation
- State MSE
- Derivative loss
- Simulation loss
- Complexity penalty
- Validation splits

---

## Phases

### Phase 1 – Stable Core

**Status:** DONE  
**Completed on:** 20.04.2026

- EvoGrow stable
- GP baseline
- discover() pipeline stable
- stopping unified
- benchmarking pipeline groundwork

**Completed work**
- Fixed the major inconsistency bug between optimization loss and final simulation loss.
- Verified `loss(search) == loss(simulate)` on stable synthetic tests.
- Implemented stable `discover()` orchestration.
- Implemented and validated:
  - `GPStructureSearch`
  - `EvoGrow` baseline
- Added shared stopping logic (`should_stop`).
- Added sanity-check reporting and final simulation validation.
- Stabilized package/module structure:
  - include order fixed
  - precompile issues resolved
  - method overwrite issues resolved
- Added structured logging infrastructure:
  - common logger module
  - timestamps
  - elapsed time
  - algorithm/optimizer level logging
- Golden test working:
  - harmonic oscillator
  - clean recovery of linear structure

**Notes**
- Phase 1 is considered complete enough for research work.
- Further refinements are allowed, but Phase 1 is no longer the focus.

---

### Phase 2 – EvoGrow Variants

**Status:** IN PROGRESS

#### v1: simple growth
**Status:** DONE  
**Completed on:** 20.04.2026

- Flat term-wise growth over available basis terms.
- Acts as the first EvoGrow baseline.

#### v2: complexity tiers
**Status:** IN PROGRESS  
**Started:** 21.04.2026

**Current state**
- `StagedPolynomialBasis` implemented with 5 stages:
  1. linear
  2. self-quadratic
  3. cross terms
  4. self-cubic
  5. trigonometric
- EvoGrow v2 implemented with staged basis release.
- EvoGrow v2.1 implemented with stage-aware child generation:
  - after stage unlock, children preferentially include terms from the new stage

**Current findings**
- On simple linear systems, EvoGrow v2 remains in Stage 1 as desired.
- On Lotka–Volterra, EvoGrow v2 improves significantly after Stage 2.
- However, current stage progression does not yet reliably recover the mechanistically correct cross-term structure.
- This is now a core research topic, not just an implementation issue.

#### v2.2: stage progression policy
**Status:** NEXT

Planned focus:
- refine when stages are opened
- ensure newly opened stages are actually exploited
- prevent premature convergence to surrogate structures
- define explicit per-stage search behavior

#### v3: equation-wise
**Status:** NOT STARTED

Planned idea:
- discover equations separately or semi-separately
- compare with full-system discovery
- possibly use teacher forcing or hybrid simulation

#### v4: coupling-aware
**Status:** NOT STARTED

Planned idea:
- explicitly prioritize discovery of coupling terms
- bias search using system-level structure information

---

### Phase 3 – Benchmarking

**Status:** STARTING NOW

Planned benchmark axes:
- Noise
- Sampling
- Coupling strength
- Dimensionality

**Immediate benchmark plan (first benchmark pack)**
1. Harmonic oscillator  
   - purpose: stable linear sanity test
   - expected useful stage: Stage 1

2. Lotka–Volterra  
   - purpose: essential cross-coupling benchmark
   - expected useful stage: Stage 3

3. Van der Pol oscillator  
   - purpose: nonlinear self-interaction benchmark
   - expected useful stage: Stage 2 and/or Stage 4

4. Duffing oscillator  
   - purpose: cubic nonlinearity benchmark
   - expected useful stage: Stage 4

**Benchmark goal**
- Compare:
  - GP baseline
  - EvoGrow v1
  - EvoGrow v2.x
- Track:
  - final loss
  - recovered structure
  - stage reached
  - runtime
  - number of invalid/unstable evaluations

---

### Phase 4 – Paper 1

**Status:** NOT STARTED

Target:
- EvoGrow baseline vs GP/SINDy

Likely scope:
- simple systems
- staged growth concept
- first systematic benchmark comparison

---

### Phase 5 – Advanced Methods

**Status:** NOT STARTED

- Error-guided growth
- Backtracking
- Hybrid search
- Multi-hypothesis models

---

## Paper Plan
1. EvoGrow baseline
2. Adaptive growth strategies
3. Systematic benchmark study

---

## Design Principles
- Modular
- Reproducible
- Interpretable
- Minimal complexity
- No unnecessary features

---

## Non-Goals
- No premature GPU work
- No UI
- No PDE expansion (yet)

---

## Guiding Rule
Every change must support a research hypothesis.

---

## Current Priorities (21.04.2026)

1. Define EvoGrow v2.2 formally
2. Build first 3–4 ODE benchmark pack
3. Compare GP vs EvoGrow v1 vs EvoGrow v2.x
4. Analyze when staged growth finds the structurally correct model vs a surrogate approximation
