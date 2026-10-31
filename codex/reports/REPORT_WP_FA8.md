# WP-FA8 — Q7 implementation and technical acceptance

Implementation: `analysis/scripts/aggregate/build_sideproject_q7_paths.py`,
`analysis/scripts/aggregate/aggregate_sideproject_q7.py`,
`analysis/tests/test_sideproject_q7.py`, `k8s/sideproject_q7_job.yaml`.
Upload mapping: `codex/reports/UPLOAD_WP_FA8.md`.

## Scope and controls

The builder imports Q6's `growth_path_with_end` unchanged. Its named significance
end condition uses the strict thresholds 6.635 and 10.828, treats nonpositive
expected noise gain as significant, and leaves numerical-zero, no-gain, full-basis
and cycle stops to Q6. A `floor` end reason in the equation table means that the
named significance condition fired. The Q5 cap identity control is recomputed
for every cell, including coefficients and signed zeros.

Exploration comparison executes the original exploratory job's threshold and
closure code via its AST, removing only its truth-reporting equation loop and
capturing the returned support sequences. No exploratory CSV is read and no
truth evaluation is executed. Both thresholds are compared per cell.

Hash controls cover the Q5 manifest, observed binary bytes, original Q5 inputs,
Q7 protocol, builders and supporting path/design sources. The original Q5
protocol digest is recovered by removing its explicitly marked execution-only
2026-10-28 amendment in memory and checking the resulting original bytes.
No Git command or repository operation is used.

The full technical build omits truth classifications. `--classify` implements
the full-run-only equation fields for a later authorized scientific run;
`--limit` forbids that flag. No scientific classification, performance rate,
structure hit, R-squared or cost comparison was evaluated on real cells.

## Runner compatibility

`q7_fit_paths.json` contains only cells with new states, and only those states in
`candidates`; `upper_candidates` is empty. All Q7 candidate IDs are `q7_###`,
and reused candidates separately carry `reuse_q5_candidate_id`; new candidates
carry `new: true`. Support equality includes every equation.

The fit input sets `protocol_commit` to `f737939`, deliberately: fitting remains
Q5. Its additional `q7_protocol` object records the frozen Q7 protocol path and
SHA-256. The unchanged runner checks that commit marker and the export-index
hash, reads ordinary Q5 cell/candidate fields, and ignores the extra metadata.
Its `q4_selected_units` view maps `cell_id` to `unit_id`: the shard file therefore
has one cell ID per line, no header, unique entries, and a zero-based `--index`.
`--limit` limits cells, not candidate states; the separate smoke input contains
exactly two new states of a single dim-2 cell.

`q5_fit` checks basis names, parameter count/order, observed byte hashes and clean
training/opposite-IC target trajectories. Those inputs and fields are preserved.
The Q4 selector does not call the Q4 input verifier from Q5's main, and does not
require clean control candidates in the Q7 fit list.

The local Q5 output directory contains probe fits only. Shard planning therefore
uses Q5's complete frozen `q4_seconds_per_candidate` planning inputs: measured Q4
mean per-unit candidate time times number of new candidates, descending planned
cost, deterministic cell-ID tie break. No missing grid time is inferred.

## Aggregation and field audit

The aggregator imports Q5's `controls`, `rows_for_cells`, `report_tables` and
selection functions. Rules (a), (b), (c), ties, sentinels, pruning, D1–D5 and metric
definitions are inherited. It refuses partial grids and missing/unexpected fits;
there is no incomplete mode. Q5 controls require every original candidate,
including upper subsets and stragglers, before any table is written.

