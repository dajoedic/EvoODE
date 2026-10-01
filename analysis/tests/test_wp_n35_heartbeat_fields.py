from __future__ import annotations

import json
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_HEARTBEAT = REPO_ROOT / "outputs" / "stage1" / "s0.05_r0.5" / "tasks" / "cell_000001.heartbeat.jsonl"
REAL_RECORD = REPO_ROOT / "outputs" / "stage1" / "s0.05_r0.5" / "tasks" / "cell_000001.jsonl"
RUN_REGRESSION = REPO_ROOT / "studies" / "regression" / "run_regression.jl"
TEST_ROOT = REPO_ROOT / ".pytest_tmp_wp_n35"

NEW_LEVEL_FIELDS = {
    "best_terms",
    "best_params",
    "best_objective",
    "accepted_new_best",
    "stage_transition",
    "previous_stage",
    "new_stage",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def derive_extended_level_fixture() -> Path:
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    TEST_ROOT.mkdir()

    heartbeat_records = read_jsonl(REAL_HEARTBEAT)
    record = read_jsonl(REAL_RECORD)[0]
    level_record = next(item.copy() for item in heartbeat_records if item["event"] == "level")

    level_record.update(
        {
            "best_terms": record["support_terms"],
            "best_params": record["model_terms"],
            "best_objective": level_record["best_loss"],
            "accepted_new_best": True,
            "stage_transition": False,
            "previous_stage": level_record["stage"],
            "new_stage": level_record["stage"],
        }
    )

    path = TEST_ROOT / "cell_000001.wp_n35.heartbeat.jsonl"
    write_jsonl(path, [heartbeat_records[0], level_record, heartbeat_records[-1]])
    return path


def test_wp_n35_extended_heartbeat_fixture_keeps_real_identity_and_new_fields() -> None:
    fixture = derive_extended_level_fixture()
    try:
        records = read_jsonl(fixture)
        start, level, complete = records
        source_level = next(item for item in read_jsonl(REAL_HEARTBEAT) if item["event"] == "level")

        assert start["event"] == "start"
        assert level["event"] == "level"
        assert complete["event"] == "complete"
        assert NEW_LEVEL_FIELDS <= set(level)
        for key in ["manifest_path", "batch_output_file", "system_id", "initial_condition_set", "seed"]:
            assert level[key] == source_level[key]

        assert level["best_terms"] == read_jsonl(REAL_RECORD)[0]["support_terms"]
        assert level["best_params"] == read_jsonl(REAL_RECORD)[0]["model_terms"]
        assert all(
            {"term", "term_index", "coefficient"} <= set(term)
            for equation in level["best_params"]
            for term in equation
        )
        assert all(
            isinstance(term["coefficient"], (int, float))
            for equation in level["best_params"]
            for term in equation
        )
        assert isinstance(level["best_objective"], (int, float))
        assert isinstance(level["accepted_new_best"], bool)
        assert isinstance(level["stage_transition"], bool)
        assert level["previous_stage"] == level["stage"]
        assert level["new_stage"] == level["stage"]
    finally:
        if TEST_ROOT.exists():
            shutil.rmtree(TEST_ROOT)


def test_run_regression_writes_wp_n35_fields_with_record_serializers() -> None:
    source = RUN_REGRESSION.read_text(encoding="utf-8")

    assert "function level_heartbeat_fields(snapshot, basis::AbstractBasis)" in source
    assert ":best_terms => active_term_names(snapshot.best_structure, basis)" in source
    assert ":best_params => active_model_terms(snapshot.best_structure, basis, snapshot.best_params)" in source
    for field in [
        ":best_objective => snapshot.best_objective",
        ":accepted_new_best => snapshot.accepted_new_best",
        ":stage_transition => snapshot.stage_transition",
        ":previous_stage => snapshot.previous_stage",
        ":new_stage => snapshot.new_stage",
    ]:
        assert field in source
    assert "write_heartbeat!(heartbeat, \"level\"; level_heartbeat_fields(snapshot, basis)..." in source
