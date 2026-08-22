# Paper 1 — ODEBench Protocol Alignment Audit

Status: **in progress.** The EvoODE side is verified against the repository and the dataset, and
§1.5 carries the protocol as it runs since 2026-08-22.
The published-source columns are **not yet verified** and are marked as such; nothing in this
document may be cited as a comparison until they are.

Purpose, per `PAPER_1.md` Phase 3: determine whether published ODEBench-related numbers may
be described as directly comparable, approximately comparable, or contextual only. If
protocol equivalence is not established, external numbers must not be framed as a benchmark
victory or defeat.

Last updated: 2026-08-22.

---

## 1. Verified: EvoODE against the dataset

Checked directly against `benchmarks/data/strogatz_extended.json` for the ten benchmark
systems (ids 2, 3, 11, 23, 24, 26, 31, 37, 54, 63).

### 1.1 Initial conditions — match, but only one of two

Every `u0` in the `BENCHMARKS` table of `benchmarks/benchmark_evogrow.jl` reproduces the
dataset's **first** initial-condition set exactly, for all ten systems.

The dataset provides **two** initial-condition sets per system. EvoODE uses only the first.
Any published number aggregated over both initial conditions therefore covers a strictly
larger evaluation set than ours.

### 1.2 Time span and sampling grid — mismatch

**Our copy of** the dataset ships every system on a uniform grid of **512 points over t ∈ [0, 10]**
— see the correction in §2.4, which shows this is *not* the sampling the literature describes.
EvoODE
uses a per-system time span and point count:

| System | EvoODE tspan | EvoODE T | points per time unit | dataset |
|---|---|---|---|---|
| 2 | (0, 12) | 120 | 10.0 | 512 over [0, 10] = 51.2 |
| 3 | (0, 20) | 200 | 10.0 | 51.2 |
| 11 | (0, 5) | 100 | 20.0 | 51.2 |
| 23 | (0, 25) | 250 | 10.0 | 51.2 |
| 24 | (0, 15) | 200 | 13.3 | 51.2 |
| 26 | (0, 10) | 200 | 20.0 | 51.2 |
| 31 | (0, 20) | 200 | 10.0 | 51.2 |
| 37 | (0, 20) | 200 | 10.0 | 51.2 |
| 54 | (0, 15) | 300 | 20.0 | 51.2 |
| 63 | (0, 30) | 300 | 10.0 | 51.2 |

No system matches the dataset grid. System 26 matches the time span but not the sampling.
EvoODE trajectories are between 2.6 and 5.1 times sparser in time, and several cover a
substantially longer horizon than the dataset — System 63 runs to t = 30 against the
dataset's t = 10.

This has two consequences that must not be conflated:

- **For comparability.** Different time spans and sampling densities mean different data.
  Results are not directly comparable to published numbers computed on the dataset grid.
- **For our own results.** A longer horizon puts more of the trajectory into the collapsed
  tail after the transient, which is exactly the regime where the look-ahead study found
  degenerate design matrices and uninformative holdout blocks.

### 1.3 Connection to a known limitation

WP-L3 measured that on System 54 the stage-3 cliff is not resolvable at the EvoODE sampling
density, and becomes resolvable at roughly twice that density. The dataset grid is 2.56
times denser in time than EvoODE's System 54 grid (51.2 against 20 points per time unit).

Adopting the dataset grid would therefore plausibly remove the remaining stage-cap safety
violations. **Run and confirmed on 2026-08-03 (WP-G1): both violations disappear** — System 54
goes `[nothing, 2, 2]` → `[nothing, 3, 3]`. See §3.

### 1.4 EvoODE protocol before Phase B (historical)

This describes the state **before** the Phase B protocol decision in §3, which supersedes the
initial-condition, time-span and sampling rows. It is kept because §1.2 and §1.3 argue against it;
for what runs today see §1.5.

