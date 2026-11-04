# WP-X14 — WISP explorable: user review of chapters 1 and 2
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-04. Follows WP-X13 (`db98fda`, plus Claude's fixes in the same commit). All earlier explorable rules stay
in force (German + English via `src/i18n/*.json`, every prose node `data-claim="review"`, no scientific number as an
editorial literal, results contract untouched, byte-identical rebuild, fixed-topology interpolation on the persistent
stage, labels never overlap). The user reviewed version 17 and asked for the following. Step numbers refer to the
current page.

## Chapter 1 ("Ein Baustein allein")

1. **Swap steps 2 and 3.** New order: data → *slope* ("Was eine Differentialgleichung beschreibt: die Steigung") →
   *noise visible* ("In jedem Messwert steckt ein Fehler") → secants → … Adjust the texts where they refer to each
   other (the slope step must not presuppose the noise step; the noise step may now refer back to the slope). The
   stage transitions must stay smooth in both scroll directions.
2. **Step 4 (secants): explain the green line.** It is the true slope (derivative of the noise-free curve, unknown
   to WISP). Give it a visible label on the stage and one sentence in the text: this line is the true change per unit
   of time that WISP tries to recover — the thing the secants estimate. Use the same wording as the slope step
   (“Steigung = wie schnell sich u gerade ändert”).
3. **Step 5 (longer sections): play through several section lengths.** Instead of one length, cycle through the
   section lengths WISP actually uses (`LIVE.windows`, read live; if there are many, use a representative subset of
   3–4 lengths from short to long, chosen by a rule stated in a code comment, never hand-typed values). Per length:
   draw its secant slopes, hold, then keep them on the stage in a **distinct colour per length** (with a small colour
   legend "Länge k Messabstände") while the next length is drawn, so the reader sees the estimates get calmer as the
   sections get longer. The green true slope stays visible as the reference. End state: all shown lengths visible,
   colour-coded. Loop like the other sequences.
4. **Merge steps 9 and 10** into one step (title: “Woher wissen wir, wie viel Rauschen drin ist?” or similar, user
   wording welcome): first the *why* text/visual (“Selbst der beste Baustein lässt einen großen Fehler übrig … muss
   wissen, wie groß dieser Teil ist”), then **after a long enough pause to read it** (≥ 4 s), the *how* part (local
   cubic through 9 points, deviation of the middle point) starts on the same page. The text column shows both
   paragraphs; the second paragraph appears/emphasises when its animation starts.
5. **The box during the noise estimate: one point at a time, not a list.** In the deviations box, always show only the
   **current** deviation as a single dot/value; then animate that dot moving **down into the sum** (the sum bar/counter
   below grows), then the next deviation appears in the box, drops into the sum, and so on (start slowly for the
   first few, then speed up, as now). No growing list of rows. End state as required by WP-X12d (full-view data with
   the estimated noise band, the sum below).

Chapter 1 thus has 11 steps instead of 12; update eyebrows ("Schritt i von n"), dots, progress, ids/anchors, and the
fit-check sample tables accordingly.

## Chapter 2 ("Noch ein Baustein dazu")

6. **Merge steps 3 and 4.** One step: first explain joint refitting with the single example `u` (as now: both numbers
   move, the constant leaves its chapter-1 value), **pause long enough to understand it** (≥ 4 s hold on the finished
   example, text paragraph 1), then the remaining candidates follow automatically in the same step (text paragraph 2
   appears), each with its joint prediction curve and its bar, exactly like chapter 1's "every" step does it.
7. **Sorting.** While trying, bars stay in catalogue order (that is the order WISP tries them). After the last
   candidate, animate the bars re-sorting by explained share (largest on top) and highlight the winner — that ranking
   is what WISP decides on. Say so in one sentence. Apply the same final re-sort to chapter 1's "every" step for
   consistency.

Chapter 2 thus has 5 steps instead of 6; update everything as above. Keep the neutral-claims test of WP-X13 passing.

## Checks

Extend the in-page fit check to the new sequences (several sample times for step 5's length cycle, the merged noise
step before/after the pause and during the drop-into-sum animation, chapter 2's merged step before/after the pause and
after the re-sort): stage inside the viewport, no SVG text overlaps, no annotation over a data dot. Update the tests
for the new page counts and order.

Acceptance: build exit 0 and byte-identical rebuild; all `-k wisp` tests passing; `check_wisp_explainer_js.py` exit 0;
fit checker exit 0 (if the browser cannot start in your sandbox, report `blocked` for that part only — Claude runs it).
Short report `codex/reports/REPORT_WP_X14.md`. Do not commit.
