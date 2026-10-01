from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("analysis/scripts/aggregate/compare_phasec_controls.py")
REAL_STAGE0_TASKS = Path("outputs/wp_n32_stage0/tasks")
REAL_C1_TASKS = Path("outputs/phase_c_campaign_221a3a7/tasks")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def record(loss: float = 1.0) -> dict:
    return {
        "condition": "capped",
        "variant": "evogrow_v2_2_stage_capped",
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


def test_compare_phasec_controls_skips_heartbeats_in_directory_input(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    reference = tmp_path / "reference"
    candidate.mkdir()
    reference.mkdir()
    stage_record = json.loads((REAL_STAGE0_TASKS / "cell_000001.jsonl").read_text(encoding="utf-8").splitlines()[0])
    c1_record = json.loads((REAL_C1_TASKS / "cell_000001.jsonl").read_text(encoding="utf-8").splitlines()[0])
    write_jsonl(candidate / "cell_000001.jsonl", [stage_record])
    write_jsonl(reference / "cell_000001.jsonl", [c1_record])
    (candidate / "cell_000001.heartbeat.jsonl").write_text(
        (REAL_STAGE0_TASKS / "cell_000001.heartbeat.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = run_compare(candidate, reference)

    assert result.returncode == 0
    assert "Compared 1 matching records with no differences" in result.stdout


def test_compare_phasec_controls_reports_missing_field_side(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.jsonl"
    reference = tmp_path / "reference.jsonl"
    bad = record()
    del bad["loss"]
    write_jsonl(candidate, [bad])
    write_jsonl(reference, [record()])

    result = run_compare(candidate, reference)

    assert result.returncode == 1
    assert "field loss missing on candidate" in result.stdout


def test_compare_phasec_controls_uses_variant_key_and_ignores_other_variants(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.jsonl"
    reference = tmp_path / "reference.jsonl"
    other_variant = record(loss=99.0)
    other_variant["variant"] = "evogrow_v2_2_stage_local"
    write_jsonl(candidate, [record(), other_variant])
    write_jsonl(reference, [record()])

    result = run_compare(candidate, reference)

    assert result.returncode == 0
    assert "Compared 1 matching records with no differences" in result.stdout
