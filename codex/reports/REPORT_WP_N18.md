# WP-N18 Report - P9 Pilot and Go Criterion

## Scope

Implemented the P9 pilot selection, the Kubernetes pilot job manifest, and an executable
Python go-criterion checker. No Smoke, Pilot, campaign, Julia, or cluster job was started.

The Julia generator was edited but not executed in this environment. This is an environment
blocker for Julia execution, not a subject-matter blocker; Claude must run the generator and the
WP-N5 reconstruction probe.

## Frozen Pilot Selection

Rule: cheapest exact Phase-B system per dimension class under the canonical support table, crossed
with C-1/C-2, one seed, and both IC sets.

I encoded the derived systems as a documented constant in `studies/regression/generate_phase_c_manifest.jl`:

| Dimension | System |
|---:|---:|
| 1 | 2 |
| 2 | 24 |
| 3 | 52 |
| 4 | 63 |

Seed: `42`.

Expected cells: `4 systems x 2 conditions x 1 seed x 2 IC sets = 16`.

Expected manifest indices under the current Phase-C row order:

```text
13
14
19
20
277
278
283
284
613
614
619
620
745
746
751
752
```

I used a documented constant rather than reading `experiments/paper1_phaseB_v1/run_registry.csv`
at generator runtime. Rationale: the pilot selection is now frozen, and the start manifest should
not depend on an analysis artifact being present and unchanged on the cluster. The drift risk is
contained by naming the rule, systems, and seed here and in code.

## Files Changed

- `studies/regression/generate_phase_c_manifest.jl`
  - Adds `PHASE_C_P9_PILOT_SYSTEM_IDS = {2, 24, 52, 63}` and `PHASE_C_P9_PILOT_SEED = 42`.
  - Writes `indices_p9_pilot_c1_c2.txt` when called with `--all-dimensions`.
- `k8s/phase_c_p9_pilot_job.yaml`
  - Indexed Job with `completions: 16`.
  - Reads `/outputs/phase_c_campaign_<COMMIT_SHA>/indices_p9_pilot_c1_c2.txt`.
  - Writes to `/outputs/phase_c_p9_pilot_<COMMIT_SHA>/tasks`, separate from campaign `tasks/`.
- `analysis/scripts/aggregate/verify_phasec_p9_pilot.py`
  - Checks all five go criteria with non-zero exit on failure.
- `analysis/tests/test_phasec_p9_pilot.py`
  - Covers one success case and one exit-code failure case for each criterion.

## Field-Origin Check Against Smoke Record

Checked against `outputs/studies/regression/phase_c/smoke_tasks/cell_000001.jsonl`.

| Plan field | Actual record field | Exists in smoke record | Non-null in smoke record | Origin note |
|---|---|---:|---:|---|
| raw support | `exact_support_match_raw` | yes | yes | Julia cell record |
| thinned/pruned hit | `exact_support_match_pruned` | yes | yes | Julia cell record |
| coefficients | `model_terms[*][*].coefficient` | yes | yes | Julia cell record, nested under `model_terms` |
| `basis_name` | `basis_name` | yes | yes | Julia cell record |
| support definition marker | `exact_support_match_definition` | yes | yes | Julia cell record |
| duplicate counter | `duplicate_candidate_structure_evaluations` | yes | yes | Julia cell record |
| restart counter | `total_parameter_fit_attempts` | yes | yes | Julia optimizer aggregate |
| restart/fallback counter | `total_optimizer_fallback_result_fits` | yes | yes | Julia optimizer aggregate |
| restart/last-resort counter | `total_optimizer_last_resort_fits` | yes | yes | Julia optimizer aggregate |

The plan names "duplicate counter" and "restart counter" are not literal column names. The checker
uses the actual record names above.

## Go-Criterion Implementation

The checker enforces:

1. exactly 16 records, each with `success is true`, no `failure_reason`, and no `error`;
2. one `git_hash`, one `config_fingerprint`, one `stage_cap_behavior_fingerprint`, plus manifest
   row identity and frozen pilot membership;
3. each required record field listed above exists and is non-null;
4. C-1/C-2 pairs use WP-N14 `ALLOWED_DIFFERENCE_COLUMNS` through `pair_registry_by_conditions`;
5. WP-N5 reconstruction-probe CSV contains every pilot cell with `reconstruction_probe_ok == true`
   and `reconstruction_abs_loss_delta == 0`.

Criterion 4 uses the WP-N14 allowlist and adds two pilot-local bookkeeping fields:
`manifest_index` and `batch_output_file`. This is necessary because raw Pilot JSONL records use
`manifest_index` where the aggregated registry uses `campaign_manifest_index`, and each raw cell
has its own output file path.

## Claude/User Runbook

1. Generate or refresh the Phase-C manifest and index lists:

```powershell
julia --project=. studies/regression/generate_phase_c_manifest.jl --all-dimensions
```

2. Start the existing Smoke job only after replacing `<COMMIT_SHA>` in
   `k8s/phase_c_indexed_smoke_job.yaml`:

```powershell
kubectl apply -f k8s/phase_c_indexed_smoke_job.yaml
```

3. Verify the Smoke records manually for cluster path health. The Smoke job is not the go
   criterion; it only proves the indexed cluster path runs.

4. Start the Pilot job only after replacing `<COMMIT_SHA>` in
   `k8s/phase_c_p9_pilot_job.yaml`:

```powershell
kubectl apply -f k8s/phase_c_p9_pilot_job.yaml
```

5. Run WP-N5 reconstruction on the Pilot records:

```powershell
julia --project=. studies/regression/wp_n5_ic_generalization.jl --input outputs/studies/regression/phase_c/p9_pilot_tasks_history.jsonl --output-dir outputs/studies/regression/phase_c/p9_pilot_wp_n5 --fresh
```

If the Pilot remains as one JSONL file per cell, first merge those 16 lines into the input JSONL
path used above.

6. Run the go criterion:

```powershell
python analysis/scripts/aggregate/verify_phasec_p9_pilot.py `
  --records-dir outputs/studies/regression/phase_c/p9_pilot_tasks `
  --manifest outputs/studies/regression/phase_c/manifest.csv `
  --reconstruction-probe outputs/studies/regression/phase_c/p9_pilot_wp_n5/reconstruction_probe.csv `
  --expected-git-hash <COMMIT_SHA> `
  --expected-stage-cap-behavior-fingerprint <STAGE_CAP_BEHAVIOR_FINGERPRINT>
```

The Phase-C campaign is released only when:

- the Smoke job has completed successfully;
- the Pilot job has produced exactly 16 successful records in its own output directory;
- WP-N5 has produced reconstruction rows for all 16 Pilot cells;
- `verify_phasec_p9_pilot.py` exits with code `0`.

Any non-zero exit is a no-go and names the failed criterion and cell.

## Verification

Python verification completed:

```text
python -m pytest analysis/tests/test_phasec_p9_pilot.py -q --basetemp .pytest_tmp
6 passed in 2.38s

python -m pytest analysis/tests -q --basetemp .pytest_tmp
43 passed in 12.04s
```

Julia verification not run: this Codex environment cannot execute the pinned Julia workflow. Claude
must run the generator and WP-N5 command above.
