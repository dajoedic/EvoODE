# REPORT WP-N48 — C-6 symbolic baseline platform

Implementation date: 2026-10-21. All changes remain uncommitted. No Git command, cluster command,
image build, baseline fit, campaign or blinded EvoGrow C-6 result read was performed.

## Implementation

- analysis/scripts/aggregate/run_k8s_symbolic_shard.py: common indexed entry for ODEFormer and legacy PySR.
- baselines/c6_shards.py: deterministic membership, smoke selection and completeness keys.
- baselines/noise_execution.py: atomic per-fit journal, provenance, no-clobber publication and ODEFormer RNG continuation.
- Optional execution hooks in both noise runners. Methods, configurations, operators, seeds, repetition
  counts, iterations and package versions are unchanged. Direct local calls retain their original behavior.
  Platform calls use runner functions and never their CLI comparison joins. Platform truth integration
  uses only shard systems, with the original helper and grids.
- aggregate_c6_symbolic_baselines.py: strict merge using original runner summary functions. Outputs:
  details.csv, records.jsonl, summary.csv, export_checks.csv, and merge_audit.json.
- compare_c6_symbolic_smoke.py: explicit control selection, PASS/FAIL and compared-field findings.
- Four new manifests; legacy PySR build/Trivy jobs; CHANGELOG compliance entry.
- Both relevant image-specific ignore files now include studies/regression/phase_c_support.json,
  required by both noise runners but missing from their previous build allowlists. The legacy Dockerfile
  explicitly precompiles Julia packages at build time and asserts PySR 0.19.4. Package pins are unchanged.

## Data and field audit

The S: drive and the task's long-name S: export were unavailable. The existing local copy
outputs/phase_c_c6_data_conditions_5dd1df8/index.csv has 4,536 rows: dimension 1: 1,656;
dimension 2: 2,016; dimension 3: 720; dimension 4: 144. Time/state hashes of all three selected
smoke cells match their local baseline references. Neither export was modified.
Manifests mount the specified long-name NFS export read-only at /export; results use /outputs.

| Field | Checked actual source |
|---|---|
| system_id, initial_condition_set, dimension, noise_sigma, subsample_rho, noise_realization | Existing export-index columns. IC becomes source_initial_condition_set in fit records. |
| time_sha256, state_sha256, n_observed_points, data_condition_fingerprint | Existing index columns. Original read_index_cell checks bytes, hashes, shapes and axes. |
| fit_state_sha256, observed_data_sha256 | Existing harness/noise fields. observed_data_sha256 reuses data_sha(row). |
| method_config | Existing serialized configuration with operators, budgets and optimizer settings. |
| odeformer_config_id, odeformer_noise_repetition | Existing ODEFormer record fields. |
| method, pysr_seed, pysr_realization, pysr_api | Existing PySR record fields; seeds remain labels. No new random_state is forwarded. |
| git_hash, code_origin_git_hash | Existing fields populated from required EVOODE_GIT_SHA in platform mode; images omit .git. |
| image_id | New record field from required EVOODE_IMAGE_ID, equal to manifest image tag. |
| hash_verified | Existing export_checks column. False plus error_message for validation failure; every requested unit gets an error record and export_validation_error. |
| context, key, sha256, rng_state | New checkpoint-envelope fields. Context binds semantic index, complete settings, image, commit, shard count and smoke mode. |

## Assignment and restart

Order is dimension band (1/2 first, 3/4 second), then ascending system_id, IC, sigma, rho,
realization. Each band is partitioned into contiguous balanced slices. No cost sorting or
round-robin mixing is used. Physical CSV row order and pod start order do not affect membership.
Each pod writes only its own shard_<index>/ directory: assignment.csv, index.csv, plan.json,
units/ and the four runner tables. Assignment is reproducible from the source index and shard count.
Indexed scheduling prioritizes low indices; it does not create a completion barrier for slow pods.

| Method | Shards | Cells/shard | Dim 1/2 indices | Dim 3/4 indices | Units/shard |
|---|---:|---:|---|---|---:|
| ODEFormer | 1,512 | 3 | 0–1,223 | 1,224–1,511 | 36 |
| PySR legacy | 4,536 | 1 | 0–3,671 | 3,672–4,535 | 6 |

