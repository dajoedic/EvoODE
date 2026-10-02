from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from baselines import harness
from baselines import run_odeformer_grid


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.run_phasec_noise_sindy_baselines import (  # noqa: E402
    data_sha,
    expand_stage_report_paths,
    read_export_index,
    read_index_cell,
)
from scripts.aggregate.run_phasec_sindy_baseline import load_phase_c_support  # noqa: E402
from scripts.aggregate.run_wp_n6_sindy_baseline import (  # noqa: E402
    integrate_truth,
    load_benchmark,
    polynomial_true_terms,
)
from utils.metrics import aggregate_equation_metrics, term_set_metrics  # noqa: E402


DEFAULT_CONFIG = Path("baselines/configs/odeformer_grid.json")
DEFAULT_OUTPUT_DIR = Path("outputs/wp_n38_noise_odeformer")
DEFAULT_EXPORT_INDICES = [
    Path("outputs/stage1/data_export/index.csv"),
    Path("outputs/stage2/data_export/index.csv"),
    Path("outputs/stage3/data_export/index.csv"),
]
DEFAULT_STAGE_REPORTS = [
    "outputs/phase_c_robustness_stage2_5dd1df8/robustness_stage_report/",
    "outputs/stage1/*/report/",
    "outputs/stage2/*/report/",
]
R2_THRESHOLD = 0.9
CONTROL_REFERENCE = Path("analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_wp_n23/records.jsonl")
ABS_TOL = 1e-8
REL_TOL = 1e-8
CONTROL_R2_FIELDS = [
    "reconstruction_r2_arithmetic_mean",
    "reconstruction_r2_variance_weighted",
    "generalization_r2_arithmetic_mean",
    "generalization_r2_variance_weighted",
]


def fail(message: str) -> None:
    raise ValueError(message)


def resolve_repo_path(path: str | Path) -> Path:
    value = Path(path)
    return value.resolve() if value.is_absolute() else (REPO_ROOT / value).resolve()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def selected_config_objects(config_path: Path, config_ids: set[str] | None = None) -> list[dict[str, Any]]:
    config = load_json(config_path)
    config["environment_id"] = "reference"
    configs = run_odeformer_grid.selected_config_objects(config, config_ids)
    run_odeformer_grid.preflight_odeformer_constant_optimization(configs)
    return configs


def clean_time_grid(config_path: Path) -> np.ndarray:
    config = load_json(config_path)
    return np.linspace(float(config.get("t_start", 0.0)), float(config.get("t_end", 10.0)), int(config.get("time_points", 512)))


def make_cell(row: pd.Series, time_values: np.ndarray, state_values: np.ndarray) -> harness.TrajectoryCell:
    return harness.TrajectoryCell(
        system_id=int(row["system_id"]),
        initial_condition_set=int(row["initial_condition_set"]),
        dimension=int(row["dimension"]),
        time=np.asarray(time_values, dtype=float),
        state=np.asarray(state_values, dtype=float),
        time_sha256=str(row["time_sha256"]),
        state_sha256=str(row["state_sha256"]),
    )


def r2_scores(reference: np.ndarray, prediction: np.ndarray | None) -> tuple[float, float, list[float], str]:
    outcome = harness.prediction_outcome(reference, prediction)
    if outcome != "finite":
        return float("nan"), float("nan"), [], outcome
    by_dim = []
    weights = []
    assert prediction is not None
    for idx in range(reference.shape[1]):
        y = reference[:, idx]
        yhat = prediction[:, idx]
        denom = float(np.sum((y - np.mean(y)) ** 2))
        if denom == 0.0:
            return float("nan"), float("nan"), [], "reference_no_variance"
        score = 1.0 - float(np.sum((y - yhat) ** 2)) / denom
        by_dim.append(float(score))
        weights.append(denom)
    arithmetic = float(np.mean(by_dim))
    weighted = float(np.average(np.asarray(by_dim), weights=np.asarray(weights)))
    return arithmetic, weighted, by_dim, "success" if math.isfinite(arithmetic) and math.isfinite(weighted) else "nonfinite_score"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def int_field(record: dict[str, Any], *names: str) -> int:
    for name in names:
        if name in record:
            return int(record[name])
    raise KeyError(names[0])


