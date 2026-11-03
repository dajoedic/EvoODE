# WP-X8 — WISP explorable: page 3 rebuilt from zero as "WISP at work", page 2 gets "show solution"
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X7e (commit `93b5532`, preview version 9). All rules from WP-X1..X7e stay in force
(whitelist, blind rule, no Q7/Q8 results, no hand-typed result numbers, both metrics, i18n parity, byte-identical
rebuild, swap test, size ≤ 14 MB, fallbacks, wheel routing, `data-claim="review"` on prose, no next-page-only links,
endless dish loop, page-2 flush columns, fit at 1366 × 657 and 1366 × 768). No change to `compute.js` or any data
file. Scope: pages 2 and 3 only.

## User decision (2026-11-03, version 9)

"Page 3 looks terrible, completely overloaded. Rebuild it from zero. Show the process — how WISP finds it, how it
builds it up, how it throws things out. Then forget the comparison with the reader's own solution; page 2 instead
needs a way to show the solution. Page 3 is WISP in action, step by step."

## Scope

### 1. Page 2 (`p-challenge`): "show solution"

- A third small round icon button next to reset (circular arrow) and hint (bulb): an **eye** icon, tooltip and
  `aria-label` DE "Lösung zeigen" / EN "Show solution", toggles to "Lösung ausblenden" / "Hide solution".
- On: the true equation's curve is drawn in the chart as a thin dashed line in the truth colour (above the data, below
  the reader's curve), and the true equation appears as a formula (`du/dt = …`, stored truth form) directly under the
  reader's live equation, labelled "Wahre Gleichung" / "True equation". The reader's cards and values are not changed.
  Off: both disappear. Reset also hides the solution.
- The truth curve comes from existing exported data (the running cell's clean/truth curve); if it is only available
  on a different time grid, draw it on its own grid. No hand-typed coefficients.
- Flush columns (±2 px, measured by the fit checker) must still hold with the solution shown.
- The reader's equation no longer needs to be carried to page 3; remove that hand-over and its tests.

### 2. Page 3 (`p-solution`): delete everything, rebuild as "WISP at work"

Remove the current content (equation boxes, term-comparison table, legend box, reader curve, R² key, keys
`x4_solution`, `x4_idea`, `x6_yours` and all WP-X7b/X7c/X7e page-3 keys). Keep the section id `p-solution`.

**Data: the recorded WISP run of the running cell** (`live.featured[0]`, cell `sys0003_ic1_s0.03_r0_n1`, the same
measurements as page 2): `path` (8 steps with `origin`, `active_idxs`, `term_names`, weak coefficients), `candidates`
(fitted trajectory candidates with `curves`, `bic`, `params`) and `chosen` (`path_004`). Use these fields only; nothing
is recomputed except presentation (e.g. support diffs between consecutive steps). Recorded run, as found by Claude:

| step | origin | support |
|---|---|---|
| 1 | addition | 1 |
| 2 | addition | 1, u³ |
| 3 | removal | u, u³ |
| 4 | removal | u, u² |
| 5 | addition | u, u², sin u |
| 6 | addition | u, u², u³, sin u |
| 7 | addition | 1, u, u², u³, sin u |
| 8 | addition | 1, u, u², u³, sin u, cos u |

BIC chooses `path_004` = the true support. A "removal" step with unchanged size is a swap: derive from the support
diff which block left and which entered, and narrate both.

**Layout (one screen, 1366 × 657 and 768):**

- Headline DE "WISP bei der Arbeit" / EN "WISP at work". One deck sentence DE "Dieselben Messwerte, dieselben sechs
  Bausteine wie eben — so geht WISP vor." / EN "The same measurements, the same six building blocks as before — this is
  how WISP proceeds."
- **Left: the six building blocks** as cards in the page-2 look (same order and notation, same size), but without
  sliders — display only. Per step: a block that enters lights up (accent fill, short grow animation), a block that
  leaves is struck through and fades back to neutral, unchanged active blocks stay lit. Under the cards the current
  equation of this step as a formula with its weak coefficients (3 significant digits).
- **Right: the chart** — the measurements (dots) plus the current step's simulated candidate curve (thick accent line)
  from `candidates[...].curves` (reconstruction curve of that candidate). Previous step's curve may fade out briefly.
- **Below: the narration line and the step track.** A row of 8 small step dots (current one highlighted; dots of
  addition vs removal/swap steps distinguishable by shape, not only colour) and one plain-language sentence per step:
  - addition: DE "Schritt {k}: WISP nimmt {block} dazu — den Baustein, der vom noch Unerklärten am meisten erklärt." /
    EN "Step {k}: WISP adds {block} — the block that explains most of what is still unexplained."
  - swap: DE "Schritt {k}: WISP tauscht {out} gegen {in} — so passt es besser, mit genauso vielen Bausteinen." / EN
    "Step {k}: WISP swaps {out} for {in} — a better fit with the same number of blocks."
  - pure removal (if a path ever has one): DE "Schritt {k}: WISP wirft {block} wieder raus — ohne ihn wird es kaum
    schlechter." / EN "Step {k}: WISP throws {block} out again — without it the fit barely gets worse."
  - after the last path step, one **choice step**: all candidates' curves briefly shown thin, then the chosen one
    highlighted; DE "Zum Schluss: Jede Stufe wurde simuliert und mit den Messwerten verglichen. WISP wählt die, die mit
    möglichst wenigen Bausteinen am besten passt — Schritt {k*}: {equation}." / EN "Finally: every stage was simulated
    and compared with the measurements. WISP picks the one that fits best with as few blocks as possible — step
    {k*}: {equation}." The chosen step's cards light up again; under the equation one small line DE "Die wahre
    Gleichung: {truth}" / EN "The true equation: {truth}" (stored truth form).
- **Controls**: small round icon buttons play/pause, next step, restart (inline SVG, tooltips, `aria-label`s DE/EN).
  Autoplay starts when the page becomes visible, ~2.5 s per step, ~6 s on the choice step, then loops from step 1.
  Pauses when the page is not visible; any manual step pauses autoplay. With `prefers-reduced-motion: reduce`: no
  autoplay, the final choice step is shown, controls work.
- No jargon on this page (no "FROLS", "FoBa", "BIC", "weak form" — those come on the later pages). A small
  `data-claim="review"` caption may say DE "Aufgezeichneter WISP-Lauf auf genau diesen Messwerten." / EN "Recorded WISP
  run on exactly these measurements."
- Phone width: cards, chart, narration stacked; no horizontal page scroll.

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; tests adapted (remove page-3 comparison/table/reader tests,
   remove the page-2 → page-3 hand-over tests) and passing, plus new tests: page 2 eye button toggles truth curve and
   formula, reset hides it, cards unchanged; page 3 has 8 path steps + 1 choice step in recorded order, the narration of
   each step matches the support diff (steps 3 and 4 are swaps: 1→u, u³→u²), the choice step highlights `path_004`,
   candidate curves are the exported ones, autoplay loops and pauses off-page, reduced motion shows the choice step,
   no jargon words on page 3 (both languages).
2. Strict numerical checks exit 0.
3. `check_wisp_explainer_fit.py`: if blocked in your sandbox, status `blocked` with "browser not runnable here —
   environment, not the task"; Claude runs it.
4. Report `codex/reports/REPORT_WP_X8.md`: what changed, which fields feed each step, the timing, the test count.
