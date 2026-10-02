from __future__ import annotations

import argparse
import glob
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from baselines import harness
from baselines import run_odeformer_noise


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.run_phasec_noise_sindy_baselines import (  # noqa: E402
    data_sha,
    read_export_index,
    read_index_cell,
)
from scripts.aggregate.run_phasec_sindy_baseline import load_phase_c_support  # noqa: E402
from scripts.aggregate.run_wp_n6_sindy_baseline import (  # noqa: E402
    integrate_truth,
    load_benchmark,
)
from utils.metrics import aggregate_equation_metrics, term_set_metrics  # noqa: E402


DEFAULT_CONFIG = Path("baselines/configs/pysr_faithful.json")
DEFAULT_OUTPUT_DIR = Path("outputs/wp_n39_noise_pysr")
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


def fail(message: str) -> None:
    raise ValueError(message)


def resolve_repo_path(path: str | Path) -> Path:
    value = Path(path)
    return value.resolve() if value.is_absolute() else (REPO_ROOT / value).resolve()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def parse_seed_set(text: str) -> list[int]:
    values = [item.strip() for item in str(text).split(",") if item.strip()]
    if not values:
        return [1, 2, 3]
    return [int(value) for value in values]


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
        by_dim.append(float(1.0 - float(np.sum((y - yhat) ** 2)) / denom))
        weights.append(denom)
    arithmetic = float(np.mean(by_dim))
    weighted = float(np.average(np.asarray(by_dim), weights=np.asarray(weights)))
    if not math.isfinite(arithmetic) or not math.isfinite(weighted):
        return float("nan"), float("nan"), [], "nonfinite_score"
    return arithmetic, weighted, by_dim, "success"


def clean_eval_fields(adapter: Any, expression: str, source_clean: harness.TrajectoryCell, target_clean: harness.TrajectoryCell) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    for regime, cell in [("reconstruction", source_clean), ("generalization", target_clean)]:
        prediction = None
        status = "not_run_no_expression"
        if expression:
            try:
                prediction, status = adapter.integrate_expression(cell, expression)
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


def structural_metric_fields(record: dict[str, Any], true_terms: list[set[str]], exact: bool) -> dict[str, Any]:
    raw = json.loads(str(record.get("active_terms_raw", "[]") or "[]"))
    pruned = json.loads(str(record.get("active_terms_pruned", "[]") or "[]"))
    outside_count = int(record.get("pysr_outside_basis_term_count", 0) or 0)
    if len(raw) != len(true_terms):
        raw = [[] for _ in true_terms]
    if len(pruned) != len(true_terms):
        pruned = [[] for _ in true_terms]
    fields: dict[str, Any] = {
        "pysr_structure_hit_raw": False,
        "pysr_structure_hit_pruned": False,
        "pysr_structure_metrics_exact_system": bool(exact),
        "pysr_structure_precision_raw": "",
        "pysr_structure_recall_raw": "",
        "pysr_structure_f1_raw": "",
        "pysr_structure_precision_pruned": "",
        "pysr_structure_recall_pruned": "",
        "pysr_structure_f1_pruned": "",
    }
    if not exact:
        return fields
    fields["pysr_structure_hit_raw"] = outside_count == 0 and harness.support_hit([set(item) for item in raw], true_terms)
    fields["pysr_structure_hit_pruned"] = outside_count == 0 and harness.support_hit([set(item) for item in pruned], true_terms)
    for label, terms in [("raw", raw), ("pruned", pruned)]:
        metrics = aggregate_equation_metrics(
            [term_set_metrics(found, truth) for found, truth in zip([set(item) for item in terms], true_terms)]
        )
        fields[f"pysr_structure_precision_{label}"] = metrics["term_precision_micro"]
        fields[f"pysr_structure_recall_{label}"] = metrics["term_recall_micro"]
        fields[f"pysr_structure_f1_{label}"] = metrics["structural_f1_micro"]
    return fields