Full expected counts: 54,432 ODEFormer records (4 configs x 3 repetitions x 4,536 cells);
27,216 PySR records (2 variants x 3 labels x 4,536 cells).
ODEFormer smoke has 2 one-cell shards, beam10_noopt, repetition 1.
PySR smoke has 1 cell, both variants, seed label 1.

The slowest complete Orion reference cell (system 45 / IC 2) sums its twelve fits to
2,652.258748 s. Three such cells cost 7,956.776244 s = 2.2102 h, below the approximate
three-hour planning target. A preliminary nine-cell plan would exceed it and was replaced.
Slowest dim-3 reference cell: 1,240.410216 s; three cost 1.0337 h.
PySR dim 4 planning: 4 equations x 527 s x 3 labels = 6,324 s = 1.7567 h per shard.
The PySR figure is explicitly a lower bound, not a guarantee; noise, startup and stragglers
can exceed these estimates. No time cutoff is introduced.

Neither original noise runner could resume: all records accumulated in memory and tables
were overwritten at the end. Platform mode commits each fit and export check together.
Unique temporary files are flushed/fsynced; same-directory hard links publish final units atomically
without replacing an existing unit. NFS/NTFS support this primitive; Orion smoke exercises it on NFS.
Checksums and required fields distinguish complete from partial files. Temporary files are ignored;
corrupt final files are quarantined; a changed context is rejected before overwriting the shard plan.
Complete scientific error records are not retried as infrastructure failures.

ODEFormer seeds global RNGs in adapter construction. Journals retain Python/NumPy/Torch CPU
RNG state and restore it after reconstructing previously used adapters; first-use adapters keep their
original initialization. Tests compare uninterrupted and interrupted sampling with four fake adapters
and interruptions in first/second repetitions. PySR's nondeterministic backend receives no new RNG policy.

The merger derives expected cell/configuration/repetition keys from the original index and frozen
configs. It verifies context, ownership, commit, image, hashes, legacy API and error/check consistency.
Duplicates must have identical canonical JSON bytes, including numeric results and metadata; no float
tolerance is used and signed zero remains distinct. Missing units abort except with explicit
--allow-incomplete. That option never bypasses conflicting duplicates or provenance/corruption failures.
Existing output directories are refused. Complete units survive interruption before final table flush.
No EvoGrow comparison table is read or produced.

## Smoke references and rules

| Control | Actual local reference |
|---|---|
| ODEFormer clean, system 1, IC 1 to 2, sigma/rho 0/0, beam10_noopt | outputs/wp_n38_noise_odeformer/control_system1_beam10_noopt/records.jsonl |
| Same clean control, Orion reference grid | analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records.jsonl |
| ODEFormer noisy, system 1, IC 1 to 2, sigma/rho 0.05/0.5, realization 1, beam10_noopt | outputs/wp_n38_noise_odeformer/stages/records.jsonl |
| PySR legacy, system 1, IC 1 to 2, sigma/rho 0.01/0, realization/seed 1, both variants | outputs/wp_n39_pysr_smoke/evoode-pysr-legacy_wp-n39/records.jsonl |

All references above exist. The earlier proposed
outputs/wp_n39_pysr_legacy_smoke_system1_sigma001_rho0/records.jsonl does not exist;
use the located legacy subdirectory. The adjacent v1 smoke is not the C-7 reference.

ODEFormer checks success, exact canonical equation, both observed-data hashes and all four clean
reconstruction/generalization R2 scores. Absolute tolerance: 2e-12, relative: 0. This is the requested
approximate 1e-12 scale: the pre-existing laptop and Orion clean records differ by 1.858e-12 in
generalization R2 and pass this explicit tolerance. Their equations and hashes are identical.
The N38 separate clean export used realization label 0; C-6 candidates must use label 1. Only the
old clean reference label is accommodated; hashes must still match exactly.

PySR checks success, legacy_0x API, both hashes, canonical expanded support per equation and all
coefficients (absolute 1e-6, relative 0). It reuses harness parsing/expansion and includes monomials
outside the polynomial basis. Missing records/references, failure statuses, altered equations,
coefficients, hashes or R2 produce FAIL. An Orion mismatch is a finding; do not change the frozen
method or relax the rule to remove it.

Fixtures under baselines/tests/fixtures/wp_n48/ were trimmed from four real N38/N39 records,
with source paths recorded. Changes for failure tests and the clean realization-label adaptation
are explicit. Self-comparisons of the selected real records and the laptop-vs-Orion clean comparison
passed. These are comparator checks, not new fitting results. No fitting smoke was run here.

