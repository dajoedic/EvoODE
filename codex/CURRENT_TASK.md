# WP-X16b — WISP explorable: chapter 3 review fixes
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-05. Follows WP-X16 (uncommitted in the working tree, report `codex/reports/REPORT_WP_X16.md`). All
explorable rules and the test policy of WP-X16 stay in force (fast presentation tests excluding
`test_wisp_explainer_x2.py`, `check_wisp_explainer_js.py`, byte-identical rebuild; no full `-k wisp` suite, no
exports). Claude ran the browser fit checker on WP-X16 and reviewed the screenshots under
`outputs/wisp_explainer_checks/pages/*_p-c3-*.png`. Fix the following.

1. **Label overlap (fit checker failure).** In `c3-linear` and `c3-quadratic` at sample 15300 ms the chip/bar labels
   `u` / `u³` (linear) and `u²` / `u³` (quadratic) overlap while the remaining chips compact after the removal. Make
   the compaction overlap-free at every sampled time (e.g. fade the leaving label out completely before the others
   move, or move them along non-overlapping paths). The fit checker must pass with zero label overlaps.

2. **Candidate boxes must not read as products.** In `c3-compare` and `c3-next` a model is written `1 · u³`,
   `1 · u · u²· u³`. A middle dot between blocks reads as multiplication. Show each model as a row of separate small
   block chips (same chip style as the top of the stage), or at least comma-separated. Never `·` between blocks.

3. **The decisive comparison must be readable.** In round 3 the constant's cost (≈1.2 %) is compared with the line
   at ≈3.2 % on an axis up to ≈82 %; in round 4 `u³`'s cost (≈0.03 %) against ≈0.83 % on an axis up to ≈77 %. On
   screen the line sits on the zero line and the comparison that decides the step is invisible. Fix generally, not
   per round: whenever the threshold is below ~10 % of the axis height, show a **magnifier inset** beside/above the
   bar chart with the y-range [0, ~2.5 × threshold], containing the same bars (clipped, with a cut mark), the
   dashed threshold line and the value of the bar closest to it; label it „vergrößert“ / „magnified“ with its own
   y-axis. The inset appears when the probe starts and stays through the removal decision. Also: the first probe of
   a round (with three blocks) and the repeated probe after removal must both be visible in the sequence long enough
   to read; the end state may show the repeated probe, but the removal moment (bar below the line turns „fliegt
   raus“, chip leaves) gets its own hold of ≥ 2 s before the repeated probe starts. If the two probes need different
   axis ranges, animate the axis rescale with its tick labels, do not jump.

4. **„Rest live neu anpassen“ panel has no axis titles.** Every chart has visible x and y titles (standing rule).
   Give this panel the same axis titles and meaning as the corresponding live-fit panel in chapter 2 (look up what
   the dots and the curve are there and use identical wording); if chapter 2's panel also lacks them, add them in
   both chapters.

5. **Step 7 redesign of the right panel.** Today: a 0–100 % axis, an invisible bar for `sin u` and a dashed line
   that looks like a threshold although there is none in this step. Replace with a small bar chart **„Gewinn je
   Runde“ / „gain per round“**: bars for rounds 1–4 (gain of the block added in that round, labelled with the block
   and value) plus a fifth, outlined/hatched bar for the next best block `sin u` labelled „noch nicht genommen“ /
   „not taken yet“. Y-axis from 0 to the largest gain, on chapter 2's explained-share scale, all values live. No
   dashed line. The shrinking bars set up the stop question of the next chapter; the text stays open (no stop rule,
   no BIC).

6. **Wording.** `c3-compare`: „Jetzt zeigen wir erstmals in der Geschichte die wahre Gleichung …“ → „Hier zeigen wir
   zum ersten Mal die wahre Gleichung des Lehrsystems …“ (English accordingly: „For the first time we show the true
   equation of the teaching system …“). Keep the rest.

7. Update tests and the fit checker sample tables for the new inset, the hold, and the step-7 chart (inset present
   exactly when threshold < 10 % of the axis, bar values equal the live computation, no `·` between blocks in model
   rows, step-7 bars equal the live gains of rounds 1–4 and the next best gain).

## Deliverables

Source changes, rebuilt `explainer/wisp/dist/wisp_explainer.html`, tests; `codex/reports/REPORT_WP_X16B.md` (what
changed, test results, rebuild hash); `codex/STATUS.md` entry. Do not commit. No exports, no Julia, no cluster jobs.
