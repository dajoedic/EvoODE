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

We adopt the dataset's sampling protocol but **integrate the trajectories ourselves**:

| Component | Setting |
|---|---|
| Time span | `t ∈ [0, 10]`, as shipped |
| Sampling | 512 uniform points, both endpoints included |
| Initial conditions | both shipped sets per system |
| Integration | `Tsit5`, `abstol = reltol = 1e-9` |
| Noise | none |

The shipped trajectories are not used. Their solver accuracy would impose mean-squared-error floors
between `2.5e-2` and `6.1e-10` depending on the system, which is above the loss that the method
reaches on several systems — the benchmark's own data would become the limiting factor rather than
the method. Grid density matters for a second reason: at 512 points, two safety violations observed
on a coarser grid disappear.

**This is a deviation in our favour and is declared as such.** If published results for other methods
were computed on the shipped trajectories, those methods worked on noisier data than we do, and no
comparison of absolute error values between them and this work is admissible until the protocol
audit (§5.5) establishes otherwise.

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
rather than a refinement: **representational adequacy**, split into two columns.

- *In principle representable* — could the method's model class express the true structure at all?
- *Representable under the evaluated protocol* — was it reachable under the operators, library,
  complexity limits and constraints actually used in the published run?

The distinction is not pedantic. A sparse-regression method can carry an arbitrary library, but a
run using polynomials to degree three cannot express a saturating term; a genetic-programming system
can permit an operator and still place it out of reach through a complexity penalty; a pretrained
sequence model is additionally bounded by its training distribution. Comparing fit quality on a
system that a method cannot represent measures the library, not the search — and that holds for this
work exactly as much as for the others, on the 43 systems where our own basis falls short.

**Status:** the external columns are unfilled at the time of writing. Until they are, this paper
makes no claim of victory or defeat against any published method.

## 5.6 Provenance

Every record carries the three identity fields of §3.7. Before any result is reported, the record set
is checked for uniformity across all three; a set that is not uniform is not publishable and is
re-run. This has already been enforced once: an earlier ablation grid was recomputed in full after a
change to the cap's decision logic, because the configuration fingerprint alone had not moved.

Records from the pilot and from cost-model probes predate the current identity by construction. They
are valid measurements of infrastructure and cost, they are reported as such where relevant, and
they are never merged into the result set.
