import sys
import shutil
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_phasec_cap_ablation import (  # noqa: E402
    CAPPED_VARIANT,
    UNCAPPED_VARIANT,
    build_pairs,
    main,
    validate_registry,
)


def base_row(system_id: int, seed: int, ic: int, variant_slug: str) -> dict[str, object]:
    is_capped = variant_slug == CAPPED_VARIANT
    return {
        "experiment_id": "paper1_phaseC_v1",
        "variant_slug": variant_slug,
        "system_id": system_id,
        "system_name": f"system_{system_id}",
        "system_dim": 2,
        "system_representability": "exact",
        "system_expected_stage": 4,
        "seed": seed,
        "initial_condition_set": ic,
        "loss": 0.01 if is_capped else 0.02,
        "r2": 0.98 if is_capped else 0.99,
        "exact_support_match_raw": is_capped,
        "exact_support_match_pruned": True,
        "structural_f1": 0.90 if is_capped else 0.95,
        "term_precision": 0.91 if is_capped else 0.96,
        "term_recall": 0.92 if is_capped else 0.97,
        "coefficient_relative_error_mean": 0.2 if is_capped else 0.1,
        "total_parameter_fits": 10 if is_capped else 20,
        "total_parameter_fit_attempts": 11 if is_capped else 22,
        "total_loss_evals": 100 if is_capped else 300,
        "total_ode_solves": 80 if is_capped else 200,
        "final_stage": 3 if is_capped else 5,
        "executed_levels": 12 if is_capped else 30,
        "basis_name": "canonical",
        "n_levels": 30,
        "trajectory_hash": "abc123",
    }


def paired_rows() -> list[dict[str, object]]:
    return [
        base_row(1, 101, 1, CAPPED_VARIANT),
        base_row(1, 101, 1, UNCAPPED_VARIANT),
        base_row(2, 101, 1, CAPPED_VARIANT),
        base_row(2, 101, 1, UNCAPPED_VARIANT),
    ]


def validated_pairs(rows: list[dict[str, object]], expected_pairs: int = 2) -> pd.DataFrame:
    registry = validate_registry(pd.DataFrame(rows), "paper1_phaseC_v1")
    return build_pairs(registry, expected_pairs)


def test_complete_pairing_over_fixture_cells_succeeds() -> None:
    pairs = validated_pairs(paired_rows())

    assert len(pairs) == 2
    assert set(pairs["executed_levels_saving_uncapped_minus_capped"]) == {18.0}
    assert "n_levels_capped" not in set(pairs.columns)


def test_missing_countercell_aborts() -> None:
    rows = paired_rows()[:-1]
    registry = validate_registry(pd.DataFrame(rows), "paper1_phaseC_v1")

    try:
        build_pairs(registry, 2)
    except ValueError as exc:
        assert "incomplete or duplicate pair" in str(exc)
        assert "system_id=2" in str(exc)
    else:
        raise AssertionError("Expected missing countercell to fail")


def test_unexpected_pair_mismatch_names_column_and_values() -> None:
    rows = paired_rows()
    rows[1]["basis_name"] = "different_basis"

    try:
        validated_pairs(rows)
    except ValueError as exc:
        message = str(exc)
        assert "basis_name" in message
        assert "canonical" in message
        assert "different_basis" in message
    else:
        raise AssertionError("Expected unexpected pair mismatch to fail")


def test_unknown_mismatching_column_is_not_silently_allowed() -> None:
    rows = paired_rows()
    rows[0]["new_future_field"] = "left"
    rows[1]["new_future_field"] = "right"
    rows[2]["new_future_field"] = "same"
    rows[3]["new_future_field"] = "same"

    try:
        validated_pairs(rows)
    except ValueError as exc:
        message = str(exc)
        assert "new_future_field" in message
        assert "left" in message
        assert "right" in message
    else:
        raise AssertionError("Expected unknown mismatching column to fail")


def test_allowed_arm_bookkeeping_and_cap_switch_differences_pass() -> None:
    rows = [
        base_row(1, 101, 1, CAPPED_VARIANT),
        base_row(1, 101, 1, UNCAPPED_VARIANT),
    ]
    for row in rows:
        row.update(
            {
                "loss": 0.01,
                "r2": 0.98,
                "exact_support_match_raw": True,
                "structural_f1": 0.90,
                "term_precision": 0.91,
                "term_recall": 0.92,
                "coefficient_relative_error_mean": 0.2,
                "total_parameter_fits": 10,
                "total_parameter_fit_attempts": 11,
                "total_loss_evals": 100,
                "total_ode_solves": 80,
                "final_stage": 3,
                "executed_levels": 12,
            }
        )
    rows[0].update(
        {
            "campaign_manifest_index": 10,
            "stage_caps": "[3, 3]",
            "stage_cap_policy_active": True,
        }
    )
    rows[1].update(
        {
            "campaign_manifest_index": 11,
            "stage_caps": "",
            "stage_cap_policy_active": False,
        }
    )

    pairs = validated_pairs(rows, expected_pairs=1)

    assert len(pairs) == 1
    assert pairs["executed_levels_saving_uncapped_minus_capped"].tolist() == [0.0]


def test_wrong_arm_label_aborts() -> None:
    rows = paired_rows()
    rows[0]["variant_slug"] = "evogrow_v2_2_stage_capped_pretune_on"

    try:
        validate_registry(pd.DataFrame(rows), "paper1_phaseC_v1")
    except ValueError as exc:
        assert "only accepts the capped/uncapped" in str(exc)
        assert "pretune_on" in str(exc)
    else:
        raise AssertionError("Expected wrong arm label to fail")


def test_missing_executed_levels_column_aborts_clearly() -> None:
    rows = paired_rows()
    df = pd.DataFrame(rows).drop(columns=["executed_levels"])

    try:
        validate_registry(df, "paper1_phaseC_v1")
    except ValueError as exc:
        message = str(exc)
        assert "executed-level count column" in message
        assert "executed_levels" in message
        assert "do not substitute n_levels" in message
    else:
        raise AssertionError("Expected missing executed_levels to fail")


def test_cli_writes_paired_csv_and_summary(monkeypatch, capsys) -> None:
    work_dir = REPO_ROOT / ".pytest_tmp_phasec_cap_ablation"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()
    input_path = work_dir / "registry.csv"
    output_dir = work_dir / "out"
    pd.DataFrame(paired_rows()).to_csv(input_path, index=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "aggregate_phasec_cap_ablation.py",
            "--campaign",
            "paper1_phaseC_v1",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
            "--expected-total-pairs",
            "2",
            "--permutations",
            "9",
            "--bootstrap-replicates",
            "9",
        ],
    )

    assert main() == 0
    assert (output_dir / "phasec_cap_ablation_paired.csv").is_file()
    assert (output_dir / "phasec_cap_ablation_summary.json").is_file()
    assert "Pairs: 2" in capsys.readouterr().out
    shutil.rmtree(work_dir)
