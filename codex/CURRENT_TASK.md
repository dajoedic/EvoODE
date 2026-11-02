# WP-X5 — WISP explorable: fix navigation, make the opening and the results visual, clean labels
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-02. Follows WP-X4 (`codex/reports/REPORT_WP_X4.md`, uncommitted in the working tree — build on it).
Every rule from WP-X1..X4 stays in force (19-page structure, one section per page, whitelist, blind rule, no Q7/Q8
results, no hand-typed result numbers, both metrics, strata separate, exact/surrogate separate, i18n parity,
byte-identical rebuild, swap test, size ≤ 14 MB, fallbacks). No change to numerical code or data.

Claude ran the fit checker (Playwright + Edge, works on this machine) and reviewed screenshots of all pages at
1366 × 768 (DE). Findings, all to fix:

## Defects

1. **Wheel navigation is blocked over figures.** From page 1, three wheel gestures with the mouse in the middle of
   the screen (over a chart) reach only page 2 — the interaction guard treats "pointer over a figure/control" as
   "interacting". Rule: the wheel changes the page **everywhere** except (a) while a slider/drag is actively held,
   (b) inside an element that itself scrolls and still has room to scroll in that direction (More drawer, explorer
   panels, tables), (c) while a `<select>` is open. Hovering a chart or a control is not interacting. Add a Playwright
   test (`channel="msedge"`, 1366 × 768): from page 1, N wheel gestures with the pointer at the screen centre reach
   page 1 + N for N = 1..5, both languages.
2. **Page 3 ("Does it find the law — and predict?") renders as a heading and banner only** in the fit checker's
   screenshot; its content appears only after an entrance animation. Content must be present and visible on arrival
   (animations may only enhance, never gate visibility), so screenshots, print and fallback always show it.
3. **Encoding:** "Drei m?gliche Entwicklungen" (a "?" for "ö") on the guess page, and Playwright's `innerText` shows
   replacement characters for "—", "·", "ä", "²" in the headline panel. Find the source (a string assembled outside
   the i18n tables, or a non-UTF-8 step in the build) and fix it; add a test that the built HTML contains no U+FFFD and
   no `?` between letters in any i18n-derived text in both languages.
4. **Baselines show a single value although the text says "ranges over configurations".** E.g. headline "SINDy 3,03 %
   (2/66)". Check what row is shown (one configuration? the `all_ten` row?). The baseline value must be the **range
   min–max over the baseline's configurations** with the counts at both ends, as the banner promises, or the banner must
   say exactly what is shown. Report which it was.

## Design (the user's bar: "the first three pages must hit hard"; results presentation is the core)

5. **Opening pages 1–3** — make them visual and large:
   - Page 1 (problem): the data chart is the hero — large (≥ 60 % of the viewport width, ≥ 50 % of the height),
     headline beside or above it, little text.
   - Page 2 (guess): the three guess curves big and clearly distinguishable, each labelled directly at its line end
     (no legend line listing "(gestrichelt/gepunktet)").
   - Page 3 (solution + how well): solution chart large (data + model curve, the model curve clearly visible over the
     data), found vs true equation side by side; then the headline result as a **chart, not text**: for dim 1 and dim 2,
     one grouped horizontal bar (or dot) chart per metric — structure (pruned, raw as a lighter inner mark) and
     generalization R² > 0.9 — with WISP as a bar and each baseline as a range (min–max over configurations, whisker or
     band) with counts on hover/focus and as text alternative. One fixed colour per method used everywhere on the page
     (WISP the accent colour, baselines muted). If solution and headline do not both fit page 3, keep the page plan's
     split (solution on page 2/3 as WP-X4 placed it) but the headline is a chart.
6. **Results explorer "Overview" tab**: replace the text dump (`raw_exact 31,8% (21/66) · pruned_exact …`) by the same
   chart type as the headline, for every stratum side by side, with the σ/ρ filters. **No internal field names** in
   reader-facing text: `raw_exact` → "structure, raw" / "Struktur roh", `pruned_exact` → "structure, pruned" /
   "Struktur bereinigt", `generalization_variance_weighted_hit` → "generalization R² > 0.9 (variance-weighted)" /
   "Generalisierung R² > 0,9 (varianzgewichtet)", etc.; the field names may appear in the provenance drawer only.
   Text alternative (a small table) behind a toggle for accessibility.
7. **Legends:** never the generic "(gestrichelt/gepunktet)"/"(dashed/dotted)" suffix. Each series has its own named,
   correct style: measurements = dots, clean reference = thin dashed, model = thick solid in the step colour. Prefer
   direct labels at line ends over legends.
8. **System names in German:** the page uses `eq_description` from the benchmark (English) also in German. Provide a
   German name for every system that appears in reader-facing text (a small translation table in the i18n data,
   keyed by system id, covering at least the featured systems, the running example and every system reachable in the
   drill-down; fall back to the English name with no error if one is missing, and report the coverage). Drop noise
   in labels: omit "0 % fehlende Messpunkte" and "Anfangspunkt 1" where they are the default; say only what differs
   ("3 % Rauschen", "zweiter Startpunkt", "jeder zweite Messpunkt fehlt").
9. **Featured cells (test page):** the curves large enough to read (≥ 260 px tall), one featured story at a time with a
   switcher (tabs) rather than three cramped columns; a negative R² gets a one-line explanation ("worse than predicting
   the mean"). One "More" button per page, not two.
10. **Fit at 1366 × 657** (still failing on `p-catalogue`, `p-weak-intro`, `p-frols-intro`, `p-test-intro`): condense or
    move secondary material into the More drawer.

## Acceptance

1. Build exit 0, byte-identical rebuild, size budget; all existing tests (29) adapted and passing, plus tests for
   defects 1–4 and for "no internal field name in reader-facing DOM outside provenance".
2. Strict numerical checks still exit 0.
3. `check_wisp_explainer_fit.py`: all pages fit at 1366 × 768 and 1366 × 657, EN and DE, with screenshots. Playwright
   with Edge works on this machine; if it is blocked in your sandbox, report `blocked` with "browser not runnable here —
   environment, not the task" — Claude runs it.
4. Report `codex/reports/REPORT_WP_X5.md` incl. the answer to defect 4 and the German-name coverage.
