# REPORT WP-C5d

## Change

Updated `test/test_wp_c5_heartbeat_segments.jl` only.

`_write_first_start_only` now records whether a `start` event was found in `found_start`, breaks out
of the input loop after writing the first matching line, and returns from the outer function after
both `open` blocks have closed.

The error path remains reachable: if the source stream contains no non-empty JSON line whose
`event` field is `"start"`, `found_start` remains `false` and the function still raises:

```text
Source heartbeat has no start event: <src>
```

## Helper Review

Checked `test/test_wp_c5_heartbeat_segments.jl` for `return` statements inside `do` blocks.

- `_legacy_read_heartbeat`: no `return` inside the `open(... ) do` block.
- `_heartbeat_counts`: no `return` inside the `open(... ) do` block.
- `_write_without_start`: no `return` inside the nested `open(... ) do` blocks.
- `_append_first_start`: has a `return` inside the inner `open(src, "r") do` block. This is OK for
  its current use because the helper has no post-block error path or success value; the return only
  stops scanning after appending the first start line, and the selected source fixture is already
  required by `_real_single_segment_heartbeats` to contain exactly one start event.
- `_write_first_start_only`: previously had the broken pattern. Fixed as described above.
- `_write_concatenated_streams`: no `return` inside the `open(... ) do` block.

## Verification

Static check:

```text
rg -n "return| do|found_start|error\(" test/test_wp_c5_heartbeat_segments.jl
```

Result: the only remaining `return` inside a `do` block is in `_append_first_start`, reviewed above.
`_write_first_start_only` now returns from the outer function after the `open` blocks.

Attempted acceptance command:

```text
julia --project=. test/test_wp_c5_heartbeat_segments.jl
```

Result in this Codex environment:

```text
Program 'julia.exe' failed to run: A specified logon session does not exist.
```

No passing Julia test result is reported by Codex. The acceptance result for this Julia task must
come from Claude's environment.
