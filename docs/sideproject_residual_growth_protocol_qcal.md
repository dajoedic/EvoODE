# Side project WISP — protocol Q-Cal: calibration of the χ² stop

**Frozen 2026-11-08 before any Q-Cal number was computed**, on the user's decision after the external review of the
manuscript draft (`paper/wisp/`, review point 1: "the statistical stop needs a stronger justification"). Report only:
Q-Cal changes nothing in WISP, decides nothing about the method, and is not an adoption gate. Laptop, no fit, no
simulation.

## 1. Question

The Q7 stop (`docs/sideproject_residual_growth_protocol_q7.md` §2) treats `g_j / n_j` — weak gain of term j over its
expected gain under pure measurement noise — as χ²₁ and stops below 6.635 (α = 0.01). Its noise model covers the noise
in the weak targets `b` only, not the noise that enters the design `G` through the library evaluated on noisy states,
and it uses the estimated noise variance σ̂². How well calibrated is the test, and where does it break?

## 2. Units and data

The Q9 cells (`outputs/sideproject_q9_inputs/grid/q9_paths.json`, data hash checked per cell against the C-6 export)
of the **30 exact systems** with σ > 0: 30 systems × 2 training ICs × 10 noisy conditions (σ ∈ {0.01, …, 0.05} ×
ρ ∈ {0, 0.5}) × 3 realizations = **1,800 cells**. Unit of analysis: (cell, equation) with true support S* from
`studies/regression/phase_c_support.json`. Weak design, noise estimator and floor exactly as frozen in Q6/Q7
(`build_design(..., 'weak')`, `estimate_noise_variance`, `projected_noise_floor` with the primary operator).

## 3. Quantities (all at the true support, no path)

For each (cell, equation):

- **N1 — false alarms.** For every term j ∉ S*: `r_j = (SSE(S*) − SSE(S* ∪ {j})) / (F(S*) − F(S* ∪ {j}))`.
  Exceedance rate `P(r_j ≥ 6.635)`. Under the test's own model this is 1 % per pair.
- **N2 — stop at the truth.** Share of equations with `max_{j ∉ S*} r_j < 6.635`, i.e. the stop would fire exactly at
  the true support. Beside it the nominal value `0.99^(p − |S*|)` under independence.
- **P1 — power.** For every true term i ∈ S*: `r_i` of adding i to `S* \ {i}`. Detection rate `P(r_i ≥ 6.635)`.
- **Oracle-variance arm.** N1, N2, P1 recomputed with the true per-point noise variance of the C-6 model,
  `(σ · x_clean(t_i))²` at the observed times, instead of σ̂². This separates estimator error from the error of the
  first-order noise model (design noise).
- **Collinearity.** For N1, each pair is binned by the R² of the unit-normalized column j regressed on the columns S*:
  < 0.9, 0.9–0.99, ≥ 0.99.
- The secondary threshold 10.828 (α = 0.001) is reported beside 6.635.

Strata: dimension (dim 1, dim 2, dim 3 = 52, 61 and 54–59 separately, dim 4) × σ × ρ; pooled over realizations and
ICs. Systems are clusters: rates carry a 95 % cluster-bootstrap interval over systems.

## 4. Reading (fixed now, no rule)

- N1 ≈ 1 % under both variance arms: the test is calibrated as stated.
- N1 near 1 % with oracle variance but not with σ̂: the deviation comes from the noise estimator.
- N1 above 1 % under both arms: the first-order model (no design noise) is liberal; spurious terms pass the test and
  the path relies on FoBa and the trajectory BIC to discard them. Reported, not repaired (WISP simplicity guardrail).
- P1 measures how often a true term is visible against noise at all; a low P1 bounds structure recovery from above,
  independently of path and selection.

## 5. Controls

Per-cell `observed_data_sha256` equal to the Q9 path file; the floor function is imported unchanged from
`build_sideproject_q6_paths.py`; the true support mapped by index and checked by term name against `phasec_basis`.
