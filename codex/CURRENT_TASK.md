# WP-X17b — WISP explorable: chapter 4 review fixes
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-05. Follows WP-X17 (uncommitted in the working tree, report `codex/reports/REPORT_WP_X17.md`). All
explorable rules and the test policy of WP-X17 stay in force. Claude ran the browser fit checker (passes) and
reviewed end-state and mid-animation screenshots of chapter 4. Fix the following.

1. **Order violation in the replay (most important).** During round 2's test phase the test column already shows
   the chips `1, u³`, i.e. the model *after* the addition. The test is done on the model *before* the round. Use one
   model row for the whole round, placed above the three panels (not inside the test column), that shows the state
   the current phase works on: during Test the pre-round model (round 1: empty, show „leer“ / „empty“), during
   Hinzufügen the newcomer joins, during Aufräumen the removal happens. Add a test that, for every round, the model
   row at every sampled time inside the test phase equals the pre-round support.

2. **Number formatting.** Values and axis labels show JavaScript exponent notation (`9.3e+3`, `1.1e+4`). Never show
   exponent notation; use locale formatting (German `9 311`, `2 932`, `0,703`; English `9,311`). Apply to every
   chart on the page (grep the formatter, not only chapter 4).

3. **Ratio axis on a logarithmic scale.** Ratios span about 0.06 to 9,300 across rounds, so on a linear axis the
   threshold sits on the zero line and the main chart says nothing; the magnifier then carries everything. Use a
   log10 y-axis for every ratio chart in chapter 4 (step 3 and the replay's test panel), with decade ticks
   (0,01 … 10 000, as far as the data need, fixed across all rounds of the replay so rounds are comparable), the
   threshold as a dashed line at its true position, the axis titled „Gewinn / Rauscherwartung (log. Achse)“ /
   „gain / noise expectation (log axis)“, and one short clause in the step-3 text that the axis is logarithmic.
   Remove the ratio magnifier there (no longer needed). The clean-up panel keeps its linear cost axis and its
   magnifier.

4. **One threshold value, one format.** The chart says „Schwelle: 6,63“, the text „6,64“; the recorded value is
   6.635. Show it everywhere with the same formatter and enough digits to be exact (6,635 / 6.635), both from the
   same source field.

5. **Overlap.** In the replay the model chips overlap the „Schwelle: …“ label (y ≈ 280–300 at 1366×768). With item 1
   the chips move above the panels; make sure the layout leaves clear space at both viewport heights (768 and 657)
   and that the fit checker's overlap test covers chip boxes against chart labels.

6. **Clean-up panel visible in every passing round.** In rounds 1 and 2 the clean-up panel shows only „wartet“ and an
   empty frame for most of the round. After the addition, run the probe in every round (rounds 1 and 2 included:
   costs vs half-gain line, all stay), so the viewer sees that clean-up happens every round, not only when something
   leaves. Round 5 keeps the greyed „Ende“ panels.

7. Update tests and fit checker samples accordingly (log ticks and threshold position, no exponent strings anywhere in
   rendered text, model row = pre-round support during test, probes present in rounds 1–4, one threshold string).

## Deliverables

Source changes, rebuilt `explainer/wisp/dist/wisp_explainer.html`, tests; `codex/reports/REPORT_WP_X17B.md` (what
changed, test results, rebuild hash); `codex/STATUS.md` entry. Do not commit. No exports, no Julia, no cluster jobs.
