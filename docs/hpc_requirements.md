# EvoODE — HPC Resource Request

Prepared for the HPC consultation on 2026-08-06.
Contact: David Jödicke. Project: EvoODE (PhD, data-driven discovery of ODE systems).

---

## 1. The ask, in one table

| Item | Request |
|---|---|
| Workload | 846 independent single-core jobs, no inter-process communication |
| Estimated compute | **~4,500 core-hours**, uncertain by a factor of ~2 — see §5 |
| Allocation requested | **10,000 core-hours**, to absorb the uncertainty and one re-run |
| Cores per job | 1 (explicitly single-threaded, see §4) |
| Memory per job | 2 GB |
| Longest single job | ~23 h estimated (one 4D system); see §6 — this is the main open question |
| Storage | < 10 GB total, ~50 MB input |
| Software | Julia 1.12.6, exact version pinned; no MPI, no GPU, no licensed software |
| Internet at runtime | **none needed**, but see §4 — needed once at image build time |

Preferred execution model: **Slurm job arrays**, one array task per run, split into four arrays by
system dimension so that walltime limits can be set per class.

---

## 2. What the workload is

The project discovers interpretable systems of ordinary differential equations from time-series
data. A single job takes one dynamical system, one algorithm configuration and one random seed, and
runs a structure search that repeatedly fits parameters and integrates candidate models.

A job is a **pure function of its inputs**: it reads a small JSON dataset (~50 MB, read-only),
writes one JSON record plus a log, and shares nothing with any other job. There is no
communication, no shared state, no ordering constraint. Failures are per-job and do not affect
others.

This makes the workload embarrassingly parallel: throughput scales linearly with the number of
cores made available, and the job count can be partitioned arbitrarily.

### Job count

| Campaign | Jobs | Purpose |
|---|---|---|
| Phase B main experiment | 756 | 63 systems × 2 conditions × 3 seeds × 2 initial-condition sets |
| Regression baseline and failure analysis | 90 | 5 systems × 3 variants × 3 seeds × 2 initial-condition sets |
| **Total** | **846** | |

---

## 3. Resource profile per job

| Resource | Value | Basis |
|---|---|---|
| Cores | 1 | single-threaded by design; parallelism comes from the array |
| Memory | ~1 GB resident, 2 GB requested | Julia runtime plus the ODE solver stack; no large data structures |
| Disk I/O | negligible | one small JSON write at the end, one append-only log |
| Network | none | |
| Scratch | none needed | |

Per-job output is a few kilobytes. Total output across all 846 jobs, including logs, stays below
10 GB.

---

## 4. Software stack and the two things that usually go wrong

Julia 1.12.6, pinned exactly. The existing Phase A and regression results were produced on
1.12.6; the earlier 1.11.5 documentation claim was incorrect. The project ships `Project.toml`
and `Manifest.toml`, so the dependency set is fully reproducible. No MPI, no GPU, no licensed
components.

Two known failure modes we would like to discuss:

**Package installation needs the internet exactly once.** Julia resolves and downloads packages at
`Pkg.instantiate()`. Compute nodes typically have no outbound network. Our solution is a container
(Apptainer/Singularity) with the dependencies installed **and precompiled** at build time, so that
compute nodes need nothing. The definition file exists (`containers/evoode_regression.apptainer`);
it pins `julia:1.12.6-bookworm`, instantiates and precompiles in `%post`, and keeps the Julia depot
inside the image rather than on a shared filesystem. It has not been built yet — we have no
Apptainer runtime locally, which is the first thing we would like to resolve. If the site prefers a
module-provided Julia and a shared
depot instead, that works too, but the depot must be populated from a login node before the array
starts, and precompilation must happen there as well — otherwise every one of 846 jobs pays the
precompilation cost again.

**Thread oversubscription.** Julia and OpenBLAS both default to using all visible cores. With many
single-core array tasks per node this causes severe oversubscription. We set
`JULIA_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` explicitly and would like to confirm this
matches the site's expectation for array jobs.

