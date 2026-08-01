# CURRENT TASK

**Language: Julia**

## WP-L5c — Finish the cap repair: System 31 equation 1, then the outstanding deliverables

### 0. Status, so you start from the right picture

WP-L5b worked. It reported a stop with "System 26 is no longer [3,3]", but that alarm was
false: the message was carried over verbatim from the previous round — it referenced WP-L5
and a section 8 that WP-L5b does not have, and described the earlier switch to
positive-evidence-only rather than the change actually made. An independent recomputation
of `estimate_stage_caps` after your change gives:

| System | per-equation truth | cap after WP-L5b | |
|---|---|---|---|
| 3 | [2] | [2] | correct |
| 11 | [4] | [4] | correct |
| 26 | [3, 3] | [3, 3] | correct |
| 31 | [3, 3] | **[1, 3]** | equation 1 violates |
| 63 | [3, 3, 1, 1] | [`nothing`×4] | safe |

Safety violations went 2 → 4 → **1**. System 26 is intact, so the in-flight decisive run
keeps its comparison basis and must not be disturbed.

**Before reporting any stop in this work package, re-run the check that justifies it and
paste its actual output.** A stop is a strong claim; it cost a full round here.

### 1. Part 1 — System 31 equation 1

`du1 = -0.4*u1*u2`. This is the only equation in the set whose true support lies entirely
in a later stage, with no stage-1 and no stage-2 term at all. It is exactly the case the
look-ahead horizon exists for: no gain on the intermediate stage, the whole gain arriving
later. The cap nevertheless lands at 1.

Two candidate causes, and the work is to tell them apart rather than guess:

- the gain test does not fire when comparing stage 1 against stage 3 — for instance because
  `delta > floors[stage]` or the relative threshold fails at that particular floor;
- the per-split decisions disagree and the aggregation finds a majority for cap 1 while
  cap 3 has none.

Instrument the per-split decisions for this equation: for each split, report the stage
residuals, the floor, which stages were usable, the gain test outcome for every pair the
horizon considers, the resulting per-split verdict, and the aggregation step that produced
the final answer. Print it. The diagnosis must be visible in numbers before any fix.

Then fix the identified cause. Note that equation 2 of the same system, whose truth adds a
stage-1 term, already comes out correct at 3 — whatever changes, it must stay correct, as
must Systems 3, 11, 26 and 63.

If the cause turns out to be the horizon being structurally unable to see a gain that only
appears two applicable stages ahead **and** widening it breaks another system, report that
with the numbers instead of tuning. That would be a real statement about the limits of the
criterion and belongs in the paper rather than in a threshold.

### 2. Part 2 — The acceptance table, first and always

Same rule as WP-L5b: produce and print the acceptance table over the five regression
systems before anything else, and again at the end. Required outcome is now:

| System | required |
|---|---|
| 3 | [2] |
| 11 | [4] |
| 26 | [3, 3] |
| 31 | [3, 3] |
| 63 | `nothing` for equations 1 and 2; equations 3 and 4 `nothing` or 1 |

with 0 safety violations. Ground truth judges the caps and must never enter their
computation; `estimate_stage_caps` keeps its signature with no channel for it.

### 3. Part 3 — The deliverables WP-L5b did not produce

- **Suite-wide safety and utility**, in one table: how many equations have a cap below
  their true stage (target 0), how many receive a cap at all, and how many stages are saved
  in total. A rule that is safe because it never caps is worthless and that has to be
  visible next to the safety number. Note explicitly that System 63 is now entirely
  uncapped and therefore contributes nothing to the utility side.
- **Aggregation sensitivity**: the five systems under the stricter and looser aggregation
  modes, so the default is a choice rather than an assumption. Add the same for at least
  one alternative `lookahead_horizon`.
- **Fingerprint**: the cap policy in `run_regression.jl` is a hardcoded tuple missing both
  `aggregation` and `lookahead_horizon`. Two semantic changes have now passed without
  moving `3f9be6d36c4043de`. Add the missing fields, report the new fingerprint, and state
  that pre-repair and post-repair records must not be pooled.
- **Tests**: floor semantics in both directions (fell to the floor after a gain versus
  already at it), the horizon crossing a useless intermediate stage, an empty stage not
  consuming horizon, no cap when the successor stage is not evaluable, plus the WP-L4
  invariants — cap never forces a promotion, uncapped equations unaffected, cap below the
  current stage handled conservatively, `EvoGrowV3` bit-identical with the cap disabled.
- **Report** under `docs/`: acceptance table, the System 31 diagnosis with its numbers,
  safety and utility counts, sensitivity, new fingerprint.

### 4. Scope and execution

**Do not run the decisive cell — it is running externally.** Nothing may be written to
`studies/regression/history.jsonl`. Verification is limited to cap computation, unit tests,
the suite-wide check and a cheap smoke run on a small system. All of that is seconds to
minutes; if anything exceeds a few minutes, stop and report — with the output that
justifies the stop.
