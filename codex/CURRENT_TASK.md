# WP-X3 — WISP explorable: full-screen pages with transitions, a visible pipeline map, final polish
**Language: Python** (build, checks) — the page itself is static HTML, CSS and JavaScript.

Stand 2026-11-02. Follows WP-X2 (`codex/reports/REPORT_WP_X2.md`, commit `3e151f3`). Every rule from WP-X1/X1b/X1c/X2
stays in force (whitelist, blind rule, no Q7/Q8 results, no hand-typed result numbers, both metrics side by side,
strata never pooled, exact/surrogate never mixed in a structure metric, i18n key parity EN/DE, byte-identical rebuild,
results contract, swap test, size budget ≤ 14 MB). **No numerical code and no data change in this WP** — `compute.js`,
the exporters' numbers and the Julia import stay as they are; only structure, layout, text and presentation change.

## User feedback driving this WP (2026-11-02)

1. The user loves sites where you **don't scroll a long page**: scrolling (wheel, arrow/PageDown key, swipe) brings in
   the **next full-screen page with a dynamic transition**. Step by step. The art is to split the content so that each
   step fits on one screen. Target: **laptop, 1366 × 768 CSS px viewport** (browser chrome already subtracted —
   design for a usable viewport of 1366 × 657 as well, see Acceptance).
2. "The beginning was good, then I **lost the thread**." It must be **unmistakably clear which part is the weak form,
   which part FROLS, which part FoBa, which part the stop rule, which part the fit, which part BIC**, and which part
   the test.
3. Polish found in review: the curve panels in the "second starting point" section are far too small; the legend says
   "Julia-Auswertung"/"Julia evaluation" where a reader needs "model"; the BIC chart's x-axis shows non-integer term
   counts (2.25); the zero-residual stop is printed as 0,00000000000001 (use scientific notation, e.g. 10⁻¹⁴).

## Scope

### 1. Full-screen pages ("slides") with transitions

- Restructure the page into a sequence of full-viewport pages. Each page: **one idea, at most one main figure**, a
  short text. Expect roughly 35–50 pages; splitting long sections into several pages is the main work.
- Navigation: mouse wheel / trackpad, ↓ ↑ PageDown PageUp Space, touch swipe, and a dot/progress navigation at the side
  that shows the current page and its section on hover. One gesture = one page (debounce trackpad inertia so one swipe
  never skips several pages). Each page has a deep link (`#p-<id>`), browser back/forward works, the URL keeps the
  `lang` parameter.
- Transitions: a calm, fast entrance (≈ 400–600 ms: fade + slight slide or a shared-element move where a figure
  continues from one page to the next). No gimmicks. Figures animate in when their page becomes active.
- **Interactions must never trigger a page change**: while dragging a slider, the weak-form window, or scrolling inside
  an element that scrolls internally (tables, the results explorer), wheel/touch go to that element. Keyboard focus
  inside a control keeps arrow keys for the control.
- Prefer native CSS scroll snapping plus a small amount of JS over a library; if a library is used, it must be pinned,
  from cdnjs/jsdelivr, and justified in the report.
- **Fallbacks:** viewports narrower than 760 px or lower than 560 px, and `prefers-reduced-motion: reduce`, get the
  normal continuous scrolling page (no snapping, no transitions) with the same content order. Print view: continuous.
- **The results explorer is the last part and is a full-screen app**: it fills the viewport and organises itself
  internally (tabs or a filter bar plus panels; internal scrolling only inside clearly bounded panels). The drill-down
  is part of that app.

### 2. The thread: a pipeline map that is always visible

- Introduce, right after the problem has been motivated (after the noise page), **one overview page "WISP in one
  picture"**: the pipeline as a diagram — data → weak form → FROLS (grow) → FoBa (clean up) → stop → fit every
  candidate → BIC (choose) → test on a second starting point — with **one sentence per box** (the existing
  one-sentence-per-component texts from the cookbook's "WISP in einem Satz pro Baustein", translated).
- From then on a **compact pipeline bar** stays visible on every method page (top or side), with the current step
  highlighted, so the reader always knows "I am in FROLS now" / "this is FoBa" / "this is BIC". Clicking a step jumps
  to its first page.
- Each method step's first page starts with a short title card: the step's name, what goes in, what comes out
  (e.g. FROLS: in = the weak linear system, out = a growing list of terms). Use one colour per step consistently in the
  bar, the title card and that step's figures.
- Where FROLS and FoBa happen in the same figure (the step-through), mark each event visibly as "FROLS: added …" or
  "FoBa: removed …".
- Before the results explorer: a recap page — the same pipeline picture, now with the running example's actual
  outcome written under each box (from the data, no typed numbers).

### 3. Polish (from the review)

- Section "second starting point": curve panels at a readable size (each featured cell gets its own page with the
  reconstruction and generalization curves large).
- Legend labels: "model" / "Modell" (and "clean target" / "saubere Referenz", "measurements" / "Messwerte"); no
  implementation names (Julia, Python) in reader-facing labels — they may appear in the provenance details only.
- BIC chart: integer ticks for the number of terms.
- Very small/large numbers in prose and captions in scientific notation with superscript exponents, locale-aware.
- German text: keep the WP-X2 approach (faithful, understandable translation; technical terms are fine). New strings
  get both languages; key parity test stays.

### 4. Fit check — every page must fit one screen

- Add a built-in check mode: when the page is opened with `?fitcheck=1`, it lays out every page in the snapped mode
  at the current viewport, measures whether any page's content overflows the viewport (content box, all figures and
  controls, in the current language), and writes the result as JSON into a `<pre id="fitcheck-result">` element
  (list of page ids with their content height vs viewport height, and `ok: true/false`).
- Add `analysis/scripts/explainer/check_wisp_explainer_fit.py`, which runs headless Microsoft Edge
  (`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe --headless=new --dump-dom`) on the built file with
  `?fitcheck=1&lang=en` and `&lang=de` at window sizes **1366×768** and **1366×657**, parses the JSON and exits
  non-zero if any page overflows. Headless Edge may be blocked in your sandbox (WP-X2 report) — then write and
  review the script; **Claude runs it** and will send overflow findings back.
- Also have the script save one screenshot per page per language at 1366×768 into `outputs/wisp_explainer_checks/
  pages/` (Edge `--screenshot` with the deep link), so the pages can be reviewed visually.

## Forbidden

Everything WP-X1/X1b/X1c/X2 forbade. In addition: no change to `compute.js` behaviour, to any number in the data files,
to the Julia script or its output, or to the featured-cell selection; no hand-typed numbers in new texts; no library
that is not pinned and justified.

## Acceptance

1. Data export (`--extend-only` is fine, since no data changes) and assembly exit 0; rebuild byte-identical; size
   budget met.
2. All existing tests pass (WP-X1..X2, 21) plus new ones: navigation logic (next/previous page, deep link, no page
   change while a slider or the drag window is active — Node DOM harness), pipeline bar highlights the right step on
   every method page, fallback mode below 760 px / reduced motion, i18n parity for new keys.
3. Strict numerical checks (`check_wisp_explainer_js.py`, `check_wisp_explainer_x2.py`) still exit 0.
4. `check_wisp_explainer_fit.py` written; either run with exit 0 (all pages fit in both languages at both window
   sizes) or, if Edge is blocked here, status `blocked` with note "Edge headless not runnable here — environment,
   not the task" and everything else done.
5. Report `codex/reports/REPORT_WP_X3.md`: the page list (id, section, pipeline step, one-line content), navigation
   design, fallback rules, what was split how, check results.
