# WP-FA9 — Q8 implementation and technical acceptance

2026-11-02. **Status: blocked ? G-Q7 is unresolved, and the cap-fallback reference/adapter is not delivered. This is a substantive integration limitation, not the reserved Julia acceptance.**

Implementation and Python technical acceptance are complete for the
explicitly declared **Q7 significance end**. Julia was neither parsed nor run;
its acceptance commands below are reserved for Claude, as CURRENT_TASK requires.
All changes remain uncommitted. No Git operation, fit, cluster job, campaign,
copy to S:, frozen-input edit or WP-N48b edit was performed.

## Implementation

- `src/optimize/bfgs.jl`: opt-in `estimate_initial_state` and
  `fixed_initial_state` keywords on `fit_parameters`; no optimizer struct field.
- `studies/regression/sideproject_q8_fits.jl`: includes the original Q5 runner
  at top level, without invoking its main. It reuses its export/index readers,
  clean-target controls, evaluations, history reader and atomic publisher.
- `studies/regression/sideproject_q8_smoke.jl`: default/Q5-record and frozen-IC
  bit controls, including deterministic optimizer metadata except wall times.
- `analysis/scripts/aggregate/build_sideproject_q8_paths.py`: original Q6 path
  engine with imported Q7 significance end, seven arms, Q7 reuse controls,
  measured Q5 solve-time planning, probe and staging tarball.
- `analysis/scripts/aggregate/aggregate_sideproject_q8.py`: strict manifest and
  record completeness, settings/source/hash controls, Q5 candidate conversion,
  selection and reporting; separate exact/surrogate output; R2 then R1 then R3;
  preliminary WSINDy reference and ablations; cost and controls.
- `analysis/scripts/aggregate/validate_sideproject_q8_inputs.py`: standalone
  technical validation, including deterministic artifacts and every tar member.
- `k8s/sideproject_q8_job.yaml`, `k8s/sideproject_q8_probe_job.yaml`: indexed
  Jobs, respectively 3,540 and 75 completions, parallelism 16, one CPU/4Gi,
  unchanged thread settings, no deadline, rebuilt image `<COMMIT_SHA>`.
- `aggregate_sideproject_q5.py`: clean-reference filtering, the explicitly named
  historical-protocol check, legacy optimizer source verification, and an
  optional reporting metric subset whose default is unchanged.
- Tests: new `analysis/tests/test_sideproject_q8.py`; two old Q5 assertions now
  explicitly use the frozen protocol revision and the already amended 16-pod
  grid manifest. No Q5 manifest was changed.

## Fit design and default identity audit

The default `BFGSOptimizer` declaration is text-identical to its pre-FA9
version. The old source is retained at
`codex/reports/WP_FA9_bfgs_legacy.jl.txt` so existing Q5/Q7 source inventories can
still be checked against actual source bytes. This exception applies only to
`src/optimize/bfgs.jl`; all other source checks remain strict. New Q8 records
must match current sources and cannot use that historical-source exception.
The final Q5 reproduction also verifies this adapter's metadata accounting.

Default calls retain the original attempt/retry loop, p0 construction, prediction
call, clamp expressions, optimizer algorithms, stopping budgets and return tuple.
The extra keywords default to false. No random draw is added to this path.
With `estimate_initial_state=true, fixed_initial_state=true`, execution takes
that same original path: fixed variables are eliminated, rather than adding
zero-gradient coordinates to finite differences or changing BFGS dimension.

For estimated IC, one `fit_parameters` call invokes the existing single-attempt
engine on `[coefficients; first_observed_state]`. `_predict_traj` takes only the
coefficient prefix as ODE parameters and the suffix as u0. The observed targets
and actual observed times remain unchanged. Every clamp site has a corresponding
opt-in prefix-only expression: prediction, best-observed tracking and final
returned parameters. The state suffix is never clamped, including the
best-observed fallback. The joint result is split into coefficient parameters
and `fit_meta.fitted_initial_state`; Q8 records also expose the fitted state,
estimated-IC training MSE and Euclidean distance to the clean IC.

