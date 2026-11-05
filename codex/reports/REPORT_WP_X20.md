# WP-X20 — Q7 results and chapter 9

## Disposition

Implementation is present, uncommitted. Acceptance is blocked by missing source
evidence and environment-dependent checks:

* `analysis/data/sideproject_residual_growth/q7_q5w_comparison.csv` does **not**
  exist in this workspace. Consequently **0 comparison rows** were copied.
  The adapter and chapter view are implemented; the delivered comparison remains
  explicitly pending. No alternate WSINDy source was opened or generated.
* Julia was **not run**, as instructed. Q7 result display curves remain withheld
  until Claude produces `outputs/wisp_explainer_julia/q7_results.jsonl`.
* The fit checker could not start Playwright: `[WinError 5] Access is denied`.
  Its direct Edge fallback timed out at the viewport probe after 35 seconds.
  Exit 2, 0 checks, 0 screenshots. This is an environment block, not evidence of
  passing or failing pixel layout. Evidence: `outputs/wisp_explainer_checks/wp_x12_fit.json`.
* The complete `-k wisp` suite is deferred until after Claude's Julia run,
  following the task's explicit test policy.

## Sources and field audit

`wisp_results_x20.py`, called by `build_wisp_explainer_x2.py`, replaces only the
results evidence after the existing verified teaching export. Contract version
2 and its top-level field inventory remain in place.

| Fields | Actual source / layer |
| --- | --- |
| `stratum`, `sigma`, `rho`, `n_units`, `n_cells`, `method`, `configuration`, `metric`, `numerator`, `denominator`, `rate`, `min_rate`, `max_rate` | Analysis aggregation: `q7_grid/q7_rates.csv`; every string and row copied unchanged, no rates calculated |
| Chosen `cell_id`, `unit_id`, `system_id`, `initial_condition_set`, `size_rule`, `candidate_id`, `active_idxs`, `params`, `raw_exact`, `pruned_exact`, both reconstruction/generalization scores and hit flags | Analysis aggregation: `q7_grid/q7_units.csv`, selecting `size_rule == c`; complete row copied unchanged |
| Candidate support/parameter inventory | Analysis aggregation: `q7_candidates.csv`, also bound to the Julia export by its SHA-256 |
| Protocol, image/commit, protocol document/hash | `q7_run_metadata.json`; commit is its declared image tag, not checkout state |
| Baseline source/reference identity | Existing WP-N47 provenance retained; no baseline refit or new baseline aggregation |
| True equation, catalogue, original observations and clean target identity | Existing benchmark and Q5 cell payload/binary exports for the same cell; original binary hash checks retained |
| Result display curves | New Julia JSONL only; full-grid targets, scores and Q7 source hashes checked before display thinning |
| `comparison`, method, metrics, numerator, denominator, rate | Expected authorized comparison CSV, absent here; no invented fixture or substitute evidence |

There are **3,672 rate rows**, **1,632 chosen-rule cells**, and **14 cells with no
chosen candidate** (blank candidate/support/parameter/score fields in the real
Q7 units file). These 14 cells display an explicit missing-model message, retain
their recorded failed structure/hit flags and are not replaced by Q5 models.

The Q7 metadata has no `result_files` or separate campaign commit field.
`provenance.campaign` therefore contains its declared image string;
`git_hash`/`protocol_commit` contain that image's full commit, and
`protocol_sha256` identifies the separately declared Q7 protocol document.
The image declaration is not presented as an image digest.

| Source | SHA-256 |
| --- | --- |
| `q7_rates.csv` | `e1cfc8e1dff980fbfc5ded55d947e0686f5467b8b585c9f4965c8d8db7a02c12` |
| `q7_units.csv` | `d627efd1546651f2ce1f8d8f2ade09416ccbb79f443a0c1ef18ced2ee4eff3f1` |
| `q7_candidates.csv` | `0169d0784bb38b22f788b05c6347e6a8417b67273c14ff90967e9661a40d9120` |
| `q7_run_metadata.json` | `3fe590237cf0baab46ccb07951044accc0bab9e6ac1c538173401a66de0cae60` |

These are also recorded in `manifest.x20_inputs`. Scientific sources were not
modified. Q7 is labelled interim, with Q9 after W-4 as the final source.

## Julia display path and cost

`--q7-results` selects the chosen rule-c row for every result cell, rather than
the named example paths. Existing `--q7-examples` and Q5 modes remain available.
The new mode evaluates stored coefficients through `q4_evaluate` and `simulate`;
it calls no fitting entry point or optimizer. The score tolerance remains
`1e-12` for all four stored score comparisons. Nonfinite scores, model failures,
hash mismatch or missing targets withhold curves.

Reuse requires the same cell, decoded support and parameter vectors, matching
stored scores, and an existing passed Q5 display record with the current Q5
units/candidate hashes. It does not rely on candidate IDs being equal. Reused
records carry `reused_from`; their new source hashes bind them to the Q7 files.
The output is written to a temporary file and renamed only after completion.

Current actual Q7 result exports: **0 reused, 0 evaluated**, **1,618 pending**,
**14 without a model**. The existing real Q5 records establish **804 eligible
reuses**, leaving **814 fresh model evaluations** for Claude's full run.
The Julia summary will report the actual counts, target validations and elapsed
wall seconds. These prospective counts are not claimed as Julia test results.

