# PhD Thesis Arc — Three Papers, One Conference Insert, One Question

Status: **working roadmap**. Created 2026-08-19, restructured 2026-09-22.

This document sits *above* `PAPER_1.md`. It defines the question the papers jointly answer and what
each of them must contribute. It does **not** replace `PAPER_1.md`, which remains the execution plan
for Paper 1. Where the two disagree about Paper 1 scope, this document states the intent and
`PAPER_1.md` states the plan, and the two must be reconciled deliberately.

**This is a plan, not a prediction.** Every paper below can be refuted by its own experiments, and
two of them are explicitly conditional on results that do not exist yet. The arc is written so that
a negative result relocates work rather than destroying the thesis — see §1.

**What changed on 2026-09-22, and what it replaced.** The earlier version of this document had a
different split: #1 bounding the search space, #2 operators for a search that fails inside a correct
space, #3 robustness. `PAPER_TIMELINE.md` proposed a different one and was merged into this file
rather than kept beside it, because two planning documents drifting apart is the failure mode this
project already has a scheduled audit for. Four decisions were taken:

- **Guidance becomes Paper 2**, and the removal/replacement operators become Paper 3.
- **Robustness — noise and sampling density — folds into Paper 1** rather than being its own paper.
- **There is no Paper 4.** The representation expansion stays the bridge decided on 2026-08-22.
- **The restart budget becomes a conference paper** inserted between Paper 1 and Paper 2.

A further correction made in the same pass: this document still described Paper 1 as the stage-cap
paper. The scope decision of 2026-09-09 superseded that — Paper 1 is a method paper about EvoGrow
with Claims A–D, and the cap is one component with its own ablation.

---

## 1. The thesis question

> **What limits structural discovery in coupled ODE systems, and how much of it can be controlled
> before the expensive search begins?**

### Why this framing, and not "the method wins"

A thesis about *limits* cannot be refuted by its own results. If guidance in Paper 2 fails to
improve support recovery, that is a valid negative result and the arc still holds — the contribution
is knowing *why*. If the operators in Paper 3 fail to repair path dependence, the same applies. A
thesis about method superiority stands or falls on numbers that the chaotic systems in this
benchmark may simply refuse to give.

**This is a deliberate risk decision, not a rhetorical one**, and it was re-confirmed on
2026-09-22 when a capability-progression framing ("grow → guide → repair") was considered and
rejected as the *thesis*. That progression is kept as the **narrative** of the three papers, which
is what it is good at; the question above remains the thing being answered.

### What the thesis is not about

Not numerical differentiation as such, even though derivative quality turns out to be a binding
constraint in Paper 1. Making that the through-line would drift the work away from its stated focus
on search strategies. Derivative quality enters as a *limit on control*, not as a subject in itself.

---

## 2. The arc at a glance

| | Role | Question | Size |
|---|---|---|---|
| **Paper 1 — EvoODE** | Foundation / method | How should ODE structure be grown incrementally, and what survives noise and sampling density? | Full paper |
| **Conference insert — restart budget** | Focused measurement | How many parameter restarts does structure discovery need, and what does the recovery/cost curve look like? | Conference |
| **Paper 2 — Trajectory-Informed EvoODE** | Major extension | Which candidate terms deserve attention first, and does that improve support recovery on coupled systems? | Full paper |
| *Representation expansion* | *Bridge, not a paper* | *Which term families does the catalogue need, and what do they cost?* | — |
| **Paper 3 — Reversible EvoODE** | Focused search extension | How can wrong structural decisions be detected and repaired? | Conference / smaller paper |

The narrative in one line:

> Paper 1 grows the structure, Paper 2 tells the search where to grow, and Paper 3 lets it recover
> when it grew in the wrong direction.

---

## 3. Paper 1 — EvoODE

**Question.** Can interpretable ODE structure be discovered through staged, incremental structure
growth with trajectory-space evaluation — and where does that stop working?

**Authority.** `PAPER_1.md` and `docs/paper1_phaseC_benchmark_plan.md`. The claims below are that
plan's, not a second set.

### The mechanism

