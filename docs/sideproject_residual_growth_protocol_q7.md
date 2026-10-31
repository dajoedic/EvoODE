# Side project WISP — protocol for Q7: path end by a significance test on the gain

**Frozen 2026-10-31, approved by the user ("ja mach ma"), before any Q7 fit was computed.** Parts before: Q5
(`_q5.md`), Q5-W (`_q5w.md`), Q6 (`_q6.md`, rule rejected: T = 591).

**Declared:** the Q7 *paths* were computed exploratorily the same evening (`DIARY.md` 2026-10-31,
`analysis/exploratory/sideproject_q7_gain_test/`), at the two thresholds below, and their truth-on-path rates were
looked at: exact truth on the path under noise equal to the 6-term cap within 2 points in every stratum, half the
path length. No fit, no R², no chosen model of Q7 has been seen. The threshold was set before that run and is not
changed.

## 1. Question

Does WISP with a data-derived path end — the significance test of §2 instead of the truth-derived 6-term cap — reach
the same final result as Q5, on the same cells, with the same fit and the same size rule?

## 2. The rule

Path and weak space unchanged (Q4/Q5; `growth_path_with_end` of Q6 with the full basis as the only hard end).
Noise variance per point from the Q6 estimator (local leverage-corrected cubic, 9 / 21 points). For an equation with
current support S and each remaining term j: gain `g_j = sse(S) − sse(S ∪ {j})`, expected gain of a pure-noise term
`n_j = F(S) − F(S ∪ {j})`, with F the Q6 primary floor `trace((I − P_S) C_b)`. **The equation stops growing when
`g_j / n_j < 6.635` for every remaining j** (χ²₁, α = 0.01; `n_j ≤ 0` counts as significant). Secondary threshold
10.828 (α = 0.001) reported for the paths only. Numerical-zero stop, `no_gain` and `cycle` as in Q6.

One sentence: *a term enters only if it lowers the weak residual by more than noise plausibly could.*

## 3. Fits — only what Q5 has not fitted

Every Q7 candidate whose support (all equations) equals a Q5 candidate of the same cell takes Q5's record unchanged:
same support gives the same weak start and the same deterministic fit (`max_fit_attempts = 1`). Only the remaining
states are fitted, with the Q5 Julia runner and image `354106398d…` unchanged, on Orion. Projection from Q5's measured
per-candidate cost (wall-clock, planning only): 3,080 new states (dim1 0, dim2 1,207, dim3 1,047, dim4 826),
~600–1,400 core-h, central ~1,100 core-h ≈ 1,650 €.

## 4. What is reported

Rule (c) trajectory BIC over each cell's Q7 candidate list (rules (a), (b) beside it), with Q5's metrics — pruned and
raw exact structure, R² > 0.9 reconstruction and generalization, variance-weighted — **always structure and R²
together**, per stratum × σ and per ρ, beside Q5 on the same cells; D1–D5 as Q5; cost (candidates, fits, loss
evaluations). Then the Q5-W comparison (W1 on ρ = 0, W1-interp on ρ = 0.5) with Q7 in place of Q5.

## 5. Decision rule (fixed now)

Q7 **replaces the 6-term cap in WISP** if, per stratum pooled over the noisy conditions, it is not worse than Q5 by
more than 5 percentage points on pruned exact structure **and** on R² > 0.9 generalization (the non-inferiority
margin of plan §9.4d). Otherwise WISP keeps the cap, declared as a computational budget, and the data-derived end
stays a Paper 2 question. `dim4` (2 units) is reported, not decided on.

## 6. Controls

- The Q7 path builder reproduces the exploratory paths bit-identically (support sequence per cell).
- Q5 reuse: for every reused state, the Q5 record's support and `p0` equal the Q7 candidate's.
- New fits: provenance of the Q5 runner (settings fingerprint, image) unchanged; `observed_data_sha256` per cell.
- Aggregation only after all Q5 cells (incl. the two stragglers) and all Q7 fits are complete.
