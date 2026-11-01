# Side project WISP — protocol for Q8: initial-state estimation, coefficient bound, surrogate systems, ablations

**DRAFT 2026-11-01 — not frozen.** Gate G1 of the WISP plan (CLAUDE.md, "WISP paper — the fixed plan"): the user
approves or changes this protocol before any Q8 number is computed. Parts before: Q5 (`_q5.md`, grid aggregated
2026-11-01), Q7 (`_q7.md`, fits running; interim look 2026-11-01 in `DIARY.md`).

## 1. Question

Q8 fixes the last three open design choices of WISP before the final run Q9, and measures the two things Q5/Q7 could
not:
1. **Variant C:** does estimating the initial state jointly with the coefficients (the user's commitment of
   2026-10-27) keep or improve the result against variant A (fit from the first noisy observed sample)?
2. **Bound 1000:** does the looser coefficient bound `[-1000, 1000]` (C-8 B-03: the next version's start by the frozen
   rule) keep the result on the systems feasible under bound 10, and what does it bring on 54–59?
3. **Surrogate systems:** how does WISP do on the systems the basis cannot represent exactly, against the
   baselines, on R² alone? Q8 covers the 30 surrogates of dim 1/2; the other 3 (53, 60, 62) come with Q9.
4. **Ablations:** what each WISP component contributes (FoBa backward step, weak-form start, trajectory refit).

## 2. Path end — conditional on G-Q7

Q8 uses the path end that gate G-Q7 selects by the frozen Q7 §5 rule: the Q7 significance test if Q7 passes, else
the 6-term cap. **On surrogate systems only the Q7 rule is possible** — the 6-term cap is derived from the true
equation size, which a surrogate does not have. If Q7 fails G-Q7, the surrogate arm runs with the Q7 rule anyway and
is labelled as such. Everything else of the pipeline is Q5 §3 verbatim: weak design and basis as WP-FA2, FROLS step,
FoBa (ν = 0.5), every path state a candidate, one `fit_parameters` call per candidate from its weak start,
`max_fit_attempts = 1`, size rule (c) trajectory BIC primary, (a) weak BIC and (b) EvoGrow objective reported.

## 3. The arms

| Arm | Initial state in fit and selection | Coefficient bound |
|---|---|---|
| **A10** | first observed sample (Q5/Q7) | 10 |
| **C10** | estimated, start = first observed sample, unbounded | 10 |
| **A1000** | first observed sample | 1000 |
| **C1000** | estimated, as C10 | 1000 |

Variant C adds d initial-state parameters per candidate (d = dimension), fitted jointly with the coefficients in the
same single `fit_parameters` call. They are the same for every candidate of a cell, so the BIC penalty count
(coefficients + d) does not change the ranking. Evaluation is unchanged: reconstruction and generalization from the
clean IC on the clean grid, as the baselines; additionally reported (diagnostic, never used for a choice): the
training MSE simulated from the estimated initial state, and the distance of the estimated to the clean initial state.

A10 on exact systems reproduces Q7 on the same cells; those records are reused (control §8), not refitted.

## 4. Data

C-6 export `phase_c_c6_data_conditions_5dd1df8`, unchanged. Units (system, training IC), both ICs.

| Block | Systems | Conditions | Arms |
|---|---|---|---|
| **dim 1/2** | all 51 (21 exact, 30 surrogate) | (σ, ρ) ∈ {0.01, 0.05} × {0, 0.5}, realization 1, plus (0, 0) | A10, C10, A1000, C1000 |
| **dim 3 sample** | 52, 61 (feasible under 10); 54–59 (infeasible under 10) | same | A1000, C1000; A10 (reused from Q7) and C10 on 52, 61 only |
| **ablations** | dim 1/2, all 51 | same | on C1000 (the intended final configuration) |

Not in Q8: the dim-3 surrogates 53, 60 (R3 decides on dim 1/2 only; they come with Q9), dim 4 (62, 63),
realizations 2–3, σ ∈ {0.02, 0.03, 0.04} — they come with Q9. 54–59 are kept complete: choosing only the systems the
C-8 oracle could fit unbounded (57, 58) would be a selection on results; the probe guards the cost.
Cells: dim 1/2 102 units × 5 = 510 per arm; dim 3 sample 16 units × 5 = 80.

## 5. Ablations (on C1000, dim 1/2)

- **No FoBa:** growth path without the backward step (forward FROLS only).
- **Random start:** every candidate fitted from `0.1 · randn` instead of its weak-form start, one attempt (the EvoGrow
  default start; Q3 measured this on the true structure only).
- **No refit:** the weak-form coefficients are simulated directly, no trajectory fit; size rule (c) on those
  trajectories.

Report only, no adoption rule: an ablation explains a component, it does not decide one. If G2 does not adopt C1000,
the ablations are rerun on the adopted configuration (dim 1/2 only, ~10–50 core-h each).

