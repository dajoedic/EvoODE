# REPORT WP-OB-B

## Scope

Implemented ODEBench smoke-test v2 in `experiments/annihilator_odebench_smoke/`.
No `--run` was started.

## Changes

1. Annihilator sample:
   - `_annihilator_record` now samples 2000 uniform points from `setup.json` training-domain bounds.
   - The annihilator noise is `f + eta * rms(f) * xi` with the existing per `(seed, system, method)` RNG.
   - `full_search` is called on the uniform `z`/`f` sample.
   - `basis_ivp_fhat` fits on the same 2000 uniform points.
   - Records include `annihilator_sample_points: 2000` and `sample_grid: uniform_training_domain`.

2. `STRUCT_OK`:
   - Annihilator `STRUCT_OK` is now `state == CORRECT and nrmse_f <= 0.05`.
   - Baseline `STRUCT_OK` is now `category == TRUE_STRUCTURE and nrmse_f <= 0.05`.
   - `record_struct_ok`, `evaluate_decision`, and `grouped_table` recompute from state/category and `nrmse_f`; stored `struct_ok` is ignored.

3. Version and storage:
   - Default result directory is `experiments/annihilator_odebench_smoke/results_v2/`.
   - `--setup` copies `setup.json` and `reference.json` from v1 `results/` and checks SHA256 identity.
   - Every new record includes `spec_version: 2`.
   - Evaluation aborts on any record without `spec_version == 2`.

4. Plausibility check 2:
   - `run_sanity` uses the exact reference operator on 2000 uniform points from the v2 sample path.
   - It writes `nrmse_f`, training trajectory errors, and the v3 `evaluate_class`/`test_operator` statistic `T` and critical value to `results_v2/sanity.json`.

5. Worker protocol:
   - The worker path returns elapsed seconds with the record, so parallel `run.log` entries now contain numeric `seconds` instead of `null`.
   - Log entries contain no states, categories, or equations.

6. Detached marker:
   - Added `--detach-marker`.
   - A completed `--run --detach-marker` writes `DONE` with timestamp, records written, and total records.
   - A failing `--run --detach-marker` writes `FAILED` with timestamp and traceback.

7. Tests:
   - Added/updated tests for the 2000-point uniform annihilator sample, reproducible noise, exact-only `STRUCT_OK`, stored-`struct_ok` ignoring, spec-version rejection, numeric worker seconds, and synthetic baseline record fields.
   - The record-field test no longer fits real systems 3, 7, 19, or 21.

## Test Output

Smoke tests:

```text
python -m pytest experiments/annihilator_odebench_smoke/tests --basetemp=.pytest_tmp/odebench_smoke
============================= 14 passed in 30.43s =============================
```

v3 tests:

```text
python -m pytest experiments/annihilator_gate2a_v3/tests --basetemp=.pytest_tmp/gate2a_v3
======================= 54 passed in 302.05s (0:05:02) ========================
```

Setup:

```text
python -m experiments.annihilator_odebench_smoke.run --setup
```

`results_v2/run.log` reports:

```json
{"event": "setup", "systems": 4, "seconds": 442.379283199989, "copied_hashes": {"setup.json": "b40bb386db93bc9ee4c07137818e1a89a8e2c70a53ec2cb5ef26524594f40082", "reference.json": "95b69b9ba97ff8cb94eb2c7c4ef9e0e219b4be86805fadb5bb106a4b11060e08"}}
```

Hash identity:

```text
results/setup.json     b40bb386db93bc9ee4c07137818e1a89a8e2c70a53ec2cb5ef26524594f40082
results_v2/setup.json  b40bb386db93bc9ee4c07137818e1a89a8e2c70a53ec2cb5ef26524594f40082
results/reference.json     95b69b9ba97ff8cb94eb2c7c4ef9e0e219b4be86805fadb5bb106a4b11060e08
results_v2/reference.json  95b69b9ba97ff8cb94eb2c7c4ef9e0e219b4be86805fadb5bb106a4b11060e08
```

## Sanity Numbers

`results_v2/sanity.json` top-level `passed`: `true`.

| system | sample points | NRMSE_f | train NRMSE_x | T | critical | v3 test |
|---:|---:|---:|---|---:|---:|---|
| 3 | 2000 | 2.631366894265924e-15 | [2.694374901270095e-06, 5.834018957428882e-06] | 6.757594838160302e-06 | 285.0310471275878 | passed |
| 7 | 2000 | 3.658410490720808e-12 | [2.478194035505324e-06, 1.0360086643937417e-05] | 4.481421505006875e-06 | 280.5969723525623 | passed |
| 19 | 2000 | 1.404320061343884e-12 | [5.468798048095774e-06, 9.496198564739241e-06] | 4.9370305599791494e-08 | 276.1590689351993 | passed |
| 21 | 2000 | 1.8303153446729512e-11 | [2.6517284280005766e-06, 6.3345857912172895e-06] | 6.214445996864512e-06 | 285.0310471275878 | passed |

Training reintegration:

| system | max NRMSE_x | passed |
|---:|---:|---|
| 3 | 5.838768295014274e-06 | true |
| 7 | 1.0385631862527078e-05 | true |
| 19 | 9.505100566055208e-06 | true |
| 21 | 6.3312201173321975e-06 | true |
