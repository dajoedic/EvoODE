import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_phasec_cap_ablation import (  # noqa: E402
    ALLOWED_DIFFERENCE_COLUMNS,
    CAPPED_VARIANT,
    UNCAPPED_VARIANT,
)
from scripts.aggregate.convert_campaign_history_to_run_registry import row_from_record  # noqa: E402
from utils.paired_stats import pair_registry_by_conditions  # noqa: E402


EXPECTED_PILOT_RECORDS = 16
EXPECTED_PAIR_COUNT = 8
EXPERIMENT_ID = "paper1_phaseC_v1"
PILOT_SYSTEM_IDS = {2, 24, 52, 63}
PILOT_SEED = 42
PILOT_CONDITIONS = {"capped", "uncapped"}
KEY_COLUMNS = ["system_id", "seed", "initial_condition_set"]
PILOT_ALLOWED_DIFFERENCE_COLUMNS = set(ALLOWED_DIFFERENCE_COLUMNS)

FIELD_CHECKS = [
    ("raw support hit", "exact_support_match_raw"),
    ("pruned support hit", "exact_support_match_pruned"),
    ("coefficients", "model_terms"),
    ("basis name", "basis_name"),
    ("support definition marker", "exact_support_match_definition"),
    ("duplicate counter", "duplicate_candidate_structure_evaluations"),
    ("restart counter: fit attempts", "total_parameter_fit_attempts"),
    ("restart counter: fallback result fits", "total_optimizer_fallback_result_fits"),
    ("restart counter: last-resort fits", "total_optimizer_last_resort_fits"),
]


class CriterionFailure(ValueError):
    def __init__(self, criterion: int, cell: str, message: str) -> None:
        super().__init__(f"criterion {criterion} failed for {cell}: {message}")
        self.criterion = criterion
        self.cell = cell


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the Phase-C P9 pilot go criterion.")
    parser.add_argument("--records-dir", required=True, help="Directory containing pilot cell_*.jsonl files.")
    parser.add_argument("--manifest", required=True, help="Phase-C manifest.csv used by the pilot.")
    parser.add_argument(
        "--reconstruction-probe",
        required=True,
        help="CSV produced by wp_n5_ic_generalization.jl for the pilot records.",
    )
    parser.add_argument("--expected-git-hash", required=True)
    parser.add_argument("--expected-stage-cap-behavior-fingerprint", required=True)
    return parser.parse_args()


def fail(criterion: int, cell: str, message: str) -> None:
    raise CriterionFailure(criterion, cell, message)


