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
EXPECTED_RECORDS_BY_DIMS = {
    (1, 2): 126,
    (3, 4): 54,
}


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


def parse_dims(value: str) -> tuple[int, ...]:
    dims = tuple(sorted({int(item.strip()) for item in value.split(",") if item.strip()}))
    if not dims:
        raise argparse.ArgumentTypeError("--dims must contain at least one dimension")
    return dims


def exact_systems_for_dims(path: Path, dims: tuple[int, ...]) -> set[int]:
    with path.open("r", encoding="utf-8") as handle:
        support = json.load(handle)
    systems = {
        int(system["system_id"])
        for system in support["systems"]
        if system.get("representability") == "exact" and int(system["dim"]) in dims
    }
    expected_systems = 21 if dims == (1, 2) else 9 if dims == (3, 4) else None
    if expected_systems is not None and len(systems) != expected_systems:
        raise SystemExit(f"Expected {expected_systems} exact dim {dims} systems in {path}, got {len(systems)}")
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
    parser.add_argument("--dims", default=(1, 2), type=parse_dims)
    parser.add_argument("--expected-records", default=None, type=int)
    args = parser.parse_args()

    systems = exact_systems_for_dims(args.support, args.dims)
    records = filter_records(read_jsonl(args.input), systems)
    expected_records = args.expected_records
    if expected_records is None:
        expected_records = EXPECTED_RECORDS_BY_DIMS.get(args.dims, len(systems) * 3 * 2)
    if len(records) != expected_records:
        raise SystemExit(f"Expected {expected_records} oracle input records, got {len(records)}")
    digest = write_jsonl(args.output, records)
    print(f"input={args.input.as_posix()}")
    print(f"support={args.support.as_posix()}")
    print(f"output={args.output.as_posix()}")
    print(f"dims={','.join(str(dim) for dim in args.dims)}")
    print(f"records={len(records)}")
    print(f"systems={len(systems)}")
    print(f"sha256={digest}")


if __name__ == "__main__":
    main()
