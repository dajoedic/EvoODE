# CURRENT TASK: WP-H1 — Regression-history runner and append-only store

**Language: Julia**

## Context

As EvoGrow evolves (v2.2 → v3.x), we need a longitudinal record of how the key metrics on a
fixed diagnostic set change across algorithm versions and commits — i.e. whether each change
makes results better or worse per system. The existing logs do not provide this: they are
either within-experiment snapshots (`run_registry.csv`, aggregates) or the narrative DIARY.

This WP builds the **Julia half** of a "regression-history" tool (agreed scope: Medium):
a runner that executes a fixed diagnostic suite on the current code and appends the results
to an append-only history file, tagged with the git commit and a config fingerprint.

A **later, separate task WP-H2 (Python)** will read this history and produce the delta report
(latest commit vs. previous, per cell ↑/↓/=) and a DIARY-ready markdown block. Do **not**
implement WP-H2 here — this task only produces the runner and the history store.

## Goal

Create `studies/regression/run_regression.jl`, a runner that:
- runs a **fixed** diagnostic suite (systems, seeds, hyperparameters) for one or more
  algorithm variants on the current code,
- computes the standard diagnostic metrics per run,
- appends one record per (variant, system, seed) to an append-only history file, tagged with
  git provenance and a config fingerprint.

The fixed suite and metric logic mirror the existing `studies/phase1_diag/run_phase1_diag.jl`.

## Files

- **New:** `studies/regression/diagnostic_systems.jl` — the fixed suite definitions
  (system list with `system_id`, `system_name`, `dim`, `u0`, `tspan`, `T`, `expected_stage`;
  the ground-truth RHS functions; the expected-terms / support-match logic). Extract these
  from `studies/phase1_diag/run_phase1_diag.jl` verbatim in behavior. This file must contain
  **no top-level execution** (no `main()` call) so it can be `include`d.
- **New:** `studies/regression/run_regression.jl` — the runner; `include`s
  `diagnostic_systems.jl` and `src/EvoODE.jl`.
- **New (append-only, tracked):** `studies/regression/history.jsonl` — created on first run,
  then only appended to. This file is committed to the repo (it is the longitudinal record,
  like DIARY, not bulk output).
- **Do not modify** `studies/phase1_diag/run_phase1_diag.jl`.

## Required Content

### 1. Fixed diagnostic suite

- Systems: 3, 11, 26, 31, 63 (the Gate-1 problem/control systems), with the exact
  `u0`, `tspan`, `T`, `expected_stage` from `run_phase1_diag.jl`.
- Seeds: the phase1_diag seed list `[42, 123, 7]`.
- Hyperparameters: fixed and equal to the phase1_diag configuration (`pop_size=10`,
  `n_levels=30`, `children_per_parent=2`, `max_terms_per_eq=6`, `λ=1e-3`,
  `min_levels_per_stage=2`, `new_term_bias_prob=0.75`, `use_pretuning=false`, and the same
  `DiscoveryOptions`). `BFGSOptimizer(maxiters=200)`.

Note in a comment that runtime is dominated by Systems 26 and 63 (26 and especially 63 can
take hours). Do not add subsetting logic in this WP, but keep the system list defined in one
obvious place so it can be trimmed later; because the system set is part of the fingerprint
(below), a trimmed suite forms a separate, cleanly-separated track.

### 2. Variants under test

Run these variants in a single invocation, each producing its own records:
- `evogrow_v2_2_stage_local` — `EvoGrow` with `progression=:stage_local`, `usage=:hard`.
- `evogrow_v3` — `EvoGrowV3` with the same progression/usage.

Structure the variant list so new variants (e.g. later v3 stages) can be added with one line.
Each variant contributes `n_systems × n_seeds` records per invocation.

### 3. Config fingerprint

Compute a stable `config_fingerprint` string (e.g. a hash) over **only the metric-affecting
configuration**: the sorted system-id list, the seed list, and all fixed hyperparameters and
`DiscoveryOptions` values and the trajectory-generation settings. It must **not** include the
variant label or the git hash. The fingerprint is what lets WP-H2 compare only like-for-like
runs; changing any hyperparameter or the system set must change the fingerprint.

### 4. Metrics per run

Reuse the phase1_diag metric computations: `loss`, `pruned_match` (from
`support_match_pruned`), `final_stage`, `expected_stage`, `stage_overshoot`, `wasted_levels`,
`elapsed_s`. Additionally, when the variant exposes it (v3), record `eq_final_stages`
(else `null`). Wrap each run in a try/catch as phase1_diag does; on error record the error
string and null metrics, but still append a record.

### 5. History record and append semantics

Append **one JSON object per line** to `studies/regression/history.jsonl` (JSONL). Never
rewrite or truncate the file. Each record contains at least:

```text
timestamp            ISO 8601
git_hash             current HEAD (short is fine)
git_dirty            true if the working tree has uncommitted changes at run time
variant              variant label
config_fingerprint   as defined above
system_id, system_name, seed
loss, pruned_match, final_stage, expected_stage, stage_overshoot, wasted_levels, elapsed_s
eq_final_stages      vector or null
n_levels, use_pretuning
```

`git_hash` and `git_dirty` should be obtained by shelling out to git (e.g. `git rev-parse`
and a porcelain/dirty check); if git is unavailable, record `git_hash="unknown"` and
`git_dirty=null` rather than failing the run.

Print a concise per-run summary line to stdout (like phase1_diag) and, at the end, print how
many records were appended and the resulting total line count of the history file.

### 6. Output-directory convention

Any bulk/per-run diagnostic artifacts (if you write any) go under
`outputs/studies/regression/`. The curated `history.jsonl` is the exception: it lives in
`studies/regression/` and is tracked. Do not write bulk data into `studies/`.

## Verification

1. Running the script once creates `studies/regression/history.jsonl` and appends
   `2 variants × 5 systems × 3 seeds = 30` records (or fewer systems if runtime forces a
   documented smaller test — but the default suite is all five).
2. Running it a **second time** on the same HEAD appends another block without overwriting the
   first; the file's line count doubles.
3. Records for `evogrow_v2_2_stage_local` and `evogrow_v3` on the same (system, seed) have
   identical `loss`, `pruned_match`, `final_stage` (lockstep anchor — confirms the store
   captures the WP-v3.2 equivalence).
4. `config_fingerprint` is identical across all records of one invocation and stays identical
   on re-run; changing any hyperparameter in the config changes it.
5. Each line is valid JSON and contains all fields listed in section 5.

Because a full run is slow (Systems 26/63), it is acceptable to demonstrate Verification 1–5
on a temporarily reduced system list during development, but the committed default suite must
be the full five systems. State clearly in the task report which systems were actually run
for verification.

## Constraints

- Do not modify `studies/phase1_diag/run_phase1_diag.jl` or any `src/` file. This is a new,
  self-contained study tool that only consumes the public EvoODE API and reuses the diagnostic
  definitions by copying them into `diagnostic_systems.jl`.
- `history.jsonl` is append-only. Never rewrite existing lines.
- Follow existing conventions: `Pkg.activate` the repo, route logs through the existing
  logging where sensible, keep the fixed config in one obvious block.
- Do not implement the Python delta report or any plotting — that is WP-H2.
