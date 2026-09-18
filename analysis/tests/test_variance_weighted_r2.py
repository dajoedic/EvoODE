import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate import aggregate_variance_weighted_r2 as vw_r2  # noqa: E402


PHASEB_REGISTRY = REPO_ROOT / "experiments" / "paper1_phaseB_v1" / "run_registry.csv"
TRAJECTORY_EXPORT = REPO_ROOT / "outputs" / "phase_c_trajectory_hashes" / "wp_c4c" / "trajectory_export"
PHASEC_SMOKE = (
    ANALYSIS_ROOT
    / "data"
    / "paper1_phaseC_v1"
    / "phasec_external_baselines_wp_n19_smoke"
    / "records.jsonl"
)


def write_manifest_row(export_dir: Path, system_id: int, ic_set: int, state: np.ndarray) -> dict[str, object]:
    cells_dir = export_dir / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)
    state = np.ascontiguousarray(state, dtype="<f8")
    state_path = Path("cells") / f"system_{system_id:04d}_ic{ic_set}_state_f64le_c_order.bin"
    state_bytes = state.tobytes(order="C")
    (export_dir / state_path).write_bytes(state_bytes)
    return {
        "system_id": system_id,
        "initial_condition_set": ic_set,
        "dimension": state.shape[1],
        "hash_format": "sha256_raw_little_endian_float64",
        "dtype": "float64",
        "byte_order": "little_endian",
        "time_axis_order": "time",
        "state_axis_order": "time_by_dimension_c_order",
        "time_shape": json.dumps([state.shape[0]], separators=(",", ":")),
        "state_shape": json.dumps(list(state.shape), separators=(",", ":")),
        "time_min": 0.0,
        "time_max": float(state.shape[0] - 1),
        "state_min": float(np.min(state)),
        "state_max": float(np.max(state)),
        "time_sha256": "unused",
        "state_sha256": hashlib.sha256(state_bytes).hexdigest(),
        "time_path": "unused",
        "state_path": state_path.as_posix(),
    }