| Fields | Actual source |
|---|---|
| `active_idxs`, `p0`, equations, weak BIC, step | Original Q5/Q7 candidate manifests |
| `params`, `pruned_active_idxs` | Existing Q5 runner record fields |
| training/reconstruction/generalization losses, sample counts, R-squared, sentinel/divergence | Existing nested runner fields |
| `clean_ic_observed_mse`, `evaluation_ode_solves` | Existing Q5 runner record fields |
| loss evaluations, ODE solves | Existing `fit_meta` fields |
| observed hash, cell identity, optimizer settings, source inventory, settings fingerprint | Existing record and provenance fields |
| `new`, `reuse_q5_candidate_id`, `q7_protocol` | New input-manifest metadata, not new runner fields |
| raw/pruned structure, chosen model, rates, D1–D5, decision inputs | Imported analysis pipeline |
| published WSINDy metrics and counts | Existing Q5-W detail CSV columns, checked against its real header |

Important schema boundary: Q5 records do not contain raw support or `p0`.
The reuse control checks these against the original Q5 candidate manifest,
whose SHA-256 the reused record's provenance must match. It does not invent
record fields. Actual record objects remain unchanged in the join.

Output tables are `q7_candidates`, `q7_units`, `q7_rates`, `q7_diagnostics`,
`q7_q5_comparison`, `q7_q5_diagnostics`, `q7_decision_inputs`, `q7_reuse_control`,
`q7_q5w_comparison`, `q7_cost` (CSV) and `q7_run_metadata.json`, beside Q5's tables.
The original Q5 weak best-subset diagnostic is reused for reporting only;
it never enters Q7's selection pool or new fit input.

The decision input pools sigma > 0 over rho and realizations, checks the exact
5-percentage-point margin using integer counts for pruned exact structure and
variance-weighted generalization, and leaves dim4 without a verdict.
The Q5-W table contains both libraries: W1 on rho=0, and W1-interp as primary
with W1 beside it on rho=0.5. Completeness and observed hashes are mandatory.
Cost rows distinguish reused states from new fits and their evaluation counts.

Image provenance has a schema limit: Q5 runner records do not store an image
digest. The manifest declares the exact unchanged Q5 image, while aggregation
checks unchanged runner/source hashes, settings fingerprint and optimizer
settings. Metadata explicitly distinguishes this declaration from record evidence.

## Commands for Claude

Two-state local smoke (not run by Codex; Julia 1.12.6 required; intended <5 min):

```powershell
julia +1.12.6 --project=. studies/regression/sideproject_q5_noise_fits.jl --paths outputs/sideproject_q7_inputs/validated/q7_smoke_two_states.json --export-dir outputs/phase_c_c6_data_conditions_5dd1df8 --output outputs/sideproject_q7_smoke/two_states.jsonl
```

