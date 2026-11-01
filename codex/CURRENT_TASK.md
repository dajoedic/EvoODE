# WP-FA9 — Q8: variant C, coefficient bound, surrogate paths, ablations; fit inputs, manifests, aggregation
**Language: Julia** (runner and optimizer option; the path builder and aggregation parts are Python)

Stand 2026-11-02. Authority: `docs/sideproject_residual_growth_protocol_q8.md` (frozen 2026-11-02 at gate G1; read it
in full, including §10). Builds on WP-FA5 (Q5 runner `studies/regression/sideproject_q5_noise_fits.jl`, Q5 path
builder, `aggregate_sideproject_q5.py`), WP-FA7 (Q6 `growth_path_with_end`) and WP-FA8 (Q7 path builder
`build_sideproject_q7_paths.py`, `aggregate_sideproject_q7.py`, `k8s/sideproject_q7_job.yaml`). Read those reports
(`codex/reports/REPORT_WP_FA5.md`, `_FA7.md`, `_FA8.md`) before you start.

Codex cannot execute Julia here (`codex/CODEX_PROTOCOL.md`). Write the Julia parts, argue their correctness from the
code, and state the exact parse and smoke commands for Claude. Report `done` when everything else is in place.

## Scope

1. **Variant C (initial state estimated) as an option of the fit, behaviour-neutral by default.**
   The initial state of every simulation inside the fit is today the first row of the supplied trajectory
   (`src/optimize/bfgs.jl:174`). Variant C adds d free initial-state parameters (d = state dimension), started at the
   first observed sample, **unbounded**, fitted jointly with the coefficients in the same single `fit_parameters`
   call; the coefficient clamp (`clamp_val`, `bfgs.jl:178`, `:354`, `:676`) applies to the coefficients only, never to
   the initial-state parameters. Choose the least invasive design (an option of the optimizer or of `fit_parameters`,
   or a Q8-side wrapper) and justify it. Hard requirements:
   - With the option off, every existing call path is **bit-identical** (Q4, Q5, Q7 records, Phase C, C-6). Audit
     every place that hashes optimizer settings (`settings_fingerprint` in the Q4/Q5 runners, `config_fingerprint`,
     Phase C identity) and show that the default leaves each hash unchanged; if a new struct field would enter a
     hash, change the design, not the hash.
   - With the option on and the initial-state parameters held fixed at the first observed sample, the result equals
     variant A bit-identically (this is the protocol §8 control; provide a way to run it).
   - The fitted initial state is returned and recorded per candidate.
2. **Q8 runner** `studies/regression/sideproject_q8_fits.jl`: includes the Q5 runner's machinery unchanged (do not edit
   `sideproject_q5_noise_fits.jl` or `sideproject_q4_path_fits.jl`; their SHA-256 are asserted by tests). Settings per
   run: `ic_mode` (first_sample | estimated), `coefficient_bound` (10 | 1000), `start` (weak | random — random =
   `0.1·randn` per candidate from a seed derived deterministically from cell and candidate ID, one attempt),
   `refit` (true | false — false simulates the weak-form coefficients directly, no optimizer call; under false the
   initial state is the first observed sample and the coefficients are clamped to the arm's bound: state both as
   declared consequences in the report). All four settings and the arm name enter the record and its settings
   fingerprint. Evaluation exactly as Q5: reconstruction and generalization from the clean IC on the clean grid; in
   addition for variant C the training MSE from the estimated initial state and the distance estimated vs clean IC.
   Same export reader, hash checks, resume and atomic publication as Q5.
3. **Path builder** `analysis/scripts/aggregate/build_sideproject_q8_paths.py`: the Q7 path end (import from
   `build_sideproject_q7_paths.py`, unchanged) on the Q8 cells of protocol §4 — dim 1/2 all 51 systems (21 exact,
   30 surrogate) and the dim-3 sample 52, 61, 54–59; conditions (σ, ρ) ∈ {0.01, 0.05} × {0, 0.5}, realization 1, plus
   (0, 0); both ICs. Surrogates have no true structure: no truth fields, no upper bounds, no truth-derived anything —
   check that nothing in the imported Q5/Q7 builder code silently needs the truth for them. One extra path variant for
   the **no-FoBa** ablation (forward FROLS only, otherwise identical); find the FoBa switch in the existing code, do
   not reimplement the path. Output per arm the paths file in the schema the Q8 runner reads, with:
   - **A10 on exact cells marked as reuse of Q7** (support and `p0` equal; `reuse_q7` marker as FA8 did for Q5), so
     those states are not refitted; everything else `new`.
   - Shard lists in descending planned cost; planned cost from the **measured Q5 solve times** (`fit_meta.solve_time_s`
     in the Q5 records under `outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/`), per stratum,
     with an explicit unmeasured factor ×1–2 for variant C and for 54–59 under bound 1000. Report core-h per block
     against protocol §9.
   - A **probe** list: one unit per block (dim 1/2 exact, dim 1/2 surrogate, 52/61, 54–59, ablations), chosen by the
     same upper-middle-order-statistic rule as Q5's probe, all arms of that block.