def build_summary(details: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_columns = ["system_id", "source_initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization", "pysr_seed"]
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
            matches = [Path(match) for match in glob.glob(str(base), recursive=True)]
        elif base.is_dir():
            matches = sorted(base.glob("**/robustness_stage_report.csv"))
        else:
            matches = [base]
        paths.extend(path for path in matches if path.is_file())
    return sorted(set(paths))


def build_comparison(details: pd.DataFrame, stage_reports: list[Path], sindy_paths: list[Path], odeformer_paths: list[Path]) -> pd.DataFrame:
    out = run_odeformer_noise.build_comparison(details, stage_reports, sindy_paths)
    keys = ["system_id", "source_initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization"]
    frames = []
    for path in odeformer_paths:
        if not path.is_file():
            continue
        frame = pd.read_csv(path)
        if set(keys) <= set(frame.columns):
            item = frame[keys + [col for col in frame.columns if col.startswith("reconstruction_") or col.startswith("generalization_")]].copy()
            item["odeformer_source_path"] = str(path)
            frames.append(item)
    if frames:
        odeformer = pd.concat(frames, ignore_index=True).drop_duplicates(keys)
        out = out.merge(odeformer, on=keys, how="left", suffixes=("", "_odeformer"), validate="many_to_one")
    else:
        out["odeformer_source_path"] = "missing"
    if "odeformer_source_path" not in out.columns:
        out["odeformer_source_path"] = "missing"
    out["odeformer_source_path"] = out["odeformer_source_path"].fillna("missing")
    return out


def run_noise_pysr(
    config_path: Path,
    export_indices: list[Path],
    output_dir: Path,
    seeds: list[int] | None = None,
    limit: int | None = None,
) -> dict[str, Path]:
    config_path = resolve_repo_path(config_path)
    config = load_json(config_path)
    output_dir = resolve_repo_path(output_dir)
    benchmark = load_benchmark(resolve_repo_path(config["benchmark_path"]))
    systems = {int(system["id"]): system for system in benchmark}
    support = load_phase_c_support(REPO_ROOT / "studies/regression/phase_c_support.json").set_index("system_id")
    clean_t = clean_time_grid(config_path)
    clean_states = {
        (int(system["id"]), ic + 1): integrate_truth(system, ic, clean_t)[0]
        for system in benchmark
        for ic in (0, 1)
    }
    work: list[tuple[Path, pd.Series]] = []
    checks: list[dict[str, Any]] = []
    for index_path in export_indices:
        index_path = resolve_repo_path(index_path)
        index = read_export_index(index_path)
        for _, row in index.iterrows():
            work.append((index_path, row))
    if limit is not None:
        work = work[: int(limit)]

    rows: list[dict[str, Any]] = []
    requested_seeds = seeds if seeds is not None else list(config.get("seeds", [1, 2, 3]))
    for index_path, row in work:
        observed_t, observed_x = read_index_cell(index_path.parent, row)
        system_id = int(row["system_id"])
        source_ic = int(row["initial_condition_set"])
        target_ic = 2 if source_ic == 1 else 1
        system = systems[system_id]
        if int(row["dimension"]) != int(system["dim"]):
            fail(f"dimension mismatch for system_id={system_id}")
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
        for seed in requested_seeds:
            pysr_config = harness.pysr_default_config(seed=int(seed), output_dir=output_dir / "models" / f"seed_{int(seed):03d}")
            pysr_config.update(config.get("pysr", {}))
            pysr_config["random_state"] = int(seed)
            pysr_config["output_dir"] = str(output_dir / "models" / f"seed_{int(seed):03d}" / f"system_{system_id:03d}_ic_{source_ic}")
            adapter = None
            started = time.perf_counter()
            try:
                adapter = harness.build_pysr_adapter(pysr_config)
                record = harness.run_pysr_record_with_adapter(system, fit_cell, clean_target, pysr_config, adapter)
                expression = str(record.get("pysr_model_canonical") or record.get("model") or "")
                if record.get("status") == "success":
                    record.update(clean_eval_fields(adapter, expression, clean_source, clean_target))
            except Exception as exc:
                record = harness.record_failure(harness.base_record("pysr", pysr_config, fit_cell, clean_target), exc)
                record.update(harness.pysr_schema_defaults(pysr_config))
            finally:
                close = getattr(adapter, "close", None)
                if callable(close):
                    close()
            for regime in ["reconstruction", "generalization"]:
                record.setdefault(f"{regime}_clean_integration_status", "not_run_fit_failed")
                record.setdefault(f"{regime}_clean_prediction_outcome", "none")
                record.setdefault(f"{regime}_clean_diverged_or_nonfinite", True)
            true_terms = harness.support_true_terms_from_system(system)
            exact = str(support.loc[system_id].get("phasec_representability", "")) == "exact"
            record.update(
                {
                    "method": "pysr",
                    "pysr_seed": int(seed),
                    "pysr_realization": int(seed),
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
                    **structural_metric_fields(record, true_terms, exact),
                    **support.loc[system_id].to_dict(),
                }
            )
            rows.append(record)

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PySR on exported Phase-C noisy trajectories.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--export-index", action="append", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--seeds", default="1,2,3")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--stage-report", action="append", default=None)
    parser.add_argument("--sindy-details", action="append", default=None)
    parser.add_argument("--odeformer-details", action="append", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        export_indices = [Path(value) for value in args.export_index] if args.export_index else DEFAULT_EXPORT_INDICES
        output_dir = resolve_repo_path(args.output_dir)
        paths = run_noise_pysr(
            Path(args.config),
            export_indices,
            output_dir,
            seeds=parse_seed_set(args.seeds),
            limit=args.limit,
        )
        stage_reports = expand_comparison_sources(args.stage_report)
        sindy_paths = [
            resolve_repo_path(path)
            for path in (args.sindy_details or ["outputs/stage2/baselines/details.csv", "outputs/wp_n34_noise_sindy_baselines/details.csv"])
        ]
        odeformer_paths = [
            resolve_repo_path(path)
            for path in (args.odeformer_details or ["outputs/wp_n38_noise_odeformer/details.csv"])
        ]
        comparison = build_comparison(pd.read_csv(paths["details"]), stage_reports, sindy_paths, odeformer_paths)
        comparison_path = output_dir / "comparison_with_external_baselines.csv"
        comparison.to_csv(comparison_path, index=False)
        paths["comparison_with_external_baselines"] = comparison_path
        print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
