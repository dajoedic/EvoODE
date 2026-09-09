# WP-N10 Report

## Implementation

Added canonical support keys and duplicate counting for `EvoGrow` in
`src/structure/evogrow.jl`.

The canonical key is built as:

```julia
Tuple(Tuple(sort(unique(eq_terms))) for eq_terms in structure.active_idxs)
```

This preserves the outer equation order and canonicalizes only the terms inside
each equation. Therefore `[u1]` in equation 1 and `[u1]` in equation 2 remain
different keys, while different insertion orders inside the same equation map to
the same key. Parameters are not part of `StructureSpec` and are not read by the
key function.

The key is used only as a `Dict` key for counting. No `StructureSpec` equality,
population selection, child generation, pruning, cache, or deduplication behavior
was changed.

## Count Location

The counter is updated immediately after existing `_evaluate!` calls:

- parent path: only inside the existing `!isfinite(ind.objective)` lazy
  evaluation branch
- child path: after every existing child evaluation

The counting operation calls no random function, does not reorder candidates,
does not change `pop`, `children`, `all_inds`, or sorting, and cannot consume or
shift RNG draws. It only computes a sorted copy of each equation's term vector
and increments `Dict{Any, Int}` counters.

## Metadata and Records

`result.meta.structure` now contains:

- `total_candidate_structures_evaluated`
- `unique_candidate_structures_evaluated`
- `duplicate_candidate_structure_evaluations`
- `structure_repeat_histogram`
- `structure_repeat_quantiles`
- `stage_structure_duplicate_stats`
- per-level `structure_duplicate_stats` inside `level_log`

`studies/regression/run_regression.jl` copies these into records:

- `total_candidate_structures_evaluated`
- `unique_candidate_structures_evaluated`
- `duplicate_candidate_structure_evaluations`
- `structure_repeat_histogram`
- `structure_repeat_quantiles`
- `stage_structure_duplicate_stats`
- `level_structure_duplicate_stats`

The record copy path is guarded with `haskey` and a helper so variants without
these fields keep writing valid records.

## Tests Added

Added `test/test_structure_canonical_key.jl` covering:

- same support with different within-equation term order gives the same key and
  hash
- same term sets assigned to different equations give different keys
- different parameter values on identical support give the same key
- duplicate histogram and totals for a small hand-counted counter

## Runtime-Error Static Review

Checked the changed code for:

- `Set` vs `Vector`: no `Set` operations were added; `unique` returns a vector
  and `sort` returns a sorted vector copy.
- Missing `collect`: `values(counter)` is collected before sorting and quantile
  indexing.
- Indexing with `nothing`: stage counters index only with `current_stage`, which
  is already used for stage arrays and bounded by existing stage logic.
- Hot-loop type instability: counting uses `Dict{Any, Int}` because tuple keys
  have stage/dimension-dependent tuple types; the hot numeric fit path is
  untouched.
- Missing fields: record extraction uses `haskey(meta, ...)`; per-level
  extraction checks `haskey(entry, :structure_duplicate_stats)` before reading
  the field.
- JSON serialization: only string-keyed histograms, named tuples, vectors, and
  primitive counts are written; the internal canonical keys are not serialized.

## Commands for Claude

Short single-cell smoke, expected to print plausible duplicate counts in the
record:

```powershell
$env:FRESH="1"; $env:EVO_REGRESSION_VARIANT="evogrow_v2_2_stage_local"; $env:EVO_REGRESSION_SYSTEM_ID="1"; $env:EVO_REGRESSION_IC_SET="1"; $env:EVO_REGRESSION_SEED="42"; $env:EVO_REGRESSION_HISTORY_PATH="outputs/studies/regression/wp_n10_smoke/history.jsonl"; julia --project=. studies/regression/run_regression.jl
```

Full regression command for the bit-identical comparison against the baseline:

```powershell
$env:FRESH="1"; Remove-Item Env:EVO_REGRESSION_VARIANT -ErrorAction SilentlyContinue; Remove-Item Env:EVO_REGRESSION_SYSTEM_ID -ErrorAction SilentlyContinue; Remove-Item Env:EVO_REGRESSION_IC_SET -ErrorAction SilentlyContinue; Remove-Item Env:EVO_REGRESSION_SEED -ErrorAction SilentlyContinue; $env:EVO_REGRESSION_HISTORY_PATH="outputs/studies/regression/wp_n10_full/history.jsonl"; julia --project=. studies/regression/run_regression.jl
```

Fingerprint checks:

```powershell
julia --project=. -e "include(\"studies/regression/run_regression.jl\"); println(phase_b_fingerprint()); println(stage_cap_behavior_fingerprint())"
```

Expected fingerprints:

- `phase_b_fingerprint()` = `604e79733b22d64d`
- `stage_cap_behavior_fingerprint()` = `ffb0266c7913352c`

## Open Acceptance

Julia was not executed in this Codex session per the standing environment
constraint. The bit-identical regression, fingerprint checks, Julia tests, and
short smoke run remain for Claude.
