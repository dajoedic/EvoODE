import sys
from pathlib import Path


ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import (  # noqa: E402
    coefficient_metrics,
    normalize_term_name,
    term_set_metrics,
)


def test_normalize_term_name_canonicalizes_equivalent_spellings() -> None:
    assert normalize_term_name(" u1 ** 2 ") == "u1^2"
    assert normalize_term_name("u2*u1") == "u1*u2"
    assert normalize_term_name("sin( u3 )") == "sin(u3)"
    assert normalize_term_name("1") == "1"


def test_term_set_metrics_counts_missing_true_term() -> None:
    metrics = term_set_metrics(["u1"], ["u1", "u1^2"])

    assert metrics["n_missing_true_terms"] == 1
    assert metrics["n_extra_found_terms"] == 0
    assert metrics["term_precision"] == 1.0
    assert metrics["term_recall"] == 0.5
    assert metrics["exact_support_match"] is False


def test_term_set_metrics_counts_extra_found_term() -> None:
    metrics = term_set_metrics(["u1", "cos(u1)"], ["u1"])

    assert metrics["n_missing_true_terms"] == 0
    assert metrics["n_extra_found_terms"] == 1
    assert metrics["term_precision"] == 0.5
    assert metrics["term_recall"] == 1.0
    assert metrics["exact_support_match"] is False


def test_term_set_metrics_handles_empty_found_set() -> None:
    metrics = term_set_metrics([], ["u1"])

    assert metrics["n_found_terms"] == 0
    assert metrics["n_true_terms"] == 1
    assert metrics["term_precision"] == 0.0
    assert metrics["term_recall"] == 0.0
    assert metrics["structural_f1"] == 0.0


def test_coefficient_metrics_without_coefficients_returns_nulls() -> None:
    metrics = coefficient_metrics(None, {"u1": 0.23})

    assert metrics["n_coefficient_terms"] == 0
    assert metrics["coefficient_relative_error_mean"] is None
    assert metrics["coefficient_relative_error_max"] is None
    assert metrics["coefficient_errors"] is None


def test_coefficient_metrics_rejects_zero_true_coefficient() -> None:
    try:
        coefficient_metrics({"u1": 1.0}, {"u1": 0.0})
    except ValueError as exc:
        assert "zero true coefficient" in str(exc)
    else:
        raise AssertionError("Expected ValueError for zero true coefficient")
