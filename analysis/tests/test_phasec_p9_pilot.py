import csv
import copy
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.verify_phasec_p9_pilot import (  # noqa: E402
    CAPPED_VARIANT,
    PILOT_SEED,
    UNCAPPED_VARIANT,
    main,
    registry_rows_from_records,
    verify_criterion_1,
)


GIT_HASH = "abc1234"
STAGE_FP = "stagefp"
CONFIG_FP = "configfp"
SMOKE_RECORD_PATH = (
    REPO_ROOT / "outputs" / "studies" / "regression" / "phase_c" / "smoke_tasks" / "cell_000001.jsonl"
)


def smoke_record_template() -> dict[str, object]:
    line = SMOKE_RECORD_PATH.read_text(encoding="utf-8").splitlines()[0]
    return json.loads(line)


def pilot_indices() -> list[int]:
    return [13, 14, 19, 20, 277, 278, 283, 284, 613, 614, 619, 620, 745, 746, 751, 752]


def record_system_dim(record: dict[str, object]) -> object:
    if "system_dim" in record:
        return record["system_dim"]
    u0 = record.get("u0")
    if isinstance(u0, list):
        return len(u0)
    return ""


def base_record(system_id: int, ic_set: int, condition: str, manifest_index: int) -> dict[str, object]:
    capped = condition == "capped"
    variant = CAPPED_VARIANT if capped else UNCAPPED_VARIANT
    record = copy.deepcopy(smoke_record_template())
    record.update(
        {
            "error": None,
            "git_hash": GIT_HASH,
            "config_fingerprint": CONFIG_FP,
            "stage_cap_behavior_fingerprint": STAGE_FP,
            "manifest_index": manifest_index,
            "system_id": system_id,
            "system_dim": 1 if system_id == 2 else 2 if system_id == 24 else 3 if system_id == 52 else 4,
            "seed": PILOT_SEED,
            "initial_condition_set": ic_set,
            "condition": condition,
            "variant": variant,
            "batch_output_file": f"cell_{manifest_index:06d}.jsonl",
            "exact_support_match_raw": True,
            "exact_support_match_pruned": True,
            "model_terms": [[{"term": "u1", "term_index": 1, "coefficient": 1.0}]],
            "basis_name": "staged_polynomial_basis_with_constant",
            "exact_support_match_definition": "pruned_support_terms_exact_match",
            "duplicate_candidate_structure_evaluations": 0,
            "total_parameter_fit_attempts": 1,
            "total_optimizer_fallback_result_fits": 0,
            "total_optimizer_last_resort_fits": 0,
            "stage_caps": [1] if capped else [None],
            "stage_cap_policy_active": capped,
            "loss": 0.1 if capped else 0.2,
            "r2": 0.99,
        }
    )
    record.pop("success", None)
    record.pop("failure_reason", None)
    return record


def complete_records() -> list[dict[str, object]]:
    records = []
    indices = pilot_indices()
    offset = 0
    for system_id in [2, 24, 52, 63]:
        for ic_set in [1, 2]:
            records.append(base_record(system_id, ic_set, "capped", indices[offset]))
            records.append(base_record(system_id, ic_set, "uncapped", indices[offset + 1]))
            offset += 2
    return records


def write_fixture(tmp_path: Path, records: list[dict[str, object]]) -> tuple[Path, Path, Path]:
    records_dir = tmp_path / "records"
    records_dir.mkdir()
    for index, record in enumerate(records, start=1):
        (records_dir / f"cell_{index:06d}.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")

    manifest_path = tmp_path / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "index",
                "campaign",
                "config_fingerprint",
                "variant",
                "condition",
                "use_pretuning",
                "basis_name",
                "max_fit_attempts",
                "system_id",
                "system_dim",
                "initial_condition_set",
                "seed",
                "representability",
            ],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "index": record["manifest_index"],
                    "campaign": "paper1_phaseC_v1",
                    "config_fingerprint": CONFIG_FP,
                    "variant": record["variant"],
                    "condition": record["condition"],
                    "use_pretuning": "false",
                    "basis_name": record["basis_name"],
                    "max_fit_attempts": "3",
                    "system_id": record["system_id"],
                    "system_dim": record_system_dim(record),
                    "initial_condition_set": record["initial_condition_set"],
                    "seed": record["seed"],
                    "representability": "exact",
                }
            )

    probe_path = tmp_path / "reconstruction_probe.csv"
    with probe_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["cell_key", "reconstruction_probe_ok", "reconstruction_abs_loss_delta"],
        )
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "cell_key": (
                        f"{record['condition']}_sys{record['system_id']}_"
                        f"ic{record['initial_condition_set']}_seed{record['seed']}"
                    ),
                    "reconstruction_probe_ok": "true",
                    "reconstruction_abs_loss_delta": "0",
                }
            )
    return records_dir, manifest_path, probe_path


