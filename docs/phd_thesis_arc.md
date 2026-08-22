# PhD Thesis Arc — Three Papers, One Question

Status: **draft for discussion**, created 2026-08-19.

This document sits *above* `PAPER_1.md`. It defines the question the three papers jointly answer and
what each of them must contribute. It does **not** replace `PAPER_1.md`, which remains the
execution plan for Paper 1. Where the two disagree about Paper 1 scope, this document states the
intent and `PAPER_1.md` states the plan, and the two must be reconciled deliberately.

---

## 1. The thesis question

> **What limits structural discovery in coupled ODE systems, and how much of it can be controlled
> before the expensive search begins?**

Three answers, in order: the **space** can be bounded, but only where the data supports it (#1); the
**search** fails even inside a correct space, for a reason that lies in the operators (#2); and what
survives **noise, sparsity, coupling and dimension** is a different question again (#3).

### Why this framing rather than "the method wins"

A thesis about *limits* cannot be refuted by its own results. If the operators in Paper 2 fail to
repair structural recovery, that is a second valid negative result and the arc still holds — the
contribution is knowing *why*. A thesis about method superiority stands or falls on numbers that the
chaotic systems in this benchmark may simply refuse to give.

This is a deliberate risk decision, not a rhetorical one.

### What the thesis is not about

Not numerical differentiation as such, even though derivative quality turns out to be the binding
constraint in #1. Making that the through-line would drift the work away from its stated focus on
search strategies. Derivative quality enters as a *limit on control*, not as a subject in itself.

---

## 2. Paper #1 — Where the search space can be bounded before searching

**Question.** How far may a hypothesis space be restricted from data alone, before the search runs
and without ground truth, and how does one know when that restriction is trustworthy?

**Contribution.** Not "a cap saves 15 % of evaluations". The contribution is the **boundary**: a
data-driven pre-search controller is safe exactly where the derivative estimate resolves the
structural difference between stages, and unsafe exactly where it does not — together with the
finding that the threshold separating the two regions **cannot be selected from the data**, and a
criterion that identifies the unsafe region *without* ground truth.

*Revised 2026-08-20.* The earlier wording put an **abstention rule** at the centre of this
contribution. WP-V1 removed it: measured over all 80 equation rows the abstention prevented zero
wrong caps and surrendered three correct ones, and the Lorenz repair it was credited with comes from
the reopen branch instead. The decision is binary again (WP-C5). What replaces abstention as the
honest answer to "how do you know when to trust it" is the negative result below — and that is a
stronger claim, because it is a limit rather than a knob.

**Evidence already in hand.**

- Look-ahead stage cap on the v2.2 substrate. Audit over 20 exact systems, 2 IC sets, 80 equation
  rows: no truncated rows remain.
- Capped against v2.2 over 30 regression cells: loss **bit-identical in all 30**, `pruned_match`
  unchanged, 15.3 % fewer loss evaluations, under one git hash and one fingerprint triple.
- The decisive causal experiment: with analytic derivatives all five residual failures reach the
  required stage, while a 5x5 sweep of `tau_rel` and `tau_abs` over four orders of magnitude repairs
  none. The cause is the derivative input, not the thresholds.
- **The threshold is not selectable from data (WP-V1).** Leave-one-system-out over the 20 exact
  systems puts the reopen threshold between 0.044 and 0.278; the shipped value is 0.35, and at every
  selected value Lorenz truncates again. The margin between 0.35 and Lorenz's worst ratio of 0.315
  is 11 % and is a human choice. This was the intended weak point of the paper and turned into one
  of its results.
- The price of a surrendered cap, predicted from the audit and then measured: System 31 / IC 1 cost
  **+16 %** evaluations at a bit-identical loss — compute, never the solution.
- Three design rules, each bought with a defect: positive evidence over its absence (System 63);
  look ahead as far as the basis creates structural gaps (WP-C1); and a mechanism must be credited
  only by an experiment that isolates it (WP-C4's band was credited with a repair the reopen branch
  had made — WP-V1).

**What is still missing.**

1. **The predictive criterion.** Can the equations where the controller will fail be identified in
   advance, from the ratio of noise floor to stage residual, *without* ground truth? The data is in
   `stage_diagnostics.csv`. **This is what turns Paper 1 from an observation into a claim.**
2. **Breadth.** Phase B, so the numbers rest on more than five diagnostic systems.
3. At least one external baseline, for positioning rather than for winning.

**Gate.** If the predictive criterion does not exist, Paper 1 is an honest efficiency and
negative-results paper. The arc still works, but it is a weaker opening and Paper 2 has to carry
more.

**Explicitly out of scope.** Structural recovery. `pruned_match = false` on coupled systems is
stated as a limitation and is the handover to Paper 2, not a failure of Paper 1.

---

## 3. Paper #2 — Why the search fails inside a correct space

**Question.** The admissible space contains the true structure, the loss reaches 1e-11, and the
recovered support is still wrong. Why?

**This is the sharpest negative result the project holds**, and it is currently unexploited. It is
sharp because the obvious alternative explanations are already excluded: the space was right, the
stage was unlocked, the fit was excellent.

**Diagnosis already available.** The search grows only. `_expand` adds terms and never removes,
every line starts from a single random term, and selection is the only corrective. A wrong early
term can therefore never leave a line. That is the structural reason recovery fails independently of
loss.

**Contribution.** Establish the mechanism, then introduce removal and replacement operators and
measure recovery against the same regression suite. A clean before/after on infrastructure that
already exists — regression suite, fingerprints, cluster path.

**Risk, stated in advance.** The operators may not repair recovery. That outcome is publishable and
keeps the arc intact, because the thesis asks what limits discovery rather than claiming to remove
the limit.

**Prerequisite.** Paper 1 must have established that the space is not the cause. Without that, any
recovery failure is confounded with the controller.

---

## 4. Paper #3 — What survives noise, sparsity, coupling and dimension

**Question.** Does incremental growth actually beat global search, and under which conditions does
that advantage disappear?

This is where the founding claim of the project finally becomes testable, and where the external
baselines belong (SINDy, PySR, GP). Before Paper 2 it would characterise a method that does not
reach its goal, and the result would be uninterpretable.

**Axes.** Noise level, sampling density, coupling strength, dimensionality — the four already
planned as Phase 3.

**Prerequisite.** Paper 2, whatever its outcome. If the operators repair recovery, Paper 3 measures
the repaired method. If they do not, Paper 3 measures the limit and says so.

---

## 5. The representation question — a decision this arc does not yet contain

*Added 2026-08-22, from the ODEBench motif audit.*

**The finding.** The staged basis represents 20 of the 63 ODEBench systems exactly. The other 43
contain terms it cannot express at all. Sorting all 82 uncovered terms into families and adding the
families greedily gives this closure curve:

| Catalogue grows by | Systems gained | Exact total |
|---|---|---|
| baseline | — | 20 / 63 |
| + constant | +10 | 30 |
| + rational (saturation, Hill) | +12 | 42 |
| + mixed monomials of degree ≥ 3 | +9 | 51 |
| + trigonometry **with a scaled argument** | +7 | **58** |
| + exp, log, real power, high power, absolute value | +1 each | 63 |

**Four families cover 92 % of the benchmark.** After that the return collapses: the last five
systems need five different one-off families, one system each — Gompertz (log), language death
(real power), Landau (high power), reduced SIR (exp), driven pendulum (absolute value). That cliff
is where a catalogue stops on evidence rather than on taste.

**Two steps, and only the second is architectural.**

- **Step A, 39 of 63.** Constant and mixed monomials are ordinary basis functions. The model stays
  linear in its coefficients, the OLS warm start is untouched, nothing but the catalogue changes.
- **Step B, 58 of 63.** Rational and scaled-trigonometric terms carry **inner** parameters — `K` in
  `u/(u+K)`, `ω` in `sin(ωu)`. The additive structure survives, but each term becomes a small
  nonlinear fit. The derivative-matching warm start survives as a separable least-squares problem:
  the outer coefficients stay linear given the inner parameters, so OLS solves them and only a one-
  or two-dimensional search per term remains.

**Why this is not a slide towards GP.** GP is a search, not a representation: global start, large
random structures, crossover. Three properties define this project instead, and Step B keeps all
three — an additive term structure, an enumerable and stageable catalogue, and minimal-start growth
under a promotion rule. What changes is expressiveness, not search discipline. The claim
"controlled incremental growth works in an expressive space where global search is expensive" is
strictly stronger than the same claim in a polynomial library.

**Where it belongs in the arc.** Nowhere yet, and that is the point of writing it down.

- It is **not** Paper #1. Changing the basis changes `config_fingerprint`, invalidates the
  regression block, and — worse — moves the ground under design rule 2, which derives the look-ahead
  horizon from where the basis creates structural gaps. That is Phase 2b re-opened.
- It **qualifies** Paper #1's role in the arc. "The space is not the cause of failed recovery" is
  established on the 20 exact systems only. On the other 43 the space *is* the cause. The arc must
  state that scope rather than imply the general claim.
- It is a **precondition for Paper #3.** External baselines are the point of #3, and PySR, SINDy
  with a rich library, and ODEFormer all search spaces that can express saturation and oscillation.
  Comparing fit quality on systems we cannot represent measures our catalogue, not our search. The
  protocol audit therefore needs a column it does not have today: **is the competitor's search space
  representationally adequate for this system?**

**The open risk, and it points the other way.** This counts representability, not findability. A
richer catalogue enlarges the space and creates near-degenerate structures — `u/(u+K)` tends to a
linear term for large `K` — which is poison for support recovery, the very thing Paper #2 is about.
Representability is necessary, not sufficient, and Step B may make #2 harder before it makes
anything better. Whether the catalogue grows before or after #2 is therefore a real decision, not a
formality.

**Status.** Undecided. Phase B is the before-measurement either way: it establishes the controller
and gives per-system R² on the 43 surrogates, which turns "cannot represent" into "approximates this
well" — the evidence that says which families are worth their cost.

---

## 6. Dependencies

```text
#1  bound the space        -> establishes that the space is not the cause of failed recovery
                              (on the 20 exactly representable systems)
#2  make the search work   -> needs #1, isolates the operators as the cause
#3  robustness and scaling -> needs #2, else it characterises a method that misses its target
                              -> and needs the representation decision from section 5, else the
                                 external comparison measures the catalogue instead of the search
```

Each paper is a precondition for the next. That is the property that makes three papers a thesis
rather than three unrelated results.

---

## 7. What belongs in none of the three

Line-search cost, the sentinel loss `1e6`, GPU, batched parameter fitting, threading over the
population, the `discover()` API cleanup. These are craft, not thesis. They may appear in a methods
section as cost context; they are not contributions.

`docs/hpc_requirements.md`, `SCRIPTS.md` and the provenance apparatus — three-field record identity,
behaviour fingerprint, frozen artefacts — are infrastructure. They earn a reproducibility appendix,
not a claim.
