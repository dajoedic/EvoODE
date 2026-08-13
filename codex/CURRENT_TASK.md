# CURRENT TASK

**Language: Julia / YAML (Kubernetes)**

## WP-H6 — Three corrections the first cluster run exposed

The path from commit to record now works end to end on Orion: the image builds in CI, the baked
precompilation cache is accepted, the bootstrap writes manifest and index lists to NFS in 22 seconds,
and an indexed Job ran three 1D cells that landed records and heartbeats. Nothing here is a
redesign. These are three defects the run surfaced, each cheap, each with a consequence that only
appears at campaign scale.

### 1. The progress bar must fall silent when there is no terminal

The per-level progress display writes terminal control sequences — cursor-up, erase-line — into the
pod log, where no terminal exists to interpret them. The log becomes unreadable, which is the
visible symptom, but not the reason this matters.

The reason is volume. Each level emits roughly twenty lines. At thirty levels per cell and 756
cells, that is on the order of half a million lines of control-sequence noise held on the cluster
nodes, for information that is already recorded properly elsewhere: the heartbeat file writes one
structured JSON event per level directly to shared storage, where it is durable, machine-readable,
and visible without cluster access. The progress bar was built for interactive laptop runs and has
no addressee in a batch pod.

Make the display conditional on the output actually being attached to a terminal. Interactive local
runs must keep the behaviour they have today; batch pods must produce no progress output at all.
Apply this wherever such a display is created, not only in the path the campaign happens to use — a
second entry point that still floods the log would reintroduce the problem silently.

The heartbeat must be unaffected. It is the batch progress mechanism and its behaviour must not
change.

### 2. The bootstrap manifest requests too little memory

The manifest bootstrap was killed by the kernel under its 2 GiB limit and completed at 8 GiB. The
committed Kubernetes manifest still carries the value that fails. Anyone applying the file as it
stands reproduces the failure — and does so after a container start, so the cause is not obvious
from the outcome.

Correct the bootstrap workload's memory request and limit to the value that is known to work.

Leave the **cell** workload's memory untouched. The bootstrap loads all 63 systems and builds the
full 756-row manifest; a cell computes a single system. They are different workloads and the
bootstrap's requirement says nothing about a cell's. The cells ran successfully at their current
value, and changing it without measurement would replace one unfounded number with another.

### 3. A failed cell must leave its evidence behind

The Job manifests use a restart policy under which the controller **deletes** the failed pod before
retrying. That is how the first bootstrap failure was lost: the job reported failure, and the logs
explaining it no longer existed. Diagnosis required reconstructing the run as a standalone pod.

At campaign scale this is the difference between a missing record you can explain and one you
cannot. Switch both Job manifests to the policy under which a failed attempt leaves its pod, and its
log, in place. Successful pods are cleaned up by the cluster as usual; only failures accumulate,
which is exactly the set worth keeping.

### Verification

The memory and restart-policy changes are structural and can be confirmed by inspection; state the
values before and after.

The progress-display change must be verified behaviourally, not by reading the code: run the same
entry point twice, once with output attached to a terminal and once with output redirected, and show
that the first still displays progress while the second emits none. Confirm in both cases that the
heartbeat file is written with its per-level events, since that is the property that must survive.

Do not apply anything to the cluster and do not run a campaign.

### Out of scope

Cell memory limits, parallelism, the campaign manifests themselves, the plotting dependencies in
`Project.toml`, and any change to metrics, configuration, hyperparameters or fingerprints. This work
package changes what is printed and what is requested, never what is computed — results must be
bit-identical.

### Report

Write `codex/REPORT_WP_H6.md`: where the terminal check was applied and which entry points it covers,
the before/after values for memory and restart policy, the two-way behavioural test of the progress
display with its output, and confirmation that the heartbeat is unchanged in both modes.
