# Paper 1 — ODEBench Protocol Alignment Audit

Status: **in progress.** The EvoODE side is verified against the repository and the dataset.
The published-source columns are **not yet verified** and are marked as such; nothing in this
document may be cited as a comparison until they are.

Purpose, per `PAPER_1.md` Phase 3: determine whether published ODEBench-related numbers may
be described as directly comparable, approximately comparable, or contextual only. If
protocol equivalence is not established, external numbers must not be framed as a benchmark
victory or defeat.

Last updated: 2026-08-02.

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

Adopting the dataset grid would therefore plausibly remove one of the two remaining stage-cap
safety violations. This is a prediction from measured behaviour, not a result — it has not
been run.

### 1.4 EvoODE protocol as currently implemented

| Dimension | EvoODE |
|---|---|
| Systems | 10 of 63 so far; all 63 planned for Phase B |
| Initial conditions | dataset set 0 only, one per system |
| Time span | per system, see table above |
| Sampling grid | uniform, per-system T, see table above |
| Trajectory generation | `Tsit5`, `abstol = reltol = 1e-9` |
| Noise | none |
| Evaluation metric | simulation MSE; R² not yet implemented |
| Structure metric | `exact_support_match_raw` and `_pruned`, exact systems only |
| Aggregation | mean and standard deviation over seeds, per system |
| Seeds | 3 in the regression suite (42, 123, 7); 5 in the frozen Phase A |

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

Open questions that decide comparability:

1. Do published results use both initial-condition sets or one?
2. Is the reported metric an R² threshold, and at what value, and computed on the trajectory
   or on the derivatives?
3. Is any noise added, and are results reported per noise level?
4. Are failed or diverged runs excluded from the aggregate, or scored as failures?

Until these are answered, published numbers are **contextual only**.

---

## 3. Consequences for Phase B

Two options, and the choice must be deliberate:

**Adopt the dataset grid.** Run Phase B on 512 points over t ∈ [0, 10] with both initial
condition sets. This makes protocol alignment plausible, doubles the run count, and changes
every trajectory — so no existing result carries over and the regression baseline would have
to be re-established. It would also likely improve derivative-based components through the
denser grid.

**Keep the current per-system grid.** Existing results remain valid and comparable within the
project, but published numbers stay contextual only and the paper must say so explicitly and
consistently.

Recommendation: decide this **before** Phase B is generated, because it determines the
trajectories and therefore everything downstream. It does not need to be decided before the
system classification (WP-P3.1), which is grid-independent.

---

## 4. Audit status

| Item | Status |
|---|---|
| EvoODE initial conditions vs dataset | verified — set 0, exact match, ten systems |
| EvoODE grid vs dataset | verified — mismatch on all ten |
| System classification of all 63 | in progress, WP-P3.1 |
| Published source protocols | not started — requires the publications |
| Comparability verdict | **not established** |
