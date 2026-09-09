# WP-N8 Report

## Changes

- `studies/regression/wp_n1_basis_probe.jl` now uses the existing `git_provenance()` from
  `studies/regression/run_regression.jl` instead of the hard-coded
  `(git_hash = "not_collected", git_dirty = nothing)`.
- `git_hash` and `git_dirty` are written by `run_one(...)` into every record. The probe now also
  writes `base_config_fingerprint = phase_b_fingerprint()` as its own record field.
- `stage_cap_behavior_fingerprint` was already written by `run_one(...)` and is unchanged.

## Identity guard

- Invalid identity means `git_hash` is `nothing`, empty after stripping, `not_collected`, or
  `unknown`.
- Without override, the script errors before calling `run_one(...)` or appending the first record:
  `WP-N1 identity guard failed: ... A probe run without collected git identity is invalid for
  configuration decisions`.
- Development override: `WP_N1_ALLOW_PLACEHOLDER_IDENTITY=1`.
- Development records are marked with:
  - `probe_identity_definition = "collected_git_identity_v1"`
  - `probe_identity_mode = "development"`
  - `probe_identity_override_env = "WP_N1_ALLOW_PLACEHOLDER_IDENTITY"`
  - `probe_identity_override_reason = <invalid git_hash reason>`
- Normal records are marked with `probe_identity_mode = "collected"` and carry the same
  `probe_identity_definition`.

## Old versus new probe data

- Existing records under `outputs/wp_n1_dim1_probe/history.jsonl` were not modified.
- A read-only sample of 3 existing records showed `git_hash = "not_collected"`, `git_dirty = null`,
  and no `probe_identity_definition` or `probe_identity_mode`.
- New records are distinguishable by the explicit `probe_identity_definition` field, following the
  WP-N7b pattern of carrying the semantic definition in the data.
- Resume and summary generation now require both the current `probe_identity_definition` and the
  current `probe_identity_mode`, so old placeholder records and development records do not silently
  count as completed cells for collected-identity runs.

## Commands for Claude

Short smoke run over 3 cells:

```bash
julia --project=. --startup-file=no studies/regression/wp_n1_basis_probe.jl --dim=1 --limit=3
```

Expected cells: 3.

Full dim-2 run:

```bash
WP_N1_ALLOW_DIM2=1 julia --project=. --startup-file=no studies/regression/wp_n1_basis_probe.jl --dim=2
```

Expected cells: 336 (`28` dim-2 systems x `2` basis variants x `2` IC sets x `3` seeds).

## Static review

Julia was not executed in this Codex session, per the environment restriction.

Checked statically:

- Included provenance source: `git_provenance()` is available through the existing
  `include(joinpath(@__DIR__, "run_regression.jl"))`.
- Record fields used by `summary_line(record)` are still produced by `run_one(...)` before the
  probe adds WP-N1 fields.
- `base_config_fingerprint` and identity fields are added before `_wp_n1_append!(...)`.
- `JSON3.Object` access in history readers uses the same `haskey(record, :field)` and
  `getproperty(record, :field)` pattern already used in this script.
- `Set{Tuple{String, Int, Int, Int}}` remains the completed-cell container; tuple keys are not
  compared against vectors.
- Meta arrays already use `collect(...)` in `run_one(...)`; the WP-N1 changes add no new Set/Vector
  conversions.
- Empty history and `--limit=0` write a summary header without indexing `records[1]` or `group[1]`.
- `--limit` is parsed as a non-negative integer and caps the total number of visited cells before
  any run is started beyond that cap.

## Acceptance status

Blocked by environment, not by implementation: Julia cannot be executed in this Codex session, so
the runtime acceptance points must be run by Claude.
