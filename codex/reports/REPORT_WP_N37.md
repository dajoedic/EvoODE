# REPORT WP-N37

## Summary

Implemented WP-N37 parts A-D without changing `src/` and without starting cluster jobs.

Julia could not be executed in this Codex environment:

```text
julia --version
Program 'julia.exe' failed to run: The file cannot be accessed by the system
```

Therefore the Julia acceptance runs below remain for Claude. This is environment, not subject matter.

## Files

- Added `k8s/phase_c_robustness_stage3_orion_job.yaml`.
- Added `k8s/phase_c_robustness_stage3_uncapped_job.yaml`.
- Added `k8s/phase_c_c8_oracle_b03_job.yaml`.
- Updated `analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py` with `--dims`.
- Added `analysis/scripts/aggregate/aggregate_c8_oracle_bounds.py`.
- Added `analysis/tests/test_aggregate_c8_oracle_bounds.py`.
- Added `studies/regression/print_phase_c_stage_caps.jl`.
- Updated `SCRIPTS.md` with Stage 3 and B-03 workflow using mounted NFS paths.
- Generated `outputs/phase_c_c8_oracle_b03_input/history.jsonl`.
- Generated B-02 aggregation outputs under `outputs/phase_c_c8_oracle_bounds_b02/`.

## Python acceptance run by Codex

Byte identity for the default dim <= 2 path:

```text
python analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py --input outputs/phase_c_campaign_221a3a7/history.jsonl --output outputs/phase_c_c8_oracle_b02_input/codex_bytecheck_history.jsonl
existing sha256  = 029b7b71abeba35074d22b66d91f3115d93f0fc40e61caef36994792d6ba768a
bytecheck sha256 = 029b7b71abeba35074d22b66d91f3115d93f0fc40e61caef36994792d6ba768a
```

The temporary bytecheck file was removed after comparison.

B-03 input:

```text
python analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py --input outputs/phase_c_campaign_221a3a7/history.jsonl --dims 3,4 --output outputs/phase_c_c8_oracle_b03_input/history.jsonl
records=54
systems=9
sha256=e7e902ebec4e522d01ea0f92ddc88373909a326d3aa752dbd06c2dc066b98c2e
```

Tests:

```text
python -m pytest analysis/tests/test_aggregate_c8_oracle_bounds.py -q
2 passed in 0.06s

python -m py_compile analysis/scripts/aggregate/prepare_phasec_b02_oracle_input.py analysis/scripts/aggregate/aggregate_c8_oracle_bounds.py analysis/tests/test_aggregate_c8_oracle_bounds.py
pass
```

B-02 aggregation:

```text
python analysis/scripts/aggregate/aggregate_c8_oracle_bounds.py --bound10 outputs/phase_c_c8_oracle_b02_5dd1df8/bound_10 --bound1000 outputs/phase_c_c8_oracle_b02_5dd1df8/bound_1000 --bound-inf outputs/phase_c_c8_oracle_b02_5dd1df8/bound_Inf --reference-c5 outputs/wp_n3_oracle_refit_phase_c --output-dir outputs/phase_c_c8_oracle_bounds_b02
control=126/126
gate=preliminary, n = 126 of 144
bound=10 n=126 hard_errors=0 penalties=2 median_loss_evals=743.5 r2_gt_0_9=72 comparable_stable=baseline
bound=1000 n=126 hard_errors=0 penalties=2 median_loss_evals=1093 r2_gt_0_9=83 comparable_stable=yes
bound=Inf n=126 hard_errors=0 penalties=2 median_loss_evals=1197 r2_gt_0_9=83 comparable_stable=no
```

Changed fits against bound 10:

```text
bound 1000: changed=86, loss_better=55, loss_worse=31, r2_flips=15
bound Inf:  changed=86, loss_better=54, loss_worse=32, r2_flips=17
```

`outputs/phase_c_c8_oracle_bounds_b02/bound_summary.csv` reports q95 loss evals as 20000.0 for all three bounds and retry rates 0.12698412698412698 / 0.12698412698412698 / 0.14285714285714285.

