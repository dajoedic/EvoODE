from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_DIR = Path("outputs/wp_n33a_stage_report")
EXPECTED_FINGERPRINT = "0c9672de35c75a9d"
NEW_FIELDS = [
    "noise_sigma",
    "subsample_rho",
    "noise_realization",
    "data_condition_fingerprint",
    "observed_data_sha256",
    "n_observed_points",
    "clamp_val",
]
R2_FIELDS = [
    "clean_reconstruction_r2_arithmetic_mean",
    "clean_reconstruction_r2_variance_weighted",
    "clean_generalization_r2_arithmetic_mean",
    "clean_generalization_r2_variance_weighted",
    "clean_reconstruction_diverged_or_nonfinite",
    "clean_generalization_diverged_or_nonfinite",
    "reconstruction_prediction_state_sha256",
    "generalization_prediction_state_sha256",
]


def is_record_file(path: Path) -> bool:
    return path.suffix == ".jsonl" and not path.name.endswith(".heartbeat.jsonl")


def read_jsonl_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    if path.is_file():
        files = [path]
    elif (path / "tasks").is_dir():
        files = sorted(p for p in (path / "tasks").glob("cell_*.jsonl") if is_record_file(p))
    else:
        files = sorted(p for p in path.glob("*.jsonl") if is_record_file(p))
    rows: list[dict[str, Any]] = []
    for file in files:
        for line in file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_clean_eval(path: Path | None) -> dict[tuple[str, int, int, int], dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    rows: list[dict[str, Any]]
    if path.suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
    else:
        rows = read_jsonl_records(path)
    return {clean_key(row): row for row in rows}


def load_export_index(path: Path | None) -> dict[tuple[int, int, str, str, int], dict[str, str]]:
    if path is None or not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        (
            int(row["system_id"]),
            int(row["initial_condition_set"]),
            float_text(row["noise_sigma"]),
            float_text(row["subsample_rho"]),
            int(row["noise_realization"]),
        ): row
        for row in rows
    }


def ref_key(record: dict[str, Any]) -> tuple[str, int, int, int]:
    return (
        str(record["variant"]),
        int(record["system_id"]),
        int(record["initial_condition_set"]),
        int(record["seed"]),
    )


def clean_key(row: dict[str, Any]) -> tuple[str, int, int, int]:
    ic = row.get("source_initial_condition_set", row.get("initial_condition_set"))
    return (str(row["variant"]), int(row["system_id"]), int(ic), int(row["seed"]))


def float_text(value: Any) -> str:
    return format(float(value), ".17g")


def cell_key(record: dict[str, Any]) -> str:
    return f"{record['variant']}|sys{int(record['system_id']):04d}|ic{int(record['initial_condition_set'])}|seed{int(record['seed'])}"


