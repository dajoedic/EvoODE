# WP-N29 Report

## Changed files

- `.gitlab-ci.yml`
- `CHANGELOG.md`
- `baselines/run_odeformer_grid_k8s.py`
- `baselines/tests/test_harness.py`
- `k8s/odeformer_candidate_grid_job.yaml`
- `k8s/odeformer_candidate_grid_smoke_job.yaml`
- `SCRIPTS.md`
- `docs/hpc_deployment_guide.md`

## Implementation

- Added `build_odeformer_candidate_image` and `trivy-odeformer-candidate-image` beside the existing reference CI jobs. The candidate image path is `$CI_REGISTRY_IMAGE/odeformer-candidate:$CI_COMMIT_SHA` plus the branch tag.
- Added `--environment-id {reference,candidate}` to `baselines/run_odeformer_grid_k8s.py`, defaulting to `reference`.
- Added a Kubernetes-runner preflight that reads the required torch pin from `baselines/requirements-odeformer-<environment_id>.txt` and aborts before calling the grid runner if the installed torch public version does not match.
- Added candidate smoke and full-grid manifests using the candidate image, `--environment-id candidate`, `/outputs/odeformer_grid_<COMMIT_SHA>/candidate`, and `/outputs/odeformer_grid_<TRAJECTORY_SHA>/trajectory_export`.
- Checked the collect path: `baselines.run_odeformer_grid --collect --repetitions 3` is output-directory based and works for `.../candidate`; a regression test now covers that.

## Manifest diff

Full grid:

```diff
--- k8s/odeformer_reference_grid_job.yaml
+++ k8s/odeformer_candidate_grid_job.yaml
@@ -1,12 +1,12 @@
 apiVersion: batch/v1
 kind: Job
 metadata:
-  name: evoode-odeformer-reference-grid
+  name: evoode-odeformer-candidate-grid
   namespace: scch-das
   labels:
     app.kubernetes.io/name: evoode
     app.kubernetes.io/part-of: evoode-phase-c
-    app.kubernetes.io/component: odeformer-reference-grid
+    app.kubernetes.io/component: odeformer-candidate-grid
@@ -35,7 +35,7 @@
       labels:
         app.kubernetes.io/name: evoode
         app.kubernetes.io/part-of: evoode-phase-c
-        app.kubernetes.io/component: odeformer-reference-grid
+        app.kubernetes.io/component: odeformer-candidate-grid
@@ -44,7 +44,7 @@
         - name: evoode-gitlab-pull
       containers:
         - name: cell
-          image: registry.gitlab.scch.at:443/joedicke/evoode/odeformer-reference:<COMMIT_SHA>
+          image: registry.gitlab.scch.at:443/joedicke/evoode/odeformer-candidate:<COMMIT_SHA>
@@ -53,10 +53,15 @@
           args:
             - --config
             - /workspace/EvoODE/baselines/configs/odeformer_grid.json
+            - --environment-id
+            - candidate
             - --trajectory-export-dir
-            - /outputs/odeformer_grid_<COMMIT_SHA>/trajectory_export
+            # Use the reference grid trajectory SHA here
+            # (55e9c753185ff6596913547cdf635bcc45d0bbfc) so the hash check
+            # runs against identical trajectory inputs in both ODEFormer arms.
+            - /outputs/odeformer_grid_<TRAJECTORY_SHA>/trajectory_export
             - --output-dir
-            - /outputs/odeformer_grid_<COMMIT_SHA>/reference
+            - /outputs/odeformer_grid_<COMMIT_SHA>/candidate
```

Smoke:

