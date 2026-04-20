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
- EvoGrow stable
- GP baseline
- discover() pipeline stable
- stopping unified
- benchmarking pipeline

### Phase 2 – EvoGrow Variants
- v1: simple growth
- v2: complexity tiers
- v3: equation-wise
- v4: coupling-aware

### Phase 3 – Benchmarking
- Noise
- Sampling
- Coupling strength
- Dimensionality

### Phase 4 – Paper 1
EvoGrow baseline vs GP/SINDy

### Phase 5 – Advanced Methods
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
