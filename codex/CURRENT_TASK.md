# WP-X2 — WISP explorable: complete the story (stop, fit + BIC, generalization, failure), German + English, curves from the Julia evaluation
**Language: Python** (data export, build, checks) and **Julia** (one display-trajectory export script, executed by Claude)
— the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-02. Follows WP-X1/X1b/X1c (reports in `codex/reports/REPORT_WP_X1*.md`; commit `6a0e352`). Preview of the
current state: the user likes it ("schaut schon ganz cool aus") and wants it **complete**, in **German and English**.
Every rule from WP-X1/X1b/X1c stays in force (whitelist, blind rule, no Q7/Q8 *results*, no hand-typed result numbers,
both metrics side by side, strata never pooled, exact/surrogate never mixed in a structure metric, byte-identical
rebuild, results contract and swap test).

## Read first

- `docs/kochbuch/Kochbuch_WISP.html` — German plain-language walkthrough; its sections "Aufhören", "Fitten",
  "Wählen (BIC)", "Abschmecken", "Drittes Beispiel: wenn es schiefgeht" and "Was wir über das Aufhören gelernt haben"
  are the content source for the new sections (content only — the German text is a translation of the English page,
  not cookbook-style prose).
- `docs/sideproject_residual_growth_protocol_q5.md` §3 (pipeline, size rule (c) trajectory BIC primary) and
  `docs/sideproject_residual_growth_protocol_q7.md` (the significance stop rule) and `_q8.md` §2–3 (variant C, bound).
- `analysis/scripts/aggregate/build_sideproject_q7_paths.py` — reference implementation of the Q7 stop rule.
- `studies/regression/sideproject_q5_noise_fits.jl`, `studies/regression/sideproject_q4_path_fits.jl`
  (`q4_evaluate`) and `src/simulate/solve.jl` — the evaluation path that produced the stored R².

## Scope

### 1. Bilingual: one page, German and English

- One built file with a visible language switch (EN | DE) in the masthead. Initial language: a `lang` URL parameter or
  hash if present, else the browser language (German if it starts with `de`, else English); the choice is remembered
  in `localStorage` wrapped in try/catch (the page must work when storage is unavailable).
- All user-visible text lives in two string tables (`explainer/wisp/src/i18n/en.json`, `de.json`) with identical keys;
  the HTML template and `app.js` contain no prose. Math, data and numbers are shared. Number formatting follows the
  language (German decimal comma, thousands separator).
- **The German version is a faithful, understandable translation of the English text** (user correction 2026-11-02:
  "Deutsch darf ruhig auch technisch sein — einfach übersetzen, dass es verständlich ist"). Same content and structure
  as English, no separate rewrite and no simplified tone; technical terms are fine. Correct, natural German grammar
  (no word-by-word calques), established terms where they exist (Differentialgleichung, Rauschen, schwache Form,
  Restfehler, Kandidat, Rekonstruktion, Generalisierung). Method names stay as they are (FROLS, FoBa, BIC, SINDy,
  Weak-SINDy, E-SINDy, WSINDy).
- Tests: key parity between the two tables; no untranslated key at runtime in either language (Node DOM harness renders
  both languages and checks that no key name or empty string reaches the DOM); the `<html lang>` attribute switches.

### 2. Display trajectories from the Julia evaluation itself (replaces the Python re-simulation for display)

WP-X1c showed that a Python integrator cannot reproduce the stored R² (Julia `Tsit5`, abstol = reltol = 1e-6) to 1e-6:
only 922 of 1,632 cells got curves. Fix by construction:
- Write `studies/explainer/export_wisp_display_trajectories.jl`. It reuses the **exact** Q5 evaluation code path
  (`q4_evaluate` and what it calls — same simulate call, same optimizer settings, same clean reconstruction and
  opposite-IC generalization targets as `sideproject_q5_noise_fits.jl`), for: (a) the chosen candidate (rule (c)) of
  every Q5 cell, and (b) **every** candidate of the featured cells listed in Scope 3. It writes the predicted
  trajectories on the full target grid plus the recomputed R² (arithmetic and variance-weighted, reconstruction and
  generalization) to `outputs/wisp_explainer_julia/` (one compact file, e.g. JSON lines or a binary with an index;
  document the format). It must not fit anything — parameters come from `q5_units.csv` / `q5_candidates.csv`.
- Pass gate: recomputed R² equals the stored value to **1e-12** absolute in all four scores (same code, same inputs —
  anything else is a defect to report, not to tolerate). Cells that fail or whose stored score is empty keep curves
  withheld, as now; the report lists them with the reason.
- Codex cannot run Julia here (`codex/CODEX_PROTOCOL.md`). Write the script, verify it by reading, and add a
  **written expected runtime** to the report (estimate from counts: cells × candidates × solves). Claude runs it. The
  Python data export reads the Julia output when present; when absent it keeps today's WP-X1c behaviour, so the build
  never breaks. Keep the WP-X1c Python check as a secondary diagnostic only.
