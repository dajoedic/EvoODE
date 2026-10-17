# Side project "residual-guided growth" — protocol for Q4 (model size without oracle)

**Frozen 2026-10-17, approved by the user, before any Q4 number was computed.** Part 3 of the side project; parts 1 and 2: `docs/sideproject_residual_growth_protocol.md` (`e61f48f`),
`docs/sideproject_residual_growth_protocol_q3.md` (`c81e7c6`). User decisions 2026-10-17: candidates from a growth
path plus an upper bound; success measured against EvoGrow C-1 and Weak-SINDy separately, decision against
Weak-SINDy; the 30 exact systems. Thresholds are human design choices, not derived from data.

## 1. Question

Without knowing the true size, does a simple pipeline — grow along the weak residual, fit each model from its weak
start, let the trajectory decide the size — recover the structure and generalise, compared with EvoGrow C-1 and
Weak-SINDy on the same cells? And does the trajectory check add anything over choosing the size in the weak space?

Clean data only (σ = 0). Noise is the next step and only if this one works.

## 2. Units, data, strata

- Unit: (system, training IC) of the 30 exact systems — 60 units; the pipeline is deterministic, so one run per unit.
  The other IC is the test trajectory (generalisation), never used for any choice.
- Weak design, solver and basis as WP-FA2 (uncentred, constant as ordinary column, orthogonal-factorisation least
  squares, full basis of the dimension, stages ignored).
- Strata: primary `dim1`, `dim2`, `dim3_feasible` (52, 61); reported only `dim3_bound_infeasible` (54–59), `dim4` (63).

## 3. The pipeline

**3.1 Growth path (the method).** Start from the empty model. Each step adds the single (equation, term) with the
largest **normalised** weak gain ΔSSE_eq / ‖b_eq‖² under a joint least-squares refit of that equation (FROLS step,
compared across equations through the normalisation — the R4 quantity ρ). After every addition a **backward check**
in the FoBa style (Zhang 2011, adaptive forward-backward greedy): remove the term of any equation whose removal
raises that equation's normalised SSE by less than ν = 0.5 times the normalised gain of the last addition; repeat
until no term qualifies. ν = 0.5 is the published default, not tuned. The path ends when every equation has 6 terms
or its normalised SSE is below 1e-14, whichever comes first (a length cap, not a selection rule; 6 is twice the
largest true equation size in the 30 systems — the only use of the truth in the design, declared).

Every distinct model on the path (each state after the backward check) is a **candidate**.

**3.2 Trajectory check.** Each candidate is fitted exactly like Q3 W1: weak-start coefficients, one
`fit_parameters` call with `build_reference_optimizer(max_fit_attempts = 1)`, bound 10. It is simulated on the
training trajectory (MSE, R²) and, for reporting only, from the test IC (generalisation R²).

**3.3 Size rules** — each picks one candidate per unit:
- **(c) trajectory BIC — primary:** N·log(MSE) + k·log(N), N = number of samples × dimension of the training
  trajectory, k = number of active terms. Parameter-free.
- **(a) weak BIC — reference:** Σ over equations of n·log(SSE_eq/n) + k_eq·log(n), n = weak design rows (the WP-T1b
  formula). No simulation needed for the choice; shows what the trajectory check adds.
- **(b) EvoGrow objective:** MSE + 1e-3·k (today's absolute λ).

Candidates whose fit ends at the sentinel loss or diverges are never chosen by (b)/(c).

**3.4 Upper bounds, reported only:** the path model whose size equals the true size (oracle size on the path); and
weak best-subset at the true size per equation (Q1, 100 % on the primary strata).

## 4. Metrics

Per unit and chosen model: raw exact structure, pruned exact structure (the project's pruning rule
`max(1e-6, 1e-3·max_abs)` per equation, as in the campaign), R² > 0.9 reconstruction and generalisation with the
**same R² definitions as the canonical comparison table** `hierarchy_n47_e935c37` (variance-weighted primary,
arithmetic reported), number of candidates and total loss evaluations.

References on the same (system, IC) units, read from `hierarchy_n47_e935c37/per_run.csv`, clean rows only:
- **EvoGrow C-1:** three seeds per unit (180 cells).
- **Weak-SINDy:** ten configurations × three realisations per unit; per configuration the rate over its 180 rows;
  the **median configuration** and the **range** (min–max) over the ten are reported.

## 5. Rules (per primary stratum, primary size rule (c))

| Rule | Criterion | Question |
|---|---|---|
| R7 — progress | pruned exact structure ≥ C-1 rate + 10 pp **and** generalisation rate ≥ C-1 rate | Better than today's EvoGrow? |
| R8 — standing (decision) | pruned exact structure ≥ Weak-SINDy median-configuration rate **and** generalisation rate ≥ Weak-SINDy median-configuration rate | At least on par with the established method? |
| R9 — value of simulation | (c) pruned exact structure ≥ (a) pruned exact structure | Does the trajectory check add anything over the weak space? |

Counting rules, no p-values. Rates compare units (ours) with cells (C-1, Weak-SINDy); comparable because the
pipeline is seed-free. Reported beside every rule: raw structure, reconstruction, rules (a) and (b), the Weak-SINDy
range, cost, and the upper bounds.

## 6. Reading (fixed in advance)

- **R8 passes** → the combination is at least on par with Weak-SINDy on both metrics at σ = 0 → go to noise.
- **R7 passes, R8 fails** → a clear improvement of EvoGrow, not yet competitive → find where it loses (size choice,
  path, fit) before noise.
- **R7 fails** → the pipeline does not beat today's EvoGrow without oracle; the size choice is the bottleneck.
- **R9 fails** → the trajectory check adds nothing over the weak space; the simulation step is not justified by
  structure recovery (generalisation reported separately).

## 7. Controls

- Path determinism: two runs of the path builder give identical candidate lists.
- One unit with the true structure forced as the only candidate reproduces the Q3 W1 loss bit-identically.
- Every candidate's fit uses the same optimizer settings as Q3 (fingerprint of the settings recorded).