## Cost planning — not evidence

N38: 240 fits, summed elapsed_s_non_evidence 2,791.045503231 s = 0.7752904 h (rounded task value 0.78 h).
Dim 1: 144 fits, mean 6.5749093 s; dim 2: 96 fits, mean 19.2110267 s.
Pooled low-dimensional projection:
3,672 x 12 x (2,791.0455 / 240) / 3,600 = 142.3433 core-h.
Weighting separate dimension means for the full C-6 mix gives 165.3916 core-h.

The Orion clean reference path above contains dim 3/4 timings: 240 / 48 fits with mean
65.205631 / 55.828308 s. Applied to 720 / 144 cells, twelve fits each:
156.4935 + 26.7976 = 183.2911 core-h. These are clean-grid timings; no local noisy dim-3/4
measurement exists. Largest individual fit: 776.6875 s (dim 2), 223.5727 s (dim 3), 165.1929 s (dim 4).

| ODEFormer projection | Core-h | EUR at 1.50/core-h | Wall h at 8 pods |
|---|---:|---:|---:|
| Dim 1/2, pooled N38 mean | 142.3433 | 213.5150 | 17.7929 |
| Dim 1/2, dimension-weighted N38 means | 165.3916 | 248.0874 | 20.6739 |
| Dim 3/4, Orion clean means | 183.2911 | 274.9367 | 22.9114 |
| Total, pooled low-dimensional estimate | 325.6344 | 488.4516 | 40.7043 |
| Total, dimension-weighted low-dimensional estimate | 348.6827 | 523.0241 | 43.5853 |

N39's measured 527 s is a complete one-equation cell including both variants and six hyper-fits.
Multiplying by another factor twelve double-counts that budget. Three repetition labels still
must be included for the actual full runner invocation.

| PySR legacy lower-end projection | One-label core-h | Three-label core-h | EUR, three labels | Wall h at 8 pods |
|---|---:|---:|---:|---:|
| Dim 1/2: 5,688 equations | 832.66 | 2,497.98 | 3,746.97 | 312.2475 |
| Dim 3/4: 2,736 equations | 400.52 | 1,201.56 | 1,802.34 | 150.1950 |
| Full: 8,424 equations | 1,233.18 | 3,699.54 | 5,549.31 | 462.4425 |

The often quoted 1,233.18 core-h / EUR 1,849.77 / 154.1475 wall h is the one-label lower bound.
The manifests run all three labels: plan at least 3,699.54 core-h, EUR 5,549.31 and 462.44 h
(~19.27 days) for PySR. ODEFormer followed by PySR totals at least ~4,025–4,048 core-h and
~503–506 wall h at eight pods. Startup, image loading, scheduling, retries and noise effects
are excluded. These calculations do not authorize a start in this session.

## Resources and CI

All four manifests: Indexed, parallelism <=8 (smokes 2/1), requested/limited CPU 1, five thread
variables 1, backoffLimit 50, TTL 3600 s, no active deadline. ODEFormer uses 4 Gi from the reference grid;
PySR uses the requested 4 Gi fallback because the N39 smoke contains no memory watermark.

Legacy CI copies the reference Dind digest, rules, disabled attestation flags, optional manual
behavior and three-hour build budget. SHA and ref-slug tags are built. The pinned Trivy component
depends on the build, has matching rules and allows failure as in the reference job. CHANGELOG
documents the addition; no new vulnerability exception or PySR 1.5.9 CI job is asserted.
The Dockerfile uses no host path and preinstalls/precompiles Julia packages before enabling both
offline flags. N39 previously ran this environment offline. A fresh image build and Orion smoke
remain deployment checks. The existing ODEFormer harness integration guard is untouched;
this package introduces no code/manifest timeout or hard wall-clock cut.

## Verification

Final acceptance command (from repository root, Python 3.12):

~~~powershell
& 'C:/Users/joedicke/AppData/Local/Programs/Python/Python312/python.exe' -m pytest baselines/tests analysis/tests -q --basetemp outputs/wp_n48_validation/pytest_acceptance
~~~

