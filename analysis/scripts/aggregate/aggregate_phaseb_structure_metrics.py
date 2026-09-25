import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import sympy as sp


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import (  # noqa: E402
    aggregate_equation_metrics,
    check_required_columns,
    coefficient_metrics,
    is_missing_value,
    normalize_term_name,
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
from scripts.aggregate.aggregate_wp_n1_coefficient_metrics import (  # noqa: E402
    local_dict,
    model_coefficients,
    term_to_expr,
)


DEFAULT_REGISTRY = campaign_registry_path(REPO_ROOT, DEFAULT_CAMPAIGN_ID)
DEFAULT_CLASSIFICATION = campaign_data_dir(ANALYSIS_ROOT, DEFAULT_CAMPAIGN_ID) / "system_classification.csv"
DEFAULT_OUTPUT_DIR = campaign_data_dir(ANALYSIS_ROOT, DEFAULT_CAMPAIGN_ID)
PHASE_C_CAMPAIGN_ID = "paper1_phaseC_v1"


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


def parse_model_terms_json(value: Any) -> list[list[dict[str, Any]]]:
    if is_missing_value(value) or str(value).strip() == "":
        return []
    data = value
    if isinstance(value, str):
        try:
            data = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"model_terms is not valid JSON: {value}") from exc
    if not isinstance(data, list):
        raise ValueError("model_terms must be a list of equations")
    return data


def complete_found_coefficients(
    found_coefficients: dict[str, float] | None,
    true_coefficients: dict[str, float],
) -> dict[str, float] | None:
    """Restrict coefficient errors to true terms; missing true terms score as zero.

    The relative error is computed termwise over true terms only:
    abs(found - true) / abs(true). Extra found terms are structural errors, not
    coefficient-error terms.
    """
    if found_coefficients is None:
        return None
    normalized_found = {
        normalize_term_name(term): float(value) for term, value in found_coefficients.items()
    }
    return {
        normalize_term_name(term): normalized_found.get(normalize_term_name(term), 0.0)
        for term in true_coefficients
    }


def true_coefficients_for_phasec_terms(
    equation: str, dim: int, terms: list[str]
) -> dict[str, float]:
    symbols = [sp.Symbol(f"x_{idx}") for idx in range(dim)]
    expr = sp.expand(sp.parse_expr(equation, local_dict=local_dict(dim), evaluate=True))
    polynomial_expr = sum(
        term for term in expr.as_ordered_terms() if not term.atoms(sp.Function)
    )
    polynomial = sp.Poly(polynomial_expr, *symbols)
    coefficients: dict[str, float] = {}
    for term in terms:
        normalized = normalize_term_name(term)
        basis_expr = term_to_expr(normalized, dim)
        if normalized == "1":
            coefficient = polynomial.coeff_monomial(1)
        elif basis_expr.is_polynomial(*symbols):
            powers = basis_expr.as_powers_dict()
            monomial = 1
            for symbol in symbols:
                monomial *= symbol ** int(powers.get(symbol, 0))
            coefficient = polynomial.coeff_monomial(monomial)
        else:
            coefficient = expr.coeff(basis_expr)
        coefficients[normalized] = float(coefficient)
    return coefficients


def aggregate_coefficient_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values: list[float] = []
    max_value: float | None = None
    n_terms = 0
    for row in rows:
        n_row_terms = int(row["n_coefficient_terms"])
        n_terms += n_row_terms
        mean = row["coefficient_relative_error_mean"]
        maximum = row["coefficient_relative_error_max"]
        if mean is not None:
            values.extend([float(mean)] * n_row_terms)
        if maximum is not None:
            max_value = float(maximum) if max_value is None else max(max_value, float(maximum))
    return {
        "coefficient_relative_error_mean": (
            sum(values) / len(values) if values else None
        ),
        "coefficient_relative_error_max": max_value,
        "n_coefficient_terms": n_terms,
    }


