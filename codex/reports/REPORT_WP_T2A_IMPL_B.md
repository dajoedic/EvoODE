# WP-T2a-impl-b Report

## Summary

Fixed the two defects found by Claude's WP-T2a-impl controls.

Julia was not executed in this Codex environment.

## Changes

- `studies/regression/generate_phase_c_manifest.jl`: added a T2a-only manifest identity that includes `candidate_prior_arm` and `candidate_prior_path`; the existing `phase_c_identity` and `phase_c_unique_identity_count` functions are unchanged and remain the non-T2a path.
- `test/test_candidate_prior.jl`: moved `run_regression.jl`, `phase_c_config.jl`, and `paper2_t2a_pilot_v1.jl` includes to top level; the assertions in the fingerprint/payload testset are unchanged.

## Static Checks

- T2a prior JSON files present: `84`.
- T2a expected manifest rows by construction: `2` arms x `21` exact dim-1/dim-2 systems x `2` IC sets x `3` seeds = `252`.
- T2a expected rows per arm: `126`.
- T2a expected S1 rows by construction: `1` oracle arm x `10` exact dim-2 systems x `2` IC sets x seed `42` = `20`.

## Claude Commands

Run the fixed Julia test file:

```bash
julia --project=. --startup-file=no test/test_candidate_prior.jl
```

Verify that regenerating the Phase C manifest is byte-identical to the frozen manifest:

```bash
mkdir -p outputs/t2a_controls/phase_c_manifest_identity
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl \
  --all-dimensions \
  --output outputs/t2a_controls/phase_c_manifest_identity/manifest.csv
cmp -s outputs/t2a_controls/phase_c_manifest_identity/manifest.csv experiments/paper1_phaseC_v1/manifest.csv && echo phase_c_manifest_byte_identical
```

Generate the T2a manifest and index files:

```bash
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl \
  --paper2-t2a-pilot \
  --output experiments/paper2_t2a_pilot_v1/manifest.csv
```

Expected T2a builder output includes:

```text
rows=252
unique_identities=252
arm_oracle_prior_rows=126
arm_guided_prior_rows=126
s1_index_rows=20
all_index_rows=252
```

Run the oracle smoke unchanged from WP-T2a-impl:

```bash
mkdir -p outputs/t2a_controls/oracle_smoke
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl \
  --manifest experiments/paper2_t2a_pilot_v1/manifest.csv \
  --output-dir outputs/t2a_controls/oracle_smoke 67
```

Oracle smoke pass criteria: the record has `candidate_prior_arm="oracle_prior"`, `candidate_prior_epsilon=0.2`, `candidate_prior_mapping="harmonic"`, non-null per-equation rankings and source hash, and a `config_fingerprint` different from `0c9672de35c75a9d`.

## Not Run

- Julia test, Phase C manifest generation, T2a manifest generation, and oracle smoke were not run because Julia is not executable in this Codex environment.