The estimated branch requires `max_fit_attempts=1`, as Q8 specifies. It reuses
all BFGS/Nelder-Mead, loss-budget and solver-statistics code. It does not introduce
an optimizer timeout. Existing time_limit_s=Inf is retained.

| Hash/identity entry point | Why its default value stays unchanged |
|---|---|
| Q4 `q4_settings` / settings_fingerprint | Same ten optimizer fields, values, types and canonical serialization |
| Q5 settings_fingerprint | Calls unchanged q4_settings; no extra setting is inserted |
| Q7 fits | Unchanged Q5 runner and settings; historical source inventories checked against archived bytes |
| `run_regression.jl:config_fingerprint` | Explicit constants/options/system payload; no keyword or source hash enters it |
| `phase_c_config.jl:phase_c_fingerprint` | Explicit coefficient bound, budgets, attempt count, variants, systems and options unchanged |
| C-6 `data_condition_fingerprint` / Phase-C identity | Data-condition constants and the Phase-C configuration tuple are unchanged |
| WP-N3/N4/N5 config fingerprint payloads | Their explicit optimizer constants/configuration and input payloads are unchanged |
| T1f optimizer identity/fingerprint | Explicit clamp_val and variant constants unchanged |

Source SHA-256 provenance necessarily changes for a new binary containing the
opt-in API; this is separate from settings/config identity. The old Q4/Q5
runners were not edited. The default fingerprint is still
`608ac81047860684035841955cf944a50f8dad6a5a6d669775d7c9b51b31fa90`.
The Python implementation of the flat settings canonical form reproduces this
actual recorded fingerprint. Each Q8 arm hashes its arm name, ic_mode,
coefficient_bound, start, refit and fixed-IC control flag in addition to the
original optimizer settings. Aggregation recomputes that fingerprint.

Random starts use a local MersenneTwister seeded from the first 15 hex digits of
SHA256(`Q8:start:<cell_id>:<candidate_id>`), and exactly `0.1*randn` per coefficient.
One attempt is used. No-refit directly clamps weak coefficients to the arm's
bound and simulates them: **its IC is the first observed sample even though its
parent arm is C1000; it makes zero optimizer calls**. These are declared
consequences, not estimated-IC fits. Simulation cost for no-refit is unmeasured
and omitted from the fit-solve planning numbers below.

Training/selection for C uses predictions from its fitted IC against all
unchanged observed samples. Reconstruction/generalization remain Q5 clean-grid,
clean-IC evaluations. Imported Q5 size rules (a), (b), (c), ties and sentinel
semantics remain unchanged. Adding d to every candidate's trajectory BIC penalty
is constant within a cell and therefore leaves its ranking unchanged.

## Paths, scope, gate and FoBa

Both complete runs were explicitly invoked with `--path-end q7`. They do not
infer or declare G-Q7. The local DIARY/CLAUDE plan still describes G-Q7 as pending;
production use of these artifacts is conditional on adoption of the Q7 end.
Surrogates always use Q7 significance, as the protocol requires.

The builder also accepts `cap6`, but refuses A10 reuse if its paths do not match
the available Q7 manifest. In particular, the present significance-ended Q7
manifest is not silently relabelled as capped. **A failed G-Q7 needs a matching
adopted capped-Q7 reference artifact/adapter before publishing a fallback Q8
input set. The delivered and validated artifacts cover the Q7-adopted branch.**
This is an explicit integration limitation; no gate decision or scientific
result was manufactured to bypass it.

No existing public FoBa switch exists: `growth_path_with_end` has a literal
`cost < .5*gain` test inside its backward loop. To preserve the frozen Q6/Q7
files and avoid reimplementing the path, Q8 compiles the imported function's AST
with only that uniquely identified innermost loop's test replaced by False.
It fails if that loop layout changes. All forward arithmetic, significance,
numerical-zero/no-gain/full/cycle stops and candidate construction are imported.
A synthetic correlated-decoy test verifies that this path retains the decoy
which the ordinary FoBa path removes.

Surrogates never call Q5's `build_cell`: that function requires a true-size
upper candidate. Q8 instead calls the original observation reader, basis/design,
noise operators, significance closure, growth engine and candidate constructor
directly. Only system ID, dimension and representability are taken from the
support inventory. No surrogate support, true size, true coefficient, oracle or
upper subset is read or derived. `upper_candidates` is an empty schema field.
All 590 observation hashes match WP-N47 (technical-only join).

