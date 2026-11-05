# WP-X20b — WISP explorable: chapter 9 polish
**Language: Python** (build, tests) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-05 night. Follows WP-X20 (`995791d`, version 25). Claude ran the Julia Q7 display export (804 reused,
814 evaluated, 14 without model; 77 withheld for missing/nonfinite stored scores, as intended), the Python export, the
build, the full `-k wisp` suite and the browser fit checker (passes after Claude updated the checker inventory, the
last-chapter dot/masthead checks and two tests to the intended Q7 switch — see the commit). Comparison path fixed by
Claude: `analysis/data/sideproject_residual_growth/q7_grid/q7_q5w_comparison.csv`. All explorable rules and the test
policy stay in force (no data/exporter changes in this WP → fast presentation tests + JS check; full `-k wisp` once at
the end, ~5 min). Claude reviewed `outputs/wisp_explainer_checks/pages/*_p-c9-*.png` and `*_p-results.png`. Fix:

1. **Meaningless configuration labels under WISP values.** In `c9-clean` and `c9-noise` the WISP (Q7) column shows
   „c“ beneath every rate (the internal rule id). WISP has one configuration; show nothing there (or „WISP, Q7“ once in
   the row header). In `c9-original` the WISP row shows the comparison key („W1-interp:L-C6“) beneath its values —
   that key belongs to the WSINDy row only. Keep exact configuration names beneath the baseline rates (project rule).
2. **`c9-noise` is cut off at 1366×768**: the per-panel legends run below the viewport (E-SINDy label cut). Use one
   shared legend for the three panels (method colour → name, plus the exact configuration names per metric in a
   compact „Konfigurationen“ disclosure or a small table), so the page fits at 768 and 657 without inner scrolling of
   essential content. The fit checker must detect this kind of cut-off (content below the viewport bottom inside a
   page that is not meant to scroll) — extend it if it did not.
3. **Chapter design.** Chapter 9 pages lack the eyebrow „Schritt n von m“ and the text/stage rhythm of chapters 1–8.
   Keep the full-width tables and charts (they suit the data), but add the eyebrow, a short lead paragraph per page in
   the left-aligned text style, and consistent spacing with chapters 6–8. The explorer page („Selbst nachsehen“) keeps
   its own layout.
4. **„Ohne Rauschen“ wording.** The page explains that clean control cells (σ = 0, ρ = 0) are excluded, so it shows
   σ = 0 with ρ = 0,5 only. Say plainly: „σ = 0 mit Ausdünnung ρ = 0,5 (die vollständig sauberen Zellen sind
   Kontrollen und zählen nicht)“; if the ρ selector has only one value, show it as text instead of a dropdown.
5. Tests and fit checker samples updated; zero overlaps, no cut-off at both viewports and both languages.

## Deliverables

Source changes, rebuilt HTML, tests; `codex/reports/REPORT_WP_X20B.md`; `codex/STATUS.md`. Do not commit. No Julia,
no exports, no cluster jobs.
