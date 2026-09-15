# WP-CI2 Report

## Change

Added a top-level `workflow: rules` section to `.gitlab-ci.yml`.

Allowed pipeline sources:

- Branch push: `$CI_PIPELINE_SOURCE == "push" && $CI_COMMIT_BRANCH`
- Tag push: `$CI_PIPELINE_SOURCE == "push" && $CI_COMMIT_TAG`
- Manual UI run: `$CI_PIPELINE_SOURCE == "web"`

The final workflow rule is `when: never`, so all other pipeline sources are rejected before any job is created.

## Source Check

GitLab documentation source:

- https://docs.gitlab.com/ci/variables/predefined_variables/
- https://docs.gitlab.com/ci/jobs/job_rules/

`CI_PIPELINE_SOURCE` is the predefined variable for how the pipeline was triggered.

Values used:

- `push`: pipelines triggered by a Git push event, including branches and tags.
- `web`: pipelines created by selecting New pipeline in the GitLab UI.
- `schedule`: scheduled pipelines; not allowed here.
- `api`: pipelines triggered by the pipelines API; not allowed here.
- `trigger`: pipelines created with a trigger token; not allowed here.

The tag rule also requires `$CI_COMMIT_TAG`, so a scheduled pipeline configured for a tag does not pass the workflow rules. The branch rule likewise requires `$CI_COMMIT_BRANCH`.

## Static Acceptance

Commands run:

```text
python -c "import yaml, pathlib; data=yaml.safe_load(pathlib.Path('.gitlab-ci.yml').read_text()); assert isinstance(data, dict); assert 'workflow' in data and 'build_campaign_image' in data; print('yaml_ok'); print('top_level_keys=' + ','.join(data.keys()))"
```

Output:

```text
yaml_ok
top_level_keys=workflow,stages,build_campaign_image
```

Job block check:

```text
job_block_textually_unchanged
```

The `build_campaign_image` section from `build_campaign_image:` to end of file is textually unchanged from the pre-change state captured before editing.

## Runtime Visibility

No build was attempted. The effect of the new workflow rules is only visible on the next GitLab pipeline creation event, for example the next push to GitLab.
