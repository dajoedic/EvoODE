# WP-X7 — WISP explorable: a new page 1 ("what this is about"), and page 2 framed as "build it yourself"
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X6 (`codex/reports/REPORT_WP_X6.md`, commit `0eee9c8`). Every rule from WP-X1..X6 stays
in force (≈ 19 pages, one section per page, whitelist, blind rule, no Q7/Q8 results, no hand-typed result numbers,
both metrics, strata separate, i18n parity, byte-identical rebuild, swap test, size ≤ 14 MB, fallbacks, wheel
routing, `data-claim="review"` on prose). No change to numerical WISP code (`compute.js`) or to any data file.

**Scope is pages 1 and 2 only.** The user goes through the page one by one; do not touch page 3 (`p-solution`) or any
later page, apart from what Scope 3 names.

## User feedback (2026-11-03)

"That was too much at once. First page: what is this about? Differential equations in nature, a vivid example, maybe
a picture. History — how differential equations came out of data. Not too much, but something. Second page: the
problem. The way it is now is already cool. Build it yourself — see whether you can do it: structure, parameters."

## Scope

### 1. Page 1 replaced: "what this is about" (`p-hook`)

Remove the current content of `p-hook` (keys `x4_problem`, `x4_why`, the `problem-chart` data plot). Keep the section
id `p-hook` so links still work. New content, in this order, all fitting one screen at 1366 × 657:

**a) Headline and deck** (texts below, verbatim; small wording fixes allowed, report them).

**b) The vivid example as a picture: a petri dish beside its growth curve.** Inline SVG, no external image, no new
library. Left: a round dish in which dots (cells) appear — first doubling quickly, then slower, until the dish is full.
Right: a small chart of the cell count over time that grows in sync with the dish (S-shaped curve, drawn as it
grows). Illustration only, generated in the browser from a logistic curve with fixed illustrative constants — label it
as an illustration (caption below). **Do not show the formula** anywhere on this page — finding it is page 2's
challenge. Animation: starts when the page becomes visible, runs ~6 s once, a small "replay" button; with
`prefers-reduced-motion: reduce` show the final state without animation. Dots placed by a seeded deterministic
generator so rebuilds stay byte-identical.

**c) A compact history timeline** — five stations, one short line each, horizontal on wide screens, vertical list on
narrow ones (phone width, 16 px gutter, no horizontal scroll). Texts below. No portraits, no external images; a small
year label plus the line is enough.

**d) A one-line bridge** to page 2 (text below) with a link/button to `#p-challenge`.

Texts (DE / EN):

| Key (suggested) | DE | EN |
|---|---|---|
| eyebrow | Worum es geht | What this is about |
| headline | Die Natur beschreibt sich in Änderungsraten | Nature describes itself in rates of change |
| deck | Wie schnell wächst eine Bakterienkultur? Wie schnell kühlt ein Kaffee ab? Wie schnell breitet sich eine Grippe aus? Eine Differentialgleichung sagt nicht, wo etwas gerade ist, sondern wie schnell es sich gerade ändert. Aus dieser einen Regel folgt der ganze Verlauf: Sie erklärt, warum etwas passiert, sagt voraus, was als Nächstes kommt, und lässt sich an neuen Messungen prüfen. | How fast does a bacterial culture grow? How fast does a coffee cool? How fast does a flu spread? A differential equation does not say where something is, but how fast it is changing right now. That one rule produces the whole course: it explains why something happens, predicts what comes next, and can be tested against new measurements. |
| dish caption | Bakterien in einer Schale: Anfangs verdoppeln sie sich in festen Abständen, dann wird der Platz knapp und das Wachstum bremst, bis die Schale voll ist. Hinter diesem S-förmigen Verlauf steckt eine einfache Regel. Illustration, keine Messdaten. | Bacteria in a dish: at first they double at fixed intervals, then space runs short and growth slows until the dish is full. Behind this S-shaped course sits a simple rule. Illustration, not measured data. |
| replay | Nochmal abspielen | Play again |
| timeline title | Aus Messungen werden Gleichungen | From measurements to equations |
| 1609–1687 | Kepler liest aus Tycho Brahes Planetenbeobachtungen feste Muster ab; Newton fasst sie als Regel für die Änderung der Bewegung — Keplers Gesetze folgen daraus. | Kepler reads fixed patterns from Tycho Brahe's planetary observations; Newton turns them into a rule for how motion changes — Kepler's laws follow from it. |
| 1838 | Verhulst gewinnt aus Volkszählungen die Regel für gebremstes Wachstum — dieselbe wie in der Schale oben. | Verhulst derives the rule for slowing growth from census data — the same one as in the dish above. |
| 1925–26 | Lotka und Volterra erklären mit zwei gekoppelten Gleichungen, warum sich in den Fischmarktdaten der Adria Räuber und Beute im Wechsel häufen. | Lotka and Volterra explain with two coupled equations why predators and prey rise and fall in turn in the Adriatic fish-market records. |
| 1952 | Hodgkin und Huxley bauen aus Messungen an der Nervenfaser eines Tintenfischs die Gleichungen des Nervenimpulses (Nobelpreis 1963). | Hodgkin and Huxley build the equations of the nerve impulse from measurements on a squid's nerve fibre (Nobel Prize 1963). |
| heute / today | Messdaten gibt es in Massen, Zeit für Handarbeit nicht. Verfahren wie SINDy (2016) suchen die Gleichung automatisch — WISP ist eines davon. | Data come in floods, time for handwork does not. Methods such as SINDy (2016) search for the equation automatically — WISP is one of them. |
| bridge | Jahrhundertelang war das Handarbeit. Probier es selbst. | For centuries this was done by hand. Try it yourself. |

