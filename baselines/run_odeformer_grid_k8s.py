import argparse
import importlib.metadata
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baselines import harness
from baselines import run_odeformer_grid


SHARDS_PER_REPETITION = 42
ENVIRONMENT_IDS = ("reference", "candidate")


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


def expected_torch_version(environment_id: str, requirements_dir: Path | None = None) -> str:
    if environment_id not in ENVIRONMENT_IDS:
        raise ValueError(f"environment_id must be one of {', '.join(ENVIRONMENT_IDS)}")
    base = requirements_dir or (REPO_ROOT / "baselines")
    path = base / f"requirements-odeformer-{environment_id}.txt"
    pattern = re.compile(r"^\s*torch\s*==\s*([^;\s#]+)")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1)
    raise ValueError(f"no torch== pin found in {path}")


def public_version(version: str) -> str:
    return version.split("+", 1)[0]


def assert_torch_environment(environment_id: str) -> None:
    expected = expected_torch_version(environment_id)
    try:
        observed = importlib.metadata.version("torch")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError(f"torch is not installed; expected torch=={expected} for {environment_id}") from exc
    if public_version(observed) != public_version(expected):
        raise RuntimeError(
            f"installed torch {observed} does not match {environment_id} requirement torch=={expected}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one indexed Kubernetes shard of the ODEFormer grid.")
    parser.add_argument("--config", default="baselines/configs/odeformer_grid.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--trajectory-export-dir", required=True)
    parser.add_argument("--environment-id", choices=ENVIRONMENT_IDS, default="reference")
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
    assert_torch_environment(args.environment_id)
    path = run_odeformer_grid.run(
        harness.resolve_path(args.config),
        args.output_dir,
        environment_id=args.environment_id,
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
