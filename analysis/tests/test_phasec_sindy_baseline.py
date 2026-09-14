import copy
import csv
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate import run_phasec_sindy_baseline as phasec_sindy  # noqa: E402


PILOT_DIR = REPO_ROOT / "outputs" / "phase_c_p9_pilot_records"
PILOT_SYSTEMS = [2, 24, 52, 63]
PHASEC_DETAILS = ANALYSIS_ROOT / "data" / "paper1_phaseC_v1" / "phasec_sindy_baseline" / "details.csv"
WPN6_DATA_DIR = ANALYSIS_ROOT / "data" / "wp_n6_sindy_baseline"
WPN6_TABLE_DIR = ANALYSIS_ROOT / "tables" / "wp_n6_sindy_baseline"


def write_exported_trajectory_fixture(tmp_path: Path) -> tuple[Path, list[dict[str, object]]]:
    export_dir = tmp_path / "trajectory_export"
    cells_dir = export_dir / "cells"
    cells_dir.mkdir(parents=True)
    benchmark = [
        {"id": 101, "dim": 1},
        {"id": 102, "dim": 2},
    ]
    t_grid = np.asarray([0.0, 0.5, 1.0], dtype="<f8")
    rows = []
    for system in benchmark:
        system_id = int(system["id"])
        dim = int(system["dim"])
        for ic_set in (1, 2):
            state = (np.arange(len(t_grid) * dim, dtype="<f8").reshape((len(t_grid), dim), order="C") + system_id + ic_set)
            time_path = Path("cells") / f"system_{system_id}_ic{ic_set}_time_f64le.bin"
            state_path = Path("cells") / f"system_{system_id}_ic{ic_set}_state_f64le_c_order.bin"
            time_bytes = np.ascontiguousarray(t_grid, dtype="<f8").tobytes(order="C")
            state_bytes = np.ascontiguousarray(state, dtype="<f8").tobytes(order="C")
            (export_dir / time_path).write_bytes(time_bytes)
            (export_dir / state_path).write_bytes(state_bytes)
            rows.append(
                {
                    "system_id": system_id,
                    "initial_condition_set": ic_set,
                    "dimension": dim,
                    "hash_format": "sha256_raw_little_endian_float64",
                    "dtype": "float64",
                    "byte_order": "little_endian",
                    "time_axis_order": "time",
                    "state_axis_order": "time_by_dimension_c_order",
                    "time_shape": json.dumps([len(t_grid)], separators=(",", ":")),
                    "state_shape": json.dumps([len(t_grid), dim], separators=(",", ":")),
                    "time_min": float(np.min(t_grid)),
                    "time_max": float(np.max(t_grid)),
                    "state_min": float(np.min(state)),
                    "state_max": float(np.max(state)),
                    "time_sha256": hashlib.sha256(time_bytes).hexdigest(),
                    "state_sha256": hashlib.sha256(state_bytes).hexdigest(),
                    "time_path": time_path.as_posix(),
                    "state_path": state_path.as_posix(),
                }
            )
    pd.DataFrame(rows).to_csv(export_dir / "trajectory_manifest.csv", index=False)
    return export_dir, benchmark


def read_pilot_records() -> list[dict[str, object]]:
    records = []
    for path in sorted(PILOT_DIR.glob("cell_*.jsonl")):
        if path.name.endswith(".heartbeat.jsonl"):
            continue
        line = path.read_text(encoding="utf-8").splitlines()[0]
        records.append(json.loads(line))
    assert len(records) == 16
    return records


