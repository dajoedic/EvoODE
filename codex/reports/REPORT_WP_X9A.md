# WP-X9a — one block alone

Page 3 now shows six selectable single-block bars, the selected window-change prediction and its equation. Buttons support keyboard activation and expose aria-pressed; the winner is selected initially. Both languages contain the requested explanation, result and recorded-run caption. Phone CSS stacks the columns. The former page-3 walkthrough, timers, controls, stage calculations, CSS and translation keys are removed. The shared x8_show/x8_hide/x8_true keys remain for page 2.

All 18 other section markups are byte-identical to the starting state. Frozen SHA-256 checks confirm that compute.js and all three data files are unchanged. No Git operation, scientific export, campaign or cluster job was run. CURRENT_TASK.md was not changed.

## Computed values

Values from the final check_wisp_work.cjs run, saved in outputs/wisp_x9a/numerical.json:

| Block | Gain / total (%) | Gain / explainable (%) | Display (%) |
|---|---:|---:|---:|
| 1 | 15.045018627 | 52.894313818 | 52.9 |
| u | 7.859972057 | 27.633586831 | 27.6 |
| u² | 4.413577143 | 15.516972112 | 15.5 |
| u³ | 2.867865288 | 10.082657276 | 10.1 |
| cos u | 1.106071659 | 3.888655967 | 3.9 |
| sin u | 0.025068351 | 0.088133704 | 0.1 |

Empty-support noise floor: **71.556453727 %**. Explainable fraction: **28.443546273 %**. Normalization is available and used; the total-share fallback is not used on these observations. Tests cover unavailable and nonpositive-explainable fallback cases.

Winner: block **1**, equal to live.featured[0].path[0].active_idxs[0] = [1]. Its fitted coefficient is **6.8542379170198435**, displayed as `du/dt = 6,85` in DE and `du/dt = 6.85` in EN, without a trailing constant block. The chart uses **496** windows of the longest design length, **16** sample intervals, with window centres on the time axis.

Field provenance: live.teaching.t, live.teaching.observed, live.windows and the first recorded support are existing export fields checked against actual live.json. Gains come from WispCompute.path(...).steps[0].gains. Coefficients use its exact private QR compression (checked verbatim against compute.js) and existing leastSquares. Noise floor and explainable shares are presentation calculations using existing noiseVariance/noiseFloor. No record fields were invented or added.

## Acceptance

- **48 tests passed in 64.06 s** on the final implementation, including bilingual DOM interactions, six chart/equation switches, bar order/values, window centres, constants, no jargon, i18n parity, corrupt-record rejection, fallback paths and the existing results swap test. Analysis dependencies emitted 15,174 deprecation warnings.
- Strict numerical checker: **exit 0**, including significance-rule checks. Maximum reported relative coefficient error: **5.82e-13**.
- Both builds: **exit 0**, byte-identical, **11,353,666 bytes**, below 14,000,000. SHA-256: aa6816233821af97b544c7ce4ee956278d3077acad81bbfb4088d0efffd84fc9. Data size budget passed.
- Final browser checker: **exit 2**, **0 rendered checks, 0 screenshots**. Playwright fails creating its transport with WinError 5; Edge fallback exits 2147483651 with Mojo/Crashpad access denied. Evidence: outputs/wisp_x9a/final_fit.log and outputs/wisp_explainer_checks/.

**browser not runnable here — environment, not the task. Umgebung, nicht Sache.** Actual fit at 1366 × 657 / 768 and phone overflow remain open for Claude. The browser checker covers every block selection, equation/line changes, constant formatting and 390 px phone overflow, alongside retained page-2 gates. The no-layout DOM harness cannot establish pixel fit.

Reproduce:

```text
python outputs/wisp_x9a/validate.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

Final logs and input/build hashes are under outputs/wisp_x9a/. Deliverables remain uncommitted.
