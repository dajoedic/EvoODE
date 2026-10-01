# WP-N35 Report

## Status

Implemented. Julia acceptance remains open because Julia is not executable in this Codex environment; this is environment, not substance.

## Changes

- `studies/regression/run_regression.jl`
  - Added `level_heartbeat_fields(snapshot, basis::AbstractBasis)`.
  - The level heartbeat now writes the previous fields `level`, `stage`, and `best_loss` plus 7 new fields:
    - `best_terms`
    - `best_params`
    - `best_objective`
    - `accepted_new_best`
    - `stage_transition`
    - `previous_stage`
    - `new_stage`
  - `best_terms` uses the existing `active_term_names(snapshot.best_structure, basis)` serializer.
  - `best_params` uses the existing `active_model_terms(snapshot.best_structure, basis, snapshot.best_params)` serializer, the same shape as record `model_terms`.
  - `basis` is still built inside the existing `try` block before `discover(...)`, preserving the previous error-record path.

- `analysis/tests/test_wp_n35_heartbeat_fields.py`
  - Added a Python test with an extended fixture derived from:
    - `outputs/stage1/s0.05_r0.5/tasks/cell_000001.heartbeat.jsonl`
    - `outputs/stage1/s0.05_r0.5/tasks/cell_000001.jsonl`
  - The source heartbeat has 22 events and 20 level events. Its first level event has only the old `level`, `stage`, and `best_loss` fields.
  - The derived fixture adds 7 WP-N35 fields to that real level event and keeps the real identity fields.
  - The paired record contributes 5 `support_terms` entries and 5 `model_terms` entries.

## Verification Run By Codex

```text
python -m pytest analysis/tests/test_wp_n35_heartbeat_fields.py
```

Result:

```text
2 passed in 0.10s
```

No Julia command was run by Codex.

## Static Review

Checked:

- `src/` was not modified.
- `CURRENT_TASK.md` was not modified.
- Record fields, fingerprints, and manifests were not modified.
- New heartbeat fields read only from the existing level snapshot and existing `basis`.
- `active_model_terms` still enforces `offset == length(params)`.
- `write_heartbeat!` still serializes through `json_safe(...)`; no record write path was changed.

Potential runtime-sensitive classes reviewed:

- `snapshot.best_params` is the copied vector emitted by `src/structure/evogrow.jl` and `src/structure/evogrow_v3.jl`.
- The acceptance target variant `evogrow_v2_2_stage_capped` uses the EvoGrow snapshot with `best_structure`, `best_params`, `best_loss`, `best_objective`, `accepted_new_best`, `stage_transition`, `previous_stage`, and `new_stage`.
- `basis` is assigned before `discover(...)`, so the callback has a concrete basis when the first level snapshot is emitted.

## Claude Acceptance Commands

Stage-0 control, system 1, seed 42, IC 1 and 2, `(0, 0, 10)` control manifest rows already correspond to indices 1 and 7 in `outputs/wp_n32_stage0/manifest.csv`. Existing reference elapsed times are 8.7268215 s and 12.3882138 s.

```text
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl 1 --manifest outputs/wp_n32_stage0/manifest.csv --output-dir outputs/wp_n35_stage0/tasks
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl 7 --manifest outputs/wp_n32_stage0/manifest.csv --output-dir outputs/wp_n35_stage0/tasks
python analysis/scripts/aggregate/compare_phasec_controls.py --candidate outputs/wp_n35_stage0/tasks --reference-c1 outputs/phase_c_campaign_221a3a7
```

Expected: `compare_phasec_controls.py` reports bit-identical compared records.

Stage-1 cell `(0.05; 0.5)`, system 1, manifest index 1. Existing reference elapsed time is 143.2165498 s.

```text
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl 1 --manifest outputs/stage1/s0.05_r0.5/manifest.csv --output-dir outputs/wp_n35_stage1_s0.05_r0.5/tasks
python analysis/scripts/aggregate/compare_phasec_controls.py --candidate outputs/wp_n35_stage1_s0.05_r0.5/tasks/cell_000001.jsonl --reference-c1 outputs/stage1/s0.05_r0.5/tasks/cell_000001.jsonl
python -c "import json, pathlib; p=pathlib.Path('outputs/wp_n35_stage1_s0.05_r0.5/tasks/cell_000001.heartbeat.jsonl'); rows=[json.loads(line) for line in p.read_text().splitlines() if line.strip()]; levels=[row for row in rows if row.get('event')=='level']; required={'best_terms','best_params','best_objective','accepted_new_best','stage_transition','previous_stage','new_stage'}; print(len(levels), sorted(required <= set(row) for row in levels)); assert levels and all(required <= set(row) for row in levels)"
```

Expected:

- Record comparison is bit-identical against `outputs/stage1/s0.05_r0.5/tasks/cell_000001.jsonl`.
- The heartbeat has at least 1 level event.
- Every level event has all 7 WP-N35 fields.

