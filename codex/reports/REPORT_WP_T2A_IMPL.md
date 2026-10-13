# WP-T2a-impl Report

## Summary

Implemented a behaviour-neutral candidate-prior hook for `EvoGrow`, a Paper 2 T2a prior generator, Julia campaign plumbing, the S1 Kubernetes Job, docs, tests, and prior JSON outputs.

Julia was not executed in this Codex environment, per task instruction.

## Files Changed

- `src/structure/evogrow.jl`: added `CandidatePrior`, harmonic categorical draw, validation, prior metadata, and term-draw hooks.
- `src/structure/evogrow_v3_childgen.jl`: routed equation-aware term draws through the same prior-aware helper.
- `src/EvoODE.jl`: exported candidate-prior API.
- `studies/regression/run_regression.jl`: records prior fields as explicit nulls or active prior metadata.
- `studies/regression/run_batch_cell.jl`: recognizes `paper2_t2a_pilot_v1` rows.
- `studies/regression/paper2_t2a_pilot_v1.jl`: loads prior JSON, fingerprints active priors, builds T2a rows and S1 index list.
- `studies/regression/generate_phase_c_manifest.jl`: added `--paper2-t2a-pilot`.
- `analysis/scripts/aggregate/build_t2a_candidate_priors.py`: generated guided/oracle prior JSON files.
- `analysis/tests/test_t2a_candidate_priors.py`, `test/test_candidate_prior.jl`: new focused tests.
- `k8s/paper2_t2a_s1_job.yaml`: S1 indexed Job, `parallelism: 8`, 1 CPU / 2 Gi, no `activeDeadlineSeconds`.
- `SCRIPTS.md`: added prior generator, T2a manifest/S1 Job, and control-test entries.

## Prior Files

- Produced `84` JSON files under `experiments/paper2_t2a_pilot_v1/priors/`.
- Coverage: `21` exact dim-1/dim-2 systems x `2` IC sets x `2` arms.
- Source: `analysis/data/wp_t1_term_relevance/records.csv`.
- Source SHA-256 is stored in each JSON as `source_sha256`.
- Trajectory hash source checked by the generator: `outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/trajectory_manifest.csv`, field `state_sha256`.
- Static validation: `84` files, `0` bad rankings; every ranking is a full permutation of the dimension's staged polynomial basis with constant.

## Draw Sites Changed

Term draws now use the prior only when `candidate_prior !== nothing`; otherwise they call the same uniform `rand(candidates)` path.

- `src/structure/evogrow.jl`
  - `_init_population`: one initial term per equation.
  - `_expand`: passive allowed-term child draw.
  - `_expand_stage_aware`: current-stage draw and fallback allowed-term draw.
  - `_expand_stage_soft`: current-stage biased draw and fallback allowed-term draw.
- `src/structure/evogrow_v3_childgen.jl`
  - `_expand_equation_aware_passive`: equation-specific allowed-term draw.
  - `_expand_equation_aware_hard`: equation-specific current-stage draw and fallback allowed-term draw.
  - `_expand_equation_aware_soft`: equation-specific current-stage draw and fallback allowed-term draw.

Uniform draws deliberately left uniform:

- `rand(1:dim)`: selects which equation grows.
- `rand(eqs_with_new_terms)` and `rand(growable_eqs)`: selects an equation among eligible equations.
- `rand() < bias_prob`: stage-usage policy coin flip.

Reason: these are equation/policy choices, not basis-term choices. The prior is specified per equation over candidate basis terms only.

## Tests Run

Passed:

```text
python -m py_compile analysis/scripts/aggregate/build_t2a_candidate_priors.py analysis/tests/test_t2a_candidate_priors.py
python -m pytest analysis/tests/test_t2a_candidate_priors.py
```

Result: `3 passed in 42.16s` with `TMPDIR`, `TEMP`, and `TMP` redirected to `tmp/pytest_tmp` inside the workspace.

Generator run:

```text
python analysis/scripts/aggregate/build_t2a_candidate_priors.py
```

Result: `priors=84`.

Not run: Julia tests or Julia manifest generation.

## Claude Control Commands

Run focused and adjacent Julia tests:

```bash
julia --project=. --startup-file=no test/test_candidate_prior.jl
julia --project=. --startup-file=no test/test_stage_cap.jl
julia --project=. --startup-file=no test/test_evogrow_v3_childgen.jl
```

Build the T2a manifest and S1 index list after the prior JSONs are present:

```bash
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl \
  --paper2-t2a-pilot \
  --output experiments/paper2_t2a_pilot_v1/manifest.csv
```

Expected builder output includes `rows=252`, `arm_oracle_prior_rows=126`, `arm_guided_prior_rows=126`, and `s1_index_rows=20`.

Bit-identity without prior, hard stop. Re-run these C-1 cells through the new code with `candidate_prior = nothing` and compare `loss`, `support_terms`, `model_terms`, `total_loss_evals`, and `config_fingerprint` against `experiments/paper1_phaseC_v1/run_registry.csv`:

- System `1`, seed `42`, IC `1`, C-1 manifest index `1`.
- System `24`, seed `42`, IC `1`, C-1 manifest index `277`.
- Cheapest dim-3 C-1 cell by `total_loss_evals`: system `53`, seed `123`, IC `2`, manifest index `633`, `total_loss_evals=403073`.

Suggested commands:

```bash
mkdir -p outputs/t2a_controls/bit_identity
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl \
  --manifest experiments/paper1_phaseC_v1/manifest.csv \
  --output-dir outputs/t2a_controls/bit_identity 1
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl \
  --manifest experiments/paper1_phaseC_v1/manifest.csv \
  --output-dir outputs/t2a_controls/bit_identity 277
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl \
  --manifest experiments/paper1_phaseC_v1/manifest.csv \
  --output-dir outputs/t2a_controls/bit_identity 633
```

Laptop smoke of the oracle arm on system `24`, seed `42`, IC `1` after T2a manifest generation. In the generated T2a order this should be manifest index `67`:

```bash
mkdir -p outputs/t2a_controls/oracle_smoke
julia --project=. --startup-file=no studies/regression/run_batch_cell.jl \
  --manifest experiments/paper2_t2a_pilot_v1/manifest.csv \
  --output-dir outputs/t2a_controls/oracle_smoke 67
```

Pass criteria: record has `candidate_prior_arm="oracle_prior"`, `candidate_prior_epsilon=0.2`, `candidate_prior_mapping="harmonic"`, non-null per-equation rankings and source hash, and a `config_fingerprint` different from `0c9672de35c75a9d`.

## Notes

- The active-prior fingerprint payload includes the Phase-C base fingerprint, arm, epsilon, mapping, per-equation rankings, source tag, and source hash.
- The inactive Phase-C fingerprint path is unchanged by construction; `test/test_candidate_prior.jl` asserts `phase_c_fingerprint() == "0c9672de35c75a9d"`.
- `evogrow_v3.jl` was not edited; only the shared child-generation helper it can call was extended with an inert default argument.