def control_key(record: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        int_field(record, "system_id"),
        int_field(record, "fit_initial_condition_set", "source_initial_condition_set"),
        int_field(record, "generalization_initial_condition_set", "target_initial_condition_set"),
        str(record.get("odeformer_config_id", "")),
    )


def control_cell_value(item: tuple[int, int, int, str]) -> list[Any]:
    return list(item)


def control_repetition_key(record: dict[str, Any]) -> tuple[int, str]:
    for name in ["odeformer_grid_repetition", "odeformer_noise_repetition", "repetition"]:
        if name in record:
            return (0, str(record[name]))
    return (1, "")


def grouped_control_records(records: list[dict[str, Any]]) -> dict[tuple[int, int, int, str], list[dict[str, Any]]]:
    groups: dict[tuple[int, int, int, str], list[dict[str, Any]]] = {}
    for record in records:
        groups.setdefault(control_key(record), []).append(record)
    for values in groups.values():
        values.sort(key=control_repetition_key)
    return groups


def control_close(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=REL_TOL, abs_tol=ABS_TOL)


def compare_control_record(
    left: dict[str, Any],
    right: dict[str, Any],
    item: tuple[int, int, int, str],
) -> list[dict[str, Any]]:
    findings = []
    cell = control_cell_value(item)
    if left.get("status") != right.get("status"):
        findings.append({"cell": cell, "field": "status", "reference": left.get("status"), "candidate": right.get("status")})
    if left.get("odeformer_model_canonical") != right.get("odeformer_model_canonical"):
        findings.append(
            {
                "cell": cell,
                "field": "odeformer_model_canonical",
                "reference": left.get("odeformer_model_canonical"),
                "candidate": right.get("odeformer_model_canonical"),
            }
        )
    if left.get("odeformer_fitted_constants") != right.get("odeformer_fitted_constants"):
        left_constants = json.loads(str(left.get("odeformer_fitted_constants", "[]")))
        right_constants = json.loads(str(right.get("odeformer_fitted_constants", "[]")))
        if len(left_constants) != len(right_constants) or any(not control_close(a, b) for a, b in zip(left_constants, right_constants)):
            findings.append(
                {
                    "cell": cell,
                    "field": "odeformer_fitted_constants",
                    "reference": left_constants,
                    "candidate": right_constants,
                }
            )
    for field in CONTROL_R2_FIELDS:
        if not control_close(float(left.get(field, 0.0)), float(right.get(field, 0.0))):
            findings.append({"cell": cell, "field": field, "reference": left.get(field), "candidate": right.get(field)})
    return findings


def compare_noise_control(reference_path: Path, candidate_path: Path) -> dict[str, Any]:
    reference_records = read_jsonl(reference_path)
    candidate_records = read_jsonl(candidate_path)
    reference = grouped_control_records(reference_records)
    candidate = grouped_control_records(candidate_records)
    findings = []
    for item in sorted(candidate):
        left_records = reference.get(item, [])
        right_records = candidate.get(item, [])
        if not left_records or not right_records:
            findings.append({"cell": control_cell_value(item), "field": "record_presence", "reference": bool(left_records), "candidate": bool(right_records)})
            continue
        for right in right_records:
            alternatives = [compare_control_record(left, right, item) for left in left_records]
            if alternatives and any(not result for result in alternatives):
                continue
            findings.extend(min(alternatives, key=len) if alternatives else [])
    return {
        "comparison_rule": {
            "canonical_expression": "exact string match",
            "constants": {"abs_tol": ABS_TOL, "rel_tol": REL_TOL},
            "r2": {"abs_tol": ABS_TOL, "rel_tol": REL_TOL},
            "key": ["system_id", "fit_initial_condition_set", "generalization_initial_condition_set", "odeformer_config_id"],
            "candidate_key_subset": True,
            "accept_any_reference_repetition": True,
        },
        "reference_record_count": len(reference),
        "candidate_record_count": len(candidate),
        "reference_raw_record_count": len(reference_records),
        "candidate_raw_record_count": len(candidate_records),
        "finding_count": len(findings),
        "findings": findings,
        "passed": len(findings) == 0,
    }


