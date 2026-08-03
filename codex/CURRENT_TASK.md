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

### What the dataset grid is

Verified directly against `benchmarks/data/strogatz_extended.json`:

- all 63 systems carry stored solutions under `solutions[1][k]`, with `k = 1, 2` for the two
  initial-condition sets
- every one of the 126 stored solutions shares a bit-identical `t` vector: 512 uniform points,
  `t[1] = 0.0`, `t[512] = 10.0`, spacing `10/511`
- `y` is stored as `dim` rows of 512 values
- all 126 carry `success = true`; no non-finite entries

Trajectories are to be **read from the file**, not re-integrated. `load_systems_json` in
`benchmarks/run_odebench.jl` already parses this structure for the first initial-condition set;
reuse or extend it rather than writing a second parser.

### Scope

Measure `estimate_stage_caps` under the frozen `LOOKAHEAD_CAP_POLICY` used by
`studies/regression/run_regression.jl`, for:

- the six systems with known ground-truth stages: 3, 11, 26, 31, 54, 63
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

The script, a CSV of the per-equation results under `outputs/`, and a short report at
`docs/wp_g1_dataset_grid_caps.md` containing the comparison table, the classification counts, and
an explicit statement on each of the two predictions above. Every factual sentence in that report
must be derived from the measured values; do not carry over expectations from this task
description as if they were results.
