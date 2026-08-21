# EvoODE — Phase B Compute: measured cost model and resource profile

*Rewritten 2026-08-21 from measurements. The previous version was a pre-access resource request
written for a Slurm site with laptop-derived estimates; it was superseded in full. What that
document asked for has been granted, and every number it estimated has now been measured.*

**Scope.** This document holds one thing: what the Phase B campaign costs, how that number was
derived, and where it is still blind. The mechanics of getting code onto the cluster live in
`docs/hpc_deployment_guide.md`; the chronology of the measurements lives in `DIARY.md`.

---

## 1. The number

| Item | Value |
|---|---|
| Campaign | `paper1_phaseB_v1` — 63 systems × 2 conditions × 3 seeds × 2 IC sets = **756 cells** |
| Projected compute | **~3,384 core-hours** on a `pretune_on` basis — see §3 for the correction |
| Platform | SCCH "Orion", OpenShift/Kubernetes, 96 cores across two worker nodes |
| Agreed concurrency | `parallelism: 16`, raise on request |
| Wall time at 16 | **~9 days** (3,384 / 16 ≈ 212 h) |
| Makespan floor | **68 h** — the longest single cell; no parallelism gets the campaign under 3 days |
| Cores per cell | 1, explicitly single-threaded |
| Memory per cell | ~1 GB resident, 2 GB requested |
| Storage | < 10 GB total, ~50 MB read-only input |
| Walltime limit | none on Orion, therefore **no checkpointing needed** |
| Software | Julia 1.12.6, pinned; no MPI, no GPU, no licensed components |

---

## 2. Where the number comes from

The projection rests on the **pilot**: 42 unique cells from `pilot_e20af80`, `pilot_sweep_tasks` and
`pilot_sweep3_tasks`, plus 888 level intervals from the heartbeat files. Coverage is systems 24–62,
seed 42, IC set 1, `pretune_on` only. All records `error = null`.

**On the admissibility of timing.** Design Principle 7 in `CLAUDE.md` forbids wall-clock as
evidence and names its own exception: *"If a claim genuinely requires timing, measure it on a
dedicated machine."* Orion gives each job a dedicated core with no suspend and no competitor. The
measurements below are therefore admissible for **capacity planning** and are **not** admissible for
method comparison. Everything in this document is a planning quantity, never a statement about
variant performance.

### The old estimate held in the sum and failed in the distribution

| Dimension | Estimated s/cell | Measured median | Measured mean | Verdict |
|---|---|---|---|---|
| 1 | 170 | 250 s | 250 s | usable — but only System 1, n = 3 |
| 2 | 20,900 | 684 s | 10,440 s | median 30x too high, mean 2x too high |
| 3 | 41,700 | 22,400 s | 63,800 s | **too low** by 1.5x on the mean |
| 4 | 83,500 | — | — | 36x too high — only System 62, two records: 4,279 s and 300 s |

Projected over the 756 Phase B cells with measured per-system means, and for unobserved systems the
mean of their dimension class: **3,384 core-hours** against the 3,900 previously estimated. The
estimate was **15 % high**, not, as this project claimed for a while, "one to two orders of
magnitude too high".

That earlier claim came from the head of the distribution — System 24 finished in 10 s against
20,900 s estimated — and does not survive the full sweep. The distribution is extremely skewed:
dimension 2 has a median of 0.19 h and a mean of 2.90 h, a factor of 15 between the two. **Planning
from median cells underestimates this campaign by an order of magnitude.** The correct planning
quantity is the mean; the correct risk quantity is the tail.

### The tail is where the campaign lives

Three chaotic systems dominate everything: System 59 (Rössler) 68.0 h, System 61 (Chen-Lee) 49.4 h,
System 56 (Lorenz) 40.0 h under `pretune_on`. They are also the reason the pilot consumed **281
core-hours** against the ~50 announced to the site — a factor of 5.6, no damage done, but to be
announced correctly next time.

Per-cell cost grows with structure size, monotonically and over three orders of magnitude. System 59
by level, in seconds:

```text
Level  1..8    49  107   60   74  107  115   91  129
Level  9..16  6214 3985 9532 4468 4482 6035 3473 2917
Level 17..24  3630 2858 3348 5996 4373 6278 8021 11538
Level 25..30 25462 20960 21524 30075 16658 42372     = 11.8 h in the last level alone
```

This is a trend, not an outlier: in the most expensive cells the slowest single level is only
17–26 % of the cell. Expensive is the **whole second half**, and any capacity plan must assume that
a cell is dominated by its final levels.

---

## 3. `pretune_off` — the other half of the campaign

The pilot ran `pretune_on` only, and the 3,384 core-hours were carried as a **lower** bound on the
assumption that the missing warm start makes the other half more expensive. Three probe cells
settled it, and the assumption was wrong:

| System | `pretune_on` | `pretune_off` | Runtime factor | Evaluation factor |
|---|---|---|---|---|
| 61 Chen-Lee | 49.41 h | 14.73 h | **0.30** | 0.73 |
| 56 Lorenz | 39.95 h | 38.68 h | 0.97 | **0.56** |
| 59 Rössler | 68.04 h | 62.35 h | 0.92 | 0.90 |

