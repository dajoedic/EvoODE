# WP-G1 Report - Heartbeat file per batch cell

## Summary

Implemented heartbeat JSONL logging for regression cells without changing record schemas, numerical behavior, or fingerprints.

- Regression fingerprint: `45cb2c4507007366`
- Phase B fingerprint: `c0a236edf030e03a`
- No `src/` files changed.
- Heartbeat write failures are contained and never abort a run.

## Heartbeat Location And Format

Suite runner heartbeats are written below the history directory:

```text
dirname(HISTORY_PATH)/heartbeats/<variant>_sys<system_id>_ic<initial_condition_set>_seed<seed>.heartbeat.jsonl
```

Acceptance example:

```text
outputs/studies/regression/wp_g1/heartbeats/evogrow_v2_2_stage_capped_sys11_ic1_seed42.heartbeat.jsonl
```

Batch runner heartbeats are written next to the batch cell output:

```text
<output_dir>/cell_<manifest_index padded to 6 digits>.heartbeat.jsonl
```

Example:

```text
<output_dir>/cell_000063.heartbeat.jsonl
```

The file format is JSONL, one JSON object per line. Common fields are:

- `timestamp`
- `event`
- `variant`
- `condition`
- `system_id`
- `initial_condition_set`
- `seed`
- `config_fingerprint`
- `pid`
- `hostname`
- `entry_point`

`start` lines include only the common cell context. `level` lines also include `level`, `stage`, and `best_loss`. `complete` lines also include `error`, `loss`, `final_stage`, and `pruned_match`.

For batch cells, additional context fields are included:

- `manifest_index`
- `manifest_path`
- `batch_output_file`

## Example Heartbeat Lines

Start:

```json
{"event":"start","system_id":11,"config_fingerprint":"45cb2c4507007366","variant":"evogrow_v2_2_stage_capped","entry_point":"run_regression","pid":46420,"hostname":"KIGEND","condition":"evogrow_v2_2_stage_capped","initial_condition_set":1,"seed":42,"timestamp":"2026-08-11T21:47:32.561Z"}
```

Level:

```json
{"event":"level","best_loss":0.1835299084368645,"system_id":11,"config_fingerprint":"45cb2c4507007366","level":1,"variant":"evogrow_v2_2_stage_capped","entry_point":"run_regression","pid":46420,"hostname":"KIGEND","stage":1,"condition":"evogrow_v2_2_stage_capped","initial_condition_set":1,"seed":42,"timestamp":"2026-08-11T21:47:47.364Z"}
```

Complete:

```json
{"event":"complete","final_stage":4,"system_id":11,"config_fingerprint":"45cb2c4507007366","variant":"evogrow_v2_2_stage_capped","entry_point":"run_regression","pid":46420,"error":null,"hostname":"KIGEND","condition":"evogrow_v2_2_stage_capped","loss":4.669965487288931e-15,"initial_condition_set":1,"seed":42,"timestamp":"2026-08-11T21:47:50.532Z","pruned_match":true}
```

## Write Sites

The shared write path is in `studies/regression/run_regression.jl`.

- `run_one(...)` creates a heartbeat sink from the supplied `heartbeat_path`.
- It writes `start` before the search begins.
- It writes one `level` event from `level_callback`.
- It writes `complete` in the `finally` block when the cell finishes.

The suite entry point passes:

```julia
heartbeat_path = suite_heartbeat_path(variant, system, ic_set, seed)
heartbeat_extra = Dict("entry_point" => "run_regression")
```

The batch entry point in `studies/regression/run_batch_cell.jl` passes:

```julia
heartbeat_path = _heartbeat_output_path(output_dir, index)
heartbeat_extra = Dict(
    "entry_point" => "run_batch_cell",
    "manifest_index" => index,
    "manifest_path" => _portable_path(manifest_path),
    "batch_output_file" => _portable_path(output_path),
)
```

## Failure Containment

`write_heartbeat!` catches all heartbeat write exceptions, disables the sink after the first failure, and does not rethrow. Each successful write opens the heartbeat file in append mode, writes one JSON line, writes a newline, and flushes before returning.

This keeps heartbeat logging observational only: it does not change records, fingerprints, optimization, budgets, pruning, or result values.

## Validation Commands

Fingerprint check:

```powershell
julia --project=. --startup-file=no --% -e "include(\"studies/regression/run_regression.jl\"); include(\"studies/regression/phase_b_config.jl\"); println(config_fingerprint()); println(phase_b_fingerprint())"
```

Expected pass criterion:

```text
45cb2c4507007366
c0a236edf030e03a
```

Observed runtime: about 251 s wall clock.

Cheap acceptance cell:

```powershell
$env:EVO_REGRESSION_HISTORY_PATH='outputs/studies/regression/wp_g1/acceptance_history.jsonl'
$env:FRESH='1'
$env:EVO_REGRESSION_VARIANT='evogrow_v2_2_stage_capped'
$env:EVO_REGRESSION_SYSTEM_ID='11'
$env:EVO_REGRESSION_IC_SET='1'
$env:EVO_REGRESSION_SEED='42'
julia --project=. --startup-file=no studies/regression/run_regression.jl
```

Expected pass criterion: one appended record for system 11, seed 42, IC set 1, variant `evogrow_v2_2_stage_capped`; heartbeat file exists and contains `start`, per-level `level`, and `complete` events.

Observed summary:

```text
Regression history fingerprint: 45cb2c4507007366
variant=evogrow_v2_2_stage_capped sys=11 ic=1 seed=42 loss=4.670e-15 stage=4/4 pruned=true elapsed=12.2s
Total cells: 1
Run this invocation: 1
Appended 1 records to outputs/studies/regression/wp_g1/acceptance_history.jsonl
History line count: 1
```

Observed runtime: about 102 s wall clock.

Field comparison command:

```powershell
@'
import json
from pathlib import Path

new_path = Path("outputs/studies/regression/wp_g1/acceptance_history.jsonl")
ref_path = Path("outputs/studies/regression/budgetcmp/arm20k.jsonl")

new = json.loads(new_path.read_text().splitlines()[0])
ref = None
for line in ref_path.read_text().splitlines():
    row = json.loads(line)
    if (
        row.get("variant") == "evogrow_v2_2_stage_capped"
        and row.get("system_id") == 11
        and row.get("seed") == 42
        and row.get("initial_condition_set") == 1
    ):
        ref = row
        break

timing = {
    "timestamp",
    "elapsed_s",
    "total_parameter_optimization_time_s",
    "total_simulation_time_s",
    "screening_time_s",
    "polish_time_s",
    "rejected_diagnostic_time_s",
}

keys = sorted((set(new) | set(ref)) - timing)
diffs = [(key, ref.get(key), new.get(key)) for key in keys if ref.get(key) != new.get(key)]
print("fields_compared", len(keys))
print("diffs", len(diffs))
for key in ["loss", "total_loss_evals", "total_parameter_fits", "support_terms", "final_stage", "pruned_match"]:
    print(key, ref.get(key), new.get(key))
'@ | python -
```

Expected pass criterion: `diffs 0`, with the requested key fields identical.

Observed:

```text
fields_compared 64
diffs 0
loss 4.669965487288931e-15 4.669965487288931e-15
total_loss_evals 11006 11006
total_parameter_fits 290 290
support_terms [['u1', 'u1^2', 'u1^3']] [['u1', 'u1^2', 'u1^3']]
final_stage 4 4
pruned_match True True
```

Only the requested cheap cell was run. No suite, campaign, or 2D execution was performed.
