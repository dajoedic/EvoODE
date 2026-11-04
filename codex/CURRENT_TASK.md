# WP-X15 — WISP explorable: second user review (looping, live fits, clearer lengths and noise sum)
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-04 evening. Follows WP-X14 (`11949a1`). All earlier explorable rules stay in force (German + English,
`data-claim="review"`, no scientific number as an editorial literal, results contract untouched, byte-identical
rebuild, fixed-topology interpolation, no overlapping labels). The user reviewed version 18.

**Test policy (new, binding):** while working run only the fast presentation tests
`python -m pytest analysis/tests/test_wisp_explainer_x*.py -q -p no:cacheprovider` **excluding**
`test_wisp_explainer_x2.py` (~2 min), plus `check_wisp_explainer_js.py`, plus the fit checker. Do **not** run the full
`-k wisp` suite (it re-runs export and re-integration, ~30 min) — data and exporters do not change in this WP.
Update the fit checker's hard-coded page inventory / dot counts / sample tables yourself when page counts change.

## Global

1. **Every animation loops forever.** At the end of a step's sequence: hold the end state ~3 s, then restart from the
   beginning; repeat while the step is shown. Applies to every animated step in chapters 1 and 2 (including the ones
   that loop today with other timing). Reduced motion: show the end state, no loop. The fit checker samples must
   still be able to seek deterministic times (seek within one cycle).
2. **Remove the hands-on slider** in chapter 1's fit step ("Selbst probieren", `#c1-play` / `#c1-c`) from the page
   for now (keep no dead code paths that the tests still reference; adjust tests).

## Chapter 1

3. **Step 5 "Längere Abschnitte" is cluttered — redesign.** Overlaid clouds of four lengths are unreadable. New design:
   - The slope panel shows **one length at a time** (replacing the previous one, not accumulating), with the green true
     slope as reference, same y-axis for all lengths so they are comparable.
   - Beside the panel, a small persistent **bar chart "typische Abweichung von der wahren Steigung"**, one bar per
     length (1, 2, 8, 16 — selected as now from `LIVE.windows`), in that length's colour. When a length has been
     drawn, its bar grows to the root-mean-square difference between its section slopes and the true slope over the
     same sections, and stays. Result: the bars shrink visibly from short to long sections. Mark it as an
     illustration that uses the true curve (one short line like the existing "(Berechnung für diese Darstellung)").
   - Text: shorter sections → slope estimates scatter widely; longer → close to the true slope; the bars show by how
     much. Remove the colour legend under the panel if the bar labels make it redundant.
4. **Step 8 "Jeden Baustein ausprobieren": live fit per block.** Show the current equation **on top of the stage**
   (large, like the solution equation), and fit each block one after another as a small animation in the style of the
   fit step: for block `1`: equation `du/dt = c · 1`, c sweeps to its optimum while the **number in the equation updates
   live** and the prediction/residuals update as now; when it settles, the block's bar gets its value; then `du/dt =
   c · u`, same animation; and so on through the catalogue. Coefficients come from the existing single-block fits (live
   computed, as now).
5. **Sort after every block** (good → bad): after each block's bar is set, the bars re-sort by explained share,
   animated, best on top. The winner is highlighted at the end. Same rule in chapter 2 (item 7).
6. **Merged noise step (step 9): show both text paragraphs at once** (no staged emphasis, no reading pause); the
   animation starts directly.
7. **The summation is still unclear — new attempt.** Make the two sums explicit and visibly arithmetic:
   - Phase A, per point: the box shows the current deviation d (one value, as now). It turns into its **square d²**
     (show "d²" with the value), drawn as a small block that **drops onto a stacked bar** labelled "Summe der
     quadrierten Abweichungen"; a running counter next to the bar shows the current sum and the number of points
     ("… aus k von n Punkten"). First few points slowly, then fast, as now.
   - Phase B: the sum is divided by the number of points → one number "typisches Rauschen ≈ …" (the existing estimate,
     `relative`, as a percentage of u), and the band appears around the data.
   - Phase C: connect to the error without a block: "Jeder Abschnitt hat zwei Endpunkte mit Rauschen → über alle
     Abschnitte zusammengezählt: {floor} des Fehlers ohne Baustein" — the existing floor bar fills to that value.
   Each phase's label appears when it starts; the final state shows all three results. Numbers are live from the
   existing functions; if the displayed arithmetic of phase A/B cannot reproduce `W.noiseVariance` exactly (it uses a
   local cubic per point and may weight differently), label phase A/B honestly as what it is (e.g. "Summe ... /
   Anzahl" only if that is what is computed) and say in the report what the frozen function computes; do not change the
   frozen function.

## Chapter 2

8. **Merged step 3 ("Zwei Bausteine gemeinsam"): show both text paragraphs at once** and start the animation directly
   (no reading pause, no staged emphasis); the example `u` is still shown first, then the remaining candidates.
9. **Sort after every candidate** (good → bad), animated, as in item 5; winner highlighted at the end.

## Acceptance

Build exit 0 and byte-identical rebuild; fast presentation tests passing (see policy); `check_wisp_explainer_js.py`
exit 0; fit checker exit 0 incl. samples for the new step-5 sequence (each length, final bars), step 8 mid-sweep and
mid-sort, step 9 in phases A/B/C, chapter 2 mid-sort, and one sample in the loop's restart. If the browser cannot start
in your sandbox, report `blocked` for that part only — Claude runs it. Short report `codex/reports/REPORT_WP_X15.md`.
Do not commit.
