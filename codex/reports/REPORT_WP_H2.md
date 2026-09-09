# WP-H2 Report - Docker image for Orion

## Dockerfile location

The OCI image definition lives at `containers/Dockerfile`, next to the existing Apptainer
definition. The Apptainer file and Slurm scripts were not deleted or rewritten.

The local image built successfully as:

```text
evoode-regression:h2
image_id=sha256:8cdb159fa56a911ad8998471e16e063f3121a033d18f6add9570b66f86fb3a33
```

## Apptainer-to-Docker correspondence

The Dockerfile mirrors `containers/evoode_regression.apptainer` section by section:

- Base image: `julia:1.12.6-bookworm`.
- Runtime environment: `JULIA_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`,
  `JULIA_DEPOT_PATH=/opt/julia_depot`, `EVO_BATCH_MANIFEST=/outputs/manifest.csv`, and
  `EVO_BATCH_OUTPUT_DIR=/outputs/tasks`.
- Copied inputs: `Project.toml`, `Manifest.toml`, `src/`, `studies/`, and `benchmarks/` under
  `/opt/EvoODE`, so the ODEBench data and `studies/regression/phase_b_support.json` are inside the
  image.
- Build provenance: `/opt/EvoODE/build_provenance.json` is written during build with
  `julia_version`, `project_toml_sha256`, and `manifest_toml_sha256`.
- Dependency freeze: `julia --project=. -e 'import Pkg; Pkg.instantiate(); Pkg.precompile()'` runs
  during the image build with the depot at `/opt/julia_depot`.
- Entry point: arguments are passed directly to
  `/opt/EvoODE/studies/regression/run_batch_cell.jl`, matching the Apptainer runscript behavior.

## Arbitrary UID / GID 0 adjustments

OpenShift may run the image as an unpredictable UID with group 0. The Dockerfile therefore does not
set a fixed `USER`.

Adjusted paths:

- `/opt/EvoODE`: source tree and build provenance; must be readable by arbitrary UID and writable via
  group 0 if Julia or local code needs to place runtime artifacts under the project root.
- `/opt/julia_depot`: baked Julia depot; must be readable and writable via group 0 so Julia can use
  precompiled state and create any missing runtime cache files without a permission error.
- `/outputs`: default mounted output root; must be writable via group 0 for manifest, index lists,
  records, heartbeat files, and any created subdirectories.

Implementation:

```dockerfile
chgrp -R 0 /opt/EvoODE /opt/julia_depot /outputs
chmod -R g=u /opt/EvoODE /opt/julia_depot /outputs
```

`HOME=/tmp` is set so tools that consult a home directory do not require a user-specific home path.

Permission probe as UID `12345`, GID `0` passed:

```text
permissions_ok
```

The probe checked read access to `/opt/EvoODE/Project.toml`, `/opt/EvoODE/src/EvoODE.jl`, and
`/opt/julia_depot`, plus write access to `/opt/EvoODE`, `/opt/julia_depot`, and mounted `/outputs`.

## Build context hygiene

Added `.dockerignore` as an allowlist. The build context includes only:

- `Project.toml`
- `Manifest.toml`
- `src/`
- `studies/`
- `benchmarks/`
- `containers/Dockerfile`

This excludes `.git/`, `outputs/`, local scratch/output trees, reports, figures, tables, and other
repo state that the image does not need. After tightening the ignore file, Docker reported a
successful rebuild with `.dockerignore` loaded and a tiny requested context.

## Build provenance verification

Inside the image:

```json
{"julia_version":"1.12.6","project_toml_sha256":"2153e124df036ec434d3e4313a63193f595c334d54baa4781c28f320ca6ad04e","manifest_toml_sha256":"2a2f5dcc0b5555178cdb76935f9f7d22b8e75bbed3ef387d5243941bcf552f6c"}
```

Local dependency-freeze hashes:

```text
Project.toml  2153E124DF036EC434D3E4313A63193F595C334D54BAA4781C28F320CA6AD04E
Manifest.toml 2A2F5DCC0B5555178CDB76935F9F7D22B8E75BBED3EF387D5243941BCF552F6C
```

Result: Julia version and both hashes match.

## Manifest generation inside Docker

Generated inside the container into mounted throwaway output roots.

Observed output:

```text
phase_b_fingerprint=c71c85ac2ec580ff
regression_fingerprint=45cb2c4507007366
rows=756
unique_identities=756
systems=63
expected_stage_missing=63
representability_exact=20
representability_surrogate=43
dimension_1_rows=276
dimension_2_rows=336
dimension_3_rows=120
dimension_4_rows=24
```

Index-list validation on the host:

```text
manifest_rows=756
index_bad=0
```

The observed Phase B fingerprint matches the WP-H1 value: `c71c85ac2ec580ff`.

## One-cell Docker run: default user

Throwaway root: `outputs/docker_wp_h2_default/`.

Command path: generated manifest inside the container, then ran manifest index `61`, a 1D System 11
cell.

Result:

```text
variant=evogrow_v2_2_stage_capped_pretune_on
system_id=11
ic=1
seed=42
loss=4.674e-15
pruned=true
elapsed=14.5s
record_lines=1
error_null=True
fingerprint=c71c85ac2ec580ff
heartbeat_events=15
starts=1
levels=13
completes=1
host_record_exists=True
host_heartbeat_exists=True
```

## One-cell Docker run: arbitrary UID / GID 0

Throwaway root: `outputs/docker_wp_h2_uid12345/`.

Command path: generated manifest inside the container as `--user 12345:0`, then ran the same
manifest index `61` as `--user 12345:0`.

Result:

```text
variant=evogrow_v2_2_stage_capped_pretune_on
system_id=11
ic=1
seed=42
loss=4.674e-15
pruned=true
elapsed=14.9s
record_lines=1
error_null=True
fingerprint=c71c85ac2ec580ff
heartbeat_events=15
starts=1
levels=13
completes=1
host_record_exists=True
host_heartbeat_exists=True
```

This confirms the highest-risk OpenShift permission case locally: the image can execute and write
outputs as an arbitrary non-root UID with GID 0.

## Untested until Orion

- GitLab CI build mechanics and registry push/pull.
- OpenShift image pull policy and registry authentication.
- OpenShift-assigned runtime UID value and exact security context constraints.
- Kubernetes Job manifest, completion-index mapping, and mounted output path conventions.
- Persistent volume or NFS behavior on Orion.
- Cluster-side performance, scheduling, and CPU/memory limits.
- Any production Phase B campaign execution.
