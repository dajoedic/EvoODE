# WP-N9 Report

## Implemented

- `studies/regression/wp_n1_basis_probe.jl` is now include-safe: including it exposes `_wp_n1_basis_modes()` and support helpers without starting the serial probe.
- `studies/regression/phase_b_config.jl` still leaves `PHASE_B_VARIANTS` unchanged and extends only `phase_b_variant(label)` so it can resolve WP-N1 basis variants after `_wp_n1_basis_modes()` is loaded.
- `studies/regression/run_batch_cell.jl` recognizes `campaign=wp_n1_basis_probe`, uses `_wp_n1_fingerprint(dim)`, resolves the row variant through `phase_b_variant(row["variant"])`, builds the per-basis WP-N1 system, and appends the same WP-N1-specific record fields as the serial probe:
  - `base_config_fingerprint`
  - `probe_identity_definition`
  - `probe_identity_mode`
  - `probe_identity_override_env`
  - `probe_identity_override_reason`
  - `wp_n1_expected_support_terms`
  - `wp_n1_support_status`
- `studies/regression/generate_wp_n1_basis_probe_manifest.jl` writes a manifest and index list for the existing indexed runner path.
- `k8s/wp_n1_basis_probe_dim2_smoke_job.yaml` runs 3 indexed cells.
- `k8s/wp_n1_basis_probe_dim2_campaign_job.yaml` runs 336 indexed cells.
- `analysis/scripts/aggregate/compare_wp_n1_manifest_equivalence.py` compares new dim-1 batch task records against the existing serial records.

## Equivalence Cells

Planned dim-1 equivalence cells:

| Manifest index | Variant | System | IC set | Seed |
|---:|---|---:|---:|---:|
| 1 | `wp_n1_old_basis` | 2 | 1 | 7 |
| 2 | `wp_n1_old_basis` | 2 | 1 | 42 |
| 3 | `wp_n1_old_basis` | 2 | 1 | 123 |
| 67 | `wp_n1_constant_basis` | 2 | 1 | 7 |
| 68 | `wp_n1_constant_basis` | 2 | 1 | 42 |
| 69 | `wp_n1_constant_basis` | 2 | 1 | 123 |

Claude command sequence for equivalence:

```powershell
julia --project=. --startup-file=no studies/regression/generate_wp_n1_basis_probe_manifest.jl --dimension 1 --output outputs/wp_n1_dim1_manifest_path_equivalence/manifest.csv --index-output outputs/wp_n1_dim1_manifest_path_equivalence/indices_dim1.txt
$indices = 1,2,3,67,68,69
foreach ($i in $indices) { julia --project=. --startup-file=no studies/regression/run_batch_cell.jl $i --manifest outputs/wp_n1_dim1_manifest_path_equivalence/manifest.csv --output-dir outputs/wp_n1_dim1_manifest_path_equivalence/tasks }
python analysis/scripts/aggregate/compare_wp_n1_manifest_equivalence.py --batch-dir outputs/wp_n1_dim1_manifest_path_equivalence/tasks --indices 1 2 3 67 68 69
```

The comparison checks `loss`, `pruned_match`, and `support_terms`. The existing reference records have `git_hash="not_collected"` and no identity fields; those are intentionally not compared.

## Fingerprint Preservation

Static preservation check:

- `PHASE_B_VARIANTS` was not edited.
- `phase_b_fingerprint()` still builds its variant payload from `PHASE_B_VARIANTS` only.
- The added WP-N1 resolver branch is outside the fingerprint payload and is reached only after existing Phase-B labels fail to match.
- The committed Phase-B campaign manifest has 336 dim-2 rows and one manifest fingerprint: `604e79733b22d64d`.

Claude should confirm the current runtime value by running the new generator; its `base_phase_b_fingerprint` output must remain `604e79733b22d64d`.

## Manifest Counts

Expected dim-2 manifest rows: `28 systems * 2 bases * 2 IC sets * 3 seeds = 336`.

Expected dim-2 index rows: `336`.

The existing Phase-B manifest also contains `336` dim-2 rows, confirming the 28-system dim-2 arm size.

## Required Commands

Manifest generation, expected `336` rows:

```powershell
julia --project=. --startup-file=no studies/regression/generate_wp_n1_basis_probe_manifest.jl --dimension 2 --output outputs/wp_n1_dim2_probe_<COMMIT_SHA>/manifest.csv --index-output outputs/wp_n1_dim2_probe_<COMMIT_SHA>/indices_dim2.txt
```

Smoke job, expected `3` cells:

```powershell
kubectl apply -f k8s/wp_n1_basis_probe_dim2_smoke_job.yaml
```

Full dim-2 run, expected `336` cells:

```powershell
kubectl apply -f k8s/wp_n1_basis_probe_dim2_campaign_job.yaml
```

## Runtime Error Classes Reviewed

| Class | Static review result |
|---|---|
| Missing manifest columns | WP-N1 manifest header includes `index,campaign,config_fingerprint,variant,condition,use_pretuning,basis_name,system_id,system_dim,initial_condition_set,seed`; `run_batch_cell.jl` requires only present fields for WP-N1 routing. |
| `Set` versus `Vector` | Generator identities use `Set` only for uniqueness counting; iteration order comes from vectors and sorted system lists. |
| `JSON3.Object` versus `Dict` | New batch route passes ordinary `Dict` objects where mutation is needed; JSON3 manifest parsing is not used. |
| Indexing with `nothing` | `identity_context` is only merged in the WP-N1 branch; WP-N1 support fields are taken from `_wp_n1_system_for_basis`, which always assigns keys with `nothing` allowed as value. |
| Missing record fields | `run_one` writes `basis_name`, `condition`, `support_terms`, `model_terms`, `loss`, and `pruned_match`; WP-N1 branch adds `wp_n1_expected_support_terms` and `wp_n1_support_status`, matching `aggregate_wp_n1_coefficient_metrics.py`. |
| Container-only paths | k8s manifests use `/outputs/wp_n1_dim2_probe_<COMMIT_SHA>/...`, matching the mounted NFS path and the existing indexed runner env vars. |
| Identity fallback | `git_provenance()` uses baked `EVOODE_GIT_SHA` when `.git` is absent in the container; `_wp_n1_identity_context` is still called and the WP-N8 identity guard is not bypassed. |

## Open Acceptance

Julia was not executed in this Codex session by instruction and environment constraint. The following acceptance points remain for Claude:

- Run the dim-1 equivalence sequence and report the exact matches.
- Generate the dim-2 manifest and verify `rows=336`, `index_rows=336`, and unchanged `base_phase_b_fingerprint`.
- Run the 3-cell smoke job only after replacing `<COMMIT_SHA>` and ensuring the manifest exists on NFS.