| Dimension | EvoODE |
|---|---|
| Systems | 10 of 63 run; all 63 classified (WP-P3.1); all 63 planned for Phase B |
| Initial conditions | dataset set 0 only, one per system |
| Time span | per system, see table above |
| Sampling grid | uniform, per-system T, see table above |
| Trajectory generation | `Tsit5`, `abstol = reltol = 1e-9` |
| Noise | none |
| Evaluation metric | simulation MSE; R² not yet implemented |
| Structure metric | `exact_support_match_raw` and `_pruned`, exact systems only |
| Aggregation | mean and standard deviation over seeds, per system |
| Seeds | 3 in the regression suite (42, 123, 7); 5 in the frozen Phase A |

### 1.5 EvoODE protocol as it runs today

State of 2026-08-22, i.e. the campaign started on that date under
`git 91f88c46063fa368101326cbfe1abcdfc9d857fc`.

| Dimension | EvoODE |
|---|---|
| Systems | **all 63**, campaign running; 20 exact / 43 surrogate by derived classification |
| Initial conditions | **both** dataset sets per system |
| Time span | `t ∈ [0, 10]` for all systems, as shipped |
| Sampling grid | 512 uniform points, both endpoints included |
| Trajectory generation | `Tsit5`, `abstol = reltol = 1e-9` — **self-integrated**, see §3 |
| Noise | none |
| Evaluation metric | simulation MSE **and R²** (implemented in WP-M1; R² is the reported metric for the 43 surrogate systems) |
| Structure metric | `exact_support_match_raw` and `_pruned`, exact systems only |
| Aggregation | per system, over seeds; the two IC sets are reported separately, not averaged |
| Seeds | 3 (42, 123, 7) |
| Conditions | `pretune_on` and `pretune_off` |
| Record identity | git hash, config fingerprint, stage-cap behaviour fingerprint |

---

## 2. Not verified: published reference sources

The following must be filled from the actual publications before any comparison is drawn.
They are listed as dimensions to check, not as claims.

| Dimension | ODEFormer / ODEBench | PySR / SINDy numbers reported there | Other sources |
|---|---|---|---|
| Systems used | to verify | to verify | to verify |
| Initial conditions | to verify — dataset ships two sets | to verify | to verify |
| Time span | to verify — dataset ships [0, 10] | to verify | to verify |
| Sampling grid | **two exist upstream**: 512 points in the committed JSON, 150 from the regeneration script — which one a run used must be checked, see §2.4 | to verify | to verify |
| Noise setting | to verify | to verify | to verify |
| Metric definition | to verify — R² threshold expected | to verify | to verify |
| Aggregation | to verify | to verify | to verify |
| Success criterion | to verify | to verify | to verify |
| **Representable in principle** | to verify | to verify | to verify |
| **Representable under the evaluated protocol** | to verify | to verify | to verify |
| **Best attainable functional fit** *(optional)* | to verify | to verify | to verify |

The last two rows were added on 2026-08-22 and are per system rather than per source as a single
verdict: *in principle* asks whether the method's model class could express the true structure at
all, *under the evaluated protocol* whether it was reachable given the operators, library,
complexity limits and constraints of the published run. A saturating term is out of reach for a
sparse-regression run restricted to polynomials of degree 3 however rich the method could be in
principle. A third row was added on the same day: **best attainable functional fit** — how well the space can
fit the dynamics irrespective of search error. It is **optional**. EvoODE can report it from
`docs/WP-R1.md`; most published runs cannot, and an audit must not impose a requirement only its
authors can meet. *Not reported* is a finding.

**All three rows apply to EvoODE itself first:** our basis represents 20 of the 63 systems exactly,
and the search-free reference quantifies how well it approximates the rest. Rationale in
`docs/diskussion_vergleichsmethoden.md`.

### 2.1 Sources in scope — decided 2026-08-22

Two, and only two, for Paper 1:

| Source | Role |
|---|---|
| **ODEFormer / ODEBench** | benchmark definition, protocol, and context — it reports several method families on the same benchmark, so part of the representation audit is fillable from one place |
| **Tonda et al. 2025**, *When Data Transformations Mislead Symbolic Regression: Deceptive Search Spaces in System Identification* | methodological evidence, **not** a performance reference: the derivative transformation can produce deceptive search landscapes |

Everything else is context at most. The broad, quantitative comparison — SINDy as fixed library,
PySR as free symbolic search, a pretrained symbolic model, EvoODE as controlled growth — belongs to
Paper 3, where it is the purpose rather than a side claim.