`full_run.log` contains no elapsed-time or core-time measurement, and no timing
metadata accompanies the Q5 display export. A core-minute estimate is therefore
unavailable. The permitted alternative is a solve count: at most **3,256 model
ODE solves** (two targets, two solves per target, for 814 models), plus **48 clean
target validation solves**, hence **3,304 ODE solves**. Exceptions can reduce the
actual solve count. No training solve is added in result mode. Julia startup,
compilation and JSON transport cost are unmeasured. Stop a local run if it
exceeds the protocol's 15-minute limit.

The whole Julia extension was read against its include chain, real CSV fields,
`q4_evaluate`, `build_trajectory` and existing JSONL shape. It explicitly handles
empty chosen records; `findfirst` is checked before indexing; JSON records to be
mutated are read as `Dict{String,Any}`; support/parameter arrays are collected
before conversion. Julia 1.12.6 remains mandatory.

## Chapter 9 and retained teaching sources

Six delivered pages follow chapter 8: what is counted, without noise, with noise,
original WSINDy, the three-tab explorer, and glossary/credits. The masthead and
page dots now include chapter 9. German and English strings are supplied.

The clean table and noise small multiples show unpruned exact structure recovery
beside variance-weighted reconstruction and generalization hit rates, with the
threshold from `results.score_threshold`. Baseline configuration names remain
under their respective values; plots preserve original source-row values.
Each stratum is separate. Noise plots select an explicit rho and do not use
pooled-rho rows. The explorer retains both score weights and raw/pruned structure
views. Its drill-down uses the Q7 selected equation and shows both verified
trajectory targets when available.

Important source constraint: the aggregation excludes clean controls. For
sigma zero, only rho **0.5** is available in the nonpooled rates. The noise-free
page therefore shows that condition explicitly and explains the exclusion;
there are no invented full-sampling clean-control rates.

The comparison view copies Q7 and W1/W1-interp comparison rows for each selected
library/condition, without using the general Q7 rates as a substitute. Its
source and the requested MATLAB/JKU/W-6b provenance note are exposed. Actual
comparison-row verification remains impossible until the CSV is supplied.

Chapters 1–5 and legacy featured narratives stay on their verified Q5 sources;
featured chosen rows are now explicitly stored as `live.featured[].result_row`
to prevent the Q7 results switch from changing their narrative scores. Chapters
6–8 retain their named Q7 example source and verified example display file.
Glossary additions cover WISP, Q7, FoBa, BIC and weak form. Existing credits remain
in their end-page detail drawer. New result views are static; existing animation
loops, deterministic seeking and reduced-motion behavior are retained.

## Validation

Final command, after the last source and data changes:

```text
python -m pytest analysis/tests/test_wisp_explainer_x20.py analysis/tests/test_wisp_explainer_x3.py analysis/tests/test_wisp_explainer_x4.py analysis/tests/test_wisp_explainer_x19.py analysis/tests/test_wisp_explainer_x19b.py -q --disable-warnings --maxfail=2
```

Result: **22 passed, 1 warning, 176.68 seconds**, exit 0. This includes exact Q7
CSV/row/hash comparisons, missing-model handling, real-record reuse identity,
all delivered/legacy bilingual DOM navigation, retained chapter animations and
named examples, and two byte-identical HTML builds. The successful HTML build
also runs the existing live-work numerical checker.

Final HTML: **10,817,240 bytes**; data directory: **10,567,989 bytes**.
HTML SHA-256:
`7e484085f713b708fdd16a0b2b645f12fb3760023bcc1221c1765b4b598089ac`.
The rebuild record in `outputs/wisp_x4/rebuild.json` contains this same hash and
`byte_identical: true`. All `x2_sources` and `x20_inputs` hashes were checked
against final workspace files and matched. On-disk live translations match the
German/English source JSON files.

Earlier intermediate failures exposed obsolete page-count / hidden-results
assertions and a German encoding error; these were corrected. An intermediate
rebuild assertion also ran while CSS was being edited; it does not count as
final rebuild evidence. No successful browser pixel check or Julia evaluation
is claimed. The full post-Julia suite remains outstanding.

## Commands for Claude, in order

Run from the repository root, with the pinned Julia **1.12.6** executable.
Expected Julia runtime in minutes is unknown; the full-run cost bound is **3,304
ODE solves** as above. The eight-cell smoke covers both reuse and fresh-model
paths and writes to a separate file.

```powershell
julia --project=. --startup-file=no studies/explainer/export_wisp_display_trajectories.jl --q7-results --limit 8 --output outputs/wisp_explainer_julia/q7_results_smoke.jsonl
julia --project=. --startup-file=no studies/explainer/export_wisp_display_trajectories.jl --q7-results --output outputs/wisp_explainer_julia/q7_results.jsonl
python analysis/scripts/explainer/build_wisp_explainer_x2.py --extend-only
python analysis/scripts/explainer/build_wisp_explainer_html_x2.py
python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp
python analysis/scripts/explainer/check_wisp_explainer_fit.py
```

Restore the authorized comparison CSV before the Python export. The exporter
uses the existing verified `live.json`, observation exports and Q5 display file;
the legacy teaching-data exporter need not be rerun for this refresh. No cluster
job, campaign, regression run, probe manifest, staging, commit or other Git
operation was performed.
