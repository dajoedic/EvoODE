import argparse
import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_c8_oracle_bounds import aggregate, run_control  # noqa: E402


def record(cell_key: str, bound_loss: float, loss_evals: int, r2: float = 0.95) -> dict:
    return {
        "cell_key": cell_key,
        "system_id": 1,
        "initial_condition_set": 1,
        "seed": 42,
        "reference_loss": bound_loss,
        "reference_coefficients": [[{"term": "1", "term_index": 1, "coefficient": 1.0}]],
        "reference_r2": r2,
        "reference_structure_hit": True,
        "reference_fit_meta": {
            "result_valid": True,
            "loss_evals": loss_evals,
            "diverged_solves": 0,
            "nonfinite_solves": 0,
            "retry_triggered": False,
        },
        "error": None,
    }


def write_shard(root: Path, rows: list[dict]) -> Path:
    shard = root / "shard_001_of_001"
    shard.mkdir(parents=True)
    with (shard / "results.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return root


def test_control_rejects_bound10_reference_mismatch() -> None:
    bound10 = {"sys0001_seed42_ic1": record("sys0001_seed42_ic1", 1.0, 10)}
    reference = {"sys0001_seed42_ic1": record("sys0001_seed42_ic1", 2.0, 10)}

    try:
        run_control(bound10, reference)
    except SystemExit as exc:
        assert "reference_loss" in str(exc)
    else:
        raise AssertionError("Expected control mismatch to abort")


def test_aggregate_writes_summary_and_changes(tmp_path: Path) -> None:
    key = "sys0001_seed42_ic1"
    bound10 = write_shard(tmp_path / "bound_10", [record(key, 1.0, 100)])
    bound1000 = write_shard(tmp_path / "bound_1000", [record(key, 0.9, 140)])
    boundinf = write_shard(tmp_path / "bound_Inf", [record(key, 0.8, 170)])
    reference = write_shard(tmp_path / "reference", [record(key, 1.0, 100)])
    support = tmp_path / "phase_c_support.json"
    support.write_text(
        json.dumps(
            {
                "basis_name": "staged_polynomial_basis_with_constant",
                "systems": [{"system_id": 1, "dim": 1, "representability": "exact"}],
            }
        ),
        encoding="utf-8",
    )
    output_dir = tmp_path / "out"

    aggregate(
        argparse.Namespace(
            bound10=[bound10],
            bound1000=[bound1000],
            bound_inf=[boundinf],
            reference_c5=reference,
            support=support,
            output_dir=output_dir,
        )
    )

    with (output_dir / "bound_summary.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["bound"] for row in rows] == ["10", "1000", "Inf"]
    assert rows[1]["comparable_stable"] == "yes"
    assert rows[2]["comparable_stable"] == "no"

    with (output_dir / "changes_by_cell.csv").open("r", encoding="utf-8", newline="") as handle:
        changes = list(csv.DictReader(handle))
    assert len(changes) == 2
    assert all(row["changed_fit"] == "True" for row in changes)
