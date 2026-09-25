import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baselines import harness
from baselines import run_odeformer_grid


SHARDS_PER_REPETITION = 42


def completion_to_repetition_shard(index: int, shards_per_repetition: int = SHARDS_PER_REPETITION) -> tuple[int, int]:
    if index < 0:
        raise ValueError("JOB_COMPLETION_INDEX must be >= 0")
    if shards_per_repetition < 1:
        raise ValueError("shards_per_repetition must be >= 1")
    return index // shards_per_repetition + 1, index % shards_per_repetition


def read_completion_index(env_name: str = "JOB_COMPLETION_INDEX") -> int:
    value = os.environ.get(env_name)
    if value is None or value == "":
        raise ValueError(f"{env_name} is required")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{env_name} must be an integer") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one indexed Kubernetes shard of the ODEFormer reference grid.")
    parser.add_argument("--config", default="baselines/configs/odeformer_grid.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--trajectory-export-dir", required=True)
    parser.add_argument("--shards-per-repetition", type=int, default=SHARDS_PER_REPETITION)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    completion_index = read_completion_index()
    repetition, shard_index = completion_to_repetition_shard(completion_index, args.shards_per_repetition)
    if args.dry_run:
        print(f"completion_index={completion_index} repetition={repetition} shard_index={shard_index} shard_count={args.shards_per_repetition}")
        return 0
    path = run_odeformer_grid.run(
        harness.resolve_path(args.config),
        args.output_dir,
        environment_id="reference",
        limit=args.limit,
        shard_index=shard_index,
        shard_count=args.shards_per_repetition,
        repetition=repetition,
        trajectory_export_dir=args.trajectory_export_dir,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
