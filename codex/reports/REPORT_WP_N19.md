# WP-N19 Report

## Implemented files

- `baselines/Dockerfile`: separate Python 3.9 baseline image; `containers/Dockerfile` was not changed.
- `baselines/requirements.txt`: separate dependency pins, including `odeformer` pinned to commit `c9193012ad07a97186290b98d8290d1a177f4609`.
- `baselines/harness.py`: CLI harness for exported Phase-C trajectories.
- `baselines/configs/wp_n19_smoke.json`: smoke config for at most 3 one-dimensional systems.
- `baselines/tests/test_harness.py`: focused tests for hash abort, method error records, smoke output shape, and arithmetic vs variance-weighted R2.

## Environment

Local environment resolved by the harness:

```json
{"gdown":"not_installed","numpy":"2.2.6","pandas":"2.2.2","pysindy":"2.1.0","scikit-learn":"1.5.1","scipy":"1.13.1","sympy":"1.13.1","torch":"2.6.0"}
```

Baseline image target in `baselines/requirements.txt`:

- Python base image: `python:3.9-slim`
- `numpy==1.23.5`
- `pandas==1.5.3`
- `scipy==1.10.1`
- `sympy==1.11.1`
- `pysindy==1.7.5`
- `torch==2.0.0`
- `gdown==4.7.1`
- `scikit-learn==1.2.2`
- `git+https://github.com/sdascoli/odeformer.git@c9193012ad07a97186290b98d8290d1a177f4609`

PySR is documented but not installed because it brings its own Julia runtime.

## Methods

- `sindy`: implemented with `pysindy`, model coefficients serialized in each record.
- `odeformer`: registered with the pinned commit and Docker dependency. In the local Codex environment it writes error records because `odeformer` and `gdown` are not installed and network/Docker reconstruction was not available in this session.
- `pysr`, `proged`, `ffx`, `ellyn`: registered inactive placeholders that return explicit error records if selected.

## Outputs

Smoke command:

```text
python -m baselines.harness --config baselines/configs/wp_n19_smoke.json
```

Output:

```text
analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke/records.jsonl
analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke/records.csv
analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke/trajectory_check.csv
```

Smoke record counts:

```text
rows: 12
odeformer/error: 6
sindy/success: 6
```

The 12 records are 3 one-dimensional systems x 2 fit IC directions x 2 methods. Records contain both trajectory hashes, `reconstruction_r2_arithmetic_mean`, `reconstruction_r2_variance_weighted`, `generalization_r2_arithmetic_mean`, and `generalization_r2_variance_weighted`.

## Checks

Focused tests:

```text
python -m pytest baselines/tests/test_harness.py -q --basetemp outputs/wp_n19_pytest_tmp
```

Result:

```text
4 passed in 7.66s
```

Hash-abort probe:

```text
python -m baselines.harness --config baselines/configs/wp_n19_smoke.json --output-dir outputs/wp_n19_hash_probe --corrupt-manifest-hash
```

Result:

```text
exit code: 1
Error: hash mismatch for system_id=1, ic=1 state: expected 0000000000000000000000000000000000000000000000000000000000000000, got 0ee16225ff89698a75ca1dd4d2560af9956e8ab3b3b0058633eb0205457986e8
```

Forced method-failure probe:

```text
python -m baselines.harness --config baselines/configs/wp_n19_smoke.json --output-dir outputs/wp_n19_failure_probe --force-sindy-failure
```

Result:

```text
odeformer/error: 6
sindy/error: 6
```

Dockerfile check:

```text
git diff -- containers/Dockerfile
```

Result: no output; `containers/Dockerfile` unchanged.

## Blocker

Abnahmepunkt 1 is not fully reachable in this local Codex environment because ODEFormer cannot be installed or imported here: `odeformer` is absent, `gdown` is absent, and external reconstruction of the pinned GitHub dependency plus Google Drive weights requires the separate Docker/network path. SINDy runs and writes success records; ODEFormer writes complete error records rather than missing rows.

