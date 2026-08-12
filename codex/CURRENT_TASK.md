# CURRENT TASK

**Language: YAML (GitLab CI)**

## WP-H3 — Build the campaign image in GitLab CI

### Why this exists

WP-H2 produced `containers/Dockerfile` and proved it locally: the image builds, carries the frozen
depot, and runs one cell correctly both as the default user and as an arbitrary UID with GID 0. What
is missing is the step that turns a commit into an image the cluster can pull.

The repository now lives in two places by design. **GitHub is the single source of truth**;
`gitlab.scch.at/joedicke/evoode` is a deploy target that receives `main`. This work package adds the
GitLab-side pipeline. It changes nothing about how the project is developed.

### 1. What the pipeline must do

One job, one purpose: build the image from `containers/Dockerfile` with the repository root as build
context, and push it to the project's own container registry.

Nothing else. No tests, no linting, no deployment to the cluster, no campaign execution. The Julia
test suite is explicitly out of scope — the project's own notes record that test execution needs
cleanup, and dragging that into the first pipeline would confuse two unrelated failure modes.

### 2. Image tags — this is the reproducibility mechanism, not a detail

Tag every built image with the **commit SHA**, using GitLab's predefined variable rather than a
hand-built string. Additionally tag with the branch or tag name for human convenience.

This matters more here than in an ordinary project. Every campaign record carries a git commit hash,
and a campaign whose jobs ran on mixed code is not publishable. If the Kubernetes Job references the
image by its commit-SHA tag, that failure mode is excluded by construction rather than by
discipline. A moving tag such as `latest` would reintroduce exactly the risk the record-keeping is
designed to prevent, so it must not be the tag the cluster consumes.

The commit SHA is identical on GitHub and GitLab, so the tag remains resolvable in the source of
truth even if institutional access is lost later.

### 3. Registry authentication — deviate from the reference here

The house reference `gitlab.scch.at/orion/dev-tutorial` logs in with a hardcoded personal username
and a personal access token stored as a CI variable. **Do not copy that.** It would make this
project's builds depend on one individual's credentials, and it puts a long-lived token where a
short-lived one suffices.

Use GitLab's built-in per-job registry credentials and the predefined registry address and image
path variables instead. They are present in every job, scoped to that job, and expire with it. No CI
variable needs to be configured by hand, which is also one less thing to document for a future
reader.

### 4. Where it runs

The instance offers two runners. Target the **CPU runner** — its own description is "slow runner for
all standard builds without special requirements", which is precisely this job. Do not target the
GPU runner: a Julia precompilation pass gains nothing from a GPU and would occupy scarce capacity.

Select it with a tag that unambiguously distinguishes the two. The reference project's `linux` tag
does not, since both runners carry it.

### 5. When it runs

Only for `main` and for git tags. Feature branches must not build.

The reason is the same as for the tag scheme: the cluster should be able to pull exactly one blessed
image per commit on the trunk, and a branch build would put images in the registry that no campaign
should ever run.

### 6. The timeout, which will otherwise bite

The image bakes a fully instantiated and precompiled Julia depot — roughly 3 GB. Locally that build
takes on the order of twenty minutes on fast hardware. On a shared runner that self-describes as
slow, it can take substantially longer.

GitLab's default job timeout is one hour. Set an explicit, generous job timeout so that a slow but
healthy build is not killed and misread as a failure. State the value chosen and the reasoning in
the report.

### 7. The one unknown, to be handled honestly

The reference pipeline invokes `docker` directly, with no Docker-in-Docker service and no explicit
daemon configuration. That implies the runner exposes a Docker daemon to the job. Follow that house
pattern rather than inventing a different one.

If the assumption is wrong, the failure is immediate and unmistakable — the build cannot reach a
Docker daemon on the first pipeline run. Record in the report what that failure would look like and
what the alternative configuration would be, so the first red pipeline is diagnosable without a
research detour.

### 8. What can and cannot be verified here

This is the first work package whose result cannot be fully verified locally: a pipeline only proves
itself by running. Verify what is verifiable — that the file is syntactically valid GitLab CI, that
the Dockerfile path and build context match what WP-H2 established and what already builds locally,
and that no variable is referenced that the instance would not provide automatically.

Then stop. Do not push to trigger a pipeline; the user drives pushes.

### 9. Out of scope

The Kubernetes Job manifest, the mapping from completion index to manifest row, NFS paths, pull
secrets on the cluster side, and any change to metrics, configuration, hyperparameters or
fingerprints. This work package adds no metric and changes no number, and it must not modify
`containers/Dockerfile`.

Leave the Apptainer definition and the Slurm scripts untouched.

### Report

Write `codex/REPORT_WP_H3.md`: the pipeline file and its location, the tagging scheme and which
predefined variables it rests on, the authentication approach and why it departs from the house
reference, the runner selection, the timeout chosen and its justification, the syntax-validation
result, and an explicit list of what only the first real pipeline run can establish — including the
Docker-daemon assumption from §7 and what its failure would look like.
