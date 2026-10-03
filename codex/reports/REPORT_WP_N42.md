# REPORT WP-N42

## Result

Implemented, but not Julia-executed in the Codex sandbox.

Environment blocker: `julia --version` fails before project code starts with
`Program 'julia.exe' failed to run: The file cannot be accessed by the system`.
Python checks ran.

## Files changed

- `studies/regression/generate_phase_c_manifest.jl`
  - Added `--c6-grid`.
  - Writes 3,366 capped C-6 rows for dim-1/2 systems only.
  - Uses `PHASE_C_SEEDS` by index: seed index `r` gets `noise_realization = r`.
  - Writes `indices_all.txt` and `indices_cost_desc.txt`.
- `studies/regression/print_phase_c_stage_caps.jl`
  - Added `--all-rows`, `--output-csv`, `--uncapped-manifest-output`, and
    `--uncapped-index-output`.
  - CSV columns: `index,system_id,initial_condition_set,seed,noise_sigma,subsample_rho,noise_realization,stage_caps,has_finite_cap_lt5`.
  - Writes a selected uncapped manifest with `variant = evogrow_v2_2_stage_local` and
    `condition = uncapped`.
- `studies/regression/export_phase_c_data_conditions.jl`
  - Added `--c6-grid` for 63 systems x 2 IC x 12 conditions x 3 realizations.
- `analysis/scripts/aggregate/compare_phasec_c6_control.py`
  - Compares the C-6 control row/record against the Stage-1 reference on manifest payload,
    `config_fingerprint`, `data_condition_fingerprint`, and `observed_data_sha256`.
- `test/test_wp_n42_c6_grid.jl`
  - Tests C-6 row count, dim scope, 11-condition scope, r-to-seed coupling, and the Stage-1
    control manifest row.
- `k8s/phase_c_c6_grid_job.yaml`
  - Two indexed jobs, capped and selected uncapped, no bootstrap, no active deadline.
- `SCRIPTS.md`
  - Added C-6 full-grid operating commands.

## Static checks

- Confirmed the data stream seed in `studies/regression/phase_c_data_condition.jl` depends on
  `(system_id, ic_set, sigma, rho, noise_realization, stream)` and not on EvoGrow seed.
- Confirmed the C-6 grid control row index is `2`: system 1, IC 1, first seed, sigma `0.01`, rho `0`,
  realization `1`.
- Confirmed `k8s/phase_c_c6_grid_job.yaml` has no `activeDeadlineSeconds`.
- Python syntax:

```powershell
python -m py_compile analysis/scripts/aggregate/compare_phasec_c6_control.py
```

Pass criterion: exit code 0. Observed in Codex: pass.

- Python control checker self-check on the existing Stage-1 reference:

```powershell
python analysis/scripts/aggregate/compare_phasec_c6_control.py `
  --grid-manifest outputs/stage1/s0.01_r0/manifest.csv `
  --grid-index 1 `
  --grid-record outputs/stage1/s0.01_r0/tasks/cell_000001.jsonl
```

Pass criterion: prints that manifest row, config fingerprint, data fingerprint and observed data
hash match. Observed in Codex: pass.

## Commands for Claude

### 1. Generate capped C-6 manifest

Purpose: create the full capped C-6 EvoGrow grid and cost-descending index list.

Expected duration: under 1 minute.

```powershell
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl `
  --c6-grid `
  --output outputs\phase_c_c6_grid_<SHA>\manifest.csv
```

Pass criteria:

- `rows=3366`
- `c6_systems=51`
- `c6_conditions=11`
- `c6_realizations=1,2,3`
- `outputs\phase_c_c6_grid_<SHA>\indices_cost_desc.txt` has 3,366 lines.

Short smoke before the full manifest, if desired:

```powershell
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl `
  --c6-grid `
  --limit 12 `
  --output outputs\phase_c_c6_grid_smoke\manifest.csv
```

### 2. Run Julia tests

Purpose: verify row counts, r-to-seed coupling, and the Stage-1 manifest control row.

Expected duration: under 2 minutes.

```powershell
julia --project=. --startup-file=no test/test_wp_n42_c6_grid.jl
```

Pass criterion: all tests pass.

### 3. Run local control cell

Purpose: verify that the grid row for system 1, IC 1, seed index 1, sigma `0.01`, rho `0` is the
same data condition as the Stage-1 cell.

Expected duration: about the Stage-1 cell runtime, previously about 1 minute.

```powershell
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl `
  --manifest outputs\phase_c_c6_grid_<SHA>\manifest.csv `
  --output-dir outputs\phase_c_c6_grid_<SHA>\control `
  2

python analysis/scripts/aggregate/compare_phasec_c6_control.py `
  --grid-manifest outputs\phase_c_c6_grid_<SHA>\manifest.csv `
  --grid-index 2 `
  --grid-record outputs\phase_c_c6_grid_<SHA>\control\cell_000002.jsonl
```

Pass criterion: Python prints that the manifest row, config fingerprint, data fingerprint and
observed data hash match Stage 1.

### 4. Cap precheck and uncapped manifest

Purpose: estimate caps without search for all 3,366 capped grid cells and select the uncapped arm.

