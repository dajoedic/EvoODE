# REPORT WP-N21

## Result

Status: blocked, environment not subject. The code, Dockerfiles, configs, equivalence scripts, and local tests are in place. The remaining acceptance requires Docker builds, ODEFormer weight download, image execution, and a full OSV/Trivy package scan; Codex has no Docker and the local shell cannot reach `https://api.osv.dev/v1/querybatch` (`Invoke-RestMethod: Unable to connect to the remote server`).

## Implemented files

- `baselines/harness.py`: replaced the ODEFormer stub with an adapter and changed `git_hash()` to read `.git/HEAD` instead of invoking git.
- `baselines/configs/odeformer_odebench_eval.json`: ODEFormer evaluation config with source line evidence.
- `baselines/configs/wp_n19_smoke.json`: smoke config now carries the ODEFormer config fields.
- `baselines/Dockerfile.odeformer-reference` and `baselines/Dockerfile.odeformer-reference.dockerignore`.
- `baselines/Dockerfile.odeformer-candidate` and `baselines/Dockerfile.odeformer-candidate.dockerignore`.
- `baselines/requirements-odeformer-reference.txt`.
- `baselines/requirements-odeformer-candidate.txt`.
- `baselines/run_odeformer_equivalence.py`.
- `baselines/compare_odeformer_equivalence.py`.
- `baselines/tests/conftest.py` and extended `baselines/tests/test_harness.py`.

## ODEFormer adapter

`run_odeformer_record` is implemented in `baselines/harness.py:377-459`.

Local behavior without ODEFormer:

- Returns a clean error record.
- Keeps reconstruction and generalization R2 aggregations at zero.
- Writes ODEFormer schema fields including expression, canonical expression, constants, config values, candidate count, weight hash, and non-evidence elapsed time.

Image behavior when ODEFormer and weights exist:

- Sets `random`, `numpy`, and `torch` seeds to `2023`.
- Calls `torch.set_num_threads(1)`.
- Verifies the configured weight SHA-256 before inference.
- Sets `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1` because ODEFormer calls `torch.load(model_path)` without a `weights_only` argument.
- Temporarily changes working directory to the weight file directory so upstream `load_pretrained()` finds `odeformer.pt` without patching or monkeypatching ODEFormer.
- Fits on the fit cell, integrates reconstruction from the same initial condition, and integrates generalization from the other initial condition.
- Stores the raw ODEFormer expression, a SymPy canonical string, numeric constants extracted from the canonical expression, both R2 aggregations, and threshold flags.

Full unpickling is intentionally enabled only after hash verification. The model pickle is treated as trusted because the image build and runtime adapter both check the fixed SHA-256 before use.

## ODEFormer source evidence

- Weight download and `torch.load(model_path)`: `outputs/third_party/odeformer/odeformer/model/sklearn_wrapper.py:58-69`.
- `SymbolicTransformerRegressor` constructor defaults: `outputs/third_party/odeformer/odeformer/model/sklearn_wrapper.py:32-41`.
- Fit input permutation and candidate sorting: `outputs/third_party/odeformer/odeformer/model/sklearn_wrapper.py:132-177`.
- Prediction integration uses the first sorted candidate: `outputs/third_party/odeformer/odeformer/model/sklearn_wrapper.py:179-194`.
- Published evaluation setup passes `beam_size=10`, `eval_size=10000`, `batch_size_eval=16`, `min_points=10`: `outputs/third_party/odeformer/scripts/run_evaluation.py:18-26`.
- Evaluation grid includes `eval_subsample_ratio=0.5` and beam sizes `[1,10,50]`: `outputs/third_party/odeformer/scripts/run_evaluation.py:28-33`.
- Parser defaults: beam size `1`, beam type `sampling`, beam temperature `0.1`, length penalty `1`, early stopping `True`, max generated output length `200`, validation metrics, evaluation task, and rescale: `outputs/third_party/odeformer/parsers.py:271-369`.
- ODEFormer evaluation calls `model.fit(..., sort_candidates=True)` without overriding `sort_metric`, so the wrapper default `snmse` applies: `outputs/third_party/odeformer/evaluate.py:275-278` and `outputs/third_party/odeformer/odeformer/model/sklearn_wrapper.py:95-101`.
- Parameter optimization is a separate script/class, not called by `evaluate.py`: `outputs/third_party/odeformer/param_optimizer.py:21-136`. Open question for Claude: whether ODEBench paper results applied this post-step externally. The adapter records `parameter_optimization=open_question_wrapper_default_disabled` and `parameter_optimization_iterations=0`.

## Environments

Reference image:

- Python `3.9-slim`
- `torch==2.0.0`
- `sympy==1.11.1`
- `numpy==1.23.5`
- `sympytorch==0.1.1`
- ODEFormer installed from `outputs/third_party/odeformer` with `--no-deps`

