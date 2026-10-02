import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baselines import harness
from baselines import run_odeformer_noise as noise_odeformer


REAL_EXPORT = REPO_ROOT / "outputs" / "stage1" / "data_export" / "index.csv"
TEST_ROOT = REPO_ROOT / "outputs" / "wp_n38_pytest"


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


class IdentityAdapter:
    actual_hash = "fake"

    def __init__(self, _config):
        pass

    def close(self):
        pass

    def fit_best_candidate(self, _fit_cell):
        return "x_0", "x_0", "x_0", ["x_0"]

    def integrate_expression(self, cell, _expression):
        return cell.state.copy()

    def timeout_count_fields(self):
        return {}

    def timeout_phase(self, _name):
        class Manager:
            def __enter__(self):
                return None

            def __exit__(self, *_args):
                return False

        return Manager()


def one_config(tmp_path: Path) -> Path:
    config = {
        "benchmark_path": "benchmarks/data/strogatz_extended.json",
        "trajectory_export_dir": "unused",
        "output_dir": str(tmp_path / "out"),
        "environment_id": "reference",
        "timeout_seconds_per_cell": None,
        "odeformer_configs": ["baselines/configs/odeformer_beam10_noopt.json"],
    }
    path = tmp_path / "odeformer_noise_config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def test_read_index_cell_reuses_noise_sindy_hash_validation() -> None:
    tmp_path = fresh_workspace("hash_fixture")
    index_path = copy_real_export_fixture(tmp_path)
    index = noise_odeformer.read_export_index(index_path)

    time, state = noise_odeformer.read_index_cell(index_path.parent, index.iloc[0])

    assert time.shape == (512,)
    assert state.shape == (512, 1)


def test_hash_mismatch_aborts_from_shared_validator() -> None:
    tmp_path = fresh_workspace("hash_mismatch")
    index_path = copy_real_export_fixture(tmp_path)
    index = pd.read_csv(index_path)
    index.loc[0, "state_sha256"] = "0" * 64
    index.to_csv(index_path, index=False)

    with pytest.raises(ValueError, match="hash mismatch"):
        row = noise_odeformer.read_export_index(index_path).iloc[0]
        noise_odeformer.read_index_cell(index_path.parent, row)


def test_clean_r2_scores_are_one_for_identity_prediction() -> None:
    reference = np.column_stack([np.linspace(0, 1, 8), np.linspace(2, 5, 8)])

    arithmetic, weighted, by_dim, status = noise_odeformer.r2_scores(reference, reference.copy())

    assert arithmetic == 1.0
    assert weighted == 1.0
    assert by_dim == [1.0, 1.0]
    assert status == "success"


def test_run_noise_odeformer_writes_clean_evaluation_with_fake_adapter(tmp_path: Path, monkeypatch) -> None:
    index_path = copy_real_export_fixture(tmp_path)
    config_path = one_config(tmp_path)
    monkeypatch.setattr(harness, "build_odeformer_adapter", lambda config: IdentityAdapter(config))

    paths = noise_odeformer.run_noise_odeformer(
        config_path,
        [index_path],
        tmp_path / "out",
        repetitions=1,
        config_ids={"beam10_noopt"},
    )
    details = pd.read_csv(paths["details"])
    checks = pd.read_csv(paths["export_checks"])
    summary = pd.read_csv(paths["summary"])

    assert len(details) == 1
    assert details.loc[0, "status"] == "success"
    assert details.loc[0, "reconstruction_r2_arithmetic_mean"] == 1.0
    assert details.loc[0, "generalization_r2_arithmetic_mean"] == 1.0
    assert details.loc[0, "odeformer_environment_id"] == "reference"
    assert bool(checks.loc[0, "hash_verified"])
    assert summary.loc[0, "repetition_count"] == 1
    assert summary.loc[0, "reconstruction_r2_arithmetic_gt_0_9_rate"] == 1.0


def test_comparison_join_marks_missing_sources(tmp_path: Path) -> None:
    details = pd.DataFrame(
        [
            {
                "system_id": 1,
                "source_initial_condition_set": 1,
                "noise_sigma": 0.01,
                "subsample_rho": 0.0,
                "noise_realization": 1,
                "odeformer_config_id": "beam10_noopt",
            }
        ]
    )

    joined = noise_odeformer.build_comparison(details, [], [])

    assert joined.loc[0, "evogrow_source_path"] == "missing"
    assert joined.loc[0, "sindy_source_path"] == "missing"


