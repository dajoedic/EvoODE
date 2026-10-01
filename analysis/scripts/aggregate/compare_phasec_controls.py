from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_C1 = Path("outputs/phase_c_campaign_221a3a7")
DEFAULT_ORACLE = Path("outputs/wp_n3_oracle_refit_phase_c")
MISSING = object()


def is_record_file(path: Path) -> bool:
    return path.suffix == ".jsonl" and not path.name.endswith(".heartbeat.jsonl")


def read_jsonl_records(path: Path) -> list[dict[str, Any]]:
    if path.is_file():
        files = [path]
    elif (path / "tasks").is_dir():
        files = sorted(p for p in (path / "tasks").glob("cell_*.jsonl") if is_record_file(p))
    else:
        files = sorted(p for p in path.glob("*.jsonl") if is_record_file(p))
    records: list[dict[str, Any]] = []
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(json.loads(line))
    return records


def campaign_key(record: dict[str, Any]) -> tuple[str, int, int, int]:
    return (
        str(record["variant"]),
        int(record["system_id"]),
        int(record["initial_condition_set"]),
        int(record["seed"]),
    )


def oracle_key(record: dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(record["system_id"]),
        int(record["initial_condition_set"]),
        int(record["seed"]),
    )


def coefficient_payload(model_terms: Any) -> Any:
    if model_terms is None:
        return None
    payload = []
    for equation in model_terms:
        payload.append(
            [
                {
                    "term_index": int(term["term_index"]),
                    "term": str(term["term"]),
                    "coefficient": float(term["coefficient"]).hex(),
                }
                for term in equation
            ]
        )
    return payload


def normalize_campaign_field(field: str, value: Any) -> Any:
    if value is MISSING:
        return value
    if field == "model_terms":
        return coefficient_payload(value)
    if field == "loss":
        return float(value).hex()
    return value


def normalize_oracle_field(field: str, value: Any) -> Any:
    if value is MISSING:
        return value
    if field == "reference_coefficients":
        return coefficient_payload(value)
    if field == "reference_loss":
        return float(value).hex()
    if field == "reference_fit_meta.loss_evals":
        return value
    return value


def compare_maps(
    candidate_records: list[dict[str, Any]],
    reference_records: list[dict[str, Any]],
    fields: list[str],
    key_func,
    normalizer,
) -> tuple[list[str], int]:
    reference = {key_func(record): record for record in reference_records}
    errors: list[str] = []
    compared = 0
    for record in candidate_records:
        key = key_func(record)
        if key not in reference:
            continue
        compared += 1
        ref = reference[key]
        for field in fields:
            candidate_value = record
            reference_value = ref
            for part in field.split("."):
                candidate_value = candidate_value.get(part, MISSING) if isinstance(candidate_value, dict) else MISSING
                reference_value = reference_value.get(part, MISSING) if isinstance(reference_value, dict) else MISSING
            if candidate_value is MISSING:
                errors.append(f"{key}: field {field} missing on candidate")
                continue
            if reference_value is MISSING:
                errors.append(f"{key}: field {field} missing on reference")
                continue
            if normalizer(field, candidate_value) != normalizer(field, reference_value):
                errors.append(f"{key}: field {field} differs")
    return errors, compared


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Phase-C control records against frozen C-1/C-5 records.")
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--reference-c1", default=DEFAULT_C1, type=Path)
    parser.add_argument("--candidate-oracle", type=Path)
    parser.add_argument("--reference-oracle", default=DEFAULT_ORACLE, type=Path)
    args = parser.parse_args()

    candidate = read_jsonl_records(args.candidate)
    reference = read_jsonl_records(args.reference_c1)
    errors, compared = compare_maps(
        candidate,
        reference,
        ["loss", "support_terms", "model_terms", "total_loss_evals", "stage_caps"],
        campaign_key,
        normalize_campaign_field,
    )

    if args.candidate_oracle is not None:
        oracle_candidate = read_jsonl_records(args.candidate_oracle)
        oracle_reference = read_jsonl_records(args.reference_oracle)
        oracle_errors, oracle_compared = compare_maps(
                oracle_candidate,
                oracle_reference,
                ["reference_loss", "reference_coefficients", "reference_fit_meta.loss_evals"],
                oracle_key,
                normalize_oracle_field,
            )
        errors.extend(oracle_errors)
        compared += oracle_compared

    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"Compared {compared} matching records with no differences")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
