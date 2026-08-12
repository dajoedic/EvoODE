# CURRENT TASK

**Language: Docker / Shell**

## WP-H2 — A Docker image for the Orion cluster

### Why this exists

The target cluster is **not a Slurm site**. It is SCCH "Orion", an **OpenShift/Kubernetes** cluster.
`containers/evoode_regression.apptainer` and the `hpc/slurm_*.sh` scripts address a platform we do
not have access to. They stay in the repository as the Slurm-side reference, but the cluster needs
an **OCI image**, built by GitLab CI and pulled by a Kubernetes Job.

This work package produces **only the image**. No CI configuration, no Kubernetes manifest, no
index-mapping wrapper — those depend on site answers we do not have yet. Scope discipline matters
here: an image that provably runs one cell locally is the precondition for everything downstream,
and it is verifiable today without any cluster access.

### 1. The Dockerfile

Translate `containers/evoode_regression.apptainer` into a `Dockerfile`. The two definitions must
stay behaviourally equivalent; the Apptainer file is the specification, not a loose inspiration.

Carry over, section by section:

- the same base image and the same pinned Julia version
- the same thread-pinning environment, both Julia and OpenBLAS
- the same depot location baked into the image, so no compute node ever resolves packages
- the same set of copied source trees, so the ODEBench dataset and the Phase B support table travel
  with the image
- the same build-provenance record, written at build time with the same fields — it is the artifact
  that proves which dependency freeze the image contains, and it must survive the port
- the same instantiate-and-precompile step, so container start does no compilation work
- an entry point that runs one cell and exits, matching the Apptainer runscript's behaviour, so that
  arguments passed to the container reach the batch entry point unchanged

Place it where the Apptainer definition already lives. Do not start a parallel directory.

### 2. The OpenShift constraint that will otherwise bite

This is the one requirement with no Apptainer counterpart, and the most likely cause of a silent
failure later.

Apptainer runs as the invoking user. **OpenShift does not** — under its default security context it
assigns an arbitrary, unpredictable UID at pod start, with group 0. A container that assumes it runs
as `root`, or as any specific user, or that writes into a directory only writable by its build-time
owner, will fail at runtime with a permission error that looks nothing like its cause.

The image must therefore run correctly as an **arbitrary UID with GID 0**. Every path the process
reads at runtime must be readable by that UID, and every path it writes must be writable through
group 0. Apply this to the Julia depot, the source tree, and any directory the entry point creates
or writes into. Do not solve it by forcing a fixed `USER` — that is precisely what the platform
overrides.

State in the report which paths you adjusted and why.

### 3. Build context hygiene

Provide a `.dockerignore`. The build context must not carry `outputs/`, the git history, local
scratch directories, or anything else the image does not need. The repository is small, so this is
about correctness and reproducibility of the context, not about transfer time: a stray local output
directory inside the image would be a silent way to ship laptop state to the cluster.

### 4. What must be verified, locally, before this is reported done

Docker is available on the development machine. Nothing here needs a cluster.

- the image builds
- the build-provenance record inside the image reports the pinned Julia version and matches the
  committed dependency-freeze hashes, exactly as the Apptainer path required
- the manifest and per-dimension index lists can be generated **inside the container** into a mounted
  output directory, and the fingerprint printed matches the value WP-H1 established
- **one 1D cell runs to completion inside the container**, writing exactly one record with a null
  error field, plus its heartbeat, into the mounted directory
- record and heartbeat are present on the host after the container exits

Use a throwaway output location. Records from this test are technically valid and scientifically
worthless; they must never land in a campaign directory.

Pick a 1D cell. A 2D cell costs hours of CPU and proves nothing extra here.

### 5. Simulate the arbitrary-UID case

Verifying the image only as the default user does not test the constraint from §2. Run the
one-cell check a second time under an arbitrary, non-root UID with group 0, mimicking what OpenShift
will do. If that run fails while the default run succeeds, §2 is not satisfied yet.

This single check is the highest-value item in the work package — it is the failure mode that would
otherwise surface for the first time on the cluster, where it is far harder to diagnose.

### 6. Out of scope

`.gitlab-ci.yml`, any Kubernetes manifest, the mapping from a completion index to a manifest row,
NFS paths, and any change to metrics, configuration, hyperparameters or fingerprints. This work
package adds no metric and changes no number.

Do not delete or rewrite the Apptainer definition or the Slurm scripts. Do not run 2D or higher
cells. Do not touch campaign output directories.

### Report

Write `codex/REPORT_WP_H2.md`: where the Dockerfile lives, the section-by-section correspondence to
the Apptainer definition, the paths adjusted for the arbitrary-UID constraint, the results of both
local one-cell runs (default user and arbitrary UID), the fingerprint observed, and an explicit list
of what remains untested until the image runs on Orion.