def structural_fields(record: dict[str, Any], true_terms: list[set[str]], exact: bool) -> dict[str, Any]:
    raw = json.loads(str(record.get("active_terms_raw", "[]") or "[]"))
    pruned = json.loads(str(record.get("active_terms_pruned", "[]") or "[]"))
    if len(raw) != len(true_terms):
        raw = [[] for _ in true_terms]
    if len(pruned) != len(true_terms):
        pruned = [[] for _ in true_terms]
    fields = {
        "odeformer_structure_hit_raw": False,
        "odeformer_structure_hit_pruned": False,
        "odeformer_structure_metrics_exact_system": bool(exact),
        "odeformer_structure_precision_raw": "",
        "odeformer_structure_recall_raw": "",
        "odeformer_structure_f1_raw": "",
        "odeformer_structure_precision_pruned": "",
        "odeformer_structure_recall_pruned": "",
        "odeformer_structure_f1_pruned": "",
    }
    if not exact:
        return fields
    fields["odeformer_structure_hit_raw"] = harness.support_hit([set(item) for item in raw], true_terms)
    fields["odeformer_structure_hit_pruned"] = harness.support_hit([set(item) for item in pruned], true_terms)
    for label, terms in [("raw", raw), ("pruned", pruned)]:
        metrics = aggregate_equation_metrics(
            [term_set_metrics(found, truth) for found, truth in zip([set(item) for item in terms], true_terms)]
        )
        fields[f"odeformer_structure_precision_{label}"] = metrics["term_precision_micro"]
        fields[f"odeformer_structure_recall_{label}"] = metrics["term_recall_micro"]
        fields[f"odeformer_structure_f1_{label}"] = metrics["structural_f1_micro"]
    return fields


def clean_eval_fields(
    adapter: Any,
    expression: str,
    source_clean: harness.TrajectoryCell,
    target_clean: harness.TrajectoryCell,
) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for regime, cell in [("reconstruction", source_clean), ("generalization", target_clean)]:
        prediction = None
        status = "not_run_no_expression"
        try:
            if expression:
                with adapter.timeout_phase(f"{regime}_after_optimization"):
                    prediction = adapter.integrate_expression(cell, expression)
                status = "success" if harness.prediction_outcome(cell.state, prediction) == "finite" else harness.prediction_outcome(cell.state, prediction)
        except Exception as exc:
            status = type(exc).__name__
        arithmetic, weighted, by_dim, outcome = r2_scores(cell.state, prediction)
        diverged = status in {"diverged", "nonfinite", "wrong_shape", "none", "odeformer_nan_sentinel"} or not math.isfinite(arithmetic)
        fields.update(
            {
                f"{regime}_clean_integration_status": status,
                f"{regime}_clean_prediction_outcome": outcome,
                f"{regime}_clean_diverged_or_nonfinite": bool(diverged),
                f"{regime}_r2_arithmetic_mean": arithmetic,
                f"{regime}_r2_variance_weighted": weighted,
                f"{regime}_r2_by_dim": json.dumps(by_dim, separators=(",", ":")),
                f"{regime}_r2_arithmetic_mean_gt_0_9": bool(math.isfinite(arithmetic) and arithmetic > R2_THRESHOLD),
                f"{regime}_r2_variance_weighted_gt_0_9": bool(math.isfinite(weighted) and weighted > R2_THRESHOLD),
            }
        )
    return fields


