import pandas as pd
import json
import math
import re
from collections.abc import Iterable, Sequence
from typing import Any


def filter_valid_runs(df: pd.DataFrame) -> pd.DataFrame:
    if "loss" not in df.columns:
        raise ValueError("DataFrame is missing required column: loss")

    return df.loc[df["loss"].notna()].copy()


def check_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        missing_columns = ", ".join(missing)
        raise ValueError(f"DataFrame is missing required columns: {missing_columns}")


_POWER_RE = re.compile(r"^u(\d+)\^(\d+)$")
_LINEAR_RE = re.compile(r"^u(\d+)$")
_TRIG_RE = re.compile(r"^(sin|cos)\(u(\d+)\)$")


def is_missing_value(value: Any) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value))


def normalize_term_name(term: Any) -> str:
    """Return the canonical term spelling used by EvoODE basis names."""
    if is_missing_value(term):
        raise ValueError("Term name is missing")
    normalized = str(term).strip()
    if not normalized:
        raise ValueError("Term name is empty")
    normalized = normalized.replace(" ", "").replace("**", "^")

    if normalized == "1":
        return normalized
    if _LINEAR_RE.fullmatch(normalized):
        return normalized
    if _POWER_RE.fullmatch(normalized):
        return normalized
    trig = _TRIG_RE.fullmatch(normalized)
    if trig:
        return f"{trig.group(1)}(u{int(trig.group(2))})"

    factors = normalized.split("*")
    if len(factors) == 2 and all(_LINEAR_RE.fullmatch(factor) for factor in factors):
        indices = sorted(int(factor[1:]) for factor in factors)
        return f"u{indices[0]}*u{indices[1]}"

    return normalized


def parse_pipe_terms(value: Any) -> list[str]:
    if is_missing_value(value) or str(value).strip() == "":
        return []
    return [normalize_term_name(term) for term in str(value).split("|") if term.strip()]


def parse_support_terms_json(value: Any) -> list[list[str]]:
    if is_missing_value(value) or str(value).strip() == "":
        return []
    data = value
    if isinstance(value, str):
        try:
            data = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"support_terms is not valid JSON: {value}") from exc
    if not isinstance(data, list):
        raise ValueError("support_terms must be a list of equations")

    equations: list[list[str]] = []
    for eq_index, terms in enumerate(data, start=1):
        if terms is None:
            equations.append([])
            continue
        if not isinstance(terms, list):
            raise ValueError(f"support_terms equation {eq_index} must be a list")
        equations.append([normalize_term_name(term) for term in terms])
    return equations


def term_set_metrics(found_terms: Iterable[Any], true_terms: Iterable[Any]) -> dict[str, Any]:
    found = {normalize_term_name(term) for term in found_terms}
    truth = {normalize_term_name(term) for term in true_terms}
    true_positive = len(found & truth)
    false_positive = len(found - truth)
    false_negative = len(truth - found)

    precision = true_positive / len(found) if found else (1.0 if not truth else 0.0)
    recall = true_positive / len(truth) if truth else (1.0 if not found else 0.0)
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall > 0.0
        else 0.0
    )

    return {
        "n_found_terms": len(found),
        "n_true_terms": len(truth),
        "n_true_positive_terms": true_positive,
        "n_missing_true_terms": false_negative,
        "n_extra_found_terms": false_positive,
        "term_precision": precision,
        "term_recall": recall,
        "structural_f1": f1,
        "exact_support_match": found == truth,
        "missing_true_terms": "|".join(sorted(truth - found)),
        "extra_found_terms": "|".join(sorted(found - truth)),
    }


def equationwise_support_match(
    found_equations: Sequence[Iterable[Any]],
    true_equations: Sequence[Iterable[Any]],
) -> bool:
    """Return whether every equation has the same normalized support-term set.

    Equations are compared by index; equation order is not permuted.
    """
    if len(found_equations) != len(true_equations):
        return False
    return all(
        {normalize_term_name(term) for term in found_terms}
        == {normalize_term_name(term) for term in true_terms}
        for found_terms, true_terms in zip(found_equations, true_equations)
    )


def aggregate_equation_metrics(equation_metrics: Sequence[dict[str, Any]]) -> dict[str, Any]:
    if not equation_metrics:
        raise ValueError("At least one equation metric row is required")

    n_equations = len(equation_metrics)
    macro_precision = sum(row["term_precision"] for row in equation_metrics) / n_equations
    macro_recall = sum(row["term_recall"] for row in equation_metrics) / n_equations
    macro_f1 = sum(row["structural_f1"] for row in equation_metrics) / n_equations

    total_found = sum(row["n_found_terms"] for row in equation_metrics)
    total_truth = sum(row["n_true_terms"] for row in equation_metrics)
    total_tp = sum(row["n_true_positive_terms"] for row in equation_metrics)
    total_missing = sum(row["n_missing_true_terms"] for row in equation_metrics)
    total_extra = sum(row["n_extra_found_terms"] for row in equation_metrics)

    micro_precision = total_tp / total_found if total_found else (1.0 if total_truth == 0 else 0.0)
    micro_recall = total_tp / total_truth if total_truth else (1.0 if total_found == 0 else 0.0)
    micro_f1 = (
        2.0 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if micro_precision + micro_recall > 0.0
        else 0.0
    )

    return {
        "n_equations": n_equations,
        "n_found_terms_micro": total_found,
        "n_true_terms_micro": total_truth,
        "n_true_positive_terms_micro": total_tp,
        "n_missing_true_terms": total_missing,
        "n_extra_found_terms": total_extra,
        "term_precision_macro": macro_precision,
        "term_recall_macro": macro_recall,
        "structural_f1_macro": macro_f1,
        "term_precision_micro": micro_precision,
        "term_recall_micro": micro_recall,
        "structural_f1_micro": micro_f1,
        "exact_support_match": all(row["exact_support_match"] for row in equation_metrics),
    }


def coefficient_metrics(
    found_coefficients: dict[str, float] | None,
    true_coefficients: dict[str, float] | None,
) -> dict[str, Any]:
    if found_coefficients is None or true_coefficients is None:
        return {
            "n_coefficient_terms": 0,
            "coefficient_relative_error_mean": None,
            "coefficient_relative_error_max": None,
            "coefficient_errors": None,
        }

    found = {normalize_term_name(term): float(value) for term, value in found_coefficients.items()}
    truth = {normalize_term_name(term): float(value) for term, value in true_coefficients.items()}
    shared = sorted(set(found) & set(truth))
    errors: dict[str, float] = {}
    for term in shared:
        denominator = abs(truth[term])
        if denominator == 0.0:
            raise ValueError(f"Cannot compute relative coefficient error for zero true coefficient: {term}")
        errors[term] = abs(found[term] - truth[term]) / denominator

    if not errors:
        return {
            "n_coefficient_terms": 0,
            "coefficient_relative_error_mean": None,
            "coefficient_relative_error_max": None,
            "coefficient_errors": json.dumps({}, sort_keys=True),
        }

    values = list(errors.values())
    return {
        "n_coefficient_terms": len(values),
        "coefficient_relative_error_mean": sum(values) / len(values),
        "coefficient_relative_error_max": max(values),
        "coefficient_errors": json.dumps(errors, sort_keys=True, separators=(",", ":")),
    }
