# 4 Failure analysis: how the controller was arrived at

The stage cap of §3.5 is not the first mechanism this project built for the same purpose. It is the
third, and the two that failed are reported here because they carry the argument: they show *which
kind* of evidence a staged search can and cannot act on. A reader who skips this section will read
the cap as an arbitrary heuristic; a reader who does not will see why each of its conditions has the
form it has.

## 4.1 v2.2 — stage-local progression is not enough (Gate 1)

The substrate of §3.3 replaced a single global plateau criterion with stage-local plateau detection
plus a minimum budget per stage. It works as a substrate — every later variant is built on it — and
it fails as a solution.

The failure is not a metric artefact. On coupled systems, support recovery stays wrong even after the
pruning rule of §3.6 is applied, and it stays wrong in cells where the loss reaches `1e-11` and where
the true structure is available at the currently unlocked stage. Both alternative explanations are
therefore excluded: the space contained the truth, and the fit was excellent.

What remains as explanation is the shape of the search operators, and this is stated as a limitation
of the method rather than repaired here: **growth is additive only**. Expansion adds terms, every
equation line starts from a single randomly chosen term, and selection is the only corrective. A
wrong term that enters a line early can never leave it, so a line can exhaust its term budget while
carrying a mixture of true and false terms. Removal and replacement operators are the obvious
response and are deliberately out of scope; they are the subject of separate work.

## 4.2 v3 — the right question asked of the wrong signal (Gate 2)

If a single global stage state is too coarse, the natural next step is per-equation stage state with
a per-equation promotion signal. v3 did exactly that: each equation carried its own stage, and
promotion was driven by an equation-local derivative residual `r_k`.

It failed on a pre-registered decision cell, and it failed twice over.

| Criterion | Target | Observed | Verdict |
|---|---|---|---|
| final stage of equation 1 | 3 | 5 | failed |
| support of `du_1` | exactly `{u_1, u_1², u_1·u_2}` | one extra term | failed |
| loss | ≤ 1.39e-3 | 2.52e-4 | met |

The better loss with the wrong structure is the whole story in one line.

Two mechanisms explain it. First, the promotion condition compared `r_k` against a tolerance of
`1e-8`, while the residual floor on coupled systems sits around `1e-3`. The condition is therefore
unreachable: it cannot distinguish an under-modelled equation from one that has hit an irreducible
floor. Second, `r_k` is contaminated by derivative-estimation error, and a model's capacity to
absorb that error grows with its term count — so the signal is systematically biased toward "more
terms help".

Downstream confirmation: on one system the v3 substrate alone loses about six orders of magnitude
against v2.2.

The lesson that survives into the cap is not "per-equation was wrong" — the cap is per-equation too.
It is:

> v3 changed **who** decides. It did not change **what evidence** justifies the decision.

Concretely: an absolute tolerance cannot serve as a promotion criterion when the achievable residual
is set by the data, and any signal read off a derivative estimate must be judged against that
estimate's own error. Both properties are built into §3.5 — every condition is relative, and the
noise floor is estimated rather than assumed.

## 4.3 Three design rules, each bought with a defect

The cap's conditions were not designed in advance. Each was forced by a failure of an earlier
version, and each is reported with the failure that produced it.

**Rule 1 — a cap requires positive evidence, never the absence of evidence.**
*Bought with:* a system whose derivative estimate resolves nothing. An early version capped whenever
no later gain appeared, which conflates "later stages do not help" with "we cannot tell whether they
help". On that system the correct answer is no cap at all, and the method now says so: a gain must
have been observed before a cap may be issued. The system in question caps at nothing everywhere and
is reported as the identifiability boundary of the method rather than as a failure cell.

**Rule 2 — look ahead as far as the basis creates structural gaps.**
*Bought with:* the horizon audit over all 20 exact systems, both initial-condition sets and horizons
2 to 5, i.e. 80 equation rows. The basis stages by degree, not parity, so an odd nonlinearity first
becomes approximable two stages later than its degree suggests. With the originally shipped horizon
of 2, six rows were truncated below the stage they demonstrably need. Raising the horizon moves
exactly those rows and every new cap lands precisely on the required stage — including one row that
moves from *no cap* to a finite cap, i.e. the longer look-ahead makes the controller **tighter**, not
looser. Horizons 3, 4 and 5 are cap-identical on all 80 rows, so the parameter is inert; setting it
to the number of basis stages removes it from the method rather than tuning it.

