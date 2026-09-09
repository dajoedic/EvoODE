# WP-H4 Report - Indexed Kubernetes cells

## Files

Bootstrap workload:

- `k8s/phase_b_bootstrap_smoke_job.yaml`

Indexed cell smoke Job:

- `k8s/phase_b_indexed_smoke_job.yaml`

Image-versioned Kubernetes index mapping:

- `studies/regression/run_k8s_indexed_cell.jl`

The bootstrap workload and the indexed cell Job are deliberately separate. The bootstrap writes the
manifest and index lists once into NFS. The cell Job only reads those files. This avoids a shared
storage write race where many concurrent pods could regenerate the manifest and disagree about what
row `n` means.

## Image change

The image content needs changing because `run_k8s_indexed_cell.jl` is a new entry point under
`studies/regression/`, which is copied into `/opt/EvoODE/studies` by `containers/Dockerfile`.

`containers/Dockerfile` itself was not changed. A rebuild is still required so the image tagged by
commit SHA contains the new mapping script.

`generate_phase_b_manifest.jl` now also writes `indices_all.txt` when called with
`--all-dimensions`. This gives a direct path from smoke to a single 756-completion Job while keeping
the existing per-dimension lists.

## Bootstrap

`k8s/phase_b_bootstrap_smoke_job.yaml` runs:

```text
julia --project=/opt/EvoODE /opt/EvoODE/studies/regression/generate_phase_b_manifest.jl \
  --output /outputs/wp_h4_smoke_<COMMIT_SHA>/manifest.csv \
  --all-dimensions
```

It uses:

- Namespace: `scch-das`
- Image: `registry.gitlab.scch.at:443/joedicke/evoode:<COMMIT_SHA>`
- Pull secret: `evoode-gitlab-pull`
- NFS: `nfs.orion.scch.at:/bigdata`
- Mount: `/bigdata/data-science/joedicke` as `/outputs`
- Resources: 1 CPU, 2 GiB

Local bootstrap-equivalent output:

```text
phase_b_fingerprint=c71c85ac2ec580ff
rows=756
all_index_rows=756
dimension_1_rows=276
dimension_2_rows=336
dimension_3_rows=120
dimension_4_rows=24
```

The observed fingerprint matches the known value `c71c85ac2ec580ff`.

## Index mapping

Kubernetes `JOB_COMPLETION_INDEX` is 0-based. The Phase B index lists are line-oriented files whose
first line is line 1. The new mapping is therefore:

```text
index_list_line = JOB_COMPLETION_INDEX + 1
manifest_index = parse(Int, index_list[index_list_line])
```

`run_k8s_indexed_cell.jl` prints the resolved line and manifest row before running the cell. It can
also be run with `--dry-run` for mapping checks.

Boundary and middle checks against the generated 1D list:

```text
JOB_COMPLETION_INDEX=0
index_list_line=1
index_list_rows=276
manifest_index=1
manifest_row_system_id=1
manifest_row_system_dim=1
manifest_row_variant=evogrow_v2_2_stage_capped_pretune_on
manifest_row_initial_condition_set=1
manifest_row_seed=42

JOB_COMPLETION_INDEX=137
index_list_line=138
index_list_rows=276
manifest_index=138
manifest_row_system_id=23
manifest_row_system_dim=1
manifest_row_variant=evogrow_v2_2_stage_capped_pretune_on
manifest_row_initial_condition_set=2
manifest_row_seed=7

JOB_COMPLETION_INDEX=275
index_list_line=276
index_list_rows=276
manifest_index=516
manifest_row_system_id=23
manifest_row_system_dim=1
manifest_row_variant=evogrow_v2_2_stage_capped_pretune_off
manifest_row_initial_condition_set=2
manifest_row_seed=7
```

Index-list validation:

```text
indices_all.txt: rows=756 bad=0 first=1 last=756
indices_dim1.txt: rows=276 bad=0 first=1 last=516
indices_dim2.txt: rows=336 bad=0 first=139 last=684
indices_dim3.txt: rows=120 bad=0 first=307 last=744
indices_dim4.txt: rows=24 bad=0 first=367 last=756
```

