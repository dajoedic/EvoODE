# CURRENT TASK

**Language: Julia**

## WP-E1 — Phase B on the regression batch path: enumeration and one verified cell

Decision taken: Phase B runs on the batch machinery under `studies/regression/`, not on
`experiments/`. That path already carries the Phase B protocol — seeds `[42, 123, 7]`,
`tspan = (0, 10)`, `T = 512`, both initial-condition sets, trajectories integrated by us from
`benchmarks/data/strogatz_extended.json` — plus one cell per process, resume, merge that refuses
failed records, and a config fingerprint. `experiments/generate_manifest.jl` is still entirely a
Phase A generator and does not know initial-condition sets at all.

This work package makes the campaign **enumerable and runnable**, and verifies exactly one cell.
Metrics, merge and registry for 756 runs are WP-E2. Do not start them here.

### The constraint that governs everything else

**`REGRESSION_SYSTEMS` must not change, and neither must the regression fingerprint.**

The regression suite is a diagnostic instrument: five systems, fast, with 42 historical records and
a fingerprint that has to stay comparable. Growing it into the campaign would destroy both. Phase B
gets its **own configuration and its own fingerprint**, while **reusing** the existing machinery —
trajectory construction, batch entry point, resume, record writing.

Reuse means reuse. Do not copy `run_regression.jl` into a near-duplicate that will drift. Where the
two need the same code, factor it so both call it; where they differ, they differ in configuration,
not in a second implementation. If a clean split is not possible somewhere without restructuring the
regression path, say so and report it rather than forcing it.

`config_fingerprint()` of the regression path must still be `7acd3ebf3f60b974` when you are done.
That is a hard acceptance criterion — measure and report it.

### 1. The campaign system set

Phase B covers **all 63 systems** of `benchmarks/data/strogatz_extended.json`, built from the
dataset rather than hand-listed: identifier, name, dimension, both initial-condition sets, and the
time grid all come from the file, through the same protocol loader the diagnostic set already uses.

`REGRESSION_SYSTEMS` entries carry a hand-maintained `expected_stage`. That does not scale to 63
systems and must not be guessed. Establish whether the dataset carries the information needed to
derive it. If it does not, represent it explicitly as absent rather than inventing a value, and
report which downstream consumers read that field so WP-E2 can handle it.

Also report, without acting on it, how many of the 63 systems are exactly representable in the
current basis and how many are surrogate. Design principle 8 forbids mixing them into one
structure-correctness metric, which WP-E2 will have to respect.

### 2. The two conditions

Phase B has exactly two arms: `evogrow_v2_2_stage_capped` with `use_pretuning = true` and with
`use_pretuning = false`. No v1, no v2.1, no v3, no GP baseline.

Both arms are otherwise identical, including the look-ahead stage cap policy. Give them variant
labels that make the condition readable in a record without parsing a configuration.

### 3. Enumeration

The campaign is 63 systems x 2 conditions x 3 seeds x 2 IC sets = **756 cells**.

Provide a way to enumerate the cells and to select exactly one of them by identity — the same
selection mechanism the batch path already uses, so a scheduler can run one cell per process. The
enumeration must be deterministic and stable in order: a cell's identity must not depend on how many
cells are being run.

Verify that the count is exactly 756 and that every cell identity is unique. Report both numbers as
measured, not as asserted.

### 4. Separate output and fingerprint

Campaign records must not be written into the regression history. Give Phase B its own history
target and its own fingerprint payload covering its own system set, conditions, seeds and IC sets.

Report the Phase B fingerprint value. It becomes the campaign identity; from that point every
fingerprint-affecting change is frozen.

### 5. One verified cell

Run exactly one cheap cell end to end — a 1D system — and show the produced record.

It must contain the four optimizer telemetry counters from WP-D3, the existing fit and solve
counters, the condition label, the IC set, and the Phase B fingerprint. Confirm that the record
schema matches the regression one wherever the fields have the same meaning; where Phase B needs a
field the regression does not have, name it and say why.

**One cell only.** Do not run the campaign, a system sweep, or anything long. If a cell turns out to
be expensive, pick a cheaper system and say which.

### 6. Out of scope

Merge, registry, aggregation and metrics for 756 runs — WP-E2. Slurm submission scripts. Anything
under `experiments/`, which stays as it is; the Phase A generator is not to be repaired or extended.
The frozen `paper1_phaseA_v1` artefacts. `src/` — this work package should need no change there, and
if you believe it does, report why before doing it.

### 7. Verification

Give me the exact commands with expected runtime and pass criterion. I run them.

Smoke only. No long runs.

### Report

Write `codex/REPORT_WP_E1.md`: what you factored versus what stayed put, the measured cell count and
uniqueness check, the Phase B fingerprint, the regression fingerprint as re-measured, the
`expected_stage` finding, the exact/surrogate split across the 63 systems, and the single verified
record.