Questions for the consultation, in the order they block us:

1. **Apptainer/Singularity available, and may we build the image ourselves?** Building needs root or
   fakeroot and outbound network. If neither is available on site, we need either a build service, a
   login node with fakeroot, or an alternative route (build elsewhere and copy the `.sif` in).
2. If containers are discouraged: is there a Julia module, at which version, and where should a
   shared depot live? It would have to be populated **and precompiled** from a login node before the
   array starts.
3. Is `--array` with a concurrency cap (`%N`) the expected pattern at this scale, and what cap is
   considered polite? 846 jobs is small in core-hours but wide in job count.
4. Any filesystem guidance for the Julia depot (many small files, read-heavy at job start)? Our
   current answer is "inside the image", which sidesteps the question — we would like to know
   whether that matches site practice.
5. Is a small pilot allocation possible ahead of the main one (§5)? It is what converts our
   estimates into measurements.

---

## 5. Where the compute estimate comes from, and how uncertain it is

**The honest position: we cannot currently produce a trustworthy runtime figure**, and this is one
reason we are here. All existing timings come from a working laptop where concurrent use, suspend
and thermal throttling leave no trace in the data. The project treats wall-clock as non-evidence by
policy and argues costs in counts instead.

What we can state precisely are the machine-independent work counts. The 1D row now comes from the
same batch entry point planned for Slurm, using the Phase B grid and the shipped regression variant
`evogrow_v2_2_stage_capped` on systems 3 and 11, initial-condition set 1, all three seeds. The
higher-dimensional rows remain pre-batch measurements and extrapolations until the pilot replaces
them. The per-fit optimizer safety budget is now **20,000 loss evaluations**. That number is based
on WP-F1/WP-F2 evaluation-sequence measurements, not extrapolation: across dimensions 1 to 3 and
parameter counts 1 to 18, the latest observed first arrival at the best loss was evaluation 5,760.
The budget is therefore a 3.5x margin over the measured worst case and twice
`2 * maxiters * (n_params + 1) = 10,000` at the campaign maximum of 24 parameters.

| System class | Parameter fits per job | ODE integrations per job |
|---|---|---|
| 1D | 110 - 290 | 1.1e4 - 5.7e5 |
| 2D | 290 - 430 | 1.2e6 - 2.4e6 |

Across the full campaign this remains on the order of **1e9 ODE integrations and ~2.7e5 parameter
fits**. The 1D batch measurement lowers the observed 1D integration range, but the total is still
dominated by 2D, 3D and 4D jobs whose timings must be calibrated on the cluster.

The core-hour estimate below is still a planning assumption, not a measurement. It converts counts
using laptop medians, keeps the 1D row as a conservative planning number until the pilot maps the
new batch counts to cluster runtime, and extrapolates the 3D and 4D classes from the 2D class. Each
of those steps carries error:

| Dimension | Systems | Jobs | Estimated s/job | Core-hours |
|---|---|---|---|---|
| 1 | 23 | 276 | 170 | 13 |
| 2 | 28 | 336 | 20,900 | 1,950 |
| 3 | 10 | 120 | 41,700 (extrapolated) | 1,390 |
| 4 | 2 | 24 | 83,500 (extrapolated) | 560 |
| **Phase B total** | **63** | **756** | | **~3,900** |
| Regression and failure analysis | 5 | 90 | | ~630 |
| **Total** | | **846** | | **~4,500** |

We regard a factor of 2 in either direction as plausible, hence the 10,000 core-hour request.

**We would like to start with a small pilot allocation** — roughly 20 jobs, ~50 core-hours — to
replace these extrapolations with measurements before committing the full campaign. That pilot
would also give this project its first reliable timing figure, which is currently missing.

---

## 6. The one thing we need site input on: walltime

