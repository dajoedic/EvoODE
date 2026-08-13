# Profiling Study: Initialization Comparison (`profile_init`)

**Dates:** 2026-04-29 to 2026-05-02
**Script:** `studies/profiling/profile_init.jl`
**Status:** closed (12/12 runs)

> **Why this is still relevant.** `use_pretuning` is one of the two conditions of the Phase B
> campaign — `pretune_on` against `pretune_off`. This study is the reason that axis is investigated
> at all.
>
> **Read the runtimes with care.** The hour figures below are wall-clock from a working laptop and
> are therefore **not evidence** under design principle 7. The loss and stage findings do not depend
> on them. A later measurement on the campaign path established that on 1D systems pretuning buys
> nothing in cost terms; see `DIARY.md`.

---

## Question

Does OLS-based pretuning — a warm start from a least-squares estimate of the derivatives — give a
measurable advantage over random initialization, in final loss and in compute?

## Setup

- **Systems:** Lotka-Volterra competition (2D, expected stage 3), Lorenz periodic (3D, expected
  stage 3)
- **Seeds:** 42, 123, 7
- **Initialization modes:** `random` (zero start), `pretune` (OLS warm start before BFGS)
- **Algorithm:** EvoGrow with `StagedPolynomialBasis`, 20 levels, Paper 1 hyperparameters
- **Termination:** all 12 runs ended on `max_levels`; no run reached `loss_tol = 1e-8`

---

## Results

### Final loss and runtime

| System | Seed | random loss | pretune loss | random time | pretune time | Better loss |
|---|---|---|---|---|---|---|
| Lotka-Volterra | 42 | 2.00e-4 | 2.62e-4 | 0.28 h | 0.60 h | random |
| Lotka-Volterra | 123 | 3.19e-4 | 5.53e-4 | 3.59 h | 0.68 h | random |
| Lotka-Volterra | 7 | 4.05e-3 | **2.62e-4** | 0.56 h | 8.37 h | pretune |
| Lorenz | 42 | 14.1 | **3.14** | 5.34 h | 4.96 h | pretune |
| Lorenz | 123 | 11.3 | **2.87** | 6.46 h | 1.32 h | pretune |
| Lorenz | 7 | 16.9 | **4.06** | 8.34 h | 2.56 h | pretune |

### Mean loss across seeds

| System | random (mean) | pretune (mean) | Factor |
|---|---|---|---|
| Lorenz periodic | 1.41e+01 | **3.36e+00** | ~4.2× |
| Lotka-Volterra | 1.52e-03 | **3.59e-04** | ~4.2× |

### Final stage

| System | Seed | random stage | pretune stage |
|---|---|---|---|
| Lotka-Volterra | 42 | 3 | 5 |
| Lotka-Volterra | 123 | 5 | 5 |
| Lotka-Volterra | 7 | 4 | 5 |
| Lorenz | 42 | 2 | 3 |
| Lorenz | 123 | 2 | 3 |
| Lorenz | 7 | 2 | 3 |

---

## Convergence curves

![Convergence curves](profile_init_convergence.png)

*Best loss per level for all 12 runs. Top row: Lotka-Volterra, bottom row: Lorenz.*

---

## Interpretation

### Lorenz (3D, complex): pretuning clearly better

On all three seeds pretuning reaches a substantially lower final loss (~4×) and gets to stage 3,
while random stagnates at stage 2.

**Explanation:** on complex systems the OLS warm start supplies a substantially better initial
estimate, so BFGS converges faster and lands in better minima. The higher stage is a genuine
qualitative improvement here: pretuning enables the step into stage 3 (cross terms), which Lorenz
requires.

### Lotka-Volterra (2D, simpler): mixed

Averaged over seeds pretuning also wins (~4×), but per seed random wins on loss in two of three.
Pretuning reaches stage 5 more often, and that does **not** translate into a lower loss — the
opposite.

**Explanation:** for Lotka-Volterra (expected stage 3) pretuning drives the search deep into higher
stages, which leads to overfitting or worse stopping behaviour. The warm start may be producing an
initial estimate that is "too good", encouraging early stage promotions and destabilising the search
strategy. The result is high compute without a gain in loss.

> This observation prefigures the stage-cap work: the problem is not the initialization as such but
> escalation beyond the stage the system actually needs. The look-ahead stage cap addresses exactly
> that, and independently of the initialization.

### Critical finding: `max_levels` as the termination reason

All 12 runs ended on `max_levels`; none converged to `loss_tol = 1e-8`. That means:

1. A level budget of 20 is too small for clean convergence on these systems.
2. The losses reported here are best-effort values, not converged solutions.
3. Runtime comparisons are heavily influenced by chance — which run happens to find a good candidate
   in which level.

---

## Conclusion

The hypothesis "pretuning generally converges faster and to a lower loss" is **partially confirmed**:

- Complex systems (Lorenz, 3D): clearly confirmed, robust across all seeds
- Simpler systems (Lotka-Volterra, 2D): confirmed on the mean, unreliable per seed

**Methodological limits:** two systems, three seeds, no run converged, `max_levels` throughout. No
statistically defensible statement is possible from this data.

---

## Open questions

- Why does pretuning cause excessive stage promotions on Lotka-Volterra? Is this connected to the
  `stage_local` promotion mechanism?
- Would a larger level budget (e.g. 50) suffice for convergence?
- Does the Lorenz finding reproduce on further seeds and on similar 3D systems?

*The first question is the one that led to the stage-cap line of work.*
