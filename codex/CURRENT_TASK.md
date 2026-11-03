# WP-X10 — WISP explorable: chapters (horizontal) × sub-steps (vertical); chapter 1 "one block alone" in 7 small steps
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X9b (commit `010a550`, preview version 12). WP-X9c was aborted and fully reverted. All
rules from WP-X1..X9b stay in force (whitelist, blind rule, no Q7/Q8 results, no hand-typed result numbers, i18n
parity, byte-identical rebuild, swap test, size ≤ 14 MB, fallbacks, `data-claim="review"` on prose, no next-page-only
links, fit at 1366 × 657 / 768, page-2 flush columns, endless dish loop, recorded-path assertion). **No change to
`compute.js` or any data file.**

## User decisions (2026-11-03, evening)

1. "Deactivate everything after the page 'Ein Baustein allein'."
2. "In the end there will be the big steps horizontally and the small steps vertically. Data → numerical differences →
   error without a block → error with a block → show each → % how good → first solution, and on it goes. The fit
   belongs in there, too."
3. "What do the % mean? Is it an R²? That must be visible on the page."

## Scope

### 1. Navigation: chapters × sub-steps

- **Chapters** are arranged horizontally, **sub-steps** of a chapter vertically. Chapter "Einführung" / "Introduction"
  = the two existing pages (`p-hook`, `p-challenge`); chapter 1 "Ein Baustein allein" / "One block on its own" = the
  seven sub-steps below. More chapters will follow in later packages; build the structure so a chapter is added by
  adding sections with a chapter attribute, no navigation code change.
- **Scrolling / wheel / PageDown** moves to the next sub-step; after the last sub-step of a chapter it continues with
  the first sub-step of the next chapter (reading linearly still works). The transition between chapters slides
  horizontally, within a chapter vertically. Keep the existing one-gesture-one-page wheel routing and its tests.
- **`←` / `→`** jump to the previous / next chapter (first sub-step); **`↑` / `↓`** previous / next sub-step. Do not
  break inputs that use arrow keys (sliders, number fields keep their keys when focused).
- **Chapter bar** at the top (replacing the current top pipeline bar if present): chapter names, current one
  highlighted, clickable. **Sub-step dots** on the right show only the current chapter's sub-steps.
- **Hidden:** every page after the old `p-solution` (headline, equation, catalogue, noise, overview, all step intros,
  recap, results, glossary) is **hidden, not deleted** — not reachable by scrolling, keys, dots, chapter bar or links;
  the masthead link "Ergebnisse erkunden" / "Explore results" is hidden too. One configuration list in the source
  decides which sections are visible, so they can be switched back on later. Tests that exercise hidden pages run
  against them with the configuration switched on (they must keep passing), plus one test that they are unreachable
  in the delivered build.

### 2. Chapter 1 — seven sub-steps (replace the current `p-solution` content; reuse its computations)

Common to all seven: eyebrow DE "Kapitel 1 · Ein Baustein allein · {i} von 7" / EN "Chapter 1 · One block on its own
· {i} of 7"; headline; at most two short paragraphs; **one** visual; at most **one** interaction; a "Im Fachjargon:" /
"In technical terms:" line at the bottom only where a term is named (the only place a technical term may appear).
Running example = the teaching cell. Displayed windows = non-overlapping windows of the longest design length (as
WP-X9b), while every number (errors, %, coefficients) uses the **full** design exactly as WISP does — say so once in a
caption on 1b. Coefficients 3 significant digits, plain decimals, locale separator, constant without trailing "1".

**1a — `p-c1-data` "Das haben wir: Messwerte" / "What we have: measurements".** Chart: the measured u over time
(dots). Text DE "Gemessen wurde u zu {n} Zeitpunkten zwischen t = {t0} und t = {t1} — mit {noise} Rauschen. Mehr hat
WISP nicht." / EN equivalent (all values from the data).

**1b — `p-c1-changes` "Was wir beschreiben wollen: die Änderung" / "What we want to describe: the change".** Text DE
"Eine Differentialgleichung sagt, wie sich u ändert. Also holen wir genau das aus den Messwerten: um wie viel sich u
in einem Zeitabschnitt verändert. Aus zwei benachbarten Punkten bleibt dabei fast nur Rauschen übrig — über längere
Abschnitte kommt der Verlauf zum Vorschein." Visual: the measured change per window (u(b) − u(a), dots) over time, and
the same from the clean reference curve as a thin line "ohne Rauschen" / "without noise". **Interaction: slider
"Länge des Zeitabschnitts"** over the lengths in `live.windows` (show sample intervals and time units); fixed y-scale
normalised per unit time (show the rate (u(b) − u(a)) / (t_b − t_a) so lengths are comparable). Caption: "Gezeigt:
Abschnitte, die sich nicht überlappen. WISP rechnet mit allen Abschnitten aller Längen." Fachjargon: "Weak Form
(schwache Form); numerische Differenzen über Zeitfenster".

