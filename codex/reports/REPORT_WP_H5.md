# WP-H5 Report - portable Julia precompile cache

## Setting

`containers/Dockerfile` now sets:

```dockerfile
JULIA_CPU_TARGET="generic;znver3,clone_all"
```

It is in the `ENV` block before the build `RUN` step that executes:

```dockerfile
julia --project=. -e 'import Pkg; Pkg.instantiate(); Pkg.precompile()'
```

That means the setting is active while Julia writes the baked package images to
`/opt/julia_depot/compiled`. Because it remains in `ENV`, runtime Julia processes see the same CPU
target setting as the build step that produced the cache.

## Why this target specification

Julia documents `JULIA_CPU_TARGET` as the control for CPU targets used when writing system and
package images to disk cache. Multi-target strings are separated by semicolons.

Chosen targets:

- `generic`: portable x86_64 baseline so the image is still usable away from Orion.
- `znver3,clone_all`: AMD Zen 3 target for Orion's EPYC 7643 nodes, with full cloning for the
  cluster target.

This avoids the previous accidental `icelake-server` cache created by the Intel GitLab runner while
also avoiding an image that only works on the cluster microarchitecture.

Reference: Julia manual, `JULIA_CPU_TARGET` environment variable:
https://docs.julialang.org/en/v1/manual/environment-variables/#JULIA_CPU_TARGET

## Build result

Local image:

```text
evoode-regression:h5
image_id=sha256:109e0b7e07d4f8c2601f3c7f6280987ec37c6e48d6645ff4a6424712c0621b73
```

Build observation:

```text
first build client attempt: timed out at 1804s
follow-up build command: build_seconds=151.9
BuildKit precompile log: 554 dependencies successfully precompiled in 1553s
BuildKit RUN step: 1771.4s
```

The first client timeout did not produce a tagged image, but BuildKit retained completed work. The
second command exported the image quickly from that state. For CI planning, the conservative number
is the BuildKit precompile/RUN timing, not the second client wall time.

Image size:

```text
before WP-H5: evoode-regression:h2 5.72GB
after WP-H5:  evoode-regression:h5 5.95GB
increase:     about 0.23GB
```

Depot/cache size inside the WP-H5 image:

```text
/opt/julia_depot/compiled/v1.12  1.5G
/opt/julia_depot/packages        281M
/opt/julia_depot/artifacts       1.5G
```

## Local verification

Runtime environment inside the image contains:

```text
JULIA_CPU_TARGET=generic;znver3,clone_all
JULIA_DEPOT_PATH=/opt/julia_depot
JULIA_VERSION=1.12.6
```

The compiled package-image cache is present:

```text
/opt/julia_depot/compiled/v1.12: 1160 files
```

Target strings in baked package-image shared objects:

```text
generic_so=580
znver3_so=580
```

This confirms that the baked cache records more than one CPU target.

Local loader-debug smoke:

```bash
docker run --rm -e JULIA_DEBUG=loading --entrypoint julia evoode-regression:h5 \
  --startup-file=no --project=/opt/EvoODE -e "using JSON3"
```

Result: exit 0. Julia printed `Loading object cache file ...` lines for package images and no
`Rejecting cache file` messages on the local CPU.

## Decisive Orion check

The decisive check cannot be performed locally. The original defect only appears when the image is
built on one CPU family and run on Orion's AMD Zen 3 nodes.

After the next CI build pushes a commit-SHA-tagged image, run one short pod on Orion with loader
debugging enabled:

```bash
COMMIT_SHA=<exact commit sha>
kubectl -n scch-das run evoode-cache-check \
  --rm -i --restart=Never \
  --image=registry.gitlab.scch.at:443/joedicke/evoode:${COMMIT_SHA} \
  --overrides='{
    "spec": {
      "imagePullSecrets": [{"name": "evoode-gitlab-pull"}],
      "containers": [{
        "name": "evoode-cache-check",
        "image": "registry.gitlab.scch.at:443/joedicke/evoode:'"${COMMIT_SHA}"'",
        "env": [
          {"name": "JULIA_DEBUG", "value": "loading"},
          {"name": "JULIA_NUM_THREADS", "value": "1"},
          {"name": "OPENBLAS_NUM_THREADS", "value": "1"}
        ],
        "command": [
          "julia",
          "--startup-file=no",
          "--project=/opt/EvoODE",
          "-e",
          "using JSON3; println(\"cache_check_done\")"
        ],
        "resources": {
          "requests": {"cpu": "1", "memory": "2Gi"},
          "limits": {"cpu": "1", "memory": "2Gi"}
        }
      }]
    }
  }'
```

Pass criterion:

- The pod starts and exits 0.
- Logs show `cache_check_done`.
- Loader debug shows `Loading object cache file ...` for dependencies.
- Logs do not contain `Rejecting cache file` or `Unable to find compatible target`.
- Runtime is seconds, not tens of minutes.

Failure shape:

```text
Rejecting cache file ... Unable to find compatible target in cached code image
```

or a long first-load recompilation pause. That would mean the cache is still not accepted on Orion
and the CPU target string needs another adjustment before any smoke Job or pilot timing run.

## Out-of-scope observation

The same Orion run also showed that manifest bootstrap was killed under a 2 GiB memory limit and
needed 8 GiB. That is a Kubernetes manifest resource value, not an image/cache issue, and was
deliberately not changed in WP-H5.

## Untested until Orion

- Whether Orion's `znver3` nodes accept the baked cache.
- Whether the next GitLab CI build time remains within the configured 3-hour timeout.
- Whether the pushed registry image has the same target-bearing cache as the local `h5` image.
- Any Kubernetes manifest memory adjustment for bootstrap.
- Any campaign, pilot, merge, aggregation, metric, configuration, hyperparameter, or fingerprint
  behavior.
