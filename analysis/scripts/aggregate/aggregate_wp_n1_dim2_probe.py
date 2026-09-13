import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import check_required_columns, equationwise_support_match  # noqa: E402


DEFAULT_INPUT = Path(
    r"S:\BigDataOrion\data-science\joedicke\wp_n1_dim2_probe_ec3b6bd5b43f06539d38b633257ca51115bfa47f\tasks"
)
DEFAULT_CLASSIFICATION = (
    ANALYSIS_ROOT / "data" / "paper1_phaseB_v1" / "system_classification.csv"
)
DEFAULT_OUTPUT_DIR = ANALYSIS_ROOT / "data" / "wp_n1_dim2_probe"
EXPECTED_RECORDS = 336
EXPECTED_BOTH_EXACT_SYSTEMS = {24, 25, 26, 27, 28, 29, 31, 32, 38}
EXPECTED_CONSTANT_ONLY_EXACT_SYSTEMS = {43}
EQUALITY_DEFINITION = (
    "normalized term-name set equality per equation index; equation order is preserved"
)
VARIANT_OLD = "wp_n1_old_basis"
VARIANT_CONSTANT = "wp_n1_constant_basis"
IDENTITY_COLUMNS = ["system_id", "seed", "initial_condition_set", "variant"]
IDENTITY_FIELDS = ["git_hash", "config_fingerprint", "stage_cap_behavior_fingerprint"]
COUNT_COLUMNS = ["total_parameter_fits", "total_loss_evals", "total_ode_solves"]
EFFORT_COLUMNS = ["total_parameter_fits", "total_loss_evals"]
QUANTILES = [0.0, 0.25, 0.5, 0.75, 1.0]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate WP-N1 dim-2 basis probe result records."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--classification", default=str(DEFAULT_CLASSIFICATION))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Allow missing manifest indices and write the missing-index list to every output.",
    )
    return parser.parse_args(argv)


def read_result_records(input_path: Path) -> list[dict[str, Any]]:
    files: list[Path]
    if input_path.is_file():
        files = [input_path]
    else:
        files = sorted(
            path
            for path in input_path.glob("cell_*.jsonl")
            if not path.name.endswith(".heartbeat.jsonl")
        )
    records: list[dict[str, Any]] = []
    for path in files:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
                if not isinstance(record, dict):
                    raise ValueError(f"Expected object at {path}:{line_number}")
                records.append(record)
    return records


def load_system_metadata(classification_path: Path) -> pd.DataFrame:
    df = pd.read_csv(classification_path)
    check_required_columns(df, ["system_id", "dim", "description"])
    return (
        df.loc[:, ["system_id", "dim", "description"]]
        .drop_duplicates(subset=["system_id"])
        .rename(columns={"description": "classification_description"})
    )


def require_single_value(records: list[dict[str, Any]], field: str) -> Any:
    values = {record.get(field) for record in records}
    if len(values) != 1:
        raise ValueError(f"Expected one {field}, found {sorted(map(str, values))}")
    value = next(iter(values))
    if field == "git_hash" and value == "not_collected":
        raise ValueError("git_hash is not_collected")
    return value


def record_error(record: dict[str, Any]) -> str:
    value = record.get("error")
    if value is None:
        return ""
    return str(value).strip()


