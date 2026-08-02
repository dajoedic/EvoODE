# CURRENT TASK

**Language: Python**

## WP-P3.1 — ODEBench system classification (Phase 3)

### 1. Purpose

Phase 3 of `PAPER_1.md` requires all 63 ODEBench systems to be classified into **exact**
(representable in the staged basis) and **surrogate** (not representable), because the two
categories must never be mixed into a single structure-correctness metric. Today only the
ten benchmark systems in `benchmarks/benchmark_evogrow.jl` carry that information, and it
was entered by hand.

This work package derives the classification for all 63 systems from
`benchmarks/data/strogatz_extended.json` and writes it as a committed analysis artifact.

It is a data-analysis task with no effect on the algorithm. Nothing under `src/`,
`studies/` or `benchmarks/` may be modified.

### 2. Input

`benchmarks/data/strogatz_extended.json`, a list of 63 entries. The relevant fields:

- `id`, `dim`, `eq_description`
- `substituted` — the equations with constants already substituted, as a list of initial-
  condition sets, each a list of `dim` expression strings, e.g.
  `"0.303030303030303 - 0.360750360750361*x_0"`. Use the **first** set; the expressions are
  identical across sets apart from the initial condition, but verify that assumption and
  report if it does not hold.
- `init`, `source` for reference.

Variables are named `x_0 … x_{dim-1}`. The project basis uses `u1 … u_dim`, so the index
shift by one must be handled explicitly and stated in the output.

Scale of the problem, from a scan of the file: 63 systems, 117 equations, dimensions
1/2/3/4 with counts 23/28/10/2. Operators appearing across the equations: `**` 42 times,
`sin` 16, `cos` 8, `exp` 6, `log` once, `cot` once, `Abs` once.

### 3. Reference basis

`default_staged_polynomial_basis(dim)` in `src/basis/staged_polynomial.jl`, five stages:

1. linear `u_i`
2. self-quadratic `u_i^2`
3. cross terms `u_i*u_j`, `i < j`
4. self-cubic `u_i^3`
5. trigonometric `sin(u_i)`, `cos(u_i)`

Note what the basis does **not** contain, because these are the decisive gaps: there is no
constant term, no `exp`/`log`/`cot`/`Abs`, no powers other than 2 and 3, no trigonometric
argument other than a bare variable, and no mixed cubic such as `u_i^2*u_j`.

### 4. Method

Parse each equation symbolically rather than by string matching — `sympy` is the natural
tool. It is not currently in the analysis dependencies; add it to
`analysis/requirements.txt` and say so in the report.

For each equation: expand the expression into additive terms, and classify every term as
either a basis term (recording which one and its stage) or out-of-basis (recording why).
Derive:

- per equation: the set of matched basis terms, the list of unmatched terms with a reason,
  and `expected_eq_stage` = the maximum stage over the matched terms if the equation is
  fully representable;
- per system: `representability` = `exact` if **every** term of **every** equation maps to
  a basis term, otherwise `surrogate`; `expected_stage` = maximum over equations for exact
  systems.

Use a controlled vocabulary for the gap reason — for example constant offset, unsupported
function, unsupported power, unsupported trigonometric argument, mixed higher-order term —
and report the frequency of each. Do not invent a free-text reason per system.

### 5. Validation against the hand-entered ground truth — mandatory

`benchmarks/benchmark_evogrow.jl` already carries `representability`, `expected_stage` and
`expected_terms` for ten systems (ids 2, 3, 11, 23, 24, 26, 31, 37, 54, 63), entered by
hand and used in every result so far. Compare the derived classification against those ten
and report each agreement and disagreement individually.

**Any disagreement is a finding, not a nuisance to be smoothed over.** It means either the
parser is wrong or a hand-entered value that current results depend on is wrong. Report it
prominently and do not adjust the parser to force agreement — investigate and state which
side is wrong.

Expected agreements to check specifically: system 23 is surrogate because of a constant
offset, system 37 is surrogate because of the mixed cubic `u1^2*u2`, and systems 2, 3, 11,
24, 26, 31, 54, 63 are exact with expected stages 1, 2, 4, 1, 3, 3, 3, 3.

### 6. Output

`analysis/data/paper1_phaseB_v1/system_classification.csv`, one row per **equation**, with
the system-level fields repeated, carrying at minimum: system id, dimension, description,
equation index, the equation string, representability of the system, expected stage of the
system, expected stage of the equation, matched basis terms, unmatched terms, gap reason,
and the source field.

Plus a short report under `docs/` giving: the exact/surrogate split with counts, the
distribution of expected stages over the exact systems, the frequency of each gap reason,
the dimension breakdown of both categories, and the full validation table against the ten
hand-entered systems.

Follow `analysis/CONVENTIONS.md` for naming and structure.

### 7. Why the split matters, so the output is fit for purpose

The exact systems determine how many systems Paper 1 can even report structural recovery
on — if that number is small, it changes what the paper can claim, so the count is a
result in itself and must be stated plainly rather than buried in a CSV. The surrogate
systems are evaluated only on stage reached, target-term usage and fit quality.

### 8. Execution

Cheap: parsing 117 expressions, no simulation. Run it and report the actual numbers. If it
takes more than a few minutes, stop and report.
