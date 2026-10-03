from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from baselines import recompute_odeformer_grid_structure as recompute_grid


def write_support(path: Path) -> Path:
    payload = {
        "basis_name": "staged_polynomial_basis_with_constant",
        "systems": [
            {
                "system_id": 1,
                "dim": 1,
                "representability": "exact",
                "support_terms": [["1", "u1"]],
            },
            {
                "system_id": 2,
                "dim": 1,
                "representability": "exact",
                "support_terms": [["u1"]],
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def write_jsonl(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    return path


def test_recompute_grid_structure_writes_sidecar_outputs_and_preserves_r2(tmp_path: Path) -> None:
    support = write_support(tmp_path / "phase_c_support.json")
    records_path = write_jsonl(
        tmp_path / "records.jsonl",
        [
            {
                "system_id": 1,
                "dimension": 1,
                "status": "success",
                "odeformer_expression_after_optimization": "0.2835 - 0.3557*x_0",
                "reconstruction_r2_arithmetic_mean": 0.999,
                "reconstruction_r2_variance_weighted": 0.998,
                "generalization_r2_arithmetic_mean": 0.997,
                "generalization_r2_variance_weighted": 0.996,
                "active_terms_raw": "[]",
                "active_terms_pruned": "[]",
                "true_terms": "[]",
                "structure_hit_raw": False,
                "structure_hit_pruned": False,
            }
        ],
    )

    paths = recompute_grid.recompute_file(records_path, support, "records_structure_recomputed", "manifest.json")
    updated = [json.loads(line) for line in paths["jsonl"].read_text(encoding="utf-8").splitlines()]
    frame = pd.read_csv(paths["csv"])
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))

    assert records_path.read_text(encoding="utf-8").count('"structure_hit_raw": false') == 1
    assert updated[0]["active_terms_raw"] == '[["1","u1"]]'
    assert updated[0]["active_terms_pruned"] == '[["1","u1"]]'
    assert updated[0]["true_terms"] == '[["1","u1"]]'
    assert updated[0]["structure_hit_raw"] is True
    assert updated[0]["structure_hit_pruned"] is True
    assert updated[0]["reconstruction_r2_arithmetic_mean"] == 0.999
    assert updated[0]["generalization_r2_variance_weighted"] == 0.996
    assert bool(frame.loc[0, "structure_hit_pruned"])
    assert manifest["record_count"] == 1
    assert manifest["structure_hit_pruned_count"] == 1


def test_recompute_grid_structure_counts_rational_expression_outside_basis(tmp_path: Path) -> None:
    support = write_support(tmp_path / "phase_c_support.json")
    records_path = write_jsonl(
        tmp_path / "records.jsonl",
        [
            {
                "system_id": 2,
                "dimension": 1,
                "status": "success",
                "odeformer_model_canonical": "x_0/(1 + x_0)",
                "reconstruction_r2_arithmetic_mean": 0.1,
                "reconstruction_r2_variance_weighted": 0.2,
                "generalization_r2_arithmetic_mean": 0.3,
                "generalization_r2_variance_weighted": 0.4,
            }
        ],
    )

    paths = recompute_grid.recompute_file(records_path, support, "records_structure_recomputed", "manifest.json")
    updated = [json.loads(line) for line in paths["jsonl"].read_text(encoding="utf-8").splitlines()]

    assert updated[0]["structure_hit_raw"] is False
    assert updated[0]["structure_hit_pruned"] is False
    assert updated[0]["odeformer_outside_basis_term_count"] == 1
    assert "x_0/(x_0 + 1)" in updated[0]["odeformer_outside_basis_terms"]
