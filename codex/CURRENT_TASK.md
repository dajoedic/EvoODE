# CURRENT TASK: WP-H1b — Progress logging for the regression runner

**Language: Julia**

## Context

The regression runner (`studies/regression/run_regression.jl`, WP-H1) is executed externally
by the user, and the runs are long (even 1D System 3 took 218-1217 s per run; Systems 26/63
take hours). The user needs to see progress **live in the terminal (cmd)** and have a
persistent log. This task adds observability only — it must not change any metric, record,
fingerprint, or the fixed configuration, so results stay comparable across the history.

Guiding principle (user's words): logging should be **as little as possible, as much as
necessary**. Keep the screen minimal; put the detail in a file.

## Goal

Add two-layer progress logging to `run_regression.jl`:
- **Terminal (cmd):** a tqdm-style progress bar over all runs, with ETA and the current item,
  plus one concise summary line per finished run.
- **File (`run.log`):** timestamped per-run start/finish lines and the per-level heartbeat from
  EvoGrow, so a long single run is visibly alive.

## Files

- **Modify:** `studies/regression/run_regression.jl`.
- **Modify:** `Project.toml` (and `Manifest.toml`) — add `ProgressMeter` as a dependency.
- **Log file:** `outputs/studies/regression/run.log` (append), consistent with the existing
  run.log convention used by other scripts.
- **Must not change:** `history.jsonl` record schema and values (except the one optional
  additive field in section 4), the metric computation, `config_fingerprint`, and the fixed
  suite/hyperparameters. This is observability only.

## Required Content

### 1. Terminal progress bar (tqdm-style)

Use `ProgressMeter.jl`. Create one `Progress` over the total number of runs
`N = length(VARIANTS) * length(REGRESSION_SYSTEMS) * length(REGRESSION_SEEDS)`. Advance it once
after each completed run. Show ETA and the current item (variant, system_id, seed) beside the
bar (e.g. via `showvalues`). This bar is **terminal-only**: its in-place `\r` updates must not
be written into `run.log`.

Note in a comment that the bar ticks once per run and a single run can take minutes to hours,
so the bar will appear to pause during a run — within-run liveness comes from the run.log
per-level lines (section 2), not the bar.

### 2. run.log with per-run lines and per-level heartbeat

Append to `outputs/studies/regression/run.log`:
- `=== Started at <ISO ts> ===` at start, `=== Finished at <ISO ts> ===` at end.
- One line when each run starts: `[i/N] variant=… sys=… seed=… — start <ts>`.
- One line when each run finishes: `[i/N] variant=… sys=… seed=… — done loss=… stage=…/… pruned=… elapsed=…s`.
- Route the EvoODE logger to this same file (via the exported `set_log_file` / `close_log_file`)
  so EvoGrow's `verbose=1` per-level output ("Level start", "Best individual", stage
  promotions) is captured in run.log as the within-run heartbeat. Close/restore the log file at
  the end.

Flush after each per-run line so external `tail -f` shows it immediately.

### 3. Keep the screen minimal

On stdout, show only the progress bar plus the concise per-run summary line (same content as
the run.log "done" line). Do **not** also print EvoGrow's full per-level detail to stdout —
that verbose stream goes to run.log only. This is the "as little as possible on screen, as much
as necessary in the file" split. Ensure the per-run summary prints cleanly above/around the
ProgressMeter bar rather than corrupting it (ProgressMeter supports printing without breaking
the bar).

### 4. Optional: surface BFGS time-limit hits

The long runs are caused by BFGS hitting its time limit. If it can be obtained cleanly from the
existing fit metadata / logs without new algorithm code, count the number of BFGS time-limit
hits per run and add it to the per-run "done" line (e.g. `bfgs_timeouts=…`) and as an additive,
null-safe field `bfgs_timeout_hits` in the history record. This field must be additive only and
must **not** enter `config_fingerprint`. If obtaining it cleanly is not straightforward, skip
this section entirely — it is a nice-to-have, not a requirement.

## Verification

Run only a small subset for verification (do NOT run the full suite; Systems 26/63 take hours).
Temporarily reduce the loop to a fast subset (Systems 3 and/or 11), confirm, then restore the
full suite before finishing. State which subset was run.

Confirm:
1. In an interactive terminal, a live progress bar with ETA and the current (variant, system,
   seed) is visible and advances once per completed run.
2. `outputs/studies/regression/run.log` contains the start/finish markers, the `[i/N]` per-run
   start and done lines, and EvoGrow per-level lines between them.
3. `history.jsonl` records are unchanged in schema and values relative to WP-H1 (plus the
   optional additive `bfgs_timeout_hits` field if section 4 was implemented). `config_fingerprint`
   is identical to before.
4. The progress bar does not appear in `run.log` (no `\r` garbage in the file).

## Constraints

- Observability only. Do not change the algorithm, metric computations, record values,
  `config_fingerprint`, or the fixed suite/hyperparameters.
- Add `ProgressMeter` to `Project.toml`/`Manifest.toml`; do not add other dependencies.
- The progress bar is terminal-only; the run.log gets plain timestamped lines.
- Do not implement the Python delta report (WP-H2) or any plotting.
- Keep the fixed config block and the history append path exactly as in WP-H1.
