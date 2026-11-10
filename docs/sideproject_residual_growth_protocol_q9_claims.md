# Side project WISP — protocol Q9-A: claims and analysis plan for the paper

**Frozen 2026-11-10 before any Q9 metric was computed** (Q9: 69 / 4,284 shards finished on Orion, none collected, none
evaluated), after the user's decisions on the draft (primary comparator, missing cells, wording, headline population,
ablations from Q8, analysis code first). Parts before: Q9 (`_q9.md`: method,
data, metrics, strata, references), Q-B (`_qb.md`: extended baselines and their in-favour selection). Q9-A adds no
measurement; it fixes which sentences the paper may say, how each is tested, and what is written when a test fails.

## 1. Data basis and freeze

1. **One evidence state.** Every WISP number in the paper comes from Q9 (one identity: image `cdfaa7d`, one settings
   fingerprint). Q8 is cited only for the ablations and design alternatives (§6), labelled as Q8 (subset: dimensions
   1–2, σ ∈ {0.01, 0.05}, realization 1). Q-Cal is cited only for the stop calibration.
2. **Data freeze** when all 4,284 Q9 cells have a record, or when the user ends the run. A WISP cell without a record
   counts as a **miss on every metric** (no exclusion). A reference cell without a result is dropped from that pairwise
   comparison only; the count of dropped cells is reported. Because a missing WISP cell can only turn into a hit, a
   re-run of the frozen analysis on more finished cells can only raise WISP's rates and differences; such a re-run is
   allowed at any time (also after submission) and is not a deviation.
3. **Analysis code first.** The aggregation script is written and tested on Q8 C1000 cells (dry run) before Q9 is
   opened; its first run on Q9 is the analysis. Any later change to it is a declared deviation in the paper.
4. **All numbers in the text are generated** by one script from the frozen records as LaTeX macros; no number is typed
   by hand (precondition for the claim check G4).

## 2. Populations and unit of inference

- **Noisy population (headline):** the 10 conditions σ ∈ {0.01, 0.02, 0.03, 0.04, 0.05} × ρ ∈ {0, 0.5}, three
  realizations, both training ICs: **60 cells per system**.
- **Reported separately, never pooled with the headline:** clean (0, 0) (2 cells per system) and noise-free subsampled
  (0, 0.5) (6 cells per system).
- **Strata** as Q9 §3: dim 1 exact (11 systems), dim 2 exact (10), dim 1 surrogate (12), dim 2 surrogate (18), dim 3
  exact split 52/61 vs 54–59, dim 3/4 rest. Exact and surrogate are never pooled (Design Principle 8).
- **Unit:** the system. Per system, the hit rate over its cells; a stratum's rate is the mean over its systems (equal to
  the pooled cell rate, since every system has the same cell count). Cells are never treated as independent.

## 3. Statistics

- **Intervals:** 95 % percentile cluster bootstrap over systems, 10,000 resamples, fixed seed.
- **Paired tests:** per-system difference of hit rates (WISP − reference), two-sided sign-flip permutation test over
  systems; exact enumeration when the stratum has ≤ 20 systems, else 100,000 random flips, fixed seed. A system with
  difference 0 contributes 0.
- **Primary family (Holm-adjusted, α = 0.05), WISP vs WSINDy (MATLAB original), noisy population:**
  P1 structure (pruned) dim 1 exact · P2 structure dim 2 exact · P3 generalization dim 1 exact · P4 generalization dim 2
  exact. WSINDy is the primary comparator because it is the strongest reference under noise in Q8 and the unmodified
  original code of the inventors of weak-form regression. A primary test against "the best reference per cell" is
  deliberately not used: that comparator picks its method after seeing the result, so it exists for no user. The
  comparison with every reference is claim C3.
- **Everything else is secondary:** reported with unadjusted p and labelled as such; it never carries a sentence of
  the form "WISP is significantly better" in the abstract.

## 4. Claims, criteria and fallback wording

