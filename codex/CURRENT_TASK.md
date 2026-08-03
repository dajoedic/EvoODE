# CURRENT TASK

**Language: Julia**

## WP-B3 — Close the three gaps that stand between WP-B2 and a campaign

WP-B2 is delivered: manifest, single-cell entry point, merge step, container, fingerprint guard,
fingerprint `256014cf6f0295e1`. The batch path reproduces the WP-B1 verification cell exactly.

Three things must be settled before the campaign can start, and two of them are cheapest to do
**now**, because no history record exists under the current fingerprint. Once one does, changing
the fingerprint means discarding runs.

The HPC consultation is on **2026-08-06**. What has to exist by then is a setup whose numbers are
defensible, not a finished campaign.

---

### 1. The merge step accepts failed records

`run_batch_cell.jl` writes a record even when the cell failed — the record carries a non-null
`error` field — and then exits non-zero. `merge_batch_records.jl` does not filter on `error`.
`load_completed_cells` in `run_regression.jl` does exactly that filtering, so the two paths disagree
about what "completed" means.

The consequence on a cluster: a cell killed by a timeout or by the OOM killer contributes a record,
the merge inserts it into the history, and the successful re-run of that same cell is then rejected
as a duplicate. The campaign ends with a permanently poisoned cell that looks merged.

Fix the disagreement. Decide deliberately whether a failed cell should produce a task file at all,
or produce one that the merge recognises and refuses — either is defensible, but the two scripts
must then agree, and the reasoning belongs in the report. Whatever you choose, failure information
must not be silently discarded: a cell that crashed 40 hours into a 4D system is a finding, and
the merge must report how many such records it saw.

Verify against a **scratch copy** of the history, never against `studies/regression/history.jsonl`:
construct a task file carrying a failed record, show that merging it does not create a key that
blocks the corresponding successful record, and show that merging a successful record afterwards
still adds it.

---

### 2. `BFGS_TIME_LIMIT_S = 1800` must become a deterministic budget

This is a wall-clock limit inside the optimizer. On a laptop it never bound, so it never mattered.
On a heterogeneous cluster it can bind on a slow node and not on a fast one — which would make a
scientific result depend on which node the scheduler happened to hand out. That is not a performance
concern, it is a reproducibility defect, and it is the last wall-clock dependency in the search path.

Replace it with a budget expressed in counts, so that two runs of the same cell on different
hardware execute the same computation. Which count is the right one is your call from the code — the
guiding property is that the budget must be a function of the search state alone, never of elapsed
time.

Two constraints on the replacement:

- **Calibrate it, do not guess it.** The existing records carry the counters needed to see what the
  optimizer actually consumes on cells that converge normally. Pick a bound that does not bind on
  those cells — the limit is a safety net against pathological line-search, not a tuning knob. State
  in the report which records you read and what margin the chosen value leaves.
- The change is fingerprint-affecting. Report the new `config_fingerprint`, and confirm that the
  WP-B1 verification cell still returns the same result under it — if the budget never bound before,
  the numbers must not move. A deviation here means the budget is binding on a healthy cell and is
  therefore set wrong.

If the counters do not exist to express a sensible budget, say so and propose what would have to be
recorded, rather than inventing a plausible-looking number.

---

### 3. Replace one extrapolation in the resource request with a measurement

`docs/hpc_requirements.md` §5 states openly that the cost table rests on laptop medians scaled by
2.56 for the denser grid, with the 3D and 4D classes extrapolated from 2D. The 1D class is the one
we can measure here cheaply.

Run through the **batch entry point**, not the suite loop, so the measured path is the path the
cluster will use: variant `evogrow_v2_2_stage_capped`, systems 3 and 11, initial-condition set 1,
all three seeds — six cells, all 1D, all previously observed to be cheap. Nothing else. Do not run
any 2D or 4D cell, and do not run any other variant; those are hours to days and are the user's
call to start, not yours.

Report per cell: `total_parameter_fits`, `total_ode_solves`, `total_loss_evals`, `n_levels`, and
loss. Then update §5 of `docs/hpc_requirements.md` so the 1D row rests on these counts instead of
on the scaling step, and adjust §1 and the total if the measurement moves them.

**On timing:** wall-clock measured on this laptop is not evidence and must not enter the cost table
as though it were. The project rule is that cost claims rest on counts. If §5 needs a counts-to-
core-hours conversion at all, it must be labelled as the assumption it is, and the request for a
pilot allocation in §5 stays — it is the only thing that can produce a trustworthy timing figure.

---

### Constraints

- Do not modify `estimate_stage_caps`, the cap policy, the variant definitions, or any ground-truth
  RHS function.
- Do not write to `studies/regression/history.jsonl`.
- Six cells, listed above. No sweep, no additional cells "for completeness".
- Generated output goes to its own subfolder under `outputs/`.
- If any part of this is not implementable as stated, stop and report the conflict rather than
  delivering a subset silently. WP-G1 delivered a subset without saying so, which is what made it
  expensive to notice.

### Deliverable

The merge fix, the deterministic optimizer budget, the updated `docs/hpc_requirements.md`, and a
report at `codex/REPORT_WP_B3.md` covering: the merge-semantics decision and its reasoning, the new
`config_fingerprint`, the calibration evidence for the budget and the confirmation that the WP-B1
cell is unchanged, and the six measured cells with their counts.
