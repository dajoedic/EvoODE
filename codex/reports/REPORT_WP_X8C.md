# WP-X8c — decision walkthrough

Status: implementation complete; browser acceptance blocked by the environment.

## Changes

Page 3 retains its section, title and deck. Compact chips and one equation slot replace the tall cards and dot track. The animation shows remaining error and short-window changes, all inactive-block gains, the jointly updated coefficients, and every removal check. Steps 3 and 4 each show the successful removal followed by a second check in which all remaining blocks stay. Later steps combine testing, addition and checking. The final phases use exported fitted parameters and reconstruction curves, with a measurement legend, eight measurement-fit R² columns, a single chosen equation and the derivative-prefixed stored truth. Missing curves/scores retain unavailable fallbacks.

Page 2 uses a 2.5 px dashed truth-colour line, painted after the dots and before the reader curve. Its truth label shares the system font, 13 px size and muted colour of the other captions. Browser fit checks now include computed font equality and truth stroke width, both eye states and all 31 page-3 frames. The existing flush-column gate remains.

The assembler runs a recorded-support assertion before writing HTML. Removal replay uses WispCompute.leastSquares. Because compression is private in the frozen numerical core, the presentation adapter contains its exact QR routine; the gate checks that copy verbatim against compute.js and independently checks gains and costs against the full normalized design (absolute tolerance 1e-10). compute.js and data files were not edited. No scientific export, cluster job or campaign was run.

## Field inventory checked against the real export

- Existing live.teaching fields: cell_id, t, observed. These supply the actual teaching observations.
- Existing live configuration: windows, cap, sse_stop, backward_fraction.
- Existing live.featured[0].path fields: candidate_id and active_idxs (one-based recorded supports).
- Existing candidate fields: row.candidate_id, row.active_idxs, row.params (JSON-encoded fitted parameters), curves.t and curves.model. Candidate supports are checked against the corresponding path support.
- Existing feature.chosen supplies the selection; no selection metric name appears on page 3.
- Existing results cell truth supplies the stored true formula, with an explicit derivative prefix. A replaced results bundle may omit this cell; unavailable is shown.
- Presentation-derived fields only: gains, pre/post-addition estimates, remaining fractions, repeated removal costs, threshold and candidate measurement-fit R². No new exported data fields.

## Computed path

All figures below are percentages of the total measured window changes. Full precision values are in outputs/wisp_x8c/numerical.json; UI percentages use one decimal. Supports match all eight recorded stages in order.

| Stage | Support after removal | Remaining before (%) | Remaining after (%) | Threshold (%) |
|---|---|---:|---:|---:|
| 1 | 1 | 100 | 84.9549814 | 7.52250931 |
| 2 | 1, u³ | 84.9549814 | 78.9068152 | 3.0240831 |
| 3 | u, u³ | 78.9068152 | 77.404343 | 0.91783781 |
| 4 | u, u² | 77.404343 | 76.9403725 | 0.235587765 |
| 5 | u, u², sin u | 76.9403725 | 76.8561002 | 0.0421361441 |
| 6 | u, u², u³, sin u | 76.8561002 | 76.8497441 | 0.00317808071 |
| 7 | 1, u, u², u³, sin u | 76.8497441 | 76.8366259 | 0.00655908528 |
| 8 | 1, u, u², u³, sin u, cos u | 76.8366259 | 76.8326637 | 0.00198108632 |

### Stage 1

Gains (%): 1: 15.0450186, u: 7.85997206, u²: 4.41357714, u³: 2.86786529, cos u: 1.10607166, sin u: 0.025068351.
Removal check 1 costs (%): 1: 15.0450186; threshold 7.52250931; all stay.

### Stage 2

Gains (%): u³: 6.0481662, u²: 5.23189351, u: 3.88063172, cos u: 0.026443876, sin u: 0.0130795827.
Removal check 1 costs (%): 1: 18.2253195, u³: 6.0481662; threshold 3.0240831; all stay.

### Stage 3

Gains (%): u: 1.83567562, u²: 1.60053565, sin u: 0.0302639438, cos u: 0.0251533508.
Removal check 1 costs (%): 1: 0.33320348, u: 1.83567562, u³: 4.0032101; threshold 0.91783781; remove 1.
Removal check 2 costs (%): u: 19.7277917, u³: 14.7356849; threshold 0.91783781; all stay.

### Stage 4

Gains (%): u²: 0.471175531, 1: 0.33320348, sin u: 0.0822104251, cos u: 0.0172514675.
Removal check 1 costs (%): u: 3.29361007, u²: 0.471175531, u³: 0.00720500207; threshold 0.235587765; remove u³.
Removal check 2 costs (%): u: 18.6460504, u²: 15.1996554; threshold 0.235587765; all stay.