**1c — `p-c1-error-empty` "Fehler ohne Baustein" / "Error without a block".** Text DE "Eine leere Gleichung sagt:
u ändert sich nie. Jede gemessene Änderung ist dann ein Fehler. Wir quadrieren jede Abweichung und zählen alles
zusammen — das ist der Fehler ohne Baustein. Wir setzen ihn auf 100 %." Visual: displayed windows' measured change
(dots), the zero line, and a vertical residual stick from each dot to the line; beside it a single bar "Fehler: 100 %".

**1d — `p-c1-fit` "Ein Baustein und seine Zahl" / "One block and its number".** Text DE "Nehmen wir den Baustein 1:
du/dt = c. Dann sagt die Gleichung für jeden Abschnitt eine Änderung von c × Länge voraus. Welches c ist am besten?
Das, bei dem der Fehler am kleinsten wird." **Interaction: slider for c** (range around the fitted value, e.g. 0 to
2 × fitted). Visual left: the displayed windows with the prediction line and residual sticks for the current c; right:
a small curve **Fehler über c** (the full-design error as a function of c, as % of the 1c error — a parabola), a
moving marker at the current c, and the minimum marked DE "kleinster Fehler bei c = {c*}" (c* from the least-squares
fit, equals WP-X9a's 6,85). Text below DE "Diese Zahl muss man nicht suchen: Weil die Vorhersage einfach c mal etwas
ist, lässt sich das beste c direkt ausrechnen." Fachjargon: "Methode der kleinsten Quadrate (Least Squares)".

**1e — `p-c1-every` "Jeden Baustein ausprobieren" / "Try every block".** Text DE "Dasselbe macht WISP für jeden der
sechs Bausteine — jeder bekommt seine beste Zahl. Dann vergleicht es: Bei welchem bleibt der kleinste Fehler übrig?"
Visual: the WP-X9a/b page (bars + chart + equation, clickable), but the bars now show the **remaining error in % of
the 1c error** (lower is better, sorted ascending), winner accented.

**1f — `p-c1-percent` "Was die Prozent bedeuten" / "What the percentages mean".** Text DE "Ein Teil jeder gemessenen
Änderung ist Messrauschen. Das kann kein Baustein erklären — egal welcher. WISP schätzt aus den Daten, wie groß dieser
Teil ist: {floor} % des Fehlers. Erklärbar sind also nur {explainable} %." Visual: one horizontal **stacked bar** of
the 1c error (100 %): a grey part "Rauschen — nicht erklärbar" ({floor} %), and the explainable part, of which the
selected block's reduction is filled in accent; a block selector (six chips). Under it, the WP-X9a bars as **share of
the explainable part** (1: 52,9 %, …) with the sentence DE "Diese Zahl ist ein R² — allerdings auf den Änderungen in
den Abschnitten, und gerechnet nur auf dem erklärbaren Teil: 100 % hieße, alles erklärt, was überhaupt erklärbar ist."
Fachjargon: "Fehlerreduktion (error reduction ratio); Rauschschätzung".

**1g — `p-c1-solution` "Die erste Lösung" / "The first solution".** Text DE "Am meisten erklärt die 1 — eine
gleichbleibende Wachstumsrate. Als grobe erste Näherung ist das nicht schlecht. WISP nimmt sie als ersten Baustein:"
then the equation `du/dt = 6,85` large, and DE "Wie es weitergeht — welcher Baustein als nächster dazukommt — kommt
im nächsten Kapitel." / EN equivalent. Visual: the measured change (dots) with the constant prediction line (as 1e for
the winner). Winner and coefficient computed (recorded-path assertion). Fachjargon: "erster Schritt von FROLS (Forward
Regression Orthogonal Least Squares)".

Every number on 1c–1g comes from the computation; the 1e/1f/1g values must equal WP-X9a's (gains, floor 71,6 %,
explainable 28,4 %, 1 → 52,9 %, c = 6,85).

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all tests passing, plus: chapter/sub-step structure and keys
   (`←→` chapters, `↑↓`/wheel sub-steps, linear continuation, inputs keep their keys); hidden pages unreachable in the
   delivered build and their tests pass with the configuration switched on; the seven sub-steps exist in DE/EN in
   order; 1d error curve minimum at the least-squares c and equal to the 1e value for block 1; 1f stacked parts sum to
   100 % and match the floor; technical terms only in the Fachjargon lines.
2. Strict numerical checks exit 0.
3. `check_wisp_explainer_fit.py` (page list follows the visible configuration): if blocked in your sandbox, status
   `blocked` with "browser not runnable here — environment, not the task"; Claude runs it.
4. Report `codex/reports/REPORT_WP_X10.md`: navigation design, the visible-page configuration, per sub-step fields and
   numbers, test count.