## 6. Metrics and references

As Q5 §4–§5: exact systems — raw and pruned exact structure, R² > 0.9 reconstruction and generalization
(variance-weighted primary, arithmetic reported), **always structure and R² together**; surrogate systems — R² > 0.9
reconstruction and generalization only (Design Principle 8, never mixed with exact systems). Cost: candidates, fits,
loss evaluations, ODE solves. References on the same cells, existing data, no new baseline run: SINDy, Weak-SINDy,
E-SINDy (WP-N47, matching library, better threshold per stratum × σ × metric) and the WSINDy port (W1 on ρ = 0,
W1-interp on ρ = 0.5; preliminary until Q5-W §5.5 passes).

## 7. Adoption rules (fixed now, before any Q8 number)

Margin as everywhere since plan §9.4d: **5 percentage points**, per stratum, pooled over the four noisy conditions;
metrics pruned exact structure **and** R² > 0.9 generalization on exact systems, R² > 0.9 generalization on surrogate
systems. **Decided on dim 1 and dim 2 only** (300–400 noisy cells per arm each). The dim-3 sample is reported, not
decided on: with 32–80 noisy cells per arm, 5 pp are 2–4 cells, and a single cell would decide.

Order: R2 first, then R1 at the adopted bound — one comparison per rule, not two.

- **R2 — bound 1000.** Adopted unless C1000 is worse than C10 by more than 5 pp on any metric in dim 1 or dim 2.
  (On 54–59 bound 10 is infeasible by construction; reported only.)
- **R1 — variant C.** At the bound adopted by R2, C is adopted (the user's commitment of 2026-10-27; a principled
  choice, not a performance one, hence non-inferiority) unless it is worse than A by more than 5 pp on any metric in
  dim 1 or dim 2. Then the fallback is A, declared (CLAUDE.md plan: "variant C or bound 1000 harm").
- **R3 — surrogates.** WISP is "clearly behind" on surrogates if, in dim 1 or dim 2, the adopted arm is more than
  5 pp below the **best** of the four references on R² > 0.9 generalization. Then the user decides whether the claim
  is narrowed to exactly representable systems (plan deviation list). Otherwise the surrogates enter Q9 as planned.
- **Not changed by Q8:** size rule (c) stays primary. (In Q5 rule (b) was far better on dim-2 structure; switching
  now would be a choice after seeing the data. It is reported, not adopted.)

## 8. Controls

- A10 on exact dim-1/2 cells: candidate lists and chosen models identical to Q7 on the same cells (reused records;
  the support and `p0` of every reused state equal).
- C with the initial-state parameters frozen at the first observed sample reproduces A bit-identically on one cell per
  stratum (laptop smoke) — the C code path changes nothing else.
- Bound 1000 with all coefficients inside [−10, 10] at the optimum: identical support to bound 10 on the same smoke
  cells is **not** required (C-8: looser bounds change optimizer paths) — reported.
- Per-cell `observed_data_sha256` equal to WP-N47; optimizer settings fingerprint recorded per arm; Q7 path builder
  bit-identical to its frozen paths on exact cells.

## 9. Execution and cost

Planning from the measured Q5 fit times (solve time, wall-clock, planning only): noisy cell dim 1 0.003 h, dim 2
0.15 h, dim 3 feasible 5.3 h (median 2.0); Q7 paths are a third of Q5's candidates; variant C ×1–2 unmeasured;
54–59 under bound 1000 unmeasured for WISP (Q5 protocol: 3–9 h per cell projected).

| Block | Cells | Core-h (range) |
|---|---|---|
| dim 1/2, 4 arms | 4 × 510 | 60–300 |
| dim 3 sample: 52/61 under C10, A1000, C1000 (A10 reused); 54–59 under A1000, C1000 | 60 + 120 | 600–1,700 |
| ablations, 3 × 510 | 1,530 | 30–150 |
| **total** | | **~700–2,150 core-h ≈ 1,050–3,250 €** |

Orion, indexed Job, shards in descending planned cost, no deadline; a probe of one unit per block first (as Q5),
then the user decides the grid. Implementation: Codex (Julia variant C in the Q5 runner as an option, bound as a
setting, surrogate paths through the Q7 builder, ablation switches), Claude parses and smoke-tests on the laptop, the
user pushes to GitLab for the image.

## 10. Decided by the user 2026-11-02 (before G1)

1. dim-3 sample: 52, 61, 54–59 complete; the surrogates 53, 60 move to Q9.
2. Ablations on C1000; rerun on the adopted configuration if G2 does not adopt it.
3. R1 non-inferiority; R1/R2 decided on dim 1/2 only, R2 before R1, one comparison each.

Remaining for G1: the user reads the whole protocol once and approves it; then it is frozen.
