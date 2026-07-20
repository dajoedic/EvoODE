# CURRENT TASK: WP-H1d — Resume support (skip already-completed cells)

**Language: Julia**

## Context

The external full run of `studies/regression/run_regression.jl` was interrupted by a machine
restart after 7 of 30 records. Thanks to the append-only `history.jsonl`, those 7 records
survived (and are committed). But re-running currently redoes the entire suite, including a
single System-26 run that took ~3 hours.

This task makes the runner **resumable**: on start it skips any (variant, system, seed) cell
that already has a successful record in `history.jsonl` for the current `config_fingerprint`,
so a re-run continues from where it stopped instead of recomputing finished work. This also
hardens the runner against the next interruption.

This is resilience/observability only. It must NOT change `config_fingerprint`, the record
schema/values, the metric computations, or the fixed suite/hyperparameters.

## Goal

Before the run loop, load existing history and build the set of already-completed cells; skip
those cells in the loop (advancing the outer progress bar and logging a skip line), and run only
the remaining cells. Report skipped/run/total counts at the end.

## Files

- **Modify only:** `studies/regression/run_regression.jl`.
- Do not touch `src/`, `Project.toml`, or the fixed config.

## Required Content

### 1. Load completed cells at startup

After computing `fingerprint = config_fingerprint()` and before the run loop, read
`history.jsonl` (if it exists) line by line and build a set of "completed keys". A record counts
as completed iff:
- its `config_fingerprint` equals the current `fingerprint`, AND
- its `error` field is `null` (successful run only — errored/failed cells must be retried).

The completed key is the tuple `(variant, system_id, seed)`. Parse each line as JSON; ignore any
malformed line defensively (do not crash the run on a bad line).

Rationale for keying on `config_fingerprint` and NOT `git_hash`: the interrupted records were
produced at an earlier commit, and this task will itself be a new commit. Because the config
(and therefore the fingerprint) is unchanged and this task does not alter algorithm behavior,
records from the interrupted run must still be recognized and skipped. A resumed baseline may
therefore span more than one `git_hash`; that is acceptable and expected.

### 2. Skip completed cells in the loop

In the `main` run loop, for each `(variant, system, seed)`:
- If its key is in the completed set: **skip it** — do not build a trajectory, do not run
  `discover`, do not append a record. Advance the outer progress bar by one and append a skip
  line to `run.log`, e.g. `[i/N] variant=… sys=… seed=… — skipped (already in history)`.
  Do not create an inner progress bar for skipped cells.
- Otherwise: run it exactly as today (append record, inner bar, done line, etc.).

Keep the outer progress bar total at the full `N = variants × systems × seeds`, so the bar
reflects true overall completion (skipped cells count as done).

### 3. Optional fresh-run override

Support an optional environment flag to force a full re-run that ignores existing history
(e.g. `FRESH=1` / `FRESH=true`): when set, the completed set is treated as empty so every cell
runs. Keep this minimal; default behavior (no flag) is resume.

### 4. End-of-run reporting

At the end, print counts: total cells, number skipped (already completed), number run this
invocation, and the resulting `history.jsonl` line count.

## Verification

Run only a small, fast subset (Systems 3 and/or 11); do not run the full suite. Temporarily
reduce the loop for verification, then restore the full suite before finishing, and state which
subset was run. Confirm:

1. First invocation on a fresh (empty) history runs all subset cells and appends their records.
2. Second invocation with the same history **skips all** already-completed cells (appends no new
   records; `run.log` shows skip lines; the end report shows skipped==subset size, run==0).
3. A cell whose only record has a non-null `error` is **not** skipped (it is retried).
4. `FRESH=1` (if implemented) forces all cells to run again.
5. `config_fingerprint`, the record schema, and existing record values are unchanged.

## Constraints

- Resilience/observability only: do not change the algorithm, metrics, record values,
  `config_fingerprint`, or the fixed configuration.
- Skip is keyed on `(config_fingerprint, variant, system_id, seed)` with `error == null`; do not
  key on `git_hash`.
- Modify only `studies/regression/run_regression.jl`; add no dependencies.
- Malformed history lines must not crash the run.
- Do not implement the Python delta report (WP-H2) or any plotting.
