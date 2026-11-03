# WP-X12d — WISP explorable: fixes from Claude's frame review of WP-X12c
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-04 00:25. Follows WP-X12c (`codex/reports/REPORT_WP_X12C.md`, uncommitted, accepted as base). All rules
stay in force. Scope: chapter-1 stage only. Claude captured frames at 1366 × 768 (Edge headless) and found:

1. **S4 neighbour triangles are tiny.** In the 8-pair phase the zoom shows ~15 points, so a neighbour triangle is a few
   pixels. Zoom deeper for this phase: about 6–8 points across the plot width (so one Δt is ≥ 60 px), dots ≥ 7 px
   radius, triangle 3 px stroke with Δt/Δu labels on its legs; move the window along with the 8 pairs (pan) if needed.
   Keep the later zoom-out and sweep.
2. **Scene transition S3 → S4 overlaps two layouts** (at ≈ 300 ms the old single panel and the new two panels are drawn
   on top of each other: lower-panel tick labels "58,7 / 0" sit inside the upper panel, the masthead area flickers).
   Sequence it: first the single panel shrinks to the upper panel's frame, then the lower panel fades/grows in below;
   the lower panel's axes appear only after it has its final position.
3. **S10 end state is empty**: after the sum animation the data and the noise band disappear and only the list, the
   counter and the bar remain. The end state must keep the full-view data with the estimated noise band, with the sum
   bar below the plot (and the deviation list beside it).
4. **S11 labels overlap the share list**: the stacked-bar legend lines ("Rauschen — nicht erklärbar: …", "vom Baustein
   erklärt: …", "noch erklärbar: …") are drawn over the six share rows. Lay out S11 as: stacked bar on top across the
   stage width with its three labels directly under their segments (or one legend line), then the six share rows
   below with enough spacing; nothing overlaps.
5. **S7 error-over-c curve is too small** and has no axes: make it a real small chart (≈ 280 × 140 px) with an x-axis
   "c" (0 … 2·c*) and a y-axis "Fehler in %", the moving orange marker and the green optimum marker on it; place it
   where it does not cover the residual plot (e.g. right of the error bar or above the plot with its own space).

Add a DOM/layout check (bounding boxes) for S10 end (data dots present, ≥ 500 visible) and S11 (no text box overlaps
a share row), and for S4 (neighbour Δt ≥ 60 px in the 8-pair phase).

Acceptance: build exit 0, byte-identical rebuild; all tests passing; strict checks exit 0; fit checker as usual
(blocked → Claude runs it). Short report `codex/reports/REPORT_WP_X12D.md`.
