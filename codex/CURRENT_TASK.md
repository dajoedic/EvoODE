# CURRENT TASK

**Language: Julia**

## WP-B1 — Move the regression suite to the Phase B sampling protocol

The Phase B sampling protocol was decided on 2026-08-03 and is recorded in
`docs/paper1_odebench_protocol_alignment.md` §3. It exists only as a decision; no code implements
it. Until it does, Phase B cannot be started the moment compute becomes available.

The regression suite is the place to land it first, because that suite exists to catch regressions
in the variant we ship, and we ship on the new protocol.

### The protocol

| Component | Value |
|---|---|
| Time span | t ∈ [0, 10] for every system |
| Sampling | 512 uniform points, spacing `10/511`, both endpoints included |
| Initial conditions | **both** sets shipped by the dataset, per system |
| Trajectory source | our own integration, `Tsit5`, `abstol = reltol = 1e-9`, saved at exactly those 512 time points |

The initial conditions come from `benchmarks/data/strogatz_extended.json`, field `init`, which holds
two sets per system. `solutions[1][k]["t"]` gives the time grid; the shipped `y` matrices are **not**
used — only the sampling.

### Scope

`studies/regression/diagnostic_systems.jl` currently hardcodes a per-system `u0`, `tspan` and `T`,
and a single initial condition. Replace that with the protocol above, keeping the ground-truth RHS
functions unchanged.

A cell is now identified by (variant, system, **initial-condition set**, seed). Everything that
currently keys on (variant, system, seed) must be extended: the runner's selection and resume
logic, the record schema, and the history uniqueness key. The existing environment-variable
selection gains a counterpart for the initial-condition set.

`config_fingerprint` must change — the payload already contains `tspan` and `T`, and the
initial-condition set now belongs in it too. **This is intended, not a problem to work around.**
The 42 existing records stay in `history.jsonl` under their old fingerprints; that is exactly what
the fingerprint mechanism is for. Do not delete or rewrite them, and do not attempt to make old and
new records comparable.

### Two things that need judgment, not just translation

**1. `expected_stage` is a property of the system, the caps are a property of the trajectory.**
WP-G1 measured that System 31 initial-condition set 2 does not identify its own true stage: the
epidemic is over by t ≈ 0.47 and only about 5% of the 512 samples carry dynamics, so a cap of 1 is
returned against a true stage of 3. `expected_stage` must therefore stay the structural truth of
the system and must not be adjusted per initial condition. But `stage_overshoot` computed against
it will now be misleading for such cells.

Record enough to tell the two apart: keep `expected_stage` as the structural truth, and add a
per-cell measure of how much dynamics the trajectory actually carries, using the same definition as
`studies/lookahead/measure_dataset_grid_caps.jl` (fraction of the 512 points at which the true
derivative magnitude exceeds one percent of its maximum, computed per equation from the
ground-truth right-hand side). A cell that fails with a low value there is a protocol limit, not a
method failure, and the record must make that readable without a separate investigation.

**2. System 63 runs for hours and now doubles.** It is already the runtime driver of the suite and
the new grid makes every trajectory longer. Do not remove it — the system list is part of the
fingerprint and removing it forms a separate track. But the suite must remain selectable per
system, per initial-condition set and per seed from the outside, so that expensive cells can be
scheduled separately.

### Verification

Do **not** run the regression matrix. Verify with the cheapest possible evidence:

- the new `config_fingerprint`, reported as a value, and a statement that it differs from
  `df5db7763bcd2449`
- for all five systems and both initial-condition sets: the constructed trajectory has 512 points,
  starts at 0.0, ends at 10.0, and its first state matches the dataset's `init` entry exactly
- one single cheap cell end to end — System 3, initial-condition set 1, seed 42, variant
  `evogrow_v2_2_stage_capped` — writing to a scratch history path, **not** to
  `studies/regression/history.jsonl`. Report its loss, cap, `eq_overshoot`, `pruned_match` and
  support. This cell previously gave cap `[2]`, loss `1.3476451847014113e-8`, support
  `[["u1", "u1^2"]]` on the old grid; the new value will differ and that is expected — report it,
  do not tune anything to reach the old number.
- that selecting by initial-condition set works, by showing that the two sets produce different
  trajectories for the same system

### Constraints

- Do not modify `estimate_stage_caps` or the cap policy.
- Do not write to `studies/regression/history.jsonl`.
- Do not run the regression matrix, Baseline v1, or any multi-cell sweep. Those are the user's to
  start, and on the new grid they belong on a server.
- Ground-truth RHS functions stay as they are; only the sampling and initial conditions change.
- Generated output goes to its own subfolder under `outputs/`.
- If any part of this is not implementable as stated, stop and report the conflict rather than
  delivering a subset silently.

### Deliverable

The changed suite, and a short report at `codex/REPORT_WP_B1.md` containing the new fingerprint,
the trajectory checks, the single-cell result, and an explicit list of every place where the
initial-condition set had to be threaded through.
