# CURRENT TASK

**Language: Julia**

## WP-L5d — Close out the stage cap: provenance, tests, sensitivity, report

### 0. Status

The cap rule is functionally done and independently verified:

| System | per-equation truth | cap | |
|---|---|---|---|
| 3 | [2] | [2] | correct |
| 11 | [4] | [4] | correct |
| 26 | [3, 3] | [3, 3] | correct |
| 31 | [3, 3] | [3, 3] | correct |
| 63 | [3, 3, 1, 1] | all `nothing` | safe |
| 54 | [1, 3, 3] | [`nothing`, 2, 2] | 2 violations |

Suite-wide: 2 violations, 8 of 16 equations capped, 18 stages saved.

**No change to the cap rule is in scope here.** If a test uncovers a genuine rule defect,
report it with the numbers and stop rather than fixing it silently — the rule is currently
verified and a quiet change would invalidate that.

Keep the working practice from WP-L5c: produce the acceptance table first and again at the
end, and back any reported stop with the actual output that justifies it.

### 1. Fingerprint — the most important item

The cap policy in `run_regression.jl` is a hardcoded tuple containing `estimator`,
`weighting`, `tau_rel`, `tau_abs`, `cond_cap` and `excitation_floor`. It does **not**
contain `aggregation` or `lookahead_horizon`. Three semantic changes to the cap have now
passed without moving `3f9be6d36c4043de`, so records produced under materially different
rules would be pooled as one configuration.

Add both fields, plus any other policy parameter that affects behaviour, and report the new
fingerprint value.

**Trap to avoid, and it is a real one.** A decisive run of `evogrow_v3_stage_capped` on
System 26 seed 42 is in flight. It computed its fingerprint at process start and will write
its record with the old value `3f9be6d36c4043de`. That is correct and must stay that way.
But `studies/gate2_do_or_die/readout.jl` runs afterwards from updated code: if it locates
the record by recomputing the current fingerprint, it will silently fail to find a result
that exists.

Check how the readout selects records. It must be able to find the in-flight record after
the fingerprint changes — by explicit selection or an explicit fingerprint argument, not by
implicitly recomputing today's value. If it currently recomputes, fix that and say so.
Verify it against the existing history records rather than by reading the code alone.

### 2. Tests

- Floor semantics in both directions: a residual that **fell** to the floor after an
  observed gain yields a cap at that stage; one that was **already** at the floor before any
  gain yields no cap.
- The horizon crosses a useless intermediate stage; an empty stage does not consume horizon.
- No cap when the successor stage is not evaluable.
- The WP-L5c relaxation: when the successor residual already sits at the floor, the absolute
  threshold `tau_abs` no longer gates the gain while `delta > floor` and the relative
  threshold still do.
- The WP-L4 invariants: the cap never forces a promotion, uncapped equations are unaffected,
  a cap below the current stage is handled conservatively without removing terms, and
  `EvoGrowV3` is bit-identical with the cap disabled.

### 3. Sensitivity

Report the six systems above under each aggregation mode and under at least two values of
`lookahead_horizon` besides the default. Give safety violations, capped equations and stages
saved for each combination, so the defaults are visibly a choice and not an assumption.

### 4. Report under `docs/`

State plainly, with numbers:

- the acceptance table and the suite-wide safety and utility counts;
- the new fingerprint, and that pre-repair and post-repair records must not be pooled;
- the sensitivity table;
- **the two System 54 violations as a known resolution limit, not an open bug.** These are
  the same equations WP-L3 identified as undershoots: at benchmark sampling the residual on
  System 54 drops below the noise floor already at stage 2, so the stage-3 cliff lies under
  the resolution of the derivative estimate, and the WP-L3 density sweep shows it becoming
  visible from twice the sampling density. This is a data limit, not a rule limit, and it
  gives the rule a closed characterisation: safe wherever the derivative estimate resolves
  the structure, unsafe exactly where it does not — and that is readable in advance from the
  noise floor;
- **the open caveat on the System 31 fix:** its diagnosis timed out, so the repair was made
  by inference rather than from instrumented numbers. The result is verified and the change
  acts in the safe direction, but the cause is unconfirmed and this is the first place to
  look if the rule surprises later.

### 5. Scope and execution

**Do not run the decisive cell — it is running externally.** Nothing may be written to
`studies/regression/history.jsonl`. Verification is limited to cap computation, unit tests,
the suite-wide check, readout record selection against existing history, and a cheap smoke
run on a small system. If anything exceeds a few minutes, stop and report with the output
that justifies the stop.
