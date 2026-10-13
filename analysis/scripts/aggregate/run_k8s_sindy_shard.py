from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.run_phasec_noise_sindy_baselines import main as noise_sindy_main  # noqa: E402


DEFAULT_CONFIG = "/workspace/EvoODE/analysis/configs/paper1_phaseC_sindy_baseline.json"


def fail(message: str) -> None:
    raise ValueError(message)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        fail(f"{name} is required")
    return value


def parse_nonnegative_int(name: str) -> int:
    value = require_env(name)
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc
    if parsed < 0:
        fail(f"{name} must be non-negative, got {parsed}")
    return parsed


def parse_positive_int(name: str) -> int:
    parsed = parse_nonnegative_int(name)
    if parsed <= 0:
        fail(f"{name} must be positive, got {parsed}")
    return parsed


def normalize_cell_dir(export_dir: Path, value: object) -> str:
    path = Path(str(value).replace("\\", "/"))
    if not path.is_absolute():
        path = export_dir / path
    return str(path.resolve())


def build_shard_index(export_dir: Path, output_dir: Path, index: int, n_shards: int) -> Path:
    source_index = export_dir / "index.csv"
    if not source_index.is_file():
        fail(f"export index does not exist: {source_index}")
    frame = pd.read_csv(source_index)
    filter_query = os.environ.get("EVO_SINDY_FILTER_QUERY", "").strip()
    if filter_query:
        frame = frame.query(filter_query).reset_index(drop=True)
    if index >= n_shards:
        fail(f"JOB_COMPLETION_INDEX {index} is outside EVO_SINDY_N_SHARDS {n_shards}")
    shard = frame.iloc[index::n_shards].copy()
    if shard.empty:
        fail(f"shard {index} of {n_shards} is empty after filtering {len(frame)} cells")
    shard["cell_dir"] = shard["cell_dir"].map(lambda value: normalize_cell_dir(export_dir, value))
    index_dir = output_dir / "shard_indexes"
    index_dir.mkdir(parents=True, exist_ok=True)
    shard_index = index_dir / f"shard_{index}.csv"
    shard.to_csv(shard_index, index=False)
    return shard_index


def main() -> int:
    try:
        index = parse_nonnegative_int("JOB_COMPLETION_INDEX")
        n_shards = parse_positive_int("EVO_SINDY_N_SHARDS")
        export_dir = Path(require_env("EVO_SINDY_EXPORT_DIR")).resolve()
        output_dir = Path(require_env("EVO_SINDY_OUTPUT_DIR")).resolve()
        config = Path(os.environ.get("EVO_SINDY_CONFIG", DEFAULT_CONFIG)).resolve()
        shard_index = build_shard_index(export_dir, output_dir, index, n_shards)
        shard_output = output_dir / f"shard_{index}"
        old_argv = sys.argv[:]
        try:
            sys.argv = [
                "run_phasec_noise_sindy_baselines.py",
                "--config",
                str(config),
                "--export-index",
                str(shard_index),
                "--output-dir",
                str(shard_output),
                "--methods",
                "sindy,weak_sindy,e_sindy",
                "--integrator",
                "dop853",
            ]
            return noise_sindy_main()
        finally:
            sys.argv = old_argv
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
