from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_record(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                return json.loads(line)
    raise ValueError(f"No JSONL record found in {path}")


def read_manifest_row(path: Path, index: int) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if int(row["index"]) == index:
                return row
    raise ValueError(f"Manifest index {index} not found in {path}")


def comparable_manifest_payload(row: dict[str, str]) -> dict[str, str]:
    keys = [
        "campaign",
        "config_fingerprint",
        "variant",
        "condition",
        "basis_name",
        "max_fit_attempts",
        "system_id",
        "system_dim",
        "initial_condition_set",
        "seed",
        "representability",
        "noise_sigma",
        "subsample_rho",
        "noise_realization",
        "clamp_val",
    ]
    return {key: row[key] for key in keys}


def comparable_record_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "config_fingerprint": record.get("config_fingerprint"),
        "data_condition_fingerprint": record.get("data_condition_fingerprint"),
        "observed_data_sha256": record.get("observed_data_sha256"),
        "system_id": int(record.get("system_id")),
        "initial_condition_set": int(record.get("initial_condition_set")),
        "seed": int(record.get("seed")),
        "noise_sigma": float(record.get("noise_sigma")),
        "subsample_rho": float(record.get("subsample_rho")),
        "noise_realization": int(record.get("noise_realization")),
        "clamp_val": str(record.get("clamp_val")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare the C-6 grid control cell against the Stage-1 reference cell."
    )
    parser.add_argument("--grid-manifest", required=True, type=Path)
    parser.add_argument("--grid-index", required=True, type=int)
    parser.add_argument("--stage1-manifest", default=Path("outputs/stage1/s0.01_r0/manifest.csv"), type=Path)
    parser.add_argument("--stage1-index", default=1, type=int)
    parser.add_argument("--grid-record", required=True, type=Path)
    parser.add_argument("--stage1-record", default=Path("outputs/stage1/s0.01_r0/tasks/cell_000001.jsonl"), type=Path)
    args = parser.parse_args()

    grid_manifest = comparable_manifest_payload(read_manifest_row(args.grid_manifest, args.grid_index))
    stage1_manifest = comparable_manifest_payload(read_manifest_row(args.stage1_manifest, args.stage1_index))
    if grid_manifest != stage1_manifest:
        print("Manifest rows differ")
        print(json.dumps({"grid": grid_manifest, "stage1": stage1_manifest}, indent=2, sort_keys=True))
        return 1

    grid_record = comparable_record_payload(read_record(args.grid_record))
    stage1_record = comparable_record_payload(read_record(args.stage1_record))
    if grid_record != stage1_record:
        print("Record identity/hash payload differs")
        print(json.dumps({"grid": grid_record, "stage1": stage1_record}, indent=2, sort_keys=True))
        return 1

    print("C-6 control matches Stage-1 manifest row, config fingerprint, data fingerprint, and observed data hash")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