The estimated runtime of a single job spans four orders of magnitude, from about 3 minutes for the
1D systems to an estimated 23 hours for the largest 4D system. Our plan is four separate arrays
with walltime limits per dimension class:

| Array | Jobs | Requested walltime per job |
|---|---|---|
| 1D | 276 | 1 h |
| 2D | 336 | 12 h |
| 3D | 120 | 24 h |
| 4D | 24 | 48 h |

If the site's maximum walltime is below the 3D or 4D figure, we need to discuss options. The
workload has no natural checkpoint today — a run is a single search that produces its result at the
end. Adding checkpointing is possible but would be a change to the scientific code, so we would
prefer to first confirm the actual runtimes in the pilot; the estimates for 3D and 4D are the
least reliable numbers in this document.

---

## 7. Reproducibility constraints we must respect

These are properties of the study, not requests, but they affect how jobs may be scheduled.

- **Every job must be deterministic given its seed.** The optimizer safety brake is a deterministic
  count budget, `max_loss_evals = 20,000` per parameter fit, not a wall-clock limit. This avoids
  node-speed-dependent results on heterogeneous hardware. Heterogeneous node types are otherwise
  unproblematic.
- **All jobs of a campaign must run from one code version.** Each job records the git commit hash
  and a configuration fingerprint; a campaign with mixed hashes is not publishable and would have
  to be re-run.
- Jobs may be scheduled in any order, restarted individually, and interleaved with other users'
  work. A failed job is simply re-submitted.

---

## 8. Timeline

The scientific method is fixed and the final algorithm variant is decided. **The port to the batch
environment is done**: a manifest enumerates the campaign as an ordered cell list, one entry point
runs exactly one cell and exits, a merge step consolidates the per-task records, and the container
definition and an example array submission script exist. Single-cell checks have been run end to end
through that path; after the WP-F3 budget change, budget-stop telemetry is expected to be part of
the campaign interpretation rather than hidden as a timing detail.

Two items remain on our side, both scheduled before access would be used: carrying the WP-F1/WP-F2
budget-stop breakdown into the campaign analysis by dimension and parameter count, and producing
pilot timing measurements on the cluster. Neither requires changing the campaign code path.

What we cannot do without access is build and run the container, and produce a single trustworthy
timing figure. We expect to be ready to run within days of receiving access, and would use a pilot
allocation immediately to firm up §5 and §6.

---

## 9. Phase B cluster bootstrap smoke runbook

This is a technical smoke test only. Use a throwaway output root, not a campaign directory.
Records from this procedure prove that the image and batch plumbing work; they are not scientific
campaign data.

Set paths on the login node:

```bash
export EVOODE_IMAGE="$PWD/containers/evoode_regression.sif"
export EVOODE_OUTPUT_ROOT="$PWD/outputs/hpc_smoke_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EVOODE_OUTPUT_ROOT" logs
```

### Step 1: build the image

```bash
apptainer build "$EVOODE_IMAGE" containers/evoode_regression.apptainer
```

Pass criterion: the command exits 0 and creates a readable `.sif`.

Failure looks like: build command fails, cannot pull `julia:1.12.6-bookworm`, fakeroot/root is
unavailable, or `Pkg.instantiate()` / `Pkg.precompile()` fails.

Meaning: the cluster cannot yet produce the frozen runtime. Resolve Apptainer permissions, network
at build time, or the Julia depot build before submitting any array job.

### Step 2: inspect build provenance inside the image

```bash
apptainer exec --cleanenv "$EVOODE_IMAGE" cat /opt/EvoODE/build_provenance.json
sha256sum Project.toml Manifest.toml
```

Pass criterion: `julia_version` is `1.12.6`, and the JSON hashes match the local committed
`Project.toml` and `Manifest.toml` SHA-256 values printed by `sha256sum`.

Failure looks like: missing `build_provenance.json`, Julia version not `1.12.6`, or either hash
differs.

