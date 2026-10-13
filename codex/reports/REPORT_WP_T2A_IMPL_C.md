# WP-T2a-impl-c Report

## Status

Implemented. Julia was not executed in this Codex session, per task prohibition.

## Changes

- `studies/regression/paper2_t2a_pilot_v1.jl`
  - T2a manifest rows now write `candidate_prior_path` as `priors/<file>.json` with forward slashes.
  - T2a prior loading resolves the relative path against the directory of the manifest being read.
  - Absolute Unix paths, Windows drive paths, and rooted Windows paths are refused with a clear stale-manifest error.
  - T2a config fingerprints still load the prior content and do not include the path string in the payload.
- `studies/regression/run_batch_cell.jl`
  - Computes `manifest_dir = dirname(abspath(manifest_path))` once and passes it through T2a fingerprint and variant construction.
- `studies/regression/print_phase_c_stage_caps.jl`
  - Updated direct `_batch_fingerprint` / `_batch_variant` calls for the new manifest-directory argument.
- `test/test_candidate_prior.jl`
  - Added a T2a portability test covering relative resolution, absolute-path rejection, and identical fingerprint after copying manifest plus `priors/`.
- `experiments/paper2_t2a_pilot_v1/manifest.csv`
  - Updated the existing 252 manifest rows from absolute Windows prior paths to manifest-relative `priors/*.json` paths.
- `SCRIPTS.md`
  - Added the S1 Orion sequence: regenerate manifest, copy `manifest.csv`, `indices_s1_oracle_dim2_seed42.txt`, and `priors/` to NFS, apply the S1 Job, collect from `/paper2_t2a_s1_<SHA>/tasks`.

## Static Checks Run

No Julia command was run.

PowerShell inspection:

```powershell
$rows = Import-Csv experiments/paper2_t2a_pilot_v1/manifest.csv
$abs = $rows | Where-Object {
  $_.candidate_prior_path -match '^[A-Za-z]:[\\/]' -or
  $_.candidate_prior_path -match '^/' -or
  $_.candidate_prior_path -match '\\'
}
```

Observed:

- `rows=252`
- `absolute_or_backslash=0`
- System 24, seed 42, IC 1, oracle row:
  - `index=67`
  - `config_fingerprint=52edf2893b9d9e70`
  - `candidate_prior_path=priors/oracle_prior_system_0024_ic1.json`
- Artifact counts:
  - `priors=84`
  - `s1_indices=20`
  - `all_indices=252`

Existing earlier smoke reference, read only from `outputs/t2a_controls/oracle_smoke/cell_000067.jsonl`:

- `config_fingerprint=52edf2893b9d9e70`
- `loss=6.868034641654147e-15`
- `support_terms=[["u1","u2"],["u1"]]`
- `total_loss_evals=74296`

## Claude Control Commands

Run the test:

```powershell
julia --project=. --startup-file=no test/test_candidate_prior.jl
```

Regenerate the T2a manifest:

```powershell
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl `
  --paper2-t2a-pilot `
  --output experiments\paper2_t2a_pilot_v1\manifest.csv
```

Check for stale absolute paths or backslashes:

```powershell
Select-String -Path experiments\paper2_t2a_pilot_v1\manifest.csv,experiments\paper2_t2a_pilot_v1\indices_s1_oracle_dim2_seed42.txt,experiments\paper2_t2a_pilot_v1\indices_all.txt `
  -Pattern ':[\\/]|^[^,]*,[^,]*.*[A-Za-z]:[\\/]|\\'
```

Expected: no matches.

Oracle smoke from a copied portable directory:

```powershell
Remove-Item -Recurse -Force tmp\t2a_portable -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force tmp\t2a_portable\priors,tmp\t2a_portable\tasks
Copy-Item experiments\paper2_t2a_pilot_v1\manifest.csv,tmp\t2a_portable\
Copy-Item experiments\paper2_t2a_pilot_v1\indices_s1_oracle_dim2_seed42.txt,tmp\t2a_portable\
Copy-Item -Recurse experiments\paper2_t2a_pilot_v1\priors\* tmp\t2a_portable\priors\

julia --project=. --startup-file=no studies/regression/run_batch_cell.jl `
  --manifest tmp\t2a_portable\manifest.csv `
  --output-dir tmp\t2a_portable\tasks `
  67
```

Expected for `tmp/t2a_portable/tasks/cell_000067.jsonl`:

- `config_fingerprint=52edf2893b9d9e70`
- `loss=6.868034641654147e-15`
- `support_terms=[["u1","u2"],["u1"]]`
- `total_loss_evals=74296`

## Notes

The T2a manifest now carries only portable paths. The runtime path resolution depends on the manifest actually being read (`EVO_BATCH_MANIFEST` or `--manifest`) and not on the current working directory.