```text
small structure -> incremental term addition -> stage-wise complexity exposure
    -> trajectory-space parameter fitting -> selection -> progressively richer structure
```

### The contribution, stated so a reviewer cannot misread it

Not "another symbolic regression method". The distinction is: no unrestricted expression-tree
generation, no GP-style crossover or subtree mutation, no one-shot sparse regression over the
complete candidate space — instead **incremental growth through a controlled staged candidate
library**. The model class is restricted and explicitly defined. The novelty is in **how the
structure space is traversed**, not in the size of the hypothesis class.

**Never call the search space unrestricted.** The canonical basis is
`1, u_i, u_i², u_i·u_j, u_i³, sin(u_i), cos(u_i)` — 30 of 63 systems exactly representable against
SINDy's 40 and ProGED's 53. The difference to SINDy is **when** library members become reachable,
not how many there are.

### Claims

- **A — Structure discovery.** Does EvoGrow recover useful structure through incremental support
  growth? Three-way representability, F1, precision, recall, coefficient error, raw **and** pruned
  support.
- **B — Stage capping.** Does trajectory-derived stage information avoid unnecessary search effort?
  **Conditional, and the condition must be reported with its frequency**: the interim Phase C
  measurement shows the cap saves effort only where *every* equation carries a finite cap (21 fully
  capped pairs: −28.3 % loss evaluations, `pruned_match` equal in 21/21; 39 uncapped pairs bit-
  identical; partially capped pairs save nothing). How often the condition holds is known:
  dim 1 32/46, dim 2 15/56, dim 3 3/20, dim 4 0/4.
- **C — Generalization.** Does the discovered ODE generalize to an unseen initial condition, in
  both directions?
- **D — Baseline.** How does EvoODE compare with SINDy on identical trajectories, in quality **and**
  cost?

Plus an oracle-structure arm that separates search failure from optimization failure.

### The negative result Paper 1 carries, and should

The reopen threshold **cannot be selected from the data**. Leave-one-system-out over the 20 exact
systems puts it between 0.044 and 0.278 while the shipped value is 0.35, and at every selected value
Lorenz truncates again. The 11 % margin between 0.35 and Lorenz's worst ratio of 0.315 is a human
choice and must be reported as one. This was the intended weak point of the paper and turned into
one of its results — a limit rather than a knob.

### Robustness folds in here — decided 2026-09-22

Noise level and sampling density become **Paper 1 axes**, not a separate paper. The reason is
comparability: ODEFormer/ODEBench and the surrounding literature vary noise and subsampling, and a
method paper that reports only the noise-free, densely sampled case cannot be placed beside them.
Coupling strength and dimensionality are already covered by the benchmark's own spread.

**This is the largest open cost in the arc, and it is not yet budgeted.** Three facts make that
concrete:

1. The Phase C campaign is **frozen and running** with no noise axis. Folding noise in means an
   additional arm, and the campaign identity `0c9672de35c75a9d` does not cover it.
2. `CLAUDE.md` lists **"no noise injection utilities"** under Known Gaps. WP-T1 built noise, but in
   the Python analysis layer on trajectories — **not in the Julia search path**. The EvoGrow side
   does not have it.
3. Phase C already costs ~12,300–15,900 core hours. A noise axis multiplies whatever subset it
   covers.

**The decision this forces, and it is not taken yet:** either a reduced noise arm on a named subset
of systems, or noise as declared future work with the comparability limitation stated in the paper.
Doing it at full campaign breadth is not affordable. **Do not let this resolve itself by drifting.**

**Deferred, deliberately — decided 2026-09-23.** No noise work is scoped, budgeted or built until
Phase C shows that EvoGrow earns its place on **noise-free** data. The reason is sequencing: a noise
axis for a method that has not yet shown its merit on clean data measures the degradation of
something unproven. This is a decision to *order* the work, not to drop the axis — the
comparability argument above still holds, and the choice between a reduced arm and declared
future work is re-opened once the Phase C evaluation exists. One correction to the premise it was
taken on: the ODEBench file ships **noise-free** solver output (`solutions[*].y`, the
`solve_ivp` fields); noise is part of ODEFormer's *evaluation protocol*, applied on top, not
contained in the data. The protocol audit (`docs/paper1_odebench_protocol_alignment.md`) still
carries the noise setting of the published baselines as "to verify".

