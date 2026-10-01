import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.summarize_wp_s04_stage_cap_noise import (  # noqa: E402
    load_detail,
    main,
    summarize_f1,
    summarize_f2,
    summarize_f4,
)


def real_record_derived_detail_row(**updates: object) -> dict[str, object]:
    row: dict[str, object] = {
        # Derived from outputs/phase_c_campaign_221a3a7/history.jsonl first capped seed-42 row:
        # system_id=1, IC=1, stage_caps=[null], condition=capped, basis with constant.
        "system_id": 1,
        "system_name": "RC-circuit (charging capacitor)",
        "dimension": 1,
        "equation_index": 1,
        "initial_condition_set": 1,
        "sigma": 0.0,
        "rho": 0.0,
        "realization": 0,
        "n_observed_points": 512,
        "cap": "nothing",
        "clean_cap": "nothing",
        "reference_clean_cap": "nothing",
        "cap_change_class": "same",
        "required_stage": 1,
        "truncates_true_terms": False,
        "rebuild_cap_matches_estimate": True,
        "clean_reference_matches_c1": True,
        "residual_stage_1": 1.0e-8,
        "residual_stage_2": 8.0e-9,
        "residual_stage_3": 7.0e-9,
        "residual_stage_4": 7.0e-9,
        "residual_stage_5": 7.0e-9,
        "floor_stage_1": 1.0e-10,
        "floor_stage_2": 1.0e-10,
        "floor_stage_3": 1.0e-10,
        "floor_stage_4": 1.0e-10,
        "floor_stage_5": 1.0e-10,
        "usable_splits_stage_1": 4,
        "usable_splits_stage_2": 4,
        "usable_splits_stage_3": 0,
        "usable_splits_stage_4": 4,
        "usable_splits_stage_5": 4,
        "split_decisions_json": "[]",
        "f4_true_sigma_prediction": 0.0,
        "f4_estimated_sigma_prediction": 1.0e-9,
        "f4_measured_derivative_error": 2.0e-9,
        "f4_true_stage_residual": 1.0e-8,
        "f4_true_pred_to_measured_deriv": 0.0,
        "f4_est_pred_to_measured_deriv": 0.5,
        "f4_true_pred_to_true_stage_residual": 0.0,
        "f4_est_pred_to_true_stage_residual": 0.1,
    }
    row.update(updates)
    return row


def fixture_rows() -> list[dict[str, object]]:
    return [
        real_record_derived_detail_row(),
        real_record_derived_detail_row(
            sigma=0.01,
            rho=0.0,
            realization=1,
            cap="1",
            cap_change_class="from_nothing",
            f4_true_sigma_prediction=3.0e-9,
            f4_estimated_sigma_prediction=4.0e-9,
            f4_true_pred_to_measured_deriv=1.5,
            f4_est_pred_to_measured_deriv=2.0,
            f4_true_pred_to_true_stage_residual=0.3,
            f4_est_pred_to_true_stage_residual=0.4,
        ),
        real_record_derived_detail_row(
            sigma=0.02,
            rho=0.5,
            realization=1,
            cap="nothing",
            clean_cap="1",
            reference_clean_cap="1",
            cap_change_class="to_nothing",
            required_stage=2,
            truncates_true_terms=False,
            f4_true_sigma_prediction=5.0e-9,
            f4_estimated_sigma_prediction=6.0e-9,
            f4_true_pred_to_measured_deriv=2.5,
            f4_est_pred_to_measured_deriv=3.0,
            f4_true_pred_to_true_stage_residual=0.5,
            f4_est_pred_to_true_stage_residual=0.6,
        ),
    ]


def test_fixture_summary_answers_f1_f2_f4(tmp_path: Path) -> None:
    input_path = tmp_path / "detail.csv"
    pd.DataFrame(fixture_rows()).to_csv(input_path, index=False)

    detail = load_detail(input_path)
    f1 = summarize_f1(detail)
    f2 = summarize_f2(detail)
    f4_ratios, f4_levels = summarize_f4(detail)

    assert int(f1["truncated_true_terms"].sum()) == 0
    assert set(f2["cap_change_class"]) == {"same", "from_nothing", "to_nothing"}
    assert set(f4_ratios["metric"]) == {
        "f4_true_pred_to_measured_deriv",
        "f4_est_pred_to_measured_deriv",
        "f4_true_pred_to_true_stage_residual",
        "f4_est_pred_to_true_stage_residual",
    }
    assert set(f4_levels["metric"]) >= {"f4_measured_derivative_error", "f4_true_stage_residual"}


def test_control_mismatch_aborts(tmp_path: Path) -> None:
    input_path = tmp_path / "detail.csv"
    rows = fixture_rows()
    rows[0]["rebuild_cap_matches_estimate"] = False
    pd.DataFrame(rows).to_csv(input_path, index=False)

    try:
        load_detail(input_path)
    except ValueError as exc:
        assert "rebuilt cap" in str(exc)
    else:
        raise AssertionError("Expected rebuild mismatch to abort")


def test_cli_writes_summary_tables(monkeypatch, tmp_path: Path, capsys) -> None:
    input_path = tmp_path / "detail.csv"
    output_dir = tmp_path / "out"
    pd.DataFrame(fixture_rows()).to_csv(input_path, index=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "summarize_wp_s04_stage_cap_noise.py",
            "--input",
            str(input_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert main() == 0
    assert (output_dir / "f1_safety.csv").is_file()
    assert (output_dir / "f4_ratio_quantiles.csv").is_file()
    assert (output_dir / "summary.md").is_file()
    assert "Rows: 3" in capsys.readouterr().out
