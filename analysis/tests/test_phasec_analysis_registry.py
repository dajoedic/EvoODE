import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate import build_phasec_analysis_registry as builder  # noqa: E402


def registry_rows() -> list[dict[str, object]]:
    base = {
        "experiment_id": "paper1_phaseC_v1",
        "system_name": "system",
        "system_dim": 1,
        "system_representability": "exact",
        "seed": 42,
        "initial_condition_set": 1,
        "use_pretuning": False,
    }
    return [
        {**base, "run_id": "c1", "system_id": 1, "variant_slug": builder.C1_VARIANT},
        {**base, "run_id": "c2", "system_id": 1, "variant_slug": builder.C2_VARIANT},
        {**base, "run_id": "c3", "system_id": 1, "variant_slug": builder.C3_VARIANT, "use_pretuning": True},
    ]


def structure_rows() -> list[dict[str, object]]:
    rows = []
    for run_id in ["c1", "c2", "c3"]:
        rows.append(
            {
                "run_id": run_id,
                "experiment_id": "paper1_phaseC_v1",
                "structural_f1_micro": 0.8,
                "structural_f1_macro": 0.7,
                "term_precision_micro": 0.9,
                "term_precision_macro": 0.85,
                "term_recall_micro": 0.6,
                "term_recall_macro": 0.55,
                "coefficient_relative_error_mean": 0.1,
                "coefficient_relative_error_max": 0.2,
                "n_coefficient_terms": 1,
                "n_equations": 1,
                "n_found_terms_micro": 1,
                "n_true_terms_micro": 1,
                "n_true_positive_terms_micro": 1,
                "n_missing_true_terms": 0,
                "n_extra_found_terms": 0,
            }
        )
    return rows


def test_join_requires_one_metric_row_per_run_id() -> None:
    registry = pd.DataFrame(registry_rows())
    metrics = pd.DataFrame(structure_rows()[:-1])

    try:
        builder.join_registry(registry, metrics)
    except ValueError as exc:
        assert "missing_metrics" in str(exc)
        assert "c3" in str(exc)
    else:
        raise AssertionError("missing structure metric row should fail")


def test_duplicate_metric_run_id_aborts() -> None:
    metrics = pd.DataFrame(structure_rows() + [structure_rows()[0]])

    try:
        builder.assert_unique_run_ids(metrics, "structure_metrics")
    except ValueError as exc:
        assert "duplicate run_id" in str(exc)
        assert "c1" in str(exc)
    else:
        raise AssertionError("duplicate run_id should fail")


def test_micro_aliases_and_subsets_use_pretuning() -> None:
    joined = builder.join_registry(pd.DataFrame(registry_rows()), pd.DataFrame(structure_rows()))

    assert joined.loc[joined["run_id"] == "c1", "structural_f1"].iloc[0] == 0.8
    assert set(builder.subset_c1_c2(joined)["run_id"]) == {"c1", "c2"}
    assert set(builder.subset_c1(joined)["run_id"]) == {"c1"}
    assert set(builder.subset_pretuning(joined)["run_id"]) == {"c1", "c3"}