### 2.2 Dataset provenance — closed 2026-08-22, see §2.4

"We use ODEBench" is not a sufficient protocol statement: repository states and releases can differ
in point counts, generators and solver defaults. The provenance was not recorded anywhere in this
repository until 2026-08-22; it is now established in §2.4. What the file itself gives:

```text
file    benchmarks/data/strogatz_extended.json
sha256  b11f8bda01ceee5c5c9445521ac74c8819361af4251bb90c0be398aaeb1a1136
in repo since  706549f (2026-04-30)
content 63 systems, all carrying shipped solutions
```

The per-system `source` field names the textbook location ("strogatz p.20"), not the dataset. Origin
and upstream commit are in §2.4. The shipped trajectories are **not** used: we integrate ourselves on
the artefact's own 512-point grid.

### 2.3 How our own trajectory generation is to be described

Not "we use cleaner ODEBench data" — that devalues the original protocol and invites the obvious
retort. The wording to use:

> We preserve the ODEBench systems, parameterizations, initial conditions and sampling grid, but
> regenerate trajectories at stricter numerical tolerances to avoid solver-error floors interfering
> with the accuracy regime studied here.

And the consequence, stated plainly: published ODEBench numbers obtained on the released
trajectories are not treated as directly comparable.

Open questions that decide comparability:

1. Do published results use both initial-condition sets or one?
2. Is the reported metric an R² threshold, and at what value, and computed on the trajectory
   or on the derivatives?
3. Is any noise added, and are results reported per noise level?
4. Are failed or diverged runs excluded from the aggregate, or scored as failures?

Until these are answered, published numbers are **contextual only**.

---

### 2.4 The 150 / 512 discrepancy — resolved, and the provenance gap with it

**Investigated 2026-08-22 after auditing Tonda et al. The first reading of this was wrong and is
corrected here.**

Tonda et al. describe the ODEBench artefact as 150 uniformly sampled points per trajectory
(`LSODA`, `rtol=1e-5`, `atol=1e-7`, `first_step=1e-6`, `min_step=1e-10`,
`t_eval=np.linspace(0,10,150)`). Our copy carries **512** points. The first conclusion drawn was
that our file must be a different version or generation configuration. **It is not.**

**Verified provenance.** The file is byte-identical to the upstream artefact:

```text
file     benchmarks/data/strogatz_extended.json
sha256   b11f8bda01ceee5c5c9445521ac74c8819361af4251bb90c0be398aaeb1a1136
upstream github.com/sdascoli/odeformer, odeformer/odebench/strogatz_extended.json
         last upstream change 32dd990839ae, 2023-09-29 ("Code release") — downloaded and compared
in repo  unchanged since the first commit; identical at 366a71a, 78143e7, 706549f and HEAD
```

The `benchmarks/odeformer/` directory it originally sat in already recorded its origin; the
restructure at `706549f` was a pure rename with no content change.

**Where the discrepancy actually lives: inside the upstream repository.** The generation script in
the same directory, `odeformer/odebench/solve_and_plot.py`, carries

```python
config = {"t_span": (0, 10), "method": "LSODA", "rtol": 1e-5, "atol": 1e-7,
          "first_step": 1e-6, "t_eval": np.linspace(0, 10, 150), "min_step": 1e-10}
```

and writes its output to **`solutions.json`**, *not* into `strogatz_extended.json`. The committed
`strogatz_extended.json` — the file everyone actually downloads, and the one we use — carries
512-point solutions under its `solutions` key.

So the repository ships two different samplings: 512 points in the committed JSON, 150 points from
the regeneration script. Tonda et al. describe the latter.

**What this changes for us.**

1. **Our sampling is the artefact's own grid**, not a deviation. The claim "we adopt the dataset's
   sampling" is correct after all, for the committed file.
2. **The comparability question moves rather than disappears.** It is now: which of the two grids
   did a given published run use? A run driven by the regeneration script sampled 3.4x more coarsely
   (`Δ ≈ 0.067` against our `Δ ≈ 0.0196`). This must be checked per source and cannot be assumed.
