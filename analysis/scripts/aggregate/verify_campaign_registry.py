import argparse
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.campaign import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    campaign_registry_path,
    require_single_campaign_id,
)


DEFAULT_EXPECTED_GIT_HASH = "91f88c4"
DEFAULT_EXPECTED_CONFIG_FINGERPRINT = "604e79733b22d64d"
DEFAULT_EXPECTED_STAGE_CAP_FINGERPRINT = "ffb0266c7913352c"

REQUIRED_COLUMNS = [
    "experiment_id",
    "system_id",
    "seed",
    "variant_slug",
    "initial_condition_set",
    "corrupted",
    "failure_reason",
    "git_hash",
    "git_dirty",
    "config_fingerprint",
    "stage_cap_behavior_fingerprint",
    "system_representability",
    "exact_support_match",
    "r2",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify campaign run_registry.csv invariants before aggregation."
    )
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument(
        "--input",
        help="Converted run_registry.csv path. Defaults to experiments/<campaign>/run_registry.csv.",
    )
    parser.add_argument("--expected-row-count", type=int, default=756)
    parser.add_argument("--expected-unique-identities", type=int, default=756)
    parser.add_argument("--expected-rows-per-condition", type=int, default=378)
    parser.add_argument("--expected-exact-rows", type=int, default=240)
    parser.add_argument("--expected-surrogate-rows", type=int, default=516)
    parser.add_argument(
        "--phase-c-support-table",
        help=(
            "Derive Phase-C row-count and representability expectations from "
            "phase_c_support.json instead of hard-coding them in Python."
        ),
    )
    parser.add_argument(
        "--expected-git-hash",
        default=DEFAULT_EXPECTED_GIT_HASH,
        help="Expected single git_hash value.",
    )
    parser.add_argument(
        "--expected-config-fingerprint",
        default=DEFAULT_EXPECTED_CONFIG_FINGERPRINT,
        help="Expected single config_fingerprint value.",
    )
    parser.add_argument(
        "--expected-stage-cap-behavior-fingerprint",
        default=DEFAULT_EXPECTED_STAGE_CAP_FINGERPRINT,
        help="Expected single stage_cap_behavior_fingerprint value.",
    )
    return parser.parse_args()


def apply_phase_c_support_expectations(args: argparse.Namespace) -> argparse.Namespace:
    if not args.phase_c_support_table:
        return args

    support_path = Path(args.phase_c_support_table)
    with support_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    systems = payload.get("systems")
    if not isinstance(systems, list) or not systems:
        raise ValueError(f"Support table has no systems list: {support_path}")

    counts = Counter(str(system.get("representability", "")).strip() for system in systems)
    exact_systems = counts.get("exact", 0)
    surrogate_systems = counts.get("surrogate", 0)
    unknown = sorted(key for key in counts if key not in {"exact", "surrogate"})
    if unknown:
        raise ValueError(f"Support table has unknown representability labels: {unknown}")

    per_full_arm = len(systems) * 3 * 2
    per_exact_arm = exact_systems * 3 * 2
    args.expected_rows_per_condition = {
        "capped": per_full_arm,
        "uncapped": per_full_arm,
        "pretune_on": per_exact_arm,
    }
    args.expected_row_count = sum(args.expected_rows_per_condition.values())
    args.expected_unique_identities = args.expected_row_count
    args.expected_exact_rows = exact_systems * 3 * 2 * 3
    args.expected_surrogate_rows = surrogate_systems * 3 * 2 * 2
    return args


def fail(message: str) -> int:
    print(f"Invariant failed: {message}", file=sys.stderr)
    return 1


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")
        return list(reader)


def normalized_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def is_false(value: object) -> bool:
    return normalized_text(value).lower() in {"false", "0", "no", "n", ""}


def is_set(value: object) -> bool:
    text = normalized_text(value)
    return text != "" and text.lower() not in {"nan", "none", "null"}


def is_numeric(value: object) -> bool:
    text = normalized_text(value)
    if not is_set(text):
        return False
    try:
        number = float(text)
    except ValueError:
        return False
    return math.isfinite(number)


def unique_values(rows: Iterable[dict[str, str]], column: str) -> set[str]:
    return {normalized_text(row[column]) for row in rows}


def condition_column(rows: list[dict[str, str]]) -> str:
    if rows and "condition" in rows[0] and any(is_set(row.get("condition")) for row in rows):
        return "condition"
    return "variant_slug"


