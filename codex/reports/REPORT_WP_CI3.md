# REPORT WP-CI3

## Scope

Updated `.gitlab-ci.yml` only.

No build, GitLab pipeline, campaign run, cluster job, or push was started. The security jobs become
observable only on the next deliberate GitLab push or tag pipeline.

## Static acceptance checks

Python parsed `.gitlab-ci.yml` as valid YAML.

`stages` is exactly:

```yaml
- build
- security
```

The top-level `include` section contains exactly 4 component entries:

| Component | Version | Pinned | `@~latest` |
|---|---:|---:|---:|
| `$CI_SERVER_FQDN/devops_examples/components/security/trivy-fs@v3.2.0` | `v3.2.0` | yes | no |
| `$CI_SERVER_FQDN/devops_examples/components/security/trivy-image@v3.2.0` | `v3.2.0` | yes | no |
| `$CI_SERVER_FQDN/devops_examples/components/python/dependency-vuln@v3.3.3` | `v3.3.3` | yes | no |
| `$CI_SERVER_FQDN/devops_examples/components/security/bandit@v3.2.0` | `v3.2.0` | yes | no |

The `workflow` block is character-identical to the previous state.

The `build_campaign_image` block is character-identical to the previous state.

All four security jobs define the same `rules` sequence as `build_campaign_image`:

```yaml
- if: '$CI_COMMIT_BRANCH == "main"'
- if: '$CI_COMMIT_TAG'
- when: never
```

`trivy-image` additionally declares:

```yaml
needs:
  - job: build_campaign_image
    artifacts: false
```

## Input-by-input check

### `security/trivy-fs@v3.2.0`

| Input used | Value | Listed in task table |
|---|---|---:|
| `stage` | `security` | yes |
| `job-name` | `trivy-fs` | yes |
| `scan-path` | `.` | yes |
| `severity` | `HIGH,CRITICAL` | yes |
| `allow-failure` | `true` | yes |
| `tags` | `["cpu"]` | yes |

Unknown inputs: 0.

### `security/trivy-image@v3.2.0`

| Input used | Value | Listed in task table |
|---|---|---:|
| `stage` | `security` | yes |
| `job-name` | `trivy-image` | yes |
| `scan-mode` | `registry` | yes |
| `image` | `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA` | yes |
| `severity` | `HIGH,CRITICAL` | yes |
| `allow-failure` | `true` | yes |
| `tags` | `["cpu"]` | yes |

Unknown inputs: 0.

`registry-user` and `registry-password` were not set.

### `python/dependency-vuln@v3.3.3`

| Input used | Value | Listed in task table |
|---|---|---:|
| `stage` | `security` | yes |
| `job-name` | `python-dependency-vuln` | yes |
| `project-path` | `analysis` | yes |
| `python-version` | `3.12` | yes |
| `requirements-file` | `requirements.txt` | yes |
| `allow-failure` | `true` | yes |
| `tags` | `["cpu"]` | yes |

Unknown inputs: 0.

The requirements file is intentionally `requirements.txt`, because the component resolves it
relative to `project-path: analysis`.

### `security/bandit@v3.2.0`

| Input used | Value | Listed in task table |
|---|---|---:|
| `stage` | `security` | yes |
| `job-name` | `python-sast` | yes |
| `scan-path` | `analysis` | yes |
| `python-version` | `3.12` | yes |
| `severity` | `medium` | yes |
| `confidence` | `medium` | yes |
| `allow-failure` | `true` | yes |
| `tags` | `["cpu"]` | yes |

Unknown inputs: 0.

## Runner tag

All four components use `tags: ["cpu"]`. These security scans do not require GPU hardware, and the
existing build job already uses `cpu`; this follows the runner guidance instead of the `fast` tag
used by the reference example.

## Verification command

The static checks above were run with Python against `.gitlab-ci.yml`. Result counts:

| Check | Result |
|---|---:|
| YAML parse | ok |
| Stage order | `["build", "security"]` |
| Component entries | 4 |
| `@~latest` entries | 0 |
| Unknown inputs | 0 |
| Missing required task-table inputs | 0 |
| Security job rules equal build rules | 4 of 4 |
| `workflow` unchanged | yes |
| `build_campaign_image` unchanged | yes |