| Block | Cell-arms | States | New shards | Planned core-h low–high |
|---|---:|---:|---:|---:|
| dim 1/2 exact | 840 | 4,392 | 630 | 22.378–37.296 |
| dim 1/2 surrogate | 1,200 | 13,412 | 1,200 | 110.734–166.102 |
| 52/61 | 80 | 1,252 | 60 | 194.082–323.471 |
| 54–59 | 120 | 2,510 | 120 | 518.793–1,556.380 |
| ablations | 1,530 | 12,624 | 1,530 | 63.981–127.962 |
| total | 3,770 | 34,190 | 3,540 | 909.969–2,211.211 |

There are 590 source cells, 230 reused A10 cell-arms, 1,411 reused states and
32,779 new candidate evaluations. Of those new evaluations, 4,451 belong to
no-refit; hence **28,328 optimizer calls** are planned. Empty candidate paths
remain in the cell scope and selection denominators.

Planning reads exactly 1,632 Q5 `index_*.jsonl` files, excluding the probe.
It sums `fit_meta.solve_time_s` and divides by candidate count within dimension:
6,030 / 10,669 / 3,440 / 2,743 records for dim 1 / 2 / 3 / 4. Only dim 1–3 means
are used. Surrogates use their dimension's measured exact-system mean as an
explicit proxy; 54–59 use the feasible dim-3 mean as a proxy. The upper factor
is x2 for estimated-IC refits and independently x2 for 54–59 under bound 1000,
so their combined upper factor is x4. All factors are unmeasured.

Against protocol §9, dim 1/2 totals 133.112–203.398 core-h (protocol 60–300),
dim 3 totals 712.876–1,879.850 (600–1,700), and ablations 63.981–127.962
(30–150). The combined upper estimate exceeds the protocol's ~2,150 core-h;
no factor was adjusted to force agreement. These are solve-time planning proxies,
not measured Q8 runtimes; no-refit simulation/JIT/startup cost is additional.

Probe units are upper-middle order statistics of summed planned upper cost over
the block, with unit-ID tie breaks. Every applicable new arm and all five
conditions of each chosen unit are included; A10 exact states are already reused.
The 75 new probe shards use sys0006_ic1 (exact), sys0044_ic2 (surrogate),
sys0052_ic1 (52/61), sys0058_ic2 (54–59), sys0029_ic1 (ablations).
Grid and probe lists are descending upper planned cost, then shard ID.

## Artifacts and staging

Final artifacts: `outputs/sideproject_q8_inputs/grid/`; independent repeat:
`outputs/sideproject_q8_inputs/repeat/`. **All 15 files are byte-identical**,
including seven per-arm paths files, full/new/probe manifests, two shard lists,
technical summary, staging CSV and tarball. Hashes/lengths and controls are in
`outputs/sideproject_q8_inputs/validation.json`.

`grid/staging.csv` contains 1,181 local → mounted NFS path → SHA256 entries:
460 already staged binaries, 720 additional binaries and the unchanged full index.
`grid/q8_export_additions.tar` contains only the 720 new binaries plus index.csv,
with deterministic headers, 5,939,200 bytes, SHA256
`46d601c577302ce9e64f3fa75da466f64f0c346fd6d6e0e2cbe2a3d47cc0830f`.
Every member's digest and exact inventory were independently validated.

Claude stages the required JSON/shard inputs from grid into
`/outputs/sideproject_q8_<COMMIT_SHA>/input/` and unpacks that single tarball into
`input/export_additions/`. Existing binaries remain at
`/outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/input/export/`.
These mounted paths correspond to NFS `/bigdata/data-science/joedicke/`.
No file was uploaded or copied to S:. The rebuilt image and every Q8 directory
placeholder must use the same chosen commit. Probe and grid outputs have distinct
filenames and different paths-manifest hashes; never merge probe records as grid.

## Aggregation and field audit