Meaning: the image was built from the wrong definition, wrong source tree, or wrong dependency
freeze. Do not run cells from it.

### Step 3: generate manifest and dimension index lists inside the image

```bash
bash hpc/bootstrap_phase_b_manifest.sh
```

This binds `$EVOODE_OUTPUT_ROOT` to `/outputs` and runs:

```bash
julia --project=/opt/EvoODE /opt/EvoODE/studies/regression/generate_phase_b_manifest.jl \
    --output /outputs/manifest.csv \
    --all-dimensions
```

Pass criterion: output includes `phase_b_fingerprint=c71c85ac2ec580ff` and `rows=756`, and the bound
root contains `manifest.csv`, `indices_dim1.txt`, `indices_dim2.txt`, `indices_dim3.txt`, and
`indices_dim4.txt`.

Failure looks like: fingerprint differs, row count differs, or an index-list file is missing or
empty.

Meaning: a fingerprint mismatch means the image does not contain the code/config/support table we
think it contains. A row/list mismatch means the campaign grid is not the expected 63 systems x 2
conditions x 3 seeds x 2 IC sets.

### Step 4: submit one to three 1D smoke cells

```bash
sbatch --array=1-1 --time=01:00:00 hpc/slurm_phase_b_smoke.sh
```

Optionally use `--array=1-3` for three 1D cells. Do not use 2D or higher cells for this smoke test.

Pass criterion: each array task exits 0 and writes exactly one
`$EVOODE_OUTPUT_ROOT/tasks/cell_*.jsonl` record.

Failure looks like: Slurm stderr says the manifest or `indices_dim1.txt` is missing, Apptainer cannot
mount `/outputs`, the cell reports a fingerprint mismatch, or no task record appears.

Meaning: missing manifest/list means Step 3 did not write into the bound root. A mount/path failure
means the cluster binding command is wrong. A fingerprint mismatch means the manifest and runtime
came from different code.

### Step 5: check the record

```bash
wc -l "$EVOODE_OUTPUT_ROOT"/tasks/cell_*.jsonl
grep -L '"error":null' "$EVOODE_OUTPUT_ROOT"/tasks/cell_*.jsonl
```

Pass criterion: each record file has exactly one line, and no file is printed by `grep -L`.

Failure looks like: zero lines, more than one line, malformed JSON, or `error` is not `null`.

Meaning: zero lines means the cell did not finish writing; multiple lines means the output path was
reused incorrectly; non-null `error` means the batch entry point caught a runtime failure and the
record must not be merged.

### Step 6: check heartbeat liveness

```bash
for hb in "$EVOODE_OUTPUT_ROOT"/tasks/cell_*.heartbeat.jsonl; do
    echo "$hb"
    grep '"event":"start"' "$hb"
    grep '"event":"level"' "$hb"
    grep '"event":"complete"' "$hb"
done
```

Pass criterion: each cell heartbeat exists and contains one `start`, at least one `level`, and one
`complete` event.

Failure looks like: missing heartbeat, no `start`, no level events, or no `complete`.

Meaning: missing start means the batch cell did not enter `run_one`; missing level events means the
search did not advance far enough to prove within-run liveness; missing complete means the process
ended before the finalizer recorded the terminal state.

### Step 7: verify outputs survive container exit

```bash
ls -l "$EVOODE_OUTPUT_ROOT"/manifest.csv "$EVOODE_OUTPUT_ROOT"/indices_dim*.txt
ls -l "$EVOODE_OUTPUT_ROOT"/tasks/cell_*.jsonl "$EVOODE_OUTPUT_ROOT"/tasks/cell_*.heartbeat.jsonl
```

Pass criterion: manifest, index lists, records, and heartbeat files are visible from the login node
after all Apptainer commands have exited.

Failure looks like: files existed during the job log but are absent on the host.

Meaning: outputs were written inside the image or an unbound working directory instead of the bound
output root. Fix bind paths before any real campaign run.
