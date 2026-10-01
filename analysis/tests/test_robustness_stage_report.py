from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path("analysis/scripts/aggregate/robustness_stage_report.py")

STAGE0_RECORD = {
    "variant": "evogrow_v2_2_stage_capped",
    "system_id": 1,
    "initial_condition_set": 1,
    "seed": 42,
    "noise_sigma": 0.0,
    "subsample_rho": 0.0,
    "noise_realization": 0,
    "data_condition_fingerprint": "084c7e70f99a50c3",
    "observed_data_sha256": {
        "hash_format": "sha256_raw_little_endian_float64",
        "time_sha256": "ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f",
        "state_sha256": "0ee16225ff89698a75ca1dd4d2560af9956e8ab3b3b0058633eb0205457986e8",
    },
    "n_observed_points": 512,
    "clamp_val": 10.0,
    "config_fingerprint": "0c9672de35c75a9d",
    "error": None,
    "failure_reason": None,
    "executed_levels": 1,
    "total_loss_evals": 1609,
    "total_parameter_fits": 30,
    "final_stage": 1,
    "stage_caps": [None],
    "representability": "exact",
    "exact_support_match_raw": True,
    "exact_support_match_pruned": True,
    "elapsed_s": 8.7268215,
}

STAGE1_RECORD = {
    **STAGE0_RECORD,
    "noise_sigma": 0.01,
    "noise_realization": 1,
    "data_condition_fingerprint": "1696ce8b0e80990d",
    "observed_data_sha256": {
        "hash_format": "sha256_raw_little_endian_float64",
        "time_sha256": "ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f",
        "state_sha256": "e7e535a1b26c412cd6b62aaca038e2591610e84bbe23c2213afd0b9cd8ea23d3",
    },
    "executed_levels": 20,
    "total_loss_evals": 310879,
    "total_parameter_fits": 410,
    "final_stage": 5,
    "elapsed_s": 50.2707988,
}

C1_RECORD = {
    **STAGE0_RECORD,
    "elapsed_s": 15.092356005,
}

# Frozen from the pre-WP-N33a2 stage-1 export index, line 2, 2026-10-01.
# The unquoted state_shape value [512,1] creates one extra CSV field.
BROKEN_STAGE1_INDEX_HEADER = (
    "system_id,initial_condition_set,dimension,noise_sigma,subsample_rho,noise_realization,"
    "noise_model,data_condition_fingerprint,n_observed_points,hash_format,time_axis_order,"
    "state_axis_order,time_shape,state_shape,time_min,time_max,state_min,state_max,time_sha256,"
    "state_sha256,time_path,state_path,cell_dir,dtype,byte_order"
)
BROKEN_STAGE1_INDEX_ROW = (
    "1,1,1,0.01,0.0,1,multiplicative_gaussian_iid,1696ce8b0e80990d,512,"
    "sha256_raw_little_endian_float64,time,time_by_dimension_c_order,[512],[512,1],0.0,10.0,"
    "1.0664403489075365,9.917848753842367,"
    "ffad3499269c08c6bd22e9e5c5d2ab32bbf827e2037cbdd6e73571aeab04432f,"
    "e7e535a1b26c412cd6b62aaca038e2591610e84bbe23c2213afd0b9cd8ea23d3,"
    "cells\\system_0001_ic1_time_f64le.bin,cells\\system_0001_ic1_state_f64le_c_order.bin,"
    "system_0001_ic1_sigma_0p01_rho_0_realization_1,float64,little_endian"
)


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")


def write_corrected_stage1_index(path: Path, header: str, broken_row: str) -> None:
    columns = header.split(",")
    fields = broken_row.split(",")
    assert len(fields) == len(columns) + 1
    fixed_fields = fields[:13] + [fields[13] + "," + fields[14]] + fields[15:]
    assert len(fixed_fields) == len(columns)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow(dict(zip(columns, fixed_fields)))


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
    stage_record = STAGE0_RECORD
    ref_record = C1_RECORD
    write_jsonl(stage_dir / "cell_000001.jsonl", [stage_record])
    write_jsonl(ref_dir / "cell_000001.jsonl", [ref_record])
    (stage_dir / "cell_000001.heartbeat.jsonl").write_text('{"heartbeat": true}\n', encoding="utf-8")

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
    stage_record = STAGE0_RECORD
    ref_record = C1_RECORD
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


def test_export_index_rejects_real_unquoted_stage1_row(tmp_path: Path) -> None:
    stage_record = STAGE1_RECORD
    ref_record = C1_RECORD
    stage_path = tmp_path / "stage.jsonl"
    ref_path = tmp_path / "ref.jsonl"
    export_path = tmp_path / "broken_index.csv"
    write_jsonl(stage_path, [stage_record])
    write_jsonl(ref_path, [ref_record])
    header, first_row = BROKEN_STAGE1_INDEX_HEADER, BROKEN_STAGE1_INDEX_ROW
    export_path.write_text(header + "\n" + first_row + "\n", encoding="utf-8")

    result = run_report(stage_path, ref_path, tmp_path / "report", "--export-index", str(export_path))

    assert result.returncode != 0
    assert "has 26 fields, expected 25" in result.stderr
    assert "Regenerate the index with quoted CSV fields" in result.stderr


def test_export_index_accepts_quoted_real_stage1_row_and_hash_passes(tmp_path: Path) -> None:
    stage_record = STAGE1_RECORD
    ref_record = C1_RECORD
    stage_path = tmp_path / "stage.jsonl"
    ref_path = tmp_path / "ref.jsonl"
    export_path = tmp_path / "quoted_index.csv"
    write_jsonl(stage_path, [stage_record])
    write_jsonl(ref_path, [ref_record])
    header, first_row = BROKEN_STAGE1_INDEX_HEADER, BROKEN_STAGE1_INDEX_ROW
    write_corrected_stage1_index(export_path, header, first_row)

    result = run_report(stage_path, ref_path, tmp_path / "report", "--export-index", str(export_path))

    assert result.returncode == 0, result.stderr
    with (tmp_path / "report" / "robustness_stage_report.csv").open("r", encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert row["check_observed_data_hash"] == "passed"
