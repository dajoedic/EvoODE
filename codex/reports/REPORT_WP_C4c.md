# REPORT WP-C4c

## Status

Blocked: environment/input, not implementation.

Implemented files:

```text
studies/regression/phase_c_trajectory_hashes.jl
analysis/scripts/aggregate/run_phasec_sindy_baseline.py
analysis/tests/test_phasec_sindy_baseline.py
```

The Julia export could not be executed in this Codex session because Julia is unavailable in the
known Codex environment. The full SINDy rerun also cannot be executed here because the required
campaign trajectory export does not exist until Claude runs the Julia exporter.

## Julia Export

`studies/regression/phase_c_trajectory_hashes.jl` now exports the same byte streams that it hashes.

Format:

```text
dtype: float64
byte_order: little_endian
time_axis_order: time
state_axis_order: time_by_dimension_c_order
hash_format: sha256_raw_little_endian_float64
manifest: trajectory_manifest.csv
```

For each `(system_id, initial_condition_set)`, the script writes:

```text
cells/system_XXXX_icY_time_f64le.bin
cells/system_XXXX_icY_state_f64le_c_order.bin
```

The manifest stores `time_sha256`, `state_sha256`, shapes, min/max fields, and relative paths. The
same serialization helpers feed both SHA-256 calculation and file writing.

## Python Loading

`run_phasec_sindy_baseline.py run-sindy` now requires:

```text
--trajectory-export-dir PATH
```

There is no default export path. The Phase-C truth trajectories are loaded only from
`trajectory_manifest.csv` and the raw binary files. Missing manifest/files, unsupported format fields,
wrong shapes, differing time grids, or SHA-256 mismatches raise `ValueError` and abort the run.

Optional output overrides were added so the export-based rerun can be written next to the old
baseline instead of overwriting it:

```text
--output-data-dir PATH
--output-table-dir PATH
```

The old truth-trajectory `solve_ivp` path is no longer used by Phase-C `run-sindy`. The existing
`simulate_model` path remains in use for reconstruction and generalization of the fitted SINDy model.

## Difference Report Tool

Added:

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py compare-details \
  --reference-details analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv \
  --candidate-details <new_export_based_run>/details.csv \
  --output analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/detail_delta_summary.csv
```

It reports:

```text
n_rows_reference
n_rows_candidate
n_rows_paired
r2_gt_0_9_changed_count
sindy_structure_hit_raw_changed_count
sindy_structure_hit_pruned_changed_count
r2_abs_delta_finite_count
r2_abs_delta_q000
r2_abs_delta_q025
r2_abs_delta_q050
r2_abs_delta_q075
r2_abs_delta_q100
```

## Verification Run Here

Python tests:

```text
python -m pytest analysis/tests/test_phasec_sindy_baseline.py --basetemp outputs\pytest-wp-c4c
```

Result:

```text
12 passed in 5.64s
```

All Python tests:

```text
python -m pytest analysis/tests --basetemp outputs\pytest-wp-c4c-all
```

Result:

```text
59 passed in 14.60s
```

CLI missing-export abort:

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py run-sindy \
  --config analysis/configs/paper1_phaseC_sindy_baseline.json \
  --trajectory-export-dir outputs\missing-wp-c4c-export
```

Result:

```text
Error: missing trajectory export manifest: ...\outputs\missing-wp-c4c-export\trajectory_manifest.csv
```

The hash-mismatch abort is covered by
`test_load_exported_trajectories_rejects_hash_mismatch`.

## Commands For Claude

Short Julia export smoke:

```text
julia --project=. studies/regression/phase_c_trajectory_hashes.jl --limit 2
```

Full Julia export:

```text
julia --project=. studies/regression/phase_c_trajectory_hashes.jl
```

Full Python rerun on exported trajectories:

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py run-sindy \
  --config analysis/configs/paper1_phaseC_sindy_baseline.json \
  --trajectory-export-dir outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export \
  --output-data-dir data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export \
  --output-table-dir tables/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export
```

Then compare old and new details:

```text
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py compare-details \
  --reference-details analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv \
  --candidate-details analysis/data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export/details.csv \
  --output analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/detail_delta_summary.csv
```

## Acceptance Points

1. Implemented, not executed here: the export writes raw bytes using the same serialization as the
   Julia hash calculation.
2. Open here: `126 / 126` equality in both hashes requires Claude to run Julia and then Python
   against the generated export.
3. Implemented and tested in Python: missing export aborts; hash mismatch aborts.
4. Open here: the new SINDy run and its old/new difference numbers require the Julia export.
5. Done here: all Python tests passed, `59 passed in 14.60s`.
