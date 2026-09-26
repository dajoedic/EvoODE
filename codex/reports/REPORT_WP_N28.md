# WP-N28 Report

## Changed files

- `analysis/scripts/aggregate/build_phasec_analysis_registry.py`
- `analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py`
- `analysis/scripts/aggregate/run_phasec_sindy_baseline.py`
- `analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py`
- `analysis/configs/paper1_phaseB_v1.json`
- `analysis/configs/paper1_phaseC_v1.json`
- `analysis/tests/test_phasec_analysis_registry.py`
- `analysis/tests/test_phasec_cap_ablation.py`
- `analysis/tests/test_phasec_sindy_baseline.py`
- `analysis/tests/test_pretuning_distribution_collapse.py`
- `SCRIPTS.md`
- `docs/paper1_phaseC_benchmark_plan.md`

## Implementation notes

- Added `build_phasec_analysis_registry.py`, which joins the verified campaign registry and cell-level structure metrics 1:1 by `run_id`, aborting on missing or duplicate metric rows.
- Unsuffixed `structural_f1`, `term_precision`, and `term_recall` are populated from the `_micro` columns. The `_micro` and `_macro` columns remain beside them.
- The builder writes:
  - `phasec_analysis_registry.csv`
  - `phasec_analysis_registry_c1_c2.csv`
  - `phasec_analysis_registry_c1.csv`
  - `phasec_analysis_registry_pretuning.csv`
  - `phasec_analysis_registry_metadata.json`
- Subsets use both `variant_slug` and `use_pretuning`.
- Cap ablation now allows surrogate blanks for truth-only metrics and computes structure/coefficient quality deltas on exact pairs only. Cost metrics and R2 still use all complete pairs.
- SINDy pairing now filters EvoGrow records to Claim-D C-1 only: `variant_slug == evogrow_v2_2_stage_capped` and `use_pretuning == false`.
- Pretuning collapse now reads the pretune-on/off mapping from config. Phase-B config preserves the old mapping; Phase-C config maps C-3 to on and C-1 to off.
- `--allow-incomplete` was added to the Phase-C consumers for the dry-run registry only. Without it, missing C-1/C-2, C-1/SINDy, or C-1/C-3 cells still abort.

## Probe-chain commands and counts

```powershell
python analysis/scripts/aggregate/build_phasec_analysis_registry.py --campaign paper1_phaseC_v1 --registry outputs/phase_c_dryrun_2026-09-25/run_registry.csv --structure-metrics outputs/phase_c_dryrun_2026-09-25/agg/structure_n26/phasec_structure_metrics_by_cell.csv --output outputs/phase_c_dryrun_2026-09-25/agg_n28/phasec_analysis_registry.csv --allow-incomplete
```

Counts from `phasec_analysis_registry_metadata.json`:

- analysis registry: 885 / 936
- C-1: 361 / 378
- C-1/C-2: 713 / 756
- pretuning subset: 347 / 360

```powershell
python analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py --campaign paper1_phaseC_v1 --input outputs/phase_c_dryrun_2026-09-25/agg_n28/phasec_analysis_registry_c1_c2.csv --output-dir outputs/phase_c_dryrun_2026-09-25/agg_n28/cap_ablation --expected-total-pairs 378 --allow-incomplete --permutations 99 --bootstrap-replicates 99
```

Counts from `phasec_cap_ablation_summary.json`:

- complete pairs: 352 / 378
- exact quality pairs: 173
- surrogate pairs: 179
- systems: 63

```powershell
python analysis/scripts/aggregate/run_phasec_sindy_baseline.py pair --sindy-details analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/details.csv --evogrow-records-dir outputs/phase_c_dryrun_2026-09-25/tasks --output outputs/phase_c_dryrun_2026-09-25/agg_n28/phasec_sindy_paired.csv --summary-output outputs/phase_c_dryrun_2026-09-25/agg_n28/phasec_sindy_paired_summary.csv --allow-incomplete
```

Counts from outputs:

- paired rows: 1167
- summary rows: 191

```powershell
python analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py --campaign paper1_phaseC_v1 --config analysis/configs/paper1_phaseC_v1.json --expected-total-pairs 180 --expected-exact-pairs 180 --expected-surrogate-pairs 0 --expected-collapse-groups-per-condition 60 --allow-incomplete
```

Counts from `pretuning_distribution_collapse.json`:

- complete pairs: 168 / 180
- exact pairs: 168
- surrogate pairs: 0
- seed-collapse groups: pretune_off 57, pretune_on 55

## Tests

```powershell
python -m py_compile analysis/scripts/aggregate/build_phasec_analysis_registry.py analysis/scripts/aggregate/aggregate_phasec_cap_ablation.py analysis/scripts/aggregate/run_phasec_sindy_baseline.py analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py
python -m pytest --basetemp .pytest_tmp_n28 analysis/tests/test_phasec_analysis_registry.py analysis/tests/test_phasec_cap_ablation.py analysis/tests/test_phasec_sindy_baseline.py analysis/tests/test_pretuning_distribution_collapse.py
```

Result: 27 passed.

Phase-B bit-equivalence check:

```powershell
python analysis/scripts/aggregate/analyze_pretuning_distribution_collapse.py --campaign paper1_phaseB_v1 --config analysis/configs/paper1_phaseB_v1.json --output outputs/phase_c_dryrun_2026-09-25/agg_n28/phaseb_pretuning_distribution_collapse_bitcheck.json
python -c "from pathlib import Path; ref=Path('analysis/data/paper1_phaseB_v1/pretuning_distribution_collapse.json'); cand=Path('outputs/phase_c_dryrun_2026-09-25/agg_n28/phaseb_pretuning_distribution_collapse_bitcheck.json'); print(ref.read_bytes()==cand.read_bytes())"
```

Result: `True`; both files are 26748 bytes.

## Not verified

- No full-campaign Phase-C run was available; all chain runs used the incomplete 885-row dry-run registry with explicit incomplete mode.
- The first pytest attempt without `--basetemp` failed before test execution on `PermissionError` for `C:\Users\joedicke\AppData\Local\Temp\pytest-of-joedicke`; rerun with repo-local `--basetemp` passed.
- Cleanup of `.pytest_tmp_n28` was attempted after the passing tests, but the command was blocked by policy; the directory may remain as a local test artifact.
