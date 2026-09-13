import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


CSV_COLUMNS = [
    "run_id",
    "experiment_id",
    "phase",
    "hypothesis",
    "run_type",
    "include_in_paper",
    "system_id",
    "system_name",
    "system_dim",
    "system_representability",
    "system_expected_stage",
    "variant",
    "variant_slug",
    "seed",
    "status",
    "inferred_status",
    "success",
    "failure_reason",
    "started_at",
    "finished_at",
    "loss",
    "objective",
    "exact_support_match",
    "exact_support_match_raw",
    "exact_support_match_pruned",
    "exact_support_match_definition",
    "final_stage",
    "stage_overshoot",
    "wasted_levels",
    "total_loss_evals",
    "total_invalid_evals",
    "elapsed_s",
    "partial",
    "metrics_available",
    "corrupted",
    "campaign_manifest_index",
    "initial_condition_set",
    "config_fingerprint",
    "git_hash",
    "git_dirty",
    "r2",
    "r2_by_dim",
    "total_parameter_fits",
    "total_parameter_fit_attempts",
    "total_ode_solves",
    "stage_cap_behavior_fingerprint",
    "basis_name",
    "support_terms",
    "pruned_support_terms",
    "model_terms",
    "condition",
    "use_pretuning",
    "max_fit_attempts",
    "n_levels",
    "executed_levels",
    "eq_overshoot",
    "eq_final_stages",
    "stage_caps",
    "solver_retcodes",
    "optimizer_retcodes",
    "total_diverged_solves",
    "total_invalid_solves",
    "total_nonfinite_solves",
    "total_solver_unstable_solves",
    "total_step_limit_solves",
    "total_optimizer_limit_hits",
    "total_optimizer_budget_stop_fits",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert campaign history JSONL to a Phase-A-style run_registry.csv."
    )
    parser.add_argument("--input", required=True, help="Campaign history JSONL path.")
    parser.add_argument("--output", required=True, help="Output run_registry.csv path.")
    parser.add_argument(
        "--experiment-id",
        default="campaign_history",
        help="Experiment id to write into the converted registry.",
    )
    return parser.parse_args()


def blank_if_none(value: Any) -> Any:
    return "" if value is None else value


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Expected object at {path}:{line_number}")
            records.append(record)
    if not records:
        raise ValueError(f"Campaign history JSONL contains no records: {path}")
    return records


def system_dim(record: dict[str, Any]) -> Any:
    u0 = record.get("u0")
    if isinstance(u0, list):
        return len(u0)
    support_terms = record.get("support_terms")
    if isinstance(support_terms, list):
        return len(support_terms)
    return ""


def support_match(record: dict[str, Any]) -> Any:
    if record.get("representability") == "surrogate":
        return ""
    return blank_if_none(record.get("pruned_match"))


def phase_from_experiment_id(experiment_id: str) -> str:
    if "phaseC" in experiment_id:
        return "C"
    if "phaseB" in experiment_id:
        return "B"
    if "phaseA" in experiment_id:
        return "A"
    return ""


