# WP-X3 ? full-screen WISP explorable

Status: **blocked ? Edge headless not runnable here ? environment, not the task**.
Implementation, data export, assembly, numerical checks and DOM tests are complete. Actual browser layout, fit acceptance and screenshots remain unverified; no successful pixel check is claimed.

## Delivery

The presentation contains **48 pages**. Existing sections were split into explanation, controls, figure and evidence pages. The four featured cells each have a dedicated page; two-state curves use both reconstruction/generalization columns with vertically stacked state curves. A long missing-truth support listing is preserved in a bounded disclosure. The glossary and credits precede the recap, so the results explorer is the last page.

The weak integration-window figure, term integrals and matrix are separate pages. FROLS gains and residual history are separate pages. Fit controls, fitted curves and BIC are separate pages. Noise motivation is separate from the noise figure. The recorded FoBa example follows its own title card. No numerical search, fitting, Julia source, featured selection, result rate, metric definition or scientific data was changed. No library was added. The existing pinned KaTeX resource is retained.

## Navigation and thread

Native CSS scroll snapping supplies page alignment; a small local JavaScript controller advances one page per wheel gesture, touch swipe or navigation key. The outer document rejects native manual scrolling in snapped mode; bounded internal panels retain their own scrolling. Each accepted gesture selects a page, updates its active class and scrolls it into view. Entrance animation is a 480 ms fade/18 px movement, with a 560 ms figure reveal. A wheel burst stays locked until a quiet gap of 220 ms, with a minimum 650 ms transition lock. Key repeats do not advance again. Sliders, weak-window pointers, focused controls, tables, disclosures and internal panels are protected from page-navigation events. Pointer cancellation releases the guard.

Side dots have page/step hover labels and accessible labels. Every page has a stable `#p-?` address. Internal links and dots use History pushState; popstate/hashchange restore the selected page. URL updates preserve the language parameter. In continuous mode, scrolling observes the nearest page and replaces the hash without scrolling it again.

The overview uses data ? weak form ? FROLS ? FoBa ? stop ? fit ? BIC ? independent-start test. Component sentences are adapted from `docs/kochbuch/Kochbuch_WISP.html`, ?WISP in einem Satz pro Baustein?; data and test complete that diagram. Each component has a title card with explicit input/output. A shared step-to-colour mapping drives title cards, pipeline links and model curves. Every method page has its step highlighted; step links jump to its first page. FROLS and FoBa events are explicitly named, including recorded backward events.

The recap reads the running featured cell, its stored supports, candidate rows, BIC and scores. It distinguishes the stored Q5 capped path from the earlier live noise-based stop; those two protocols are not presented as one measured outcome. Outcome text is generated from exported fields or existing displayed weak-system dimensions. Long outcomes scroll within visibly bounded boxes.

## Fallback and polish

Widths below 760 CSS px, heights below 560 CSS px and reduced-motion preferences use continuous scrolling with the identical content order. Print removes fixed navigation, snapping, animation and internal height caps. `fitcheck=1` explicitly forces the full-screen layout even when a fallback would otherwise apply.

Legends say model/Modell, clean target/saubere Referenz and measurements/Messwerte. Pending curve captions also avoid implementation names. BIC's term axis renders integer ticks. Finite small/large values use locale-aware mantissas and Unicode superscript powers of ten; scientific calculations and stored values are untouched. All new text is in both language tables, with key parity checked.

## Reproducibility and data invariants

`build_wisp_explainer_x2.py --extend-only` exited **0**, consumed the existing **1,663** Julia records and produced **1,667** display checks. Its run took **29.453 s**. Export was checked with a byte snapshot of all three existing data files; those exact bytes were restored afterwards so this presentation WP leaves the on-disk data unchanged. The assembler reads the current source translation tables into the HTML presentation copy. It does not rewrite the data files. Two final assemblies exited 0 and were byte-identical.

Final HTML: **11,298,085 bytes**, below 14,000,000; SHA-256 `5265156b27e2472c15f31f11435bd173a7efa4b6627a03b3ac03411bd646dcb2`. Source language tables: **325 keys** each.

