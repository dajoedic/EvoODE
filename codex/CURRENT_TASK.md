# CURRENT TASK

**Language: Julia**

## WP-G1 — Heartbeat file per batch cell

A running cell is currently opaque from outside the process. The `level_callback` in
`studies/regression/run_regression.jl` feeds a `ProgressMeter` display in the terminal — level, stage,
best loss — and nothing of it reaches disk. The only write is the finished record at the end of the
cell.

On the campaign this matters. 756 jobs, and cells that can run for hours: the question "is this job
still computing or has it been stuck for six hours" decides whether it gets killed and requeued or
left alone. Without a heartbeat that is only visible once the job finishes or hits the wall-time
limit.

This is **logging only**. It must not influence a single computed number, and it must not change
either fingerprint — regression `45cb2c4507007366`, Phase B `c0a236edf030e03a`. Measure and report
both at the end.

### 1. What to write

One heartbeat file per cell, written as the search progresses, next to the cell's output rather than
into it. Never into the record itself — the record schema is frozen.

Per level, one appended line carrying at least: a timestamp, the level, the stage, and the best loss
so far. Line-oriented and machine-readable, consistent with how the project already writes JSONL.

**Flush on every write.** A heartbeat that sits in a buffer is worthless for exactly the case it
exists for — a job that dies or hangs.

Write a start marker before the search begins and a completion marker when the cell finishes. The
decisive diagnostic on a cluster is "started, has not finished, last sign of life at time X", and
that requires both ends to be explicit.

Include what identifies the process on a cluster node: cell identity, plus process id and hostname.
Keep it small.

### 2. Where it has to work

Both entry points: the suite runner `run_regression.jl` and the batch entry point
`run_batch_cell.jl`, since the campaign runs through the latter. Phase B cells go through the same
machinery and must produce heartbeats too.

One file per cell, never a shared file — 756 processes appending to one file on a cluster filesystem
is a corruption source, not a diagnostic.

### 3. It must never break a run

A cell that computes correctly must not fail because a heartbeat could not be written — a full disk,
a read-only path, a lost network mount. Failures to write are to be swallowed silently, at most
logged once. The heartbeat is a diagnostic, and a diagnostic that kills the thing it observes is
worse than none.

Equally, it must not slow the search measurably. One append per level, at most a few dozen per cell,
is fine; anything per fit or per evaluation is not.

### 4. Acceptance: the record must stay bit-identical

Run one cheap cell — system 11, seed 42, IC set 1, `evogrow_v2_2_stage_capped` — into a scratch
history, and compare the produced record field by field against the same cell from the budget
comparison under `outputs/studies/regression/budgetcmp/arm20k.jsonl`.

Every field except timing must be identical, including `loss`, `total_loss_evals`,
`total_parameter_fits`, `support_terms`, `final_stage` and `pruned_match`. That system was chosen
because the budget does not bind there, so the cell is deterministic and any deviation is a real
defect.

Show the heartbeat file this run produced.

### 5. Out of scope

Aggregating heartbeats, a monitoring script, a dashboard, anything that reads them back. Changes to
the record schema, the campaign configuration, the optimizer, or `src/` beyond what the callback
genuinely requires. If a change under `src/` seems necessary, report why before making it.

### 6. Execution limits

One cheap cell. Do not run the suite, the campaign, or any 2D system — two 2D comparison runs are
currently occupying this machine.

Give me the exact commands with expected runtime and pass criterion. I run them.

### Report

Write `codex/REPORT_WP_G1.md`: the file location and format with an example, where the writes happen
for both entry points, how write failures are contained, the field-by-field comparison proving the
record is unchanged, and both fingerprints.
