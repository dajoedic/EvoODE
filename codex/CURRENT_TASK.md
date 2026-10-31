# WP-FA8 — Q7: significance-test path end; fit inputs for Orion and the aggregation
**Language: Python**

Stand 2026-10-31. Authority: `docs/sideproject_residual_growth_protocol_q7.md` (frozen; read it in full). Builds on
WP-FA7 (`build_sideproject_q6_paths.py`), the Q5 aggregation `aggregate_sideproject_q5.py`, the Q5 job
`k8s/sideproject_q5_job.yaml`, the Q5 Julia runner `studies/regression/sideproject_q5_noise_fits.jl` (read it; do not
change it), and the exploratory script `analysis/exploratory/sideproject_q7_gain_test/q7_gain_test.py` (the rule as
run; do not copy its evaluation code, reimplement the rule cleanly).

## Scope

1. **Path builder** `analysis/scripts/aggregate/build_sideproject_q7_paths.py`: the §2 rule as a named end condition
   on Q6's `growth_path_with_end` (imported, unchanged), both thresholds, all 1,632 Q5 cells. Output under
   `outputs/sideproject_q7_inputs/`: `q7_paths.json` (per cell all Q7 candidates of the α = 0.01 rule in the Q5
   candidate schema, each marked `reuse_q5_candidate_id` or `new`), the α = 0.001 paths as a second file, and a
   per-equation table like Q6's `equations.csv` (end reason, length; truth classification fields only in the full run).
   Control: the support sequences equal those of the exploratory run — reproduce that run's paths for the comparison,
   not its CSV. Determinism (two runs identical). Hash controls as Q6.
2. **Fit input for the unchanged Q5 runner:** `q7_fit_paths.json` in exactly the schema the runner reads
   (`--paths`), containing only cells with new states and in them only the new states as `candidates`
   (`upper_candidates` empty), new candidate IDs `q7_###` that cannot collide with Q5 IDs. The runner checks
   `protocol_commit == "f737939"` and the index hash: set `protocol_commit` to `f737939` (the fit protocol is Q5's,
   unchanged) and add a field `q7_protocol` with the Q7 protocol path and its SHA-256; state this in the report.
   Verify by reading the runner that nothing else blocks (e.g. the Q4 selector, `--unit-list` format). Plus a shard list
   in descending planned cost (same method as Q5's `shards_cost_desc`).
3. **Manifest** `k8s/sideproject_q7_job.yaml`: a copy of the Q5 job with the same image, a new NFS directory
   `sideproject_q7_354106398d5e67ffa72c237e2ba83e3feeb25b31/` (input/out), completions = number of cells with new
   states, **parallelism 14**, no deadline, same resources. Plus a short `upload` note: which local files go where on
   `S:\BigDataOrion\data-science\joedicke\` (Claude copies them).
4. **Aggregation** `analysis/scripts/aggregate/aggregate_sideproject_q7.py`: joins Q5 records (reused states) and Q7
   records (new states) per cell, applies rules (a), (b), (c) exactly as `aggregate_sideproject_q5.py` does (import,
   do not duplicate), writes the §4 tables beside Q5's and the §5 decision inputs, and the §6 reuse control. Refuses
   to run on incomplete inputs (no `--allow-incomplete` unless it is clearly marked in every output).
   Test on synthetic fixtures only.
5. Focused tests for 1, 2, 4; a small local smoke of the unchanged Julia runner is **not** possible for Codex —
   instead state the exact command Claude should run to fit two new states of one dim-2 cell locally (< 5 min).

## Verboten

- Reporting any truth classification, rate, structure hit, R² or cost comparison (technical counts allowed: cells,
  states, new states, shard sizes).
- Changing the Q5 runner, Q5/Q6 builders, any frozen protocol, Q5 inputs or records; any git operation; cluster jobs;
  copying to `S:`; anything over 15 minutes; built-in timeouts.
- Touching the uncommitted WP-N48b files: `analysis/scripts/aggregate/aggregate_c6_symbolic_baselines.py`,
  `analysis/scripts/aggregate/run_k8s_symbolic_shard.py`, `baselines/c6_shards.py`,
  `baselines/tests/test_c6_symbolic_execution.py`, `codex/reports/REPORT_WP_N48.md`, `k8s/phase_c_c6_pysr*.yaml`.

## Abnahme

- Path builder reproduces the exploratory supports; fit input readable by the runner as written (argued from its code);
  manifest and upload note; aggregation tested on fixtures; counts of cells / new states stated.
- Report `codex/reports/REPORT_WP_FA8.md`; `codex/STATUS.md` as `CODEX_PROTOCOL.md` prescribes.