Technical path rerun, in a fresh output directory:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python analysis/scripts/aggregate/build_sideproject_q7_paths.py --workers 4 --output outputs/sideproject_q7_inputs/claude_repeat
```

Small technical input check: add `--limit 2` and use another fresh output folder.
The parallel implementation uses independent Python interpreters and workspace
files rather than multiprocessing pipes, which the managed Windows sandbox can deny.

After all original Q5 and new Q7 records are present, aggregate with the complete
grid records only (exclude the differently hashed probe files):

```powershell
python analysis/scripts/aggregate/aggregate_sideproject_q7.py --q5-input 'outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/index_*.jsonl' --q7-input 'outputs/sideproject_q7_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/index_*.jsonl' --wsindy-input outputs/sideproject_q5w_wsindy/full/details.csv outputs/sideproject_q5w_wsindy/w1_interp_full/details.csv
```

No actual-data aggregation or Julia fit was run. No cluster job was started,
no file was copied to S:, no frozen file or WP-N48b file was changed, and no
Git operation was performed. Work remains uncommitted.

## Measured technical counts

Primary threshold: 1,632 cells, 11,678 joint candidate states, 8,608 reused
states and 3,070 new states in 338 cells.

| Dimension | Cells requiring fits | New states |
|---|---:|---:|
| 1 | 0 | 0 |
| 2 | 228 | 1,200 |
| 3 | 83 | 1,044 |
| 4 | 27 | 826 |
| Total | 338 | 3,070 |

Matching only Q5 path candidates gives 3,080 new states, matching the protocol's
projection. Ten additional supports can reuse the already fitted Q5 upper-subset candidate
without a corresponding Q5 path candidate: 7 dim-2 and 3 dim-3 states.
This accounts exactly for the difference; no state is dropped or refitted.
The reuse matching permits every fitted Q5 candidate, including upper subsets.

The Q7 protocol SHA-256 in both input headers is
`b6b261af968e33d8d9b8038e3c4fb470bf3e93a78cae3bef022eb206ec4fc838`.
The manifest has 338 completions, parallelism 14, unchanged 1 CPU / 4Gi resources,
unchanged image/runner and no deadline.

## Validation provenance

Final focused test command:

```powershell
python -m pytest analysis/tests/test_sideproject_q7.py -q -p no:cacheprovider -W ignore::DeprecationWarning
```

Result: **21 passed in 34.40 seconds**; log:
`outputs/sideproject_q7_inputs/tests/pytest_final.log`.
Fixtures start from actual Q5 cells and an actual Q5 probe record; replacements
of fit parameters, pruning and path provenance are explicit. Tests cover both
thresholds and strict equality, nonpositive expected noise gain, real-data
exploration support identity, deterministic serial/file-worker writers, bad
hashes, incomplete inputs, duplicate conflicts, support/p0 reuse mismatches,
provenance/settings/source mismatches, imported selections and diagnostics,
exact margin arithmetic, dim4 exclusion, empty-path reporting and complete WSINDy library coverage.
Scientific tables in tests use synthetic values only.

During implementation, preliminary threaded runs were stopped before 15 minutes;
the final implementation uses independent processes with file transport.
The first complete numerical pass finished within 14 minutes, then its original
planning lookup failed because only Q5 probe records were local. All four
completed worker result files were preserved. After correcting the planning-only
lookup to frozen Q5 planning inputs, `publish_completed_pass.py` compared the ASTs
of every path, significance, exploratory comparison and worker function against
`work/134cc4943df84a7fb15c5dc97bff889c/builder_at_computation.py`, verified all
1,632 worker inputs and unique result indices, and published the complete first
pass through the corrected writer. Numerical functions were identical.

A fresh independent full numerical pass uses the corrected builder directly in
`outputs/sideproject_q7_inputs/repeat/`. The acceptance validator compares every
artifact byte-for-byte with `validated/`, checks all input hashes, reuse
support/p0, fit candidate parameter/basis schema, exact new-only fit coverage,
shard coverage/order, two-state smoke schema and manifest invariants.
The executable validator is `outputs/sideproject_q7_inputs/validate.py`.


## Final acceptance result

Both full passes reproduce the exploratory support sequences at both thresholds
for all 1,632 cells. **All eight output artifacts are byte-identical** between
`validated/` and the independently computed `repeat/` pass, including both path
files, new-fit input, shard list, equations, controls, smoke input and technical
summary. The secondary threshold contains 10,761 states.

`outputs/sideproject_q7_inputs/validation.json` records byte lengths and SHA-256
for every artifact and successful input-hash, reuse, fit-schema, shard-order and
manifest checks. Validation ran successfully after the final source correction.
The independent repeat finished within 12 minutes; no execution exceeded
15 minutes. The final focused tests also ran after the planning correction.

Fourteen actual cells have empty primary paths. Q5's reporting function indexes
the final pool state when emitting its upper-subset diagnostic, so it cannot
represent this case directly. The Q7 adapter calls imported Q5 selection on the
empty pool for (a), (b), (c), emits Q5's unselected-row schema, and takes the
unchanged upper diagnostic from the original Q5 reporting rows. These cells stay
in every denominator. No candidate is inserted into an empty pool, and ordinary
nonempty paths continue through Q5 reporting unchanged. This case has a dedicated
synthetic test; no real-data scientific aggregation was executed.

WP-FA8 is complete. Julia smoke and production fitting are intentionally left
for Claude as required by the task, using the exact commands and upload mapping
above. All implementation and artifacts remain uncommitted.
