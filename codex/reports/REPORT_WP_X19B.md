# WP-X19b — implementation and acceptance record

## Scope and delivered changes

Chapters 6–8 now have 15 text-column steps with numbered eyebrows and a single persistent `#x21-stage`. The stage uses the same desktop geometry as chapters 1–5. Each step owns a panel mounted in that persistent host. The host is parsed before the application script. The scientific inputs and the Julia exporter were not modified; Julia was not run.

- System 27 uses x/y, ẋ/ẏ and reader-facing chips, including x², y², x·y, sin x. System 3 uses u. Candidate identifiers remain in records, never in these rendered panels.
- The two replays preserve the recorded test → add → clean-up order, followed by the failed stop test. Test panels use log-ratio bars and a threshold line. Add compares the normalised best gains for the equations on a shared magnified scale; the winning chip flies into its row. Clean-up shows removal costs against half the winning gain and states that no block leaves. The quadratic truth chip is highlighted only after the chapter-seven stop.
- Candidate panels show per-equation chips, split BIC bars (fit error and block price), an axis break, the winner and fitted/true coefficient equations.
- The orbit panels explicitly identify the displayed variable as prey x and use the requested start titles, observations as dots, rounded axes and a magnified two-bar training-error comparison.
- The RHS plot has a shaded observed range, ticks 0/20/40/60/80, named axes, a stage legend and computed markers/readout at the teaching cell's true start u=7.3.
- Lessons have structure chips/meters, the shaded RHS comparison or the three-example structure/R² matrix. The matrix marks R² > 0.9 from the actual records.
- Curves draw in order and hold before looping. Replays support deterministic seek, looping, finish and reduced motion.

## Provenance and frozen results

The legacy exporter no longer reads repository HEAD. `source_identity(metadata)` requires one campaign identity across every declared `result_files` path in the real Q5 run metadata. Those metadata have no separate `git_hash` member. Their canonical directory embeds `354106398d5e67ffa72c237e2ba83e3feeb25b31`; this is also the image tag in the existing `k8s/sideproject_q5_job.yaml`. The manifest uses this source identity, including during `--extend-only`. A new full legacy export uses it in `results.provenance.git_hash` as well. No build-at-commit field is added.

As expressly requested, the shipped historical `results.json` was restored using the task's read-only `git show HEAD:explainer/wisp/data/results.json` command. Its old provenance hash remains part of that frozen historical artifact; it is not rewritten by the extension. Its SHA-256 is `7fb7b8a5f96b5bf118471ea46486d352091a6ad3cf23763782587097c6bb5959`, identical to the original frozen-hash contract and to the committed bytes saved in `outputs/wp_x19b/committed_results.json`. A future full legacy export deliberately changes that historical export-time hash to the source hash; no claim is made that these two provenance values are the same.

A repeat of the actual Python extension export with unchanged inputs produced byte-identical `live.json`, `results.json` and `manifest.json`; exit 0, 236.422 seconds. Hashes are in `outputs/wp_x19b/repeat_export.json`. This checks the actual shipped extension path; the full legacy re-simulation export was not run.

## Field audit against real sources

| Displayed quantity | Origin |
|---|---|
| Candidate support and fitted coefficients | Existing `active_idxs` and `params` in `analysis/data/sideproject_residual_growth/q7_grid/q7_candidates.csv` |
| BIC components | Analysis/presentation calculation from existing `n_samples`, `mse`, `k`: N log(MSE) + k log(N) |
| Structure verdict | Existing `raw_exact` in the candidate CSV; no invented record `success` field |
| Reconstruction/generalization scores | Existing `reconstruction_r2_variance_weighted` / `generalization_r2_variance_weighted` in that CSV |
| True support and coefficients | Existing `studies/regression/phase_c_support.json` and benchmark expressions, using the existing coefficient derivation helper |
| Tests, gains and clean-up costs | Existing Q6/Q7 path functions; the one-dimensional browser path is recomputed and checked against the recorded supports and gains |
| Model curves and start-error bars | Existing verified `outputs/wisp_explainer_julia/q7_examples.jsonl`, including `training`, `true_initial` and clean evaluation arrays |
| Variable names and chips | Presentation mapping of the actual 12-term / 6-term catalogues |
| Seen range and start annotations | Existing observed state arrays, `live.teaching.truth[0]`, and algebraic evaluation of the true/fitted RHS; no replacement ODE solve |

