import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import (  # noqa: E402
    aggregate_equation_metrics,
    check_required_columns,
    is_missing_value,
    parse_pipe_terms,
    parse_support_terms_json,
    term_set_metrics,
)
from utils.campaign import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    campaign_data_dir,
    campaign_registry_path,
    require_single_campaign_id,
)


DEFAULT_REGISTRY = campaign_registry_path(REPO_ROOT, DEFAULT_CAMPAIGN_ID)
DEFAULT_CLASSIFICATION = campaign_data_dir(ANALYSIS_ROOT, DEFAULT_CAMPAIGN_ID) / "system_classification.csv"
DEFAULT_OUTPUT_DIR = campaign_data_dir(ANALYSIS_ROOT, DEFAULT_CAMPAIGN_ID)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute Phase-B structural term metrics from run_registry.csv."
    )
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument("--registry")
    parser.add_argument("--classification")
    parser.add_argument("--output-dir")
    return parser.parse_args()


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    data_dir = campaign_data_dir(ANALYSIS_ROOT, args.campaign)
    registry_path = (
        Path(args.registry).resolve()
        if args.registry
        else campaign_registry_path(REPO_ROOT, args.campaign)
    )
    classification_path = (
        Path(args.classification).resolve()
        if args.classification
        else data_dir / "system_classification.csv"
    )
    output_dir = Path(args.output_dir).resolve() if args.output_dir else data_dir
    return registry_path, classification_path, output_dir


def registry_match_value(value: Any, derived: bool) -> Any:
    if is_missing_value(value) or str(value).strip() == "":
        return None
    return derived


def parse_boolish(value: Any) -> bool | None:
    if is_missing_value(value) or str(value).strip() == "":
        return None
    if isinstance(value, bool):
        return value
    lowered = str(value).strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    raise ValueError(f"Cannot parse boolean value: {value}")


def load_truth(path: Path) -> dict[int, dict[int, list[str]]]:
    df = pd.read_csv(path)
    check_required_columns(df, ["system_id", "equation_index", "matched_basis_terms"])
    truth: dict[int, dict[int, list[str]]] = {}
    for _, row in df.iterrows():
        system_id = int(row["system_id"])
        equation_index = int(row["equation_index"])
        truth.setdefault(system_id, {})[equation_index] = parse_pipe_terms(
            row["matched_basis_terms"]
        )
    return truth


def run(
    registry_path: Path,
    classification_path: Path,
    output_dir: Path,
    campaign_id: str = DEFAULT_CAMPAIGN_ID,
) -> dict[str, Any]:
    registry = pd.read_csv(registry_path)
    check_required_columns(
        registry,
        [
            "run_id",
            "system_id",
            "support_terms",
            "exact_support_match",
            "experiment_id",
            "variant_slug",
            "seed",
            "initial_condition_set",
        ],
    )
    require_single_campaign_id(registry, campaign_id, "run_registry")
    truth_by_system = load_truth(classification_path)

    equation_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []

    for _, row in registry.iterrows():
        system_id = int(row["system_id"])
        if system_id not in truth_by_system:
            raise ValueError(f"No classification truth for system_id={system_id}")
        found_by_equation = parse_support_terms_json(row["support_terms"])
        truth_equations = truth_by_system[system_id]
        if len(found_by_equation) != len(truth_equations):
            raise ValueError(
                f"Equation count mismatch for run_id={row['run_id']}: "
                f"found {len(found_by_equation)}, truth {len(truth_equations)}"
            )

        metrics_for_cell: list[dict[str, Any]] = []
        for equation_index in sorted(truth_equations):
            found_terms = found_by_equation[equation_index - 1]
            true_terms = truth_equations[equation_index]
            metrics = term_set_metrics(found_terms, true_terms)
            metrics_for_cell.append(metrics)
            equation_rows.append(
                {
                    "run_id": row["run_id"],
                    "experiment_id": row["experiment_id"],
                    "system_id": system_id,
                    "variant_slug": row["variant_slug"],
                    "seed": row["seed"],
                    "initial_condition_set": row["initial_condition_set"],
                    "equation_index": equation_index,
                    **metrics,
                    "coefficient_relative_error_mean": None,
                    "coefficient_relative_error_max": None,
                    "n_coefficient_terms": 0,
                }
            )

        cell_metrics = aggregate_equation_metrics(metrics_for_cell)
        registry_compatible = registry_match_value(
            row["exact_support_match"], cell_metrics["exact_support_match"]
        )
        expected_registry = parse_boolish(row["exact_support_match"])
        matches_registry = registry_compatible == expected_registry
        cell_rows.append(
            {
                "run_id": row["run_id"],
                "experiment_id": row["experiment_id"],
                "system_id": system_id,
                "variant_slug": row["variant_slug"],
                "seed": row["seed"],
                "initial_condition_set": row["initial_condition_set"],
                **cell_metrics,
                "structural_exact_support_match": cell_metrics["exact_support_match"],
                "derived_registry_exact_support_match": registry_compatible,
                "registry_exact_support_match": expected_registry,
                "registry_exact_support_match_agrees": matches_registry,
                "coefficient_relative_error_mean": None,
                "coefficient_relative_error_max": None,
                "n_coefficient_terms": 0,
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    equation_path = output_dir / "phaseb_structure_metrics_by_equation.csv"
    cell_path = output_dir / "phaseb_structure_metrics_by_cell.csv"
    discrepancy_path = output_dir / "phaseb_support_match_registry_discrepancies.csv"
    pd.DataFrame(equation_rows).to_csv(equation_path, index=False)
    cell_df = pd.DataFrame(cell_rows)
    cell_df.to_csv(cell_path, index=False)
    cell_df.loc[~cell_df["registry_exact_support_match_agrees"]].to_csv(
        discrepancy_path, index=False
    )

    agreements = sum(1 for row in cell_rows if row["registry_exact_support_match_agrees"])
    return {
        "equation_path": equation_path,
        "cell_path": cell_path,
        "discrepancy_path": discrepancy_path,
        "n_cells": len(cell_rows),
        "n_equation_rows": len(equation_rows),
        "registry_agreements": agreements,
        "registry_disagreements": len(cell_rows) - agreements,
    }


def main() -> int:
    args = parse_args()
    registry_path, classification_path, output_dir = resolve_paths(args)
    try:
        result = run(registry_path, classification_path, output_dir, args.campaign)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {result['equation_path'].relative_to(REPO_ROOT)}")
    print(f"Wrote {result['cell_path'].relative_to(REPO_ROOT)}")
    print(f"Wrote {result['discrepancy_path'].relative_to(REPO_ROOT)}")
    print(f"Cells: {result['n_cells']}")
    print(
        "Registry exact_support_match agreements: "
        f"{result['registry_agreements']}/{result['n_cells']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