### Limitations Paper 1 may leave open

These are not reasons to delay Paper 1. They are the motivation for the papers after it:
add-only growth and strong path dependence; weak support recovery on coupled higher-dimensional
systems (0 of 50 exact dim-3/dim-4 cells in Phase B); uniform candidate selection inside the
eligible set; constant-term false positives; duplicate structures acting as implicit multistarts;
a limited candidate library; and the difficulty of separating identifiability from search failure.

---

## 4. Conference insert — the restart budget

**Decided 2026-09-22:** this is inserted between Paper 1 and Paper 2 rather than absorbed into
either.

**Question.** How many parameter restarts does structure discovery need, and how does the
recovery-versus-cost curve behave?

**Evidence already in hand (WP-N4).** Handed the *true* structure, a single fit from a random start
hits the sentinel loss `1e6` in **15 of 102** cells; at k = 2 it is 13, at **k = 3 it is zero**, and
R² > 0.9 on the reference fit rises from 71.6 % (k = 1) to 97.1 % (k = 10).

**Why it earns its own output, and why it sits *before* Paper 2.**

1. It is cheap: no structure search, one fit per restart.
2. It has a natural cost axis, so it speaks directly to the efficiency claim the thesis rests on.
3. It is **currently a confound in every comparison the project has made.** Under `pretuning=false`
   every fit draws `0.1 .* randn` (`bfgs.jl:269`); under `pretuning=true` the start is deterministic
   per structure. The two arms therefore differ in start *count*, not only start *quality* — the
   Phase B contrast measured two things at once.
4. **Paper 2 cannot be interpreted until this is settled.** A relevance prior concentrates the
   sampling distribution, which *raises* the duplicate rate, and duplicates act as implicit
   multistarts. Guidance would then change search breadth and effective restart count
   simultaneously — the same confound again, one layer up.

**Honest framing.** The restart dependence is a symptom of our loss, not a universal necessity. We
optimize MSE on the *integrated* trajectory, which is badly conditioned; SINDy has no analogous
failure mode because it fits in derivative space where the coefficient problem is linear. The paper
says **"our approach carries a failure class SINDy structurally cannot have"**, not "everyone needs
a budget".

**Three budget levels must be kept apart** and currently are not: structural search budget
(structures examined), parameter optimization budget (restarts k), and run-level stochasticity
(seeds). Beam size is not our k: it varies *structures*, k varies *parameter starts*. Any
recovery-versus-k curve needs a cost axis in *fits*, not in k.

---

## 5. Paper 2 — Trajectory-Informed EvoODE

**Question.** Can trajectory-derived term relevance guide evolutionary ODE discovery toward better
structures by ranking candidate terms before the expensive structure search?

Sharper: **can the observed trajectory provide an equation-specific prior over candidate terms that
improves support recovery on coupled systems?**

### The target is support recovery, not speed

Compute reduction is a **secondary outcome metric**, never the goal. WP-N6 settles why: EvoODE is
level with SINDy on reconstruction (95.5 % vs 95.7 %) and ahead on generalization (68.2 % vs 60.9 %)
at roughly **two orders of magnitude** more compute. A factor of two does not close that; it moves
it one digit. Improved support recovery on dim 2 and dim 3 would address a capability gap that
direct sparse regression does not reliably solve either.

"Faster" may be part of the result. It is not the claim.

### Why the mechanism should work

1. **Add-only path dependence.** `_expand` adds and never removes; a bad early addition poisons a
   lineage, and selection is the only corrective. The order in which candidates are tried therefore
   matters more here than in a search with free deletion.
2. **Candidate drawing is uniform.** Every draw in `src/structure/evogrow.jl:271-450` is
   `rand(candidates)`. The observed trajectory does not influence which candidate is tried first.