**Rule 3 — credit a mechanism only through an experiment that isolates it.**
*Bought with:* the most expensive detour in the project. After the horizon fix, five equation rows
still truncated. They were derivative-driven: with analytic derivatives all five reach the required
stage, and a 5×5 sweep of the two thresholds over four orders of magnitude repairs none of them —
so thresholds were ruled out empirically rather than by argument. Two candidate repairs were then
introduced together: a *reopen branch* (a later stage that drops the residual well below the floor
reopens the walk) and a *doubt band* (an ambiguous region in which the decision abstains and issues
no cap). The combination worked, and the doubt band was credited with it.

It was later measured on its own, over all 80 rows:

| | |
|---|---|
| caps correct | 77 |
| caps wrong | 0 |
| wrong caps **prevented by the band** | **0** |
| correct caps **surrendered to the band** | **3** |

The repair came entirely from the reopen branch — the rows the band was built for return the correct
cap under a binary decision as well. The band was removed. Finite caps rose from 45 to 48, exactly
the three rows the measurement predicted.

The price of the abstention had also been measured before removal, and it is worth reporting because
it is the shape of trade the method is willing to make: the one cell that lost its cap to the band
cost **+16 % loss evaluations at a bit-identical loss** — compute, never the solution.

## 4.4 What the cap does not do, and what remains uncertain

**It does not repair structural recovery.** The cap bounds the space; it does not change the
operators that search it. Support recovery on coupled systems remains wrong for the reason given in
§4.1, and the cap neither helps nor hurts it: across the regression grid, pruned support matches are
unchanged in every cell.

**It is auditable only where ground truth exists.** Cap correctness can be checked on the 20 exactly
representable systems. On the 43 surrogate systems there is no true support, so controller safety is
unverifiable by construction. Several of those systems carry an equation capped at stage 1; because
they are scored on approximation quality, that is a fit-quality risk rather than a support error —
but it is a risk, and it is not detectable from within the method.

**Two constants remain, and one of them cannot be derived.** The reopen ratio 0.35 and the
floor-depth guard 0.1 are configuration, and both are inside the configuration fingerprint so that
moving either moves the identity of every record. The guard separates the control system's floor
ratios (0.03–0.07) from the target rows (0.30–0.85) by a factor of four; that is a verified margin,
not a derivation.

The reopen ratio is worse than that, and the paper reports it as a result rather than a detail.
Leave-one-system-out over the 20 exact systems selects values between 0.044 and 0.278, while the
shipped value is 0.35 — and at every selected value the control system truncates again. The margin
between 0.35 and the worst ratio the control system produces, 0.315, is 11 %. **The threshold that
separates the safe from the unsafe region cannot be selected from the data available.** This was the
intended weak point of the work; it became one of its findings.

**Aggregation is not robust.** Per-equation caps are the majority over cross-validation splits, and
rows flip through split majorities rather than through clear detection. In one row a single split
changed the outcome. This is open.

**The cap decides in derivative space, and that space can misrank.** Every condition in §3.5 is
evaluated on weighted least-squares residuals of estimated derivatives, against a floor derived from
an estimate of the derivative error. Recent work on system identification shows that transforming a
trajectory problem into an algebraic derivative problem can produce *deceptive* search spaces, in
which the ground-truth equation carries worse fitness than its competitors even on noise-free data,
and in which a state-of-the-art search is demonstrably misled; the effect correlates with the
sampling step and weakens as the step shrinks (Tonda et al., 2025).

This work is exposed to that mechanism at exactly one point, and it is worth being precise about
where. The warm start of §3.4 is *not* the exposure: it only initialises a fit whose objective is
the simulation loss, so a misranked derivative space costs iterations rather than decisions. The cap
is the exposure, because its walk consists of decisions taken on that objective.

Four things bound the risk, and none of them removes it. The rule demands positive evidence rather
than the absence of it; every condition is relative rather than absolute; the floor is estimated
from the data rather than assumed; and the audit over the exactly representable systems finds no
truncated equation row. The sampling grid used here is also 3.4 times denser than the published
benchmark protocol, which places this work on the mitigating side of the effect. But the mechanism
is real, and an independent measurement in this project reproduces its signature: of 126 full-basis
reference fits computed in derivative space, 13 diverge when integrated, and on the exactly
representable systems the mean trajectory R² is −2.8 against a median of 0.9999. A near-perfect
derivative fit is not a usable dynamical model.

The honest formulation for the method is therefore: derivative-space optimisation is a legitimate
computational surrogate, but trajectory-space verification is what decides, and any decision that
*cannot* be moved to trajectory space — the cap is one — inherits this limitation.

**The behaviour fingerprint is narrow.** It observes the decision function of §3.5 and nothing else:
derivative estimation, floor computation, split aggregation and the search loop are unobserved by it.
A change in any of those would leave all three identity fields standing.