Candidate image:

- Python `3.11-slim`
- `torch==2.14.0`
- `sympy==1.13.3`
- `numpy==1.23.5`
- `sympytorch==0.1.1`
- ODEFormer installed from `outputs/third_party/odeformer` with `--no-deps`

Both Dockerfiles use Harbor cache base images: `registry.scch.at/cache/library/python:<tag>`.

## Candidate vulnerability evidence

Local OSV API query from Codex failed:

```powershell
$body = @{ queries = @(@{ package = @{ name = 'torch'; ecosystem = 'PyPI' }; version = '2.14.0' }) } | ConvertTo-Json -Depth 6
Invoke-RestMethod -Uri 'https://api.osv.dev/v1/querybatch' -Method Post -Body $body -ContentType 'application/json'
```

Observed result: `Unable to connect to the remote server`.

Partial web evidence checked:

- OSV `GHSA-rrmf-rvhw-rf47` for `torch` has severity Medium/Low and fixed version `2.13.0`; affected versions stop at `2.12.1`.
- OSV `PYSEC-2024-251` for `torch` is fixed in `2.2.0`.
- OSV `PYSEC-2025-208` for `torch` is High and fixed in `2.7.1`; affected versions stop at `2.7.0`.

Full per-package acceptance is blocked until Claude runs OSV or Trivy against `baselines/requirements-odeformer-candidate.txt`. Exact command:

```bash
osv-scanner --lockfile=baselines/requirements-odeformer-candidate.txt --format=json > outputs/wp_n21_security/osv_candidate.json
```

Pass criterion: every finding for candidate runtime packages is below HIGH, or no finding exists. If `osv-scanner` cannot read plain requirements as a lockfile in Claude's environment, use:

```bash
trivy fs --scanners vuln --severity HIGH,CRITICAL --exit-code 1 --format json --output outputs/wp_n21_security/trivy_candidate.json baselines/requirements-odeformer-candidate.txt
```

Pass criterion: exit code `0` and zero HIGH/CRITICAL candidate runtime package findings.

## Equivalence rule

Implemented in `baselines/compare_odeformer_equivalence.py:9-83`.

- Canonical expression: exact string match.
- Fitted constants: `abs_tol=1e-8`, `rel_tol=1e-8`.
- Reconstruction and generalization R2 aggregations: `abs_tol=1e-8`, `rel_tol=1e-8`.

Justification before image runs: both images are CPU-only, deterministic seed-fixed runs on the same float64 exported inputs. A `1e-8` mixed absolute/relative tolerance allows small BLAS/PyTorch arithmetic differences without accepting materially different fits. Expressions remain exact because different symbolic forms are a methodological finding, not numeric noise.

## Commands for Claude

Create output folders:

```bash
mkdir -p outputs/wp_n21_reference outputs/wp_n21_candidate outputs/wp_n21_equivalence outputs/wp_n21_security
```

Build once to obtain the weight hash. Expected output: the build fails after printing `ODEFormer weights sha256: <hash>`.

```bash
docker build -f baselines/Dockerfile.odeformer-reference -t evocode/odeformer-reference:hash-probe .
```

Pass criterion: the printed hash is copied into both Dockerfiles in place of `TO_BE_FILLED_BY_CLAUDE_AFTER_FIRST_DOWNLOAD`, and the source of the hash is documented by Claude.

Build both images after replacing the placeholder:

```bash
docker build -f baselines/Dockerfile.odeformer-reference -t evocode/odeformer-reference:wp-n21 .
docker build -f baselines/Dockerfile.odeformer-candidate -t evocode/odeformer-candidate:wp-n21 .
```

Expected output: both builds finish successfully. Pass criterion: both build logs include the same `ODEFormer weights sha256: <hash>` and no hash mismatch.

Run the equivalence cell list in both images:

```bash
docker run --rm -v "$PWD/outputs:/workspace/EvoODE/outputs" evocode/odeformer-reference:wp-n21 python -m baselines.run_odeformer_equivalence --output-dir outputs/wp_n21_reference
docker run --rm -v "$PWD/outputs:/workspace/EvoODE/outputs" evocode/odeformer-candidate:wp-n21 python -m baselines.run_odeformer_equivalence --output-dir outputs/wp_n21_candidate
```

Expected output: each command prints its `records.jsonl` path. Pass criterion: each JSONL has 6 ODEFormer records for systems 1, 2, and 24 with both IC directions, all `status=success`.

Compare environments:

```bash
python -m baselines.compare_odeformer_equivalence --reference outputs/wp_n21_reference/records.jsonl --candidate outputs/wp_n21_candidate/records.jsonl --output outputs/wp_n21_equivalence/comparison.json
```

Expected output on equivalence: `{"finding_count": 0, "passed": true}`. Pass criterion: `passed=true`. If `passed=false`, the differences in `outputs/wp_n21_equivalence/comparison.json` are the finding and must not be tuned away.