def row_from_record(record: dict[str, Any], experiment_id: str) -> dict[str, Any]:
    error = record.get("error")
    success = error in ("", None)
    status = "finished" if success else "failed"
    variant = blank_if_none(record.get("variant"))
    system_id = blank_if_none(record.get("system_id"))
    seed = blank_if_none(record.get("seed"))
    ic_set = blank_if_none(record.get("initial_condition_set"))
    manifest_index = blank_if_none(record.get("manifest_index"))
    run_id_parts = [str(part) for part in (manifest_index, variant, system_id, ic_set, seed) if part != ""]

    return {
        "run_id": "_".join(run_id_parts),
        "experiment_id": experiment_id,
        "phase": phase_from_experiment_id(experiment_id),
        "hypothesis": "",
        "run_type": "campaign_cell",
        "include_in_paper": "",
        "system_id": system_id,
        "system_name": blank_if_none(record.get("system_name")),
        "system_dim": system_dim(record),
        "system_representability": blank_if_none(record.get("representability")),
        "system_expected_stage": blank_if_none(record.get("expected_stage")),
        "variant": variant,
        "variant_slug": variant,
        "seed": seed,
        "status": status,
        "inferred_status": status,
        "success": success,
        "failure_reason": "" if success else error,
        "started_at": "",
        "finished_at": blank_if_none(record.get("timestamp")),
        "loss": blank_if_none(record.get("loss")),
        "objective": "",
        "exact_support_match": support_match(record),
        "exact_support_match_raw": blank_if_none(record.get("exact_support_match_raw")),
        "exact_support_match_pruned": blank_if_none(
            record.get("exact_support_match_pruned", record.get("pruned_match"))
        ),
        "exact_support_match_definition": blank_if_none(
            record.get("exact_support_match_definition", "pruned_support_terms_exact_match")
        ),
        "final_stage": blank_if_none(record.get("final_stage")),
        "stage_overshoot": blank_if_none(record.get("stage_overshoot")),
        "wasted_levels": blank_if_none(record.get("wasted_levels")),
        "total_loss_evals": blank_if_none(record.get("total_loss_evals")),
        "total_invalid_evals": "",
        "elapsed_s": blank_if_none(record.get("elapsed_s")),
        "partial": False,
        "metrics_available": success,
        "corrupted": False,
        "campaign_manifest_index": manifest_index,
        "initial_condition_set": ic_set,
        "config_fingerprint": blank_if_none(record.get("config_fingerprint")),
        "git_hash": blank_if_none(record.get("git_hash")),
        "git_dirty": blank_if_none(record.get("git_dirty")),
        "r2": blank_if_none(record.get("r2")),
        "r2_by_dim": blank_if_none(record.get("r2_by_dim")),
        "total_parameter_fits": blank_if_none(record.get("total_parameter_fits")),
        "total_parameter_fit_attempts": blank_if_none(
            record.get("total_parameter_fit_attempts")
        ),
        "total_ode_solves": blank_if_none(record.get("total_ode_solves")),
        "stage_cap_behavior_fingerprint": blank_if_none(
            record.get("stage_cap_behavior_fingerprint")
        ),
        "basis_name": blank_if_none(record.get("basis_name")),
        "support_terms": json_cell(record.get("support_terms")),
        "pruned_support_terms": json_cell(record.get("pruned_support_terms")),
        "model_terms": json_cell(record.get("model_terms")),
        "condition": blank_if_none(record.get("condition")),
        "use_pretuning": blank_if_none(record.get("use_pretuning")),
        "max_fit_attempts": blank_if_none(record.get("max_fit_attempts")),
        "n_levels": blank_if_none(record.get("n_levels")),
        "executed_levels": blank_if_none(record.get("executed_levels")),
        "eq_overshoot": json_cell(record.get("eq_overshoot")),
        "eq_final_stages": json_cell(record.get("eq_final_stages")),
        "stage_caps": json_cell(record.get("stage_caps")),
        "solver_retcodes": json_cell(record.get("solver_retcodes")),
        "optimizer_retcodes": json_cell(record.get("optimizer_retcodes")),
        "total_diverged_solves": blank_if_none(record.get("total_diverged_solves")),
        "total_invalid_solves": blank_if_none(record.get("total_invalid_solves")),
        "total_nonfinite_solves": blank_if_none(record.get("total_nonfinite_solves")),
        "total_solver_unstable_solves": blank_if_none(
            record.get("total_solver_unstable_solves")
        ),
        "total_step_limit_solves": blank_if_none(record.get("total_step_limit_solves")),
        "total_optimizer_limit_hits": blank_if_none(record.get("total_optimizer_limit_hits")),
        "total_optimizer_budget_stop_fits": blank_if_none(
            record.get("total_optimizer_budget_stop_fits")
        ),
    }


def write_registry(records: list[dict[str, Any]], output_path: Path, experiment_id: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(row_from_record(record, experiment_id))


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        records = read_records(input_path)
        write_registry(records, output_path, args.experiment_id)
        print(f"Converted {len(records)} campaign records")
        print(f"  Input:  {input_path}")
        print(f"  Output: {output_path}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
