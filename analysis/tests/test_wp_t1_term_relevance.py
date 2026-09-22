import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from exploratory.term_relevance import term_relevance as tr  # noqa: E402


def test_phasec_basis_consistency_against_real_exact_supports() -> None:
    _basis_name, supports = tr.load_exact_supports(REPO_ROOT / "studies" / "regression" / "phase_c_support.json")

    tr.verify_basis_consistency(supports)

    assert [len(tr.phasec_basis(dim)) for dim in (1, 2, 3, 4)] == [6, 12, 19, 27]


def test_synthetic_well_excited_system_ranks_true_support_first() -> None:
    rng = np.random.default_rng(123)
    Q, _ = np.linalg.qr(rng.normal(size=(120, 8)))
    A = Q[:, :8]
    true_idxs = {1, 4}
    y = 2.0 * A[:, 1] - 1.5 * A[:, 4]

    for method in ("marginal", "forward"):
        order, _scores, _degenerate, _A_std = tr.ranking_for(A, y, method)
        metrics = tr.metrics_from_order(order, true_idxs)
        assert metrics["n_false_before_last_true"] == 0


def test_null_model_empirical_mean_matches_analytic() -> None:
    rng = np.random.default_rng(456)
    empirical = float(np.mean(tr.random_false_before(12, 2, rng, n=20_000)))
    analytic = tr.analytic_null_mean(12, 2)

    assert abs(empirical - analytic) < 0.12


def test_ranking_is_deterministic_for_identical_input() -> None:
    rng = np.random.default_rng(789)
    A = rng.normal(size=(80, 8))
    y = rng.normal(size=80)
    first = tr.ranking_for(A, y, "forward")[0]
    second = tr.ranking_for(A, y, "forward")[0]

    assert first == second


def test_degenerate_column_is_marked_and_ranked_last() -> None:
    rng = np.random.default_rng(42)
    A = rng.normal(size=(40, 4))
    A[:, 0] = 1.0
    y = A[:, 1] - 0.5 * A[:, 2]

    order, _scores, degenerate, _A_std = tr.ranking_for(A, y, "marginal")

    assert degenerate[0]
    assert order[-1] == 0


def _write_export_fixture(base: Path) -> Path:
    export_dir = base / "trajectory_export"
    cells = export_dir / "cells"
    cells.mkdir(parents=True)
    time = np.asarray([0.0, 0.5, 1.0], dtype="<f8")
    state = np.asarray([[1.0, 2.0], [1.5, 1.8], [2.0, 1.7]], dtype="<f8")
    time_path = Path("cells/system_0101_ic1_time_f64le.bin")
    state_path = Path("cells/system_0101_ic1_state_f64le_c_order.bin")
    (export_dir / time_path).write_bytes(time.tobytes(order="C"))
    (export_dir / state_path).write_bytes(state.tobytes(order="C"))
    row = {
        "system_id": 101,
        "initial_condition_set": 1,
        "dimension": 2,
        "hash_format": "sha256_raw_little_endian_float64",
        "dtype": "float64",
        "byte_order": "little_endian",
        "time_axis_order": "time",
        "state_axis_order": "time_by_dimension_c_order",
        "time_shape": json.dumps([3]),
        "state_shape": json.dumps([3, 2]),
        "time_min": 0.0,
        "time_max": 1.0,
        "state_min": 1.0,
        "state_max": 2.0,
        "time_sha256": hashlib.sha256(time.tobytes(order="C")).hexdigest(),
        "state_sha256": hashlib.sha256(state.tobytes(order="C")).hexdigest(),
        "time_path": str(time_path),
        "state_path": str(state_path),
    }
    with (export_dir / "trajectory_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    return export_dir


def test_trajectory_export_hash_mismatch_aborts(tmp_path: Path) -> None:
    export_dir = _write_export_fixture(tmp_path)
    state_path = export_dir / "cells/system_0101_ic1_state_f64le_c_order.bin"
    state_path.write_bytes(state_path.read_bytes()[:-8] + np.asarray([9.0], dtype="<f8").tobytes())

    try:
        tr.load_exported_trajectories(export_dir)
    except ValueError as exc:
        assert "hash mismatch" in str(exc)
    else:
        raise AssertionError("hash mismatch should abort")
