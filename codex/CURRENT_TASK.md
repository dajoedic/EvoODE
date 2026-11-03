# WP-X8d — WISP explorable: page 3 fixes from Claude's frame-by-frame review of WP-X8c
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X8c (`codex/reports/REPORT_WP_X8C.md`, uncommitted, accepted as base). All rules from
WP-X1..X8c stay in force (incl. the recorded-path assertion, no jargon on page 3, no change to `compute.js` or data,
fit at 1366 × 657 / 768). Scope: page 3 only.

Claude stepped through every frame (Edge headless, `#work-next`). Defects, all to fix:

1. **Equation rendering.**
   - The constant block is rendered as a trailing digit: stage 2 `params [10.0, -1.32e-5]` shows `du/dt = 101 − …`.
     The constant term must render as its coefficient alone (`10`).
   - Long equations are clipped at the column edge (step 3 ④ "… − 7.8", step 4 ③ "… + 1.:"). The equation must always
     be fully visible: wrap to a second line or scale down to fit its column (min. ~70 % of the normal size); test
     with the longest equation on the path (6 blocks).
   - Coefficient format: 3 significant digits in plain decimal notation with the locale separator (e.g. −0,0000275),
     no `× 10⁻ⁿ`. Signs as proper minus.
   - The true equation in ⑥ is rendered at the same size as the chosen equation (today a tiny inline fraction).
2. **The noise floor is missing, and without it the page misleads.** At the true support (step 4) "still unexplained"
   is still ~77 %, because the short-window changes are dominated by measurement noise. Add, in ① and ③, a marker on
   the "still unexplained" bar at the share no equation can explain: compute it with `compute.js`'s existing noise
   functions (`noiseVariance` on the teaching observations and `noiseFloor(D, support, variance)` for the current
   support, divided by `‖b‖²`; reuse, do not modify). Label DE "Rauschen — diesen Teil kann keine Gleichung erklären" /
   EN "Noise — no equation can explain this part". If, at a step, `remaining` is within 10 % (relative) of the floor,
   append to the ① narration DE "Was jetzt noch übrig ist, ist fast nur Rauschen." / EN "What is left now is almost
   only noise." Report the floor and `remaining` per step; if the floor at step 4 is not within 10 % of `remaining`,
   do **not** show that sentence anywhere and say so in the report (do not tune anything to make it fit).
   Gains in ② are additionally shown relative to the explainable part (`gain / (remaining − floor)`, in %) in the
   bar label, e.g. "1,8 % (davon erklärbar: 8 %)" / "1.8 % (of the explainable: 8 %)" — only if the floor is
   available; otherwise keep the plain share.
3. **Window plot shows mostly noise.** Use the **longest** window length of the design instead of the shortest, so
   the signal is visible; caption unchanged in meaning ("… in Zeitabschnitten …"; drop "kurzen" / "short").
4. **Step-strip bars are not proportional** (0.727 and 0.994 look almost equal). Bar height ∝ R² on a fixed 0–1 scale
   (≈ 110 px for 1.0 at 768 height, scaled at 657), with a thin baseline; negative values at 0 with the number still
   shown. Same in ⑤ and ⑥.
5. **Wording / layout details:**
   - "1 Bausteine" / "1 blocks" → singular "1 Baustein" / "1 block".
   - All six chips equal width with inner padding ("sin u", "cos u" currently touch the border).
   - The ⑥ legend says "gewählt: Stufe {k*}" / "chosen: stage {k*}" (per WP-X8c spec), not "Kurve von Stufe {k*}".
6. Run the same frame walk in DE and EN in the DOM harness and assert: no equation element wider than its container,
   constant terms rendered without a trailing "1", no "×10" in page-3 equations, singular/plural correct, bar heights
   proportional to R².

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all tests passing plus the checks of item 6 and a test that the
   noise-floor marker equals the `compute.js` noise functions' value.
2. Strict numerical checks exit 0.
3. `check_wisp_explainer_fit.py`: if blocked in your sandbox, status `blocked` with "browser not runnable here —
   environment, not the task"; Claude runs it.
4. Report `codex/reports/REPORT_WP_X8D.md`: fixes, per step `remaining` and floor (both in %), whether the "almost only
   noise" sentence is shown, test count.