def build_summary(details: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_columns = ["system_id", "source_initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization", "odeformer_config_id"]
    for keys, group in details.groupby(group_columns, dropna=False):
        row = dict(zip(group_columns, keys))
        row["repetition_count"] = int(len(group))
        row["success_count"] = int(group["status"].astype(str).eq("success").sum())
        row["error_count"] = int((~group["status"].astype(str).eq("success")).sum())
        for regime in ["reconstruction", "generalization"]:
            values = pd.to_numeric(group[f"{regime}_r2_arithmetic_mean"], errors="coerce")
            weighted = pd.to_numeric(group[f"{regime}_r2_variance_weighted"], errors="coerce")
            finite = values.apply(math.isfinite)
            weighted_finite = weighted.apply(math.isfinite)
            row[f"{regime}_r2_arithmetic_median"] = float(values[finite].median()) if bool(finite.any()) else float("nan")
            row[f"{regime}_r2_arithmetic_std"] = float(values[finite].std(ddof=0)) if bool(finite.any()) else float("nan")
            row[f"{regime}_r2_variance_weighted_median"] = float(weighted[weighted_finite].median()) if bool(weighted_finite.any()) else float("nan")
            row[f"{regime}_r2_variance_weighted_std"] = float(weighted[weighted_finite].std(ddof=0)) if bool(weighted_finite.any()) else float("nan")
            row[f"{regime}_r2_arithmetic_gt_0_9_rate"] = float(group[f"{regime}_r2_arithmetic_mean_gt_0_9"].astype(bool).mean())
            row[f"{regime}_r2_variance_weighted_gt_0_9_rate"] = float(group[f"{regime}_r2_variance_weighted_gt_0_9"].astype(bool).mean())
        rows.append(row)
    return pd.DataFrame(rows)


def expand_comparison_sources(values: list[str] | None) -> list[Path]:
    raw_values = values if values else DEFAULT_STAGE_REPORTS
    paths: list[Path] = []
    for value in raw_values:
        text = str(value)
        base = resolve_repo_path(text)
        if any(char in text for char in "*?[]"):
            matches = [Path(match) for match in glob.glob(str(resolve_repo_path(text)), recursive=True)]
        elif base.is_dir():
            matches = sorted(base.glob("**/robustness_stage_report.csv"))
        else:
            matches = [base]
        paths.extend(path for path in matches if path.is_file())
    return sorted(set(paths))


def build_comparison(details: pd.DataFrame, stage_reports: list[Path], sindy_paths: list[Path]) -> pd.DataFrame:
    keys = ["system_id", "source_initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization"]
    out = details.copy()
    out["comparison_key_status"] = "odeformer"
    evogrow_frames = []
    for path in stage_reports:
        frame = pd.read_csv(path)
        source_col = "initial_condition_set" if "initial_condition_set" in frame.columns else "source_initial_condition_set"
        required = {"system_id", source_col, "noise_sigma", "subsample_rho", "noise_realization"}
        if not required <= set(frame.columns):
            continue
        cols = list(required) + [col for col in frame.columns if "structure" in col or "r2" in col or "cost" in col or "eval" in col]
        item = frame[cols].copy().rename(columns={source_col: "source_initial_condition_set"})
        item["evogrow_source_path"] = str(path)
        evogrow_frames.append(item)
    if evogrow_frames:
        evogrow = pd.concat(evogrow_frames, ignore_index=True).drop_duplicates(keys)
        out = out.merge(evogrow, on=keys, how="left", suffixes=("", "_evogrow"), validate="many_to_one")
    else:
        out["evogrow_source_path"] = "missing"
    sindy_frames = []
    for path in sindy_paths:
        if not path.is_file():
            continue
        frame = pd.read_csv(path)
        if set(keys) <= set(frame.columns):
            frame = frame.copy()
            frame["sindy_source_path"] = str(path)
            sindy_frames.append(frame)
    if sindy_frames:
        sindy = pd.concat(sindy_frames, ignore_index=True).drop_duplicates(keys)
        out = out.merge(sindy, on=keys, how="left", suffixes=("", "_sindy"), validate="many_to_one")
    else:
        out["sindy_source_path"] = "missing"
    for column in ["evogrow_source_path", "sindy_source_path"]:
        if column not in out.columns:
            out[column] = "missing"
        out[column] = out[column].fillna("missing")
    return out


def run_noise_odeformer(
    config_path: Path,
    export_indices: list[Path],
    output_dir: Path,
    repetitions: int = 3,
    config_ids: set[str] | None = None,
    limit: int | None = None,
) -> dict[str, Path]:
    config_path = resolve_repo_path(config_path)
    output_dir = resolve_repo_path(output_dir)
    benchmark = load_benchmark(resolve_repo_path(load_json(config_path)["benchmark_path"]))
    systems = {int(system["id"]): system for system in benchmark}
    support = load_phase_c_support(REPO_ROOT / "studies/regression/phase_c_support.json").set_index("system_id")
    configs = selected_config_objects(config_path, config_ids)
    clean_t = clean_time_grid(config_path)
    clean_states = {
        (int(system["id"]), ic + 1): integrate_truth(system, ic, clean_t)[0]
        for system in benchmark
        for ic in (0, 1)
    }
    rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    work: list[tuple[Path, pd.Series]] = []
    for index_path in export_indices:
        index_path = resolve_repo_path(index_path)
        index = read_export_index(index_path)
        for _, row in index.iterrows():
            work.append((index_path, row))
    if limit is not None:
        work = work[: int(limit)]

    adapters: dict[str, Any] = {}
    try:
        for index_path, row in work:
            observed_t, observed_x = read_index_cell(index_path.parent, row)
            system_id = int(row["system_id"])
            source_ic = int(row["initial_condition_set"])
            target_ic = 2 if source_ic == 1 else 1
            system = systems[system_id]
            fit_cell = make_cell(row, observed_t, observed_x)
            clean_source = harness.TrajectoryCell(system_id, source_ic, int(row["dimension"]), clean_t, clean_states[(system_id, source_ic)], "", "")
            clean_target = harness.TrajectoryCell(system_id, target_ic, int(row["dimension"]), clean_t, clean_states[(system_id, target_ic)], "", "")
            checks.append(
                {
                    "export_index": str(index_path),
                    "system_id": system_id,
                    "initial_condition_set": source_ic,
                    "noise_sigma": float(row["noise_sigma"]),
                    "subsample_rho": float(row["subsample_rho"]),
                    "noise_realization": int(row["noise_realization"]),
                    "n_observed_points": int(row["n_observed_points"]),
                    "time_sha256": str(row["time_sha256"]),
                    "state_sha256": str(row["state_sha256"]),
                    "hash_verified": True,
                }
            )
            for repetition in range(1, int(repetitions) + 1):
                for ode_config in configs:
                    config_id = str(ode_config["config_id"])
                    if config_id not in adapters:
                        adapters[config_id] = harness.build_odeformer_adapter(ode_config)
                    adapter = adapters[config_id]
                    started = time.perf_counter()
                    target_for_harness = clean_target
                    record = harness.run_odeformer_record_with_adapter(system, fit_cell, target_for_harness, ode_config, adapter)
                    expression = str(record.get("odeformer_expression_after_optimization") or record.get("odeformer_model_canonical") or "")
                    record.update(
                        clean_eval_fields(adapter, expression, clean_source, clean_target)
                        if record.get("status") == "success"
                        else {}
                    )
                    for regime in ["reconstruction", "generalization"]:
                        record.setdefault(f"{regime}_clean_integration_status", "not_run_fit_failed")
                        record.setdefault(f"{regime}_clean_prediction_outcome", "none")
                        record.setdefault(f"{regime}_clean_diverged_or_nonfinite", True)
                    record.update(
                        {
                            "method": "odeformer",
                            "odeformer_environment_id": "reference",
                            "odeformer_grid_mode": "faithful",
                            "odeformer_noise_repetition": repetition,
                            "export_index": str(index_path),
                            "source_initial_condition_set": source_ic,
                            "target_initial_condition_set": target_ic,
                            "noise_sigma": float(row["noise_sigma"]),
                            "subsample_rho": float(row["subsample_rho"]),
                            "noise_realization": int(row["noise_realization"]),
                            "data_condition_fingerprint": str(row["data_condition_fingerprint"]),
                            "observed_data_sha256": data_sha(row),
                            "n_observed_points": int(row["n_observed_points"]),
                            "clean_grid_points": int(len(clean_t)),
                            "code_origin_path": str(REPO_ROOT),
                            "code_origin_git_hash": harness.git_hash(),
                            "elapsed_s_non_evidence": time.perf_counter() - started,
                            **structural_fields(
                                record,
                                polynomial_true_terms(system),
                                str(support.loc[system_id, "phasec_representability"]) == "exact",
                            ),
                            **support.loc[system_id].to_dict(),
                        }
                    )
                    rows.append(record)
    finally:
        for adapter in adapters.values():
            close = getattr(adapter, "close", None)
            if callable(close):
                close()

    output_dir.mkdir(parents=True, exist_ok=True)
    details = pd.DataFrame(rows)
    paths = {
        "details": output_dir / "details.csv",
        "records": output_dir / "records.jsonl",
        "summary": output_dir / "summary.csv",
        "export_checks": output_dir / "export_checks.csv",
    }
    details.to_csv(paths["details"], index=False)
    paths["records"].write_text(
        "\n".join(json.dumps(record, sort_keys=True) for record in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )
    build_summary(details).to_csv(paths["summary"], index=False)
    pd.DataFrame(checks).to_csv(paths["export_checks"], index=False)
    return paths


def compare_control(candidate_records: Path, output_dir: Path, reference_records: Path = CONTROL_REFERENCE) -> tuple[Path, bool]:
    if not reference_records.is_file():
        fail(f"control reference records do not exist: {reference_records}")
    result = compare_noise_control(reference_records, candidate_records)
    path = output_dir / "control_equivalence.json"
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path, bool(result["passed"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run ODEFormer on exported Phase-C noisy trajectories.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--export-index", action="append", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--config-ids", default="")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--stage-report", action="append", default=None)
    parser.add_argument("--sindy-details", action="append", default=None)
    parser.add_argument("--control-reference", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        export_indices = [Path(value) for value in args.export_index] if args.export_index else DEFAULT_EXPORT_INDICES
        output_dir = resolve_repo_path(args.output_dir)
        paths = run_noise_odeformer(
            Path(args.config),
            export_indices,
            output_dir,
            repetitions=args.repetitions,
            config_ids=run_odeformer_grid.parse_str_set(args.config_ids),
            limit=args.limit,
        )
        comparison = build_comparison(
            pd.read_csv(paths["details"]),
            expand_comparison_sources(args.stage_report),
            [resolve_repo_path(path) for path in (args.sindy_details or ["outputs/stage2/baselines/details.csv", "outputs/wp_n34_noise_sindy_baselines/details.csv"])],
        )
        comparison_path = output_dir / "comparison_with_robustness_stage_report.csv"
        comparison.to_csv(comparison_path, index=False)
        paths["comparison_with_robustness_stage_report"] = comparison_path
        if args.control_reference:
            control_path, control_ok = compare_control(paths["records"], output_dir, resolve_repo_path(args.control_reference))
            paths["control_equivalence"] = control_path
            if not control_ok:
                raise ValueError(f"control equivalence failed; see {control_path}")
        print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
