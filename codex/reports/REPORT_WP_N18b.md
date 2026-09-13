# WP-N18b Report - P9 Pilot Verifier Fix

## Scope

Fixed the blocking WP-N18 verifier defect without weakening the go criterion.
No Smoke, Pilot, campaign, Julia, or cluster job was started.

## Decision

The verifier still accepts raw `cell_*.jsonl` files as input, but it now builds the same in-memory
registry view used by `convert_campaign_history_to_run_registry.py` before checking Criterion 1.

Rationale:

- `success` and `failure_reason` are registry fields, not raw record fields.
- The raw record success source is `error`; the shared converter maps `error in ("", None)` to
  `success == True` and writes an empty `failure_reason`.
- Criterion 1 remains strict: every converted registry row must have `success is True` and empty
  `failure_reason`.
- Criterion 4 now pairs the converted registry rows, so the WP-N14 allowlist is used unchanged.
  No pilot-local extension for `manifest_index` or `batch_output_file` remains.

Criterion 3 intentionally stays on the raw records because it validates real Julia record fields:
support hits, model-term coefficients, basis name, support-definition marker, duplicate counter,
and restart counters.

## Files Changed

- `analysis/scripts/aggregate/verify_phasec_p9_pilot.py`
  - Imports and reuses `row_from_record`.
  - Converts raw records to registry rows in memory.
  - Checks Criterion 1, Criterion 2 identity fields, and Criterion 4 pairing on registry rows.
  - Keeps Criterion 3 and Criterion 5 on raw records.
  - Removes the extra pilot allowlist entries for `manifest_index` and `batch_output_file`.
- `analysis/tests/test_phasec_p9_pilot.py`
  - Derives fixtures from
    `outputs/studies/regression/phase_c/smoke_tasks/cell_000001.jsonl`.
  - Removes invented raw `success` and `failure_reason` fixture fields.
  - Adds a direct Criterion 1 check over sixteen copies of the real Smoke-record shape.
  - Adds a CLI regression where sixteen Smoke-record copies reach Criterion 2, not the old
    `success is None` Criterion 1 failure.

## Runbook

The verifier command is unchanged:

```powershell
python analysis/scripts/aggregate/verify_phasec_p9_pilot.py `
  --records-dir outputs/studies/regression/phase_c/p9_pilot_tasks `
  --manifest outputs/studies/regression/phase_c/manifest.csv `
  --reconstruction-probe outputs/studies/regression/phase_c/p9_pilot_wp_n5/reconstruction_probe.csv `
  --expected-git-hash <COMMIT_SHA> `
  --expected-stage-cap-behavior-fingerprint <STAGE_CAP_BEHAVIOR_FINGERPRINT>
```

The input remains the raw Pilot record directory. The registry conversion is internal to the
checker.

## Verification

```text
python -m pytest analysis/tests/test_phasec_p9_pilot.py -q --basetemp .pytest_tmp
8 passed in 1.05s

python -m pytest analysis/tests -q --basetemp .pytest_tmp
45 passed in 8.24s
```

The explicit Smoke-copy regression passes Criterion 1 and exits at Criterion 2 because sixteen
copies are not a valid pilot set. This confirms the old `success is None` failure is gone.
