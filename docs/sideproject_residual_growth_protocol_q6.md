# Side project "residual-guided growth" (WISP) — protocol for Q6: a data-derived path end

**DRAFT 2026-10-31, not frozen, not approved.** Part 6 of the side project; Q5: `_q5.md` (`f737939`), Q5-W: `_q5w.md`.
Method name WISP (Weak-form Incremental Structure Pursuit), user 2026-10-31.

**Declared before drafting:** the Q5 results have been looked at provisionally (`DIARY.md` 2026-10-31), including D1:
under noise every path ends at the 6-term cap. Nothing in this protocol is chosen from per-cell Q5 numbers; every
constant below is fixed in this text before the first evaluation and is a human choice where it is one.

## 1. Question

Can the truth-derived path end (6 terms per equation) be replaced by a stop that follows from the observed data alone,
such that the stop **never truncates a true term** — on all exact systems and all C-6 noise levels — and, at σ = 0,
reduces to today's numerical-zero stop?

The size choice stays with trajectory BIC (rule (c)); Q6 only decides where the candidate list ends.

## 2. The stop rule (fixed a priori)

Per equation, along the existing WISP path (unchanged: FROLS step, FoBa check ν = 0.5, weak design as Q4/Q5):

1. **Noise estimate from the observed data only.** Per state component, residuals of a local cubic fit over a sliding
   window of 9 observed points (the stage-cap estimator family), degrees-of-freedom corrected. Because the C-6 noise is
   multiplicative, the per-point variance is modelled as σ̂²_rel · x̂(t_i)², with x̂ the local fit and σ̂²_rel estimated
   as the pooled variance of residual / x̂ — **[open choice A: relative model as stated, or a homoscedastic σ̂²_k as in
   `docs/design_stopping_criterion.md`; the relative model uses knowledge of the C-6 noise model, which a reviewer may
   call oracle information]**.
2. **Propagation into the weak space** (the WENDy idea, to first order): the expected weak SSE of the true model is
   `F_eq = Σ_rows Σ_i (w_i · φ'_row(t_i))² · σ̂²_i` with the actual quadrature weights w_i on the observed grid —
   the derivative-of-test-function term only. **[open choice B: include the linearised right-hand-side term
   ∂f/∂x · ε with the current path state's coefficients, as WENDy does; more faithful, but then the floor depends on
   the candidate.]**
3. **Stop:** the path of an equation ends at the first state whose `weak_sse ≤ c · F_eq`, with **c = 1** (expected
   value, not tuned). If it never fires, the path runs to the full basis of that dimension (6 / 12 / 19 / 27 terms) —
   the grammar, not the truth, is then the limit.
4. At σ = 0, σ̂² is at round-off level and the rule reduces to the existing `normalised SSE < 1e-14` stop; checked,
   not assumed (§5).

## 3. Stage 1 — retrospective, zero compute (laptop)

Input: `outputs/sideproject_q5_inputs/q5_grid_paths.json` (1,632 cells, `weak_sse` per path state and equation) plus
the C-6 export for the noise estimate. No fit, no simulation. Per equation × cell, classify the stop position:

- **T truncation** — the stop fires before every true term is on the path (violation);
- **E exact** — fires at the first state containing every true term;
- **O overshoot** — fires later, with k − k_true extra terms;
- **N not within the recorded path** — would continue past the 6-term cap (needs stage 2);
- where the true support is never on the recorded path (Q5 D3), report true-term recall at the stop instead.

Plus: the estimator check — σ̂_rel against the true σ per condition (quantiles), as Track S item 1 asked for.

**Acceptance (fixed now):** T = 0 over all cells, strata and conditions. Any truncation means the rule is rejected as
stated — no constant is adjusted afterwards; a revised rule needs a revised protocol. E, O, N are reported, not judged.

## 4. Stage 2 — only if stage 1 passes and N > 0 (Orion)

Paths of the N equations are extended past the cap up to the stop (laptop, weak space only), and only the new path
states are fitted with the unchanged Q5 fit machinery on Orion, within the free cores. Rule (c) is re-run on the full
candidate list; reported beside Q5 with the same metrics (both always: structure and R² > 0.9), D1–D5, and cost.
Cost projection in counts before the run, from Q5's per-candidate cost.

## 5. Controls

- σ = 0 cells: stop position identical to Q5's numerical-zero stop in every equation.
- Determinism: the estimator and the floor are pure functions of the observed data; two runs bit-identical.
- `observed_data_sha256` per cell equal to the Q5 records.

## 6. Not in Q6

Joint initial-state estimation (variant C, committed in the Q5 amendment of 2026-10-27) has its own protocol. The
whiteness guard and the information-criterion promotion of `docs/design_stopping_criterion.md` (B), (C) are not tested.