### 2. Page 2 re-framed: "build it yourself" (`p-challenge`)

The playground stays exactly as it is (term cards, coefficient controls, live equation, curve, meter, hints, reset,
reveal). Change only the framing:

- Headline (`x6_challenge`): DE "Jetzt du: Bau die Gleichung selbst." / EN "Your turn: build the equation yourself."
- New deck paragraph directly under the headline: DE "Das sind echte Messwerte eines solchen Wachstums, mit
  {noise} Rauschen. Eine Gleichung besteht aus zwei Teilen: der **Struktur** — welche Bausteine vorkommen — und den
  **Parametern** — wie stark jeder Baustein wirkt. Wähle beides und sieh zu, wie nah deine Kurve an die Messpunkte
  kommt." / EN "These are real measurements of such growth, with {noise} noise. An equation has two parts: the
  **structure** — which building blocks appear — and the **parameters** — how strongly each block acts. Choose both and
  watch how close your curve gets to the measured points." `{noise}` is rendered from `teaching.sigma` as a percentage
  (never typed).
- Two small labels in the playground so the two parts are visible: above the on/off checkboxes of the term cards
  "Struktur: Baustein an/aus" / "Structure: block on/off", and above the coefficient controls "Parameter: Gewicht" /
  "Parameter: weight". Placement as fits the existing card layout; keep it compact.
- Hint 1 currently says logistic growth needs two terms; keep the hint ladder unchanged.
- Punchline and reveal unchanged.

### 3. Consequences elsewhere (only these)

- Any test, checker or fit target that names `problem-chart`, `x4_problem` or `x4_why` is adapted. Remove keys that
  are no longer used from both i18n files (parity check must still pass).
- `explainer/wisp/README.md`: the sentence "The hook, noise and weak-form figures use the real System 3 cell" becomes
  correct for the new state (the hook no longer shows real data; the challenge does).
- Glossary credits: add nothing unless a source is needed for the timeline; the timeline lines are historical facts,
  no citations on the page.

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all existing tests (35) adapted and passing, plus new tests:
   page 1 exists in EN and DE with the five timeline stations, no formula/`data-tex` and no real-data chart on page 1;
   the dish animation is deterministic (two builds identical) and the reduced-motion path renders the final state;
   page 2 shows the deck with the noise percentage from `teaching.sigma` and both labels; page count unchanged.
2. Strict numerical checks (`check_wisp_explainer_js.py`, `check_wisp_explainer_x2.py`) exit 0.
3. `check_wisp_explainer_fit.py`: if the browser is blocked in your sandbox, status `blocked` with "browser not
   runnable here — environment, not the task"; Claude runs it.
4. Report `codex/reports/REPORT_WP_X7.md`: what changed, any wording changes against the table above, the illustrative
   constants of the dish, and the test count.
