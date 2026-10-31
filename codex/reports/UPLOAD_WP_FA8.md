# WP-FA8 upload note

Claude copies these files; Codex has not written to S: or started a job.

NFS base on Windows:
`S:\BigDataOrion\data-science\joedicke\sideproject_q7_354106398d5e67ffa72c237e2ba83e3feeb25b31\`

| Local source | Destination under the NFS base |
|---|---|
| `outputs/sideproject_q7_inputs/validated/q7_fit_paths.json` | `input/q7_fit_paths.json` |
| `outputs/sideproject_q7_inputs/validated/q7_fit_paths.shards_cost_desc.txt` | `input/q7_fit_paths.shards_cost_desc.txt` |
| Entire `outputs/phase_c_c6_data_conditions_5dd1df8/` | `input/export/` (preserve all relative names and raw bytes) |

Create an empty `out/` beside `input/`. The job writes `out/index_<index>.jsonl`.
The full export is intentional: the runner also reads each clean training and opposite-IC test trajectory.
The export is identical to Q5's existing NFS input/export; Claude may copy that tree on NFS instead of uploading
it again, preserving byte identity. Do not use Q5's output directory for Q7 results.

Keep the full Q7 paths and secondary-threshold paths locally for aggregation; they are not runner inputs.
The job manifest is `k8s/sideproject_q7_job.yaml`. It uses the unchanged Q5 runner and image, 14 pods,
whole-cell shards ordered by descending planned cost, and no deadline.

The fit input deliberately has `protocol_commit: f737939`: the fitting protocol is Q5.
Its separate `q7_protocol` object identifies and hashes `docs/sideproject_residual_growth_protocol_q7.md`.
The runner checks the commit marker and export index hash, and ignores extra top-level metadata.

Copy the fit JSON without reformatting it. Aggregation compares its raw SHA-256
with each fit record's `provenance.paths_sha256`. Do not run this job with the
two-state local smoke input. Keep smoke output separate from the production
Q7 `out/` directory because its path-file hash differs.
