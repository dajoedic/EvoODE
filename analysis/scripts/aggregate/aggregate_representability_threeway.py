import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import check_required_columns, parse_pipe_terms  # noqa: E402
from utils.campaign import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    campaign_data_dir,
)


DEFAULT_CLASSIFICATION = campaign_data_dir(ANALYSIS_ROOT, DEFAULT_CAMPAIGN_ID) / "system_classification.csv"
DEFAULT_ADEQUACY = campaign_data_dir(ANALYSIS_ROOT, DEFAULT_CAMPAIGN_ID) / "representational_adequacy.csv"
DEFAULT_OUTPUT_DIR = campaign_data_dir(ANALYSIS_ROOT, DEFAULT_CAMPAIGN_ID)

BASIS_OLD = "default_staged_polynomial_basis"
BASIS_CONSTANT = "staged_polynomial_basis_with_constant"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify systems and equations into three representability classes."
    )
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument("--classification")
    parser.add_argument("--adequacy")
    parser.add_argument("--output-dir")
    return parser.parse_args()


def split_unmatched(value: Any) -> list[str]:
    if pd.isna(value) or str(value).strip() == "":
        return []
    return [part for part in str(value).split("|") if part.strip()]


def is_constant_unmatched(term_with_reason: str) -> bool:
    return term_with_reason.strip().endswith("[constant_offset]")


def classify_counts(representable_terms: int, total_terms: int) -> str:
    if total_terms <= 0:
        return "fully_representable"
    if representable_terms == total_terms:
        return "fully_representable"
    if representable_terms == 0:
        return "non_representable"
    return "partially_representable"


def equation_count_row(row: pd.Series, basis_name: str) -> dict[str, Any]:
    matched = parse_pipe_terms(row["matched_basis_terms"])
    unmatched = split_unmatched(row["unmatched_terms"])
    constant_terms = [term for term in unmatched if is_constant_unmatched(term)]

    if basis_name == BASIS_OLD:
        representable = len(matched)
    elif basis_name == BASIS_CONSTANT:
        representable = len(matched) + len(constant_terms)
    else:
        raise ValueError(f"Unsupported basis: {basis_name}")

    total = len(matched) + len(unmatched)
    return {
        "basis_name": basis_name,
        "system_id": int(row["system_id"]),
        "dim": int(row["dim"]),
        "description": row["description"],
        "equation_index": int(row["equation_index"]),
        "n_true_terms": total,
        "n_representable_true_terms": representable,
        "n_nonrepresentable_true_terms": total - representable,
        "representability_class": classify_counts(representable, total),
        "matched_basis_terms": "|".join(matched),
        "unmatched_terms": "|".join(unmatched),
    }


def system_class(rows: list[dict[str, Any]]) -> str:
    total = sum(row["n_true_terms"] for row in rows)
    representable = sum(row["n_representable_true_terms"] for row in rows)
    return classify_counts(representable, total)


def run(classification_path: Path, adequacy_path: Path, output_dir: Path) -> dict[str, Any]:
    classification = pd.read_csv(classification_path)
    check_required_columns(
        classification,
        [
            "system_id",
            "dim",
            "description",
            "equation_index",
            "matched_basis_terms",
            "unmatched_terms",
        ],
    )
    adequacy = pd.read_csv(adequacy_path)
    check_required_columns(adequacy, ["system_id", "evoode_staged"])
    adequacy_by_system = {
        int(row["system_id"]): row["evoode_staged"] for _, row in adequacy.iterrows()
    }

    equation_rows: list[dict[str, Any]] = []
    for basis_name in [BASIS_OLD, BASIS_CONSTANT]:
        for _, row in classification.iterrows():
            equation_rows.append(equation_count_row(row, basis_name))

    system_rows: list[dict[str, Any]] = []
    for (basis_name, system_id), group in pd.DataFrame(equation_rows).groupby(
        ["basis_name", "system_id"], sort=True
    ):
        records = group.to_dict("records")
        first = records[0]
        system_rows.append(
            {
                "basis_name": basis_name,
                "system_id": int(system_id),
                "dim": int(first["dim"]),
                "description": first["description"],
                "n_equations": len(records),
                "n_true_terms": sum(row["n_true_terms"] for row in records),
                "n_representable_true_terms": sum(
                    row["n_representable_true_terms"] for row in records
                ),
                "n_nonrepresentable_true_terms": sum(
                    row["n_nonrepresentable_true_terms"] for row in records
                ),
                "representability_class": system_class(records),
                "phaseb_evoode_staged_matrix_flag": adequacy_by_system.get(int(system_id), ""),
            }
        )

    summary_rows: list[dict[str, Any]] = []
    for basis_name in [BASIS_OLD, BASIS_CONSTANT]:
        counts = Counter(
            row["representability_class"] for row in system_rows if row["basis_name"] == basis_name
        )
        for label in [
            "fully_representable",
            "partially_representable",
            "non_representable",
        ]:
            summary_rows.append(
                {"basis_name": basis_name, "representability_class": label, "systems": counts[label]}
            )

    if len(system_rows) != 126:
        raise ValueError(f"Expected 126 basis-system rows, found {len(system_rows)}")
    if len({row["system_id"] for row in system_rows}) != 63:
        raise ValueError("Expected 63 systems")

    output_dir.mkdir(parents=True, exist_ok=True)
    equation_path = output_dir / "representability_threeway_by_equation.csv"
    system_path = output_dir / "representability_threeway_by_system.csv"
    summary_path = output_dir / "representability_threeway_summary.csv"
    pd.DataFrame(equation_rows).to_csv(equation_path, index=False)
    pd.DataFrame(system_rows).to_csv(system_path, index=False)
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)

    return {
        "equation_path": equation_path,
        "system_path": system_path,
        "summary_path": summary_path,
        "summary_rows": summary_rows,
    }


def main() -> int:
    args = parse_args()
    data_dir = campaign_data_dir(ANALYSIS_ROOT, args.campaign)
    classification_path = (
        Path(args.classification).resolve()
        if args.classification
        else data_dir / "system_classification.csv"
    )
    adequacy_path = (
        Path(args.adequacy).resolve()
        if args.adequacy
        else data_dir / "representational_adequacy.csv"
    )
    output_dir = Path(args.output_dir).resolve() if args.output_dir else data_dir
    try:
        result = run(classification_path, adequacy_path, output_dir)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {result['equation_path'].relative_to(REPO_ROOT)}")
    print(f"Wrote {result['system_path'].relative_to(REPO_ROOT)}")
    print(f"Wrote {result['summary_path'].relative_to(REPO_ROOT)}")
    for row in result["summary_rows"]:
        print(f"{row['basis_name']} {row['representability_class']}: {row['systems']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
