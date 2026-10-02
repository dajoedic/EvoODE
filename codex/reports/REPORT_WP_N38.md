# WP-N38 Report

## Implemented

- Added `baselines/run_odeformer_noise.py`.
- Added the ODEFormer control comparison used by `baselines/run_odeformer_noise.py`:
  comparison keys include `odeformer_config_id`, the noise control only requires candidate keys to
  be present in the reference, and a candidate may match any reference repetition with the same
  system, fit IC, generalization IC, and config. The legacy
  `baselines/compare_odeformer_equivalence.py` remains byte-identical to HEAD.
- Reused WP-N34 export-index validation and byte hash checks from
  `analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py`.
- Reused the ODEFormer reference harness and grid configuration path:
  `baselines/harness.py`, `baselines/run_odeformer_grid.py`, and
  `baselines/configs/odeformer_grid.json`.
- Added `baselines/tests/test_run_odeformer_noise.py`.

## Runner behavior

The runner reads one or more noisy export `index.csv` files and writes:

- `outputs/wp_n38_noise_odeformer/details.csv`
- `outputs/wp_n38_noise_odeformer/records.jsonl`
- `outputs/wp_n38_noise_odeformer/summary.csv`
- `outputs/wp_n38_noise_odeformer/export_checks.csv`
- `outputs/wp_n38_noise_odeformer/comparison_with_robustness_stage_report.csv`

Each detail record includes the observed `time_sha256` and `state_sha256`, the JSON combined
`observed_data_sha256`, ODEFormer config fields, repetition id, expression fields, status, clean
reconstruction and generalization R2 metrics, structure metrics for exact systems, support metadata,
and code-origin fields (`code_origin_path`, `code_origin_git_hash`).

ODEFormer receives the corrupted observed `(t, x)` directly. There is no interpolation path in the
runner. Irregular time grids are passed as stored in the export index.

Source behavior for times:

- `baselines/harness.py` calls `self.model.fit(fit_cell.time, fit_cell.state, ...)`.
- `outputs/third_party/odeformer/odeformer/model/sklearn_wrapper.py` rescales the provided `time`,
  then applies one common random permutation to scaled time and trajectory.
- `outputs/third_party/odeformer/odeformer/model/mixins.py` sorts `times` before integrating and
  unsorts the result afterward.

This means ODEFormer consumes the supplied time vector; it does not require uniform spacing in the
wrapper path used here.

## Tests run

```text
pytest baselines/tests/test_run_odeformer_noise.py -q
8 passed in 5.27s
```

```text
python -m pytest baselines/tests/test_run_odeformer_noise.py -q
8 passed in 11.48s
```

```text
python -m pytest baselines/tests -q
49 passed, 5 skipped in 23.26s
```

```text
python -m pytest baselines/tests/test_harness.py -q
41 passed, 5 skipped in 12.47s
```

```text
python -m py_compile baselines/compare_odeformer_equivalence.py baselines/run_odeformer_noise.py baselines/tests/test_run_odeformer_noise.py
passed
```

```text
python -m baselines.run_odeformer_noise --help
passed
```

No local ODEFormer scientific run was started. The tests use a fake adapter for the ODEFormer call
boundary and real exported bytes for index/hash validation.

## Legacy equivalence comparison impact

`baselines/compare_odeformer_equivalence.py` is unchanged from HEAD. Its key is still
`system_id`, `fit_initial_condition_set`, and `generalization_initial_condition_set`, so a
four-config grid is collapsed from 504 records to 126 keys. The bug is not repaired there because
older reports cite that script's outputs.

Known outputs and reports:

- WP-N21 introduced `baselines/compare_odeformer_equivalence.py` and wrote
  `outputs/wp_n21_equivalence/comparison.json`. The comparison JSON contains
  `reference_record_count = 6`, `candidate_record_count = 6`, `finding_count = 34`, and
  `passed = false`.
- `analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke/records.jsonl`, the
  WP-N21 smoke dataset, has 12 total records: 6 ODEFormer records and 6 SINDy records. The 6
  ODEFormer records cover 6 cells with exactly 1 `odeformer_config_id` per cell. Therefore the
  missing-config key was ineffective for WP-N21's equivalence comparison.
- WP-N23/WP-N24 reports cite the four-configuration ODEFormer grid records under
  `analysis/data/paper1_phaseC_v1/odeformer_baseline/`. Those full-grid record sets each have
  126 cells and 4 configurations per cell, so the legacy comparison would collapse them if used
  directly.
- WP-N27 and WP-N29 grid rates do not run through
  `baselines/compare_odeformer_equivalence.py`. They use `baselines/summarize_odeformer_grid.py`,
  whose summary groups by `odeformer_environment_id`, `odeformer_config_id`, and `dimension`, and
  whose expression pairing uses `odeformer_config_id`, `system_id`,
  `fit_initial_condition_set`, and `generalization_initial_condition_set`.

Measured record/config counts:

