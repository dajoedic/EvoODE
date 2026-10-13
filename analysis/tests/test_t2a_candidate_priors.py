import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate import build_t2a_candidate_priors as t2a  # noqa: E402


def test_oracle_ranking_promotes_true_terms_in_guided_order() -> None:
    assert t2a.oracle_ranking([4, 2, 1, 3], [1, 2]) == [2, 1, 4, 3]


def test_name_mapping_refuses_unknown_order() -> None:
    try:
        t2a.guided_ranking(
            {
                "row_id": "fixture",
                "candidate_names": ["1", "u1", "not_a_phase_c_term"],
                "candidate_ranks": [1, 2, 3],
            },
            1,
        )
    except ValueError as exc:
        assert "candidate name mapping mismatch" in str(exc)
    else:
        raise AssertionError("expected name mapping refusal")


def test_build_priors_from_minimal_real_shape_fixture(tmp_path: Path) -> None:
    records = tmp_path / "records.csv"
    trajectory_manifest = tmp_path / "trajectory_manifest.csv"
    support = tmp_path / "support.json"
    names = ["1", "u1", "u1^2", "u1^3", "sin(u1)", "cos(u1)"]
    rows = []
    for system_id in range(1, 22):
        for ic in (1, 2):
            rows.append(
                {
                    "system_id": str(system_id),
                    "system_name": "fixture",
                    "dimension": "1",
                    "equation_idx": "1",
                    "ic_strategy": f"ic{ic}",
                    "signal": "weak",
                    "ranking_method": "forward",
                    "sigma_rel": "0.0",
                    "noise_replicate": "0",
                    "noise_seed": "",
                    "basis_name": "staged_polynomial_basis_with_constant",
                    "library_size": "6",
                    "true_support_terms": json.dumps(["u1"]),
                    "true_support_size": "1",
                    "candidate_names": json.dumps(names),
                    "candidate_scores": json.dumps([0, 0, 0, 0, 0, 0]),
                    "candidate_ranks": json.dumps([3, 2, 1, 4, 5, 6]),
                    "trajectory_sha256": f"statehash{system_id}_{ic}",
                }
            )
    with records.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    with trajectory_manifest.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["system_id", "initial_condition_set", "state_sha256"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {
                    "system_id": str(system_id),
                    "initial_condition_set": str(ic),
                    "state_sha256": f"statehash{system_id}_{ic}",
                }
                for system_id in range(1, 22)
                for ic in (1, 2)
            ]
        )
    support.write_text(
        json.dumps(
            {
                "basis_name": "staged_polynomial_basis_with_constant",
                "systems": [
                    {
                        "system_id": system_id,
                        "dim": 1,
                        "representability": "exact",
                        "status": "ok",
                        "support_idxs": [[2]],
                        "support_terms": [["u1"]],
                    }
                    for system_id in range(1, 22)
                ],
            }
        ),
        encoding="utf-8",
    )

    original_loader = t2a.tr.load_exact_supports
    t2a.tr.load_exact_supports = lambda _path: (
        "staged_polynomial_basis_with_constant",
        json.loads(support.read_text(encoding="utf-8"))["systems"],
    )
    try:
        priors = t2a.build_priors(records, support, trajectory_manifest)
    finally:
        t2a.tr.load_exact_supports = original_loader

    guided = priors[("guided_prior", 1, 1)]["rankings"][0]
    oracle = priors[("oracle_prior", 1, 1)]["rankings"][0]
    assert guided == [3, 2, 1, 4, 5, 6]
    assert oracle[0] == 2
    assert len(priors) == 84
