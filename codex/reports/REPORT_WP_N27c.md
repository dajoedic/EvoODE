# REPORT WP-N27c

## Changes

- `baselines/Dockerfile.odeformer-reference` and `baselines/Dockerfile.odeformer-candidate` now clone the pinned ODEFormer upstream commit `c9193012ad07a97186290b98d8290d1a177f4609` to `/opt/odeformer-src`, set `ODEFORMER_SOURCE_ROOT=/opt/odeformer-src`, and verify `param_optimizer.py` against LF-normalized SHA-256 `31e4a6cabf2b180118c6ee47286a537968720710b420c1dc17bc8d670ceb0bea` during image build.
- `baselines/harness.py` now records `odeformer_source_root`, `odeformer_source_root_source`, and `odeformer_param_optimizer_normalized_sha256` in ODEFormer records via schema defaults.
- ODEFormer constant optimization imports now use `ODEFORMER_SOURCE_ROOT` when set and fall back to `outputs/third_party/odeformer` otherwise.
- Missing `param_optimizer.py`, hash mismatch, or any `ImportError` in the constant-optimization import path raises `ODEFormerInfrastructureError` and aborts the run instead of writing `error_unoptimized_expression_retained`.
- Non-import optimizer exceptions still produce an ODEFormer record with `odeformer_optimization_status = error_unoptimized_expression_retained`.
- `baselines/run_odeformer_grid.py` preflights `param_optimizer` once before the first cell whenever selected configs include constant optimization. `run_odeformer_grid_k8s.py` reaches the same check through `run()`.
- `SCRIPTS.md` now states that the Orion smoke must include at least one `_opt` config and check `odeformer_optimization_status`.

## Nachtrag 2026-09-26 00:45

- The originally specified hash `5f73e0dff443bf7ab8d065a074c7279a30ceec53111456b72576d64f510e5328` was the Windows CRLF working-tree hash.
- The canonical comparison now normalizes CRLF to LF before hashing and compares against `31e4a6cabf2b180118c6ee47286a537968720710b420c1dc17bc8d670ceb0bea`.
- The Dockerfile checks and `harness.py` runtime check use the same normalized hash. The record field is `odeformer_param_optimizer_normalized_sha256`.
- Regression tests cover LF/CRLF equivalence and changed source content aborting with `ODEFormerInfrastructureError`.

## Acceptance checks run locally

```text
python -m pytest baselines/tests/test_harness.py -q
35 passed, 5 skipped in 10.53s
```

```text
python -m pytest baselines/tests -q
35 passed, 5 skipped in 12.19s
```

The skipped tests are the existing POSIX fork tests skipped on Windows.

## Docker commands for Claude

Reference image build:

```bash
docker build \
  -f baselines/Dockerfile.odeformer-reference \
  -t evoode/odeformer-reference:wp-n27c \
  .
```

Candidate image build:

```bash
docker build \
  -f baselines/Dockerfile.odeformer-candidate \
  -t evoode/odeformer-candidate:wp-n27c \
  .
```

Import check for a built image:

```bash
docker run --rm evoode/odeformer-reference:wp-n27c python - <<'PY'
import hashlib
import os
import sys
from pathlib import Path

source_root = Path(os.environ["ODEFORMER_SOURCE_ROOT"])
sys.path.insert(0, str(source_root))
import param_optimizer  # noqa: F401

target = source_root / "param_optimizer.py"
print("param_optimizer_import=ok")
print(f"odeformer_source_root={source_root}")
print(f"param_optimizer_normalized_sha256={hashlib.sha256(target.read_bytes().replace(b'\r\n', b'\n')).hexdigest()}")
PY
```

Expected normalized SHA-256 in the import check: `31e4a6cabf2b180118c6ee47286a537968720710b420c1dc17bc8d670ceb0bea`.