```diff
--- k8s/odeformer_reference_grid_smoke_job.yaml
+++ k8s/odeformer_candidate_grid_smoke_job.yaml
@@ -1,12 +1,12 @@
 apiVersion: batch/v1
 kind: Job
 metadata:
-  name: evoode-odeformer-reference-grid-smoke
+  name: evoode-odeformer-candidate-grid-smoke
   namespace: scch-das
   labels:
     app.kubernetes.io/name: evoode
     app.kubernetes.io/part-of: evoode-phase-c
-    app.kubernetes.io/component: odeformer-reference-grid-smoke
+    app.kubernetes.io/component: odeformer-candidate-grid-smoke
     app.kubernetes.io/managed-by: kubectl
     hpc.scch.at/service: evoode-phase-c-cells
     hpc.scch.at/responsibility: joedicke
@@ -21,7 +21,7 @@
       labels:
         app.kubernetes.io/name: evoode
         app.kubernetes.io/part-of: evoode-phase-c
-        app.kubernetes.io/component: odeformer-reference-grid-smoke
+        app.kubernetes.io/component: odeformer-candidate-grid-smoke
         hpc.scch.at/service: evoode-phase-c-cells
         hpc.scch.at/responsibility: joedicke
     spec:
@@ -30,7 +30,7 @@
         - name: evoode-gitlab-pull
       containers:
         - name: cell
-          image: registry.gitlab.scch.at:443/joedicke/evoode/odeformer-reference:<COMMIT_SHA>
+          image: registry.gitlab.scch.at:443/joedicke/evoode/odeformer-candidate:<COMMIT_SHA>
           imagePullPolicy: IfNotPresent
           command:
             - python
@@ -39,10 +39,15 @@
           args:
             - --config
             - /workspace/EvoODE/baselines/configs/odeformer_grid.json
+            - --environment-id
+            - candidate
             - --trajectory-export-dir
-            - /outputs/odeformer_grid_<COMMIT_SHA>/trajectory_export
+            # Use the reference grid trajectory SHA here
+            # (55e9c753185ff6596913547cdf635bcc45d0bbfc) so the hash check
+            # runs against identical trajectory inputs in both ODEFormer arms.
+            - /outputs/odeformer_grid_<TRAJECTORY_SHA>/trajectory_export
             - --output-dir
-            - /outputs/odeformer_grid_<COMMIT_SHA>/reference/smoke
+            - /outputs/odeformer_grid_<COMMIT_SHA>/candidate/smoke
             - --limit
             - "2"
           env:
```

The unchanged fields include resources, full-grid `parallelism`, `backoffLimit`,
`activeDeadlineSeconds`, NFS mount, threading environment, namespace, image pull secret, and
`JOB_COMPLETION_INDEX` for the smoke job.

## Commands for Orion

Reference smoke/grid/collect:

```bash
# Smoke manifest: substitute <COMMIT_SHA> in k8s/odeformer_reference_grid_smoke_job.yaml.
# Full manifest: substitute <COMMIT_SHA> in k8s/odeformer_reference_grid_job.yaml.
python -m baselines.run_odeformer_grid \
  --config baselines/configs/odeformer_grid.json \
  --output-dir /outputs/odeformer_grid_<COMMIT_SHA>/reference \
  --collect --repetitions 3
```

Candidate smoke/grid/collect:

```bash
# Smoke manifest: substitute <COMMIT_SHA> and <TRAJECTORY_SHA> in
# k8s/odeformer_candidate_grid_smoke_job.yaml.
# Full manifest: substitute <COMMIT_SHA> and <TRAJECTORY_SHA> in
# k8s/odeformer_candidate_grid_job.yaml.
# Use <TRAJECTORY_SHA>=55e9c753185ff6596913547cdf635bcc45d0bbfc for the completed reference grid.
python -m baselines.run_odeformer_grid \
  --config baselines/configs/odeformer_grid.json \
  --output-dir /outputs/odeformer_grid_<COMMIT_SHA>/candidate \
  --collect --repetitions 3
```

Before the full candidate grid, inspect the smoke output under
`/bigdata/data-science/joedicke/odeformer_grid_<COMMIT_SHA>/candidate/smoke`; at least one `_opt`
cell must have `odeformer_optimization_status = success`.

## Verification

- `python -m pytest baselines/tests/test_harness.py -k "odeformer_grid_k8s or odeformer_grid_completion_index_mapping or odeformer_grid_shards_cover_504_cells_once or odeformer_grid_collect_rejects_incomplete_repetition"`: 8 passed, 37 deselected.
- `python -m pytest baselines/tests/test_harness.py`: 41 passed, 5 skipped.
- Python/YAML parse check with `yaml.safe_load_all`: `.gitlab-ci.yml`, both reference manifests, and both candidate manifests each parse as 1 YAML document.

## Not verified

- No Docker build was run.
- No Trivy result exists yet for `odeformer-candidate`, so HIGH/CRITICAL counts are not reported.
- No image pull on Orion was attempted.
- No `oc`/`kubectl` command was run.
- The NFS path `/outputs/odeformer_grid_<TRAJECTORY_SHA>/trajectory_export` was not accessed in this session.
