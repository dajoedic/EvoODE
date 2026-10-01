from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.run_phasec_sindy_baseline import (  # noqa: E402
    R2_THRESHOLD,
    active_terms_by_equation,
    load_phase_c_support,
    parse_shape,
    read_exported_float64,
    resolve_path,
    support_hit,
)
from scripts.aggregate.run_wp_n6_sindy_baseline import (  # noqa: E402
    build_library,
    fit_sindy,
    integrate_truth,
    library_grid,
    load_benchmark,
    load_config,
    polynomial_true_terms,
    simulate_model,
)
from utils.metrics import aggregate_equation_metrics, term_set_metrics  # noqa: E402


DEFAULT_OUTPUT_DIR = Path("outputs/wp_n34_noise_sindy_baselines")
DEFAULT_CONFIG = Path("analysis/configs/paper1_phaseC_sindy_baseline.json")
DEFAULT_EXPORT_INDEX = Path("outputs/stage1/data_export/index.csv")
DEFAULT_STAGE_REPORT = Path("outputs/wp_n33a_stage_report/robustness_stage_report.csv")
DEFAULT_C4_DETAILS = Path("analysis/data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export/details.csv")
DEFAULT_C4_TRAJECTORY_HASHES = Path(
    "analysis/data/paper1_phaseC_v1/phasec_sindy_baseline_wp_c4c_export/trajectory_hashes.csv"
)
HASH_FORMAT = "sha256_raw_little_endian_float64"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SINDy and Weak-SINDy on Phase-C exported noisy data.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Phase-C SINDy config JSON.")
    parser.add_argument("--export-index", default=str(DEFAULT_EXPORT_INDEX), help="Quoted CSV export index.")
    parser.add_argument(
        "--stage-report",
        action="append",
        default=None,
        help=(
            "Optional robustness stage report CSV, directory, or glob. "
            "May be passed multiple times; directories are searched for robustness_stage_report.csv."
        ),
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory under outputs/.")
    parser.add_argument(
        "--control-export-index",
        default="",
        help="Optional export index for the (noise_sigma=0, subsample_rho=0) C-1 reproduction check.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def relative_path(text: Any) -> Path:
    return Path(str(text).replace("\\", "/"))


def read_export_index(index_path: Path) -> pd.DataFrame:
    if not index_path.is_file():
        fail(f"export index does not exist: {index_path}")
    frame = pd.read_csv(index_path)
    required = {
        "system_id",
        "initial_condition_set",
        "dimension",
        "noise_sigma",
        "subsample_rho",
        "noise_realization",
        "data_condition_fingerprint",
        "n_observed_points",
        "hash_format",
        "dtype",
        "byte_order",
        "time_axis_order",
        "state_axis_order",
        "time_shape",
        "state_shape",
        "time_sha256",
        "state_sha256",
        "time_path",
        "state_path",
        "cell_dir",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        fail(f"export index missing columns: {missing}")
    if frame.duplicated(["system_id", "initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization"]).any():
        fail("export index contains duplicate cell keys")
    return frame.sort_values(["system_id", "initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization"]).reset_index(drop=True)


def read_index_cell(export_root: Path, row: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    key = (
        int(row["system_id"]),
        int(row["initial_condition_set"]),
        float(row["noise_sigma"]),
        float(row["subsample_rho"]),
        int(row["noise_realization"]),
    )
    if str(row["hash_format"]) != HASH_FORMAT:
        fail(f"unsupported hash_format for {key}: {row['hash_format']!r}")
    if str(row["dtype"]) != "float64" or str(row["byte_order"]) != "little_endian":
        fail(f"unsupported dtype/byte_order for {key}: {row['dtype']!r}/{row['byte_order']!r}")
    if str(row["time_axis_order"]) != "time" or str(row["state_axis_order"]) != "time_by_dimension_c_order":
        fail(f"unsupported axis order for {key}")

    time_shape = parse_shape(row["time_shape"], f"time_shape {key}")
    state_shape = parse_shape(row["state_shape"], f"state_shape {key}")
    dim = int(row["dimension"])
    if len(time_shape) != 1 or state_shape != (time_shape[0], dim):
        fail(f"shape mismatch for {key}: time={time_shape}, state={state_shape}, dim={dim}")

    cell_dir = export_root / relative_path(row["cell_dir"])
    time = read_exported_float64(cell_dir / relative_path(row["time_path"]), time_shape, str(row["time_sha256"]), f"{key} time")
    state = read_exported_float64(cell_dir / relative_path(row["state_path"]), state_shape, str(row["state_sha256"]), f"{key} state")
    if len(time) != int(row["n_observed_points"]):
        fail(f"n_observed_points mismatch for {key}: index={row['n_observed_points']}, bytes={len(time)}")
    return time, state


def r2_scores(reference: np.ndarray, prediction: np.ndarray | None) -> tuple[float, float, list[float]]:
    if prediction is None or reference.shape != prediction.shape or not np.all(np.isfinite(prediction)):
        return float("nan"), float("nan"), []
    by_dim = []
    weights = []
    for idx in range(reference.shape[1]):
        y = reference[:, idx]
        yhat = prediction[:, idx]
        denom = float(np.sum((y - np.mean(y)) ** 2))
        if denom == 0.0:
            return float("nan"), float("nan"), []
        by_dim.append(1.0 - float(np.sum((y - yhat) ** 2)) / denom)
        weights.append(denom)
    arithmetic = float(np.mean(by_dim))
    variance_weighted = float(np.average(np.asarray(by_dim, dtype=float), weights=np.asarray(weights, dtype=float)))
    return arithmetic, variance_weighted, by_dim


def data_sha(row: pd.Series) -> str:
    return json.dumps(
        {"time_sha256": str(row["time_sha256"]), "state_sha256": str(row["state_sha256"])},
        sort_keys=True,
        separators=(",", ":"),
    )


def weak_source_note() -> str:
    return (
        "pysindy 2.1.0 WeakPDELibrary source: function_library default PolynomialLibrary(degree=3, "
        "include_bias=False), derivative_order=0, include_interaction=True, K=100, H_xt=L_xt/20, p=4; "
        "the source requires a spatiotemporal_grid and computes weak integral features on sampled subdomains."
    )


def serialize_coefficients(coefficients: np.ndarray, feature_names: list[str]) -> str:
    payload = []
    for row in coefficients:
        terms = []
        max_abs = float(np.max(np.abs(row))) if row.size else 0.0
        threshold = max(1e-6, 1e-3 * max_abs)
        for feature, value in zip(feature_names, row):
            coefficient = float(value)
            if abs(coefficient) > threshold:
                terms.append({"term": feature.replace(" ", "*"), "coefficient": coefficient})
        payload.append(terms)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def structural_metrics_pruned(
    pruned_terms: list[set[str]],
    true_terms: list[set[str]],
    support: dict[str, Any],
) -> dict[str, Any]:
    is_exact = str(support.get("phasec_representability", "")) == "exact"
    if not is_exact:
        return {
            "sindy_structure_metrics_exact_system": False,
            "sindy_structure_precision_pruned": "",
            "sindy_structure_recall_pruned": "",
            "sindy_structure_f1_pruned": "",
        }
    metrics = aggregate_equation_metrics(
        [term_set_metrics(found, truth) for found, truth in zip(pruned_terms, true_terms)]
    )
    return {
        "sindy_structure_metrics_exact_system": True,
        "sindy_structure_precision_pruned": metrics["term_precision_micro"],
        "sindy_structure_recall_pruned": metrics["term_recall_micro"],
        "sindy_structure_f1_pruned": metrics["structural_f1_micro"],
    }


def fit_weak_sindy(train_x: np.ndarray, t_grid: np.ndarray, names: list[str], cfg: Any):
    import pysindy as ps

    library = ps.WeakPDELibrary(
        function_library=build_library(cfg),
        derivative_order=0,
        spatiotemporal_grid=np.asarray(t_grid, dtype=float).reshape((-1, 1)),
        include_bias=False,
    )
    model = ps.SINDy(
        optimizer=ps.STLSQ(threshold=cfg.threshold, alpha=1e-6, normalize_columns=False),
        feature_library=library,
    )
    model.fit(train_x, t=t_grid, feature_names=names)
    return model


def run_one_model(
    method: str,
    cfg: Any,
    system: dict[str, Any],
    support: dict[str, Any],
    export_row: pd.Series,
    observed_t: np.ndarray,
    observed_x: np.ndarray,
    clean_t: np.ndarray,
    clean_by_ic: dict[int, np.ndarray],
) -> dict[str, Any]:
    system_id = int(system["id"])
    dim = int(system["dim"])
    source_ic = int(export_row["initial_condition_set"])
    target_ic = 2 if source_ic == 1 else 1
    names = [f"x{idx}" for idx in range(dim)]
    true_terms = polynomial_true_terms(system)
    fit_status = "success"
    fit_error = ""
    model = None
    started = time.perf_counter()
    try:
        if method == "sindy":
            model = fit_sindy(observed_x, observed_t, names, cfg)
        elif method == "weak_sindy":
            model = fit_weak_sindy(observed_x, observed_t, names, cfg)
        else:
            fail(f"unknown method: {method}")
    except Exception as exc:
        fit_status = type(exc).__name__
        fit_error = str(exc)
    elapsed = time.perf_counter() - started

    feature_names: list[str] = []
    raw_terms: list[set[str]] = [set() for _ in range(dim)]
    pruned_terms: list[set[str]] = [set() for _ in range(dim)]
    coefficients = np.empty((dim, 0))
    if model is not None:
        feature_names = model.get_feature_names()
        coefficients = model.coefficients()
        raw_terms = active_terms_by_equation(coefficients, feature_names)
        pruned_terms = raw_terms

    predictions: dict[str, tuple[np.ndarray | None, str, int]] = {}
    for regime, eval_ic in [("reconstruction", source_ic), ("generalization", target_ic)]:
        if model is None:
            predictions[regime] = (None, "fit_failed", eval_ic)
            continue
        prediction, status = simulate_model(coefficients, feature_names, clean_by_ic[eval_ic][0, :], clean_t)
        predictions[regime] = (prediction, status, eval_ic)

    row: dict[str, Any] = {
        "method": method,
        "method_config_id": f"{method}_{cfg.library_id}",
        "library_id": cfg.library_id,
        "polynomial_degree": cfg.polynomial_degree,
        "include_sin_cos": cfg.include_trig,
        "stlsq_threshold": cfg.threshold,
        "system_id": system_id,
        "system_name": system["eq_description"],
        "dimension": dim,
        "source_initial_condition_set": source_ic,
        "target_initial_condition_set": target_ic,
        "noise_sigma": float(export_row["noise_sigma"]),
        "subsample_rho": float(export_row["subsample_rho"]),
        "noise_realization": int(export_row["noise_realization"]),
        "data_condition_fingerprint": str(export_row["data_condition_fingerprint"]),
        "observed_data_sha256": data_sha(export_row),
        "time_sha256": str(export_row["time_sha256"]),
        "state_sha256": str(export_row["state_sha256"]),
        "n_observed_points": int(export_row["n_observed_points"]),
        "fit_status": fit_status,
        "fit_error": fit_error,
        "fit_elapsed_s_context": elapsed,
        "elapsed_s_evidence_role": "context_not_evidence",
        "n_library_terms": len(feature_names),
        "n_target_regressions": dim if model is not None else 0,
        "sindy_structure_hit_raw": support_hit(raw_terms, true_terms),
        "sindy_structure_hit_pruned": support_hit(pruned_terms, true_terms),
        "active_terms_raw": json.dumps([sorted(terms) for terms in raw_terms], separators=(",", ":")),
        "active_terms_pruned": json.dumps([sorted(terms) for terms in pruned_terms], separators=(",", ":")),
        "true_terms": json.dumps([sorted(terms) for terms in true_terms], separators=(",", ":")),
        "sindy_coefficients_active": serialize_coefficients(coefficients, feature_names),
        **structural_metrics_pruned(pruned_terms, true_terms, support),
        "weak_sindy_source_note": weak_source_note() if method == "weak_sindy" else "",
        **support,
    }
    for regime, (prediction, status, eval_ic) in predictions.items():
        reference = clean_by_ic[eval_ic]
        arithmetic, variance_weighted, by_dim = r2_scores(reference, prediction)
        diverged = status in {"diverged", "nonfinite"} or not math.isfinite(arithmetic)
        row.update(
            {
                f"{regime}_initial_condition_set": eval_ic,
                f"{regime}_integration_status": status,
                f"{regime}_diverged_or_nonfinite": diverged,
                f"{regime}_r2_arithmetic_mean": arithmetic,
                f"{regime}_r2_variance_weighted": variance_weighted,
                f"{regime}_r2_by_dim": json.dumps(by_dim, separators=(",", ":")),
                f"{regime}_r2_arithmetic_mean_gt_0_9": bool(math.isfinite(arithmetic) and arithmetic > R2_THRESHOLD),
                f"{regime}_r2_variance_weighted_gt_0_9": bool(math.isfinite(variance_weighted) and variance_weighted > R2_THRESHOLD),
            }
        )
    return row


def build_summary(details: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_columns = ["method", "library_id", "polynomial_degree", "include_sin_cos", "stlsq_threshold", "noise_sigma", "subsample_rho"]
    for keys, group in details.groupby(group_columns, dropna=False):
        row = dict(zip(group_columns, keys))
        row["n_cells"] = int(len(group))
        row["fit_success_count"] = int((group["fit_status"].astype(str) == "success").sum())
        for regime in ["reconstruction", "generalization"]:
            finite = pd.to_numeric(group[f"{regime}_r2_arithmetic_mean"], errors="coerce").apply(math.isfinite)
            row[f"{regime}_r2_finite_count"] = int(finite.sum())
            row[f"{regime}_r2_gt_0_9_count"] = int(group[f"{regime}_r2_arithmetic_mean_gt_0_9"].astype(bool).sum())
            row[f"{regime}_r2_gt_0_9_rate"] = float(row[f"{regime}_r2_gt_0_9_count"] / len(group)) if len(group) else float("nan")
            row[f"{regime}_diverged_or_nonfinite_count"] = int(group[f"{regime}_diverged_or_nonfinite"].astype(bool).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def expand_stage_report_paths(stage_reports: list[str] | None) -> list[Path]:
    values = stage_reports if stage_reports else [str(DEFAULT_STAGE_REPORT)]
    paths: list[Path] = []
    for value in values:
        raw = Path(value)
        matches: list[Path]
        if any(char in value for char in "*?[]"):
            matches = [Path(match) for match in glob.glob(value, recursive=True)]
        elif raw.is_dir():
            matches = sorted(raw.glob("**/robustness_stage_report.csv"))
        else:
            matches = [raw]
        paths.extend(path for path in matches if path.is_file())
    return sorted(set(paths))


def build_comparison(details: pd.DataFrame, stage_report_paths: list[Path]) -> pd.DataFrame:
    keys = ["system_id", "initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization"]
    frames = []
    for stage_report_path in stage_report_paths:
        stage = pd.read_csv(stage_report_path)
        required = set(keys + ["clean_reconstruction_r2_arithmetic_mean", "clean_generalization_r2_arithmetic_mean"])
        missing = sorted(required - set(stage.columns))
        if missing:
            fail(f"stage report missing columns in {stage_report_path}: {missing}")
        stage = stage[keys + ["clean_reconstruction_r2_arithmetic_mean", "clean_generalization_r2_arithmetic_mean"]].copy()
        stage["stage_report_path"] = str(stage_report_path)
        frames.append(stage)
    if frames:
        stage = pd.concat(frames, ignore_index=True)
        duplicate = stage.duplicated(keys, keep=False)
        if bool(duplicate.any()):
            fail(f"stage reports contain duplicate comparison keys: {stage.loc[duplicate, keys].to_dict('records')[:5]}")
        stage = stage.rename(
            columns={
                "initial_condition_set": "source_initial_condition_set",
                "clean_reconstruction_r2_arithmetic_mean": "evogrow_reconstruction_r2_arithmetic_mean",
                "clean_generalization_r2_arithmetic_mean": "evogrow_generalization_r2_arithmetic_mean",
            }
        )
    else:
        stage = pd.DataFrame(
            columns=[
                "system_id",
                "source_initial_condition_set",
                "noise_sigma",
                "subsample_rho",
                "noise_realization",
                "evogrow_reconstruction_r2_arithmetic_mean",
                "evogrow_generalization_r2_arithmetic_mean",
                "stage_report_path",
            ]
        )
    base = details.rename(columns={"initial_condition_set": "source_initial_condition_set"}).copy()
    merged = base.merge(
        stage,
        on=["system_id", "source_initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization"],
        how="left",
        validate="many_to_one",
    )
    merged["evogrow_comparison_status"] = np.where(
        merged["evogrow_reconstruction_r2_arithmetic_mean"].notna()
        | merged["evogrow_generalization_r2_arithmetic_mean"].notna(),
        "matched",
        "missing_in_stage_report",
    )
    return merged


def run_baselines(
    config_path: Path,
    export_index_path: Path,
    output_dir: Path,
    stage_report_paths: list[Path],
    methods: list[str] | None = None,
    use_export_trajectories_for_evaluation: bool = False,
) -> dict[str, Path]:
    config = load_config(config_path)
    benchmark = load_benchmark(resolve_path(config.get("benchmark_path", "../benchmarks/data/strogatz_extended.json"), config_path))
    systems = {int(system["id"]): system for system in benchmark}
    support = load_phase_c_support(resolve_path(config.get("phase_c_support_path", "../studies/regression/phase_c_support.json"), config_path))
    support_by_id = support.set_index("system_id")
    index = read_export_index(export_index_path)
    export_root = export_index_path.parent
    clean_t = np.linspace(float(config.get("t_start", 0.0)), float(config.get("t_end", 10.0)), int(config.get("time_points", 512)))
    configs = library_grid(config)
    requested_methods = methods if methods is not None else ["sindy", "weak_sindy"]
    detail_rows: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    exported_cells: dict[tuple[int, int], tuple[np.ndarray, np.ndarray]] = {}
    if use_export_trajectories_for_evaluation:
        for _, export_row in index.iterrows():
            exported_cells[(int(export_row["system_id"]), int(export_row["initial_condition_set"]))] = read_index_cell(
                export_root, export_row
            )
    for _, export_row in index.iterrows():
        system_id = int(export_row["system_id"])
        if system_id not in systems:
            fail(f"export index references unknown system_id={system_id}")
        system = systems[system_id]
        if int(export_row["dimension"]) != int(system["dim"]):
            fail(f"dimension mismatch for system_id={system_id}")
        observed_t, observed_x = read_index_cell(export_root, export_row)
        if use_export_trajectories_for_evaluation:
            missing_ics = sorted(ic for ic in [1, 2] if (system_id, ic) not in exported_cells)
            if missing_ics:
                fail(f"control export missing evaluation ICs for system_id={system_id}: {missing_ics}")
            clean_by_ic = {ic: exported_cells[(system_id, ic)][1] for ic in [1, 2]}
            clean_t_for_cell = exported_cells[(system_id, 1)][0]
            if not all(np.array_equal(clean_t_for_cell, exported_cells[(system_id, ic)][0]) for ic in [1, 2]):
                fail(f"control export time grids differ across ICs for system_id={system_id}")
        else:
            clean_by_ic = {
                1: integrate_truth(system, 0, clean_t)[0],
                2: integrate_truth(system, 1, clean_t)[0],
            }
            clean_t_for_cell = clean_t
        checks.append(
            {
                "system_id": system_id,
                "initial_condition_set": int(export_row["initial_condition_set"]),
                "noise_sigma": float(export_row["noise_sigma"]),
                "subsample_rho": float(export_row["subsample_rho"]),
                "noise_realization": int(export_row["noise_realization"]),
                "n_observed_points": int(export_row["n_observed_points"]),
                "time_sha256": str(export_row["time_sha256"]),
                "state_sha256": str(export_row["state_sha256"]),
                "hash_verified": True,
            }
        )
        support_row = support_by_id.loc[system_id].to_dict()
        for cfg in configs:
            for method in requested_methods:
                detail_rows.append(
                    run_one_model(method, cfg, system, support_row, export_row, observed_t, observed_x, clean_t_for_cell, clean_by_ic)
                )

    details = pd.DataFrame(detail_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    frames = {
        "details": details,
        "summary": build_summary(details),
        "export_checks": pd.DataFrame(checks),
    }
    frames["comparison_with_robustness_stage_report"] = build_comparison(details, stage_report_paths)
    for name, frame in frames.items():
        path = output_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    return paths


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_control_hashes(control_export_index: Path, output_dir: Path) -> tuple[pd.DataFrame, bool]:
    index = read_export_index(control_export_index)
    reference_path = DEFAULT_C4_TRAJECTORY_HASHES
    if not reference_path.is_file():
        fail(f"C-4 trajectory hash reference does not exist: {reference_path}")
    reference = pd.read_csv(reference_path)
    keys = ["system_id", "initial_condition_set"]
    required = set(keys + ["time_sha256", "state_sha256"])
    missing = sorted(required - set(reference.columns))
    if missing:
        fail(f"C-4 trajectory hash reference missing columns: {missing}")
    merged = index.merge(
        reference[keys + ["time_sha256", "state_sha256"]],
        on=keys,
        how="left",
        validate="one_to_one",
        suffixes=("_control", "_c4"),
    )
    merged["time_hash_matches_c4"] = merged["time_sha256_control"].astype(str) == merged["time_sha256_c4"].astype(str)
    merged["state_hash_matches_c4"] = merged["state_sha256_control"].astype(str) == merged["state_sha256_c4"].astype(str)
    merged["trajectory_hash_status"] = np.where(
        merged["time_hash_matches_c4"] & merged["state_hash_matches_c4"],
        "matched",
        "differs_from_c4",
    )
    path = output_dir / "control_trajectory_hash_check.csv"
    merged.to_csv(path, index=False)
    return merged, bool((merged["trajectory_hash_status"] == "matched").all())


def long_control_details(details: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in details.iterrows():
        for regime in ["reconstruction", "generalization"]:
            rows.append(
                {
                    "library_id": row["library_id"],
                    "system_id": int(row["system_id"]),
                    "source_initial_condition_set": int(row["source_initial_condition_set"]),
                    "target_initial_condition_set": int(row["target_initial_condition_set"]),
                    "regime": regime,
                    "fit_status": row["fit_status"],
                    "integration_status": row[f"{regime}_integration_status"],
                    "r2": row[f"{regime}_r2_arithmetic_mean"],
                    "active_terms_raw": row["active_terms_raw"],
                    "active_terms_pruned": row["active_terms_pruned"],
                    "sindy_coefficients_active": row["sindy_coefficients_active"],
                }
            )
    return pd.DataFrame(rows)


def compare_control_to_c4(control_details: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, bool]:
    reference_path = DEFAULT_C4_DETAILS
    if not reference_path.is_file():
        fail(f"C-4 detail reference does not exist: {reference_path}")
    reference = pd.read_csv(reference_path)
    keys = ["library_id", "system_id", "source_initial_condition_set", "target_initial_condition_set", "regime"]
    reference = reference.loc[reference["system_id"].isin([1, 24])].copy()
    reference = reference[keys + ["fit_status", "integration_status", "r2", "active_terms_raw", "active_terms_pruned"]]
    candidate = long_control_details(control_details)
    merged = candidate.merge(reference, on=keys, how="outer", validate="one_to_one", suffixes=("_control", "_c4"), indicator=True)
    merged["row_presence_status"] = merged["_merge"].astype(str)
    for field in ["fit_status", "integration_status", "active_terms_raw", "active_terms_pruned"]:
        merged[f"{field}_matches_c4"] = merged[f"{field}_control"].astype(str) == merged[f"{field}_c4"].astype(str)
    merged["r2_abs_delta"] = (
        pd.to_numeric(merged["r2_control"], errors="coerce") - pd.to_numeric(merged["r2_c4"], errors="coerce")
    ).abs()
    merged["r2_matches_c4"] = merged["r2_abs_delta"] <= 1e-12
    if "sindy_coefficients_active_c4" not in merged.columns:
        merged["coefficient_compare_status"] = "reference_missing_coefficients"
    else:
        merged["coefficient_compare_status"] = np.where(
            merged["sindy_coefficients_active_control"].astype(str) == merged["sindy_coefficients_active_c4"].astype(str),
            "matched",
            "differs_from_c4",
        )
    comparable_fields = [
        "fit_status_matches_c4",
        "integration_status_matches_c4",
        "active_terms_raw_matches_c4",
        "active_terms_pruned_matches_c4",
        "r2_matches_c4",
    ]
    merged["control_comparison_status"] = np.where(
        (merged["row_presence_status"] == "both")
        & merged[comparable_fields].all(axis=1)
        & (merged["coefficient_compare_status"] == "matched"),
        "matched",
        "differs_or_incomplete",
    )
    path = output_dir / "control_c4_comparison.csv"
    merged.to_csv(path, index=False)
    return merged, bool((merged["control_comparison_status"] == "matched").all())


def run_control(control_export_index: Path, config_path: Path, output_dir: Path) -> tuple[dict[str, Path], str, bool]:
    control_dir = output_dir / "control_c4_reproduction"
    control_dir.mkdir(parents=True, exist_ok=True)
    hash_check, hashes_match = compare_control_hashes(control_export_index, control_dir)
    paths = run_baselines(
        config_path,
        control_export_index,
        control_dir,
        [],
        methods=["sindy"],
        use_export_trajectories_for_evaluation=True,
    )
    comparison, comparison_passed = compare_control_to_c4(pd.read_csv(paths["details"]), control_dir)
    paths["control_trajectory_hash_check"] = control_dir / "control_trajectory_hash_check.csv"
    paths["control_c4_comparison"] = control_dir / "control_c4_comparison.csv"
    if not hashes_match:
        return paths, "failed: control trajectory hashes differ from C-4 reference", False
    if not comparison_passed:
        statuses = comparison["control_comparison_status"].value_counts(dropna=False).to_dict()
        coefficient_statuses = comparison["coefficient_compare_status"].value_counts(dropna=False).to_dict()
        return (
            paths,
            f"failed: C-4 comparison incomplete/different; statuses={statuses}; coefficient_statuses={coefficient_statuses}",
            False,
        )
    return paths, f"passed: {len(hash_check)} trajectory hashes and {len(comparison)} control rows matched C-4", True


def control_status(control_export_index: str, config_path: Path, output_dir: Path) -> tuple[dict[str, Path], str, bool]:
    if not control_export_index:
        return {}, "not_run: no (noise_sigma=0, subsample_rho=0) export index was provided.", True
    path = Path(control_export_index)
    if not path.is_file():
        return {}, f"not_run: control export index does not exist: {path}", False
    return run_control(path.resolve(), config_path, output_dir)


def main() -> int:
    args = parse_args()
    try:
        config_path = Path(args.config).resolve()
        output_dir = Path(args.output_dir)
        paths = run_baselines(
            config_path,
            Path(args.export_index).resolve(),
            output_dir,
            expand_stage_report_paths(args.stage_report),
        )
        printable = {key: str(value) for key, value in paths.items()}
        control_paths, control_note, control_ok = control_status(args.control_export_index, config_path, output_dir)
        for key, value in control_paths.items():
            printable_key = key if key.startswith("control_") else f"control_{key}"
            printable[printable_key] = str(value)
        printable["control"] = control_note
        print(json.dumps(printable, indent=2))
        return 0 if control_ok else 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