def write_trajectory_export(tmp_path: Path, rows: list[dict[str, object]]) -> Path:
    export_dir = tmp_path / "trajectory_export"
    manifest_rows = []
    for row in rows:
        manifest_rows.append(
            write_manifest_row(
                export_dir,
                int(row["system_id"]),
                int(row["initial_condition_set"]),
                np.asarray(row["state"], dtype=float),
            )
        )
    with (export_dir / "trajectory_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0].keys()))
        writer.writeheader()
        writer.writerows(manifest_rows)
    return export_dir


def test_run_registry_reconstructs_weighted_r2_and_controls(tmp_path: Path) -> None:
    export_dir = write_trajectory_export(
        tmp_path,
        [
            {
                "system_id": 101,
                "initial_condition_set": 1,
                "state": [[0.0, 0.0], [1.0, 4.0], [2.0, 8.0]],
            },
            {
                "system_id": 102,
                "initial_condition_set": 1,
                "state": [[2.0], [3.0], [4.0]],
            },
        ],
    )
    registry = pd.DataFrame(
        [
            {
                "system_id": 101,
                "initial_condition_set": 1,
                "condition": "arm_a",
                "r2": 0.8,
                "r2_by_dim": json.dumps([0.6, 1.0]),
            },
            {
                "system_id": 102,
                "initial_condition_set": 1,
                "condition": "arm_a",
                "r2": 0.7,
                "r2_by_dim": json.dumps([0.7]),
            },
        ]
    )
    input_path = tmp_path / "run_registry.csv"
    registry.to_csv(input_path, index=False)

    outputs = vw_r2.aggregate(
        argparse.Namespace(
            campaign="fixture_campaign",
            input=str(input_path),
            input_format="run_registry",
            trajectory_export=str(export_dir),
            output_dir=str(tmp_path / "out"),
        )
    )

    cells = pd.read_csv(outputs["cells"])
    multi = cells[cells["dimension"] == 2].iloc[0]
    assert multi["r2_arithmetic_mean"] == 0.8
    assert multi["r2_variance_weighted"] > 0.9
    assert bool(multi["threshold_flip"])
    assert multi["threshold_flip_direction"] == "arithmetic_le_0_9_to_variance_weighted_gt_0_9"

    controls = pd.read_csv(outputs["controls"])
    arithmetic = controls[controls["control"] == "arithmetic_mean_reproduces_r2"].iloc[0]
    one_dim = controls[controls["control"] == "one_dimensional_aggregations_identical"].iloc[0]
    assert arithmetic["n_checked"] == 2
    assert arithmetic["n_failed"] == 0
    assert one_dim["n_checked"] == 1
    assert one_dim["n_failed"] == 0


def test_run_registry_rejects_arithmetic_control_violation(tmp_path: Path) -> None:
    export_dir = write_trajectory_export(
        tmp_path,
        [{"system_id": 101, "initial_condition_set": 1, "state": [[0.0], [1.0], [2.0]]}],
    )
    input_path = tmp_path / "run_registry.csv"
    pd.DataFrame(
        [
            {
                "system_id": 101,
                "initial_condition_set": 1,
                "condition": "arm_a",
                "r2": 0.8,
                "r2_by_dim": json.dumps([0.7]),
            }
        ]
    ).to_csv(input_path, index=False)

    try:
        vw_r2.aggregate(
            argparse.Namespace(
                campaign="fixture_campaign",
                input=str(input_path),
                input_format="run_registry",
                trajectory_export=str(export_dir),
                output_dir=str(tmp_path / "out"),
            )
        )
    except ValueError as exc:
        assert "arithmetic control failed" in str(exc)
    else:
        raise AssertionError("arithmetic control violation should fail")


def test_real_phaseb_outputs_have_required_controls_and_flips(tmp_path: Path) -> None:
    outputs = vw_r2.aggregate(
        argparse.Namespace(
            campaign="paper1_phaseB_v1",
            input=str(PHASEB_REGISTRY),
            input_format="run_registry",
            trajectory_export=str(TRAJECTORY_EXPORT),
            output_dir=str(tmp_path / "phaseb"),
        )
    )

    cells = pd.read_csv(outputs["cells"])
    controls = pd.read_csv(outputs["controls"])
    assert len(cells) == 756
    assert int(controls.loc[controls["control"] == "arithmetic_mean_reproduces_r2", "n_checked"].iloc[0]) == 756
    assert int(controls.loc[controls["control"] == "arithmetic_mean_reproduces_r2", "n_failed"].iloc[0]) == 0
    assert int(controls.loc[controls["control"] == "one_dimensional_aggregations_identical", "n_failed"].iloc[0]) == 0
    assert int((cells["dimension"] > 1).sum()) > 0
    assert int(
        (
            (cells["dimension"] > 1)
            & (cells["r2_difference_variance_weighted_minus_arithmetic"].abs() > 1e-12)
        ).sum()
    ) > 0
    assert int(cells["threshold_flip"].sum()) > 0


def test_phasec_external_baseline_smoke_is_second_parameterized_input(tmp_path: Path) -> None:
    outputs = vw_r2.aggregate(
        argparse.Namespace(
            campaign="paper1_phaseC_v1",
            input=str(PHASEC_SMOKE),
            input_format="auto",
            trajectory_export=str(TRAJECTORY_EXPORT),
            output_dir=str(tmp_path / "phasec"),
        )
    )

    cells = pd.read_csv(outputs["cells"])
    rates = pd.read_csv(outputs["rates"])
    expected_records = sum(1 for line in PHASEC_SMOKE.read_text(encoding="utf-8").splitlines() if line.strip())
    assert len(cells) == expected_records * 2
    assert set(cells["source_format"]) == {"phasec_external_baseline"}
    assert {"reconstruction", "generalization"} == set(cells["metric_scope"])
    assert not rates.empty
    assert (rates["n_cells"] > 0).all()
