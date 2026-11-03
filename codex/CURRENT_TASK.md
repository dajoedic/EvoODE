# WP-X12b — WISP explorable: scroll story readability fixes from Claude's frame-by-frame review
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03 23:15. Follows WP-X12 (`codex/reports/REPORT_WP_X12.md`, uncommitted, accepted as base). All rules
from WP-X12 stay in force (vertical scroll only, one persistent stage, autoplay sequences, injectable clock, reduced
motion, no `compute.js`/data change, fit at 1366 × 657 / 768, byte-identical rebuild). Scope: chapter-1 stage only.

Claude captured every step at several times (Edge headless, 1366 × 768). The story works; these defects make it hard
to read. Fix all of them:

1. **S2 noise sticks are invisible** (thin, same tone as the curve). Draw them in the model/accent-contrast colour
   (`--model`), ≈ 1.5 px, 70 % opacity; the clean curve 2.5 px in `--truth`. The curve label must not overlap the top
   tick label.
2. **S3 tangent is invisible.** Draw the tangent as a long (≈ 25 % of the plot width) 2.5 px line in `--model` through
   the travelling marker, plus a small slope triangle (Δt, Δu) on it; readout "Steigung du/dt = {value}" next to the
   marker (follows it), not under the plot.
3. **S4 does not show what a slope from two points is.** Restructure into two phases:
   (a) **zoomed first**: start zoomed on a short stretch (~12 neighbouring points, large dots); for 3 consecutive
   neighbour pairs draw the triangle (Δt, Δu) large and labelled, and drop the resulting slope dot into the bottom
   panel with a short connecting animation; (b) then zoom out and run the fast sweep over all pairs (triangles only
   every k-th pair). The bottom panel needs its own **y-axis with ticks and a label "Steigung (Änderung pro
   Zeiteinheit)"**, a zero line, and a **robust fixed scale**: ± 4 × max |true slope|; slopes outside are drawn at the
   edge as small triangles (▲/▼) and counted in a caption "{n} Werte außerhalb". The true slope from the clean curve is
   a 2.5 px `--truth` line, visible as the hump (max ≈ 14.6). Dots must never fly in from outside the panel: they
   appear at their final position (fade/scale in) or travel from the triangle on the top panel straight down.
   The Δt/Δu readout belongs next to the current triangle, not below the stage.
4. **S5**: use the same bottom-panel scale as S4 (so the reader sees the long-window slopes land on the hump);
   triangles for lengths 2–16 drawn clearly (2 px, labelled with the length); after zooming out the 31 long-window
   slope dots appear on the same axis.
5. **S6–S8: the error bar overlaps the x-axis label "Zeit t".** Place the error bar (and its "Fehler: …" label) clearly
   below the plot with its own spacing, or to the right of the plot; no overlap at 768 and 657.
6. **S9 is cluttered.** (a) The local cubic must be clearly visible: 3 px `--model` line across the whole 9-point
   window, drawn before the ring/stick appear; the deviation stick 3 px. (b) The list "Abweichungen" goes into its own
   box outside the plot area (right of the plot or below it), one line per example point with its value, never over
   data. (c) The final overview: draw the estimated noise as a smooth translucent band (filled area between
   u_smooth ± sqrt(variance), where u_smooth is the local-cubic prediction at each point) instead of two jagged lines;
   legend "geschätztes Rauschen (± eine Standardabweichung)". (d) Split the long text: the step text keeps the method
   (first paragraph); the result (est vs true, floor, actual) appears as a second paragraph only after the sequence
   has finished (fade in), in the same step.
7. **The caption "Gezeigt: Abschnitte, die sich nicht überlappen …"** may appear only on steps that show windowed
   changes (S5–S8), not on S9–S11.
8. **Top-panel tick labels** ("6,61" at the bottom left) overlap the x-axis zero label: start the y ticks one tick
   above the axis or offset the first tick label.

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all tests passing plus: S4 phase (a) shows 3 labelled triangles
   in a zoomed view before the sweep; bottom-panel scale = ± 4 × max |true slope| with clipped-count caption; S9 list
   element outside the plot's bounding box; S9 result paragraph hidden until the sequence ends; caption only on S5–S8;
   DOM check that no two text labels' bounding boxes overlap on S2–S9 final states (Claude checks pixels).
2. Strict numerical checks exit 0.
3. `check_wisp_explainer_fit.py`: if blocked in your sandbox, status `blocked` with "browser not runnable here —
   environment, not the task"; Claude runs it.
4. Short report `codex/reports/REPORT_WP_X12B.md`.
