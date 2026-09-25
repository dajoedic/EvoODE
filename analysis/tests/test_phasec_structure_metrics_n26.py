import csv
import json
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_phaseb_structure_metrics import run as aggregate_run  # noqa: E402
from scripts.aggregate.build_phasec_system_classification import (  # noqa: E402
    DEFAULT_PHASE_B_CLASSIFICATION,
    DEFAULT_SUPPORT,
    build_rows,
    load_support,
)


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def phasec_classification_row(basis_name: str = "staged_polynomial_basis_with_constant") -> dict:
    return {
        "system_id": 1,
        "dim": 1,
        "description": "RC-circuit (charging capacitor)",
        "equation_index": 1,
        "equation": "0.303030303030303 - 0.360750360750361*x_0",
        "representability": "exact",
        "expected_stage": 1,
        "expected_eq_stage": 1,
        "matched_basis_terms": "1|u1",
        "unmatched_terms": "",
        "gap_reason": "",
        "source": "fixture",
        "substituted_sets_identical": "true",
        "n_substituted_sets": 1,
        "variable_mapping": "x_0->u1",
        "basis_name": basis_name,
    }


def phasec_registry_row(raw_terms: list[list[str]], pruned_terms: list[list[str]]) -> dict:
    raw_match = raw_terms == [["1", "u1"]]
    pruned_match = pruned_terms == [["1", "u1"]]
    return {
        "run_id": "fixture_run",
        "experiment_id": "paper1_phaseC_v1",
        "system_id": 1,
        "support_terms": json.dumps(raw_terms),
        "pruned_support_terms": json.dumps(pruned_terms),
        "exact_support_match": str(pruned_match),
        "exact_support_match_raw": str(raw_match),
        "exact_support_match_pruned": str(pruned_match),
        "exact_support_match_definition": "pruned_support_terms_exact_match",
        "experiment_id": "paper1_phaseC_v1",
        "variant_slug": "evogrow_v2_2_stage_capped",
        "seed": 42,
        "initial_condition_set": 1,
        "basis_name": "staged_polynomial_basis_with_constant",
        "model_terms": json.dumps(
            [[{"term": "1", "term_index": 1, "coefficient": 0.303030303030303}]]
        ),
    }


def test_phasec_truth_from_support_has_30_exact_systems_and_new_constant_terms() -> None:
    _, support_by_system = load_support(DEFAULT_SUPPORT)
    rows = build_rows(pd.read_csv(DEFAULT_PHASE_B_CLASSIFICATION), support_by_system)

    exact = rows[rows["representability"] == "exact"]
    assert exact["system_id"].nunique() == 30

    newly_exact = {1, 5, 9, 17, 23, 43, 52, 57, 58, 59}
    for system_id in newly_exact:
        system_rows = exact[exact["system_id"] == system_id]
        assert not system_rows.empty
        assert any(
            "1" in set(str(value).split("|"))
            for value in system_rows["matched_basis_terms"]
        )


def test_phasec_expected_stage_matches_dryrun_registry_records() -> None:
    _, support_by_system = load_support(DEFAULT_SUPPORT)
    rows = build_rows(pd.read_csv(DEFAULT_PHASE_B_CLASSIFICATION), support_by_system)
    generated = (
        rows[rows["representability"] == "exact"]
        .drop_duplicates("system_id")
        .set_index("system_id")["expected_stage"]
    )
    registry = pd.read_csv(REPO_ROOT / "outputs" / "phase_c_dryrun_2026-09-25" / "run_registry.csv")
    exact_registry = registry[registry["system_representability"] == "exact"]

    for _, row in exact_registry.drop_duplicates("system_id").iterrows():
        assert int(generated[int(row["system_id"])]) == int(row["system_expected_stage"])


def test_phasec_aggregation_uses_pruned_registry_match_and_phasec_filenames(tmp_path: Path) -> None:
    classification_path = tmp_path / "classification.csv"
    registry_path = tmp_path / "registry.csv"
    output_dir = tmp_path / "out"
    write_csv(classification_path, [phasec_classification_row()])
    write_csv(
        registry_path,
        [phasec_registry_row([["1", "u1", "u1^2"]], [["1", "u1"]])],
    )

    result = aggregate_run(
        registry_path,
        classification_path,
        output_dir,
        campaign_id="paper1_phaseC_v1",
    )

    assert result["cell_path"].name == "phasec_structure_metrics_by_cell.csv"
    assert result["equation_path"].name == "phasec_structure_metrics_by_equation.csv"
    assert result["registry_raw_disagreements"] == 0
    assert result["registry_pruned_disagreements"] == 0
    discrepancies = pd.read_csv(result["discrepancy_path"])
    assert discrepancies.empty
    cells = pd.read_csv(result["cell_path"])
    assert cells.loc[0, "structural_exact_support_match_raw"] == False
    assert cells.loc[0, "structural_exact_support_match_pruned"] == True
    assert cells.loc[0, "registry_exact_support_match_pruned_agrees"] == True


def test_phasec_coefficient_error_counts_missing_true_terms_as_zero(tmp_path: Path) -> None:
    classification_path = tmp_path / "classification.csv"
    registry_path = tmp_path / "registry.csv"
    output_dir = tmp_path / "out"
    write_csv(classification_path, [phasec_classification_row()])
    write_csv(registry_path, [phasec_registry_row([["1"]], [["1"]])])

    aggregate_run(
        registry_path,
        classification_path,
        output_dir,
        campaign_id="paper1_phaseC_v1",
    )

    equations = pd.read_csv(output_dir / "phasec_structure_metrics_by_equation.csv")
    assert equations.loc[0, "n_coefficient_terms"] == 2
    assert equations.loc[0, "coefficient_relative_error_mean"] == 0.5
    assert equations.loc[0, "coefficient_relative_error_max"] == 1.0


def test_phasec_basis_mismatch_aborts(tmp_path: Path) -> None:
    classification_path = tmp_path / "classification.csv"
    registry_path = tmp_path / "registry.csv"
    output_dir = tmp_path / "out"
    write_csv(classification_path, [phasec_classification_row("old_basis")])
    write_csv(registry_path, [phasec_registry_row([["1", "u1"]], [["1", "u1"]])])

    try:
        aggregate_run(
            registry_path,
            classification_path,
            output_dir,
            campaign_id="paper1_phaseC_v1",
        )
    except ValueError as exc:
        assert "basis_name" in str(exc)
    else:
        raise AssertionError("Expected Phase-C basis mismatch to abort")