Expected duration: search-free but all cells; likely minutes to tens of minutes locally. Stop and
move to a controlled environment if it exceeds the 15-minute Codex-style bound.

```powershell
julia --project=. --startup-file=no studies/regression/print_phase_c_stage_caps.jl `
  --manifest outputs\phase_c_c6_grid_<SHA>\manifest.csv `
  --all-rows `
  --output-csv outputs\phase_c_c6_grid_<SHA>\stage_caps.csv `
  --uncapped-manifest-output outputs\phase_c_c6_grid_uncapped_<SHA>\manifest.csv `
  --uncapped-index-output outputs\phase_c_c6_grid_uncapped_<SHA>\indices_cost_desc.txt
```

Pass criteria:

- `output_csv_rows=3366`
- `uncapped_rows=<N_UNCAPPED_ROWS>`
- `outputs\phase_c_c6_grid_uncapped_<SHA>\indices_cost_desc.txt` has `<N_UNCAPPED_ROWS>` lines.
- Every uncapped manifest row has `variant=evogrow_v2_2_stage_local` and `condition=uncapped`.

### 5. Export baseline data

Purpose: export shared data for SINDy, Weak-SINDy and ODEFormer.

Expected duration: minutes. Size estimate: 4,536 trajectory exports, about 0.05 GiB raw arrays plus
CSV/file overhead; keep C: above 30 GB free before running.

```powershell
julia --project=. --startup-file=no studies/regression/export_phase_c_data_conditions.jl `
  --c6-grid `
  --output-dir outputs\phase_c_c6_data_conditions_<SHA>
```

Pass criteria:

- `rows=4536`
- `outputs\phase_c_c6_data_conditions_<SHA>\index.csv` has 4,536 data rows.
- Conditions include `(0,0)` and the 11 noisy/subsampled grid conditions.

### 6. Upload to Orion NFS

Purpose: place manifests and data where the Orion jobs expect them.

Expected duration: minutes; data copy is small for the export, manifests are tiny.

```powershell
New-Item -ItemType Directory -Force -Path `
  S:\BigDataOrion\data-science\joedicke\phase_c_c6_grid_<SHA>, `
  S:\BigDataOrion\data-science\joedicke\phase_c_c6_grid_uncapped_<SHA>, `
  S:\BigDataOrion\data-science\joedicke\phase_c_c6_data_conditions_<SHA>

Copy-Item outputs\phase_c_c6_grid_<SHA>\manifest.csv,outputs\phase_c_c6_grid_<SHA>\indices_cost_desc.txt `
  S:\BigDataOrion\data-science\joedicke\phase_c_c6_grid_<SHA>\
Copy-Item outputs\phase_c_c6_grid_uncapped_<SHA>\manifest.csv,outputs\phase_c_c6_grid_uncapped_<SHA>\indices_cost_desc.txt `
  S:\BigDataOrion\data-science\joedicke\phase_c_c6_grid_uncapped_<SHA>\
Copy-Item -Recurse outputs\phase_c_c6_data_conditions_<SHA>\* `
  S:\BigDataOrion\data-science\joedicke\phase_c_c6_data_conditions_<SHA>\
```

Pass criterion: all copied files/directories are visible under the NFS paths.

### 7. Apply Orion jobs

Purpose: run capped and selected uncapped C-6 arms as indexed jobs.

Expected duration: cost model is 25.4k-35.1k core hours for the capped grid. Some cells may exceed
24 h and are intentionally not cut.

```powershell
(Get-Content k8s\phase_c_c6_grid_job.yaml) `
  -replace '<COMMIT_SHA>','<SHA>' `
  -replace '<UNCAPPED_COMPLETIONS>','<N_UNCAPPED_ROWS>' `
  -replace '<PARALLELISM>','<PARALLELISM>' | oc apply -f -
```

Pass criteria:

- Both jobs are accepted by the API.
- Capped job has `completions: 3366`.
- Uncapped job has `completions: <N_UNCAPPED_ROWS>`.
- No `activeDeadlineSeconds` is present.

### 8. Progress

Purpose: watch capped and uncapped indexed jobs.

Expected duration: seconds per query.

```powershell
oc -n scch-das get jobs,pods -l hpc.scch.at/service=evoode-phase-c-c6-grid
oc -n scch-das get jobs,pods -l hpc.scch.at/service=evoode-phase-c-c6-grid-uncapped
```

Pass criterion: completed pod count rises; failed infrastructure pods are visible for retry/debug.

### 9. Collect

Purpose: copy records back for aggregation.

Expected duration: depends on record volume; use direct NFS copy when available.

```powershell
New-Item -ItemType Directory -Force outputs\phase_c_c6_grid_<SHA>,outputs\phase_c_c6_grid_uncapped_<SHA>
Copy-Item -Recurse S:\BigDataOrion\data-science\joedicke\phase_c_c6_grid_<SHA>\tasks `
  outputs\phase_c_c6_grid_<SHA>\
Copy-Item -Recurse S:\BigDataOrion\data-science\joedicke\phase_c_c6_grid_uncapped_<SHA>\tasks `
  outputs\phase_c_c6_grid_uncapped_<SHA>\
```

Pass criterion: capped task count is 3,366 and uncapped task count is `<N_UNCAPPED_ROWS>`, excluding
heartbeat files.