3. **The axis still matters.** Tonda et al. find the sampling step strongly correlated with whether
   the transformed search space misleads, and report that reducing it mitigates the effect. Whoever
   sampled at 150 was on the unfavourable side of that axis; the difference is a genuine
   confounder in any comparison, in our favour.
4. **The remaining deviation is the tolerance**, and it stands unchanged: we integrate ourselves at
   `abstol = reltol = 1e-9` against the artefact's `rtol=1e-5, atol=1e-7`. WP-G1b measured what that
   buys for the stage cap specifically: **nothing** — shipped and self-integrated data give
   identical caps in all 26 measured cells, because the integration error of the shipped data is
   smooth in `t` and a derivative-based noise floor barely sees smooth error. The gain observed on
   System 54 belongs to grid density, not to data quality. Self-integration is retained for the
   search loss, where the shipped tolerances would impose MSE floors above what the method reaches.

**Provenance gap from §2.2: closed.** Origin, upstream path, upstream commit and content hash are
recorded above.

### 2.5 Source audited: Tonda et al. 2025 — what it says and what it costs us

Read in full on 2026-08-22.

**Bibliography.** Alberto Tonda, Hengzhe Zhang, Qi Chen, Bing Xue, Mengjie Zhang, Evelyne Lutton.
*When Data Transformations Mislead Symbolic Regression: Deceptive Search Spaces in System
Identification.* GECCO '25 Companion, Malaga, pp. 2563–2571. DOI 10.1145/3712255.3734301.
CC-BY, 9 pages.

**What it studies.** The two most common ways of turning trajectory data into a problem that
standard symbolic regression can handle — the derivative transformation and an integral
transformation — evaluated on ODEBench with PySR as the search method.

**The three findings, in their order of importance for us:**

1. **Misleading search spaces arise without any noise.** In the transformed space the ground-truth
   equations, which ought to be the global optima, carry *worse* fitness than other candidates, and
   the authors show experimentally that a state-of-the-art SR algorithm is duly misled.
2. **The sampling step is strongly correlated with the effect**, and reducing it mitigates the
   problem. Their explanation: the forward-difference basis of the transformation produces large
   errors where the derivative changes quickly.
3. **Noise degrades both transformations markedly**, to different degrees.

**Their practitioner recommendation:** noise-free, the order-4 derivative transformation performs
best; under noise, derivative transformations with Savitzky-Golay smoothing (degree 3, window 15 or
25).

**Where this hits EvoODE — and it is not where we first assumed.**

The obvious reading is that the warm start is affected, since it fits in derivative space. That is
true but harmless: the warm start only *initialises* a fit whose objective is the simulation loss,
so a misranked derivative space costs iterations, not decisions.

**The stage cap is the real exposure.** Its entire walk is a sequence of decisions taken on weighted
least-squares residuals in derivative space, against a floor derived from a Richardson estimate of
the derivative error. That is precisely a derivative-space objective used to *decide*, and Tonda et
al. show such objectives can rank the truth below its competitors. The mitigations already in the
design are real — the cap requires positive evidence, all conditions are relative, the floor is
estimated rather than assumed, and the audit finds 0 truncated rows of 80 — but the mechanism-level
threat is genuine and belongs in the limitations rather than in a footnote.

**Two convergences worth reporting.**

- Their central phenomenon is reproduced independently by our own search-free reference: of 126
  full-basis fits, **13 diverge on integration** despite near-perfect derivative fits, and on the
  exact systems the mean trajectory R² is −2.8 against a median of 0.9999. Same effect, different
  measurement, different codebase.
- Their stated future direction — *anticipate when the transformation will mislead, from the
  characteristics of the trajectory data* — is, in different words, this project's open "predictive
  criterion" question. That is a strong external motivation for it.

**What the paper does not give us.** It is not a performance reference and must never be used as
one: different task framing, different method, and a stated focus on comparing transformations
rather than ranking systems.

### 2.6 Source audited: ODEFormer / ODEBench — the benchmark source

Read in full 2026-08-22 (arXiv 2310.05573, ICLR 2024; d'Ascoli, Becker, Mathis, Schwaller,
Kilbertus). Items the paper does not state are marked as such rather than guessed.