Record audit (`outputs/wp_x19b/record_audit.json`): System 27 has 4 additions, with final maximum test ratios 3.4689504862 and 3.9912479358 below 6.635. The chosen model has exact structure, reconstruction R² 0.5225316301 and generalization R² 0.8216468118. Its noisy/true-start training MSE values are 0.02422074619 and 2.95862176761. System 3 has 3 additions and final maximum ratio 0.02503682074 below 6.635; its structure is incorrect despite reconstruction R² 0.9995847427 and generalization R² 0.9639646781. Its observed range is 20.49018834 to 80.48406418. At the teaching start u=7.3, the true RHS is 5.20039030956; the model RHS is 10.70167913646, computed from the stored constant/linear/cubic coefficients.

## Tests and browser acceptance

The axis-title failure was caused by the legacy harness hard-coding y=306 for a 310-pixel chart while X19 introduced 360-pixel wide-label charts. The assertion now derives the baseline from the SVG viewBox. It still requires a visible axis title. The small legacy harness explicitly leaves mounted example stages to the bilingual DOM harness, which executes the real source against the shipped HTML.

The mounted harness checks all replay phase boundaries, support order, gain agreement, stop highlighting, cost threshold lines, per-equation competition bars, teaching-start annotation, loop hold, reduced motion, and the absence of `u1^`, `u2^`, `u1*u2`, `q7_0` in the new panels. New Python tests cover the real source-identity metadata, conflicting/empty metadata rejection, restored frozen results, manifest identity, panel inventory and stage-before-script ordering.

The fit checker retains both languages and both requested viewports. It now inspects the mounted stage, stage overflow, minimum text size, raw names, exponent notation and chart-label overlaps; replay samples include both sides of phase boundaries and the flying-chip interval.

Final full suite: `python -X utf8 -m pytest analysis/tests -k wisp -q -p no:cacheprovider` ? **71 passed, 333 deselected, 30,348 warnings, 450.68 seconds** (wrapper exit 0, 459.813 seconds). Raw output: `outputs/wp_x19b/full_wisp.log`; wrapper result: `outputs/wp_x19b/full_wisp_run.json`. The warnings are retained verbatim in that log. The final assembled HTML was also checked to contain the current app, navigation and CSS sources verbatim. No full-suite rerun was performed.

Browser acceptance is **blocked by the environment**. Playwright fails before browser creation with `PermissionError: [WinError 5] Access is denied` while creating its subprocess pipe. The existing Edge fallback also exits 2147483651 with `FATAL:mojo/public/cpp/platform/platform_channel.cc:187 … Access is denied (0x5)`. There are 0 browser checks and 0 screenshots from this session. There is no assertion of zero visual overlaps, no overflow, or completed visual QA. Raw evidence is in `outputs/wp_x19b/fit_run.log`, `outputs/wp_x19b/browser_failure.json` and `outputs/wp_x19b/edge_failure.json`. A final-build retry subsequently produced no output for more than four minutes; its own Python/Edge processes were identified by their start times and stopped. This is recorded in `outputs/wp_x19b/fit_final_retry.txt`. These remain open acceptance requirements.

Commands for acceptance on a machine that permits browser launch:

```powershell
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python -X utf8 -m pytest analysis/tests -k wisp -q -p no:cacheprovider
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

The final HTML is 12,920,677 bytes; SHA-256 `233c79a0af7773ba34e6ecf8da7c5b8b6e84e5efa4c0b80af3d47571310451e4`.

All changes remain uncommitted. No staging, commit, push, cluster/campaign work, or Julia execution was performed. Each invoked export has a 14-minute timeout; the full test suite likewise has a 14-minute timeout. The sole Git invocation was the read-only restore command explicitly prescribed by CURRENT_TASK.md. CURRENT_TASK.md was not edited.
