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
| Software | Julia 1.11.5, exact version pinned; no MPI, no GPU, no licensed software |
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

Julia 1.11.5, pinned exactly. The project ships `Project.toml` and `Manifest.toml`, so the
dependency set is fully reproducible. No MPI, no GPU, no licensed components.

Two known failure modes we would like to discuss:

**Package installation needs the internet exactly once.** Julia resolves and downloads packages at
`Pkg.instantiate()`. Compute nodes typically have no outbound network. Our solution is a container
(Apptainer/Singularity) with the dependencies installed **and precompiled** at build time, so that
compute nodes need nothing. The definition file exists (`containers/evoode_regression.apptainer`);
it pins `julia:1.11.5-bookworm`, instantiates and precompiles in `%post`, and keeps the Julia depot
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

What we can state precisely are the machine-independent work counts, measured on the current
sampling grid:

| System class | Parameter fits per job | ODE integrations per job |
|---|---|---|
| 1D | 170 – 270 | 9e3 – 1.2e6 |
| 2D | 290 – 430 | 1.2e6 – 2.4e6 |

Across the full campaign this is on the order of **1e9 ODE integrations and ~2.7e5 parameter
fits**.

The core-hour estimate below converts those counts using laptop medians, scales by 2.56 for the
denser sampling grid Phase B will use, and extrapolates the 3D and 4D classes from the 2D class.
Each of those three steps carries error:

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

- **Every job must be deterministic given its seed.** The code currently contains one wall-clock
  dependency: the optimizer carries a 1800 s time limit per parameter fit. It has never been hit in
  any recorded run, but on heterogeneous nodes it could bind on a slow node and not on a fast one,
  which would make results node-dependent. This will be replaced by an evaluation budget before the
  campaign runs. Heterogeneous node types are otherwise unproblematic.
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
definition and an example array submission script exist. A single cell has been verified end to end
through that path and reproduces the previously measured result exactly.

Two items remain on our side, both scheduled before access would be used: replacing the optimizer's
wall-clock limit with a deterministic budget (§7), and measuring the 1D cost class instead of
scaling it (§5). Neither requires cluster access.

What we cannot do without access is build and run the container, and produce a single trustworthy
timing figure. We expect to be ready to run within days of receiving access, and would use a pilot
allocation immediately to firm up §5 and §6.
