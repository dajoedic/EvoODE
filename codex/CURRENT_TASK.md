# CURRENT TASK

**Language: YAML (Kubernetes)**

## WP-H4b — Correct the attribution labels to the site convention

WP-H4 is otherwise accepted. The manifest generator change is additive and leaves the fingerprint at
`c71c85ac2ec580ff`; the index mapping and its boundary checks are correct; the Job references the
image by commit SHA rather than a moving tag. One defect must be fixed before anything is applied to
the cluster.

### The defect

Both Kubernetes manifests carry invented attribution labels:

```text
scch.at/owner
scch.at/workload
```

The site convention, visible in the reference project's own deployment manifest, uses a different
prefix and different keys:

```text
hpc.scch.at/service
hpc.scch.at/responsibility
```

### Why this is not cosmetic

The cluster operators impose no hard walltime. Their stated policy is that batch Jobs are left alone
unless one obviously hangs, and that the owner is contacted **before** any intervention — explicitly
conditional on the workload carrying identifying metadata.

That contact path is what allows a single cell to run for 24 to 48 hours without a checkpoint, which
in turn is why this project needs no checkpointing at all. A workload labelled with keys the site
does not recognise is, for that purpose, unlabelled: an operator inspecting a long-running pod finds
no owner and no service name. The failure would surface only once a campaign is well under way,
which is the most expensive possible moment.

### What to change

In **both** manifests, replace the invented labels with the site convention. Apply them in both
places each manifest carries labels — the object's own metadata **and** the pod template — because an
operator inspecting a running pod sees the pod's labels, not the parent object's.

Use the responsibility value that identifies the owner, and a service value that identifies this
workload as the EvoODE Phase B campaign, distinguishing the bootstrap workload from the cell
workload as the existing component labels already do.

Keep the standard `app.kubernetes.io/*` labels. They are good practice, they do not conflict, and
they are not the ones at issue.

### Out of scope

Everything else in WP-H4 stands. Change no image, no mapping logic, no manifest generator, no
resource values, no metric, no configuration, no fingerprint.

### Report

Append a short section to `codex/REPORT_WP_H4.md` recording the label keys and values now used, and
confirming they appear in both the object metadata and the pod template of both manifests.
