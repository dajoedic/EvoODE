import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from exploratory.term_relevance import term_relevance as tr  # noqa: E402
from scripts.aggregate import run_wp_t1b_standalone_ranking as wp  # noqa: E402


def test_fd_explicit_intercept_can_rank_constant_candidate() -> None:
    x = np.linspace(-1.0, 1.0, 80)
    A = np.column_stack([np.ones_like(x), x, x**2])
    y = 2.0 + 0.25 * x

    legacy_order = tr.ranking_for(A, y, "forward")[0]
    repaired_order = tr.ranking_for(A, y, "forward", explicit_intercept=True)[0]

    assert legacy_order[-1] == 0
    assert repaired_order[0] == 0


def test_synthetic_oracle_support_recovers_coefficients() -> None:
    rng = np.random.default_rng(123)
    x = np.linspace(-1.0, 1.0, 120)
    A = np.column_stack([np.ones_like(x), x, x**2, rng.normal(size=len(x))])
    y = 1.5 - 2.0 * x**2

    order, _bics, coefs = wp.ranking_and_path(A, y, "fd")
    selected = order[:2]
    coef = wp.fit_coefficients(A, y, selected)

    assert set(selected) == {0, 2}
    assert math.isclose(coef[0], 1.5, rel_tol=0.0, abs_tol=1e-10)
    assert math.isclose(coef[2], -2.0, rel_tol=0.0, abs_tol=1e-10)


def test_details_schema_required_columns_are_present() -> None:
    columns = {
        "system_id",
        "system_name",
        "dimension",
        "source_initial_condition_set",
        "target_initial_condition_set",
        "direction",
        "regime",
        "n_library_terms",
        "true_terms",
        "active_terms_raw",
        "active_terms_pruned",
        "structure_hit_raw",
        "structure_hit_pruned",
        "r2",
        "r2_gt_0_9",
        "diverged_or_nonfinite",
        "integration_status",
        "fit_status",
        "n_target_regressions",
        "n_evaluation_integrations",
        "phasec_representability_threeway",
        "phasec_basis_name",
        "valid_for_analysis",
        "signal",
        "operating_point",
        "selected_k",
        "sigma_rel",
        "noise_replicate",
    }
    frame = pd.read_csv(REPO_ROOT / "analysis" / "data" / "wp_t1b_standalone_ranking" / "details.csv", nrows=1)

    assert columns <= set(frame.columns)
    assert set(frame["direction"]).issubset({"IC1_to_IC2", "IC2_to_IC1"})
    assert set(frame["regime"]).issubset({"reconstruction", "generalization"})


def test_ranking_path_is_deterministic_for_identical_input() -> None:
    rng = np.random.default_rng(456)
    A = rng.normal(size=(90, 6))
    A[:, 0] = 1.0
    y = 0.7 + A[:, 3] - 0.5 * A[:, 4]

    first = wp.ranking_and_path(A, y, "fd")
    second = wp.ranking_and_path(A, y, "fd")

    assert first[0] == second[0]
    assert np.allclose(first[1], second[1])
    assert all(np.allclose(lhs, rhs) for lhs, rhs in zip(first[2], second[2]))
