# WP-N33a3 Report

## Changes

- Froze `analysis/tests/test_robustness_stage_report.py` fixtures that previously read from:
  - `outputs/wp_n32_stage0/tasks/cell_000001.jsonl`
  - `outputs/stage1/s0.01_r0/tasks/cell_000001.jsonl`
  - `outputs/phase_c_campaign_221a3a7/tasks/cell_000001.jsonl`
  - `outputs/stage1/data_export/index.csv`
- Added a literal pre-WP-N33a2 broken stage-1 CSV header and row 2. The frozen row has 26 parsed CSV fields against 25 header columns because `state_shape` is `[512,1]` without quotes.
- Replaced real heartbeat-file reads in the touched tests with minimal heartbeat literals.
- Froze `analysis/tests/test_compare_phasec_controls.py::test_compare_phasec_controls_skips_heartbeats_in_directory_input` to use the existing in-test `record()` fixture instead of `outputs/wp_n32_stage0` and `outputs/phase_c_campaign_221a3a7`.

## Outputs-read scan

`rg -n "outputs" analysis/tests` still finds older tests that intentionally validate checked-in or generated reference artifacts outside this WP:

- `test_phasec_structure_metrics_n26.py`: reads `outputs/phase_c_dryrun_2026-09-25/run_registry.csv`.
- `test_phasec_p9_pilot.py`: reads `outputs/studies/regression/phase_c/smoke_tasks/cell_000001.jsonl`.
- `test_variance_weighted_r2.py`: reads `outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export`.
- `test_phasec_sindy_baseline.py`: reads `outputs/phase_c_p9_pilot_records` indirectly through `PILOT_DIR`; its WP-N6 comparisons use promoted `analysis/data` and `analysis/tables` artifacts.
- `test_wp_t1c_prior_generator.py`: reads `outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export`.

I did not change those because they are not derived from the repaired stage-1 export index and are not part of the failing quoting fixture. The direct `outputs/` reads in the two acceptance test files are gone.

## Acceptance

Command run with `TMP` and `TEMP` redirected to `.pytest_tmp` inside the workspace because the default `C:\Users\joedicke\AppData\Local\Temp\pytest-of-joedicke` is not readable in this session:

```text
python -m pytest analysis/tests/test_robustness_stage_report.py analysis/tests/test_compare_phasec_controls.py -q
```

Result:

```text
9 passed in 1.41s
```
