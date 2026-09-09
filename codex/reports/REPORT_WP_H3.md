# WP-H3 Report - GitLab CI campaign image build

## Pipeline file

Added `.gitlab-ci.yml` at the repository root.

It defines one job:

```text
build_campaign_image
```

The job builds `containers/Dockerfile` with the repository root as context:

```bash
docker build --pull -f containers/Dockerfile \
  -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA" \
  -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG" \
  .
```

It then pushes both tags to the project container registry. No tests, linting, deployment, or
campaign execution were added.

## Tagging scheme

Each image is tagged twice:

- Reproducibility tag: `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA`
- Human convenience tag: `$CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG`

Predefined variables used:

- `CI_REGISTRY_IMAGE`: project registry image path.
- `CI_COMMIT_SHA`: exact commit SHA; this is the tag Kubernetes campaign jobs should consume.
- `CI_COMMIT_REF_SLUG`: GitLab-safe branch or tag name for human lookup.

No `latest` tag is produced. The SHA tag is the reproducibility mechanism: a Kubernetes Job pinned
to that tag cannot silently move to another commit.

## Registry authentication

The job uses GitLab's built-in per-job registry credentials:

```bash
docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" "$CI_REGISTRY"
```

Predefined variables used:

- `CI_REGISTRY_USER`
- `CI_REGISTRY_PASSWORD`
- `CI_REGISTRY`

This deliberately departs from the house reference that uses a personal username and long-lived
personal access token. The CI job token is short-lived, scoped to the job, automatically available,
and requires no manually configured project secret.

## Runner selection

The job selects the CPU runner with:

```yaml
tags:
  - cpu
```

This avoids the ambiguous `linux` tag mentioned in the task, since both available runners carry it.
The build is CPU-only Julia package instantiation/precompilation work and should not occupy the GPU
runner.

The first real pipeline run will also establish that `cpu` is the exact tag registered on the SCCH
instance for the CPU runner. If it is not, the job will remain pending with a runner/tag matching
message rather than failing during the build.

## When it runs

Rules restrict the job to `main` and Git tags:

```yaml
rules:
  - if: '$CI_COMMIT_BRANCH == "main"'
  - if: '$CI_COMMIT_TAG'
  - when: never
```

Feature branches do not build images. This keeps the registry aligned with trunk commits and
release tags only.

## Timeout

The job timeout is:

```yaml
timeout: 3 hours
```

Reasoning: WP-H2 showed that the image bakes the full Julia depot and precompiles the project. That
took roughly twenty minutes locally on fast hardware; the target runner self-describes as slow. A
three-hour timeout is generous enough for a healthy slow build while still bounding stuck downloads,
registry problems, or pathological precompile hangs.

## Docker daemon assumption

The pipeline follows the house pattern: it invokes `docker` directly and defines no Docker-in-Docker
service and no explicit daemon configuration.

Assumption: the CPU runner exposes a Docker daemon to the job.

If this assumption is wrong, the first pipeline will fail immediately at `docker login` or
`docker build` with an error like:

```text
Cannot connect to the Docker daemon
```

or an unavailable `/var/run/docker.sock` / Docker host message.

The alternative would be a runner-specific Docker-in-Docker or BuildKit/Kaniko configuration, but
that is intentionally not introduced until the house-pattern assumption is disproved by the actual
GitLab runner.

## Local validation

Validated locally:

```text
yaml_ok
```

The validation used Python/PyYAML to parse `.gitlab-ci.yml`.

Additional static checks:

```text
has_dockerfile_path=True
has_root_context=True
no_latest=True
no_dind=True
CI_REGISTRY_USER=True
CI_REGISTRY_PASSWORD=True
CI_REGISTRY=True
CI_REGISTRY_IMAGE=True
CI_COMMIT_SHA=True
CI_COMMIT_REF_SLUG=True
CI_COMMIT_BRANCH=True
CI_COMMIT_TAG=True
```

`containers/Dockerfile`, the Apptainer definition, and the Slurm scripts were not modified.

## Untested until the first real GitLab pipeline run

- Whether `cpu` is the exact tag that selects the CPU runner on `gitlab.scch.at`.
- Whether the CPU runner exposes a usable Docker daemon without Docker-in-Docker.
- Whether the runner can pull `docker:29-cli` and `julia:1.12.6-bookworm`.
- Whether the runner can push to `$CI_REGISTRY_IMAGE` with GitLab's job-scoped registry credentials.
- Whether the project registry path and permissions are enabled for `gitlab.scch.at/joedicke/evoode`.
- The final pushed image digests in the GitLab registry.
- Any later Orion pull-secret, Kubernetes Job, NFS, or completion-index behavior.
