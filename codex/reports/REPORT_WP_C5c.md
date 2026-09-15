# WP-C5c Report

## Changes

- Fixed `read_heartbeat` in `studies/regression/analyze_wasted_search_levels.jl` so both discarded-level aggregations return `0` for empty inputs:
  - no selected segment with level events: `sum((length(segment.levels) for segment in segments); init = 0)`
  - selected segment exists, but all other segments form an empty filtered generator: `sum((... if idx != selected_index); init = 0)`
- Added a regression test in `test/test_wp_c5_heartbeat_segments.jl` for a stream with no evaluable `level` events.

## Fixture Derivation

- The new test derives its temporary fixture from a real heartbeat selected by the existing `_real_single_segment_heartbeats(2)` search under `outputs/`.
- In this working tree, the first matching sorted source is `outputs/docker_wp_h2_default/tasks/cell_000061.heartbeat.jsonl`.
- The fixture writer copies only the first real `start` line into a temporary `start_only.heartbeat.jsonl`, producing a stream with one segment, no level events, and no malformed lines.

## Acceptance

Codex did not run Julia in this session. Per `codex/CODEX_PROTOCOL.md` and `codex/CURRENT_TASK.md`, Julia execution is blocked by the Codex environment and Claude runs the acceptance.

Commands for Claude:

```bash
julia --project=. test/test_wp_c5_heartbeat_segments.jl
```

Expected scope: the test file should complete with zero failures and zero errors, including the new `stream without evaluable level events returns empty result` testset.

Testergebnis: not from this Codex session; must come from Claude's run.
