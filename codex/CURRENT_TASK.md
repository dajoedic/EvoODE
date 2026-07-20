# CURRENT TASK: WP-H1c — Within-run live progress bar for the regression runner

**Language: Julia**

## Context

WP-H1b added an outer `ProgressMeter` bar over all runs plus a `run.log`. But that outer bar
only advances at the END of each run (`next!` after `discover`), so during a single long run
(System 3: minutes; System 63: hours) the terminal shows a static bar and no on-screen sign of
life. The within-run heartbeat currently goes only to `run.log`.

This task adds a **second, inner progress bar per run**, driven live from within `discover`, so
the user sees per-level progress in the terminal without a second `tail -f` window. EvoGrow and
EvoGrowV3 already expose the `level_callback` hook (a `Union{Nothing,Function}` field) that is
invoked at the end of every level with a snapshot NamedTuple — no `src/` change is needed.

This is observability only: metrics, record schema, `config_fingerprint`, and the fixed
configuration must not change.

## Goal

In `studies/regression/run_regression.jl`, show a live inner progress bar per run that ticks
once per level (Level x/n, current stage, current best loss), stacked below the existing outer
per-run bar. Keep `run.log` and the minimal-screen behavior from WP-H1b.

## Files

- **Modify only:** `studies/regression/run_regression.jl`.
- **Do not modify `src/`.** EvoGrow and EvoGrowV3 already call
  `strategy.level_callback(snapshot)` at the end of each level. The snapshot is a NamedTuple
  whose fields include at least `level::Int`, `stage::Int`, `best_loss::Float64`, and
  `best_objective::Float64`. Read those fields; do not assume others.

## Required Content

### 1. Let variants accept a per-run level callback

Change the `VARIANTS` constructors so each takes a `level_callback` argument and passes it into
the strategy via the existing `level_callback` keyword (both `EvoGrow` and `EvoGrowV3` support
it). `run_one` then builds the strategy with the inner-bar callback it created for that run.
Everything else about the variant configuration stays identical (so results are unchanged).

### 2. Inner progress bar per run

In `run_one`, before calling `discover`:
- Create an inner `Progress` whose total is the effective level cap
  `min(N_LEVELS, OPTIONS_CONFIG.max_levels)`.
- Build a `level_callback` closure that, on each call, advances the inner bar and shows the
  current run's `system_id`, `seed`, `snapshot.level`, `snapshot.stage`, and `snapshot.best_loss`
  via `showvalues`.
- After `discover` returns (or errors), `finish!` the inner bar. Put the `finish!` in a
  `try/finally` so an errored run still closes its inner bar cleanly.

The inner bar ticks once per level. Note in a comment that a single level can still pause for up
to the BFGS time limit (~300 s) if that call is slow — this is expected and far better than the
per-run granularity of the outer bar.

### 3. Stack the two bars without clobbering

The outer (per-run) bar and the inner (per-level) bar are shown at the same time. Use
`ProgressMeter`'s multi-bar mechanism: give each bar a distinct `offset` so they occupy separate
terminal lines and do not overwrite each other (e.g. outer `offset = 0`, inner `offset = 1`).
Verify the two bars render cleanly together and that the inner bar is recreated per run.

Keep both bars on `ProgressMeter`'s default stream (stderr). Keep the existing
`redirect_stdout(devnull)` around `discover` so EvoGrow's per-level `stdout` text stays off the
screen (it continues to go to `run.log` through the logger). The result: screen shows only the
two bars; `run.log` keeps the full per-level detail.

### 4. Unchanged behavior

`run.log` content/format, the history record schema and values, `config_fingerprint`, and the
fixed suite/hyperparameters must be identical to WP-H1b. The only changes are the `VARIANTS`
constructor signature and the inner-bar wiring in `run_one`/`main`.

## Verification

Run only a small, fast subset (Systems 3 and/or 11); do not run the full suite (26/63 take
hours). Temporarily reduce the loop, confirm, then restore the full suite before finishing, and
state which subset was run. Confirm:

1. During a run, the inner bar updates live per level (level number and best loss change while
   the run is in progress), stacked below the outer bar which advances once per completed run.
2. Both bars render without overwriting each other; the inner bar resets for each new run.
3. `run.log` still contains the start/finish markers, `[i/N]` lines, and the per-level heartbeat.
4. `history.jsonl` records and `config_fingerprint` are unchanged relative to WP-H1b.

## Constraints

- Observability only: do not change the algorithm, metrics, record values, `config_fingerprint`,
  or the fixed configuration.
- Modify only `studies/regression/run_regression.jl`; do not touch `src/` or add dependencies
  (`ProgressMeter` is already present).
- Keep `redirect_stdout(devnull)` around `discover` so the screen stays minimal (bars only).
- Do not implement the Python delta report (WP-H2) or any plotting.
