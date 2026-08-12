# WP-H1 Report - Cluster bootstrap smoke path

## Bootstrap step

Added `hpc/bootstrap_phase_b_manifest.sh`.

It requires:

```bash
export EVOODE_IMAGE=/path/to/evoode_regression.sif
export EVOODE_OUTPUT_ROOT=/path/to/throwaway/output/root
bash hpc/bootstrap_phase_b_manifest.sh
```

The script binds `${EVOODE_OUTPUT_ROOT}` to `/outputs` and runs the manifest generator inside the
image:

```bash
julia --project=/opt/EvoODE /opt/EvoODE/studies/regression/generate_phase_b_manifest.jl \
    --output /outputs/manifest.csv \
    --all-dimensions
```

It writes `manifest.csv` and `indices_dim1.txt` through `indices_dim4.txt` into the bound output
root, not into the image.

`studies/regression/generate_phase_b_manifest.jl` now supports `--all-dimensions`, while preserving
the existing `--dimension N --index-output PATH` path.

## Smoke submission path

Added `hpc/slurm_phase_b_smoke.sh`.

Submit one to three 1D cells only:

```bash
export EVOODE_IMAGE=/path/to/evoode_regression.sif
export EVOODE_OUTPUT_ROOT=/path/to/throwaway/output/root
sbatch --array=1-1 --time=01:00:00 hpc/slurm_phase_b_smoke.sh
# or, at most:
sbatch --array=1-3 --time=01:00:00 hpc/slurm_phase_b_smoke.sh
```

The general `hpc/slurm_regression_array.sh` remains unchanged.

## Runbook location

The ordered runbook was added to `docs/hpc_requirements.md`, section 9:
`Phase B cluster bootstrap smoke runbook`.

It includes pass criteria, failure shape, and interpretation for image build, image provenance,
manifest bootstrap, 1D smoke submission, record inspection, heartbeat inspection, and host-side
output persistence.

## Local verification

Apptainer is not available locally, so image build and container execution were not tested.

Verified local file presence for every runtime path that the image sees through `%files`:

- `Project.toml`
- `Manifest.toml`
- `src/`
- `studies/`
- `benchmarks/`
- `studies/regression/run_batch_cell.jl`
- `studies/regression/generate_phase_b_manifest.jl`
- `studies/regression/phase_b_config.jl`
- `studies/regression/phase_b_support.json`
- `benchmarks/data/strogatz_extended.json`

Generated the Phase B manifest locally into `outputs/smoke_wp_h1/`:

```text
phase_b_fingerprint=c71c85ac2ec580ff
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

Validated all dimension index lists against the generated manifest:

```text
indices_dim1.txt: rows=276 bad=0
indices_dim2.txt: rows=336 bad=0
indices_dim3.txt: rows=120 bad=0
indices_dim4.txt: rows=24 bad=0
```

Ran one local 1D cell from that generated manifest:

```text
index=61
system_id=11
variant=evogrow_v2_2_stage_capped_pretune_on
ic=1
seed=42
loss=4.276e-15
pruned=true
elapsed=41.5s
record=outputs/smoke_wp_h1/tasks/cell_000061.jsonl
```

Record verification:

```text
records=1
error_is_null=True
manifest_index=61
system_id=11
config_fingerprint=c71c85ac2ec580ff
```

Heartbeat verification:

```text
heartbeat_events=15
events=start,level,level,level,level,level,level,level,level,level,level,level,level,level,complete
starts=1
levels=13
completes=1
complete_error=null
```

## Untested until the image exists

- `apptainer build` itself.
- Network/fakeroot availability during the image build on the cluster.
- Julia depot installation and precompilation inside the image.
- `/opt/EvoODE/build_provenance.json` inside the built image.
- Hash comparison between image provenance and the committed `Project.toml` / `Manifest.toml`.
- Container-side manifest generation through `hpc/bootstrap_phase_b_manifest.sh`.
- Slurm submission through `hpc/slurm_phase_b_smoke.sh`.
- Apptainer bind behavior from the cluster filesystem to `/outputs`.
- Host-side survival of files written from inside the container.
