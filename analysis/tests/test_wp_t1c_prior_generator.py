import hashlib
import sys
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from exploratory.term_relevance import term_relevance as tr  # noqa: E402
from scripts.aggregate import run_wp_t1c_prior_generator as wp  # noqa: E402


REFERENCE_HASHES = {
    "analysis/data/wp_t1_term_relevance/gate_decision.json": "a1ab0b888fb8bc36b8b1f164fb4e3d70dd5362003ac0bdce3aeb50fa1e0131f0",
    "analysis/data/wp_t1_term_relevance/aggregate_by_configuration_dimension.csv": "8a1c3d7c8b56da5f42f936b034542311313638ffd189eb44fa3ba9d3f49e1893",
    "analysis/data/wp_t1b_standalone_ranking/summary.csv": "bab3d1103461245e3e57eadcb63b7c5917089b073fdf663694e8446aef6726d8",
    "analysis/data/wp_t1b_standalone_ranking/cost.csv": "23e337575f33d42726742fa57ec17c9f76580150c338796984870496edfc525e",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_wp_t1_and_t1b_reference_artifacts_are_unchanged() -> None:
    for relative, expected in REFERENCE_HASHES.items():
        assert sha256(REPO_ROOT / relative) == expected


def test_synthetic_support_is_ranked_first_by_forward_and_stlsq_path() -> None:
    rng = np.random.default_rng(123)
    Q, _ = np.linalg.qr(rng.normal(size=(160, 8)))
    A = Q[:, :8]
    true_idxs = {1, 4}
    y = 2.0 * A[:, 1] - 1.5 * A[:, 4]

    for method in ("forward", "stlsq_path"):
        order, _scores, _degenerate, _A_std, _metadata = wp.ranking_with_metadata(A, y, method)
        metrics = tr.metrics_from_order(order, true_idxs)
        assert metrics["n_false_before_last_true"] == 0


def test_stlsq_threshold_grid_coverage() -> None:
    rng = np.random.default_rng(456)
    A = rng.normal(size=(80, 5))
    y = 0.5 * A[:, 0] - A[:, 3]

    _order, _scores, metadata = tr.stlsq_path(A, y, tr.STLSQ_THRESHOLD_GRID)

    assert metadata["active_counts"][0] == A.shape[1]
    assert metadata["active_counts"][-1] == 0


def test_stlsq_tie_break_is_deterministic_by_coefficient_then_basis_index() -> None:
    x = np.linspace(-1.0, 1.0, 100)
    A = np.column_stack([x, x, x**2])
    y = 2.0 * A[:, 0] + 0.25 * A[:, 2]

    order, _scores, _metadata = tr.stlsq_path(A, y, [0.0, 0.1, 0.3, 1.0, 10.0])

    assert order[:2] == [0, 1]


def test_wp_t1c_records_are_deterministic_for_identical_seed() -> None:
    support_path = REPO_ROOT / "studies" / "regression" / "phase_c_support.json"
    benchmark_path = REPO_ROOT / "benchmarks" / "data" / "strogatz_extended.json"
    export_dir = REPO_ROOT / "outputs" / "phase_c_trajectory_hashes" / "wp_c4c" / "trajectory_export"
    _basis_name, supports = tr.load_exact_supports(support_path)
    supports = [item for item in supports if int(item["system_id"]) == 24]
    benchmark = tr.load_benchmark(benchmark_path)
    trajectories = tr.load_exported_trajectories(export_dir, [24])

    first_records = wp.build_records(supports, benchmark, trajectories)
    second_records = wp.build_records(supports, benchmark, trajectories)
    first = wp.jsonable_frame(first_records).to_csv(index=False)
    second = wp.jsonable_frame(second_records).to_csv(index=False)

    assert first == second
    decision = wp.generator_decision(wp.pd.DataFrame(first_records))
    assert decision["winner"] in {"forward", "stlsq_path", "no_winner"}
