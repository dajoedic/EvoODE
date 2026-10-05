from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from experiments.annihilator_gate2a_v3.config import Settings
from experiments.annihilator_gate2a_v3.diagnostics import ambiguity_diagnostic as diag
from experiments.annihilator_gate2a_v3.oracle import reference_for


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "record_f2_seed50000.json"


def _base_record() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def _record(function: str, group: str, seed: int, state: str, *, sources=None) -> dict:
    record = dict(_base_record())
    record.update(
        {
            "function": function,
            "group": group,
            "seed": seed,
            "state": state,
            "ambiguity_sources": sources or [],
            "angle_degrees": 0.0,
            "tested_classes": 3,
            "aml_iterations": 5,
            "wall_clock_seconds": 0.25,
        }
    )
    return record


def _six_function_records(states_by_group: dict[str, list[str]], *, reps: int = 10) -> list[dict]:
    out = []
    for k in range(reps):
        for function in diag.GROUPS["N1"]:
            state = states_by_group["N1"][k % len(states_by_group["N1"])]
            out.append(_record(function, "N1", diag.SEED_BASE + k, state, sources=["A1"] if state == "AMBIGUOUS" else []))
        for function in diag.GROUPS["I"]:
            state = states_by_group["I"][k % len(states_by_group["I"])]
            out.append(_record(function, "I", diag.SEED_BASE + k, state, sources=["A2"] if state == "AMBIGUOUS" else []))
    return out


def test_summarize_criteria_on_and_near_thresholds():
    interesting = _six_function_records(
        {
            "N1": ["AMBIGUOUS"] * 5 + ["CORRECT"] * 5,
            "I": ["CORRECT"] * 8 + ["AMBIGUOUS"] + ["WRONG"],
        }
    )
    summary = diag.summarize_records(interesting)
    assert summary["criteria"]["B1"]["passed"] is True
    assert summary["criteria"]["B2"]["passed"] is True
    assert summary["criteria"]["B3"]["passed"] is True
    assert summary["criteria"]["B4"]["passed"] is True
    assert summary["verdict"] == "interesting"

    near = _six_function_records(
        {
            "N1": ["AMBIGUOUS"] * 4 + ["CORRECT"] * 4 + ["WRONG"] * 2,
            "I": ["CORRECT"] * 6 + ["AMBIGUOUS"] * 4,
        }
    )
    summary = diag.summarize_records(near)
    assert summary["criteria"]["B1"]["passed"] is False
    assert summary["criteria"]["B2"]["passed"] is False
    assert summary["criteria"]["B3"]["passed"] is False
    assert summary["criteria"]["B4"]["passed"] is False
    assert summary["verdict"] == "negative"


def test_b1_passes_when_n1_has_no_unambiguous_outputs():
    records = _six_function_records(
        {
            "N1": ["AMBIGUOUS"] * 10,
            "I": ["CORRECT"] * 8 + ["AMBIGUOUS"] * 2,
        }
    )
    summary = diag.summarize_records(records)
    assert summary["criteria"]["B1"]["value"] == 0.0
    assert summary["criteria"]["B1"]["passed"] is True


def test_unequal_n_is_incomplete():
    records = _six_function_records({"N1": ["AMBIGUOUS"], "I": ["CORRECT"]}, reps=2)
    records.pop()
    summary = diag.summarize_records(records)
    assert summary["complete_equal_n"] is False
    assert summary["criteria"] is None
    assert summary["verdict"] == "incomplete"


def test_principal_angle_reference_and_orthogonal_vector():
    (r, d), ref = reference_for("F2", "wide")
    cls = (r, d)
    cache = {}
    assert diag.principal_angle_degrees(ref, "F2", cls, 1, cache) < 1e-5
    orthogonal = np.array([ref[1], -ref[0]], dtype=float)
    assert abs(diag.principal_angle_degrees(orthogonal, "F2", cls, 1, cache) - 90.0) < 1e-6


def test_resume_skips_existing_record():
    diag.OUTDIR.mkdir(parents=True, exist_ok=True)
    records = diag.OUTDIR / "resume_test_records.jsonl"
    records.write_text(json.dumps({"function": "F2", "seed": 50000}) + "\n")
    assert diag.completed_keys(records) == {("F2", 50000)}
    tasks = [task for task in diag.tasks_for_reps(1) if task not in diag.completed_keys(records)]
    assert ("F2", 50000) not in tasks
    assert len(tasks) == 5
    records.unlink()


def test_parts_cover_open_tasks_after_pilot_records():
    parts = [diag.tasks_for_part(100, (index, 11), diag.RECORDS_PATH) for index in range(11)]
    union = {task for part in parts for task in part}
    completed = diag.completed_keys(diag.RECORDS_PATH)
    expected = set(diag.tasks_for_reps(100)) - completed
    assert union == expected
    assert sum(len(part) for part in parts) == 588
    assert len(union) == 588
    assert sum(len(part) for part in parts) == sum(len(set(part)) for part in parts)
    sizes = [len(part) for part in parts]
    assert max(sizes) - min(sizes) <= 1


def test_merge_aborts_on_duplicate_between_main_and_part(tmp_path):
    outdir = tmp_path / "diagnostic_ambiguity"
    part_dir = outdir / "parts" / "part_0_of_2"
    part_dir.mkdir(parents=True)
    record = _base_record()
    (outdir / "records.jsonl").write_text(json.dumps(record) + "\n")
    (part_dir / "records.jsonl").write_text(json.dumps(record) + "\n")
    with pytest.raises(SystemExit):
        diag.merge_records(outdir, reps=100)


def test_nullspace_cache_treats_partial_file_as_empty_and_merges(tmp_path):
    cache_path = tmp_path / "nullspace_cache.json"
    log_path = tmp_path / "run.log"
    cache_path.write_text("{")
    assert diag.load_nullspace_cache(cache_path, log_path) == {}
    assert "WARNING ignoring unreadable nullspace cache" in log_path.read_text()

    diag.save_nullspace_cache({"F2:1,0": {"basis": [[1.0]], "n_exact": 1}}, cache_path, log_path)
    diag.save_nullspace_cache({"F2:2,0": {"basis": [[0.0, 1.0]], "n_exact": 1}}, cache_path, log_path)
    cache = json.loads(cache_path.read_text())
    assert set(cache) == {"F2:1,0", "F2:2,0"}


def test_progress_log_omits_state_and_ambiguity_fields(tmp_path):
    path = tmp_path / "run.log"
    record = _base_record()
    diag.log_progress(record, path)
    line = path.read_text()
    for forbidden in ("NONE", "AMBIGUOUS", "CORRECT", "TRUE_NOT_REF", "WRONG", "A1", "A2", "A3", "bootstrap"):
        assert forbidden not in line


def test_single_real_fixture_has_required_shape():
    record = _base_record()
    assert record["function"] == "F2"
    assert record["seed"] == 50000
    assert record["settings"]["ell_max"] == 4
    assert record["settings"]["boot_reps"] == Settings().boot_reps
    assert "selection" in record
    assert "tested_classes" in record