3. **The constant term is the minimal example.** It is required for representability (30 instead of
   20 exact systems) and is simultaneously a measured false-positive attractor — present in 31 of 37
   missed dim-1 cells, and on dim 2 it drops pruned recovery from 55.6 % to 35.2 %. Threshold tuning
   provably does not fix it (WP-N2: zero-sum dial, 45 is the ceiling). A prior can say *"the term
   stays reachable, but this trajectory gives little evidence for it"* — without removing a library
   component because it produces false positives.
4. **Coupled systems are the regime that matters.** A positive dim-1 result is not evidence.

### The prior is per equation

The same library, different rankings per equation. For
`ẋ₁ = −x₁ + x₂`, `ẋ₂ = x₁ − x₂³`, equation 1 should rank `x₁, x₂` first and equation 2 should rank
`x₂³, x₁` first. A single global ranking for the whole system is a different, weaker method and must
not be built by accident.

### The integration is soft guidance, never hard pruning

```text
P(φ_j) = (1−ε)·P_relevance(φ_j) + ε·P_uniform(φ_j)
```

Every candidate stays reachable, the library does not shrink, trajectory-supported terms are tried
more often, and exploration stays nonzero. The model class is preserved; only search **priority**
changes. Hard top-K pruning is an aggressive ablation at most — with add-only growth, one false
negative permanently destroys reachability.

### Novelty caution, to be stated rather than discovered by a reviewer

The cheap ranking step is closely related to **weak-form / integral SINDy**. The paper must name
that. The contribution is the **division of labour**:

```text
trajectory -> cheap weak/integral candidate evidence -> term relevance prior
    -> evolutionary support search -> trajectory-space nonlinear fitting
```

And the screening compute belongs to EvoODE's total cost, not outside it.

### Status: conditional on WP-T1 and WP-T1b

**WP-T1 is done (2026-09-22) and positive.** In the pre-declared decision cell (weak signal, forward
residual ranking, σ = 0, IC1, dim 2+3, 18 systems, 44 equations) the median of
`n_false_before_last_true` is **0.0** against a random-ordering expectation of 6.1 (dim 2) and 11.5
(dim 3), with 37 of 44 equations at ≤ 3. Failures concentrate in systems 52, 54 and 57 and are
identifiability-driven: max cosine between a true and a false column is 0.9989 there against 0.9723
where the ranking succeeds.

Two corrections that travel with that result: all cluster-robust p-values sit at the **resolution
floor** of 18 clusters and must be reported as such rather than to twelve digits; and the WP-T1
statement "weak beats fd" is **not supportable** — on the 39 equations whose support excludes the
constant the two signals are identical at σ = 0, and the apparent gap comes from a centering defect
that makes the constant unfindable in the `fd` arm.

**WP-T1b decides what Paper 2 actually is.** It measures how far the ranking carries as a
*standalone* discovery method against the SINDy baseline on identical trajectories (exact systems:
dim 2 66.7 % structure hit, dim 3 28.6 %). Three outcomes, pre-declared:

- **A** — standalone matches or beats that. Then "guidance" is not the paper; the finding is that
  the cheap step does the work, and Paper 2 becomes a paper about the division of labour, or about
  why the expensive search is worse than its own preprocessing.
- **B** — ranking strong, standalone selection fails. The division of labour is real and guided
  EvoGrow is justified. **This is the case Paper 2 as written above assumes.**
- **C** — standalone fails and the oracle-size arm fails too. Ranking quality was necessary but not
  sufficient.

**Do not rewrite this section before WP-T1b reports.**

### The confounder Paper 2 must control

A concentrated sampling distribution produces **more** repeated structures, not fewer, and under
`pretuning=false` duplicates act as implicit multistarts. A fair comparison therefore reports
together: support recovery, unique structures, duplicate rate, fits per unique structure,
`max_fit_attempts`, total parameter fits, loss evaluations, ODE solves, and R². **Δ loss evaluations
alone is uninterpretable.**

### The frozen sequence — decided 2026-09-22

**This list is closed.** No work package in this branch that is not on it, unless a gate outcome
forces one. The purpose of freezing is not rigidity but protection against creep: every step so far
was individually cheap and individually justified, and that is exactly how a side branch eats a
thesis.