def odeformer_equivalence_record(
    system_id: int,
    config_id: str,
    expression: str,
    repetition: int,
    fit_ic: int = 1,
    target_ic: int = 2,
) -> dict[str, object]:
    return {
        "system_id": system_id,
        "fit_initial_condition_set": fit_ic,
        "generalization_initial_condition_set": target_ic,
        "odeformer_config_id": config_id,
        "odeformer_grid_repetition": repetition,
        "status": "success",
        "odeformer_model_canonical": expression,
        "odeformer_fitted_constants": "[]",
        "reconstruction_r2_arithmetic_mean": 0.95,
        "reconstruction_r2_variance_weighted": 0.95,
        "generalization_r2_arithmetic_mean": 0.94,
        "generalization_r2_variance_weighted": 0.94,
    }


def write_jsonl(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    return path


def reference_grid_records() -> list[dict[str, object]]:
    configs = ["beam10_noopt", "beam10_opt", "beam20_noopt", "beam20_opt"]
    records = []
    for system_id in range(1, 6):
        for config_id in configs:
            for repetition in range(1, 4):
                expression = f"{config_id}_system_{system_id}_rep_{repetition}"
                records.append(odeformer_equivalence_record(system_id, config_id, expression, repetition))
    return records


def test_noise_control_matches_candidate_against_same_config_reference_repetition(tmp_path: Path) -> None:
    reference_records = reference_grid_records()
    candidate = odeformer_equivalence_record(
        1,
        "beam10_noopt",
        "beam10_noopt_system_1_rep_2",
        repetition=1,
    )
    reference_path = write_jsonl(tmp_path / "reference.jsonl", reference_records)
    candidate_path = write_jsonl(tmp_path / "candidate.jsonl", [candidate])

    control_path, passed = noise_odeformer.compare_control(candidate_path, tmp_path, reference_path)
    result = json.loads(control_path.read_text(encoding="utf-8"))

    assert passed is True
    assert result["passed"] is True
    assert result["reference_record_count"] == 20
    assert result["candidate_record_count"] == 1
    assert result["reference_raw_record_count"] == 60
    assert result["candidate_raw_record_count"] == 1
    assert result["comparison_rule"]["candidate_key_subset"] is True
    assert result["comparison_rule"]["accept_any_reference_repetition"] is True


def test_noise_control_rejects_candidate_matching_only_other_config(tmp_path: Path) -> None:
    reference_records = reference_grid_records()
    candidate = odeformer_equivalence_record(
        1,
        "beam10_noopt",
        "beam10_opt_system_1_rep_2",
        repetition=1,
    )
    reference_path = write_jsonl(tmp_path / "reference.jsonl", reference_records)
    candidate_path = write_jsonl(tmp_path / "candidate.jsonl", [candidate])

    control_path, passed = noise_odeformer.compare_control(candidate_path, tmp_path, reference_path)
    result = json.loads(control_path.read_text(encoding="utf-8"))

    assert passed is False
    assert result["findings"][0]["cell"] == [1, 1, 2, "beam10_noopt"]
    assert result["findings"][0]["field"] == "odeformer_model_canonical"


def test_noise_control_reports_missing_candidate_key_only_within_candidate_subset(tmp_path: Path) -> None:
    reference_records = [
        odeformer_equivalence_record(1, "beam10_noopt", "x_0", 1),
        odeformer_equivalence_record(2, "beam10_noopt", "x_0", 1),
    ]
    candidate_records = [
        odeformer_equivalence_record(1, "beam10_noopt", "x_0", 1),
        odeformer_equivalence_record(3, "beam10_noopt", "x_0", 1),
    ]
    reference_path = write_jsonl(tmp_path / "reference.jsonl", reference_records)
    candidate_path = write_jsonl(tmp_path / "candidate.jsonl", candidate_records)

    result = noise_odeformer.compare_noise_control(reference_path, candidate_path)

    assert result["passed"] is False
    assert result["findings"] == [
        {"cell": [3, 1, 2, "beam10_noopt"], "field": "record_presence", "reference": False, "candidate": True}
    ]
