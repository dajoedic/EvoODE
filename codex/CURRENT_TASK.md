# WP-X13 — WISP explorable: chapter 2 "Noch ein Baustein dazu" as a scroll story
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-04. Follows WP-X12d (`344c52f`, accepted). All earlier explorable rules stay in force (German + English
via `src/i18n/*.json`, every prose node `data-claim="review"`, no scientific number as an editorial literal, results
contract untouched, byte-identical rebuild). Chapter 1 stays as it is — do not change its stages, texts or timing.

## Goal

The user approved chapter 1 ("Ein Baustein allein"). Chapter 2 tells the **second WISP step** on the same running
example (`LIVE.teaching`, cell `sys0003_ic1_s0.03_r0_n1`): a second block is added, both numbers are refitted
together, the error sinks. **User decision (binding): chapter 2 only shows "one more block, the error sinks".** It does
**not** say whether the chosen block is right or wrong, does **not** show the true equation, and does **not** mention
that the real path later swaps blocks. That reveal belongs to chapter 3 (not part of this WP). No sentence may imply
the second solution is correct or final; the closing line only points ahead neutrally (see S6).

## What the real path gives (for orientation — every number on the page is computed live, never typed in)

`W.path(teaching.t, teaching.observed, LIVE)`: step 1 support `[0]` (constant), step 2 support `[0,3]` (constant +
`u³`), step-2 gains `u³` 0.0605, `u²` 0.0523, `u` 0.0388, `cos u` 0.0003, `sin u` 0.0001 (fractions of the
no-block error); noise floor 0.716; so as share of the explainable part: constant alone ≈ 52.9 %, constant + `u³`
≈ 74.2 %, + `u²` ≈ 71.3 %, + `u` ≈ 66.6 %, + `sin`/`cos` ≈ 53 %. Weak coefficients of step 2 (recorded path,
`featured[0].path[1]`): constant ≈ 12.84, `u³` ≈ −2·10⁻⁵. Guard like `soloModel`: throw if the live step-2 support
differs from the recorded `featured[0].path[1].active_idxs`.

Gain semantics (state them correctly in the page and in the jargon line): the step-2 gain of a candidate equals the
error drop when the constant and that candidate are fitted **jointly** by least squares on all windows of all lengths
— exactly what `W.path` computes. Joint refit: the constant's number changes too (6.85 → 12.84 for `u³`).

## Pages and stage

Add chapter `two` with its own pages (`data-chapter="two"`, `data-stage="c2-…"`, ids `p-c2-…`) directly after
`p-c1-solution`, and add `'two'` to `visibleChapters`. Masthead indicator "Kapitel 2 · Noch ein Baustein dazu" /
"Chapter 2 · One more block"; progress and dots per chapter as in chapter 1. One persistent animated SVG stage for the
whole chapter (same visual language, colours, fonts, axes style and fixed-topology interpolation approach as the
chapter-1 stage; reuse its helpers, do not fork chapter 1's code into a second copy where a shared function does). The
stage's start state must match chapter 1's final visual (slope-over-time plot of the long windows with the constant
prediction line and the share bar), so scrolling from chapter 1 into chapter 2 reads as one continuation.

Six steps, autoplaying sequences, looping where chapter 1 loops, one scroll gesture per step:

- **S1 "Wo wir stehen"** — the measured slopes of the long windows (as in chapter 1), the flat prediction line
  du/dt = 6,85 from chapter 1, the share bar "Rauschen — nicht erklärbar / erklärt / noch erklärbar" with the constant's
  explained share (≈ 52,9 % of the explainable part). Text: chapter 1 found one block; about half of what is
  explainable is explained; the rest is still open.
- **S2 "Was noch fehlt"** — the residual per window (measured slope minus prediction) drawn as vertical segments from
  the line to each point; then the estimated noise band (± one standard deviation of the window slope's noise,
  derived from the frozen `W.noiseVariance`, converted to slope units for the shown window length) around the line.
  The residuals form a clear pattern (too low early, too high in the middle, too low late) that leaves the band. Text:
  the leftover is not just noise; it follows a pattern, so another block can explain more.
- **S3 "Zwei Bausteine gemeinsam"** — one worked example with the candidate `u` (a deliberately neutral choice — not
  the winner, not `u²`): the prediction morphs from the flat line to c₁ + c₂·u(t) at the joint optimum; a readout shows
  **both** numbers moving to their joint values (the constant leaves 6,85). Error bar sinks to the joint error. Text:
  WISP does not keep the first number fixed — both are determined anew together; new counts only what the first block
  does not already explain. Optional single hands-on control is **not** needed here.
- **S4 "Jeden zweiten Baustein ausprobieren"** — cycle through the five remaining blocks (catalogue order), each
  showing its joint prediction curve, while a bar per candidate grows to its explained share (of the explainable
  part, same definition as chapter 1's percent step). Winner highlighted at the end. Pace like chapter 1's "every"
  step; labels never overlap.
- **S5 "Der Fehler sinkt"** — the winner's prediction stays; the share bar animates from the constant's share to
  the two-block share (≈ 52,9 % → 74,2 %), with both values labelled. One sentence explaining what "sinkt" means in
  the chapter-1 terms (less unexplained, the noise part unchanged).
- **S6 "Die zweite Lösung"** — the equation du/dt = 12,8 − 0,00002·u³ (formatted live from the recorded step-2 weak
  coefficients; format small numbers readably in both languages, e.g. `−2·10⁻⁵` or `−0,00002`, consistently) and one
  sentence why the number in front of u³ is so small: u³ becomes large (state the live maximum of u³ over the
  observations, e.g. "bis etwa 400 000"). Closing line, neutral: "Ob das schon die richtige Gleichung ist — und was WISP
  als Nächstes tut — zeigt das nächste Kapitel." / "Whether this is already the right equation — and what WISP does
  next — is the next chapter." No other claim about correctness.

Jargon line (chapter-1 style, small): "Im Fachjargon: zweiter Schritt von FROLS; gemeinsames Neuschätzen
(orthogonale kleinste Quadrate)" / English equivalent.

Every number shown must be explained on its page (user rule). Percent always means "share of the explainable part"
as in chapter 1, and the share bar's three segments use chapter 1's labels unchanged (the user will revisit that
split later — do not redesign it now).

## Checks

- Extend `check_wisp_explainer_fit.py`'s in-page measurement (`pages.js` `measure`) to the c2 stages: stage inside
  the viewport, no visible SVG text overlaps, no annotation label over a data dot, at several sample times per
  animated step (as done for chapter 1), plus S4 bars/labels without overlap.
- Tests (pytest, `-k wisp`): chapter `two` visible, six pages in order after `p-c1-solution`, both languages carry
  every new key, no new hard-coded scientific numbers in the source (step-2 values come from `W.path`/LIVE), the
  step-2 guard exists, no page in chapter 2 contains the true equation or the words "falsch"/"richtig" except the
  neutral closing question.
- Chapter 1 unchanged: its fit-check results and tests stay as before.

Acceptance: build exit 0 and byte-identical rebuild; all tests passing; `check_wisp_explainer_js.py` exit 0; fit
checker as usual (if the browser cannot start in your sandbox, report `blocked` for that part only — Claude runs it).
Short report `codex/reports/REPORT_WP_X13.md`. Do not commit.
