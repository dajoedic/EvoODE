"""Prepare the B-02 Phase-C oracle input history."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("outputs/phase_c_campaign_221a3a7/history.jsonl")
DEFAULT_SUPPORT = Path("studies/regression/phase_c_support.json")
DEFAULT_OUTPUT = Path("outputs/phase_c_c8_oracle_b02_input/history.jsonl")
EXPECTED_RECORDS = 126


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("error") is not None:
                raise SystemExit(f"{path}:{line_no}: input record has error={record.get('error')!r}")
            records.append(record)
    return records


def exact_dim12_systems(path: Path) -> set[int]:
    with path.open("r", encoding="utf-8") as handle:
        support = json.load(handle)
    systems = {
        int(system["system_id"])
        for system in support["systems"]
        if system.get("representability") == "exact" and int(system["dim"]) <= 2
    }
    if len(systems) != 21:
        raise SystemExit(f"Expected 21 exact dim<=2 systems in {path}, got {len(systems)}")
    return systems


def cell_key(record: dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(record["system_id"]),
        int(record["initial_condition_set"]),
        int(record["seed"]),
    )


def filter_records(records: list[dict[str, Any]], systems: set[int]) -> list[dict[str, Any]]:
    selected = [
        record
        for record in records
        if int(record.get("system_id", -1)) in systems
        and record.get("variant") == "evogrow_v2_2_stage_capped"
        and record.get("condition") == "capped"
        and record.get("basis_name") == "staged_polynomial_basis_with_constant"
        and record.get("representability") == "exact"
        and float(record.get("noise_sigma", 0.0)) == 0.0
        and float(record.get("subsample_rho", 0.0)) == 0.0
        and int(record.get("noise_realization", 0)) == 0
        and float(record.get("clamp_val", 10.0)) == 10.0
    ]
    selected.sort(key=cell_key)
    keys = [cell_key(record) for record in selected]
    duplicate_count = len(keys) - len(set(keys))
    if duplicate_count:
        raise SystemExit(f"Selected records contain {duplicate_count} duplicate cell keys")
    return selected


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with path.open("wb") as handle:
        for record in records:
            line = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
            handle.write(line)
            digest.update(line)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT, type=Path)
    parser.add_argument("--support", default=DEFAULT_SUPPORT, type=Path)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    parser.add_argument("--expected-records", default=EXPECTED_RECORDS, type=int)
    args = parser.parse_args()

    systems = exact_dim12_systems(args.support)
    records = filter_records(read_jsonl(args.input), systems)
    if len(records) != args.expected_records:
        raise SystemExit(f"Expected {args.expected_records} B-02 records, got {len(records)}")
    digest = write_jsonl(args.output, records)
    print(f"input={args.input.as_posix()}")
    print(f"support={args.support.as_posix()}")
    print(f"output={args.output.as_posix()}")
    print(f"records={len(records)}")
    print(f"systems={len(systems)}")
    print(f"sha256={digest}")


if __name__ == "__main__":
    main()