| # | WP | Question it closes | Cost | Gate / stop rule |
|---|---|---|---|---|
| 0 | WP-T1 ✔ | Is there ranking signal at all? | done | **positive** — median 0 on dim 2+3 |
| 1 | WP-T1b ✔ | Does the signal replace the search? | done | **C — no.** 30.0 % / 0.0 % against SINDy's 66.7 % / 28.6 % |
| 2 | WP-T1c ✔ | Which prior generator orders our basis better? | ~0 | winner, else the incumbent `forward` stays |
| 3 | WP-T1d | **Is the true support even a local optimum of our trajectory loss?** | **~12 h** | if no → **stop the branch** and report it as a loss finding, not a guidance finding |
| 4 | WP-T2a pilot | Does EvoGrow improve with a prior? dim 1 + dim 2, three arms | 130–420 h, local | see below |
| 5 | WP-T2a full | The same on dim 3, where the failure lives | ~1,000–1,600 h, Orion | only after the Phase C campaign ends |

**Step 4 carries three arms** — control (free, C-1 supplies it), guided, and **oracle prior** (ground
truth ranked first). The oracle arm is what makes the pilot conclusive in both directions:

- oracle prior fails → **stop.** Guidance is not the lever, learned for the price of one arm
  instead of one paper.
- oracle works, guided does not → the **prior generator** is the problem, not the idea.
- both work → guidance is established, and the distance between them says how much is left in the
  generator.

**Step 3 comes first because it can make steps 4 and 5 unnecessary.** It costs about 12 h — derived,
not guessed: roughly 2,900 fixed-structure fits at the measured 9.48 s per dim-2 fit, from
add-one (p−s), remove-one (s) and same-size swap (s·(p−s)) neighbours over 18 exact systems and both
IC sets. The first estimate recorded here was "under an hour", which was a per-cell figure for
dim 2 mistaken for the total. It asks something nobody has asked: the project holds cells at loss
6.8e-11 with `pruned_match = false`, so a *wrong* support reaches essentially zero loss.

**Within step 3 the decisive class is the same-size swap.** An added term cannot fit worse by
construction, so `add_one` winning is nesting, not evidence; `remove_one` winning means a true term
does not earn its place, which is an identifiability or optimizer finding. Only a same-size wrong
support beating the truth shows that the objective does not identify it. The three classes are
never aggregated into one number. If the true support is not even a local
optimum of the objective, no ordering can help, because the search converges correctly to something
wrong. That finding would belong to Paper 1 or Paper 3 — it is about the loss, not about guidance.

**Why exhaustive enumeration is not on the list.** Measured from the Phase B registry: a dim-2 cell
runs a median of 430 parameter fits at 9.48 s each. Enumerating all supports with |S| ≤ 4 in
trajectory space is 630,436 joint models per cell, or **1,660 h per cell** — about 33,200 h for the
ten exact dim-2 systems alone, more than twice the entire Phase C campaign, and dim 3 is four
million hours. In weak-form space the same enumeration is free, but it answers the ranking question
WP-T1 already answered rather than the question about our loss.

**What may reopen this plan:** a gate outcome, a cost finding that makes a step unaffordable, or a
blocking dependency. **What may not:** a result we dislike, an idea that arrives mid-flight, or a
threshold chosen after seeing data.

**Priority rule.** Paper 1's blocking items outrank every step above: the noise-scope decision
(§3), the completion of Phase C, and the claim-tracing audit. The branch runs in the gaps, not
against them.

### Kept separate, deliberately

The same trajectory-derived signal may serve stage progression and the stage cap — WP-L2 showed the
current promotion signal `r_k` is derivative-contaminated, and the integral form needs no pointwise
derivative. That is a **separate experiment** (WP-T2b). Paper 2 must not mix candidate-prior
effects, stage-cap repair and child-generation effects into one measurement; otherwise it is
afterwards unclear which change acted.

---

## 6. The bridge — representation expansion, not a paper

**Decided 2026-08-22, re-confirmed 2026-09-22.** Not a fourth paper. A methodical bridge:

```text
Paper 1  ->  conference insert  ->  Paper 2  ->  representation expansion (bridge)  ->  Paper 3
```