**Benchmark construction — verified.** 63 ODEs: 23 one-dimensional, 28 two-dimensional, 10
three-dimensional, 2 four-dimensional; **4 chaotic**. Curated primarily from Strogatz's *Nonlinear
Dynamics and Chaos* plus well-known systems from other sources, selected for having been proposed as
models of real phenomena or for being 'iconic'; realistic parameter values chosen where suggested.
Typically one parameter set per equation — systems whose behaviour changes qualitatively across
regimes appear as **separate equations** (Lorenz occurs in a chaotic and a non-chaotic regime).
**Two manually chosen initial-condition sets per equation**, included specifically to evaluate
generalization. The dimension breakdown matches our classification exactly.

**Sampling grid — not stated in the paper.** Appendix A describes the curation and mentions "well
integrated solution trajectories" without solver, tolerances or point count. Those live in the
artefact, where the two values of §2.4 disagree. **Which grid the published evaluation used cannot
be established from the paper** — the most consequential open item in this audit, and an artefact
question rather than a reading one.

**Metric and success criterion — verified, and it is not ours.** The paper uses
`R² = 1 − Σ(y − ŷ)² / Σ(y − ȳ)² ∈ (−∞, 1]` and states explicitly that because R² is unbounded from
below, **average R² is not reported**. The headline quantity is

> the percentage of predictions for which R² exceeds a threshold of **0.9**

Two settings are evaluated **separately**: *reconstruction* (integrate the inferred ODE from the
same initial condition) and *generalization* (integrate from the second initial condition).
Generalization accuracy is substantially lower throughout.

**Consequence:** a thresholded rate over all 63 systems is not commensurable with either of our
metrics — support recovery on the 20 exact systems, mean R² on the 43 surrogates. Even under an
identical data protocol the numbers would not compare. This is an independent reason for the
no-cross-method-claim rule, on top of the protocol questions.

**Perturbation protocol — verified.** Multiplicative Gaussian noise `x_j(t_i) ← (1 + ξ)·x_j(t_i)`
with level drawn uniformly from `[0, 0.1]`, and subsampling with ratio drawn uniformly from
`[0, 0.5]`; result figures use grids such as 0 %/5 % noise and 0 %/25 % subsampling. Phase B is
noise-free and fully sampled, i.e. it sits at the easiest corner of that grid — a further declared
difference.

**Baselines — verified.** AFP, FE-AFP, EHC, EPLEX and PySR (genetic programming), SINDy (sparse
regression), FFX (regularized regression), ProGED (Monte-Carlo over probabilistic context-free
grammars). Apart from ProGED and SINDy all were developed for *functional* SR and adapted to the
dynamical setting via derivative estimation. **A separate hyperparameter optimization is run per
run**, stated as a fairness measure.

**Derivative handling — verified, and directly relevant.** Temporal derivatives are computed by
**finite differences with a hyperparameter search over the approximation order and optional
Savitzky-Golay smoothing**. That is precisely the transformation whose failure mode §2.5 documents:
the published baseline numbers are numbers *after* a tuned derivative transformation.

**Representational adequacy — partially fillable from this source.** The evaluated search spaces are
documented:

| Method | Search space as evaluated |
|---|---|
| SINDy (poly) | `[polynomials]`, degree searched over 1–10 |
| SINDy (esc) | `[polynomials, sin, cos, exp]` and `[polynomials, sin, cos, exp, log, sqrt, 1/x]` |
| ProGED | grammars: polynomial, universal, rational, simplerational, trigonometric |

This is enough to fill the *representable under the evaluated protocol* column per system for those
methods, which is what the column was introduced for.

One observation that applies symmetrically to us: **SINDy fits a linear combination of fixed library
functions**, so a saturating response `u/(K + u)` with unknown `K` lies outside the span of *every*
library above — `1/x` does not help, because the constant sits inside the nonlinearity. The methods
differ in where their boundary runs, not in whether they have one. ProGED's rational grammars and
the GP methods with a division operator are the ones that reach such forms.

**Unverified after this reading.** Which sampling grid the evaluation used; whether the evaluation
interval is `[0, 10]` as in the artefact or `[1, 10]` as stated for the model's own setting; and the
per-system results, which are given as figures rather than tables.

## 3. Phase B sampling protocol — decided 2026-08-03