## Static checks

New manifests contain no `activeDeadlineSeconds` or `timeout` string:

```text
rg -n "activeDeadlineSeconds|timeout" k8s/phase_c_robustness_stage3_orion_job.yaml k8s/phase_c_robustness_stage3_uncapped_job.yaml k8s/phase_c_c8_oracle_b03_job.yaml
no matches
```

`studies/regression/print_phase_c_stage_caps.jl` includes `run_batch_cell.jl` and reuses `_manifest_row`, `_batch_fingerprint`, `_batch_variant`, `_batch_system`, `build_trajectory`, `apply_phase_c_data_condition`, `phase_c_basis`, and `estimate_stage_caps`. It does not call `run_one`, `fit_parameters`, or `search_structure`.

`select_phase_c_stage2_manifest.jl` already had `--variant` and `--condition`; no change was needed, preserving Stage-2 output behavior.

## Commands for Claude

### Teil D: noisy Stage-3 cap precheck

Purpose: decide whether `k8s/phase_c_robustness_stage3_uncapped_job.yaml` is needed.

Expected duration: seconds to minutes; no search or fit.

Pass criterion: System 41 rows print JSON with `stage_caps`; apply the uncapped manifest only if a noisy System 41 cap is finite and below 5.

```powershell
julia --project=. --startup-file=no studies/regression/print_phase_c_stage_caps.jl `
  --manifest S:\BigDataOrion\data-science\joedicke\phase_c_robustness_stage3_<SHA>\manifest.csv `
  --rows 1,2
```

### Teil B: B-03 cost estimate

Purpose: fill the `Expected runtime: TODO(Claude) from --estimate-cost` line in `k8s/phase_c_c8_oracle_b03_job.yaml`.

Expected duration: seconds to minutes; it estimates cost only.

Pass criterion: command prints a cost estimate for 54 cells and exits 0.

```powershell
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl `
  --campaign paper1_phaseC_v1 `
  --input outputs/phase_c_c8_oracle_b03_input/history.jsonl `
  --output-dir outputs/phase_c_c8_oracle_b03_bound10 `
  --clamp-val 10 `
  --estimate-cost
```

### Teil A: Stage-3 smoke

Purpose: verify the Stage-3 image and manifest path before the two System 41 cells.

Expected duration: bootstrap minutes, smoke < 5 min.

Pass criterion: bootstrap writes manifest/index files under `/outputs/phase_c_robustness_stage3_<SHA>`, and the smoke writes `smoke/tasks/cell_000001.jsonl` with `error: null`.

```powershell
(Get-Content k8s\phase_c_robustness_stage3_orion_job.yaml) -replace '<COMMIT_SHA>','<SHA>' | oc apply -f -
oc -n scch-das logs job/evoode-phase-c-robustness-stage3-bootstrap
```

### Teil C after B-03 finishes

Purpose: rerun the Section 9.6 aggregation on B-02 plus B-03.

Expected duration: seconds.

Pass criterion: control passes for all bound-10 rows, gate set becomes `complete, n = 144`, and CSV/Markdown are written.

```bash
python analysis/scripts/aggregate/aggregate_c8_oracle_bounds.py \
  --bound10 outputs/phase_c_c8_oracle_b02_5dd1df8/bound_10 outputs/phase_c_c8_oracle_b03_<SHA>/bound_10 \
  --bound1000 outputs/phase_c_c8_oracle_b02_5dd1df8/bound_1000 outputs/phase_c_c8_oracle_b03_<SHA>/bound_1000 \
  --bound-inf outputs/phase_c_c8_oracle_b02_5dd1df8/bound_Inf outputs/phase_c_c8_oracle_b03_<SHA>/bound_Inf \
  --reference-c5 outputs/wp_n3_oracle_refit_phase_c \
  --output-dir outputs/phase_c_c8_oracle_bounds_<SHA>
```
