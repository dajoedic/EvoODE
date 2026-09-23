# Changelog

Notable changes to the EvoODE CI/CD pipeline and its compliance status against the
[SCCH Pipeline Policy](https://gitlab.scch.at/devops_examples/devops-documentation/-/wikis/CI-CD/Pipeline-Policy).

This file exists because §11.1 of that policy requires documented exceptions to live **in the
project**. Scientific history belongs in `DIARY.md`, not here.

---

## [Unreleased]

### Fixed — 2026-09-23

- `baselines/Dockerfile.dockerignore` added. The root `.dockerignore` is an allowlist for the Julia
  campaign image and excludes `baselines/`, so `docker build -f baselines/Dockerfile .` failed on its
  first `COPY` — **the baseline image could never be built.** BuildKit reads a
  `<Dockerfile>.dockerignore` next to the Dockerfile in place of the root file; the new one allowlists
  `baselines/`, `analysis/` and `benchmarks/data/`, which is what the harness imports and reads.
  Verified locally: the build context loads and the build reaches `pip install`. The trajectory
  export stays under the gitignored `outputs/` and is mounted at run time, never baked in.

### Changed — 2026-09-23

- The CI service image is pinned by digest:
  `registry.scch.at/cache/library/docker:29-dind@sha256:5efed980cba3fc126cf54e21a5a6ff8849d05b6e0623d6e7612f48e9cd6cd17e`.
  This closes the follow-up named under *Fixed — 2026-09-22*: the floating tag was the underlying
  defect. The digest is the one pipeline #8379 (`5a87efb`) pulled and built successfully with, read
  from that job's service log. It is **not** the version that built `221a3a7`. That version was
  never established, and the attestation flags stay because they are harmless under either version.
  A future upgrade is a deliberate change of this line, recorded here.

### Fixed — 2026-09-22

- `build_campaign_image` no longer attaches build attestations: `--provenance=false --sbom=false`
  on `docker build`, plus `BUILDX_NO_DEFAULT_ATTESTATIONS: "1"` in the job variables.

  **Symptom.** The build itself succeeded — 554 packages precompiled in 1,687 s, image exported and
  named — and every layer pushed. Only the final manifest failed, with
  `error from registry: blob unknown to registry - sha256:651d95e6…`. The tag therefore never
  resolved, and pods referencing it stayed in `ImagePullBackOff` reporting `manifest unknown`.

  **Cause.** Two lines above the push, BuildKit reports `exporting attestation manifest` and
  `exporting manifest list`: the default provenance attestation turns the result into an OCI image
  index, which this registry does not accept. Nothing in the project changed — the build step is
  `Pkg.instantiate(); Pkg.precompile()` against unchanged `Project.toml` and `Manifest.toml`.

  **Why it worked before.** The service image is pinned to the floating tag
  `registry.scch.at/cache/library/docker:29-dind`, recorded under *Changed — 2026-09-15* below.
  A patch-level move of that tag enabled attestations by default. **The floating tag is the
  underlying defect; this entry fixes the symptom.** Pinning the service image to an exact version
  is the follow-up, and it needs the version that last built successfully (commit `221a3a7`,
  2026-09-14) to be established first.

### Added — 2026-09-15

- `workflow: rules` — the pipeline now answers only branch pushes, tag pushes and manual runs from
  the UI. Scheduled pipelines, the pipelines API and trigger tokens are rejected before any job is
  created (§4).
- Four non-blocking security jobs in a new `security` stage (§5.1), composed from catalog
  components at pinned versions (§10.1, §10.2): `security/trivy-fs@v3.2.0`,
  `security/trivy-image@v3.2.0`, `python/dependency-vuln@v3.3.3`, `security/bandit@v3.2.0`.
  All four run with `allow-failure: true`.

### Changed — 2026-09-15

- Base images are pulled through the SCCH Harbor cache instead of Docker Hub (§9.1):
  `registry.scch.at/cache/library/julia:1.12.6-bookworm` in `containers/Dockerfile` and
  `registry.scch.at/cache/library/docker:29-dind` as the CI service image. Versions unchanged —
  this is a change of source, not an upgrade.

  Measured before the change: the cache answers **anonymously** for both images (HTTP 200), so no
  Harbor robot account and no `HARBOR_*` variables are needed. The wiki suggests otherwise, which
  is a documentation gap worth reporting to DevOps rather than a blocker.

---

## Pipeline Policy — Compliance Status

Assessed 2026-09-15 against the policy revision of 2026-09-02. The policy itself states in §1.1
that it describes a target state whose enforcement is armed in stages through mid-2027.

### Not applicable

These requirements hang off a release flow this project does not have. They are **out of scope**,
not deviated from, and need no exception:

| Requirement | Why it does not apply |
|---|---|
| §8.1 Harbor push | Harbor is mandatory for customer-facing and production images. The campaign image is internal research compute, executed on the Orion cluster and consumed by nobody outside the project. §8.2 makes the GitLab Container Registry the correct destination for exactly this case. |
| §7.4 SBOM, §7.5 release asset links | Both are properties of a GitLab Release. The project publishes no releases. |
| §7.1 version from `setuptools-scm` | No package is published. |
| §8.3 manual Harbor promotion | Follows from §8.1 not applying. |

### Exceptions under §11.1

Each states the requirement, the reason, and what compensates. **Time limit: 30 days. Review due
2026-10-15**, after which each is either resolved or consciously renewed.

**E1 — §3.1: no Git Flow, direct pushes to `main`.**
The policy requires `main` and `develop` to be protected with merges only via Merge Request. This
repository has only `main`, and commits land on it directly.
*Reason:* single-researcher project with an AI-assisted workflow. Changes are specified, executed
and reviewed before the commit is written; a Merge Request with one participant adds ceremony, not
review.
*Compensating:* every commit is mirrored to GitHub, which is the project's single source of truth
and carries the full auditable history. GitLab is a deploy target only.

**E2 — §4 and §6: no Merge Request pipeline.**
Follows directly from E1. Merge request events are not allowed in `workflow: rules`.
*Reason:* with no MR workflow, allowing the trigger would create pipelines containing no jobs,
because the only build job is bound to `main`.
*Compensating:* none, and none is claimed. If the project ever gains a second contributor, E1 and
E2 must be revisited together.

**E3 — §9.2: single-stage Dockerfile, no `USER` directive.**
The policy requires a multi-stage build whose runtime stage runs as a non-root user with a fixed
UID.
*Reason:* the image carries a precompiled Julia depot; splitting builder and runtime stages without
losing the precompilation is non-trivial, and the Phase C campaign is currently running against
this image. Deferred deliberately rather than rushed.
*Compensating:* the image is prepared for OpenShift's arbitrary-UID model — `chgrp -R 0` and
`chmod -R g=u` on all writable paths — so on the Orion cluster the container does **not** in fact
run as root, regardless of the missing `USER` directive. This is mitigation, not compliance: a
local `docker run` would still run as root.

**E4 — §10.1: hand-written image build instead of `docker/build-push`.**
The policy forbids custom inline scripting for capabilities an existing component covers.
*Reason:* the build passes `EVOODE_GIT_SHA` as a build argument so the image can report its own
source revision at runtime, and needs a three-hour timeout for Julia precompilation. Whether the
component supports both has not been checked.
*Compensating:* the inline script is three commands — login, build, push — with no bespoke logic.
*Action before renewal:* check `docker/build-push@v3.4.0` for build-argument support.

**E5 — §5.1: no lint job, no test job.**
Both are *recommended*, not mandatory. The repository has Julia tests under `test/` and a Python
analysis pipeline, and CI runs neither.
*Reason:* Julia tests are run per file; there is no `runtests.jl` aggregating them, which is a known
gap recorded in `CLAUDE.md`.
*Compensating:* none. This is the weakest item on the list and the most likely to be resolved
first.

**E6 — §5.1: `trivy-fs` and `trivy-image` report HIGH/CRITICAL findings that are not remediated.**
Both jobs failed in pipeline #8379 (`5a87efb`) for the first time with real results. They run
`allow-failure: true`, so the pipeline stays green. Inventory reproduced locally on 2026-09-23
with the same scanner (`aquasec/trivy:0.71.2`, `--severity HIGH,CRITICAL`):

| Job | Findings | Source | Fixable now? |
|---|---|---|---|
| `trivy-fs` | 109 in `Manifest.toml`, 13 packages | Julia binary packages (`*_jll`), see below | no — requires changing the frozen campaign environment |
| `trivy-fs` | torch 2.0.0 in `baselines/requirements.txt` (1 CRITICAL, several HIGH) | pin for the ODEFormer baseline | blocked, see below |
| `trivy-image` | 72 in the Debian 12.15 layer | base image `julia:1.12.6-bookworm` | 5 of 72 have a Debian fix |
| `trivy-image` | 88 in Julia's own shipped test and doc `Manifest.toml` files | the official Julia image, not this project | no — upstream content |
| `trivy-image` | the Julia depot of the image, presumably the same 109 as `trivy-fs` | `Pkg.instantiate()` against `Manifest.toml` | no — as for `trivy-fs` |

The 109 Julia findings have two sources. **The plotting stack:** `Plots` and `CairoMakie` are
direct dependencies in `Project.toml` and pull in `FFMPEG_jll`, `Glib_jll`, `HarfBuzz_jll`,
`OpenEXR_jll`, `libpng_jll`, `Giflib_jll` and `Expat_jll` — most of the findings, in code that the
campaign never executes. **Julia's standard library:** `OpenSSL_jll`, `LibCURL_jll`,
`LibSSH2_jll`, `LibGit2_jll`, `MbedTLS_jll` and `nghttp2_jll` are bound to the Julia version; 3
`MbedTLS_jll` findings have no fix at all.

*Reason:* every remediation changes the image the Phase C campaign and WP-T1d run on. Records are
reproducible because each names the one image it ran in; changing that environment mid-campaign
breaks the identity the results depend on. The torch pin cannot be raised on its own either: every
torch release that clears the HIGH findings (≥ 2.10) requires `sympy ≥ 1.13.3`, while the pinned
ODEFormer commit requires exactly `sympy==1.11.1`.
*Compensating:* the image runs isolated batch compute on an internal cluster. It exposes no
service, accepts no untrusted input, and makes no outbound request during a run. The baseline
image, which carries torch, has never been built or deployed.
*Action, after the campaign ends and with the planned namespace move:* move `Plots` and
`CairoMakie` out of the compute environment into a separate plotting environment; raise Julia to
the current 1.12 patch release; add `apt-get upgrade` for the five fixable Debian packages; then
rescan. This produces a new image identity, which is why it waits. The torch/sympy conflict is
resolved inside the ODEFormer baseline work package, whose acceptance requires ODEFormer to load
its weights under torch ≥ 2.10 and to reproduce, on a test system, the result it gives under
`sympy==1.11.1`.

### Declared limitation — security scan coverage

Not an exception, because the policy is met as written. Stated because four green jobs suggest more
coverage than exists:

| Scanned for vulnerabilities | Listed but not scanned | Not covered |
|---|---|---|
| Debian base layer of the image (`trivy-image`) | | The 80 Julia source files: no SAST exists for Julia |
| Julia binary packages (`*_jll`) in `Manifest.toml` and in the image's depot (`trivy-fs`, `trivy-image`) | | Pure-Julia packages: see below |
| `analysis/requirements.txt`, 6 pinned packages (`python-dependency-vuln`) | | |
| `baselines/requirements.txt` (`trivy-fs` only — `python-dependency-vuln` reads `analysis/` alone) | | |
| 43 Python files of the analysis pipeline (`bandit`) | | |
| Repository secrets and misconfiguration (`trivy-fs`) | | |

**Corrected 2026-09-23.** This section said until then that no vulnerability advisory database
exists for Julia and that no scanner can report Julia package vulnerabilities. That was wrong by
the time the scans first ran: Trivy 0.71.2 reports advisories for Julia's binary wrapper packages
(`*_jll`), which ship C libraries such as OpenSSL, libcurl and libpng, and it found 109 of them in
`Manifest.toml` (E6). What remains uncovered is **pure-Julia package code** and the project's own
Julia sources — for those, the ecosystem-gap reasoning below still holds.

The defensible position for any audit is therefore: everything that can be scanned is scanned,
the binary layer is scanned and its findings are inventoried under E6, and the pure-Julia layer has
no advisory source. That last part needs no DevOps ticket — there is nothing for them to fix.

Residual risk is low for a second reason worth stating: the image runs isolated batch compute on an
internal cluster. It exposes no service, accepts no untrusted input, and is reachable from nothing.

### Open questions for DevOps

Neither blocks anything; both are service desk questions, not approval requests.

1. **Registry retention.** `Container-Registries` states that images tagged only with a commit hash
   are deleted after 14 days with no per-project opt-out. The project's registry reports
   *cleanup disabled*. Which applies?
2. **Cache access without Harbor credentials.** §9.1 makes the cache mandatory; `CI-Variables`
   states that projects not releasing to Harbor need no Harbor credentials. For such a project the
   two read as contradictory. Anonymous access works today — is that intended and stable?

### Not adopted from the reference implementation

`python-example` sets `tags: ["fast"]` on every job. Per `CI-CD/Basics-and-Runners` that is the GPU
runner, and the same page says to use it only when the job genuinely requires GPU hardware. All
EvoODE jobs use `cpu`.
