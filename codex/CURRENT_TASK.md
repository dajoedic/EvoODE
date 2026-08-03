# CURRENT TASK

**Language: Julia**

## WP-G1 — Re-measure the look-ahead stage caps on the ODEBench dataset grid

### Why

The look-ahead stage cap is the contribution of Paper 1. It is search-independent: it reads only
the trajectory and the basis. Every cap verified so far was measured on EvoODE's per-system grid
(100–300 points, per-system time span). Phase B will adopt the dataset grid, which changes every
trajectory and therefore every cap.

Before that switch is made, we want to see what the caps become. This is a **measurement, not a
migration** — nothing in the search, the regression runner, the fingerprint or the variant
definitions may change.

Two predictions are on record and this run tests them:

1. WP-L3 measured that System 54's stage-3 cliff is unresolvable at EvoODE's sampling density and
   becomes resolvable at roughly twice that density. The dataset grid is 2.56x denser in time.
   Prediction: the two safety violations on System 54 equations 2 and 3 disappear.
2. System 63 currently yields `nothing` on all four equations and is documented as an
   identifiability limit. EvoODE runs it to t = 30, so most sample points sit in the settled tail.
   On the dataset grid the system is still mid-transient at t = 10. Prediction: at least some of
   its equations become identifiable.

Both are predictions from measured behaviour. Report what comes out, including if it contradicts
them.

A third question was added after the task was first written, and it is now the decisive one — see
"Data source" below.

### What the dataset grid is

Verified directly against `benchmarks/data/strogatz_extended.json`:

- all 63 systems carry stored solutions under `solutions[1][k]`, with `k = 1, 2` for the two
  initial-condition sets
- every one of the 126 stored solutions shares a bit-identical `t` vector: 512 uniform points,
  `t[1] = 0.0`, `t[512] = 10.0`, spacing `10/511`
- `y` is stored as `dim` rows of 512 values
- all 126 carry `success = true`; no non-finite entries

`load_systems_json` in `benchmarks/run_odebench.jl` already parses this structure for the first
initial-condition set; reuse or extend it rather than writing a second parser.

### Data source — measure both, this decides the grid question

The stored trajectories carry the accuracy of the solver that produced them, and that accuracy is
low. Verified against an independently converged RK4 reference with exact time alignment
(reference self-convergence ~1e-13, so the reference is trustworthy):

| system | IC | max absolute error of the stored data | relative |
|---|---|---|---|
| 11 | 0 | 1.0e-05 | 3.0e-06 |
| 26 | 0 | 2.0e-05 | 4.0e-06 |
| 31 | 0 | 1.1e-04 | 1.6e-05 |
| 54 | 1 | 2.9e-03 | 8.3e-05 |
| 3 | 0 | 2.3e-01 | 3.1e-03 |

The `nfev` fields corroborate this: System 3 was integrated with 77 function evaluations over
t ∈ [0, 10]. EvoODE generates its own data at `abstol = reltol = 1e-9`.

This matters directly for the cap: the policy compares a per-stage residual against a derivative
noise floor. Dirtier data raises that floor, which pushes equations into "cannot judge" and
produces *more* `nothing` caps — the opposite of prediction 2. The denser grid helps and the
lower data quality hurts, and which effect dominates is unknown.

Therefore measure the caps on **both** data sources, on the identical grid:

- **A — stored**: the `y` matrices as shipped
- **B — self-integrated**: the ground-truth ODE integrated with `Tsit5`, `abstol = reltol = 1e-9`,
  from the same initial condition, saved at exactly the dataset's 512 time points

A and B differ only in data accuracy, so any difference in the caps is attributable to that alone.
This is the comparison that decides whether Phase B uses the shipped trajectories or only the
shipped sampling protocol. Report the per-equation noise floor for both, since that is the
mechanism by which a difference would arise.

### Scope

Measure `estimate_stage_caps` under the frozen `LOOKAHEAD_CAP_POLICY` used by
`studies/regression/run_regression.jl`, for:

- the six systems with known ground-truth stages: 3, 11, 26, 31, 54, 63
- both data sources A and B as defined above
- both initial-condition sets, reported separately — the second set has never been used in this
  project and whether the cap is stable across initial conditions is itself a finding
- the same staged polynomial basis the regression suite uses, at the system's dimension

For every (system, IC set, equation) report: the cap, the per-equation true stage, and the
resulting classification — correct, conservative (cap above truth), **violation** (cap below
truth), or `nothing` (not identifiable). A violation is the only outcome that makes the truth
unreachable and must be called out separately in the summary.

Include, per equation, whatever intermediate quantity the policy uses to make its decision
(residual per stage and the noise floor it is compared against). Without those numbers a changed
cap cannot be explained, only observed.

### Comparison against the current state

Report side by side with the caps measured on the per-system grid, which are:

| system | cap on per-system grid |
|---|---|
| 3 | `[2]` |
| 11 | `[4]` |
| 26 | `[3,3]` |
| 31 | `[3,3]` |
| 54 | `[nothing, 2, 2]` |
| 63 | `[nothing, nothing, nothing, nothing]` |

Per-equation ground truth for the two interesting cases: System 54 is `[3,3,3]`, System 63 is
`[3,3,1,1]`. The known violations are System 54 equations 2 and 3.

### Constraints

- Do not modify `estimate_stage_caps`, the cap policy, `FINGERPRINT_VARIANT_LABELS`, the
  fingerprint payload, `run_regression.jl`, or any variant definition.
- Do not write to `studies/regression/history.jsonl`.
- Do not run the regression matrix or any discovery run. This work package performs **no search**
  — it evaluates the cap estimator on given trajectories and nothing else.
- New code goes into a new script under `studies/lookahead/`; generated output into its own
  subfolder under `outputs/`.
- The run must be cheap. If any part of it takes more than a few minutes, that is a signal that
  something other than cap estimation is being executed — stop and report instead of waiting.

### Deliverable

The script, a CSV of the per-equation results under `outputs/` with one row per
(system, IC set, data source, equation), and a short report at `docs/wp_g1_dataset_grid_caps.md`
containing:

- the comparison table against the per-system-grid caps
- the classification counts, separately for data source A and B
- an explicit statement on each of the two predictions above
- a statement on whether A and B produce different caps, and where

Every factual sentence in that report must be derived from the measured values; do not carry over
expectations from this task description as if they were results.