- Display thinning (48 points, 5 significant digits) stays.

### 3. The missing sections (replace the three placeholders)

Choose **featured cells** from the Q5 grid and record the choice and the reason in the manifest. At least: the
running example `sys0003_ic1_s0.03_r0_n1`; one dim-2 cell (predator–prey or another readable dim-2 system) where the
chosen structure is exact; one cell where the **truth is not on the path** (`truth_on_path = False`) for the failure
story; one cell where reconstruction is good but **generalization fails** (high reconstruction R², low generalization
R²). Pick them by a rule written in the report before looking at which systems come out (e.g. the lowest system id
satisfying the condition at a stated σ), not by taste.

6. **Where to stop.** Why a path has to end (each extra term always lowers the training error a bit → overfitting).
   Interactive: on the live path, show the remaining weak error per step against the noise level the data can explain.
   Present **both** path ends that exist in the project and say plainly which is the current state:
   - the interim 6-term cap (Q5) — honestly described as taken from the truth (twice the largest true equation size),
     a declared limitation;
   - the Q7 significance test ("a term only joins if it brings more than noise plausibly could") — implemented live in
     JS for the featured dim-1 cells, reproducing `build_sideproject_q7_paths.py` on them (same check style as WP-X1b:
     identical stop step, exit non-zero on mismatch), **but no Q7 result rate anywhere**.
   - A data-driven status line: "Which rule WISP uses is decided at gate G-Q7" — driven by a field in the data so that
     after the decision only data changes.
7. **Fit every candidate, then choose (BIC).** Every path state is a candidate; each gets one trajectory fit started
   from its weak coefficients. Interactive: a candidate scrubber over the featured cell's path — for each candidate its
   equation (formatted, with coefficients), its simulated trajectory over the data (from the Julia export), its fit
   error and its BIC; a chart BIC vs number of terms with the chosen one marked; a clear explanation of the trade-off
   (fit vs size, the penalty per term) for laypeople. Mention initial-state estimation (variant C) and the coefficient
   bound only as "decided at gate G2", data-driven like the stop status.
8. **The real test: a second starting point — and what failure looks like.** The cookbook's "fridge" idea: the second
   trajectory is never used for training. Show reconstruction vs generalization for the featured cells side by side
   (trajectory over clean data from the other initial condition). Then the two failure stories with their real cells:
   (a) truth not on the path (show the path's terms vs the true terms), (b) fits the training curve, fails the second
   starting point. End with an honest "what WISP cannot do yet" paragraph from the cookbook's open points.

### 4. Results explorer and claim markers

- Keep the explorer as is (contract version bump only if needed). In the drill-down, curves now come from the Julia
  export.
- **Narrow `data-claim`:** today every paragraph carries it, which defeats its purpose. Mark only sentences (in both
  languages, by string key) that **interpret a result or a comparison**; explanations of the method carry no marker. A
  test lists the marked keys and fails if a marked key exists in one language only.

### 5. Polish

- Section 5 residual chart: at step 0 it shows an empty plot with a negative y-axis; show a sensible state (the
  starting point at 100 %, y-axis from 0).
- Re-check every figure in both languages at 360 px and 1280 px for overflow (long German words!). Use hyphenation
  (`hyphens: auto` with the correct `lang`) where needed.
- Size budget: built HTML ≤ 14 MB (hard publish limit 16 MB), `explainer/wisp/data/` ≤ 17 MB.

## Forbidden

Everything WP-X1/X1b/X1c forbade. In particular: no C-6 EvoGrow result; **no Q7 or Q8 result rate or result file**
(implementing the Q7 stop *rule* live on featured cells is allowed and required); no fitting in the Julia script; no
change under `src/`, to `sideproject_q4_path_fits.jl`, `sideproject_q5_noise_fits.jl`, or any existing analysis script
or output; no git operations; nothing running longer than 15 minutes in your session.

## Acceptance

1. Data export and assembly exit 0; rebuild byte-identical; size budget met (test).
2. Strict JS checks exit 0: WP-X1b FROLS/FoBa reference cells, plus the Q7 stop step on the featured dim-1 cells.
3. Julia script present, reviewed, expected runtime written; Python export consumes its output when present and is
   unchanged in behaviour when absent (test with a small fixture written to a temp dir).
4. Featured-cell selection rule written in the report and reproduced by a test from `q5_units.csv`.
5. i18n tests (key parity, no raw keys, `lang` switch) and narrowed claim-marker test pass; all earlier tests pass.
6. Report `codex/reports/REPORT_WP_X2.md`: what was built, featured cells and rule, Julia script format and expected
   runtime, all check results, open points. Status `blocked` is correct **only** for "Julia not executable here —
   environment, not the task"; say so in `note` if that is the only open item.