def is_null(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def cell_label(record: dict[str, Any]) -> str:
    if "batch_output_file" in record:
        return str(record["batch_output_file"])
    parts = [
        f"system_id={record.get('system_id')}",
        f"condition={record.get('condition')}",
        f"ic={record.get('initial_condition_set')}",
        f"seed={record.get('seed')}",
    ]
    return ", ".join(parts)


def registry_label(row: dict[str, Any]) -> str:
    if not is_null(row.get("run_id")):
        return str(row["run_id"])
    parts = [
        f"campaign_manifest_index={row.get('campaign_manifest_index')}",
        f"system_id={row.get('system_id')}",
        f"condition={row.get('condition')}",
        f"ic={row.get('initial_condition_set')}",
        f"seed={row.get('seed')}",
    ]
    return ", ".join(parts)


def read_records(records_dir: Path) -> list[dict[str, Any]]:
    if not records_dir.is_dir():
        raise FileNotFoundError(f"Pilot record directory does not exist: {records_dir}")
    records: list[dict[str, Any]] = []
    for path in sorted(
        path
        for path in records_dir.glob("cell_*.jsonl")
        if not path.name.endswith(".heartbeat.jsonl")
    ):
        file_records: list[dict[str, Any]] = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            record["_source_file"] = str(path)
            record["_source_line"] = line_no
            file_records.append(record)
        if len(file_records) != 1:
            raise ValueError(f"{path} contains {len(file_records)} records, expected exactly 1")
        records.extend(file_records)
    if not records:
        raise ValueError(f"No pilot JSONL records found in {records_dir}")
    return records


def read_manifest(path: Path) -> dict[int, dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Manifest CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Manifest CSV has no data rows: {path}")
    return {int(row["index"]): row for row in rows}


def require_record_count(records: list[dict[str, Any]]) -> None:
    if len(records) != EXPECTED_PILOT_RECORDS:
        fail(1, "pilot", f"expected {EXPECTED_PILOT_RECORDS} records, got {len(records)}")


def registry_rows_from_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row_from_record(record, EXPERIMENT_ID) for record in records]


def verify_criterion_1(registry_rows: list[dict[str, Any]]) -> None:
    require_record_count(registry_rows)
    for row in registry_rows:
        label = registry_label(row)
        if row.get("success") is not True:
            fail(1, label, f"registry success is {row.get('success')!r}, expected true")
        if not is_null(row.get("failure_reason")):
            fail(1, label, f"registry failure_reason is {row.get('failure_reason')!r}, expected null/empty")


def verify_pilot_selection(record: dict[str, Any], manifest_row: dict[str, str]) -> None:
    label = registry_label(record)
    system_id = int(record.get("system_id"))
    seed = int(record.get("seed"))
    condition = str(record.get("condition"))
    ic_set = int(record.get("initial_condition_set"))
    if system_id not in PILOT_SYSTEM_IDS or seed != PILOT_SEED or condition not in PILOT_CONDITIONS or ic_set not in {1, 2}:
        fail(2, label, "record is outside the frozen P9 pilot selection")
    expected_variant = CAPPED_VARIANT if condition == "capped" else UNCAPPED_VARIANT
    checks = {
        "system_id": system_id,
        "seed": seed,
        "initial_condition_set": ic_set,
        "condition": condition,
        "variant": expected_variant,
    }
    for column, value in checks.items():
        manifest_value = manifest_row.get(column)
        if str(manifest_value) != str(value):
            fail(2, label, f"manifest {column}={manifest_value!r}, record has {value!r}")


def verify_criterion_2(
    registry_rows: list[dict[str, Any]],
    manifest: dict[int, dict[str, str]],
    expected_git_hash: str,
    expected_stage_fp: str,
) -> None:
    git_hashes = {row.get("git_hash") for row in registry_rows}
    config_fps = {row.get("config_fingerprint") for row in registry_rows}
    stage_fps = {row.get("stage_cap_behavior_fingerprint") for row in registry_rows}
    if len(git_hashes) != 1 or None in git_hashes:
        fail(2, "pilot", f"expected one non-null git_hash, got {sorted(map(str, git_hashes))}")
    if len(config_fps) != 1 or None in config_fps:
        fail(2, "pilot", f"expected one non-null config_fingerprint, got {sorted(map(str, config_fps))}")
    if len(stage_fps) != 1 or None in stage_fps:
        fail(2, "pilot", f"expected one non-null stage_cap_behavior_fingerprint, got {sorted(map(str, stage_fps))}")
    if next(iter(git_hashes)) != expected_git_hash:
        fail(2, "pilot", f"git_hash {next(iter(git_hashes))!r} != expected {expected_git_hash!r}")
    if next(iter(stage_fps)) != expected_stage_fp:
        fail(2, "pilot", f"stage_cap_behavior_fingerprint {next(iter(stage_fps))!r} != expected {expected_stage_fp!r}")

    seen_indices: set[int] = set()
    for row in registry_rows:
        label = registry_label(row)
        manifest_index = int(row.get("campaign_manifest_index"))
        if manifest_index in seen_indices:
            fail(2, label, f"duplicate campaign_manifest_index {manifest_index}")
        seen_indices.add(manifest_index)
        if manifest_index not in manifest:
            fail(2, label, f"campaign_manifest_index {manifest_index} is not present in manifest")
        manifest_row = manifest[manifest_index]
        if row.get("config_fingerprint") != manifest_row.get("config_fingerprint"):
            fail(
                2,
                label,
                "config_fingerprint "
                f"{row.get('config_fingerprint')!r} != manifest {manifest_row.get('config_fingerprint')!r}",
            )
        verify_pilot_selection(row, manifest_row)


def model_terms_have_coefficients(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for equation in value:
        if not isinstance(equation, list):
            return False
        for term in equation:
            if not isinstance(term, dict) or is_null(term.get("coefficient")):
                return False
    return True


def verify_criterion_3(records: list[dict[str, Any]]) -> None:
    for record in records:
        label = cell_label(record)
        for description, field in FIELD_CHECKS:
            if field not in record:
                fail(3, label, f"missing field {field!r} ({description})")
            if is_null(record[field]):
                fail(3, label, f"field {field!r} ({description}) is null")
        if not model_terms_have_coefficients(record["model_terms"]):
            fail(3, label, "model_terms does not contain per-term coefficients")


def registry_dataframe(registry_rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(registry_rows)


def verify_criterion_4(registry_rows: list[dict[str, Any]]) -> None:
    try:
        pair_registry_by_conditions(
            registry_dataframe(registry_rows),
            key_columns=KEY_COLUMNS,
            condition_column="condition",
            left_condition="capped",
            right_condition="uncapped",
            expected_total_pairs=EXPECTED_PAIR_COUNT,
            allowed_difference_columns=PILOT_ALLOWED_DIFFERENCE_COLUMNS,
        )
    except ValueError as exc:
        fail(4, "pilot pairs", str(exc))


def read_reconstruction_probe(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Reconstruction probe CSV does not exist: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Reconstruction probe CSV has no data rows: {path}")
    return rows


def probe_key_from_record(record: dict[str, Any]) -> str:
    return (
        f"{record['condition']}_sys{int(record['system_id'])}_"
        f"ic{int(record['initial_condition_set'])}_seed{int(record['seed'])}"
    )


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def numeric_zero(value: Any) -> bool:
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def verify_criterion_5(records: list[dict[str, Any]], probe_rows: list[dict[str, str]]) -> None:
    probe_by_key = {row.get("cell_key"): row for row in probe_rows}
    for record in records:
        key = probe_key_from_record(record)
        row = probe_by_key.get(key)
        if row is None:
            fail(5, key, "missing wp_n5 reconstruction-probe row")
        if not truthy(row.get("reconstruction_probe_ok")):
            fail(5, key, f"reconstruction_probe_ok is {row.get('reconstruction_probe_ok')!r}")
        if not numeric_zero(row.get("reconstruction_abs_loss_delta")):
            fail(5, key, f"reconstruction_abs_loss_delta is {row.get('reconstruction_abs_loss_delta')!r}, expected 0")


def verify(args: argparse.Namespace) -> int:
    records = read_records(Path(args.records_dir))
    registry_rows = registry_rows_from_records(records)
    manifest = read_manifest(Path(args.manifest))
    probe_rows = read_reconstruction_probe(Path(args.reconstruction_probe))
    verify_criterion_1(registry_rows)
    verify_criterion_2(
        registry_rows,
        manifest,
        args.expected_git_hash,
        args.expected_stage_cap_behavior_fingerprint,
    )
    verify_criterion_3(records)
    verify_criterion_4(registry_rows)
    verify_criterion_5(records, probe_rows)
    print(f"Phase-C P9 pilot go criterion passed: {len(records)} records, {EXPECTED_PAIR_COUNT} pairs")
    return 0


def main() -> int:
    args = parse_args()
    try:
        return verify(args)
    except (CriterionFailure, FileNotFoundError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
