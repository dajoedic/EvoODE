# WP-X7d — WISP explorable: page 1 fix after WP-X7c
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-03. Follows WP-X7c (`codex/reports/REPORT_WP_X7C.md`, uncommitted, accepted by Claude for pages 2 and 3).
All rules from WP-X1..X7c stay in force. Scope: page 1 (`p-hook`) only; pages 2 and 3 must stay exactly as WP-X7c
left them.

## Claude's browser review of WP-X7c (1366 × 768)

1. Page 1 shows a visible dashed box "Platz für ein späteres Video" / its EN equivalent. That was a misreading of
   WP-X7c ("keep a slot free" meant: do not build the layout in a way that prevents adding media later — not a
   visible placeholder). **Remove the placeholder box, its text and its i18n keys entirely.** Nothing on the page may
   refer to a video.
2. The dish and curve shrank against WP-X7b (dish now ~175 px diameter, before ~250 px). Restore at least the
   WP-X7b size: dish ≥ 250 px diameter at 1366 × 768, curve beside it using the freed width (dish + curve together
   about the full content width), caption directly below the picture. The "Zeit" axis label stays fully visible.
3. Keep the slightly looser vertical rhythm of WP-X7c. Page 1 must still fit 1366 × 657 and 1366 × 768 without
   internal scroll; at 657 the picture may scale down proportionally.

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all 44 tests pass (adapt the ones that reference the
   placeholder) plus one test: no element or i18n key on page 1 mentions a video/placeholder.
2. Strict numerical checks exit 0.
3. `check_wisp_explainer_fit.py`: if blocked in your sandbox, status `blocked` with "browser not runnable here —
   environment, not the task"; Claude runs it.
4. Short report `codex/reports/REPORT_WP_X7D.md`.
