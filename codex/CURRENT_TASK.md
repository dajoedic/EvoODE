# CURRENT TASK

**Language: Julia**

## WP-G1b — Add the missing data-source arm and the horizon diagnostic

WP-G1 is delivered and committed (`8c5319b`). Its arm-A results stand and must not be recomputed
differently: System 54 caps become `[nothing, 3, 3]` against a truth of `[3,3,3]`, System 63 stays
`nothing` on all equations and both initial-condition sets, System 31 initial-condition set 2
produces a cap of 1 on equation 1 against a truth of 3.

Two things are missing. Both are cheap, and neither involves any search.

### Gap 1 — Arm B was not implemented

The task specified measuring the caps on two data sources on the identical grid:

- **A — stored**: the `y` matrices as shipped in `benchmarks/data/strogatz_extended.json`
- **B — self-integrated**: the ground-truth ODE integrated with `Tsit5`, `abstol = reltol = 1e-9`,
  from the same initial condition, saved at exactly the dataset's 512 time points

Only A was produced. `studies/lookahead/measure_dataset_grid_caps.jl` contains no integration at
all, and the output CSV has one row per (system, IC set, equation) with no data-source column.

This matters because the two candidate explanations for every change WP-G1 measured are still
confounded. The dataset grid is 2.56x denser in time than EvoODE's grid, which should help; the
shipped trajectories carry solver error up to 2.3e-1 absolute on System 3 and 1e-5 to 1e-3
elsewhere, which should hurt, because the cap policy compares a residual against a derivative
noise floor and dirtier data raises that floor. Without arm B we cannot say which effect produced
the System 54 improvement or the System 31 violation.

Add arm B and report both arms side by side. Extend the existing script and CSV with a data-source
column rather than writing a second script; arm A must reproduce the committed numbers exactly,
and any deviation is a regression to report, not to explain away.

The report must state explicitly, per equation, whether A and B give the same cap, and where they
differ it must show the noise floors of both, since that is the mechanism through which a
difference would arise.

### Gap 2 — Quantify how much of each trajectory carries dynamics

The System 31 violation was diagnosed after the fact, outside the script. With
`u0 = [20.0, 12.4]` the epidemic is over by `t ≈ 0.47`, so roughly 5 percent of the 512 samples
carry any dynamics and the rest sit in a dead tail; on initial-condition set 1 the same figure is
about 30 percent. The residuals are flat at ~1e-15 across all five stages, so the rule correctly
reports that nothing beyond stage 1 helps — it is right about the data and wrong about the truth,
because the trajectory does not contain the truth.

This is a property of the fixed `t ∈ [0, 10]` window applied to every system and every initial
condition, and it is a direct input to the Phase B grid decision. Measure it rather than leaving
it as an anecdote.

For every (system, IC set) in the six-system set, add to the CSV:

- the fraction of the 512 sample points at which the true derivative magnitude exceeds one percent
  of its maximum over the trajectory, computed per equation from the ground-truth right-hand side
  rather than from a finite difference
- the time at which the state first falls below one percent of the spread it covers

Report these alongside the classification, so that a violation or a `nothing` can be read against
how much signal the trajectory actually offered. State in the report whether the low-signal cells
and the failing cells coincide.

Do not draw a conclusion about which grid Phase B should use. That decision is not yours; supply
the measurement it needs.

### Constraints

- Do not modify `estimate_stage_caps`, the cap policy, `FINGERPRINT_VARIANT_LABELS`, the
  fingerprint payload, `run_regression.jl`, or any variant definition.
- Do not write to `studies/regression/history.jsonl`.
- Perform no discovery run and no search of any kind.
- Output goes to the existing `outputs/studies/lookahead/wp_g1/` folder; update
  `docs/wp_g1_dataset_grid_caps.md` in place rather than adding a second report.
- The run must stay cheap. Integrating 12 trajectories at 1e-9 takes seconds; if anything runs
  longer than a few minutes, stop and report rather than waiting.
- If any part of this is not implementable as stated, stop and report the conflict instead of
  silently delivering a subset. The omission of arm B in WP-G1 went unmentioned in the report,
  which is what made it expensive to notice.