def load_truth(path: Path) -> dict[int, dict[str, Any]]:
    df = pd.read_csv(path)
    check_required_columns(
        df,
        [
            "system_id",
            "dim",
            "equation_index",
            "equation",
            "representability",
            "matched_basis_terms",
        ],
    )
    truth: dict[int, dict[str, Any]] = {}
    for _, row in df.iterrows():
        system_id = int(row["system_id"])
        equation_index = int(row["equation_index"])
        system_truth = truth.setdefault(
            system_id,
            {
                "dim": int(row["dim"]),
                "representability": str(row["representability"]),
                "basis_name": None
                if "basis_name" not in df.columns or is_missing_value(row.get("basis_name"))
                else str(row["basis_name"]),
                "equations": {},
                "terms": {},
            },
        )
        system_truth["equations"][equation_index] = str(row["equation"])
        system_truth["terms"][equation_index] = parse_pipe_terms(row["matched_basis_terms"])
    return truth


def validate_phase_c_basis(registry: pd.DataFrame, truth_by_system: dict[int, dict[str, Any]]) -> None:
    check_required_columns(registry, ["basis_name"])
    registry_basis_values = sorted(
        {
            str(value).strip()
            for value in registry["basis_name"]
            if not is_missing_value(value) and str(value).strip()
        }
    )
    classification_basis_values = sorted(
        {
            str(system_truth["basis_name"]).strip()
            for system_truth in truth_by_system.values()
            if system_truth["basis_name"] is not None
            and str(system_truth["basis_name"]).strip()
        }
    )
    if not classification_basis_values:
        raise ValueError("Phase-C classification is missing required basis_name column")
    if len(registry_basis_values) != 1 or len(classification_basis_values) != 1:
        raise ValueError(
            "Phase-C basis check requires one registry basis and one classification basis; "
            f"got registry={registry_basis_values}, classification={classification_basis_values}"
        )
    if registry_basis_values[0] != classification_basis_values[0]:
        raise ValueError(
            "Phase-C registry basis_name does not match classification basis_name: "
            f"{registry_basis_values[0]!r} != {classification_basis_values[0]!r}"
        )


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
    is_phase_c = campaign_id == PHASE_C_CAMPAIGN_ID
    if is_phase_c:
        validate_phase_c_basis(registry, truth_by_system)
        check_required_columns(registry, ["model_terms"])

    equation_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    has_phase_c_match_definition = "exact_support_match_definition" in registry.columns
    if has_phase_c_match_definition:
        check_required_columns(
            registry,
            ["exact_support_match_raw", "exact_support_match_pruned", "pruned_support_terms"],
        )

    for _, row in registry.iterrows():
        system_id = int(row["system_id"])
        if system_id not in truth_by_system:
            raise ValueError(f"No classification truth for system_id={system_id}")
        found_by_equation = parse_support_terms_json(row["support_terms"])
        truth = truth_by_system[system_id]
        truth_equations = truth["terms"]
        if len(found_by_equation) != len(truth_equations):
            raise ValueError(
                f"Equation count mismatch for run_id={row['run_id']}: "
                f"found {len(found_by_equation)}, truth {len(truth_equations)}"
            )
        pruned_by_equation = (
            parse_support_terms_json(row["pruned_support_terms"])
            if has_phase_c_match_definition and "pruned_support_terms" in registry.columns
            else None
        )
        model_terms_by_equation = (
            parse_model_terms_json(row["model_terms"]) if is_phase_c else []
        )

        metrics_for_cell: list[dict[str, Any]] = []
        pruned_metrics_for_cell: list[dict[str, Any]] = []
        coeff_metrics_for_cell: list[dict[str, Any]] = []
        for equation_index in sorted(truth_equations):
            found_terms = found_by_equation[equation_index - 1]
            true_terms = truth_equations[equation_index]
            metrics = term_set_metrics(found_terms, true_terms)
            metrics_for_cell.append(metrics)
            coeff = {
                "coefficient_relative_error_mean": None,
                "coefficient_relative_error_max": None,
                "n_coefficient_terms": 0,
            }
            if is_phase_c and truth["representability"] == "exact":
                equation = truth["equations"][equation_index]
                true_coeffs = true_coefficients_for_phasec_terms(
                    equation, int(truth["dim"]), true_terms
                )
                found_coeffs = (
                    model_coefficients(model_terms_by_equation[equation_index - 1])
                    if model_terms_by_equation
                    else None
                )
                coeff = coefficient_metrics(
                    complete_found_coefficients(found_coeffs, true_coeffs),
                    true_coeffs,
                )
            coeff_metrics_for_cell.append(coeff)
            if pruned_by_equation is not None:
                pruned_metrics_for_cell.append(
                    term_set_metrics(pruned_by_equation[equation_index - 1], true_terms)
                )
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
                    **coeff,
                }
            )

        cell_metrics = aggregate_equation_metrics(metrics_for_cell)
        coeff_cell = aggregate_coefficient_metrics(coeff_metrics_for_cell)
        registry_compatible = registry_match_value(
            row["exact_support_match"], cell_metrics["exact_support_match"]
        )
        expected_registry = parse_boolish(row["exact_support_match"])
        matches_registry = registry_compatible == expected_registry
        cell_row = {
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
            **coeff_cell,
        }
        if has_phase_c_match_definition:
            if pruned_by_equation is None:
                raise ValueError(
                    "exact_support_match_definition is present but pruned_support_terms is missing"
                )
            pruned_cell_metrics = aggregate_equation_metrics(pruned_metrics_for_cell)
            raw_expected = parse_boolish(row["exact_support_match_raw"])
            pruned_expected = parse_boolish(row["exact_support_match_pruned"])
            raw_derived = registry_match_value(
                row["exact_support_match_raw"], cell_metrics["exact_support_match"]
            )
            pruned_derived = registry_match_value(
                row["exact_support_match_pruned"],
                pruned_cell_metrics["exact_support_match"],
            )
            cell_row.update(
                {
                    "structural_exact_support_match_raw": cell_metrics["exact_support_match"],
                    "structural_exact_support_match_pruned": pruned_cell_metrics[
                        "exact_support_match"
                    ],
                    "registry_exact_support_match_raw": raw_expected,
                    "derived_registry_exact_support_match_raw": raw_derived,
                    "registry_exact_support_match_raw_agrees": raw_derived == raw_expected,
                    "registry_exact_support_match_pruned": pruned_expected,
                    "derived_registry_exact_support_match_pruned": pruned_derived,
                    "registry_exact_support_match_pruned_agrees": (
                        pruned_derived == pruned_expected
                    ),
                }
            )
        cell_rows.append(cell_row)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_prefix = "phasec" if is_phase_c else "phaseb"
    equation_path = output_dir / f"{output_prefix}_structure_metrics_by_equation.csv"
    cell_path = output_dir / f"{output_prefix}_structure_metrics_by_cell.csv"
    discrepancy_path = output_dir / f"{output_prefix}_support_match_registry_discrepancies.csv"
    pd.DataFrame(equation_rows).to_csv(equation_path, index=False)
    cell_df = pd.DataFrame(cell_rows)
    cell_df.to_csv(cell_path, index=False)
    if has_phase_c_match_definition:
        discrepancy_mask = (
            ~cell_df["registry_exact_support_match_raw_agrees"]
            | ~cell_df["registry_exact_support_match_pruned_agrees"]
        )
    else:
        discrepancy_mask = ~cell_df["registry_exact_support_match_agrees"]
    cell_df.loc[discrepancy_mask].to_csv(discrepancy_path, index=False)

    agreements = sum(1 for row in cell_rows if row["registry_exact_support_match_agrees"])
    result = {
        "equation_path": equation_path,
        "cell_path": cell_path,
        "discrepancy_path": discrepancy_path,
        "n_cells": len(cell_rows),
        "n_equation_rows": len(equation_rows),
        "registry_agreements": agreements,
        "registry_disagreements": len(cell_rows) - agreements,
    }
    if has_phase_c_match_definition:
        raw_agreements = sum(
            1 for row in cell_rows if row["registry_exact_support_match_raw_agrees"]
        )
        pruned_agreements = sum(
            1 for row in cell_rows if row["registry_exact_support_match_pruned_agrees"]
        )
        result.update(
            {
                "registry_raw_agreements": raw_agreements,
                "registry_raw_disagreements": len(cell_rows) - raw_agreements,
                "registry_pruned_agreements": pruned_agreements,
                "registry_pruned_disagreements": len(cell_rows) - pruned_agreements,
            }
        )
    return result


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
    if "registry_pruned_agreements" in result:
        print(
            "Registry exact_support_match_raw agreements: "
            f"{result['registry_raw_agreements']}/{result['n_cells']}"
        )
        print(
            "Registry exact_support_match_pruned agreements: "
            f"{result['registry_pruned_agreements']}/{result['n_cells']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
