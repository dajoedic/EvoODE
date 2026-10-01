# Design note — a data-derived stopping and promotion criterion for the next EvoGrow version

**Status: proposal (Track S, S-03), 2026-10-01. Not part of Paper 1** — Paper 1's termination
(`loss_tol = 1e-8`, 30 levels) is frozen (`docs/paper1_phaseC_benchmark_plan.md` §9.1). Evidence:
`DIARY.md` 2026-10-01, the two stopping retrospectives. Nothing here is decided; the user decides at
a gate.

## 1. The problem, measured

Under noise the loss cannot fall below the noise variance, so `loss_tol = 1e-8` is unreachable and
the search runs until the level budget or a deadline ends it. Six noisy cells on three systems
(1, 17, 24) show the same shape:

- the best loss is reached at level 1–5, after which up to 19 levels add nothing or add terms that
  fit noise (system 1 at (0.05, 0.5) ends **below** the estimated noise floor with five terms where
  the truth has two);
- the cost is dominated by these silent late levels — ×193–712 loss evaluations on system 1, over
  an hour on system 24 whose clean cell took 33 s;
- the stage cap does not help: noise turns finite caps into `nothing` (system 17).

Two failure kinds are distinct and must not be conflated:

| kind | example | repaired by a stop? |
|---|---|---|
| **late growth** — extra terms bought by later stages fitting noise | system 1 and 17 at (0.05, 0.5) | yes, if the stop fires at the right level |
| **intra-stage selection** — an extra term chosen inside stage 1 | system 24, both conditions | no |

## 2. Design principles (inherited, binding)

1. **Positive evidence, data-derived, no system identity** — the stage-cap rules (WP-C1–C5).
2. **No constant chosen after seeing results** — WP-V1, WP-N2. Every constant below is fixed before
   the first test run and reported as a human choice where it is one.
3. **Two roles stay separate** — evaluation is trajectory-based; any derivative-space estimate may
   bound or gate the search, never carry model quality (`PAPER_1.md`, Method Positioning).
4. **No global level budget** — WP-B1 measured it and rejected it.

## 3. Proposal

**(A) Termination: stop at the estimated noise floor.**
Estimate `σ̂²_k` per state component from the observed data alone — residual variance of a local
cubic fit (the cap's estimator family), with its degrees-of-freedom correction. Terminate when

```text
best_loss <= c_floor * mean_k(σ̂²_k)
```

with `c_floor = 1` as the a-priori choice (no tuning). On clean data `σ̂² ≈ 0` and the rule reduces
to today's `loss_tol`, so the clean behaviour — and Claim B's evidence — would be unchanged by
construction; that is a testable acceptance criterion.

**(B) Termination guard: residual whiteness.** Before (A) fires, additionally require that the
residuals of the best model are not distinguishable from white noise (runs test or Ljung–Box at a
fixed level α = 0.05). Purpose: (A) alone stops a model that is merely *as bad as* the noise; (B)
asks whether structure is left. If (A) holds and (B) fails, the search continues.

**(C) Promotion: information criterion.** A new stage's best model replaces the incumbent only if
it lowers BIC computed with the estimated noise variance:

```text
BIC = n * log(MSE) + p * log(n)
```

This targets late growth directly. It does **not** address intra-stage selection; extending the
same penalty to candidate selection within a stage is the follow-on question, and it touches the
search operators, which are outside this note.

## 4. What must be shown before (A)–(C) become a method version

1. **Estimator quality over many systems.** Today: biased high by ×1.3 in 6 of 6 cells and ×1.77
   once. A high estimate stops early; for steep or stiff trajectories it may stop before the true
   structure is reached. Measure on all 51 dim-1/2 systems × noise levels, offline, from the
   exported data — no search needed.
2. **Retrospective on full heartbeats** (WP-N35 provides per-level structure): for every noisy cell
   that exists, where would (A), (A)+(B), (A)+(B)+(C) have stopped, with which structure, at what
   cost. Zero compute.
3. **Clean-data neutrality:** on C-1 cells the new rules must return the identical result — a
   bit-identity control like stage 0.
4. Only then a prospective test, staged like C-6, with its own identifier.

## 5. Constants and their status

| constant | value | status |
|---|---|---|
| `c_floor` | 1 | a-priori, not tuned |
| local-fit window / degree | 9 points / cubic | inherited from the stage cap |
| whiteness test level α | 0.05 | conventional, a human choice, reported as such |
| BIC penalty | `log(n)` | definitional |

## 6. Where it would go

The next EvoGrow version and Paper 2's method contribution, next to the bound question (C-8) and
the trajectory-overfitting direction (`CLAUDE.md`, "Open, not scheduled"). Placement in
`docs/phd_thesis_arc.md` at the status review.