Actual final result: **289 passed, 5 skipped, 1 failed**, in 81.15 s; 240,248 warnings.
All 17 new platform tests passed, including both multiple-adapter RNG-continuation cases.
The sole failure is the existing unrelated
analysis/tests/test_evaluate_hypotheses_dataset_classification.py::test_phase_a_evaluation_does_not_overwrite_frozen_artifacts
(line 106): expected frozen-diagnostic reproduction text is absent; output reports the generalization
summary unavailable. The task mentioned two known failures; this environment reproduced one.
No baseline/analysis test or implementation for that failure was changed. No new failures remain.
Raw final log: outputs/wp_n48_validation/acceptance_suite.log.

Coverage includes all 4,536 actual-index assignments at multiple shard counts; dimension priority;
restart without refitting completed units; corrupt/partial unit rejection; no-clobber atomic publication;
recorded export validation failures for both methods; complete/missing/identical/conflicting duplicate merges;
overwrite refusal; smoke PASS and manipulated FAIL cases; four YAML manifests, thread/resource invariants;
CI YAML parsing and equality of build/scan rules with the reference job.
Earlier targeted command (before the final additional RNG/atomic tests):
python -m pytest baselines/tests/test_c6_symbolic_execution.py baselines/tests/test_run_odeformer_noise.py baselines/tests/test_run_pysr_noise.py -q
Result: 32 passed in 27.37 s (outputs/wp_n48_validation/targeted.log).

No Docker build or actual baseline fit was executed. Fresh CI image build, NFS-platform smoke and
actual Orion/reference equivalence remain the explicit operator gates above; their results are not invented.


## Operator sequence — PowerShell from repository root

These are commands for Claude/the user. No cluster command below was executed in this session.
Monitor with get until the specified completion criterion holds; no wait deadline is added.
Never apply PySR jobs while ODEFormer is running.

1. After review/commit by Claude, use the full SHA of a successful CI build containing WP-N48.
Both relevant image builds and scans must refer to that SHA. Review scan findings under the existing
pinned-environment policy. Substitute placeholders into a separate launch directory.
Pass: four files without remaining placeholders, matching SHA-tagged image/provenance values.

~~~powershell
$sha = Read-Host 'Full 40-character CI_COMMIT_SHA containing WP-N48, with successful image builds'
if ($sha -notmatch '^[0-9a-f]{40}$') { throw 'Expected full lowercase commit SHA' }
$launch = "outputs/wp_n48_launch_$sha"
New-Item -ItemType Directory -Path $launch -ErrorAction Stop | Out-Null
foreach ($name in @('odeformer_smoke','odeformer','pysr_smoke','pysr')) {
    $text = [IO.File]::ReadAllText((Join-Path $PWD "k8s/phase_c_c6_${name}_job.yaml"))
    $text = $text.Replace('<COMMIT_SHA>', $sha)
    [IO.File]::WriteAllText((Join-Path $PWD "$launch/phase_c_c6_${name}_job.yaml"), $text)
}
$env:PYTHONPATH = "$PWD;$PWD/analysis"
$py = 'python' # use the project's available Python executable
$export = 'S:/BigDataOrion/data-science/joedicke/phase_c_c6_data_conditions_5dd1df839f8ece98f2bb3bbff78d15d8c433d9d3/index.csv'
$nfs = 'S:/BigDataOrion/data-science/joedicke'
$odeImage = "registry.gitlab.scch.at:443/joedicke/evoode/odeformer-reference:$sha"
$pysrImage = "registry.gitlab.scch.at:443/joedicke/evoode/pysr-legacy:$sha"
$odeRoot = "$nfs/c6_odeformer_$sha"
$pysrRoot = "$nfs/c6_pysr_legacy_$sha"
~~~

2. Apply only the ODEFormer smoke (image, weights, read-only export, NFS publication, equivalence).
Monitor until succeeded=2 and active=0. Completed Jobs can contain scientific error records;
completion alone is not a PASS.

~~~powershell
kubectl -n scch-das apply -f "$launch/phase_c_c6_odeformer_smoke_job.yaml"
kubectl -n scch-das get job evoode-phase-c-c6-odeformer-smoke -o json
~~~

3. After completion compare both clean references and the noisy reference, then validate smoke
completeness. Pass: every control PASS, each command exit 0; merge expected=present=2, missing=0.
Any FAIL stops this sequence: preserve/report it. The output directory must not already exist.