def verify(rows: list[dict[str, str]], args: argparse.Namespace) -> int:
    row_count = len(rows)
    try:
        require_single_campaign_id(
            pd.DataFrame(rows), args.campaign, "campaign registry"
        )
    except ValueError as exc:
        return fail(str(exc))

    if row_count != args.expected_row_count:
        return fail(f"row count expected {args.expected_row_count}, got {row_count}")

    condition = condition_column(rows)
    identities = {
        (
            normalized_text(row["system_id"]),
            normalized_text(row["seed"]),
            normalized_text(row["initial_condition_set"]),
            normalized_text(row[condition]),
        )
        for row in rows
    }
    if len(identities) != args.expected_unique_identities:
        return fail(
            "unique identities from system_id, seed, initial_condition_set, "
            f"{condition} expected {args.expected_unique_identities}, got {len(identities)}"
        )

    corrupted_rows = sum(not is_false(row["corrupted"]) for row in rows)
    if corrupted_rows != 0:
        return fail(f"corrupted rows expected 0, got {corrupted_rows}")

    failure_rows = sum(is_set(row["failure_reason"]) for row in rows)
    if failure_rows != 0:
        return fail(f"rows with failure_reason expected 0, got {failure_rows}")

    git_hashes = unique_values(rows, "git_hash")
    if git_hashes != {args.expected_git_hash}:
        return fail(
            f"git_hash expected only {args.expected_git_hash}, got {sorted(git_hashes)}"
        )

    dirty_rows = sum(not is_false(row["git_dirty"]) for row in rows)
    if dirty_rows != 0:
        return fail(f"git_dirty false rows expected {row_count}, dirty rows got {dirty_rows}")

    config_fingerprints = unique_values(rows, "config_fingerprint")
    if config_fingerprints != {args.expected_config_fingerprint}:
        return fail(
            "config_fingerprint expected only "
            f"{args.expected_config_fingerprint}, got {sorted(config_fingerprints)}"
        )

    stage_cap_fingerprints = unique_values(rows, "stage_cap_behavior_fingerprint")
    if stage_cap_fingerprints != {args.expected_stage_cap_behavior_fingerprint}:
        return fail(
            "stage_cap_behavior_fingerprint expected only "
            f"{args.expected_stage_cap_behavior_fingerprint}, got {sorted(stage_cap_fingerprints)}"
        )

    rows_per_condition = Counter(normalized_text(row[condition]) for row in rows)
    if isinstance(args.expected_rows_per_condition, dict):
        expected_condition_counts = {
            str(key): int(value)
            for key, value in args.expected_rows_per_condition.items()
        }
        actual_condition_counts = dict(rows_per_condition)
        if actual_condition_counts != expected_condition_counts:
            return fail(
                f"rows per {condition} expected {expected_condition_counts}, "
                f"got {actual_condition_counts}"
            )
    else:
        wrong_condition_counts = {
            key: value
            for key, value in rows_per_condition.items()
            if value != args.expected_rows_per_condition
        }
        if wrong_condition_counts:
            return fail(
                f"rows per {condition} expected {args.expected_rows_per_condition}, "
                f"got {dict(rows_per_condition)}"
            )

    representability_counts = Counter(
        normalized_text(row["system_representability"]) for row in rows
    )
    exact_rows = representability_counts.get("exact", 0)
    surrogate_rows = representability_counts.get("surrogate", 0)
    if exact_rows != args.expected_exact_rows or surrogate_rows != args.expected_surrogate_rows:
        return fail(
            "representability counts expected "
            f"exact={args.expected_exact_rows}, surrogate={args.expected_surrogate_rows}; "
            f"got exact={exact_rows}, surrogate={surrogate_rows}, all={dict(representability_counts)}"
        )

    exact_support_set = sum(
        is_set(row["exact_support_match"])
        for row in rows
        if normalized_text(row["system_representability"]) == "exact"
    )
    surrogate_support_set = sum(
        is_set(row["exact_support_match"])
        for row in rows
        if normalized_text(row["system_representability"]) == "surrogate"
    )
    if exact_support_set != args.expected_exact_rows or surrogate_support_set != 0:
        return fail(
            "exact_support_match population expected "
            f"exact={args.expected_exact_rows}, surrogate=0; "
            f"got exact={exact_support_set}, surrogate={surrogate_support_set}"
        )

    surrogate_r2_numeric = sum(
        is_numeric(row["r2"])
        for row in rows
        if normalized_text(row["system_representability"]) == "surrogate"
    )
    if surrogate_r2_numeric < args.expected_surrogate_rows:
        return fail(
            f"numeric r2 in surrogate rows expected at least {args.expected_surrogate_rows}, "
            f"got {surrogate_r2_numeric}"
        )

    print(f"Verified campaign registry: {row_count} rows")
    print(f"  Unique identities: {len(identities)}")
    print(f"  Condition column: {condition}")
    print(f"  Rows per condition: {dict(sorted(rows_per_condition.items()))}")
    print(f"  Representability: exact={exact_rows}, surrogate={surrogate_rows}")
    print(f"  git_hash: {args.expected_git_hash}")
    print(f"  config_fingerprint: {args.expected_config_fingerprint}")
    print(
        "  stage_cap_behavior_fingerprint: "
        f"{args.expected_stage_cap_behavior_fingerprint}"
    )
    print(f"  Numeric surrogate r2 rows: {surrogate_r2_numeric}")
    return 0


def main() -> int:
    args = parse_args()
    input_path = (
        Path(args.input)
        if args.input
        else campaign_registry_path(REPO_ROOT, args.campaign)
    )
    try:
        args = apply_phase_c_support_expectations(args)
        rows = read_rows(input_path)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return verify(rows, args)


if __name__ == "__main__":
    sys.exit(main())
