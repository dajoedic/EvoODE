# WP-X20 — WISP explorable: results on Q7, WSINDy comparison, chapter 9 „Wie oft klappt das?“
**Language: Python** (exporter, build, tests) + **Julia** (display export for Q7 chosen models; Claude runs it)

Stand 2026-11-05. Follows WP-X19 (version 24 (`3da07fb`): intro, chapters 1–8). All explorable rules stay in force (German +
English, `data-claim="review"`, no scientific number as an editorial literal, results contract v2 untouched in shape,
byte-identical rebuild, fixed-topology interpolation, no overlaps, x/y titles, locale formatting without exponent
notation, looping animations with 3 s hold, reduced motion, deterministic `seek`, ≥ 14 px rendered text, separate
block chips). Project rules that bind the results: **always both metrics** (structure recovery and the R² > 0.9 rate,
side by side, never one alone); **exact and surrogate systems never mixed** (structure metrics only for exact strata);
**strata never pooled**; reconstruction and generalization separately; numbers are copied from the aggregation, never
recomputed by the page or the adapter. Codex cannot run Julia here: write it, do not run it, leave Claude the commands.

**Test policy:** exporters and data change → the full `-k wisp` suite once at the end (after Claude's Julia run;
Claude runs it if you cannot); fast presentation tests while iterating.

## Why

G-Q7 passed on 2026-11-05: the significance rule Q7 replaces the 6-term cap; Q7 is the current WISP version. The
results explorer still shows Q5 (interim, superseded). The single authorized comparison file
`analysis/data/sideproject_residual_growth/q7_q5w_comparison.csv` now exists (original MATLAB WSINDy W1 and
W1-interp, two library variants), so the reserved comparison slot can be filled.

## Part A — results.json on Q7

- Switch the results source from the Q5 grid to `analysis/data/sideproject_residual_growth/q7_grid/`
  (`q7_rates.csv`, `q7_units.csv`, `q7_candidates.csv`, `q7_run_metadata.json`), same results contract v2:
  `primary_method` = `Q7`, `provenance.protocol` = `Q7`, `provenance.status` = `interim` (the final numbers come from
  Q9 after W-4; say so in the provenance note), campaign/commit/hashes from the Q7 run metadata. Baselines (SINDy,
  Weak-SINDy, E-SINDy, WP-N47) unchanged.
- Fill `comparison` from `q7_q5w_comparison.csv` exactly as the adapter contract describes (copy rows, `comparison`
  as configuration, no rates computed). Method labels: „WSINDy (MATLAB-Original) W1 / W1-interp, Bibliothek C-6 /
  Q5“ (English accordingly). Provenance note for these rows: original MATLAB code, re-run under the JKU licence on 2026-11-05
  (plan item W-6b), byte-identical to the earlier run — show the source and that note in the provenance panel.
- Drill-down cells: from the Q7 records (chosen candidate per cell), same cell contract. Display curves only from the
  Julia display export: extend `studies/explainer/export_wisp_display_trajectories.jl` to evaluate the **Q7 chosen
  candidate** of every results cell (evaluation only, `q4_evaluate`/`simulate`, no optimizer), into a new file
  (e.g. `outputs/wisp_explainer_julia/q7_results.jsonl`), with the same pass/fail checks against the stored scores;
  reuse an existing Q5 record where the Q7 chosen candidate is provably identical (same cell, support, params) —
  state how many were reused vs evaluated. Provide a cost estimate for the Julia run in core-minutes from the Q5
  display run if its log/metadata has timing; otherwise count ODE solves.
- Featured cells and chapters 1–8 keep working; if any featured narrative reads Q5-only fields, keep them on their
  verified sources and document it.

## Part B — chapter 9 „Wie oft klappt das?“

Re-enable the results as a chapter in the new scroll-story style (masthead „Kapitel 9 · …“, dots), replacing the old
legacy results pages (keep them hidden or remove them if nothing references them; tests updated):

1. **„Was gezählt wird“** — the two metrics side by side (structure exactly right; share with R² > 0.9, reconstruction
   and generalization), strata (dim 1, dim 2, dim 3 feasible, dim 4; exact vs surrogate), the noise conditions, and
   that the numbers are interim (Q7, final from Q9) — all from provenance/axes data.
2. **„Ohne Rauschen“** — per stratum the two metrics for WISP (Q7) beside SINDy / Weak-SINDy / E-SINDy at σ = 0,
   from the rates (selected configuration per baseline and metric, with its exact name beneath).
3. **„Mit Rauschen“** — the same over the noise levels (σ, ρ) as small multiples per stratum: one line per method,
   both metrics as separate panels, never averaged across strata.
4. **„Gegen das Original: WSINDy“** — the comparison rows (W1, W1-interp; both libraries) against Q7 on the same
   cells, both metrics, with the provenance note.
5. **„Selbst nachsehen“** — the existing interactive explorer (Overview / By condition / Look inside a system),
   restyled to the chapter design, as the last page; the drill-down shows the Q7 chosen model, its curves (verified),
   both metrics, and for exact systems the true equation.
6. Glossary and credits pages at the end, if they exist and are current (update terms: WISP, Q7, FoBa, BIC, weak form).

Interpretive sentences only where they follow directly from the displayed rates, marked `data-claim="review"`; no
claims about which method „wins“ beyond what the numbers on that page show.

## Commands for Claude (into the report)

Julia smoke (`--limit`) into a separate file, the full Julia display export, the Python exports, the HTML build, the
full `-k wisp` suite, the fit checker — in that order, with the expected Julia runtime.

## Deliverables

Exporter + Julia extension + source changes, rebuilt HTML (Julia-pending state allowed), tests;
`codex/reports/REPORT_WP_X20.md` (sources and hashes, reuse count, comparison rows copied, chapter-9 content, commands,
test results); `codex/STATUS.md`. Do not commit. No cluster jobs.
