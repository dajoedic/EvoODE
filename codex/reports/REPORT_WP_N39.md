# REPORT WP-N39 - PySR GP Baseline

## Implemented

- Added the PySR adapter path to `baselines/harness.py`, including method dispatch for `"pysr"` and package-version capture.
- Added `baselines/run_pysr_noise.py` for the noisy Phase-C exports. It reuses the WP-N34 export index/hash validator, fits on observed data, evaluates clean reconstruction/generalization on the 512-point truth grid, writes `details.csv`, `records.jsonl`, `summary.csv`, `export_checks.csv`, and a comparison join.
- Added `baselines/configs/pysr_faithful.json`, `baselines/requirements-pysr.txt`, and `baselines/Dockerfile.pysr`.
- Added fake-adapter tests for PySR structure expansion, exact-system R2=1, output files, and comparison-join behavior.
- Added frozen decisions and cost formula in `docs/WP-N39.md`.

## Continuation 2026-10-02

- Changed the faithful PySR config to `optimize_hyperparams=true`, `hyper_opt_eval_fraction=0.3`, and `sorting_metric=r2`.
- Added the ODEFormer PySR hyperparameter grid from `pysr_wrapper.py:64-68`: `finite_difference_order in {2,3,4}` x `smoother_window_length in {None,15}`.
- The adapter selects hyperparameters on the held-out fraction of the observed training trajectory and records the selected pair per equation in `pysr_selected_hyperparams`. Clean source/target trajectories are evaluated only after fitting.
- The runner now emits both ODEFormer variants for every cell and seed: `method=pysr` and `method=pysr_poly`; `pysr_poly` has `pysr_unary_operators=[]`.
- Updated `docs/WP-N39.md` A.3 and the cost formula to the `6 hyper-fits x 2 configurations` factor. The old `optimize_hyperparams=false` freeze is retained there as discarded on 2026-10-02.

## Continuation 2 2026-10-02

- Added `baselines/Dockerfile.pysr.dockerignore` with the same allowlist shape as the ODEFormer image-specific ignore files: `baselines/`, `analysis/`, and `benchmarks/data/`, excluding Python bytecode/cache files.
- Updated `baselines/Dockerfile.pysr` so `baselines/requirements-pysr.txt` is visible to BuildKit under the Dockerfile-specific ignore file.
- Added a Docker build-time PySR warm-up step after `pip install`. It imports `pysr`, initializes JuliaCall/JuliaPkg, installs/precompiles the Julia backend into `/opt/pysr-julia`, and writes `/opt/evoode-pysr-image-metadata.json`.
- The metadata file records PySR, Julia, and `SymbolicRegression.jl` versions plus the Julia depot/project paths. `baselines/harness.py` now merges this file into every record's `environment` JSON when present.
- The image sets `PYTHON_JULIAPKG_OFFLINE=yes` and `JULIA_PKG_OFFLINE=true` after the warm-up step so container startup uses the preinstalled backend instead of resolving/downloading at first run.

Source basis:

- PySR upstream README says Julia dependencies are installed at first import and that PySR uses `SymbolicRegression.jl` as its search engine: https://github.com/astroautomata/PySR
- PySR 1.5.9 `pysr/juliapkg.json` pins Julia compatibility to `=1.10.0, 1.10.3` and requests `SymbolicRegression` `~1.11.0`: https://raw.githubusercontent.com/astroautomata/PySR/v1.5.9/pysr/juliapkg.json
- JuliaPkg documents `PYTHON_JULIAPKG_PROJECT` for the Julia project location and `PYTHON_JULIAPKG_OFFLINE=yes` for offline operation without installing Julia/packages: https://github.com/JuliaPy/pyjuliapkg

## Continuation 3 2026-10-03

- Added the legacy PySR image path:
  - `baselines/Dockerfile.pysr-legacy`
  - `baselines/Dockerfile.pysr-legacy.dockerignore`
  - `baselines/requirements-pysr-legacy.txt`
- Pinned the legacy image to `pysr==0.19.4` and `juliacall==0.9.24`. PySR 0.19.4 is the last 0.x release listed before 1.0.0 on PyPI.
- Kept `baselines/Dockerfile.pysr` on `pysr==1.5.9`, and added image API labels:
  - v1 image: `EVOODE_PYSR_API_LABEL=pysr_v1`
  - legacy image: `EVOODE_PYSR_API_LABEL=pysr_legacy_0x`