Run the candidate harness smoke test:

```bash
docker run --rm -v "$PWD/outputs:/workspace/EvoODE/outputs" evocode/odeformer-candidate:wp-n21 python -m baselines.harness --config baselines/configs/wp_n19_smoke.json --output-dir outputs/wp_n21_candidate_harness_smoke
```

Expected output: path to `outputs/wp_n21_candidate_harness_smoke/records.jsonl`. Pass criterion: 12 records total, 6 SINDy and 6 ODEFormer, with ODEFormer `status=success`.

Run candidate package vulnerability check:

```bash
osv-scanner --lockfile=baselines/requirements-odeformer-candidate.txt --format=json > outputs/wp_n21_security/osv_candidate.json
```

Expected output: scanner completes. Pass criterion: no HIGH or CRITICAL findings for candidate runtime packages.

## Local tests run by Codex

```text
python -m pytest baselines/tests/test_harness.py -q
........
8 passed in 18.63s
```

```text
python -m compileall -q baselines/harness.py baselines/run_odeformer_equivalence.py baselines/compare_odeformer_equivalence.py baselines/tests/test_harness.py baselines/tests/conftest.py
```

Expected output: no output. Observed: no output.

## Open acceptance points

1. Docker builds not run: Docker unavailable to Codex.
2. ODEFormer weights not downloaded: network/Google Drive access unavailable to Codex.
3. Reference/candidate equivalence not run: depends on Docker images and weights.
4. Full candidate HIGH/CRITICAL package scan not run: OSV API unreachable from Codex shell.

## Claude's execution and review (2026-09-23)

**Corrections made before building.** ODEFormer was copied into the image from the untracked clone
under `outputs/third_party/`; both Dockerfiles now install the pinned commit from GitHub with
`--no-deps`, so the images build anywhere. `gdown` raised from 5.2.0 to 5.2.2 (CVE-2026-40491).
`eval_subsample_ratio = 0.5` was recorded but never applied — it belongs to ODEFormer's in-domain
synthetic evaluation (`scripts/run_evaluation.py:28-33`), not to ODEBench; the field now reads
`not_applied_full_512_point_trajectory`. The reference image moved from Python 3.9 to 3.10, because
the SINDy module the harness imports uses `X | None` annotations; torch 2.0.0 / sympy 1.11.1 are
unchanged, which is what the reference is for. The trajectory manifest stores Windows paths
(`cells\file.bin`); `manifest_relative_path` normalises them inside Linux containers — bytes and
hash checks unchanged. The commands above need `--entrypoint python`, because the images'
entrypoint is the harness.

**Weights.** SHA-256 `56754040be5aa92ed4767fc43ee2008faa293f87c12b643e66c7df3e1623a5e8`, downloaded
by `gdown` from Google Drive id `1L_UZ0qgrBVkRuhg5j3BQoGxlvMk_Pm1W` during the first reference build
on 2026-09-23, identical in every later build of both images.

**Equivalence: failed under the pre-registered rule — 34 findings, 0 of 6 canonical expressions
identical.** Systems 1 and 2 give the same expression form with constants differing in the third
digit; system 24 differs structurally. Diagnosis, measured, not assumed:

| Check | Result |
|---|---|
| same image, same seed, rerun | 6/6 identical, both images |
| same image, seeds 2023 / 2024 / 2025 | 6/6 identical across seeds, both images |
| reference vs candidate, same seed | 0/6 identical, for every seed |

The seed is inert: `odeformer/model/transformer.py:495` calls `torch.manual_seed(seed)` with the
default `seed=0` inside `generate`, overriding any outer seed. ODEFormer is therefore deterministic
per environment, and the difference is a genuine environment effect — torch 2.0 and 2.14 draw
different samples from the same internal seed. The R² > 0.9 counts are identical (reconstruction
6/6, generalization 3/6 in both), individual R² values move by up to 0.04.

**SINDy cannot share either image.** The harness's SINDy path uses the pysindy 2.x API
(`fit(feature_names=...)`), which is what C-4 ran with (pysindy 2.1.0). pysindy 2.1.0 requires
`numpy >= 2.0`; ODEFormer requires `numpy==1.23.5`. In both images the six SINDy records fail with
`TypeError: SINDy.fit() got an unexpected keyword argument 'feature_names'`; the six ODEFormer
records succeed. The ODEFormer images therefore run `methods: ["odeformer"]` only, and SINDy stays
in the environment C-4 used. `baselines/requirements.txt` has pinned pysindy 1.7.5 against 2.x code
since WP-N19 — the baseline image was never built, so nobody noticed.

**Open, for the user:** which environment produces the published ODEFormer numbers; beam size
(10 in `run_evaluation.py`, 50 in the README usage example); parameter optimisation on or off.
