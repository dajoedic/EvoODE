# Side project WISP — protocol Q9-ABL: ablations and design alternatives on the full Q9 grid

**Frozen 2026-11-17, before any Q9-ABL number exists.** Decided by the user the same day: the paper's Figure 6 must
rest on the final run's data, not on the Q8 subset ("Das MUSS rein"), and all five arms of the figure are repeated.

## 1. Why

Figure 6 of the WISP manuscript shows three ablations and two design alternatives on the Q8 subset (σ ∈ {1, 5} %,
ρ ∈ {0, 0.5}, realization 1; 408 noisy dim-1/2 data sets per arm). The final configuration chose identically in Q8 and
Q9 on all 588 shared data sets (`DIARY.md` 2026-11-17), so the subset is a strict part of the final data. It is still
a subset: two of five noise levels and one of three realizations. Q9-ABL repeats the five arms on exactly the noisy
dim-1/2 data sets of Q9, so that Figure 6 and the main results rest on the same 3,060 data sets.

## 2. Arms

Settings exactly as Q8 (`build_sideproject_q8_paths.ARMS`), the Q8 fit function unchanged (`q8_fit`):

| arm | initial state | bound | start | refit | path |
|---|---|---|---|---|---|
| `no_foba` | estimated | 1000 | weak | yes | forward-only (backward loop disabled, Q8 `FORWARD`) |
| `random_start` | estimated | 1000 | `0.1 · randn`, seed from cell and candidate id | yes | Q9 path |
| `no_refit` | setting "estimated", but without a fit the first observed sample is used | 1000 | weak coefficients simulated, clamped to 1000 | no | Q9 path |
| `C10` | estimated | 10 | weak | yes | Q9 path |
| `A1000` | first sample | 1000 | weak | yes | Q9 path |

The reference is Q9 `C1000` on the same data sets (already computed). Size rule (c) selects in every arm.

## 3. Grid

All dim-1/2 systems (51), both initial conditions, the ten noisy conditions σ ∈ {1, 2, 3, 4, 5} % × ρ ∈ {0, 0.5},
realizations 1–3: **3,060 data sets per arm, 15,300 cell-arms.** No clean or subsampling-only cells (Figure 6 is on
noisy data), no dimension 3 or 4 (as in Q8). Data: the C-6 export, read by hash, as in Q9.

One shard is one data set with all five arms (3,060 shards), ordered by planned cost, descending. Planned cost:
measured Q8 solve seconds per candidate, per arm and system (planning only, never evidence).

## 4. Controls (technical, before any rate is read)

1. **Q8 identity.** On the 408 noisy dim-1/2 data sets that Q8 also ran, every arm must reproduce the Q8 records:
   same candidates, bit-identical fitted parameters, training loss and clean reconstruction/generalization loss.
   Checked on the laptop for a sample before the image is built, and on all 408 × 5 after the run. A failure stops the
   evaluation and is reported.
2. **Path identity.** The non-`no_foba` arms use the Q9 candidate lists unchanged (hash per cell); `no_foba` paths of
   the 408 Q8 data sets equal the Q8 `no_foba` paths.
3. Completeness: 3,060 shards, every candidate of every cell-arm present; settings fingerprint per arm constant.

## 5. Reporting

Descriptive only, as in Q8 §5: an ablation explains a component, it does not decide one. **C10 and A1000 were decided
by the frozen G2 rules on Q8 (2026-11-07); Q9-ABL reports them and does not reopen G2**, whatever the numbers show.
Per arm × stratum (dim 1/2 exact, dim 1/2 surrogate) × metric (structure, raw structure, reconstruction,
generalization; structure on exact systems only, Design Principle 8/9): pooled rate with the Q9-A cluster bootstrap
over systems (10,000 resamples, seed 20261110), and the paired per-system difference to C1000 with the Q9-A sign-flip
test, reported unadjusted and labelled descriptive. Cost: candidates, loss evaluations, ODE solves per arm.
Figure 6 and Sect. 6.3 of the manuscript switch to these numbers; the Q8 ablation numbers move to the supplement as
the subset they were.

## 6. Cost and slot

Planning from Q8 fit times scaled to 3,060 data sets: no FoBa ~1,500, random start ~2,000, no refit ~0 (simulation
only), C10 ~930, A1000 ~630 core-h; **~5,100 core-h (≈ 7,600 €)**, about 6 days at 40 cores plus the tail. Slot:
after Q9's stragglers and Q-B (B1, B3), on every freed core, before 31.12. (user, 2026-11-17: first exception to "no
cores after Q-B"). No time limit (CLAUDE.md, run locations).

## 7. Implementation

- Paths: `analysis/scripts/aggregate/build_sideproject_q9_ablation_paths.py` (reuses `build_sideproject_q8_paths`
  unchanged: `build_path`, `FORWARD`, `ARMS`).
- Fits: `studies/regression/sideproject_q9_ablation_fits.jl` (includes `sideproject_q8_fits.jl`, calls `q8_fit`
  unchanged; checks protocol, protocol hash, export index hash and per-arm settings).
- New image (GitLab push by the user), manifest `k8s/sideproject_q9_ablation_job.yaml`.