- Updated `baselines/run_pysr_noise.py` so the default output directory is split by image API label:
  - v1 default: `outputs/wp_n39_noise_pysr_pysr_v1`
  - legacy default: `outputs/wp_n39_noise_pysr_pysr_legacy_0x`
  - explicit `--output-dir` still overrides this behavior.
- Updated `baselines/harness.py` so the adapter detects the installed PySR API family:
  - `legacy_0x`: passes ODEFormer's `PySRRegressor` constructor arguments unchanged, including `equation_file`.
  - `v1`: renames only `equation_file` to `output_directory` plus `run_id`.
- Every PySR record now carries `pysr_api` and `pysr_api_renamed_arguments`.
- Added tests that verify both API argument mappings without importing PySR.
- Updated `docs/WP-N39.md` with:
  - the two-image version rationale,
  - source links for the 0.19.4 choice and the 1.x output rename,
  - the default-difference table for `PySRRegressor` parameters not explicitly set by ODEFormer.

Source basis:

- PyPI `pysr==0.19.4` page lists 0.19.4 as the last 0.x release before 1.0.0 and gives release date 2024-08-23: https://pypi.org/project/pysr/0.19.4/
- PySR 0.19.4 `PySRRegressor.__init__` includes `equation_file`: https://raw.githubusercontent.com/MilesCranmer/PySR/v0.19.4/pysr/sr.py
- PySR 1.0.0 release notes list `equation_file -> output_directory + run_id`: https://github.com/astroautomata/PySR/discussions/755
- PySR 1.5.9 API documents `output_directory` and `run_id`: https://pysr.ai/v1.5.9/api/
- PySR 0.19.4 `juliapkg.json` pins SymbolicRegression.jl `=0.24.5`: https://raw.githubusercontent.com/MilesCranmer/PySR/v0.19.4/pysr/juliapkg.json

## Local Verification

Command:

```text
python -m pytest baselines/tests/test_run_pysr_noise.py baselines/tests/test_run_odeformer_noise.py baselines/tests/test_harness.py -q
```

Result:

```text
63 passed, 5 skipped in 67.07s
```

Additional command:

```text
python -m compileall -q baselines
```

Result: exit code 0.

No PySR run was started.
No Docker build was started.

## Commands for Claude

### 1. Build the PySR 1.5.9 image

Purpose: build the isolated PySR 1.5.9 environment without modifying the existing baseline image.

Command:

```text
docker build -f baselines/Dockerfile.pysr -t evoode-pysr:wp-n39 .
```

Expected duration: image build; includes PySR/Julia artifact download and Julia package precompilation once, during build.

Pass criterion: image builds successfully, contains the pinned packages from `baselines/requirements-pysr.txt`, contains `/opt/evoode-pysr-image-metadata.json`, and has `EVOODE_PYSR_API_LABEL=pysr_v1`.

### 2. Build the PySR 0.19.4 legacy image

Purpose: build the legacy ODEFormer-compatible PySR 0.x environment without modifying the existing baseline image.

Command:

```text
docker build -f baselines/Dockerfile.pysr-legacy -t evoode-pysr-legacy:wp-n39 .
```

Expected duration: image build; includes PySR/Julia artifact download and Julia package precompilation once, during build.

Pass criterion: image builds successfully, contains the pinned packages from `baselines/requirements-pysr-legacy.txt`, contains `/opt/evoode-pysr-image-metadata.json`, and has `EVOODE_PYSR_API_LABEL=pysr_legacy_0x`.

### 3. Smoke PySR 1.5.9 on one exported cell

Purpose: run the allowed one-cell PySR smoke on system 1, sigma 0.01, rho 0, from `outputs/stage1/data_export/index.csv`.

Command:

```text
MSYS_NO_PATHCONV=1 docker run --rm --network none --cpus=1 -v "C:/Users/joedicke/Documents/reps/EvoODE:/workspace/EvoODE" evoode-pysr:wp-n39 --export-index outputs/stage1/data_export/index.csv --output-dir outputs/wp_n39_pysr_v1_smoke_system1_sigma001_rho0 --seeds 1 --limit 1
```

Expected duration: one PySR cell with both variants and all six hyper-fits per equation; this is the measurement that fills `T_cell` in `docs/WP-N39.md`.

