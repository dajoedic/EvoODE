# REPORT WP-CI1

## Changes

- `containers/Dockerfile:1` changed the base image from `julia:1.12.6-bookworm` to `registry.scch.at/cache/library/julia:1.12.6-bookworm`.
- `.gitlab-ci.yml:10` changed the DinD service image from `docker:29-dind` to `registry.scch.at/cache/library/docker:29-dind`.

## Static checks

- Both changed references use the Harbor pull-through cache prefix `registry.scch.at/cache/library/`.
- The `library` namespace is present in both references, as required for official Docker Hub images.
- The Julia tag remains `1.12.6-bookworm`.
- The Docker tag remains `29-dind`.
- The GitLab service alias remains `docker`.

## Not run

- No Docker build was run.
- No `docker pull` was run.
- The next intentional GitLab push is still required to verify effective CI behavior.
