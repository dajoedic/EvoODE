# Changelog

Notable changes to the EvoODE CI/CD pipeline and its compliance status against the
[SCCH Pipeline Policy](https://gitlab.scch.at/devops_examples/devops-documentation/-/wikis/CI-CD/Pipeline-Policy).

This file exists because §11.1 of that policy requires documented exceptions to live **in the
project**. Scientific history belongs in `DIARY.md`, not here.

---

## [Unreleased]

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

### Declared limitation — security scan coverage

Not an exception, because the policy is met as written. Stated because four green jobs suggest more
coverage than exists:

| Scanned | Not scanned |
|---|---|
| Debian base layer of the campaign image (`trivy-image`) | The 80 Julia source files |
| Repository filesystem, secrets and misconfiguration (`trivy-fs`) | `Manifest.toml` and the Julia dependency graph |
| `analysis/requirements.txt`, 6 pinned packages (`python-dependency-vuln`) | |
| 43 Python files of the analysis pipeline (`bandit`) | |

The catalog offers no Julia component, and Trivy has no Julia ecosystem support. The project's
primary language is therefore covered by nothing. Reporting this to DevOps is more useful than
working around it.

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
