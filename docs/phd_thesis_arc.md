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
structural difference between stages, and unsafe exactly where it does not — with an abstention rule
for the region in between, and a criterion that identifies that region *without* ground truth.

**Evidence already in hand.**

- Look-ahead stage cap on the v2.2 substrate. Audit over 20 exact systems, 2 IC sets, 80 equation
  rows: no truncated rows remain.
- Capped against v2.2 over 30 regression cells: loss **bit-identical in all 30**, `pruned_match`
  unchanged, 15.3 % fewer loss evaluations, under one git hash and one fingerprint triple.
- The decisive causal experiment: with analytic derivatives all five residual failures reach the
  required stage, while a 5x5 sweep of `tau_rel` and `tau_abs` over four orders of magnitude repairs
  none. The cause is the derivative input, not the thresholds.
- The abstention price, predicted from the audit and then measured: System 31 / IC 1 costs **+16 %**
  evaluations at an identical loss.
- Three design rules, each bought with a defect: positive evidence over its absence (System 63);
  look ahead as far as the basis creates structural gaps (WP-C1); abstain in the doubt band (WP-C4).

**What is still missing.**

1. **A hold-out for the band constants.** `0.35 / 0.62 / 0.1` were chosen on the same 20 systems
   they are validated against. This is the most attackable point in the paper and cannot be argued
   away; it needs a split.
2. **The predictive criterion.** Can the equations where the controller will fail be identified in
   advance, from the ratio of noise floor to stage residual, *without* ground truth? The data is in
   `stage_diagnostics.csv`. **This is what turns Paper 1 from an observation into a claim.**
3. **Breadth.** Phase B, so the numbers rest on more than five diagnostic systems.
4. At least one external baseline, for positioning rather than for winning.

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

## 5. Dependencies

```text
#1  bound the space        -> establishes that the space is not the cause of failed recovery
#2  make the search work   -> needs #1, isolates the operators as the cause
#3  robustness and scaling -> needs #2, else it characterises a method that misses its target
```

Each paper is a precondition for the next. That is the property that makes three papers a thesis
rather than three unrelated results.

---

## 6. What belongs in none of the three

Line-search cost, the sentinel loss `1e6`, GPU, batched parameter fitting, threading over the
population, the `discover()` API cleanup. These are craft, not thesis. They may appear in a methods
section as cost context; they are not contributions.

`docs/hpc_requirements.md`, `SCRIPTS.md` and the provenance apparatus — three-field record identity,
behaviour fingerprint, frozen artefacts — are infrastructure. They earn a reproducibility appendix,
not a claim.
