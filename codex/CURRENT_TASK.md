# WP-X9b — WISP explorable: page 3 display fixes after Claude's browser check of WP-X9a
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X9a (`codex/reports/REPORT_WP_X9A.md`, uncommitted, accepted as base). All rules stay in
force; no change to `compute.js` or data; scope page 3 only.

1. **The chart is an unreadable cloud** (496 overlapping windows). For the **display** use only non-overlapping
   windows of the longest length (consecutive, starting at the first sample; ≈ 31 points), drawn as clearly visible
   dots (radius ≈ 4 px), so the hump of fastest growth is visible. The computation (gains, coefficients, bars) is
   unchanged and still uses the full design. Add to the chart caption DE "Gezeigt: Zeitabschnitte, die sich nicht
   überlappen. WISP rechnet mit allen Abschnitten, auch überlappenden und kürzeren." / EN "Shown: windows that do
   not overlap. WISP computes with all windows, including overlapping and shorter ones." The prediction line is
   drawn over the same displayed windows.
2. The eyebrow "So geht WISP vor · 1" / "How WISP proceeds · 1" is not visible in the snapped layout — make it visible
   above the headline (same style as other eyebrows).
3. y-axis label: horizontal text DE "Änderung von u" / EN "change of u" above the axis instead of the rotated "Δu".
4. x-axis ticks: round values (0, 2,5, 5, 7,5, 10) instead of window-centre values (0,157 … 9,84).

Acceptance: build exit 0, byte-identical rebuild; tests passing plus: displayed windows are non-overlapping and of the
longest length, bars/gains unchanged against WP-X9a; strict numerical checks exit 0; fit checker as usual (blocked →
Claude runs it). Short report `codex/reports/REPORT_WP_X9B.md`.
