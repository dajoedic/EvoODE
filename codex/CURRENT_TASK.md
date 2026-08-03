# CURRENT TASK

**Language: Julia**

## WP-B2 — Batch entry point and container for an HPC cluster

WP-B1 is delivered (fingerprint `fa2469a4dad1b72c`). The suite now runs the Phase B sampling
protocol but is still driven as a nested loop over variants, systems, initial-condition sets and
seeds inside one process, selected through environment variables. That model does not survive
contact with a batch scheduler.

There is a hard deadline: an HPC consultation on **2026-08-06**. What must exist by then is a setup
that can be shown to run, not a finished campaign. See `docs/hpc_requirements.md` for the resource
profile the setup has to match.

### Target execution model

A Slurm job array. Each array task is one independent process that runs **exactly one cell** and
exits. No loop, no resume logic inside the process — the scheduler owns retries and concurrency.

Three pieces are needed.

**1. A manifest.** A generator that enumerates the campaign as an explicit, ordered list of cells
and writes it to CSV, one row per cell, with a stable integer index as the first column. The index
is what an array task receives. The manifest must be regenerable and identical when regenerated
from the same configuration, and it must record the `config_fingerprint` it was generated under.

The campaign to enumerate: the regression suite as it now stands (5 systems × 2 initial-condition
sets × 3 seeds × the variants in `VARIANTS`). Phase B over all 63 systems is a later work package;
do not build it now, but do not build anything that would have to be thrown away to get there.

**2. A single-cell entry point.** A script that takes one index — from a command-line argument, and
falling back to `SLURM_ARRAY_TASK_ID` — resolves it against the manifest, runs that one cell, writes
one JSONL record to a per-task output file, and exits.

Requirements that follow from running under a scheduler:

- **Exit code** is 0 only if the cell completed and produced a record; non-zero otherwise, so a
  failed task is visible to Slurm rather than silently "successful".
- **Never write to `studies/regression/history.jsonl`.** Each task writes its own file; a separate
  merge step consolidates. Concurrent appends to one file across nodes are not safe.
- **All paths configurable** through environment variables with sane defaults, and no Windows path
  separators anywhere. The target is Linux.
- **Refuse to start on a fingerprint mismatch.** If the manifest was generated under a different
  `config_fingerprint` than the code computes at run time, abort with a clear message rather than
  producing records that cannot be pooled. This is the single most valuable guard in the whole
  setup: a campaign with mixed fingerprints is not publishable.

**3. A merge step.** Collects the per-task files into `history.jsonl`, applying the existing
uniqueness key (variant, system, initial-condition set, seed, fingerprint), reporting how many
records were added and how many were skipped as duplicates. It must be safe to run repeatedly and
must never rewrite or drop existing records.

### Dimension classes

`docs/hpc_requirements.md` §6 asks for separate arrays per system dimension, because the estimated
runtime per cell spans four orders of magnitude and walltime limits are set per array. The manifest
must therefore carry the system dimension as a column, and it must be possible to emit the index
list for one dimension class. How that is expressed — a filter flag, separate manifest files — is
your call; state which you chose and why.

### Container

An Apptainer/Singularity definition (a Dockerfile is acceptable if it converts cleanly) that
produces an image able to run one cell with no network access:

- Julia pinned to **1.11.5**
- `Project.toml` and `Manifest.toml` copied in, then **instantiated and precompiled at build time**.
  If precompilation is left to run time, every array task pays it again.
- `JULIA_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` set in the image. Julia and OpenBLAS otherwise
  each grab all visible cores, which collapses throughput when many single-core tasks share a node.
- The Julia depot inside the image, not on a shared filesystem.
- Repository code and the dataset available to the entry point; outputs written to a bind-mounted
  directory, never inside the image.

Also provide an example Slurm submission script, as documentation rather than something we can test
here: array specification with a concurrency cap, one core, 2 GB, a per-class walltime, and the
container invocation.

### Verification

The environment here is Windows and has no Slurm, so verify what can be verified and say plainly
what could not:

- the manifest generator produces a stable, ordered CSV; regenerating gives an identical file
- resolving indices 1, 2 and the last index yields the expected cells
- **one cheap cell end to end through the batch entry point** — the System 3 cell, initial-condition
  set 1, seed 42, variant `evogrow_v2_2_stage_capped` — writing to a per-task file under
  `outputs/`. Report loss, cap, `eq_overshoot`, `pruned_match`, support and the process exit code.
  WP-B1 measured this cell as loss `5.18873247985214e-9`, cap `[2]`, support `[["u1","u1^2"]]`;
  the batch path must reproduce it **exactly**, since it is the same computation. A deviation is a
  bug in the port, not an acceptable difference.
- the fingerprint guard actually fires: show that a manifest carrying a wrong fingerprint is
  rejected
- the merge step: merging the single record into a **scratch copy** of `history.jsonl` adds one
  record, and merging again adds none
- the container definition is syntactically valid; state explicitly that it was not built here if
  it was not

### One correction to carry along

The `config_fingerprint` payload records `saveat = "range(0.0, 10.0; length=512)"`, but the grid
actually used is the `t` vector read from the dataset. Numerically that vector equals `i*10/511`
exactly, which a Julia `range` need not reproduce bit-for-bit, so the label describes something
other than what runs. Replace it with a description of the true source. This changes the
fingerprint again — which is precisely why it has to happen **now**, before any campaign record
exists, rather than later. Report the new fingerprint value.

### Constraints

- Do not modify `estimate_stage_caps`, the cap policy, the variant definitions, or any ground-truth
  RHS function.
- Do not write to `studies/regression/history.jsonl`.
- Do not run the regression matrix or any multi-cell sweep. One cell for verification, nothing more.
- Generated output goes to its own subfolder under `outputs/`.
- If any part of this is not implementable as stated, stop and report the conflict rather than
  delivering a subset silently.

### Deliverable

The manifest generator, the batch entry point, the merge step, the container definition, the
example submission script, and a report at `codex/REPORT_WP_B2.md` with the new fingerprint, the
verification results, what could not be verified in this environment, and the dimension-class
decision with its reasoning.