def manifest_index(record: dict[str, Any]) -> int:
    try:
        return int(record["manifest_index"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Every record must carry an integer manifest_index") from exc


def validate_records(records: list[dict[str, Any]], allow_incomplete: bool) -> dict[str, Any]:
    if not records:
        raise ValueError("No result records found")

    for field in IDENTITY_FIELDS:
        require_single_value(records, field)

    errored = [
        manifest_index(record)
        for record in records
        if record_error(record)
    ]
    if errored:
        raise ValueError(f"Records carry non-empty error values at manifest indices {errored}")

    identities: set[tuple[Any, ...]] = set()
    duplicates: list[tuple[Any, ...]] = []
    for record in records:
        identity = tuple(record.get(column) for column in IDENTITY_COLUMNS)
        if identity in identities:
            duplicates.append(identity)
        identities.add(identity)
    if duplicates:
        raise ValueError(f"Duplicate cells for identities {duplicates}")

    indices = {manifest_index(record) for record in records}
    expected_indices = set(range(1, EXPECTED_RECORDS + 1))
    missing = sorted(expected_indices - indices)
    extra = sorted(indices - expected_indices)
    if extra:
        raise ValueError(f"Unexpected manifest indices {extra}")
    if missing and not allow_incomplete:
        raise ValueError(f"Missing manifest indices {missing}")

    return {
        "is_incomplete": bool(missing),
        "missing_manifest_indices": missing,
        "expected_records": EXPECTED_RECORDS,
        "observed_records": len(records),
    }


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no", ""}:
            return False
    return bool(value)


def support_field(record: dict[str, Any], field: str) -> list[list[Any]]:
    value = record.get(field)
    if not isinstance(value, list):
        raise ValueError(f"Record {manifest_index(record)} field {field} must be a list")
    for eq_index, terms in enumerate(value, start=1):
        if not isinstance(terms, list):
            raise ValueError(
                f"Record {manifest_index(record)} field {field} equation {eq_index} must be a list"
            )
    return value


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def derive_exact_system_sets(df: pd.DataFrame) -> tuple[set[int], set[int], set[int]]:
    exact = df.loc[df["representability"] == "exact", ["system_id", "variant"]].drop_duplicates()
    old_exact = set(exact.loc[exact["variant"] == VARIANT_OLD, "system_id"].astype(int))
    constant_exact = set(exact.loc[exact["variant"] == VARIANT_CONSTANT, "system_id"].astype(int))
    both_exact = old_exact & constant_exact
    constant_only = constant_exact - old_exact
    old_only = old_exact - constant_exact
    if both_exact != EXPECTED_BOTH_EXACT_SYSTEMS:
        raise ValueError(
            f"Both-basis exact systems differ from expected check value: {sorted(both_exact)}"
        )
    if constant_only != EXPECTED_CONSTANT_ONLY_EXACT_SYSTEMS:
        raise ValueError(
            f"Constant-only exact systems differ from expected check value: {sorted(constant_only)}"
        )
    if old_only:
        raise ValueError(f"Old-only exact systems are not expected: {sorted(old_only)}")
    return both_exact, constant_only, old_only


def layer_for(system_id: int, variant: str, both_exact: set[int], constant_only: set[int]) -> str:
    if system_id in both_exact:
        return "A_paired_both_exact"
    if system_id in constant_only and variant == VARIANT_CONSTANT:
        return "B_constant_only_exact"
    return "C_literature_all_cells"


def base_cell_rows(
    records: list[dict[str, Any]],
    metadata: pd.DataFrame,
    validation: dict[str, Any],
) -> tuple[pd.DataFrame, int]:
    rows: list[dict[str, Any]] = []
    containment_violations = 0
    missing_indices_text = "|".join(map(str, validation["missing_manifest_indices"]))

    for record in records:
        representability = str(record.get("representability")).strip().lower()
        if representability == "exact":
            raw_support_match = equationwise_support_match(
                support_field(record, "support_terms"),
                support_field(record, "wp_n1_expected_support_terms"),
            )
            pruned_support_match = as_bool(record.get("pruned_match"))
        elif representability == "surrogate":
            raw_support_match = None
            pruned_support_match = None
            if record.get("wp_n1_expected_support_terms") is not None:
                support_field(record, "wp_n1_expected_support_terms")
        else:
            raise ValueError(
                f"Record {manifest_index(record)} representability must be exact or surrogate"
            )

        raw_implies_pruned_violation = bool(
            raw_support_match is True and pruned_support_match is False
        )
        if raw_implies_pruned_violation:
            containment_violations += 1

        rows.append(
            {
                "manifest_index": manifest_index(record),
                "system_id": int(record["system_id"]),
                "system_name": record.get("system_name"),
                "seed": int(record["seed"]),
                "initial_condition_set": record.get("initial_condition_set"),
                "variant": record.get("variant"),
                "basis_name": record.get("basis_name"),
                "representability": representability,
                "wp_n1_support_status": record.get("wp_n1_support_status"),
                "raw_support_match": raw_support_match,
                "pruned_support_match": pruned_support_match,
                "support_equality_definition": EQUALITY_DEFINITION,
                "raw_implies_pruned_violation": raw_implies_pruned_violation,
                "r2": record.get("r2"),
                "r2_gt_0_9": float(record.get("r2")) > 0.9 if record.get("r2") is not None else False,
                "loss": record.get("loss"),
                "final_stage": record.get("final_stage"),
                "eq_final_stages": json.dumps(record.get("eq_final_stages"), separators=(",", ":")),
                "total_parameter_fits": record.get("total_parameter_fits"),
                "total_loss_evals": record.get("total_loss_evals"),
                "total_ode_solves": record.get("total_ode_solves"),
                "elapsed_s": record.get("elapsed_s"),
                "elapsed_s_evidence_role": "non_evidence",
                "git_hash": record.get("git_hash"),
                "config_fingerprint": record.get("config_fingerprint"),
                "stage_cap_behavior_fingerprint": record.get("stage_cap_behavior_fingerprint"),
                "incomplete_allowed": validation["is_incomplete"],
                "expected_manifest_records": validation["expected_records"],
                "observed_manifest_records": validation["observed_records"],
                "missing_manifest_indices": missing_indices_text,
            }
        )

    df = pd.DataFrame(rows).merge(metadata, on="system_id", how="left")
    both_exact, constant_only, _ = derive_exact_system_sets(df)
    df["decision_layer"] = [
        layer_for(int(row.system_id), str(row.variant), both_exact, constant_only)
        for row in df.itertuples(index=False)
    ]
    df = df.sort_values(["manifest_index", "system_id", "seed", "initial_condition_set", "variant"])
    return df, containment_violations


def rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def summary_row(
    row_type: str,
    layer: str,
    df: pd.DataFrame,
    validation: dict[str, Any],
    containment_violations: int,
    variant: str | None = None,
    representability: str | None = None,
    system_id: int | None = None,
) -> dict[str, Any]:
    n_cells = len(df)
    support_applicable = df[df["representability"] == "exact"] if n_cells else df
    support_denominator = len(support_applicable)
    raw_hits = int(support_applicable["raw_support_match"].sum()) if support_denominator else 0
    pruned_hits = (
        int(support_applicable["pruned_support_match"].sum()) if support_denominator else 0
    )
    r2_hits = int(df["r2_gt_0_9"].sum()) if n_cells else 0
    systems = sorted(df["system_id"].dropna().astype(int).unique().tolist()) if n_cells else []
    row: dict[str, Any] = {
        "row_type": row_type,
        "decision_layer": layer,
        "variant": variant,
        "representability": representability,
        "system_id": system_id,
        "n_systems": len(systems),
        "effective_sample_size_systems": len(systems) if layer == "A_paired_both_exact" else None,
        "n_cells": n_cells,
        "raw_support_hits": raw_hits,
        "raw_support_denominator": support_denominator,
        "raw_support_rate": rate(raw_hits, support_denominator),
        "pruned_support_hits": pruned_hits,
        "pruned_support_denominator": support_denominator,
        "pruned_support_rate": rate(pruned_hits, support_denominator),
        "r2_gt_0_9_hits": r2_hits,
        "r2_gt_0_9_rate": rate(r2_hits, n_cells),
        "support_equality_definition": EQUALITY_DEFINITION,
        "raw_implies_pruned_violations_total": containment_violations,
        "incomplete_allowed": validation["is_incomplete"],
        "expected_manifest_records": validation["expected_records"],
        "observed_manifest_records": validation["observed_records"],
        "missing_manifest_indices": "|".join(map(str, validation["missing_manifest_indices"])),
        "systems": "|".join(map(str, systems)),
        "elapsed_s_evidence_role": "non_evidence",
    }
    for column in EFFORT_COLUMNS + ["elapsed_s"]:
        numeric = pd.to_numeric(df[column], errors="coerce") if n_cells else pd.Series(dtype=float)
        quantiles = numeric.quantile(QUANTILES) if not numeric.dropna().empty else {}
        for quantile in QUANTILES:
            row[f"{column}_q{int(quantile * 100):03d}"] = (
                float(quantiles.loc[quantile]) if quantile in quantiles else None
            )
    return row


def layer_a_contingency_rows(
    df: pd.DataFrame,
    validation: dict[str, Any],
    containment_violations: int,
) -> list[dict[str, Any]]:
    layer = df[df["decision_layer"] == "A_paired_both_exact"]
    pivot = layer.pivot_table(
        index=["system_id", "seed", "initial_condition_set"],
        columns="variant",
        values="raw_support_match",
        aggfunc="first",
    )
    counts = {
        "both": 0,
        "old_only": 0,
        "constant_only": 0,
        "neither": 0,
    }
    for _, row in pivot.iterrows():
        old_value = row.get(VARIANT_OLD)
        constant_value = row.get(VARIANT_CONSTANT)
        if pd.isna(old_value) or pd.isna(constant_value):
            continue
        old_hit = bool(old_value)
        constant_hit = bool(constant_value)
        if old_hit and constant_hit:
            counts["both"] += 1
        elif old_hit:
            counts["old_only"] += 1
        elif constant_hit:
            counts["constant_only"] += 1
        else:
            counts["neither"] += 1

    rows: list[dict[str, Any]] = []
    for cell_type, count in counts.items():
        row = summary_row(
            "layer_a_raw_contingency",
            "A_paired_both_exact",
            layer.iloc[0:0],
            validation,
            containment_violations,
        )
        row["contingency_cell"] = cell_type
        row["paired_cell_count"] = count
        row["paired_cell_denominator"] = int(len(pivot))
        rows.append(row)
    return rows


def build_decision_table(
    cells: pd.DataFrame,
    validation: dict[str, Any],
    containment_violations: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    layer_a = cells[cells["decision_layer"] == "A_paired_both_exact"]
    for variant, group in layer_a.groupby("variant", sort=True):
        rows.append(
            summary_row(
                "layer_summary",
                "A_paired_both_exact",
                group,
                validation,
                containment_violations,
                variant=variant,
            )
        )

    layer_b = cells[cells["decision_layer"] == "B_constant_only_exact"]
    rows.append(
        summary_row(
            "layer_summary",
            "B_constant_only_exact",
            layer_b,
            validation,
            containment_violations,
            variant=VARIANT_CONSTANT,
        )
    )

    for (variant, representability), group in cells.groupby(["variant", "representability"], sort=True):
        rows.append(
            summary_row(
                "literature_r2_summary",
                "C_literature_all_cells",
                group,
                validation,
                containment_violations,
                variant=variant,
                representability=representability,
            )
        )

    rows.extend(layer_a_contingency_rows(cells, validation, containment_violations))

    for (system_id, variant), group in layer_a.groupby(["system_id", "variant"], sort=True):
        rows.append(
            summary_row(
                "layer_a_by_system",
                "A_paired_both_exact",
                group,
                validation,
                containment_violations,
                variant=variant,
                system_id=int(system_id),
            )
        )

    return pd.DataFrame(rows)


def run(
    input_path: Path,
    classification_path: Path,
    output_dir: Path,
    allow_incomplete: bool = False,
) -> dict[str, Any]:
    records = read_result_records(input_path)
    validation = validate_records(records, allow_incomplete)
    metadata = load_system_metadata(classification_path)
    cells, containment_violations = base_cell_rows(records, metadata, validation)
    decisions = build_decision_table(cells, validation, containment_violations)

    output_dir.mkdir(parents=True, exist_ok=True)
    cell_path = output_dir / "wp_n1_dim2_probe_cells.csv"
    decision_path = output_dir / "wp_n1_dim2_probe_decision_table.csv"
    cells.to_csv(cell_path, index=False)
    decisions.to_csv(decision_path, index=False)
    return {
        "cell_path": cell_path,
        "decision_path": decision_path,
        "n_records": len(records),
        "missing_manifest_indices": validation["missing_manifest_indices"],
        "containment_violations": containment_violations,
        "layer_a_systems": sorted(
            cells.loc[cells["decision_layer"] == "A_paired_both_exact", "system_id"]
            .drop_duplicates()
            .astype(int)
            .tolist()
        ),
        "layer_a_counts_by_variant": (
            cells[cells["decision_layer"] == "A_paired_both_exact"]
            .groupby("variant")
            .size()
            .to_dict()
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run(
            Path(args.input),
            Path(args.classification),
            Path(args.output_dir),
            allow_incomplete=args.allow_incomplete,
        )
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {display_path(result['cell_path'])}")
    print(f"Wrote {display_path(result['decision_path'])}")
    print(f"Records read: {result['n_records']}")
    if result["missing_manifest_indices"]:
        print(f"Missing manifest indices: {result['missing_manifest_indices']}")
    print(f"Raw-implies-pruned violations: {result['containment_violations']}")
    print(f"Layer A systems: {result['layer_a_systems']}")
    print(f"Layer A counts by variant: {result['layer_a_counts_by_variant']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