4. **Inputs on NFS.** The Q5 staging covered only exact systems; Q8 needs the surrogate cells and 54–59 of the C-6
   export. Produce the staging inventory (local path → NFS path → SHA-256) and **one tarball** of all binaries not
   already staged under `sideproject_q5_354106398…/input/export/` (many small files over VPN take hours). Do not copy
   anything to `S:`; Claude does it.
5. **Manifests** `k8s/sideproject_q8_probe_job.yaml` and `k8s/sideproject_q8_job.yaml`: copies of the Q7 job pattern,
   image placeholder `<COMMIT_SHA>` (the image must be rebuilt because of scope 1/2), new NFS directory
   `sideproject_q8_<COMMIT_SHA>/`, the export directory of Q5 plus the new tarball's unpack location, parallelism 16,
   no deadline, same resources. One indexed shard = one (cell, arm).
6. **Aggregation** `analysis/scripts/aggregate/aggregate_sideproject_q8.py`: per arm × stratum × σ (pooled over ρ and
   per ρ) the protocol §6 metrics — exact systems structure and R², surrogates R² only, never mixed; the §7 rules in
   the frozen order (R2, then R1 at the adopted bound; decided on dim 1/2 only; dim 3 reported); R3 against the best
   of the four references (WP-N47 SINDy / Weak-SINDy / E-SINDy, matching library, better threshold as in Q5; WSINDy
   port W1 on ρ = 0 and W1-interp on ρ = 0.5, from `outputs/sideproject_q5w_wsindy/full/details.csv` and
   `w1_interp_full/details.csv`, marked preliminary); the ablations beside C1000; the §8 controls; cost. Import the
   Q5/Q7 selection and reporting, do not duplicate. Refuses incomplete inputs; refuses to overwrite. Tests on synthetic
   fixtures only.
7. **Fix in `aggregate_sideproject_q5.py` (found 2026-11-01).** `report_tables` drops the clean (0, 0) cells from the
   Q5 rows but not from the references, so the (σ = 0, ρ = 0.5) group fails the count check ("Incomplete matching
   baseline configuration"); the probe had no such condition. Claude ran the official Q5 aggregation through a wrapper
   that drops them from the references too (`DIARY.md` 2026-11-01). Fix it in the script so the result equals the
   wrapper's: the committed tables under `analysis/data/sideproject_residual_growth/q5_grid/` must come out
   **byte-identical** (except run metadata fields that name files or times) when rerun into a fresh directory. The
   frozen-input hash check against the protocol file also failed, because the Q5 protocol received the 2026-10-28
   execution amendment (`ecc8bac`, pure 10-line addition) after the paths were built; the wrapper hashed the version
   at `f454a32`. Give the script a documented way to verify a frozen input against a named commit, used only for that
   file. Check whether `aggregate_sideproject_q7.py` inherits either defect and fix it there too.

## Verboten

- Running any fit, Julia, cluster job, git operation, or copying to `S:`; anything over 15 minutes; built-in timeouts
  in scripts.
- Changing the Q4/Q5 runners, the Q5/Q6/Q7 builders, any frozen protocol, Q5/Q7 inputs or records, the committed
  Q5 tables.
- Reporting any rate, structure hit, R² or comparison from real data (technical counts allowed: cells, states, shards,
  planned core-h).
- Touching the uncommitted WP-N48b files: `analysis/scripts/aggregate/aggregate_c6_symbolic_baselines.py`,
  `analysis/scripts/aggregate/run_k8s_symbolic_shard.py`, `baselines/c6_shards.py`,
  `baselines/tests/test_c6_symbolic_execution.py`, `codex/reports/REPORT_WP_N48.md`, `k8s/phase_c_c6_pysr*.yaml`.

## Abnahme

- Scope 1: the behaviour-neutral design argued from the code, every settings hash audited; the commands for Claude:
  `Meta.parseall` of every changed Julia file, a laptop smoke that reruns one Q5 clean cell and one Q5 noisy dim-2 cell
  with the defaults and compares to the existing records bit-identically, and the variant-C-fixed-IC control on the
  same cells (each < 10 min).
- Scopes 3–6: builder determinism (two runs identical), A10 reuse control, surrogate paths built without truth,
  cell/state/shard counts and planned core-h per block, staging inventory and tarball, manifests, aggregation tested
  on fixtures.
- Scope 7: the rerun of the Q5 aggregation into a scratch directory reproduces the committed tables byte-identically
  (you may run this Python aggregation; it reads local files only).
- Focused tests only; the full test run must stay under 15 minutes.
- Report `codex/reports/REPORT_WP_FA9.md`; `codex/STATUS.md` as `CODEX_PROTOCOL.md` prescribes.