def write_heartbeat_files(records_dir: Path, records: list[dict[str, object]]) -> None:
    for index, record in enumerate(records, start=1):
        heartbeat_path = records_dir / f"cell_{index:06d}.heartbeat.jsonl"
        events = [
            {"event": "start", "manifest_index": record["manifest_index"]},
            {"event": "level", "manifest_index": record["manifest_index"], "level": 1},
            {"event": "complete", "manifest_index": record["manifest_index"]},
        ]
        heartbeat_path.write_text(
            "".join(json.dumps(event) + "\n" for event in events),
            encoding="utf-8",
        )


def run_checker(monkeypatch, records_dir: Path, manifest_path: Path, probe_path: Path) -> int:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "verify_phasec_p9_pilot.py",
            "--records-dir",
            str(records_dir),
            "--manifest",
            str(manifest_path),
            "--reconstruction-probe",
            str(probe_path),
            "--expected-git-hash",
            GIT_HASH,
            "--expected-stage-cap-behavior-fingerprint",
            STAGE_FP,
        ],
    )
    return main()


def test_complete_pilot_passes(tmp_path, monkeypatch, capsys) -> None:
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, complete_records())

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 0
    assert "16 records, 8 pairs" in capsys.readouterr().out


def test_heartbeat_files_are_not_read(tmp_path, monkeypatch, capsys) -> None:
    records = complete_records()
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, records)
    write_heartbeat_files(records_dir, records)

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 0
    assert "16 records, 8 pairs" in capsys.readouterr().out


def test_result_file_with_multiple_records_exits_nonzero(tmp_path, monkeypatch, capsys) -> None:
    records = complete_records()
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, records)
    duplicated = json.dumps(records[0]) + "\n" + json.dumps(records[0]) + "\n"
    (records_dir / "cell_000001.jsonl").write_text(duplicated, encoding="utf-8")

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 1
    err = capsys.readouterr().err
    assert "expected exactly 1" in err


def test_criterion_1_failure_exits_nonzero(tmp_path, monkeypatch, capsys) -> None:
    records = complete_records()
    records[0]["error"] = "pilot cell failed"
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, records)

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 1
    assert "criterion 1" in capsys.readouterr().err


def test_criterion_1_accepts_real_record_shape_without_success_field() -> None:
    records = [copy.deepcopy(smoke_record_template()) for _ in range(16)]

    verify_criterion_1(registry_rows_from_records(records))


def test_copied_smoke_records_reach_criterion_2_not_success_failure(tmp_path, monkeypatch, capsys) -> None:
    records = [copy.deepcopy(smoke_record_template()) for _ in range(16)]
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, records)

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 1
    err = capsys.readouterr().err
    assert "criterion 2" in err
    assert "success" not in err


def test_criterion_2_failure_exits_nonzero(tmp_path, monkeypatch, capsys) -> None:
    records = complete_records()
    records[0]["git_hash"] = "different"
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, records)

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 1
    assert "criterion 2" in capsys.readouterr().err


def test_criterion_3_failure_exits_nonzero(tmp_path, monkeypatch, capsys) -> None:
    records = complete_records()
    del records[0]["duplicate_candidate_structure_evaluations"]
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, records)

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 1
    assert "criterion 3" in capsys.readouterr().err


def test_criterion_4_failure_exits_nonzero(tmp_path, monkeypatch, capsys) -> None:
    records = complete_records()
    records[0]["basis_name"] = "wrong_basis"
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, records)

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 1
    assert "criterion 4" in capsys.readouterr().err


def test_criterion_5_failure_exits_nonzero(tmp_path, monkeypatch, capsys) -> None:
    records = complete_records()
    records_dir, manifest_path, probe_path = write_fixture(tmp_path, records)
    text = probe_path.read_text(encoding="utf-8")
    probe_path.write_text(text.replace(",0\n", ",1e-12\n", 1), encoding="utf-8")

    assert run_checker(monkeypatch, records_dir, manifest_path, probe_path) == 1
    assert "criterion 5" in capsys.readouterr().err