def as_json(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def ratio(candidate: Any, reference: Any) -> str:
    if candidate is None or reference in (None, 0, "0", ""):
        return ""
    return format(float(candidate) / float(reference), ".17g")


def stage_cap_change(candidate: Any, reference: Any) -> str:
    if candidate is None or reference is None:
        return ""
    changes: list[str] = []
    for idx, (cand, ref) in enumerate(zip(candidate, reference), start=1):
        if cand == ref:
            label = "gleich"
        elif cand is None and ref is not None:
            label = "zu nothing"
        elif ref is None and cand is not None:
            label = "enger"
        elif int(cand) < int(ref):
            label = "enger"
        else:
            label = "weiter"
        changes.append(f"eq{idx}:{label}")
    return "; ".join(changes)


def observed_hash_match(record: dict[str, Any], export_index: dict[tuple[int, int, str, str, int], dict[str, str]]) -> str:
    if not export_index:
        return "not_checked"
    key = (
        int(record["system_id"]),
        int(record["initial_condition_set"]),
        float_text(record.get("noise_sigma", 0.0)),
        float_text(record.get("subsample_rho", 0.0)),
        int(record.get("noise_realization", 0)),
    )
    expected = export_index.get(key)
    if expected is None:
        return "not_found"
    observed = record.get("observed_data_sha256")
    if not isinstance(observed, dict):
        return "not_passed"
    ok = observed.get("time_sha256") == expected.get("time_sha256") and observed.get("state_sha256") == expected.get("state_sha256")
    return "passed" if ok else "not_passed"


def non_null_new_fields(record: dict[str, Any]) -> str:
    missing = [field for field in NEW_FIELDS if record.get(field) is None]
    return "passed" if not missing else "not_passed:" + "|".join(missing)


def hard_checks(record: dict[str, Any], export_index: dict[tuple[int, int, str, str, int], dict[str, str]]) -> dict[str, str]:
    no_error = record.get("error") in (None, "")
    no_failure = record.get("failure_reason") in (None, "")
    fingerprint = str(record.get("config_fingerprint")) == EXPECTED_FINGERPRINT and float(record.get("clamp_val", 0.0)) == 10.0
    return {
        "check_no_error_no_failure_reason": "passed" if no_error and no_failure else "not_passed",
        "check_method_fingerprint": "passed" if fingerprint else "not_passed",
        "check_new_fields_non_null": non_null_new_fields(record),
        "check_observed_data_hash": observed_hash_match(record, export_index),
    }


def clean_value(row: dict[str, Any] | None, key: str) -> Any:
    if row is None:
        return ""
    value = row.get(key)
    return "" if value is None else value


def build_rows(
    stage_records: list[dict[str, Any]],
    reference_records: list[dict[str, Any]],
    clean_eval: dict[tuple[str, int, int, int], dict[str, Any]],
    export_index: dict[tuple[int, int, str, str, int], dict[str, str]],
) -> list[dict[str, Any]]:
    references = {ref_key(record): record for record in reference_records}
    rows: list[dict[str, Any]] = []
    for record in sorted(stage_records, key=lambda row: (int(row["system_id"]), int(row["initial_condition_set"]), int(row["seed"]), str(row["variant"]))):
        reference = references.get(ref_key(record))
        clean = clean_eval.get(ref_key(record))
        row: dict[str, Any] = {
            "cell_key": cell_key(record),
            "c1_cell_key": cell_key(reference) if reference else "",
            "variant": record.get("variant", ""),
            "system_id": record.get("system_id", ""),
            "initial_condition_set": record.get("initial_condition_set", ""),
            "seed": record.get("seed", ""),
            "noise_sigma": record.get("noise_sigma", ""),
            "subsample_rho": record.get("subsample_rho", ""),
            "noise_realization": record.get("noise_realization", ""),
            "clamp_val": record.get("clamp_val", ""),
            "executed_levels": record.get("executed_levels", ""),
            "c1_executed_levels": reference.get("executed_levels", "") if reference else "",
            "total_loss_evals": record.get("total_loss_evals", ""),
            "c1_total_loss_evals": reference.get("total_loss_evals", "") if reference else "",
            "loss_eval_factor_vs_c1": ratio(record.get("total_loss_evals"), reference.get("total_loss_evals") if reference else None),
            "total_parameter_fits": record.get("total_parameter_fits", ""),
            "c1_total_parameter_fits": reference.get("total_parameter_fits", "") if reference else "",
            "parameter_fit_factor_vs_c1": ratio(record.get("total_parameter_fits"), reference.get("total_parameter_fits") if reference else None),
            "final_stage": record.get("final_stage", ""),
            "c1_final_stage": reference.get("final_stage", "") if reference else "",
            "stage_caps": as_json(record.get("stage_caps")),
            "c1_stage_caps": as_json(reference.get("stage_caps") if reference else None),
            "stage_caps_change_vs_c1": stage_cap_change(record.get("stage_caps"), reference.get("stage_caps") if reference else None),
            "support_surrogate_mark": "" if record.get("representability") == "exact" else "surrogate",
            "exact_support_match_raw": record.get("exact_support_match_raw", "") if record.get("representability") == "exact" else "",
            "exact_support_match_pruned": record.get("exact_support_match_pruned", "") if record.get("representability") == "exact" else "",
            "elapsed_s_capacity_context_no_evidence": record.get("elapsed_s", ""),
            "clean_eval_status": "present" if clean else "missing_clean_eval",
        }
        row.update(
            {
                "clean_reconstruction_r2_arithmetic_mean": clean_value(clean, "reconstruction_r2_arithmetic_mean"),
                "clean_reconstruction_r2_variance_weighted": clean_value(clean, "reconstruction_r2_variance_weighted"),
                "clean_generalization_r2_arithmetic_mean": clean_value(clean, "generalization_r2_arithmetic_mean"),
                "clean_generalization_r2_variance_weighted": clean_value(clean, "generalization_r2_variance_weighted"),
                "clean_reconstruction_diverged_or_nonfinite": clean_value(clean, "reconstruction_diverged_or_nonfinite"),
                "clean_generalization_diverged_or_nonfinite": clean_value(clean, "generalization_diverged_or_nonfinite"),
                "reconstruction_prediction_state_sha256": clean_value(clean, "reconstruction_prediction_state_sha256"),
                "generalization_prediction_state_sha256": clean_value(clean, "generalization_prediction_state_sha256"),
            }
        )
        row.update(hard_checks(record, export_index))
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    table_cols = [
        "cell_key",
        "c1_cell_key",
        "executed_levels",
        "total_loss_evals",
        "loss_eval_factor_vs_c1",
        "total_parameter_fits",
        "parameter_fit_factor_vs_c1",
        "final_stage",
        "stage_caps_change_vs_c1",
        "exact_support_match_raw",
        "exact_support_match_pruned",
        "clean_reconstruction_r2_arithmetic_mean",
        "clean_reconstruction_r2_variance_weighted",
        "clean_generalization_r2_arithmetic_mean",
        "clean_generalization_r2_variance_weighted",
        "elapsed_s_capacity_context_no_evidence",
    ]
    check_cols = [
        "cell_key",
        "check_no_error_no_failure_reason",
        "check_method_fingerprint",
        "check_new_fields_non_null",
        "check_observed_data_hash",
    ]
    with path.open("w", encoding="utf-8") as handle:
        handle.write("# Robustness Stage Gate Report\n\n")
        handle.write("`elapsed_s` is capacity context only, not evidence.\n\n")
        write_md_table(handle, table_cols, rows)
        handle.write("\n## Hard Checks\n\n")
        write_md_table(handle, check_cols, rows)


def write_md_table(handle, columns: list[str], rows: list[dict[str, Any]]) -> None:
    handle.write("| " + " | ".join(columns) + " |\n")
    handle.write("| " + " | ".join("---" for _ in columns) + " |\n")
    for row in rows:
        values = [str(row.get(col, "")).replace("|", "\\|") for col in columns]
        handle.write("| " + " | ".join(values) + " |\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a per-cell C-6 staged-entry gate report.")
    parser.add_argument("--stage-records", required=True, type=Path)
    parser.add_argument("--clean-eval", type=Path)
    parser.add_argument("--reference-c1", required=True, type=Path)
    parser.add_argument("--export-index", type=Path)
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, type=Path)
    args = parser.parse_args()

    stage_records = read_jsonl_records(args.stage_records)
    reference_records = read_jsonl_records(args.reference_c1)
    rows = build_rows(stage_records, reference_records, load_clean_eval(args.clean_eval), load_export_index(args.export_index))
    csv_path = args.output_dir / "robustness_stage_report.csv"
    md_path = args.output_dir / "robustness_stage_report.md"
    write_csv(csv_path, rows)
    write_markdown(md_path, rows)
    print(f"rows={len(rows)}")
    print(f"csv={csv_path}")
    print(f"markdown={md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
