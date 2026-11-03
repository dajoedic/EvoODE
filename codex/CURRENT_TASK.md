# WP-X7b — WISP explorable: pages 1–3 polish from the user's review of version 6
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X7 (`codex/reports/REPORT_WP_X7.md`, commit `f76a84c`, preview version 6). Every rule from
WP-X1..X7 stays in force (one section per page, whitelist, blind rule, no Q7/Q8 results, no hand-typed result
numbers, both metrics, strata separate, i18n parity, byte-identical rebuild, swap test, size ≤ 14 MB, fallbacks,
wheel routing, `data-claim="review"` on prose). No change to numerical WISP code (`compute.js`) or to any data file.
Scope: pages 1–3, plus the navigation-link rule in 4.

## User feedback (2026-11-03)

"Page 1: very squeezed — we have more room, use it. The simulation should loop forever. The link at the bottom is not
needed. Otherwise I like the opening. Page 2: also cramped, loosen it up. A link to the next page is always
unnecessary, that happens by scrolling. When you tick the checkbox, the card changes size — I don't like that, they
should always be the same size. 'Neu anfangen' and 'Nächster Hinweis' could be less prominent — a circular arrow and a
light bulb? Page 3: very cool. Only the chart is missing the reader's own equation, and it would be cool if the error
were shown."

Claude's own findings from the browser check of version 6 (same direction): on page 1 the dish and curve are small and
the caption floats far to the right; on page 2 the "Struktur: Baustein an/aus" label is repeated on all six cards; at
1366 × 657 page 2 overflows by ~32 px (`challenge-reveal`).

## Scope

### 1. Page 1 (`p-hook`)

- **Use the screen.** Dish and growth curve clearly larger (together roughly the width of the text column, the dish
  at least ~2× today's diameter at 1366 × 768), placed side by side; the caption directly beneath them (or beside,
  but adjacent — no wide empty gap). The timeline below keeps its five stations. The page must still fit 1366 × 657
  and 1366 × 768 without internal scroll, and stack cleanly at phone width.
- **Endless loop.** The dish animation and the curve run in a continuous loop: grow over ~6 s, hold the full state
  ~1.5 s, clear, start again. It runs only while the page is visible (pause when scrolled away or the tab is hidden).
  Remove the "play again" button. With `prefers-reduced-motion: reduce`: static final state, no loop. Deterministic
  as before (seeded positions, byte-identical rebuild).
- **Remove the bridge link** ("Jahrhundertelang war das Handarbeit. Probier es selbst." and its link) and its i18n
  keys.

### 2. Page 2 (`p-challenge`)

- **Loosen the layout**: more space between deck, cards and chart panel, and inside the cards; it must still fit
  1366 × 657 (today it overflows by ~32 px — removing the reveal link, see below, frees room).
- **Cards have a fixed size.** A card never changes its size when its checkbox is toggled. The coefficient controls
  are always present in the layout; for a switched-off term they are shown disabled/greyed (not hidden), and enabling
  the term activates them. All six cards are equally tall.
- **One label each, not six.** "Struktur: Baustein an/aus" / "Structure: block on/off" and "Parameter: Gewicht" /
  "Parameter: weight" appear once above the card grid (e.g. as a small legend explaining the checkbox and the
  slider), not repeated in every card.
- **Reset and hint as unobtrusive icon buttons**: a circular arrow (reset) and a light bulb (next hint), small, round,
  inline SVG icons, no text label but a tooltip and `aria-label` with the existing texts ("Neu anfangen" / "Nächster
  Hinweis", EN equivalents). Hints still appear in order under the cards; the bulb is disabled after the third.
- **Remove the reveal link** "Zeig mir, was WISP findet" (`challenge-reveal`, key `x6_reveal`). The punchline stays.
  The reader's equation must still reach page 3 (page state, as today).

### 3. Page 3 (`p-solution`)

- **The reader's own curve in the chart.** Simulate the reader's last equation from page 2 exactly as the playground
  does (same RK4, same start at the first measurement, same time grid, same clipping of divergent values) and draw it
  in the solution chart next to the WISP model curve, the truth and the measurements. Distinct colour and a legend
  entry "Deine Gleichung" / "Your equation"; WISP's curve stays the visually dominant one. If the reader never touched
  the playground, use the playground's initial state (as the equation box already does).
- **Show the error.** For each drawn curve (yours, WISP, truth) show its R² against the measured points in the legend
  or a small table beside the chart, computed in the browser with the **same definition as the playground meter**
  (R² of the curve against the observations on the observation times; interpolate a curve onto those times if its
  grid differs). Label: DE "Passung zu den Messwerten (R², im Browser berechnet)" / EN "Fit to the measurements (R²,
  computed in the browser)". These are presentation computations from exported curves and the reader's state; they
  do not replace and must not be confused with the stored reconstruction/generalization scores. If the WISP model
  curve and the observations do not share a time base that can be compared, report it rather than guess.
- The equation boxes (yours / WISP / truth) stay.

### 4. Navigation-link rule (all pages)

Navigation happens by scrolling. Remove every link or button whose only purpose is to go to the **immediately
following** page. Links that jump elsewhere (e.g. "Alle Ergebnisse erkunden" to the results explorer, the catalogue's
link back to the challenge, pipeline-map entries) stay. List every removed link in the report.

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all existing tests (37) adapted and passing, plus new tests:
   page 1 has no replay button and no bridge link, the loop restarts (DOM harness, fake timers) and pauses when the
   page is not visible, reduced-motion renders the static final state; page 2 card heights are identical with any
   checkbox state (DOM-level: same layout classes/markup, controls disabled not removed), icon buttons carry
   `aria-label`s in both languages, the reveal link is gone; page 3 draws the reader curve and shows three R² values
   computed by the playground's formula (test: for a fixed reader equation the page-3 value equals the page-2 meter
   value).
2. Strict numerical checks (`check_wisp_explainer_js.py`, `check_wisp_explainer_x2.py`) exit 0.
3. `check_wisp_explainer_fit.py`: if the browser is blocked in your sandbox, status `blocked` with "browser not
   runnable here — environment, not the task"; Claude runs it.
4. Report `codex/reports/REPORT_WP_X7B.md`: what changed, the removed navigation links, the loop timing, how the
   page-3 R² is computed (time base, interpolation), and the test count.