The question was originally framed as a binary choice between adopting the dataset grid and
keeping the per-system grid. WP-G1 and WP-G1b showed that framing to be wrong: "adopting the
dataset grid" has two separable components, and the measurement says they should be separated.

**Decision: adopt the dataset's sampling protocol, integrate the trajectories ourselves.**

| Component | Decision |
|---|---|
| Time span | t ∈ [0, 10], as shipped |
| Sampling | 512 uniform points, spacing `10/511`, both endpoints included |
| Initial conditions | **both** sets per system |
| Trajectory source | **our own integration**, `Tsit5`, `abstol = reltol = 1e-9`, saved at the dataset's 512 time points |

### Why the sampling protocol is adopted

The dataset grid is 2.56x denser in time than EvoODE's grid. Measured consequence: on System 54
the look-ahead stage cap goes from `[nothing, 2, 2]` to `[nothing, 3, 3]` against a true
`[3, 3, 3]`, i.e. **the two known safety violations disappear.** Across the 13 equations of the
six ground-truth systems on initial-condition set 1, violations go 2 → 0 and correct caps 6 → 8.

This is the prediction WP-L3 made from the resolution limit, now confirmed.

### Why the shipped trajectories are not adopted

They carry the accuracy of the solver that produced them. Verified against an independently
converged RK4 reference (self-convergence ~1e-13):

| System | max absolute error of shipped data | implied MSE floor | current EvoODE result |
|---|---|---|---|
| 3 | 2.3e-01 | **2.5e-02** | 1.3e-08 |
| 11 | 1.0e-05 | 1.9e-11 | **4.4e-15** |
| 26 | 2.0e-05 | 3.5e-11 | 1.4e-03 |
| 31 | 1.1e-04 | 6.1e-10 | **6.8e-11** |
| 54 | 1.2e-03 | 2.0e-07 | — |

On Systems 3, 11 and 31 our current results are below the floor the shipped data imposes, i.e.
unreachable on that data — on System 3 by six orders. The `nfev` fields corroborate the cause:
System 3 was integrated with 77 function evaluations over t ∈ [0, 10], consistent with scipy
`solve_ivp` default tolerances.

### Why this costs nothing that WP-G1 measured

The caps were measured on both data sources on the identical grid and are **identical in all 26
cells**; the noise floors differ only in the third to fourth significant digit. The reason is that
the shipped data's integration error is smooth in t, and a derivative-based noise floor barely
sees smooth error. The System 54 gain therefore belongs to grid density, not to data quality, and
is retained by our own integration.

### Consequences that must be carried through

1. `tspan` and `T` enter `config_fingerprint`, so the regression history's 42 records are not
   comparable across the change. A Baseline v1 must be established on the new grid before the
   final variant is regression-checked.
2. Every per-equation cap must be re-derived; the values in this project's older documents refer
   to the per-system grid.
3. Run count doubles to 63 × 2 conditions × 3 seeds × 2 IC sets = 756.
4. **A deviation in our favour that must be declared** (see §2, open question 1): if published
   numbers were computed on the shipped trajectories, we work on cleaner data than the comparison
   works. This is not resolvable until the publications are checked.
5. The cap is **not stable across initial conditions**. System 31 initial-condition set 2 yields a
   cap of 1 against a true stage of 3, because the epidemic is over by t ≈ 0.47 and only 5.3% of
   the 512 points carry dynamics (30.3% on set 1). This is bounded rather than systematic: of 26
   cells, 5 are low-signal and only 1 of those fails; of 12 failing cells only 1 is low-signal.
   Phase B will contain cells in which no method can recover the structure, and those must be
   reported as a property of the protocol, not as method failure.

---

## 4. Audit status

| Item | Status |
|---|---|
| EvoODE initial conditions vs dataset | verified — set 0, exact match, ten systems |
| EvoODE grid vs dataset | verified — mismatch on all ten |
| Accuracy of the shipped trajectories | verified — MSE floors 2.5e-2 to 2e-7, WP-G1b |
| Phase B sampling protocol | **decided 2026-08-03** — §3 |
| System classification of all 63 | done, WP-P3.1 |
| Published source protocols | not started — requires the publications |
| Comparability verdict | **not established** |
