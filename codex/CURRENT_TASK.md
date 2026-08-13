# CURRENT TASK

**Language: Docker**

## WP-H5 — Make the baked precompilation cache usable on the cluster

### The defect, measured on Orion

The image bakes a 3.1 GB Julia depot with 1.3 GB of precompiled code, exactly as intended. On the
cluster, Julia discards all of it and recompiles the entire dependency stack at pod start — several
tens of minutes, single-threaded, **per pod**.

The cause is not configuration. `JULIA_DEPOT_PATH` is set correctly, `DEPOT_PATH` resolves to the
baked depot, and the cache is present and the expected size. Julia's own loader states the reason:

```text
Rejecting cache file .../compiled/v1.12/Logging/....ji
Reasons = "Unable to find compatible target in cached code image.
           Target 0 (icelake-server): Rejecting this target due to
           use of runtime-disabled features"
(cache misses: target mismatch (1))
```

The GitLab CI runner is an Intel machine and precompiles for `icelake-server`. The Orion worker
nodes are AMD EPYC 7643, reported by Julia as `znver3`. Julia's precompiled images contain native
code and are validated against the running CPU's feature set, so every cache file is rejected.

This was invisible until now because WP-H2 built and ran the image on the same laptop CPU. Local
verification cannot detect it by construction; it appears only once build host and run host differ.

### Why it must be fixed before anything is scaled up

Every one of the 756 campaign cells would pay this cost. For the 1D cells, which compute in seconds,
the recompilation would dominate the runtime by orders of magnitude — the campaign would spend more
CPU warming up than computing.

It would also corrupt the pilot measurement that the whole cost model depends on. `docs/hpc_requirements.md`
states the project has no trustworthy timing figure yet and that the pilot must produce one. A pilot
run under this defect would measure compilation, not discovery.

### What to change

Instruct Julia at **image build time** to generate precompiled code for a CPU target that the Orion
nodes can actually use, rather than for whatever the build machine happens to be.

Requirements:

- The setting must be in effect **before** the instantiate-and-precompile step, so that the baked
  cache is generated for the intended targets. Setting it only at runtime would not fix the cache
  that is already in the image.
- It must remain part of the image environment, so the running process selects the same target it
  was compiled for.
- Choose a **multi-target** specification: a portable generic baseline plus a variant optimised for
  the Zen 3 microarchitecture of the EPYC 7643. Do not pin exclusively to the cluster's CPU — the
  image is also built and occasionally run elsewhere, and an image that only works on one
  microarchitecture reintroduces the same class of failure in the other direction.
- Consult Julia's documented convention for such specifications rather than inventing one; this is
  the mechanism Julia itself uses to ship portable binaries.

Expect the image to grow, because it now carries code for more than one target, and expect the CI
build to take longer for the same reason. Both are acceptable: they are paid once per commit, against
tens of minutes saved per pod.

### Verification

Locally, confirm that the build still succeeds and that the baked cache is present and now records
more than one target.

State plainly in the report that the **decisive** check cannot be performed locally: only a pod on an
Orion node can confirm that the cache is accepted. Describe exactly what that check is, so it can be
run immediately after the next CI build — it is a single short pod that loads one package with
Julia's loader debugging enabled and shows either a rejection or a silent, fast load.

Do not apply anything to the cluster and do not run the campaign.

### Out of scope

The Kubernetes manifests, the index mapping, the manifest generator, resource limits, and any change
to metrics, configuration, hyperparameters or fingerprints. This work package changes how code is
compiled, never what is computed — the numerical results must be identical.

Note for the report: a separate observation from the same run is that the manifest bootstrap was
killed at a 2 GiB memory limit and needed 8 GiB. That is a manifest-side value, not an image
concern, and is deliberately not part of this work package.

### Report

Write `codex/REPORT_WP_H5.md`: the setting used and why that specification, where it sits relative to
the precompilation step, the observed effect on image size and build time, the local verification
result, and the exact cluster-side check that must follow the next CI build.
