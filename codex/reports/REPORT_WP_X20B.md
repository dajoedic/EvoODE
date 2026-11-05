# WP-X20b - Chapter 9 polish

Status: implementation complete; viewport acceptance blocked by environment.

## Presentation changes

- WISP (Q7) retains its method heading but no per-value `c` or comparison-key subtitle. Baseline table values retain their exact configuration/comparison names.
- Clean, noise and original-comparison pages select one of the four existing strata at a time. No rates are pooled or recomputed. This preserves the full-width tables and three-chart stage without an essential-content scroll container.
- Noise charts have one shared method-colour legend. The Configurations dialog lists the exact baseline configuration for every metric and sigma in the selected stratum/rho. Its optional content may scroll; the essential charts and legend do not.
- Clean prose explicitly states sigma zero, rho 0.5 and the excluded fully clean controls, in both languages. The single clean rho is text; only the system-group selector remains.
- The four story pages have step eyebrows, left-aligned leads and spacing matching the later teaching chapters. The glossary has its step eyebrow and lead. The explorer retains its own layout.
- Original-source metadata is in a compact source disclosure. Unsupported comparison/group/condition combinations display the existing unavailable message.

## Fit checker and tests

The old checker skipped descendants of every `data-internal-scroll` container. Chapter-nine essential content is now checked even if such a marker is accidentally restored. Bounds, container clipping and pairwise SVG text overlaps are checked for every selector combination, including groups without comparison data. Each language/viewport run samples 1 count view, 4 clean views, 8 noise views and 176 original-comparison views: 189 chapter-nine samples. The Python checker rejects missing sampling/clipping evidence and propagates clipping and overlap failures.

The new DOM tests execute the shipped app and page code against actual assembled data in German and English. They check values and exact baseline names across all four groups, both noise rho values, four WSINDy comparisons and eleven comparison conditions; shared legend and dialog opening/closing are also checked. Geometry regression cases check a fitting legend and explicitly mutated below-viewport bounds at both requested heights. These are functional tests, not evidence of browser pixel acceptance.

Field provenance: `stratum`, `sigma`, `rho`, `method`, `configuration`, `metric`, `rate`, `numerator` and `denominator` are existing aggregation rate-row fields in `data/results.json`. Original comparison rows use their existing `comparison` field when `configuration` is absent. `primary_method`, `method_labels` and `selected_configuration_methods` are existing presentation contract fields. No scientific fields were added. Fixtures take their complete field inventory and values from the real assembled HTML; no exporter or scientific data file was edited.

## Validation

- HTML assembler: passed; final HTML 13,755,853 bytes (limit 14,000,000).
- JavaScript numerical checker: passed all six reported cases (final scientific/JS implementation).
- Initial focused presentation tests: 15 passed in 42.03 seconds.
- New focused WP-X20b tests: 3 passed in 6.05 seconds before the final CSS-only adjustment.
- Final complete WISP suite: 77 passed, 333 deselected in 244.02 seconds. The run emitted 30,348 existing `np.trapz` deprecation warnings from `analysis/exploratory/term_relevance/term_relevance.py:198`. All three new WP-X20b cases passed in this final run.
- Final fit checker: exit 2, 0 checks, 0 screenshots. Playwright fails before browser launch with `[WinError 5] Access is denied` while creating subprocess pipes. Edge CLI fallback also fails, exit 2147483651, with `platform_channel.cc` / `Access is denied (0x5)`.

Evidence: `outputs/wp_x20b/fit_attempt.txt`, `outputs/wisp_explainer_checks/wp_x12_fit.json`, `outputs/wisp_explainer_checks/wp_x12_edge_fit.json`; final pytest output: `outputs/wp_x20b/pytest_wisp.txt`. Existing screenshots in the shared output directory are not evidence for this revision.

## Open acceptance and handoff

**Environment, not substance:** no actual browser geometry was measured in this session. Zero overlaps and zero cutoffs at both requested viewports and in both languages remain unverified. Run the following outside the restricted browser-launch environment, then inspect the chapter-nine screenshots. Do not interpret the zero-length overflow list from the failed checker as a successful fit check.

```text
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

Reproduction commands for the completed implementation checks:

```text
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python analysis/scripts/explainer/check_wisp_explainer_js.py
python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp
```

Changes are left uncommitted. No Git commands, Julia, exports or cluster work were performed. `CURRENT_TASK.md` was not edited.