Each claim has a criterion fixed now and a fallback sentence written now. Wording rules in §5 apply to all.

| # | Claim (sentence in the paper) | Criterion | If the criterion fails |
|---|---|---|---|
| C1 | Under noise, WISP recovers the exact law more often than WSINDy (dim 1 and 2). | P1 and P2 pass (Holm), difference > 0 in both. | Report the differences with intervals; "comparable" where a test fails; the abstract leads with the metric that passes. |
| C2 | Under noise, WISP predicts from an unseen initial condition more often than WSINDy (dim 1 and 2). | P3 and P4 pass (Holm). | As C1. |
| C3 | WISP is ahead of every reference, not only WSINDy. | For each reference (SINDy, Weak-SINDy, E-SINDy in WP-N47 and in B1 form, WeakIdent B2a/B2b, ODEFormer B3) and each of structure / generalization on dim 1–2 exact: difference > 0 and secondary p < 0.05. References always at their in-favour selection (Q-B). | Name the reference and metric where it fails; the sentence becomes "ahead of every reference except …". |
| C4 | The advantage holds per system, not on a few systems. | Counted per system and metric vs WSINDy (ahead / tied / behind, tie = equal rate): ahead on more systems than behind in every exact stratum × metric. | Report the counts; drop the sentence. |
| C5 | The gap opens with noise. | Structure on exact dim 1–2 pooled: (WISP − WSINDy) at σ = 0.05 minus the same on clean > 0, bootstrap interval excluding 0. | Report the per-σ curve without the sentence. |
| C6 | When the true law is on the growth path, the trajectory criterion selects it. | Share selected among noisy exact dim 1–2 cells with the truth on the path ≥ 0.90 and interval lower bound ≥ 0.80. | Report the share as "in most cases (x %)". |
| C7 | The remaining failures lie in the path, not in the selection. | Among noisy exact dim 1–2 structure misses, ≥ 2/3 are cells whose path never contains the truth. | Report the split without the sentence. |
| C8 | Selecting on the weak residual over-sizes; the trajectory BIC does not. | Share of over-sized models (chosen size > true size), noisy exact dim 2: weak BIC − trajectory BIC > 0, interval excluding 0. | Descriptive only. |
| C9 | Surrogate systems: WISP's models reproduce and predict more often than the references'. | Secondary tests vs WSINDy, reconstruction and generalization, dim 1 and 2 surrogate. | Name the failing cell; no pooled statement. |

**Not claims, descriptive only:** dimension 3 and 4 (eight + two systems; per-system table, 52/61 apart from 54–59);
clean and (0, 0.5) conditions; cost (candidates, fits, loss evaluations, ODE solves per stratum as quantiles; wall-clock
as labelled context, never evidence); runtime tail.

## 5. Wording rules

These rules govern content, not style; the user writes the text.

- Every qualitative statement about size or difference ("doubles", "better", "more often") is backed by its number in
  the same sentence or table. "Roughly doubles" requires a ratio of rates ≥ 1.8 in every stratum it refers to.
- "Significant" is used only for the primary family after Holm correction.
- Every rate carries its stratum and population; no Q8 number appears in the abstract.
- Weaknesses the analysis shows (for example a reference ahead on clean data) are stated in Results, not only in
  Limitations.
- Scientific register: plain, specific statements; no promotional or generic phrasing.

## 6. Ablations and design alternatives

Not re-run in Q9. The paper reports them from Q8 (C1000 vs no-FoBa, random start, no refit, bound 10, variant without
initial-state estimation) with Q8's own population and intervals, labelled as Q8, and makes no Q9 claim about them.

## 7. Robustness checks (reported, never used to rescue a claim)

Raw instead of pruned structure; each IC direction separately; each realization separately; ρ = 0 only; references at
their single best threshold per stratum (instead of per σ × metric); available-case analysis instead of missing = miss.
If any of these flips the sign of a primary difference, the abstract says so.
