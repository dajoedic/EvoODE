import json
import shutil
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate import run_phasec_noise_sindy_baselines as noise_sindy  # noqa: E402


REAL_EXPORT = REPO_ROOT / "outputs" / "stage1" / "data_export" / "index.csv"
REAL_CONFIG = REPO_ROOT / "analysis" / "configs" / "paper1_phaseC_sindy_baseline.json"
TEST_ROOT = REPO_ROOT / "outputs" / "wp_n34_pytest"


def fresh_workspace(name: str) -> Path:
    path = TEST_ROOT / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def copy_real_export_fixture(tmp_path: Path, n_rows: int = 1) -> Path:
    real = pd.read_csv(REAL_EXPORT).head(n_rows).copy()
    export_root = tmp_path / "data_export"
    export_root.mkdir()
    for _, row in real.iterrows():
        cell_dir = Path(str(row["cell_dir"]).replace("\\", "/"))
        source_dir = REAL_EXPORT.parent / cell_dir
        target_dir = export_root / cell_dir
        target_dir.mkdir(parents=True)
        for column in ["time_path", "state_path"]:
            rel = Path(str(row[column]).replace("\\", "/"))
            (target_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_dir / rel, target_dir / rel)
    path = export_root / "index.csv"
    real.to_csv(path, index=False)
    return path


def minimal_config(tmp_path: Path) -> Path:
    config = json.loads(REAL_CONFIG.read_text(encoding="utf-8"))
    config["polynomial_degrees"] = [2]
    config["thresholds"] = [0.01]
    config["trig_polynomial_degree"] = 2
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_read_index_cell_recomputes_hashes_from_real_export_fixture() -> None:
    tmp_path = fresh_workspace("hash_fixture")
    index_path = copy_real_export_fixture(tmp_path)
    index = noise_sindy.read_export_index(index_path)

    time, state = noise_sindy.read_index_cell(index_path.parent, index.iloc[0])

    assert time.shape == (512,)
    assert state.shape == (512, 1)
    assert int(index.iloc[0]["n_observed_points"]) == 512


def test_run_baselines_reports_sindy_and_weak_sindy_on_real_export_fixture() -> None:
    tmp_path = fresh_workspace("baseline_fixture")
    index_path = copy_real_export_fixture(tmp_path)
    output_dir = tmp_path / "out"

    paths = noise_sindy.run_baselines(minimal_config(tmp_path), index_path, output_dir, [])
    details = pd.read_csv(paths["details"])

    assert set(details["method"]) == {"sindy", "weak_sindy"}
    assert set(details["library_id"]) == {"poly_deg2_stlsq_0.01", "poly_deg2_sin_cos_stlsq_0.01"}
    assert len(details) == 4
    assert details["fit_status"].notna().all()
    assert details["observed_data_sha256"].str.contains("state_sha256").all()
    assert {"sindy_structure_precision_pruned", "sindy_structure_recall_pruned", "sindy_structure_f1_pruned"} <= set(details.columns)
    assert details["sindy_structure_metrics_exact_system"].all()
    assert details["sindy_structure_f1_pruned"].notna().all()
    assert (pd.read_csv(paths["export_checks"])["hash_verified"]).all()


def test_stage_report_glob_matches_available_real_stage_reports() -> None:
    tmp_path = fresh_workspace("stage_report_glob")
    index_path = copy_real_export_fixture(tmp_path, n_rows=4)
    output_dir = tmp_path / "out"

    paths = noise_sindy.run_baselines(
        minimal_config(tmp_path),
        index_path,
        output_dir,
        noise_sindy.expand_stage_report_paths(["outputs/stage1/*/report/robustness_stage_report.csv"]),
    )
    comparison = pd.read_csv(paths["comparison_with_robustness_stage_report"])

    matched = comparison.loc[comparison["evogrow_comparison_status"] == "matched"]
    matched_conditions = {
        (round(float(row.noise_sigma), 2), float(row.subsample_rho))
        for row in matched.itertuples(index=False)
    }
    assert (0.01, 0.0) in matched_conditions
    assert (0.05, 0.5) in matched_conditions
    assert "missing_in_stage_report" in set(comparison["evogrow_comparison_status"])


def test_control_hash_check_matches_c4_reference_for_real_control_export() -> None:
    tmp_path = fresh_workspace("control_hash_check")

    frame, passed = noise_sindy.compare_control_hashes(
        REPO_ROOT / "outputs" / "wp_n34_control_export" / "index.csv",
        tmp_path,
    )

    assert passed
    assert len(frame) == 4
    assert frame["time_hash_matches_c4"].all()
    assert frame["state_hash_matches_c4"].all()