### Stage 5

Gains (%): sin u: 0.0842722882, u³: 0.00720500207, cos u: 0.00257415887, 1: 0.000468031757.
Removal check 1 costs (%): u: 18.6638138, u²: 15.231556, sin u: 0.0842722882; threshold 0.0421361441; all stay.

### Stage 6

Gains (%): u³: 0.00635616143, cos u: 0.00259515072, 1: 6.65217104e-05.
Removal check 1 costs (%): u: 3.32630385, u²: 0.472388553, u³: 0.00635616143, sin u: 0.0834234475; threshold 0.00317808071; all stay.

### Stage 7

Gains (%): 1: 0.0131181706, cos u: 0.00170697804.
Removal check 1 costs (%): 1: 0.0131181706, u: 0.405732517, u²: 0.15972325, u³: 0.0194078103, sin u: 0.0871240462; threshold 0.00655908528; all stay.

### Stage 8

Gains (%): cos u: 0.00396217263.
Removal check 1 costs (%): 1: 0.0153733652, u: 0.409352967, u²: 0.163270237, u³: 0.0208371257, sin u: 0.0876259303, cos u: 0.00396217263; threshold 0.00198108632; all stay.

## Candidate measurement-fit R²

Exported reconstruction curves are linearly interpolated onto teaching observation times, then scored with the same observation-centred R² definition as page 2. These are browser presentation scores, not the stored reconstruction/generalization evaluation scores. Both existing evaluation metrics elsewhere remain unchanged.

| Stage | Blocks | R² | UI |
|---|---:|---:|---:|
| 1 | 1 | 0.727142773868 | 0.727 |
| 2 | 2 | 0.943690389738 | 0.944 |
| 3 | 2 | 0.990166758132 | 0.990 |
| 4 | 2 | 0.994097775938 | 0.994 |
| 5 | 3 | 0.993653327388 | 0.994 |
| 6 | 4 | 0.994036584425 | 0.994 |
| 7 | 5 | 0.993527085473 | 0.994 |
| 8 | 6 | 0.993941680733 | 0.994 |

Selected candidate: path_004; difference from best R²: 0 (within 0.001, so the plateau sentence is enabled).

## Timing and controls

31 navigable frames: 18 detailed decision frames (including two post-removal rechecks), 4 combined frames, 8 simulation frames and 1 choice frame. Each detailed/combined frame lasts 3.5 s; each simulation stage 1.5 s; choice 8 s. Total nominal loop: 97 s. Combined frames show testing for 1.2 s, addition for 1.1 s and removal checking for 1.2 s. Gain rows enter every 0.3 s (0.25 s fade).

Autoplay begins on page arrival, pauses off-page and in a hidden tab, then resumes. Back/next/restart and strip selection pause playback; play resumes it. Reduced motion starts at the final choice without autoplay, with manual controls available. The DOM harness verifies timing, looping, page/tab pause and reduced motion. Phone CSS stacks the panels and uses two rows for the stage strip; pixel fit is pending.

## Acceptance from this run

- Presentation suite: 49 passed. Bilingual DOM harness checks every frame, computed supports, gains, repeated costs and removal strikes, remaining fractions, R² columns, chosen marker, unique fitted equation, derivative truth, absence of jargon and controls. Includes real-record-derived support corruption, swap, both evaluation metrics, i18n parity and frozen whitelist tests.
- Strict numerical checks: exit 0 (outputs/wisp_x8c/strict.log).
- Recorded path / independent full-design removal-cost gate: exit 0 (outputs/wisp_x8c/trace.log).
- Two byte-identical builds: 11,368,027 bytes, below 14,000,000. SHA-256: 36beb8a64ed5b534691bc3c5cbb641fc66ce3a4237b5928a180417ec3f771905.
- Frozen compute/data hashes stayed identical across acceptance; see outputs/wisp_x8c/acceptance.json.
- Browser fit checker: exit 1. Playwright fails creating its transport with PermissionError [WinError 5] Access is denied. Edge fallback exits 2147483651 and reports Crashpad CreateFile: Access is denied (0x5). No screenshot or layout pass is claimed.

browser not runnable here — environment, not the task. Umgebung, nicht Sache. Acceptance point 3 remains open: Claude must run the fit checker at both requested heights and inspect the DE/EN screenshots. Computed caption font equality, stroke width, flush columns and all-frame pixel fit await that run.

## Reproduction

```text
python outputs/wisp_x8c/validate.py
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

All deliverables remain uncommitted. CURRENT_TASK.md was not modified.