| Data file | Unchanged SHA-256 |
| --- | --- |
| live.json | `a78b46e3025402ecdc339cde9f415b9a518900695440c34060ad4f53be6aa4eb` |
| manifest.json | `f15b0f12df2d7df0ac3f2b815830ea2f9aa4c60558fd0fe19fa32119c3e6ab76` |
| results.json | `7fb7b8a5f96b5bf118471ea46486d352091a6ad3cf23763782587097c6bb5959` |

Evidence: `outputs/wisp_explainer_checks/wp_x3_rebuild.json`.

## Checks and remaining browser acceptance

The combined suite passed **26 tests** (21 existing and 5 new), exit 0, in **42.81 s**. The final DOM suite was rerun after the last bounded-provenance adjustment; see `wp_x3_final_dom.txt`. The 15,174 existing NumPy trapz deprecation warnings are unchanged.

The new tests derive page inventory and markup from the real built deliverable. They execute both shipped presentation scripts in a minimal Node DOM in English and German: all 48 pages initialize, four featured panels and four result-claim markers survive, slider and weak-window events do not navigate, normal keys do, back/forward restores the page, language stays in the URL, every method page highlights its own step, and narrow-screen fallback activates. Pure controller checks additionally cover boundaries, inertia, reduced motion and height/width thresholds. This DOM has no layout engine and provides no pixel evidence.

Both strict numerical scripts exited **0**. Reference maximum relative coefficient errors remain 5.82e-13, 4.39e-14 and 1.83e-14. The significance-rule stop steps remain 4, 3 and 2. Logs: `wp_x3_strict_js.txt`, `wp_x3_strict_x2.txt`. Node syntax checks and Python compilation checks exited 0.

The built-in fitcheck forces full-screen mode, waits for fonts and optional KaTeX, disables animations, measures each content box and descendant bounds, and publishes JSON in `<pre id="fitcheck-result">`. Descendants inside bounded internal panels are excluded while their panel boundaries remain checked. Results include page id, section, step, content/available/viewport heights, overflowing element ids and per-page/overall `ok`.

`check_wisp_explainer_fit.py` invokes Edge `--headless=new --dump-dom` at 1366?768 and 1366?657, in both languages. It rejects missing reports, wrong viewport dimensions, empty inventories, language mismatch and overflow. It requests one screenshot per page/language at 1366?768 using the same deep links and validates that each image was created. A 14-minute overall budget bounds the run. Evidence is saved even on failure.

Edge failed before page initialization with native exit **2147483651**, `mojo/platform_channel.cc: Access is denied (0x5)` and crashpad access failures. Checker evidence records exit **2**; no screenshots or browser measurements were produced. See `outputs/wisp_explainer_checks/wp_x3_fit.json`. Therefore acceptance 4 follows the prescribed environment-blocked branch. Claude must run:

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

A successful run must contain four fit reports, all `ok: true`, and **96** page screenshots under `outputs/wisp_explainer_checks/pages/`. Fix any reported overflow before visual acceptance. The checker has been written and reviewed, not passed in this sandbox.

Reproduction:

```text
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python analysis/scripts/explainer/check_wisp_explainer_js.py
python analysis/scripts/explainer/check_wisp_explainer_x2.py
python -m pytest analysis/tests/test_wisp_explainer.py analysis/tests/test_wisp_explainer_x2.py analysis/tests/test_wisp_explainer_x3.py -q -p no:cacheprovider --tb=short
```

No Git operation, staging, commit, campaign, cluster job, regression run or new scientific simulation was performed. All changes are uncommitted.

## Page inventory