**The finding.** Four families take the catalogue from 20 to 58 of 63 systems: constant (+10),
rational saturation (+12), mixed monomials of degree ≥ 3 (+9), scaled trigonometry (+7). The
constant is done — it is in the canonical basis since the P3 freeze. After the four families the
return collapses; the last five systems need one family each.

**Why after Paper 2, and not before.** Paper 2 asks why recovery fails *although* the truth is in
the space. Widening the space first moves the candidate set, the collinearities, the optimization
landscape and identifiability at the same time, and Paper 2 could then isolate nothing.

**The countermeasure belongs to the decision, and it now binds Paper 3.** The removal and
replacement operators must be designed **catalogue-agnostically**. If they lean on polynomial
structure they do not transfer to the widened space, and the ordering costs exactly what it was
meant to save. This constraint moved from Paper 2 to Paper 3 with the operators on 2026-09-22 —
it must not be lost in the renumbering.

**Two further decisions that stand.** Step A and Step B are paid for once, together: a new basis
moves `config_fingerprint`, candidate counts, promotion points, the look-ahead, every cap, the cost
model and the regression block — for A exactly as for B, while 39 of 63 leaves out precisely the
interesting motifs. And the tail is not served: five operator families for five systems is where
benchmark completeness turns into benchmark overfitting. Those five stay declared **out-of-catalog
cases**.

**The catalogue must not be read off the benchmark it is then measured on.** Define it semantically
— offsets and forcing, polynomial self dynamics, polynomial interaction, saturating interaction,
oscillatory transformation — and let ODEBench measure its reach afterwards. Under that order the
coverage number is a property of the modelling philosophy rather than its definition, and it is
allowed to differ from 58. For the same reason "rational" is not an admissible family: `P(u)/Q(u)`
blows the space open. Admissible are **named mechanistic motifs** — `u/(K+u)`, optionally
`uⁿ/(Kⁿ+uⁿ)`, `sin(ωu)`, `cos(ωu)`.

**A precision worth keeping.** "Enumerable catalogue" is false once `sin(ωu)` with real `ω` is
admissible — that is a continuum of basis functions. What stays finite is the set of term
*templates*; each instance carries a few inner parameters under linear outer coefficients. The
method must be defined over templates, not over basis functions.

**The open risk, and it points the other way.** This counts representability, not findability. A
richer catalogue creates near-degenerate structures — `u/(u+K)` tends to a linear term for large `K`
— which is poison for support recovery. Representability is necessary, not sufficient, and the
expansion may make Paper 3 harder before it makes anything better.

**Evidence status (WP-R1).** In derivative space the current basis approximates surrogate systems
almost as well as exact ones — median 0.999993 against 0.999998 — and the ranking of the missing
families is close to the inverse of their system count: saturating interaction costs nothing in the
median, while mixed monomials of degree ≥ 3 are the one family with a real approximation loss, and
they need no inner parameters.

---

## 7. Paper 3 — Reversible / Corrective EvoODE

**Question.** How can EvoODE detect and correct wrong structural decisions made earlier in the
search?

Paper 1 grows structure. Paper 2 improves which terms are added. Paper 3 asks what happens when an
earlier decision was wrong anyway.

### The motivation is the project's sharpest negative result

The admissible space contains the true structure, the loss reaches 1e-11, and the recovered support
is still wrong. The obvious alternative explanations are already excluded: the space was right, the
stage was unlocked, the fit was excellent. `pruned_match = false` on coupled cells is not a fit
problem.

The diagnosis is available: the search grows only. A wrong early term can never leave a line.

```text
S0 -> S0 + term_a -> ... -> S3
```

If `term_a` was wrong, that lineage cannot undo it. Selection can kill the whole lineage; local
correction does not exist.

### The operators

Beyond `S → S + φ_j`, allow local support-space moves: **delete** `S → S − φ_k`, and
**replace** `S → S − φ_k + φ_j`. Evidence-driven rather than blind: delete a term that contributes
little unique explanatory value after refitting; replace an active term when an inactive one
explains the residual substantially better; add using the Paper 2 prior.

