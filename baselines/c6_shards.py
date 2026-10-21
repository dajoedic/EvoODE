"""Deterministic C-6 platform plan; dimensions 1/2 precede dimensions 3/4."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from baselines.noise_execution import cell_key, unit_key, digest

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = {"odeformer": ROOT / "baselines/configs/odeformer_grid.json",
           "pysr": ROOT / "baselines/configs/pysr_faithful.json"}
N_SHARDS = {"odeformer": 1512, "pysr": 4536}


def ordered_index(frame):
    frame = frame.copy()
    if not frame["dimension"].isin([1, 2, 3, 4]).all():
        raise ValueError("Only dimensions 1 through 4 are supported")
    frame["_dimension_band"] = (frame["dimension"] > 2).astype(int)
    return frame.sort_values(["_dimension_band", "system_id", "initial_condition_set", "noise_sigma",
                              "subsample_rho", "noise_realization"], kind="stable").drop(columns="_dimension_band").reset_index(drop=True)


def assign_shards(frame, n_shards):
    frame = ordered_index(frame)
    if not 1 <= n_shards <= len(frame):
        raise ValueError("Shard count must be between one and the cell count")
    low = frame[frame.dimension <= 2]
    high = frame[frame.dimension > 2]
    if low.empty or high.empty or n_shards == 1:
        groups = [(frame, n_shards)]
    else:
        low_count = min(len(low), n_shards - 1, math.ceil(n_shards * len(low) / len(frame)))
        low_count = max(low_count, n_shards - len(high))
        groups = [(low, low_count), (high, n_shards - low_count)]
    parts = []
    shard_id = 0
    for group, count in groups:
        for positions in np.array_split(np.arange(len(group)), count):
            part = group.iloc[positions].copy()
            part["shard_index"] = shard_id
            parts.append(part)
            shard_id += 1
    import pandas as pd
    return pd.concat(parts, ignore_index=True)


def smoke_index(frame, method):
    rows = frame[(frame.system_id == 1) & (frame.initial_condition_set == 1) & (frame.noise_realization == 1)]
    conditions = [(0.0, 0.0), (0.05, 0.5)] if method == "odeformer" else [(0.01, 0.0)]
    selected = []
    for sigma, rho in conditions:
        match = rows[np.isclose(rows.noise_sigma, sigma, rtol=0, atol=1e-14) &
                     np.isclose(rows.subsample_rho, rho, rtol=0, atol=1e-14)]
        if len(match) != 1:
            raise ValueError(f"Expected exactly one smoke cell for {(sigma, rho)}, found {len(match)}")
        selected.append(match)
    import pandas as pd
    return pd.concat(selected, ignore_index=True)


def configurations(method, config_path=None, smoke=False):
    path = Path(config_path or CONFIGS[method])
    config = json.loads(path.read_text(encoding="utf-8"))
    if method == "odeformer":
        configs = [json.loads((ROOT / p).read_text(encoding="utf-8")) for p in config["odeformer_configs"]]
        for item in configs:
            item["environment_id"] = "reference"
        if smoke:
            configs = [item for item in configs if item["config_id"] == "beam10_noopt"]
        labels = [item["config_id"] for item in configs]
    else:
        labels = ["pysr", "pysr_poly"]
        configs = [config["pysr"]]
    if not labels or len(labels) != len(set(labels)):
        raise ValueError("Invalid configuration labels")
    repetitions = [1] if smoke else [1, 2, 3]
    return labels, repetitions, dict(config=config, method_configs=configs)


def expected_units(frame, method, config_path=None, smoke=False):
    labels, repetitions, _ = configurations(method, config_path, smoke)
    return {unit_key(row, label, repetition): row for _, row in frame.iterrows()
            for repetition in repetitions for label in labels}


def context_id(frame, method, n_shards, git_commit, image_id, config_path=None, smoke=False):
    _, _, settings = configurations(method, config_path, smoke)
    # Include the source index's semantic content, independent of platform path spellings.
    columns = [name for name in frame.columns if name not in {"cell_dir", "time_path", "state_path", "shard_index"}]
    semantic_index = json.loads(frame[columns].to_json(orient="records", double_precision=15))
    return digest(dict(method=method, n_shards=n_shards, git_commit=git_commit, image_id=image_id,
                       settings=settings, smoke=smoke, index=semantic_index))