The Q8 adapter imports Q5 candidate conversion, selection and report_tables;
Q7 record joins, expected-key checks and WSINDy reporting are imported too.
No optimizer or model-selection algorithm is duplicated. Exact and surrogate
strata are separate; surrogate output contains trajectory metrics only. No
truth support is supplied for a surrogate candidate. Clean cells are controls,
not rate/adoption rows. R2 is evaluated first, R1 once at its adopted bound,
then R3 on the adopted arm against the best of all four references. Only noisy
dim-1/2 cells decide; dim 3 is reported. The exact 5 pp test uses integer counts.
WP-N47 matching-library thresholds are chosen by the imported Q5 rule, per
stratum x sigma x metric; WSINDy uses L-Q5, W1 on rho=0 and W1-interp on rho=.5,
and is marked preliminary. Ablations are displayed beside C1000.

Completeness checks cover cell/arm scope, duplicate cells/candidates/records,
Q8 provenance and source inventories, hashes, settings and IC dimension,
WP-N47 hashes, both WSINDy libraries, and Q7 support/p0/candidate-list reuse.
The aggregator refuses an existing output directory and requires passed,
source-bound Julia smoke controls before writing. Bound-10/1000 support equality
on the smoke cells is reported informationally and is not required to pass.

| Fields | Provenance checked against actual files |
|---|---|
| cell/unit/system/IC/dimension/sigma/rho/realization/export | Existing Q5 cell and C-6 index fields |
| observed_data_sha256 | Existing data_sha of actual time/state raw hashes, not an index column |
| candidate_id, active_idxs, p0, k, equations, weak_bic, step, origin | Imported candidate constructor; original Q5/Q7 manifests |
| params, pruning, optimizer_loss, training/reconstruction/generalization, fit_meta | Actual Q5 record inventory; Q8 preserves the nested schemas |
| arm, ic_mode, coefficient_bound, start, refit | New Q8 manifest and record fields |
| fitted_initial_state, estimated_ic_training_mse, estimated_clean_ic_distance | New Q8 per-candidate result fields |
| reuse_q7, reuse_q7_candidate_id, shard_id, planned costs | New Q8 manifest/analysis metadata |
| selection, structure on exact cells, R2 flags, adoption and costs | Analysis pipeline, never assumed record-level success fields |
| WP-N47 and Q5-W columns | Actual details.csv headers; fixture metrics are explicitly replaced by synthetic values |

## Executed verification

Final focused command:

```powershell
python -m pytest analysis/tests/test_sideproject_q8.py analysis/tests/test_sideproject_q7.py analysis/tests/test_sideproject_q5.py -q -p no:cacheprovider -W ignore::DeprecationWarning --tb=short
```

**59 passed in 39.67 s**; `codex/reports/WP_FA9_pytest.log`.
Aggregation tests use fixtures derived from a real Q5 record's field inventory,
with scientific values explicitly replaced. Tests include empty paths, estimated
training selection, surrogate absence of truth outputs, clean-reference filtering,
WSINDy rho/library coverage, all four adoption outcomes and exact margin equality,
missing references/records, duplicates, wrong hashes/settings, stale smoke,
no overwrite, FoBa removal, complete cell/arm scope, manifests and shard order.
Six changed/new Python files passed AST parsing. The separate technical validator
passed full real-input scope, Q7 reuse, 15 byte comparisons and tar validation.
No real-data rate, structure hit, R2 or scientific comparison is reported here.

