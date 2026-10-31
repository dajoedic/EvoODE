# Side project "residual-guided growth" (WISP) — protocol for Q6: a data-derived path end

**Frozen 2026-10-31, approved by the user, before any Q6 number was computed.** Part 6 of the side project; Q5:
`_q5.md` (`f737939`), Q5-W: `_q5w.md`. Method name WISP (Weak-form Incremental Structure Pursuit), user 2026-10-31.

**Declared:** the Q5 results have been looked at provisionally (`DIARY.md` 2026-10-31), including D1: under noise
every path ends at the 6-term cap. Nothing here is chosen from per-cell Q5 numbers; every constant below is fixed in
this text before the first Q6 evaluation and is a human choice where it is one. User decisions 2026-10-31: noise
variance estimated locally without a noise model; primary floor without the right-hand-side term, the floor with it as
a secondary rule; Q6 before variant C.

## 1. Question

Can the truth-derived path end (6 terms per equation) be replaced by a stop that follows from the observed data alone,
such that the stop **never truncates a true term** — on all Q5 cells (30 exact systems minus the bound-infeasible
dim-3 ones, all C-6 conditions, three realizations) — and leaves the σ = 0 paths unchanged?

Size choice stays with trajectory BIC (rule (c)); Q6 decides only where the candidate list ends.

## 2. The weak space, as it is (no change)

The WISP weak design (`build_design(..., 'weak', ...)`, `analysis/exploratory/term_relevance/term_relevance.py`) is an
integral form over windows of 1, 2, 4, 8, 16 observed samples: row r has target `b_r = x(t_stop) − x(t_start)` and
design `G_r = trapz(θ(x), t)` over the window, on the actual observed times. Growth path: `growth_path` in
`build_sideproject_q4_paths.py` (joint over equations, FROLS step, FoBa check ν = 0.5), unchanged except for the end
condition in §3.

## 3. The stop rule (fixed a priori)

1. **Local noise variance, no noise model.** Per state component j and observed point i: fit a cubic by least squares
   to the 9 observed points centred on i (at the edges the first / last 9 points), in the actual times; take the
   residual at i corrected by its leverage, `e_i / sqrt(1 − h_ii)`. The variance at i, σ̂²_ij, is the mean of the
   corrected squared residuals over the 21 observed points centred on i (edges truncated). Constants 9 (inherited from
   the stage-cap estimator) and 21 are human choices.
2. **Primary floor (no right-hand-side term).** Target noise of row r is `ε_stop(r) − ε_start(r)` in the equation's
   state; its covariance `C_b` follows from σ̂² (rows sharing an endpoint are correlated). For the current support S of
   the equation, the floor is the first-order expected residual of a correct model,
   `F(S) = trace((I − P_S) C_b)`, with `P_S` the projector onto the columns of G in S.
3. **Secondary floor (with right-hand-side term).** As 2, but the row noise also carries the linearised design noise
   `− Σ_i w_ri · (∂f_S/∂x)(t_i) · ε_i` over all state components, with f_S evaluated at the path state's weak
   least-squares coefficients and w_ri the trapezoid weights. Reported only; does not decide acceptance.
4. **End condition.** In `growth_path`, an equation stops growing when `sse(S) ≤ F(S)`, **or** its normalised SSE is
   below 1e-14 (unchanged numerical-zero stop), **or** S equals the full basis of its dimension (6 / 12 / 19 / 27).
   The 6-term cap is removed. If FoBa would repeat a model, the path ends at the state before (end reason `cycle`)
   instead of raising.

## 4. Stage 1 — rebuilt paths in the weak space (laptop, no fit, no simulation)

Paths are rebuilt for all 1,632 Q5 cells with the §3 end condition, once with the primary and once with the secondary
floor, and once with only the numerical-zero and full-basis stops (**reference path**, needed to tell a stop failure
from a path failure). Truth: `studies/regression/phase_c_support.json`. Per equation × cell:

- **T truncation:** the reference path contains a state whose support holds every true term of the equation, but the
  stopped path ends before reaching such a state — **violation**;
- **R reached:** the stopped path contains such a state; report the number of extra terms at the path end and at the
  first state holding the truth;
- **P path failure:** no state of the reference path holds every true term — not counted against the stop; report
  true-term recall at the stopped path end;
- path length, end reason (`floor`, `sse`, `full`, `cycle`), and the number of path states above 6 terms.

Plus the estimator check: σ̂ per state against the true per-point noise level of the C-6 model (σ · |x_clean|),
quantiles per condition — the Track S item 1 question.

**Acceptance (fixed now): T = 0 under the primary floor**, over all cells. Any truncation rejects the rule as stated;
no constant is adjusted afterwards, a revised rule needs a revised protocol. R, P and the secondary floor are reported,
not judged.

## 5. Stage 2 — fits of the new path states (Orion, only after stage 1 passes and the user opens it)

Only the path states that Q5 did not fit (states beyond 6 terms, and any state that differs from Q5's) are fitted with
the unchanged Q5 fit machinery (Julia, one fit from the weak start, bound 10, first observed sample as initial state).
Rule (c) is re-run on the stopped candidate lists; reported beside Q5 with the Q5 metrics — structure **and** R² > 0.9,
always both — D1–D5, and cost in counts. Cost projected in counts before the run.

## 6. Controls

- **σ = ρ = 0 cells:** stopped primary path identical to the Q5 path (candidate list and weak coefficients); any
  deviation is reported per cell and, if it truncates, counts as T.
- **Reference path vs Q5:** on every cell, the reference path's first states up to Q5's end are identical to the Q5
  candidate list where Q5 ended by `sse`; where Q5 ended at the cap, its prefix up to the cap is identical.
- Determinism: two runs bit-identical; `observed_data_sha256` per cell equal to the Q5 records.

## 7. Not in Q6

Joint initial-state estimation (variant C) has its own protocol and runs after Q6 stage 1, on the final candidate
lists. The whiteness guard and the information-criterion promotion of `docs/design_stopping_criterion.md` (B), (C) are
not tested.
