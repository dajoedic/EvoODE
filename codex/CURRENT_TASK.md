# CURRENT TASK

**Language: Julia**

## WP-H1 — Cluster bootstrap: from image build to one finished cell

Goal is a **technical** smoke test on the HPC, not a scientific run: does the image build, does Julia
find its frozen depot, does one cell complete, do record and heartbeat land in the bound directory.

The campaign itself is not ready — the surrogate scoring scheme for 43 of 63 systems is undefined and
will move the Phase B fingerprint once more. Records produced by this test are therefore technically
valid and scientifically worthless. That is fine, and it is exactly why they must land in a throwaway
location and never in the campaign history.

### What already exists

`containers/evoode_regression.apptainer` copies `src`, `studies` and `benchmarks` into the image, so
the ODEBench dataset and `studies/regression/phase_b_support.json` come along. Its runscript calls
`run_batch_cell.jl`, which serves both campaigns via the manifest.

`hpc/slurm_regression_array.sh` runs one cell per array task and binds an output root to `/outputs`.

### The gap

The array script expects `${EVOODE_OUTPUT_ROOT}/manifest.csv` and `indices_dim<N>.txt` to exist.
Both live under `outputs/` locally, are gitignored, and are therefore **not** in the image. Nothing
in the cluster workflow creates them.

### 1. Manifest bootstrap inside the container

Provide the step that generates the manifest and the per-dimension index lists **inside the image**,
so they are produced by the same code and the same fingerprint the cells will run under. Writing them
on a laptop and copying them up would be a silent way to run cells against a manifest from different
code.

It must write into the bound output root, not into the image.

Report the fingerprint it prints, so it can be compared against the local value
`c71c85ac2ec580ff`. A mismatch means the image does not contain the code we think it does — that is
the single most valuable check in this whole work package.

### 2. Smoke submission for a handful of cells

A submission path for **one to three cells**, not 756, writing into a throwaway output root separate
from any campaign directory.

Pick 1D cells. A 2D cell took over two hours of CPU per arm in the budget comparison and is useless
for a smoke test; system 11 completes in well under a minute locally.

Keep the existing array script intact and general. If a separate small script is cleaner than adding
flags, write a separate one.

### 3. The runbook

A short, ordered procedure from `apptainer build` to a finished record, with a **pass criterion per
step** — not prose. At minimum:

- image builds
- `build_provenance.json` inside the image reports Julia 1.12.6 and matches the committed
  `Project.toml` / `Manifest.toml` hashes (this is what WP-D1 put there; this is the moment it earns
  its keep)
- manifest generation prints `phase_b_fingerprint=c71c85ac2ec580ff` and `rows=756`
- one cell completes, writes exactly one record, `error=null`
- the heartbeat file for that cell exists and contains `start`, per-level and `complete` events
- record and heartbeat are in the bound output root and survive container exit

State for each step what failure looks like and what it would mean. A runbook that only describes
success is useless at 2 a.m. on a login node.

Put it where the HPC documentation already lives; do not start a new parallel document.

### 4. What you can verify without a cluster

Apptainer is not available here, so the build cannot be tested. Verify what can be verified:

- every file the workflow references exists at the path the image will see, given the `%files`
  section — walk it explicitly rather than assuming
- the manifest generator produces manifest and index lists into a given output root, and the index
  lists reference valid manifest rows
- one cell runs locally from a generated manifest into a throwaway directory, producing record and
  heartbeat

Say plainly which steps remain untested until the image is built.

### 5. Out of scope

WP-E3 (merge, registry, aggregation), the surrogate scoring scheme, the resource estimate, and any
change to metrics, configuration or fingerprints. This work package adds no metric and changes no
number.

Do not run 2D or higher cells. Do not touch the campaign output directories.

### Report

Write `codex/REPORT_WP_H1.md`: the bootstrap step and where it writes, the smoke submission path, the
runbook location, the local verification results, and an explicit list of what remains untested until
the image exists.