def write_records(tmp_path: Path, records: list[dict[str, object]]) -> Path:
    records_dir = tmp_path / "records"
    records_dir.mkdir()
    for idx, record in enumerate(records, start=1):
        (records_dir / f"cell_{idx:06d}.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    return records_dir


def sindy_fixture(path: Path, systems: list[int] | None = None, invalid_control: bool = False) -> Path:
    systems = systems or PILOT_SYSTEMS
    rows = []
    for system_id in systems:
        dim = 1 if system_id == 2 else 2 if system_id == 24 else 3 if system_id == 52 else 4
        for source_ic, target_ic, direction in [(1, 2, "IC1_to_IC2"), (2, 1, "IC2_to_IC1")]:
            rows.append(
                {
                    "library_id": "poly_deg2_stlsq_0.01",
                    "polynomial_degree": 2,
                    "include_sin_cos": False,
                    "stlsq_threshold": 0.01,
                    "system_id": system_id,
                    "system_name": f"system {system_id}",
                    "dimension": dim,
                    "source_initial_condition_set": source_ic,
                    "target_initial_condition_set": target_ic,
                    "initial_condition_set": target_ic,
                    "direction": direction,
                    "regime": "generalization",
                    "fit_status": "success",
                    "integration_status": "success",
                    "diverged_or_nonfinite": False,
                    "r2": 0.95,
                    "r2_gt_0_9": True,
                    "sindy_structure_hit_raw": True,
                    "sindy_structure_hit_pruned": True,
                    "n_library_terms": 3,
                    "fit_elapsed_s_context": 0.01,
                    "elapsed_s_evidence_role": "context_not_evidence",
                    "n_target_regressions": dim,
                    "n_evaluation_integrations": 1,
                    "reconstruction_control_max_abs": 1.0 if invalid_control else 0.0,
                    "reconstruction_control_valid": not invalid_control,
                    "valid_for_analysis": not invalid_control,
                    "phasec_representability": "exact",
                    "phasec_representability_threeway": "exact",
                    "phasec_support_status": "ok",
                    "phasec_basis_name": "staged_polynomial_basis_with_constant",
                }
            )
    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    return path


def real_phasec_summary_rows() -> pd.DataFrame:
    details = pd.read_csv(PHASEC_DETAILS)
    diverged = details[(details["diverged_or_nonfinite"]) & (details["r2"].notna())].iloc[[0]].copy()
    clean = details[
        (~details["diverged_or_nonfinite"])
        & (details["r2"].notna())
        & (details["library_id"] == diverged.iloc[0]["library_id"])
        & (details["direction"] == diverged.iloc[0]["direction"])
        & (details["regime"] == diverged.iloc[0]["regime"])
        & (details["dimension"] == diverged.iloc[0]["dimension"])
        & (details["phasec_representability_threeway"] == diverged.iloc[0]["phasec_representability_threeway"])
    ].iloc[[0]].copy()
    clean.loc[:, "r2"] = 0.25
    clean.loc[:, "r2_gt_0_9"] = False
    diverged.loc[:, "r2"] = -1.0e80
    diverged.loc[:, "r2_gt_0_9"] = False
    return pd.concat([clean, diverged], ignore_index=True)


def copy_wpn6_outputs(tmp_path: Path) -> tuple[Path, Path]:
    data_dir = tmp_path / "data"
    table_dir = tmp_path / "tables"
    shutil.copytree(WPN6_DATA_DIR, data_dir)
    shutil.copytree(WPN6_TABLE_DIR, table_dir)
    return data_dir, table_dir


def rewrite_csv_cells(path: Path, updates: dict[tuple[int, str], str]) -> None:
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    header = rows[0]
    column_indexes = {column: index for index, column in enumerate(header)}
    for (data_row_index, column), value in updates.items():
        rows[data_row_index + 1][column_indexes[column]] = value
    with path.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def pair_args(tmp_path: Path, records_dir: Path, sindy_path: Path, **updates: object):
    class Args:
        sindy_details = str(sindy_path)
        evogrow_records_dir = str(records_dir)
        output = str(tmp_path / "paired.csv")
        expected_systems = ""
        expected_ic_sets = "1,2"
        expected_seeds = ""
        expected_git_hash = ""
        expected_config_fingerprint = ""
        expected_stage_cap_behavior_fingerprint = ""

    args = Args()
    for key, value in updates.items():
        setattr(args, key, value)
    return args


def test_load_exported_trajectories_recomputes_hashes_and_returns_c_order_arrays(tmp_path: Path) -> None:
    export_dir, benchmark = write_exported_trajectory_fixture(tmp_path)

    t_grid, trajectories, checks = phasec_sindy.load_exported_trajectories(export_dir, benchmark)

    assert t_grid.tolist() == [0.0, 0.5, 1.0]
    assert trajectories[(101, 1)].shape == (3, 1)
    assert trajectories[(102, 2)].shape == (3, 2)
    assert len(checks) == 4
    assert checks["hash_verified"].all()
    assert set(checks["truth_trajectory_source"]) == {"campaign_export"}


def test_load_exported_trajectories_rejects_missing_export(tmp_path: Path) -> None:
    try:
        phasec_sindy.load_exported_trajectories(tmp_path / "missing", [{"id": 1, "dim": 1}])
    except ValueError as exc:
        assert "missing trajectory export manifest" in str(exc)
    else:
        raise AssertionError("missing trajectory export should fail")


def test_load_exported_trajectories_rejects_hash_mismatch(tmp_path: Path) -> None:
    export_dir, benchmark = write_exported_trajectory_fixture(tmp_path)
    state_path = export_dir / "cells" / "system_101_ic1_state_f64le_c_order.bin"
    state_path.write_bytes(state_path.read_bytes()[:-8] + np.asarray([999.0], dtype="<f8").tobytes())

    try:
        phasec_sindy.load_exported_trajectories(export_dir, benchmark)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("hash mismatch should fail")


def test_pairing_runs_against_real_pilot_records_and_keeps_directions(tmp_path: Path) -> None:
    records_dir = write_records(tmp_path, read_pilot_records())
    sindy_path = sindy_fixture(tmp_path / "sindy.csv")

    output = phasec_sindy.pair_sindy_evogrow(pair_args(tmp_path, records_dir, sindy_path))
    paired = pd.read_csv(output)

    assert len(paired) == 8
    assert set(paired["direction"]) == {"IC1_to_IC2", "IC2_to_IC1"}
    assert set(paired["evogrow_seed_policy"]) == {"mean_rate_over_available_phasec_seeds"}
    assert paired["git_hash"].nunique() == 1
    assert paired["config_fingerprint"].nunique() == 1
    assert paired["stage_cap_behavior_fingerprint"].nunique() == 1


def test_pairing_rejects_incomplete_evogrow_input(tmp_path: Path) -> None:
    records = read_pilot_records()
    records_dir = write_records(tmp_path, records[:-1])
    sindy_path = sindy_fixture(tmp_path / "sindy.csv")

    try:
        phasec_sindy.pair_sindy_evogrow(
            pair_args(tmp_path, records_dir, sindy_path, expected_systems="2,24,52,63")
        )
    except ValueError as exc:
        assert "incomplete" in str(exc)
    else:
        raise AssertionError("incomplete EvoGrow input should fail")


def test_pairing_rejects_non_phasec_identity(tmp_path: Path) -> None:
    records = read_pilot_records()
    records[0] = copy.deepcopy(records[0])
    records[0]["basis_name"] = "staged_polynomial_basis"
    records_dir = write_records(tmp_path, records)
    sindy_path = sindy_fixture(tmp_path / "sindy.csv")

    try:
        phasec_sindy.pair_sindy_evogrow(pair_args(tmp_path, records_dir, sindy_path))
    except ValueError as exc:
        assert "staged_polynomial_basis_with_constant" in str(exc)
    else:
        raise AssertionError("non-Phase-C identity should fail")


def test_pairing_excludes_nonzero_reconstruction_control_rows(tmp_path: Path) -> None:
    records_dir = write_records(tmp_path, read_pilot_records())
    sindy_path = sindy_fixture(tmp_path / "sindy.csv")
    frame = pd.read_csv(sindy_path)
    frame.loc[0, "reconstruction_control_max_abs"] = 1.0
    frame.loc[0, "reconstruction_control_valid"] = False
    frame.loc[0, "valid_for_analysis"] = False
    frame.to_csv(sindy_path, index=False)

    output = phasec_sindy.pair_sindy_evogrow(pair_args(tmp_path, records_dir, sindy_path))
    paired = pd.read_csv(output)

    assert len(paired) == 7
    assert paired["reconstruction_control_valid"].all()


def test_summary_is_layered_by_dimension_and_phasec_representability(tmp_path: Path) -> None:
    details = pd.read_csv(sindy_fixture(tmp_path / "unused.csv"))
    summary = phasec_sindy.summarize(details)

    assert not summary.empty
    assert "dimension" in summary.columns
    assert "phasec_representability_threeway" in summary.columns
    assert set(summary["aggregation_scope"]) == {"dimension_by_phasec_representability_threeway"}
    assert "structure_hit_raw_count" in summary.columns
    assert "structure_hit_pruned_count" in summary.columns
    assert "r2_gt_0_9_count" in summary.columns


def test_summary_excludes_finite_diverged_r2_from_median_and_quantiles() -> None:
    details = real_phasec_summary_rows()
    summary = phasec_sindy.summarize(details)

    assert len(summary) == 1
    row = summary.iloc[0]
    assert row["diverged_or_nonfinite_count"] == 1
    assert row["r2_finite_nondiverged_count"] == 1
    assert row["r2_median_valid"] == 0.25
    assert row["r2_q000_finite_nondiverged"] == 0.25
    assert row["r2_q025_finite_nondiverged"] == 0.25
    assert row["r2_q075_finite_nondiverged"] == 0.25
    assert row["r2_q100_finite_nondiverged"] == 0.25


def test_summary_empty_clean_r2_selection_reports_nan_not_zero() -> None:
    details = real_phasec_summary_rows().iloc[[1]].copy()
    summary = phasec_sindy.summarize(details)

    row = summary.iloc[0]
    assert row["diverged_or_nonfinite_count"] == 1
    assert row["r2_finite_nondiverged_count"] == 0
    assert pd.isna(row["r2_median_valid"])
    assert pd.isna(row["r2_q000_finite_nondiverged"])
    assert pd.isna(row["r2_q100_finite_nondiverged"])


def test_wpn6_reported_measure_check_allows_runtime_and_diverged_r2_only(tmp_path: Path) -> None:
    candidate_data, candidate_tables = copy_wpn6_outputs(tmp_path)
    details = pd.read_csv(candidate_data / "details.csv")
    diverged_index = details.index[details["integration_status"] == "diverged"][0]
    rewrite_csv_cells(
        candidate_data / "details.csv",
        {
            (0, "fit_elapsed_s_non_evidence"): "123.0",
            (int(diverged_index), "r2"): str(float(details.loc[diverged_index, "r2"]) - 1.0),
        },
    )
    rewrite_csv_cells(candidate_data / "costs.csv", {(0, "elapsed_s_non_evidence_total"): "123.0"})
    rewrite_csv_cells(candidate_tables / "wp_n6_costs.csv", {(0, "elapsed_s_non_evidence_total"): "123.0"})

    failures = phasec_sindy.compare_wpn6_outputs(WPN6_DATA_DIR, WPN6_TABLE_DIR, candidate_data, candidate_tables)

    assert failures == []


def test_wpn6_reported_measure_check_rejects_reported_column_flip(tmp_path: Path) -> None:
    candidate_data, candidate_tables = copy_wpn6_outputs(tmp_path)
    rewrite_csv_cells(candidate_data / "details.csv", {(0, "r2_gt_0_9"): "False"})

    failures = phasec_sindy.compare_wpn6_outputs(WPN6_DATA_DIR, WPN6_TABLE_DIR, candidate_data, candidate_tables)

    assert len(failures) == 1
    assert "r2_gt_0_9" in failures[0]