Both complete technical builds used:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
python analysis/scripts/aggregate/build_sideproject_q8_paths.py --path-end q7 --workers 4 --output outputs/sideproject_q8_inputs/grid
python analysis/scripts/aggregate/build_sideproject_q8_paths.py --path-end q7 --workers 4 --output outputs/sideproject_q8_inputs/repeat
python analysis/scripts/aggregate/validate_sideproject_q8_inputs.py
```

Each build completed in less than 15 minutes. No script contains a new timeout.
An initial Q5 reproduction had loaded the earlier aggregator before the optimizer
source adapter was added and rejected the modified source. This failed attempt
is preserved in `outputs/sideproject_q8_inputs/q5_initial_attempt.log`; it is not
used as acceptance evidence. Early test failures exposed an old manifest
parallelism assertion and the need to opt into the historical protocol revision;
the final command above ran after their corrections.

## Q5 reproduction — final source version

Only `docs/sideproject_residual_growth_protocol_q5.md` can use
`--q5-protocol-commit f454a32`. The script reconstructs that known revision by
removing only its marked execution amendment, then requires the exact manifest
SHA256. Unknown revisions and every unrelated hash mismatch fail. No Git command
is used. Without that explicit option, the current changed protocol is rejected.
Q7 already verifies the same historical blob without Git; its imported
report_tables inherits the clean-reference fix, so no Q7 source edit was needed.

Executed after the final code changes:

```powershell
python analysis/scripts/aggregate/aggregate_sideproject_q5.py --input 'outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/index_*.jsonl' --output-dir outputs/sideproject_q8_inputs/q5_reproduction_final --q5-protocol-commit f454a32
```

All four committed CSV tables reproduce byte-identically. Parsed run metadata
also has **zero differing fields**, exceeding the allowed path/time exceptions.
Evidence: `codex/reports/WP_FA9_q5_bytes.json`; complete run metadata log:
`codex/reports/WP_FA9_q5_reproduction_final.log`. The committed tables were not
changed. No Q5 scientific values are copied into this report.

## Commands for Claude — not executed here

Parse every changed Julia file with the pinned version:

```powershell
julia +1.12.6 --project=. -e 'VERSION == v"1.12.6" || error("Julia 1.12.6 required"); for f in ["src/optimize/bfgs.jl", "studies/regression/sideproject_q8_fits.jl", "studies/regression/sideproject_q8_smoke.jl"]; Meta.parseall(read(f, String)); println(f); end'
```

The laptop bit smoke uses the complete Q5 clean cell sys0009_ic2_s0_r0_n1
(six candidates including upper) and noisy dim-2 cell sys0025_ic1_s0.05_r0_n1
(13 including upper). Original Q5 measured solve totals are 1.929 and 2.239 s;
this is sizing evidence only, not a runtime guarantee. The command reruns defaults
and fixed-IC C on all 19 candidates, compares parameters, losses, pruning and
all evaluation dictionaries to existing Q5 records, then writes source-bound
`outputs/sideproject_q8_smoke/controls.json`. Intended <10 minutes:

```powershell
julia +1.12.6 --project=. studies/regression/sideproject_q8_smoke.jl
```

Actual estimated-IC short smoke, two candidate states of the same noisy dim-2
cell, also intended <10 minutes; repeat with the same output to check resume:

```powershell
julia +1.12.6 --project=. studies/regression/sideproject_q8_fits.jl --paths outputs/sideproject_q8_inputs/estimated_smoke.json --export-dir outputs/phase_c_c6_data_conditions_5dd1df8 --limit 1 --output outputs/sideproject_q8_smoke/estimated.jsonl
```

A full input invocation, for subsequent execution authorization only (not a
laptop smoke or a command run by Codex):

```powershell
julia +1.12.6 --project=. studies/regression/sideproject_q8_fits.jl --paths outputs/sideproject_q8_inputs/grid/q8_fit_paths.json --export-dir outputs/phase_c_c6_data_conditions_5dd1df8 --output outputs/sideproject_q8_fits/grid.jsonl
```

After G-Q7, image/staging, probe/grid approval and all fits are complete:

```powershell
python analysis/scripts/aggregate/aggregate_sideproject_q8.py --input 'outputs/sideproject_q8_<COMMIT_SHA>/out/index_*.jsonl' --q5-input 'outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/index_*.jsonl' --q7-input 'outputs/sideproject_q7_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/index_*.jsonl' --wsindy-input outputs/sideproject_q5w_wsindy/full/details.csv outputs/sideproject_q5w_wsindy/w1_interp_full/details.csv --output-dir analysis/data/sideproject_residual_growth/q8_grid
```

No Julia parse, numerical default/fixed-IC equivalence or estimated-IC execution
success is claimed. Static review covered top-level includes, JSON3 values and
collect conversions, Vector/Set use, nullable evaluation metrics, per-arm resume
keys/provenance, 0-based shard indices, parameter/state splitting and all clamps.
