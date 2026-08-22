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

The dataset ships every system on a uniform grid of **512 points over t ∈ [0, 10]**. EvoODE
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
| Sampling grid | to verify — dataset ships 512 points | to verify | to verify |
| Noise setting | to verify | to verify | to verify |
| Metric definition | to verify — R² threshold expected | to verify | to verify |
| Aggregation | to verify | to verify | to verify |
| Success criterion | to verify | to verify | to verify |
| **Representable in principle** | to verify | to verify | to verify |
| **Representable under the evaluated protocol** | to verify | to verify | to verify |

The last two rows were added on 2026-08-22 and are per system rather than per source as a single
verdict: *in principle* asks whether the method's model class could express the true structure at
all, *under the evaluated protocol* whether it was reachable given the operators, library,
complexity limits and constraints of the published run. A saturating term is out of reach for a
sparse-regression run restricted to polynomials of degree 3 however rich the method could be in
principle. **The same two columns apply to EvoODE itself:** our basis represents 20 of the 63
systems exactly, and the search-free reference in `docs/WP-R1.md` quantifies how well it
approximates the rest. Rationale in `docs/diskussion_vergleichsmethoden.md`.

Open questions that decide comparability:

1. Do published results use both initial-condition sets or one?
2. Is the reported metric an R² threshold, and at what value, and computed on the trajectory
   or on the derivatives?
3. Is any noise added, and are results reported per noise level?
4. Are failed or diverged runs excluded from the aggregate, or scored as failures?

Until these are answered, published numbers are **contextual only**.

---

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