| Dataset | Records | Cells | Configs per cell | Repetitions per cell-config |
|---|---:|---:|---:|---:|
| `phasec_external_baselines_wp_n19_smoke/records.jsonl` | 12 | 6 | 1 | n/a |
| `reference_wp_n23/records.jsonl` | 504 | 126 | 4 | n/a |
| `candidate_wp_n23/records.jsonl` | 504 | 126 | 4 | n/a |
| `reference_orion_55e9c75/records.jsonl` | 1512 | 126 | 4 | 3 |
| `candidate_orion_8e0e699/records.jsonl` | 1512 | 126 | 4 | 3 |
| `reference/records.jsonl` | 504 | 126 | 4 | n/a |
| `candidate/records.jsonl` | 504 | 126 | 4 | n/a |

Claude's control table for the legacy-vs-new behavior:

| Pair | old: Records / Findings | new: Records / Findings |
|---|---:|---:|
| `reference_wp_n23` / `candidate_wp_n23` | 126 / 615 | 504 / 2685 |
| `reference_orion_55e9c75` / `candidate_orion_8e0e699` | 126 / 617 | 504 (raw 1512) / 8079 |
| `reference` / `candidate` | 126 / 615 | 504 / 2687 |

## Docker commands for Claude

Use the local reference image from Claude's control:

```bash
docker image inspect evoode/odeformer-reference:wp-n27c
```

Purpose: confirm the local ODEFormer reference environment exists. Expected duration: seconds. Pass
criterion: the image metadata is visible.

Control run, one clean System 1 IC1 cell and one config:

```bash
MSYS_NO_PATHCONV=1 \
docker run --rm \
  --entrypoint python \
  --cpus=1 \
  -e OMP_NUM_THREADS=1 \
  -e MKL_NUM_THREADS=1 \
  -e OPENBLAS_NUM_THREADS=1 \
  -e ODEFORMER_TORCH_THREADS=1 \
  -v "C:/Users/joedicke/Documents/reps/EvoODE:/workspace/EvoODE" \
  -w /workspace/EvoODE \
  evoode/odeformer-reference:wp-n27c \
  -m baselines.run_odeformer_noise \
    --export-index outputs/wp_n34_control_export/index.csv \
    --output-dir outputs/wp_n38_noise_odeformer/control_system1_beam10_noopt \
    --repetitions 1 \
    --config-ids beam10_noopt \
    --limit 1 \
    --control-reference analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records.jsonl
```

Purpose: hard acceptance control against the reference-grid record for the same cell and config.
Expected duration: one ODEFormer cell. Pass criterion: command exits 0 and writes
`control_equivalence.json` with `"passed": true`.

Full stage-cell run:

```bash
MSYS_NO_PATHCONV=1 \
docker run --rm \
  --entrypoint python \
  --cpus=1 \
  -e OMP_NUM_THREADS=1 \
  -e MKL_NUM_THREADS=1 \
  -e OPENBLAS_NUM_THREADS=1 \
  -e ODEFORMER_TORCH_THREADS=1 \
  -v "C:/Users/joedicke/Documents/reps/EvoODE:/workspace/EvoODE" \
  -w /workspace/EvoODE \
  evoode/odeformer-reference:wp-n27c \
  -m baselines.run_odeformer_noise \
    --export-index outputs/stage1/data_export/index.csv \
    --export-index outputs/stage2/data_export/index.csv \
    --export-index outputs/stage3/data_export/index.csv \
    --output-dir outputs/wp_n38_noise_odeformer \
    --repetitions 3
```

Purpose: run all exported stage-index rows through the four ODEFormer configs and three repetitions.
Expected duration: long ODEFormer run, to be started by Claude, not Codex. Pass criterion: command
exits 0, `export_checks.csv` has all `hash_verified = True`, and `details.csv` contains
`row_count = index rows x 4 configs x 3 repetitions`.

Comparison table regeneration only, if needed after adding/moving source reports:

```bash
MSYS_NO_PATHCONV=1 \
docker run --rm \
  --entrypoint python \
  --cpus=1 \
  -e OMP_NUM_THREADS=1 \
  -e MKL_NUM_THREADS=1 \
  -e OPENBLAS_NUM_THREADS=1 \
  -e ODEFORMER_TORCH_THREADS=1 \
  -v "C:/Users/joedicke/Documents/reps/EvoODE:/workspace/EvoODE" \
  -w /workspace/EvoODE \
  evoode/odeformer-reference:wp-n27c \
  -m baselines.run_odeformer_noise \
    --export-index outputs/stage1/data_export/index.csv \
    --export-index outputs/stage2/data_export/index.csv \
    --export-index outputs/stage3/data_export/index.csv \
    --output-dir outputs/wp_n38_noise_odeformer \
    --repetitions 3 \
    --stage-report outputs/phase_c_robustness_stage2_5dd1df8/robustness_stage_report/ \
    --stage-report "outputs/stage1/*/report/" \
    --stage-report "outputs/stage2/*/report/" \
    --sindy-details outputs/stage2/baselines/details.csv \
    --sindy-details outputs/wp_n34_noise_sindy_baselines/details.csv
```

Purpose: make the joint EvoGrow/SINDy/Weak-SINDy/ODEFormer comparison CSV with explicit `missing`
source markers. Expected duration: same as full run if records do not already exist; run only when
needed. Pass criterion: `comparison_with_robustness_stage_report.csv` exists and source-path columns
show matched paths or `missing`.

## Open in this environment

The Docker ODEFormer control and full stage run were not executed in this Codex session. Code and
Python tests are complete; Docker acceptance remains for Claude.
