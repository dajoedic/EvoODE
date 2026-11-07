# Side project WISP — protocol for Q9: the final run (plan step W-4)

**Frozen 2026-11-07 before any Q9 number, on the user's instruction ("Bau dann Q9 … alles selbstständig") after
gate G2.** Parts before: Q5 (pipeline), Q7 (path end, G-Q7 passed 2026-11-05), Q8 (`_q8.md`; G2 decided 2026-11-07,
`DIARY.md`). Q9 is the single run every WISP number in the paper comes from. It adds no new component and decides
nothing about the method; it measures the frozen configuration on the full benchmark.

## 1. The method (frozen at G2)

WISP exactly as Q8 arm **C1000**:

1. weak-form design and basis as WP-FA2 (canonical basis with constant), one equation at a time;
2. growth path by FROLS steps with FoBa backward checks (ν = 0.5), ending by the **Q7 significance stop**
   (χ² threshold 6.635, the frozen Q7 §3 rule) on every system, exact or surrogate;
3. every path state is a candidate; one `fit_parameters` call per candidate from its weak-form start,
   `max_fit_attempts = 1`, **initial state estimated jointly** (variant C, start = first observed sample, unbounded),
   **coefficient bound `[-1000, 1000]`**;
4. selection by size rule (c), trajectory BIC (penalty: coefficients + d, constant within a cell); (a) weak BIC and
   (b) EvoGrow objective reported.

Bound 1000 is a **declared deviation** from the frozen Q8 rule R2 (which selected bound 10 by one cell in one of six
comparisons); reasons in `DIARY.md` 2026-11-07. Both Q8 arms are reported beside Q9.

## 2. Data

C-6 export `phase_c_c6_data_conditions_5dd1df8`, unchanged (index sha256 `ce20350b…`). **All 63 systems, both
training ICs (126 units).** Per unit: the 11 noisy/subsampled conditions (σ, ρ) ∈ {0.01, …, 0.05} × {0, 0.5} plus
(0, 0.5), each in realizations 1, 2, 3, plus the clean cell (0, 0) once (realizations 2, 3 of the clean cell are
byte-identical to realization 1 and are not refitted). **4,284 cells, one arm, one shard per cell.** Evaluation
unchanged from Q5/Q8: reconstruction from the clean training IC, generalization from the clean other IC, clean grid.

## 3. Metrics, strata, references

As Q5 §4–§5 and Q8 §6. Strata by dimension × representability (exact / surrogate), dim 3 exact additionally split
into 52, 61 (feasible under bound 10) and 54–59. Exact systems: raw and pruned structure **and** R² > 0.9
reconstruction and generalization (variance-weighted primary). Surrogates: R² > 0.9 only. Primary unit of inference:
**systems as clusters** (plan W-6); cells are never treated as independent. References on the same cells, existing
data, no new baseline run: SINDy, Weak-SINDy, E-SINDy (WP-N47, matching library, threshold per stratum × σ × metric)
and WSINDy from the MATLAB original (W1 on ρ = 0, W1-interp on ρ = 0.5, L-Q5). Cost: candidates, fits, loss
evaluations, ODE solves (wall-clock is never evidence).

## 4. Execution

Orion, image built from the commit that adds this protocol, indexed Job, one shard per cell, shards in descending
planned cost (planning from measured Q8 C1000 solve seconds per candidate per system; systems without a Q8 timing —
53, 60, 62, 63 — get the maximum per-candidate time of their dimension so they start early). No deadline, no hard
cut. **Probe first**: one shard per stratum block (the cheapest cell of the block's median unit), technically
checked (shard count, 0 failed, record count = candidate count, data hash = path file, one settings fingerprint,
provenance); if clean, the grid starts without a further gate (user, 2026-11-07). Cores: at most 40 for EvoODE in
total; Q9 takes what the Q8 stragglers leave and grows as they finish; C-6 stays at 0 until Q9 ends.

**Cost (planning, 2026-11-07):** ~8,000–10,000 core-h (≈ 12–15 k€), ~10–12 days at 40 cores; dominated by Lorenz
55, 56 and 61 (Q8: 25 / 22 / 18 core-h per cell, maximum 92 h). Accepted by the user above the plan's 3,000–8,000.
If the projection from the first finished long shards exceeds 21 days, the user decides (plan W-4).

## 5. Controls

- Path files reproduce the Q8 C1000 candidate lists bit-identically on every Q8 cell (same builder function, same
  data); checked before upload.
- Per-cell `observed_data_sha256` equal to the export index and to WP-N47 rows.
- One settings fingerprint over the whole run, equal to Q8 C1000's.
- The Q9 runner adds no fitting code: it calls the Q8 `q8_fit` unchanged; only the protocol label, the protocol hash
  and the source inventory differ.
