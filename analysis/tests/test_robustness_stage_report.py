from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("analysis/scripts/aggregate/robustness_stage_report.py")
REAL_STAGE0_TASKS = Path("outputs/wp_n32_stage0/tasks")
REAL_C1_TASKS = Path("outputs/phase_c_campaign_221a3a7/tasks")


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def read_real_record(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def run_report(stage_records: Path, reference_c1: Path, output_dir: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--stage-records",
            str(stage_records),
            "--reference-c1",
            str(reference_c1),
            "--output-dir",
            str(output_dir),
            *extra,
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_robustness_stage_report_runs_without_clean_eval_and_skips_heartbeats(tmp_path: Path) -> None:
    stage_dir = tmp_path / "stage"
    ref_dir = tmp_path / "ref"
    stage_record = read_real_record(REAL_STAGE0_TASKS / "cell_000001.jsonl")
    ref_record = read_real_record(REAL_C1_TASKS / "cell_000001.jsonl")
    write_jsonl(stage_dir / "cell_000001.jsonl", [stage_record])
    write_jsonl(ref_dir / "cell_000001.jsonl", [ref_record])
    (stage_dir / "cell_000001.heartbeat.jsonl").write_text(
        (REAL_STAGE0_TASKS / "cell_000001.heartbeat.jsonl").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    result = run_report(stage_dir, ref_dir, tmp_path / "report")

    assert result.returncode == 0, result.stderr
    with (tmp_path / "report" / "robustness_stage_report.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["clean_eval_status"] == "missing_clean_eval"
    assert rows[0]["clean_reconstruction_r2_arithmetic_mean"] == ""
    assert rows[0]["check_no_error_no_failure_reason"] == "passed"
    assert rows[0]["check_method_fingerprint"] == "passed"
    assert rows[0]["check_new_fields_non_null"] == "passed"
    assert rows[0]["check_observed_data_hash"] == "not_checked"
    assert rows[0]["elapsed_s_capacity_context_no_evidence"] != ""


def test_robustness_stage_report_joins_clean_eval_and_export_index(tmp_path: Path) -> None:
    stage_record = read_real_record(REAL_STAGE0_TASKS / "cell_000001.jsonl")
    ref_record = read_real_record(REAL_C1_TASKS / "cell_000001.jsonl")
    stage_path = tmp_path / "stage.jsonl"
    ref_path = tmp_path / "ref.jsonl"
    clean_path = tmp_path / "clean.jsonl"
    export_path = tmp_path / "index.csv"
    write_jsonl(stage_path, [stage_record])
    write_jsonl(ref_path, [ref_record])
    write_jsonl(
        clean_path,
        [
            {
                "variant": stage_record["variant"],
                "system_id": stage_record["system_id"],
                "source_initial_condition_set": stage_record["initial_condition_set"],
                "seed": stage_record["seed"],
                "reconstruction_r2_arithmetic_mean": 0.9,
                "reconstruction_r2_variance_weighted": 0.91,
                "generalization_r2_arithmetic_mean": 0.8,
                "generalization_r2_variance_weighted": 0.81,
                "reconstruction_diverged_or_nonfinite": False,
                "generalization_diverged_or_nonfinite": False,
                "reconstruction_prediction_state_sha256": "abc",
                "generalization_prediction_state_sha256": "def",
            }
        ],
    )
    with export_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "system_id",
                "initial_condition_set",
                "noise_sigma",
                "subsample_rho",
                "noise_realization",
                "time_sha256",
                "state_sha256",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "system_id": stage_record["system_id"],
                "initial_condition_set": stage_record["initial_condition_set"],
                "noise_sigma": stage_record["noise_sigma"],
                "subsample_rho": stage_record["subsample_rho"],
                "noise_realization": stage_record["noise_realization"],
                "time_sha256": stage_record["observed_data_sha256"]["time_sha256"],
                "state_sha256": stage_record["observed_data_sha256"]["state_sha256"],
            }
        )

    result = run_report(
        stage_path,
        ref_path,
        tmp_path / "report",
        "--clean-eval",
        str(clean_path),
        "--export-index",
        str(export_path),
    )

    assert result.returncode == 0, result.stderr
    with (tmp_path / "report" / "robustness_stage_report.csv").open("r", encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["clean_eval_status"] == "present"
    assert row["clean_reconstruction_r2_arithmetic_mean"] == "0.9"
    assert row["clean_generalization_r2_variance_weighted"] == "0.81"
    assert row["reconstruction_prediction_state_sha256"] == "abc"
    assert row["check_observed_data_hash"] == "passed"