`pretune_off` is **cheaper on all three**, so 3,384 core-hours is an upper rather than a lower
bound — at least for dimension 3, which is where the cost of this campaign sits.

**But there is no factor to apply.** 0.30 against 0.97 against 0.92 within one dimension class, all
three chaotic. The cost model may state a **range**, never a single multiplier. Planning figure:
the campaign will consume **between roughly 2,000 and 3,400 core-hours**, and the upper end is what
should be reserved.

**And counts do not convert into core-hours.** On System 56 evaluations fall 44 % while runtime
falls 3 % — deriving core-hours from that count is off by a factor of 15. On System 59 the two track
each other (0.90 against 0.92); on System 61 runtime falls three times faster than the count. Cost
per evaluation varies by more than a factor of two *inside* one dimension class, plausibly through
differently stiff parameter regions. Counts remain the correct evidence for **search effort** and
are demonstrably unusable as a proxy for **compute time**.

---

## 4. What the projection is still blind to

1. **Systems 1–23 rest on a single measured system** (System 1, 3 records), and System 63 on none.
   That is 276 of 756 cells projected from one system — cheap cells, so the absolute risk is small,
   but the row is an assumption, not a measurement.
2. **One seed, one IC set.** Where seed spread was measured it is large: System 62 takes 4,279 s at
   seed 42 and 300 s at seed 123 — a factor of 14 at identical configuration.
3. **Dimension 4 rests on two records of one system**, which disagree by that same factor of 14.
4. `pretune_off` rests on three cells of one dimension class (§3).

None of these blocks the campaign. Orion has no walltime limit, capacity was confirmed as
sufficient, and a mis-projected class costs calendar days, not results.

---

## 5. A third to a half of this compute contributes nothing

Measured over 287 cells and 599.6 h of recorded runtime (WP-B1, `docs/WP-B1.md`), the share of
runtime spent in levels that improve nothing:

| Dimension | Levels per cell | Silent levels | Share of runtime |
|---|---|---|---|
| 1 | 10.8 | 2.3 | 10 % |
| 2 | 17.9 | 7.1 | **50 %** |
| 3 | 25.3 | 8.6 | 44 % |
| 4 | 19.8 | 18.5 | **96 %** |

This is **not** treated as a cost lever for this campaign. A global "stop after k silent levels" was
evaluated and rejected at every threshold: k = 3 saves 94 % of the runtime and costs 152 of 287
cells a materially worse result; k = 5 saves 37 % against 23 damaged cells; k = 8 saves 15 %. The
decision (2026-08-21) is to run at 30 levels and **report the waste as a result** rather than to
introduce a second constant that does not follow from the data. See `CLAUDE.md`, *Settled*.

For capacity planning this means the figures in §1 to §3 are the ones to reserve against, and they
already contain the waste.

---

## 6. Resource profile per cell

| Resource | Value | Basis |
|---|---|---|
| Cores | 1 | single-threaded by design; parallelism comes from the Indexed Job |
| Memory | ~1 GB resident, 2 GB requested | Julia runtime plus the ODE solver stack, no large data structures |
| Disk I/O | negligible | one small JSON record and an append-only heartbeat per cell |
| Network | none at runtime | needed once at image build time, in GitLab CI |
| Scratch | none | |

A cell is a **pure function of its inputs**: it reads a small read-only JSON dataset, writes one
JSON record plus a heartbeat log to NFS, and shares nothing with any other cell. No communication,
no shared state, no ordering constraint. Cells may be scheduled in any order, restarted
individually, and interleaved with other users' work; a failed cell is simply re-submitted.

**Thread oversubscription** is the one operational trap: Julia and OpenBLAS both default to all
visible cores. `JULIA_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS=1` are set explicitly in the image.

---

## 7. Reproducibility constraints that affect scheduling

These are properties of the study, not requests, but they constrain how cells may be run.

- **Every cell is deterministic given its seed.** The optimizer safety brake is a deterministic
  count budget — `max_loss_evals = 20,000` per parameter fit — never a wall-clock limit. Results are
  therefore independent of node speed, and heterogeneous nodes are unproblematic.
- **All cells of a campaign must run from one code version.** Publishability requires one git commit
  hash, one `config_fingerprint` **and** one `stage_cap_behavior_fingerprint`. A campaign with mixed
  identity is not publishable and has to be re-run — this has already cost one regression suite.
  Current Phase B values: `604e79733b22d64d` / `ffb0266c7913352c`.
- Pilot, probe and regression records carry **different** fingerprints by construction. They are
  valid infrastructure and cost measurements and must never be merged into campaign data.

---

## 8. What has been consumed so far

| Run | Cells | Core-hours | Purpose |
|---|---|---|---|
| Pilot | 42 | 281 | this cost model |
| `pretune_off` probe | 3 | 116 | §3 |
| Regression, two rounds | 240 | — | correctness of the final variant |
| **Phase B campaign** | **756** | **~2,000–3,400 projected** | the paper |

The campaign itself has **no records yet**.
