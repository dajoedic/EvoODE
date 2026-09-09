import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import (  # noqa: E402
    aggregate_equation_metrics,
    check_required_columns,
    coefficient_metrics,
    normalize_term_name,
    term_set_metrics,
)


DEFAULT_INPUT = REPO_ROOT / "outputs" / "wp_n1_dim1_probe" / "history.jsonl"
DEFAULT_CLASSIFICATION = (
    ANALYSIS_ROOT / "data" / "paper1_phaseB_v1" / "system_classification.csv"
)
DEFAULT_OUTPUT_DIR = ANALYSIS_ROOT / "data" / "wp_n1_dim1_probe"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute structure and coefficient metrics for WP-N1 probe records."
    )
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--classification", default=str(DEFAULT_CLASSIFICATION))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
            rows.append(record)
    return rows


def local_dict(dim: int) -> dict[str, Any]:
    values: dict[str, Any] = {
        "sin": sp.sin,
        "cos": sp.cos,
        "exp": sp.exp,
        "log": sp.log,
        "cot": sp.cot,
        "Abs": sp.Abs,
    }
    for idx in range(dim):
        values[f"x_{idx}"] = sp.Symbol(f"x_{idx}")
    return values


def term_to_expr(term: str, dim: int) -> sp.Expr:
    normalized = normalize_term_name(term)
    local = local_dict(dim)
    expr_text = normalized.replace("^", "**")
    for idx in range(dim, 0, -1):
        expr_text = expr_text.replace(f"u{idx}", f"x_{idx - 1}")
    return parse_expr(expr_text, local_dict=local, evaluate=True)


def true_coefficients_for_terms(equation: str, dim: int, terms: list[str]) -> dict[str, float]:
    expr = sp.expand(parse_expr(equation, local_dict=local_dict(dim), evaluate=True))
    coefficients: dict[str, float] = {}
    for term in terms:
        normalized = normalize_term_name(term)
        if normalized == "1":
            coefficient = expr.as_coeff_Add()[0]
        else:
            basis_expr = term_to_expr(normalized, dim)
            coefficient = expr.coeff(basis_expr)
        if coefficient is None:
            raise ValueError(f"No coefficient found for term {normalized} in equation {equation}")
        coefficients[normalized] = float(coefficient)
    return coefficients


def load_equations(path: Path) -> dict[tuple[int, int], tuple[str, int]]:
    df = pd.read_csv(path)
    check_required_columns(df, ["system_id", "equation_index", "equation", "dim"])
    equations: dict[tuple[int, int], tuple[str, int]] = {}
    for _, row in df.iterrows():
        equations[(int(row["system_id"]), int(row["equation_index"]))] = (
            str(row["equation"]),
            int(row["dim"]),
        )
    return equations


def model_coefficients(equation_model_terms: Any) -> dict[str, float] | None:
    if equation_model_terms is None:
        return None
    if not isinstance(equation_model_terms, list):
        raise ValueError("model_terms equation entry must be a list")
    coefficients: dict[str, float] = {}
    for entry in equation_model_terms:
        if not isinstance(entry, dict):
            raise ValueError("model_terms entries must be objects")
        if "term" not in entry or "coefficient" not in entry:
            raise ValueError("model_terms entry is missing term or coefficient")
        coefficients[normalize_term_name(entry["term"])] = float(entry["coefficient"])
    return coefficients


def run(input_path: Path, classification_path: Path, output_dir: Path) -> dict[str, Any]:
    records = read_jsonl(input_path)
    equations = load_equations(classification_path)
    equation_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []

    for record_index, record in enumerate(records, start=1):
        system_id = int(record["system_id"])
        expected = record.get("wp_n1_expected_support_terms")
        support = record.get("support_terms")
        model_terms = record.get("model_terms")
        if expected is None or support is None:
            continue
        if not isinstance(expected, list) or not isinstance(support, list):
            raise ValueError(f"Record {record_index} support fields must be lists")
        if model_terms is not None and not isinstance(model_terms, list):
            raise ValueError(f"Record {record_index} model_terms must be a list")

        metrics_for_cell: list[dict[str, Any]] = []
        cell_coeff_metrics: list[dict[str, Any]] = []
        for equation_offset, true_terms_raw in enumerate(expected, start=1):
            found_terms = support[equation_offset - 1]
            true_terms = [normalize_term_name(term) for term in true_terms_raw]
            metrics = term_set_metrics(found_terms, true_terms)
            metrics_for_cell.append(metrics)
            equation, dim = equations[(system_id, equation_offset)]
            true_coeffs = true_coefficients_for_terms(equation, dim, true_terms)
            found_coeffs = (
                model_coefficients(model_terms[equation_offset - 1])
                if model_terms is not None
                else None
            )
            coeff = coefficient_metrics(found_coeffs, true_coeffs)
            cell_coeff_metrics.append(coeff)
            equation_rows.append(
                {
                    "record_index": record_index,
                    "system_id": system_id,
                    "system_name": record.get("system_name"),
                    "basis_name": record.get("basis_name"),
                    "condition": record.get("condition"),
                    "seed": record.get("seed"),
                    "initial_condition_set": record.get("initial_condition_set"),
                    "equation_index": equation_offset,
                    **metrics,
                    **coeff,
                }
            )

        cell_metrics = aggregate_equation_metrics(metrics_for_cell)
        coeff_values = [
            row["coefficient_relative_error_mean"]
            for row in cell_coeff_metrics
            if row["coefficient_relative_error_mean"] is not None
        ]
        cell_rows.append(
            {
                "record_index": record_index,
                "system_id": system_id,
                "system_name": record.get("system_name"),
                "basis_name": record.get("basis_name"),
                "condition": record.get("condition"),
                "seed": record.get("seed"),
                "initial_condition_set": record.get("initial_condition_set"),
                **cell_metrics,
                "n_coefficient_terms": sum(row["n_coefficient_terms"] for row in cell_coeff_metrics),
                "coefficient_relative_error_mean": (
                    sum(coeff_values) / len(coeff_values) if coeff_values else None
                ),
                "coefficient_relative_error_max": (
                    max(
                        row["coefficient_relative_error_max"]
                        for row in cell_coeff_metrics
                        if row["coefficient_relative_error_max"] is not None
                    )
                    if coeff_values
                    else None
                ),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    equation_path = output_dir / "wp_n1_structure_coefficient_metrics_by_equation.csv"
    cell_path = output_dir / "wp_n1_structure_coefficient_metrics_by_cell.csv"
    pd.DataFrame(equation_rows).to_csv(equation_path, index=False)
    pd.DataFrame(cell_rows).to_csv(cell_path, index=False)

    return {
        "equation_path": equation_path,
        "cell_path": cell_path,
        "n_records": len(records),
        "n_cells": len(cell_rows),
        "n_equation_rows": len(equation_rows),
    }


def main() -> int:
    args = parse_args()
    try:
        result = run(Path(args.input), Path(args.classification), Path(args.output_dir))
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {result['equation_path'].relative_to(REPO_ROOT)}")
    print(f"Wrote {result['cell_path'].relative_to(REPO_ROOT)}")
    print(f"Records read: {result['n_records']}")
    print(f"Cells written: {result['n_cells']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
