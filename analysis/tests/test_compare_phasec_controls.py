from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("analysis/scripts/aggregate/compare_phasec_controls.py")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def record(loss: float = 1.0) -> dict:
    return {
        "condition": "capped",
        "system_id": 1,
        "initial_condition_set": 1,
        "seed": 42,
        "loss": loss,
        "support_terms": [["1", "x_0"]],
        "model_terms": [[{"term_index": 1, "term": "1", "coefficient": 2.0}]],
        "total_loss_evals": 17,
        "stage_caps": [2],
    }


def run_compare(candidate: Path, reference: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--candidate", str(candidate), "--reference-c1", str(reference)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_compare_phasec_controls_accepts_identical_records(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.jsonl"
    reference = tmp_path / "reference.jsonl"
    write_jsonl(candidate, [record()])
    write_jsonl(reference, [record()])

    result = run_compare(candidate, reference)

    assert result.returncode == 0
    assert "no differences" in result.stdout


def test_compare_phasec_controls_reports_field_difference(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.jsonl"
    reference = tmp_path / "reference.jsonl"
    write_jsonl(candidate, [record(loss=1.25)])
    write_jsonl(reference, [record(loss=1.0)])

    result = run_compare(candidate, reference)

    assert result.returncode == 1
    assert "field loss differs" in result.stdout
