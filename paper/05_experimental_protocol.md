# 5 Experimental protocol

## 5.1 Systems

All 63 systems of the ODEBench collection, a curated set of textbook models from population
dynamics, chemical kinetics, epidemiology and mechanics, with published parameter values and two
initial conditions per system.

The systems are partitioned once, mechanically, and the partition governs every metric that follows.
A system is **exact** if every one of its equations is a linear combination of terms in the staged
basis of §3.2, and **surrogate** otherwise. The classification is derived by symbolic comparison of
each equation against the basis, one record per equation; a system counts as exact only if all of
its equations do. The split is 20 exact and 43 surrogate systems.

The surrogate side is not homogeneous, and the paper reports what it is made of: 82 uncovered terms
across the 117 equations, falling into constant offsets, saturating (rational) responses, mixed
monomials of degree three and above, trigonometric terms with a scaled argument, and a small tail of
one-off forms — logarithmic growth, a non-integer power law, a degree-five polynomial, an
exponential response, and a signed quadratic drag term.

## 5.2 Data generation

We keep the systems, parameterizations and initial conditions of the benchmark and **integrate the
trajectories ourselves** on the grid our copy of the artefact carries:

| Component | Setting |
|---|---|
| Time span | `t ∈ [0, 10]`, as shipped |
| Sampling | 512 uniform points, both endpoints included |
| Initial conditions | both shipped sets per system |
| Integration | `Tsit5`, `abstol = reltol = 1e-9` |
| Noise | none |

We preserve the ODEBench systems, parameterizations, initial conditions and sampling grid, but
regenerate the trajectories at stricter numerical tolerances, to keep solver-error floors from
interfering with the accuracy regime studied here. Those floors are not hypothetical: on the shipped
trajectories they range from `2.5e-2` to `6.1e-10` depending on the system, above the loss this
method reaches on several of them. Grid density matters for a second reason: at 512 points, two
safety violations observed on a coarser grid disappear.

The consequence is stated plainly rather than argued away: **published ODEBench numbers obtained on
the released trajectories are not treated as directly comparable to ours.**

*Dataset version, and a difference that matters.* "ODEBench" alone is not a sufficient protocol
statement, and in this case the ambiguity is real rather than hypothetical. The published
description of the artefact specifies LSODA integration with `rtol = 1e-5`, `atol = 1e-7` and
`t_eval = linspace(0, 10, 150)` — **150 points per trajectory**. The copy used here carries **512**
points over the same span, verified directly in the file (content hash
`b11f8bda01ceee5c5c9445521ac74c8819361af4251bb90c0be398aaeb1a1136`, 63 systems, two
initial-condition sets, shipped solutions present but unused).

Our grid is therefore **3.4 times denser** than the published protocol — `Δ ≈ 0.0196` against
`Δ ≈ 0.067` — in addition to the tighter integration tolerances. This is stated here because it is
the larger of the two deviations and because sampling density is not a neutral axis: it is the axis
under which the derivative transformation is known to produce misleading search spaces, and under
which reducing the step mitigates them. Our denser grid places this work on the favourable side of
that axis. *(Artefact origin — repository commit, release or DOI — to be completed.)*

## 5.3 Conditions and grid

Two conditions, differing only in whether the least-squares warm start of §3.4 is enabled:

```text
63 systems × 2 conditions × 3 seeds × 2 initial-condition sets = 756 runs
```

No genetic-programming baseline, no earlier EvoGrow variants. The comparison against the uncapped
substrate is carried by a separate, smaller regression grid (§5.4), because the campaign's purpose
is characterising the capped method across the full benchmark rather than re-running an ablation 63
times.

Pretuning is a condition, not a claim. One measurement constrains how it may be discussed: on three
chaotic three-dimensional systems the runtime ratio between the two conditions was 0.30, 0.92 and
0.97 — a factor of three apart within a single dimension class. Any statement about the cost of
pretuning is therefore per system or per class, never a single global factor.

## 5.4 The ablation grid

The controller's effect is measured on a dedicated grid: 5 systems × 3 seeds × 2 initial-condition
sets, run under both the capped variant and the uncapped v2.2 substrate, 120 records under a single
identity triple.

This grid answers the question the campaign cannot: what changes when the cap is switched off, all
else held exactly equal.

## 5.5 Comparability with published results

No external baselines are run in this work. Published numbers may be cited as context only, and the
conditions under which they become comparable are recorded in a protocol audit that tabulates, per
published source: systems used, initial conditions, time span, sampling grid, noise setting, metric
definition, and aggregation.

The audit carries one dimension that comparisons in this area usually omit, and it is a prerequisite
rather than a refinement: **representational adequacy**, in three columns.

- *In principle representable* — could the method's model class express the true structure at all?
- *Representable under the evaluated protocol* — was it reachable under the operators, library,
  complexity limits and constraints actually used in the published run?
- *Best attainable functional fit* — how well can that space fit the observed dynamics irrespective
  of search error? This column is **optional**: we can report it for our own method from a
  search-free reference fit, and it will be unavailable for most published runs. An audit may not
  impose a requirement that only its authors can satisfy, and *not reported* is itself a finding.

The distinction is not pedantic. A sparse-regression method can carry an arbitrary library, but a
run using polynomials to degree three cannot express a saturating term; a genetic-programming system
can permit an operator and still place it out of reach through a complexity penalty; a pretrained
sequence model is additionally bounded by its training distribution. Comparing fit quality on a
system that a method cannot represent measures the library, not the search — and that holds for this
work exactly as much as for the others, on the 43 systems where our own basis falls short.

Two sources are in scope, and only two: the benchmark source itself, and a methodological study of
how the derivative transformation reshapes the search landscape (Tonda et al., 2025). The second is
not a performance reference. It matters because the warm start of §3.4 and the reference fit above
both operate in derivative space, and because this work reproduces the effect it describes: of 126
full-basis reference fits, 13 diverge on integration despite near-perfect derivative fits.

**Status:** the external columns are unfilled at the time of writing. Independently of them, this
paper makes **no quantitative cross-method performance claim** — not a cautious one and not an
approximate one. What it does state is protocol: which conditions would have to hold for published
numbers to be comparable, and which of them are unverified.

## 5.6 Provenance

Every record carries the three identity fields of §3.7. Before any result is reported, the record set
is checked for uniformity across all three; a set that is not uniform is not publishable and is
re-run. This has already been enforced once: an earlier ablation grid was recomputed in full after a
change to the cap's decision logic, because the configuration fingerprint alone had not moved.

Records from the pilot and from cost-model probes predate the current identity by construction. They
are valid measurements of infrastructure and cost, they are reported as such where relevant, and
they are never merged into the result set.
