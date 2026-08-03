# REPORT WP-B2

## Fingerprint

- New `config_fingerprint`: `256014cf6f0295e1`
- Previous WP-B1 fingerprint: `fa2469a4dad1b72c`
- Changed intentionally because the fingerprint payload now describes the actual sampling source as `dataset solutions[1][1].t grid; shipped y ignored`.

## Batch Artifacts

- Manifest generator: `studies/regression/generate_manifest.jl`
- Single-cell entry point: `studies/regression/run_batch_cell.jl`
- Merge step: `studies/regression/merge_batch_records.jl`
- Container definition: `containers/evoode_regression.apptainer`
- Slurm example: `hpc/slurm_regression_array.sh`

## Manifest Verification

- Manifest path: `outputs/studies/regression/wp_b2/manifest.csv`
- Rows: `120` (`5 systems * 2 initial-condition sets * 3 seeds * 4 VARIANTS`)
- Regeneration check: `outputs/studies/regression/wp_b2/manifest.csv` and `outputs/studies/regression/wp_b2/manifest_regen.csv` were byte-identical.
- Resolved index `1`: `evogrow_v2_2_stage_local`, system `3`, dim `1`, IC set `1`, seed `42`.
- Resolved index `2`: `evogrow_v2_2_stage_local`, system `3`, dim `1`, IC set `1`, seed `123`.
- Resolved last index `120`: `evogrow_v3_stage_capped`, system `63`, dim `4`, IC set `2`, seed `7`.

## Dimension Classes

I kept one global manifest and emit per-dimension index-list files with `--dimension DIM --index-output PATH`.
This keeps the campaign identity and ordering in one CSV while letting Slurm arrays have separate walltime limits per dimension class.

- `indices_dim1.txt`: `48` cells
- `indices_dim2.txt`: `48` cells
- `indices_dim4.txt`: `24` cells
- There are no 3D systems in the current regression suite.

## Single-Cell Batch Run

- Command path: `studies/regression/run_batch_cell.jl`
- Manifest index: `61`
- Output file: `outputs/studies/regression/wp_b2/tasks/cell_000061.jsonl`
- Process exit code: `0`
- Variant: `evogrow_v2_2_stage_capped`
- System: `3`
- Initial-condition set: `1`
- Seed: `42`
- Loss: `5.18873247985214e-9`
- Cap: `[2]`
- `eq_overshoot`: `[0]`
- `pruned_match`: `true`
- Support: `[["u1","u1^2"]]`

This reproduces the WP-B1 cell result exactly.

## Fingerprint Guard

An intentionally corrupted manifest at `outputs/studies/regression/wp_b2/manifest_bad_fingerprint.csv` was rejected before running a cell.

- Process exit code: `1`
- Error included: `Fingerprint mismatch ... manifest=badfingerprint000, runtime=256014cf6f0295e1`
- No task output file was produced under `outputs/studies/regression/wp_b2/tasks_bad/`.

## Merge Verification

Merged the single task record into a scratch copy, not into `studies/regression/history.jsonl`.

- Scratch history path: `outputs/studies/regression/wp_b2/scratch_history.jsonl`
- Original copied line count: `42`
- First merge: `considered=1`, `added=1`, `skipped_duplicates=0`
- Second merge: `considered=1`, `added=0`, `skipped_duplicates=1`
- Final scratch line count: `43`

## Container Check

The Apptainer definition is present and statically checked for the required structure:

- base image pins Julia as `julia:1.11.5-bookworm`
- `Project.toml` and `Manifest.toml` are copied before build-time `Pkg.instantiate()` and `Pkg.precompile()`
- `JULIA_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` are set
- depot is inside the image at `/opt/julia_depot`
- repository code and dataset are copied into `/opt/EvoODE`
- runtime outputs are expected through a bind-mounted `/outputs`

The container was not built here because this Windows environment has no Apptainer/Singularity runtime. Slurm execution was likewise not tested here.