~~~powershell
& $py -m analysis.scripts.aggregate.compare_c6_symbolic_smoke --control odeformer-clean --candidate "$odeRoot/smoke" --reference outputs/wp_n38_noise_odeformer/control_system1_beam10_noopt/records.jsonl --reference analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records.jsonl
if ($LASTEXITCODE -ne 0) { throw 'ODEFormer clean smoke FAIL' }
& $py -m analysis.scripts.aggregate.compare_c6_symbolic_smoke --control odeformer-stage --candidate "$odeRoot/smoke" --reference outputs/wp_n38_noise_odeformer/stages/records.jsonl
if ($LASTEXITCODE -ne 0) { throw 'ODEFormer noisy smoke FAIL' }
& $py -m analysis.scripts.aggregate.aggregate_c6_symbolic_baselines --method odeformer --smoke --n-shards 2 --input-dir "$odeRoot/smoke" --export-index $export --output-dir "$odeRoot/smoke_merged" --git-sha $sha --image-id $odeImage
if ($LASTEXITCODE -ne 0) { throw 'ODEFormer smoke completeness FAIL' }
~~~

4. Only after step 3 passes apply full ODEFormer. Monitor until succeeded=1512 and active=0.
Inspect completion within one hour because TTL removes completed Job objects; NFS data remain.

~~~powershell
kubectl -n scch-das apply -f "$launch/phase_c_c6_odeformer_job.yaml"
kubectl -n scch-das get job evoode-phase-c-c6-odeformer -o json
~~~

5. After ODEFormer has ended merge its full units. Pass: expected=present=54432, missing=0;
four runner tables plus audit. Scientific fit errors count as completed units; review their counts.

~~~powershell
& $py -m analysis.scripts.aggregate.aggregate_c6_symbolic_baselines --method odeformer --input-dir $odeRoot --export-index $export --output-dir "$odeRoot/merged" --git-sha $sha --image-id $odeImage
if ($LASTEXITCODE -ne 0) { throw 'ODEFormer full merge FAIL' }
~~~

6. Only after ODEFormer has finished and step 5 passes, apply PySR smoke.
Monitor until succeeded=1 and active=0.

~~~powershell
kubectl -n scch-das apply -f "$launch/phase_c_c6_pysr_smoke_job.yaml"
kubectl -n scch-das get job evoode-phase-c-c6-pysr-legacy-smoke -o json
~~~

After completion compare both variants and merge. Pass: two PASS results, exit 0;
merge expected=present=2, missing=0. A support/coefficient mismatch is a finding to preserve,
not a reason to reconfigure the frozen method.

~~~powershell
& $py -m analysis.scripts.aggregate.compare_c6_symbolic_smoke --control pysr --candidate "$pysrRoot/smoke" --reference outputs/wp_n39_pysr_smoke/evoode-pysr-legacy_wp-n39/records.jsonl
if ($LASTEXITCODE -ne 0) { throw 'PySR smoke FAIL: preserve and report findings' }
& $py -m analysis.scripts.aggregate.aggregate_c6_symbolic_baselines --method pysr --smoke --n-shards 1 --input-dir "$pysrRoot/smoke" --export-index $export --output-dir "$pysrRoot/smoke_merged" --git-sha $sha --image-id $pysrImage
if ($LASTEXITCODE -ne 0) { throw 'PySR smoke completeness FAIL' }
~~~

7. Only after step 6 passes apply full PySR. Monitor until succeeded=4536 and active=0.

~~~powershell
kubectl -n scch-das apply -f "$launch/phase_c_c6_pysr_job.yaml"
kubectl -n scch-das get job evoode-phase-c-c6-pysr-legacy -o json
~~~

8. Later, after PySR ends, merge without an incomplete override.
Pass: expected=present=27216, missing=0; four runner tables plus audit; no EvoGrow comparison.

~~~powershell
& $py -m analysis.scripts.aggregate.aggregate_c6_symbolic_baselines --method pysr --input-dir $pysrRoot --export-index $export --output-dir "$pysrRoot/merged" --git-sha $sha --image-id $pysrImage
if ($LASTEXITCODE -ne 0) { throw 'PySR full merge FAIL' }
~~~

For an explicitly requested partial diagnostic only, add --allow-incomplete and use a new directory
(e.g. $pysrRoot/partial_<label>). A missing>0 audit is not full-grid acceptance. Repeating verification
uses a fresh destination, never deletes complete results. Pod retries resume automatically.
Do not reuse a result root with a different image, index, configuration or shard count.