### Why this does not become GP

The distinction is the representation, not the vocabulary. EvoODE navigates a **support space over
an explicit catalogue** with equation-specific active terms and trajectory-space fitting. GP
generates expression trees with subtree mutation, operator insertion and crossover between arbitrary
structures.

**But the boundary is not `EvoODE ↔ GP`.** Between catalogue-based structural growth and GP sit
grammar-guided symbolic regression, beam search, MCTS, enumerative search and program synthesis. The
axis that orders the field is:

```text
statically bounded space  <->  controlled growing space  <->  freely compositional space
```

EvoODE sits in the middle, and the middle is thinly populated. It becomes GP-like only when it
starts freely generating nested symbolic expressions.

### Framing

Not "we added more mutation operators" — that is too thin. The question is whether **trajectory
evidence can be used not only to guide growth but to detect and repair structurally wrong
decisions**, producing reversible support refinement rather than blind mutation.

### Why it can be smaller

The limitation is already established by Papers 1 and 2, the mechanism is focused, the evaluation is
narrower, and the contribution is a search-operator extension rather than a new framework. A clean
comparison: add-only EvoGrow, guided add-only EvoGrow, guided reversible EvoGrow.

**Design Paper 3 from the residual failure modes of Paper 2, not from speculation.** Do not
implement before Papers 1 and 2 clarify how severe path dependence remains and which structural
errors dominate after guidance.

---

## 8. Dependencies

```text
Paper 1  grow the structure      -> establishes the method and its limits under noise and sampling
            |                       density; hands over structural recovery as a limitation
            v
insert   restart budget          -> removes a confound present in every comparison, and must precede
            |                       any guided-search comparison
            v
Paper 2  guide the growth        -> needs the insert, else search breadth and restart count move
            |                       together; identity conditional on WP-T1b
            v
bridge   expand representation   -> after Paper 2, so Paper 2 can isolate a cause
            |
            v
Paper 3  repair wrong growth     -> needs Paper 2's residual failure modes; operators must be
                                    catalogue-agnostic because of the bridge
```

Each stage is a precondition for the next. That is the property that makes this a thesis rather than
a sequence of results.

---

## 9. Guardrails

Across all papers:

- Do not claim an unrestricted model class.
- Do not blur support search with final coefficient fitting.
- Do not hide screening compute from total method cost.
- Do not mix exact and surrogate systems in one structure-correctness metric.
- Do not use dim-1 success as evidence for coupled-system success.
- Do not attribute gains to guidance while duplicate and multistart effects are uncontrolled.
- Do not extend into arbitrary expression-tree generation without explicitly acknowledging the shift.
- Always report both structure recovery **and** the R² > 0.9 rate; report support recovery **raw and
  pruned**.
- Never choose a threshold after seeing the results, and never remove a library component because it
  produces false positives.
- Wall-clock is never evidence. Cost claims rest on counts.
- Keep each paper centered on one dominant question.

---

## 10. What belongs in none of them

Line-search cost, the sentinel loss `1e6`, GPU, batched parameter fitting, threading over the
population, the `discover()` API cleanup. These are craft, not thesis. They may appear in a methods
section as cost context; they are not contributions.

`docs/hpc_requirements.md`, `SCRIPTS.md` and the provenance apparatus — three-field record identity,
behaviour fingerprint, frozen artefacts — are infrastructure. They earn a reproducibility appendix,
not a claim.

---

## 11. Open items this arc does not resolve

1. **The noise and sampling-density scope of Paper 1** — §3. The single largest unbudgeted cost.
   **Deferred 2026-09-23** until Phase C shows merit on noise-free data; re-open then, not before.
2. **Paper 2's identity**, pending WP-T1b — §5.
3. **Where the predictive criterion for cap failure lands.** Identifying in advance, without ground
   truth, where the controller will fail was the item that turned Paper 1's cap work from an
   observation into a claim. Under the current Claim A–D scope it has no owner.
4. **Whether the conference insert is written before or after Paper 1 is submitted.** Its data
   largely exists; its dependency runs to Paper 2, not to Paper 1.