Pass criterion: command exits 0 without network at container start and writes `details.csv`, `records.jsonl`, `summary.csv`, `export_checks.csv`, and `comparison_with_external_baselines.csv`; `export_checks.csv` has `hash_verified=True`; `details.csv` contains both `method=pysr` and `method=pysr_poly` rows for system 1 with either `status=success` or recorded error rows; records contain `pysr_api=v1` and `pysr_api_renamed_arguments=["equation_file->output_directory+run_id"]`. Each record's `environment` JSON contains the `pysr_image_*` metadata keys from `/opt/evoode-pysr-image-metadata.json`.

### 4. Smoke PySR 0.19.4 on one exported cell

Purpose: run the allowed one-cell legacy PySR smoke on system 1, sigma 0.01, rho 0, from `outputs/stage1/data_export/index.csv`.

Command:

```text
MSYS_NO_PATHCONV=1 docker run --rm --network none --cpus=1 -v "C:/Users/joedicke/Documents/reps/EvoODE:/workspace/EvoODE" evoode-pysr-legacy:wp-n39 --export-index outputs/stage1/data_export/index.csv --output-dir outputs/wp_n39_pysr_legacy_smoke_system1_sigma001_rho0 --seeds 1 --limit 1
```

Expected duration: one PySR cell with both variants and all six hyper-fits per equation.

Pass criterion: command exits 0 without network at container start and writes `details.csv`, `records.jsonl`, `summary.csv`, `export_checks.csv`, and `comparison_with_external_baselines.csv`; `export_checks.csv` has `hash_verified=True`; `details.csv` contains both `method=pysr` and `method=pysr_poly` rows for system 1 with either `status=success` or recorded error rows; records contain `pysr_api=legacy_0x` and `pysr_api_renamed_arguments=[]`. Each record's `environment` JSON contains the `pysr_image_*` metadata keys from `/opt/evoode-pysr-image-metadata.json`.

### 5. Full PySR 1.5.9 run after smoke approval

Purpose: run the declared full PySR grid only after Claude accepts the smoke.

Command:

```text
MSYS_NO_PATHCONV=1 docker run --rm --network none --cpus=1 -v "C:/Users/joedicke/Documents/reps/EvoODE:/workspace/EvoODE" evoode-pysr:wp-n39 --export-index outputs/stage1/data_export/index.csv --export-index outputs/stage2/data_export/index.csv --export-index outputs/stage3/data_export/index.csv --output-dir outputs/wp_n39_noise_pysr_v1 --seeds 1,2,3
```

Expected duration: `4,536 * T_cell / parallel_cell_count` wall-clock seconds, with `4,536 * T_cell / 3,600` core-hours at one core per cell, where one `T_cell` already includes both PySR variants and the six-point hyperparameter grid.

Pass criterion: command exits 0 and writes all five output files; `export_checks.csv` has all hashes verified; `records.jsonl` has two records per exported cell and seed, one for `pysr` and one for `pysr_poly`; all records carry `pysr_api=v1`.

### 6. Full PySR 0.19.4 run after smoke approval

Purpose: run the declared full legacy PySR grid only after Claude accepts the smoke.

Command:

```text
MSYS_NO_PATHCONV=1 docker run --rm --network none --cpus=1 -v "C:/Users/joedicke/Documents/reps/EvoODE:/workspace/EvoODE" evoode-pysr-legacy:wp-n39 --export-index outputs/stage1/data_export/index.csv --export-index outputs/stage2/data_export/index.csv --export-index outputs/stage3/data_export/index.csv --output-dir outputs/wp_n39_noise_pysr_legacy --seeds 1,2,3
```

Expected duration: `4,536 * T_cell / parallel_cell_count` wall-clock seconds, with `4,536 * T_cell / 3,600` core-hours at one core per cell, where one `T_cell` already includes both PySR variants and the six-point hyperparameter grid.

Pass criterion: command exits 0 and writes all five output files; `export_checks.csv` has all hashes verified; `records.jsonl` has two records per exported cell and seed, one for `pysr` and one for `pysr_poly`; all records carry `pysr_api=legacy_0x`.

## Notes

The smoke commands use `--limit 1`; if Claude needs to guarantee the exact condition before running, filter `outputs/stage1/data_export/index.csv` to system 1, `noise_sigma=0.01`, `subsample_rho=0`, and pass the filtered index instead.