| Page id | Section | Pipeline step | Content |
| --- | --- | --- | --- |
| `p-hook` | hook | ? | Motivation: infer a rule from a measured trajectory. |
| `p-guess` | hook | ? | Guess a rule and compare its curve to measurements. |
| `p-equation` | equation | ? | The logistic equation and the meaning of its coefficients. |
| `p-logistic` | equation | ? | Interactive rate and capacity controls with the logistic curve. |
| `p-predator` | equation | ? | A coupled predator?prey equation. |
| `p-predator-curves` | equation | ? | Coupled time curves and phase portrait. |
| `p-data-intro` | catalogue | data | Data title card: measurements in, catalogue out. |
| `p-catalogue` | catalogue | ? | Why a catalogue of possible terms is needed. |
| `p-term-controls` | catalogue | ? | Choose terms and set coefficients in the illustration. |
| `p-play` | catalogue | ? | See the selected terms generate a trajectory. |
| `p-library` | catalogue | ? | Catalogue dimension, term count and combination count. |
| `p-noise-context` | noise | ? | Why numerical differentiation amplifies measurement noise. |
| `p-noise` | noise | ? | Noise control, observations and the noisy derivative side by side. |
| `p-overview` | overview | ? | Eight-box pipeline with the cookbook component sentences. |
| `p-weak-intro` | method | weak | Weak-form title card, input and output. |
| `p-weak` | weak | weak | Integrated equation rather than differentiated measurements. |
| `p-window` | weak | weak | Drag or adjust an integration window and compare its change. |
| `p-matrix` | weak | weak | A window becomes a row in the weak linear system. |
| `p-integrals` | weak | weak | Integrals for the possible terms, with clean and noisy areas. |
| `p-frols-intro` | method | frols | FROLS title card, weak system in and growing support out. |
| `p-growth` | growth | frols | Search explanation, source selection and live/reference provenance. |
| `p-path` | growth | frols | Step controls, candidate gains, current equation and labelled FROLS/FoBa event. |
| `p-path-residual` | growth | frols | Residual history, including the empty-model starting point. |
| `p-foba-intro` | method | foba | FoBa title card and backward-removal criterion. |
| `p-backward-record` | growth | foba | The recorded backward event and its resulting equation. |
| `p-stop-intro` | method | stop | Noise-based stop title card, input and output. |
| `p-stopping` | stopping | stop | The Q5 cap and the live significance stop remain distinguished. |
| `p-stop-example` | stopping | stop | Residual versus estimated noise floor and resulting stop. |
| `p-fit-intro` | method | fit | Fit title card: path candidates in, fitted trajectories out. |
| `p-selection` | selection | fit | Refit explanation and the unchanged pending/accepted gate notices. |
| `p-candidate` | selection | fit | Candidate controls, stored equation, MSE, penalty and BIC. |
| `p-fit-curves` | selection | fit | Large reconstruction curves for the selected candidate. |
| `p-bic-intro` | method | bic | BIC title card and selection criterion. |
| `p-bic` | selection | bic | Candidate BIC chart with integer term ticks and the BIC equation. |
| `p-test-intro` | method | test | Independent-start test title card, input and output. |
| `p-generalization` | generalization | test | Explain reconstruction and an excluded second starting point. |
| `p-featured-0` | generalization | test | Running example: large reconstruction/generalization panels and both R? weights. |
| `p-featured-1` | generalization | test | Exact dim-2 example: large panels for both states and both R? weights. |
| `p-featured-2` | generalization | test | Missing-truth example, scores, curves and bounded path-support evidence. |
| `p-featured-3` | generalization | test | Generalization failure: large reconstruction/generalization panels and both weights. |
| `p-generalization-caution` | generalization | test | Limits of the current method. |
| `p-glossary` | glossary | ? | Glossary entry page. |
| `p-definitions` | glossary | ? | First group of glossary definitions. |
| `p-definitions-more` | glossary | ? | Second group of glossary definitions. |
| `p-definitions-last` | glossary | ? | Final group of glossary definitions. |
| `p-credits` | glossary | ? | Component origins, credits, provenance footer and return link. |
| `p-recap` | recap | ? | Same pipeline, annotated with stored running-example outcomes. |
| `p-results` | results | ? | Full-screen explorer with shared filters, scrollable strata and scrollable drill-down. |
