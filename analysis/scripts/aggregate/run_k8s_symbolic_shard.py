"""Run one indexed ODEFormer/PySR shard, without any EvoGrow comparison joins."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for path in (ROOT, ROOT / "analysis"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from baselines.c6_shards import (CONFIGS, assign_shards, configurations, context_id, smoke_index)
from baselines.noise_execution import UnitJournal, atomic_write
from scripts.aggregate.run_phasec_noise_sindy_baselines import read_export_index


def required(name):
    value = os.environ.get(name, "").strip()
    if not value or "<" in value:
        raise ValueError(f"Set {name} to a concrete value")
    return value


def main():
    method = required("EVO_SYMBOLIC_METHOD")
    if method not in CONFIGS:
        raise ValueError("EVO_SYMBOLIC_METHOD must be odeformer or pysr")
    index = int(required("JOB_COMPLETION_INDEX"))
    n_shards = int(required("EVO_SYMBOLIC_N_SHARDS"))
    smoke = os.environ.get("EVO_SYMBOLIC_SMOKE", "0") == "1"
    git_commit, image_id = required("EVOODE_GIT_SHA"), required("EVOODE_IMAGE_ID")
    if len(git_commit) != 40 or any(c not in "0123456789abcdef" for c in git_commit):
        raise ValueError("EVOODE_GIT_SHA must be a full lowercase commit SHA")
    export = Path(required("EVO_SYMBOLIC_EXPORT_DIR")).resolve()
    output = Path(required("EVO_SYMBOLIC_OUTPUT_DIR")).resolve()
    config = Path(os.environ.get("EVO_SYMBOLIC_CONFIG", str(CONFIGS[method]))).resolve()
    frame = read_export_index(export / "index.csv")
    if smoke:
        frame = smoke_index(frame, method)
    mapping = assign_shards(frame, n_shards)
    if not 0 <= index < n_shards:
        raise ValueError("JOB_COMPLETION_INDEX is outside the shard range")
    shard = mapping[mapping.shard_index == index].drop(columns="shard_index").copy()
    shard["cell_dir"] = shard.cell_dir.map(lambda p: str((export / str(p).replace("\\", "/")).resolve()))
    shard_output = output / f"shard_{index}"
    context = context_id(frame, method, n_shards, git_commit, image_id, config, smoke)
    journal = UnitJournal(shard_output, context, git_commit, image_id)
    plan_path = shard_output / "plan.json"
    if plan_path.exists() and json.loads(plan_path.read_text(encoding="utf-8"))["context"] != context:
        raise ValueError(f"Existing shard plan changed: {plan_path}")
    # Every pod writes exclusively inside its own shard directory.
    atomic_write(shard_output / "assignment.csv", mapping[mapping.shard_index == index].to_csv(index=False).encode())
    index_path = shard_output / "index.csv"
    atomic_write(index_path, shard.to_csv(index=False).encode())
    atomic_write(shard_output / "plan.json", (json.dumps(dict(context=context, method=method, n_shards=n_shards,
                 shard_index=index, smoke=smoke, git_commit=git_commit, image_id=image_id), sort_keys=True) + "\n").encode())
    labels, repetitions, _ = configurations(method, config, smoke)
    if method == "odeformer":
        from baselines.run_odeformer_noise import run_noise_odeformer
        paths = run_noise_odeformer(config, [index_path], shard_output, repetitions=len(repetitions),
                                   config_ids=set(labels), execution=journal)
    else:
        from baselines.run_pysr_noise import run_noise_pysr
        paths = run_noise_pysr(config, [index_path], shard_output, seeds=repetitions, execution=journal)
    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