This explicitly checks the off-by-one boundary: the first Kubernetes completion runs the first list
row, and the last 1D completion runs the last 1D list row without reading past the end.

## Indexed smoke Job

`k8s/phase_b_indexed_smoke_job.yaml` uses:

```yaml
completionMode: Indexed
completions: 3
parallelism: 3
```

For smoke, it reads:

```text
EVO_BATCH_MANIFEST=/outputs/wp_h4_smoke_<COMMIT_SHA>/manifest.csv
EVO_BATCH_INDEX_LIST=/outputs/wp_h4_smoke_<COMMIT_SHA>/indices_dim1.txt
EVO_BATCH_OUTPUT_DIR=/outputs/wp_h4_smoke_<COMMIT_SHA>/tasks
```

The Job references the image by commit SHA placeholder only:

```text
registry.gitlab.scch.at:443/joedicke/evoode:<COMMIT_SHA>
```

It does not use the moving `main` tag.

Restart policy is `OnFailure` with `backoffLimit: 2`. The workload is deterministic by seed, so a
failed cell can be retried and should produce the same record when the failure was transient.

The pod requests and limits 1 CPU and 2 GiB memory. No GPU is requested.

## Smoke-to-campaign knobs

Values to change for a real run:

- Replace `<COMMIT_SHA>` in both YAML files with the exact GitLab/GitHub commit SHA tag.
- Change the bootstrap output directory from `/outputs/wp_h4_smoke_<COMMIT_SHA>/...` to the chosen
  throwaway or campaign-specific output root.
- Change `EVO_BATCH_OUTPUT_DIR` to the matching `tasks` directory.
- For the current smoke: keep `EVO_BATCH_INDEX_LIST=.../indices_dim1.txt`, `completions: 1` to
  `3`, and small `parallelism`.
- For the full 756-cell campaign as one Job: use `EVO_BATCH_INDEX_LIST=.../indices_all.txt`,
  `completions: 756`, and set `parallelism` to the approved concurrency.
- For dimension-split operation: use the relevant `indices_dim<N>.txt` and set `completions` to
  `276`, `336`, `120`, or `24` for dimensions 1 through 4.

## Local validation

Validated locally:

```text
k8s_yaml_ok
```

This used Python/PyYAML to parse both Kubernetes manifests.

`kubectl apply --dry-run=client --validate=false` could not be used as a purely local structural
check in this environment: even with a dummy kubeconfig it attempted API discovery at
`localhost:8080` and failed because no local API server exists. Nothing was applied to Orion.

## Untested until a real cluster run

- Whether the YAML labels exactly match any additional SCCH operator convention beyond the standard
  attribution labels used here.
- Whether `<COMMIT_SHA>` resolves to a pulled image in `scch-das`.
- Whether the pull secret `evoode-gitlab-pull` works for this Job.
- Whether the NFS mount and `subPath: data-science/joedicke` behave as expected in a Job pod.
- Whether Kubernetes injects `JOB_COMPLETION_INDEX` exactly as expected for this Orion v1.30.10
  indexed Job configuration.
- Whether the bootstrap Job lands manifest and index files on NFS.
- Whether the indexed Job lands records and heartbeat files on NFS for each completion.
- Runtime behavior under Orion scheduling, retry, eviction, and filesystem latency.
- Merge, aggregation, full campaign execution, and any walltime policy.

## WP-H4b label correction

The invented `scch.at/owner` and `scch.at/workload` labels were removed from both Kubernetes
manifests.

Site-convention labels now used:

```text
hpc.scch.at/responsibility: joedicke
hpc.scch.at/service: evoode-phase-b-bootstrap
hpc.scch.at/service: evoode-phase-b-cells
```

`phase_b_bootstrap_smoke_job.yaml` uses `hpc.scch.at/service: evoode-phase-b-bootstrap`.
`phase_b_indexed_smoke_job.yaml` uses `hpc.scch.at/service: evoode-phase-b-cells`.

Both manifests carry `hpc.scch.at/service` and `hpc.scch.at/responsibility` in the Job object's
`metadata.labels` and in the pod template's `spec.template.metadata.labels`, so the attribution is
visible both when inspecting the Job and when inspecting a running pod.
