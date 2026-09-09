import argparse
import json
import math
from pathlib import Path
from typing import Any


DEFAULT_REFERENCE = Path("outputs/wp_n1_dim1_probe/history.jsonl")
DEFAULT_BATCH_DIR = Path("outputs/wp_n1_dim1_manifest_path_equivalence/tasks")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare WP-N1 manifest-path records against the existing dim-1 probe records."
    )
    parser.add_argument("--reference", default=str(DEFAULT_REFERENCE))
    parser.add_argument("--batch-dir", default=str(DEFAULT_BATCH_DIR))
    parser.add_argument("--indices", nargs="+", type=int, required=True)
    parser.add_argument("--loss-atol", type=float, default=0.0)
    parser.add_argument("--loss-rtol", type=float, default=0.0)
    return parser.parse_args()


def read_jsonl_record(path: Path) -> dict[str, Any]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    if len(records) != 1:
        raise ValueError(f"Expected exactly one record in {path}, found {len(records)}")
    if not isinstance(records[0], dict):
        raise ValueError(f"Expected object record in {path}")
    return records[0]


def key(record: dict[str, Any]) -> tuple[str, int, int, int]:
    return (
        str(record["variant"]),
        int(record["system_id"]),
        int(record["initial_condition_set"]),
        int(record["seed"]),
    )


def read_reference(path: Path) -> dict[tuple[str, int, int, int], dict[str, Any]]:
    records: dict[tuple[str, int, int, int], dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            record_key = key(record)
            if record_key in records:
                raise ValueError(f"Duplicate reference key {record_key} at {path}:{line_number}")
            records[record_key] = record
    return records


def compare_record(reference: dict[str, Any], candidate: dict[str, Any], loss_atol: float, loss_rtol: float) -> list[str]:
    errors: list[str] = []
    if not math.isclose(float(reference["loss"]), float(candidate["loss"]), abs_tol=loss_atol, rel_tol=loss_rtol):
        errors.append(f"loss reference={reference['loss']} candidate={candidate['loss']}")
    if reference.get("pruned_match") != candidate.get("pruned_match"):
        errors.append(f"pruned_match reference={reference.get('pruned_match')} candidate={candidate.get('pruned_match')}")
    if reference.get("support_terms") != candidate.get("support_terms"):
        errors.append(f"support_terms reference={reference.get('support_terms')} candidate={candidate.get('support_terms')}")
    return errors


def main() -> int:
    args = parse_args()
    reference = read_reference(Path(args.reference))
    compared = 0
    failures = []

    for index in args.indices:
        candidate_path = Path(args.batch_dir) / f"cell_{index:06d}.jsonl"
        candidate = read_jsonl_record(candidate_path)
        record_key = key(candidate)
        if record_key not in reference:
            failures.append(f"index {index}: missing reference key {record_key}")
            continue
        errors = compare_record(reference[record_key], candidate, args.loss_atol, args.loss_rtol)
        if errors:
            failures.append(f"index {index} key {record_key}: " + "; ".join(errors))
            continue
        compared += 1
        print(f"match index={index} key={record_key}")

    if failures:
        for failure in failures:
            print(f"mismatch {failure}")
        return 1

    print(f"compared={compared}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
