# WP-N17 Report

## Result

Implemented Phase-C Kubernetes manifests and extended the Phase-C manifest generator with the index lists used by those manifests.

New manifests:

- `k8s/phase_c_bootstrap_campaign_job.yaml`
- `k8s/phase_c_indexed_smoke_job.yaml`
- `k8s/phase_c_c1_c2_campaign_job.yaml`
- `k8s/phase_c_c3_campaign_job.yaml`

Generator additions in `studies/regression/generate_phase_c_manifest.jl`:

- `indices_c1_c2_cost_desc.txt`: 756 rows, conditions `capped` and `uncapped`, cost-descending with original pair adjacency preserved by stable sorting.
- `indices_c3_cost_desc.txt`: 180 rows, condition `pretune_on`, cost-descending.
- `indices_smoke_dim1_all_arms.txt`: 3 rows, one dim-1 cell each for `capped`, `uncapped`, and `pretune_on`.

Existing outputs remain unchanged: `indices_all.txt`, `indices_cost_desc.txt`, and `indices_dim1.txt` through `indices_dim4.txt`.

## Campaign split decision

The campaign is split into two Indexed Jobs:

- `evoode-phase-c-c1-c2-campaign`: 756 completions for C-1 plus C-2.
- `evoode-phase-c-c3-campaign`: 180 completions for C-3.

Reason: C-1 and C-2 are the paired Claim-B comparison and must share one abort boundary. The generator already emits pair members adjacent for each `(system, initial_condition_set, seed)`, and `indices_c1_c2_cost_desc.txt` keeps that adjacency inside each cost class. C-3 is unpaired, has 180 cells, and can be skipped or rerun independently if budget requires it.

Both campaign Jobs use `parallelism: 32`. This follows the WP-N1 operating point but is explicitly marked as requiring a fresh namespace check before launch. Commands are included below and in the manifest comments.

## Manifest checks

Static checks completed by Codex:

- Parsed all four `k8s/phase_c*.yaml` files with PyYAML.
- Confirmed each file is a Kubernetes `Job`.
- Confirmed job names do not collide with existing Phase-B or WP-N1 manifests.
- Confirmed `<COMMIT_SHA>` appears in the image tag and output paths.
- Confirmed all containers use `imagePullSecrets: evoode-gitlab-pull`.
- Confirmed `requests` and `limits` match for CPU and memory in all new manifests.
- Confirmed token-expiry and start-order failure modes are present as YAML comments.

Julia was not executed by Codex because the environment cannot start Julia. The Julia acceptance commands for Claude are listed in "Open Julia acceptance".

## Start guide

Set the image commit and namespace:

```bash
export COMMIT_SHA=<COMMIT_SHA>
export NS=scch-das
```

Create or refresh the GitLab deploy-token Secret. Do not write the token to a file:

```bash
export GITLAB_DEPLOY_USER=<deploy-token-user>
read -rsp "GitLab deploy token: " GITLAB_DEPLOY_TOKEN; echo
kubectl -n "$NS" create secret docker-registry evoode-gitlab-pull \
  --docker-server=registry.gitlab.scch.at:443 \
  --docker-username="$GITLAB_DEPLOY_USER" \
  --docker-password="$GITLAB_DEPLOY_TOKEN" \
  --dry-run=client -o yaml | kubectl apply -f -
unset GITLAB_DEPLOY_TOKEN
```

Repeat the namespace checks before launch. The 32-way parallelism is not an entitlement:

```bash
kubectl -n "$NS" get resourcequota,limitrange
kubectl -n "$NS" top pods
kubectl get nodes
```

Apply the bootstrap Job first:

```bash
sed "s/<COMMIT_SHA>/${COMMIT_SHA}/g" k8s/phase_c_bootstrap_campaign_job.yaml | kubectl apply -f -
kubectl -n "$NS" wait --for=condition=complete job/evoode-phase-c-bootstrap-campaign --timeout=30m
kubectl -n "$NS" logs job/evoode-phase-c-bootstrap-campaign
```

Expected bootstrap outputs on NFS under `/outputs/phase_c_campaign_${COMMIT_SHA}/`:

- `manifest.csv`
- `indices_all.txt`
- `indices_cost_desc.txt`
- `indices_c1_c2_cost_desc.txt`
- `indices_c3_cost_desc.txt`
- `indices_smoke_dim1_all_arms.txt`
- `indices_dim1.txt`
- `indices_dim2.txt`
- `indices_dim3.txt`
- `indices_dim4.txt`

Run the smoke Job second:

```bash
sed "s/<COMMIT_SHA>/${COMMIT_SHA}/g" k8s/phase_c_indexed_smoke_job.yaml | kubectl apply -f -
kubectl -n "$NS" wait --for=condition=complete job/evoode-phase-c-indexed-smoke --timeout=2h
kubectl -n "$NS" logs job/evoode-phase-c-indexed-smoke
```

Smoke checklist for the 3 output records in `/outputs/phase_c_smoke_${COMMIT_SHA}/tasks`:

- `config_fingerprint = 0c9672de35c75a9d`
- `basis_name = staged_polynomial_basis_with_constant`
- `max_fit_attempts = 3`
- `executed_levels` is present and non-empty
- `git_hash` is real and not `not_collected`
- `error` is empty
- conditions represented: `capped`, `uncapped`, `pretune_on`

Only after the smoke checklist passes, apply the two campaign Jobs:

```bash
sed "s/<COMMIT_SHA>/${COMMIT_SHA}/g" k8s/phase_c_c1_c2_campaign_job.yaml | kubectl apply -f -
sed "s/<COMMIT_SHA>/${COMMIT_SHA}/g" k8s/phase_c_c3_campaign_job.yaml | kubectl apply -f -
```

Monitor:

```bash
kubectl -n "$NS" get jobs,pods -l app.kubernetes.io/part-of=evoode-phase-c
kubectl -n "$NS" describe job evoode-phase-c-c1-c2-campaign
kubectl -n "$NS" describe job evoode-phase-c-c3-campaign
kubectl -n "$NS" get pods -l app.kubernetes.io/part-of=evoode-phase-c
```

If pods show `ErrImagePull` or `HTTP Basic: Access denied`, refresh `evoode-gitlab-pull` and rerun smoke before continuing. This is a token failure, not evidence that the image is missing.

## Open Julia acceptance

Codex could not run these commands. Claude should run the short path first, then the full bootstrap-equivalent path:

```bash
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl \
  --output outputs/studies/regression/phase_c_codex_limit/manifest.csv \
  --all-dimensions \
  --limit 3
```

Check the printed rows:

- `rows=3`
- `arm_capped_rows=1`
- `arm_uncapped_rows=1`
- `arm_pretune_on_rows=1`
- `c1_c2_cost_desc_index_rows=2`
- `c3_cost_desc_index_rows=1`
- `smoke_dim1_all_arms_index_rows=3`

Full NFS-equivalent command:

```bash
julia --project=. --startup-file=no studies/regression/generate_phase_c_manifest.jl \
  --output outputs/studies/regression/phase_c/manifest.csv \
  --all-dimensions
```

Expected full-run printed rows:

- `rows=936`
- `arm_capped_rows=378`
- `arm_uncapped_rows=378`
- `arm_pretune_on_rows=180`
- `c1_c2_cost_desc_index_rows=756`
- `c3_cost_desc_index_rows=180`
- `smoke_dim1_all_arms_index_rows=3`
