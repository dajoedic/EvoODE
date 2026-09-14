import argparse
import hashlib
import json
import math
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.convert_campaign_history_to_run_registry import row_from_record  # noqa: E402
from scripts.aggregate.run_wp_n6_sindy_baseline import (  # noqa: E402
    INTEGRATION_LIMIT,
    LibraryConfig,
    active_terms_by_equation,
    fit_sindy,
    integrate_truth,
    library_grid,
    load_benchmark,
    load_config,
    polynomial_true_terms,
    r2_score,
    resolve_path,
    simulate_model,
    support_hit,
)


CAMPAIGN_ID = "paper1_phaseC_v1"
R2_THRESHOLD = 0.9
RECONSTRUCTION_CONTROL_TOL = 0.0
PAIR_OUTPUT = ANALYSIS_ROOT / "data" / CAMPAIGN_ID / "phasec_sindy_paired.csv"
PAIR_TABLE_DIR = ANALYSIS_ROOT / "tables" / CAMPAIGN_ID / "phasec_sindy_pairing"
WPN6_DETAILS_RUNTIME_COLUMNS = {"fit_elapsed_s_non_evidence"}
WPN6_COST_RUNTIME_COLUMNS = {"elapsed_s_non_evidence_total"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and pair the Phase-C SINDy baseline.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-sindy")
    run_parser.add_argument("--config", required=True, help="Phase-C SINDy config JSON.")
    run_parser.add_argument(
        "--trajectory-export-dir",
        required=True,
        help="Directory containing trajectory_manifest.csv and raw campaign trajectory bytes.",
    )
    run_parser.add_argument("--output-data-dir", default="", help="Optional override for config output_data_dir.")
    run_parser.add_argument("--output-table-dir", default="", help="Optional override for config output_table_dir.")

    pair_parser = subparsers.add_parser("pair")
    pair_parser.add_argument("--sindy-details", required=True, help="SINDy details CSV from run-sindy.")
    pair_parser.add_argument("--evogrow-records-dir", required=True, help="Directory with EvoGrow JSONL records.")
    pair_parser.add_argument("--output", default=str(PAIR_OUTPUT), help="Paired CSV output path.")
    pair_parser.add_argument(
        "--expected-systems",
        default="",
        help="Comma-separated system ids required in EvoGrow input; empty means derive from input.",
    )
    pair_parser.add_argument("--expected-ic-sets", default="1,2")
    pair_parser.add_argument("--expected-seeds", default="", help="Comma-separated seed set; empty means derive.")
    pair_parser.add_argument(
        "--expected-git-hash",
        default="",
        help="Optional exact git_hash required for all EvoGrow records.",
    )
    pair_parser.add_argument(
        "--expected-config-fingerprint",
        default="",
        help="Optional exact config_fingerprint required for all EvoGrow records.",
    )
    pair_parser.add_argument(
        "--expected-stage-cap-behavior-fingerprint",
        default="",
        help="Optional exact stage_cap_behavior_fingerprint required for all EvoGrow records.",
    )

    check_parser = subparsers.add_parser("check-wpn6-bitidentical")
    check_parser.add_argument("--config", default="analysis/configs/wp_n6_sindy_baseline.json")
    check_parser.add_argument("--reference-data-dir", default="analysis/data/wp_n6_sindy_baseline")
    check_parser.add_argument("--reference-table-dir", default="analysis/tables/wp_n6_sindy_baseline")

    compare_parser = subparsers.add_parser("compare-details")
    compare_parser.add_argument("--reference-details", required=True)
    compare_parser.add_argument("--candidate-details", required=True)
    compare_parser.add_argument(
        "--output",
        default="analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/detail_delta_summary.csv",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def parse_int_set(text: str) -> set[int]:
    if not text.strip():
        return set()
    return {int(piece.strip()) for piece in text.split(",") if piece.strip()}


def phasec_output_path(path_value: str, config_path: Path) -> Path:
    return resolve_path(path_value, config_path)


def load_phase_c_support(path: Path) -> pd.DataFrame:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("basis_name") != "staged_polynomial_basis_with_constant":
        fail(f"unexpected Phase-C basis_name: {payload.get('basis_name')!r}")
    rows = []
    for system in payload.get("systems", []):
        status = str(system.get("status", ""))
        representability = str(system.get("representability", ""))
        threeway = "exact" if representability == "exact" else f"surrogate:{status}"
        rows.append(
            {
                "system_id": int(system["system_id"]),
                "dimension": int(system["dim"]),
                "phasec_representability": representability,
                "phasec_representability_threeway": threeway,
                "phasec_support_status": status,
                "phasec_basis_name": payload["basis_name"],
            }
        )
    frame = pd.DataFrame(rows)
    if len(frame) != 63:
        fail(f"phase_c_support must contain 63 systems, got {len(frame)}")
    counts = frame["phasec_representability"].value_counts().to_dict()
    if counts.get("exact", 0) != 30 or counts.get("surrogate", 0) != 33:
        fail(f"unexpected Phase-C representability counts: {counts}")
    return frame


def sha256_float64_le(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array, dtype="<f8")
    return hashlib.sha256(contiguous.tobytes(order="C")).hexdigest()


def trajectory_hash_rows(
    benchmark: list[dict[str, Any]],
    t_grid: np.ndarray,
    trajectories: dict[tuple[int, int], np.ndarray],
) -> pd.DataFrame:
    rows = []
    for system in benchmark:
        system_id = int(system["id"])
        dim = int(system["dim"])
        for ic_set in (1, 2):
            y = trajectories[(system_id, ic_set)]
            rows.append(
                {
                    "system_id": system_id,
                    "initial_condition_set": ic_set,
                    "dimension": dim,
                    "hash_format": "sha256_raw_little_endian_float64",
                    "time_axis_order": "time",
                    "state_axis_order": "time_by_dimension_c_order",
                    "time_shape": json.dumps(list(t_grid.shape), separators=(",", ":")),
                    "state_shape": json.dumps(list(y.shape), separators=(",", ":")),
                    "time_min": float(np.nanmin(t_grid)),
                    "time_max": float(np.nanmax(t_grid)),
                    "state_min": float(np.nanmin(y)),
                    "state_max": float(np.nanmax(y)),
                    "time_sha256": sha256_float64_le(t_grid),
                    "state_sha256": sha256_float64_le(y),
                }
            )
    return pd.DataFrame(rows)


def parse_shape(text: Any, label: str) -> tuple[int, ...]:
    try:
        values = json.loads(str(text))
    except json.JSONDecodeError as exc:
        fail(f"{label} is not valid JSON shape: {text!r}")
        raise AssertionError("unreachable") from exc
    if not isinstance(values, list) or not all(isinstance(value, int) and value >= 0 for value in values):
        fail(f"{label} must be a JSON integer list, got {text!r}")
    return tuple(int(value) for value in values)


def read_exported_float64(path: Path, expected_shape: tuple[int, ...], expected_sha256: str, label: str) -> np.ndarray:
    if not path.is_file():
        fail(f"missing exported trajectory file for {label}: {path}")
    payload = path.read_bytes()
    actual_sha256 = hashlib.sha256(payload).hexdigest()
    if actual_sha256 != str(expected_sha256):
        fail(
            f"hash mismatch for exported trajectory {label}: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    expected_values = int(np.prod(expected_shape, dtype=np.int64))
    expected_bytes = expected_values * 8
    if len(payload) != expected_bytes:
        fail(f"wrong byte length for exported trajectory {label}: expected {expected_bytes}, got {len(payload)}")
    return np.frombuffer(payload, dtype="<f8").reshape(expected_shape, order="C").copy()


def load_exported_trajectories(
    export_dir: Path,
    benchmark: list[dict[str, Any]],
) -> tuple[np.ndarray, dict[tuple[int, int], np.ndarray], pd.DataFrame]:
    manifest_path = export_dir / "trajectory_manifest.csv"
    if not manifest_path.is_file():
        fail(f"missing trajectory export manifest: {manifest_path}")
    manifest = pd.read_csv(manifest_path)
    required_columns = {
        "system_id",
        "initial_condition_set",
        "dimension",
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
    }
    missing_columns = sorted(required_columns - set(manifest.columns))
    if missing_columns:
        fail(f"trajectory export manifest missing columns: {missing_columns}")
    if len(manifest) != len(benchmark) * 2:
        fail(f"trajectory export manifest must contain {len(benchmark) * 2} rows, got {len(manifest)}")

    benchmark_dims = {int(system["id"]): int(system["dim"]) for system in benchmark}
    expected_keys = {(system_id, ic_set) for system_id in benchmark_dims for ic_set in (1, 2)}
    actual_keys = {
        (int(row["system_id"]), int(row["initial_condition_set"]))
        for _, row in manifest.iterrows()
    }
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        extra = sorted(actual_keys - expected_keys)
        fail(f"trajectory export manifest key mismatch: missing={missing}, extra={extra}")
    if manifest.duplicated(["system_id", "initial_condition_set"]).any():
        fail("trajectory export manifest contains duplicate system_id/initial_condition_set rows")

    trajectories: dict[tuple[int, int], np.ndarray] = {}
    trajectory_checks: list[dict[str, Any]] = []
    t_grid: np.ndarray | None = None
    first_time_sha256: str | None = None
    for _, row in manifest.sort_values(["system_id", "initial_condition_set"]).iterrows():
        system_id = int(row["system_id"])
        ic_set = int(row["initial_condition_set"])
        dim = int(row["dimension"])
        key = (system_id, ic_set)
        if dim != benchmark_dims[system_id]:
            fail(f"trajectory export dimension mismatch for {key}: manifest {dim}, benchmark {benchmark_dims[system_id]}")
        if str(row["hash_format"]) != "sha256_raw_little_endian_float64":
            fail(f"unsupported trajectory hash_format for {key}: {row['hash_format']!r}")
        if str(row["dtype"]) != "float64" or str(row["byte_order"]) != "little_endian":
            fail(f"unsupported trajectory dtype/byte_order for {key}: {row['dtype']!r}/{row['byte_order']!r}")
        if str(row["time_axis_order"]) != "time" or str(row["state_axis_order"]) != "time_by_dimension_c_order":
            fail(f"unsupported trajectory axis order for {key}")
        time_shape = parse_shape(row["time_shape"], f"time_shape {key}")
        state_shape = parse_shape(row["state_shape"], f"state_shape {key}")
        if len(time_shape) != 1:
            fail(f"time_shape for {key} must be one-dimensional, got {time_shape}")
        if state_shape != (time_shape[0], dim):
            fail(f"state_shape for {key} must be {(time_shape[0], dim)}, got {state_shape}")

        time_values = read_exported_float64(export_dir / str(row["time_path"]), time_shape, str(row["time_sha256"]), f"{key} time")
        state_values = read_exported_float64(export_dir / str(row["state_path"]), state_shape, str(row["state_sha256"]), f"{key} state")
        if t_grid is None:
            t_grid = time_values
            first_time_sha256 = str(row["time_sha256"])
        elif str(row["time_sha256"]) != first_time_sha256 or not np.array_equal(time_values, t_grid):
            fail(f"trajectory export time grid differs for {key}")
        trajectories[key] = state_values
        trajectory_checks.append(
            {
                "system_id": system_id,
                "initial_condition_set": ic_set,
                "dimension": dim,
                "grid_points": int(time_shape[0]),
                "t_start": float(time_values[0]),
                "t_end": float(time_values[-1]),
                "truth_trajectory_source": "campaign_export",
                "hash_format": str(row["hash_format"]),
                "time_sha256": str(row["time_sha256"]),
                "state_sha256": str(row["state_sha256"]),
                "hash_verified": True,
            }
        )
    if t_grid is None:
        fail("trajectory export manifest contains no rows")
    return t_grid, trajectories, pd.DataFrame(trajectory_checks)


def fit_eval_rows(
    system: dict[str, Any],
    cfg: LibraryConfig,
    t_grid: np.ndarray,
    trajectories: dict[tuple[int, int], np.ndarray],
    support_by_id: pd.DataFrame,
) -> list[dict[str, Any]]:
    system_id = int(system["id"])
    dim = int(system["dim"])
    names = [f"x{idx}" for idx in range(dim)]
    true_terms = polynomial_true_terms(system)
    support = support_by_id.loc[system_id].to_dict()
    rows: list[dict[str, Any]] = []
    for source_ic, target_ic, direction in [(1, 2, "IC1_to_IC2"), (2, 1, "IC2_to_IC1")]:
        train_x = trajectories[(system_id, source_ic)]
        model_start = time.perf_counter()
        fit_status = "success"
        model = None
        try:
            model = fit_sindy(train_x, t_grid, names, cfg)
        except Exception as exc:
            fit_status = type(exc).__name__
        elapsed = time.perf_counter() - model_start

        feature_names: list[str] = []
        raw_terms: list[set[str]] = [set() for _ in range(dim)]
        pruned_terms: list[set[str]] = [set() for _ in range(dim)]
        if model is not None:
            feature_names = model.get_feature_names()
            raw_terms = active_terms_by_equation(model.coefficients(), feature_names)
            pruned_terms = raw_terms

        train_prediction, train_status = (None, "fit_failed")
        control_prediction, control_status = (None, "fit_failed")
        if model is not None:
            train_prediction, train_status = simulate_model(model.coefficients(), feature_names, train_x[0, :], t_grid)
            control_prediction, control_status = simulate_model(model.coefficients(), feature_names, train_x[0, :], t_grid)
        if train_prediction is None or control_prediction is None:
            control_abs_max = float("nan")
            valid_reconstruction_control = False
        else:
            control_abs_max = float(np.max(np.abs(train_prediction - control_prediction)))
            valid_reconstruction_control = control_abs_max == RECONSTRUCTION_CONTROL_TOL

        for regime, eval_ic in [("reconstruction", source_ic), ("generalization", target_ic)]:
            reference = trajectories[(system_id, eval_ic)]
            if regime == "reconstruction":
                prediction, sim_status = train_prediction, train_status
            else:
                prediction, sim_status = (None, "fit_failed")
                if model is not None:
                    prediction, sim_status = simulate_model(model.coefficients(), feature_names, reference[0, :], t_grid)
            score = float("nan") if prediction is None else r2_score(reference, prediction)
            rows.append(
                {
                    "library_id": cfg.library_id,
                    "polynomial_degree": cfg.polynomial_degree,
                    "include_sin_cos": cfg.include_trig,
                    "stlsq_threshold": cfg.threshold,
                    "system_id": system_id,
                    "system_name": system["eq_description"],
                    "dimension": dim,
                    "source_initial_condition_set": source_ic,
                    "target_initial_condition_set": target_ic,
                    "initial_condition_set": source_ic if regime == "reconstruction" else target_ic,
                    "direction": direction,
                    "regime": regime,
                    "fit_status": fit_status,
                    "integration_status": sim_status,
                    "diverged_or_nonfinite": sim_status in {"diverged", "nonfinite"},
                    "r2": score,
                    "r2_gt_0_9": bool(math.isfinite(score) and score > R2_THRESHOLD),
                    "sindy_structure_hit_raw": support_hit(raw_terms, true_terms),
                    "sindy_structure_hit_pruned": support_hit(pruned_terms, true_terms),
                    "active_terms_raw": json.dumps([sorted(terms) for terms in raw_terms], separators=(",", ":")),
                    "active_terms_pruned": json.dumps([sorted(terms) for terms in pruned_terms], separators=(",", ":")),
                    "true_terms": json.dumps([sorted(terms) for terms in true_terms], separators=(",", ":")),
                    "n_library_terms": len(feature_names),
                    "fit_elapsed_s_context": elapsed,
                    "elapsed_s_evidence_role": "context_not_evidence",
                    "n_target_regressions": dim if model is not None else 0,
                    "n_evaluation_integrations": 2 if regime == "reconstruction" else 1,
                    "reconstruction_control_integration_status": control_status,
                    "reconstruction_control_max_abs": control_abs_max,
                    "reconstruction_control_valid": valid_reconstruction_control,
                    "valid_for_analysis": valid_reconstruction_control,
                    **support,
                }
            )
    return rows


def summarize(details: pd.DataFrame) -> pd.DataFrame:
    valid = details[details["valid_for_analysis"]].copy()
    rows = []
    group_columns = [
        "library_id",
        "polynomial_degree",
        "include_sin_cos",
        "stlsq_threshold",
        "direction",
        "regime",
        "dimension",
        "phasec_representability_threeway",
    ]
    for keys, group in valid.groupby(group_columns, dropna=False):
        row = dict(zip(group_columns, keys))
        n_cells = int(len(group))
        finite = group["r2"].apply(math.isfinite)
        r2_clean = finite & ~group["diverged_or_nonfinite"].astype(bool)
        clean_r2_values = group.loc[r2_clean, "r2"]
        row.update(
            {
                "aggregation_scope": "dimension_by_phasec_representability_threeway",
                "n_cells": n_cells,
                "structure_hit_raw_count": int(group["sindy_structure_hit_raw"].sum()),
                "structure_hit_raw_rate": float(group["sindy_structure_hit_raw"].mean()) if n_cells else float("nan"),
                "structure_hit_pruned_count": int(group["sindy_structure_hit_pruned"].sum()),
                "structure_hit_pruned_rate": float(group["sindy_structure_hit_pruned"].mean()) if n_cells else float("nan"),
                "diverged_or_nonfinite_count": int(group["diverged_or_nonfinite"].sum()),
                "r2_finite_nondiverged_count": int(r2_clean.sum()),
                "r2_gt_0_9_count": int(group["r2_gt_0_9"].sum()),
                "r2_gt_0_9_rate_over_cells": float(group["r2_gt_0_9"].sum() / n_cells) if n_cells else float("nan"),
                "r2_median_valid": float(clean_r2_values.median()) if int(r2_clean.sum()) else float("nan"),
                "r2_q000_finite_nondiverged": float(clean_r2_values.quantile(0.0)) if int(r2_clean.sum()) else float("nan"),
                "r2_q025_finite_nondiverged": float(clean_r2_values.quantile(0.25)) if int(r2_clean.sum()) else float("nan"),
                "r2_q075_finite_nondiverged": float(clean_r2_values.quantile(0.75)) if int(r2_clean.sum()) else float("nan"),
                "r2_q100_finite_nondiverged": float(clean_r2_values.quantile(1.0)) if int(r2_clean.sum()) else float("nan"),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def cost_table(details: pd.DataFrame) -> pd.DataFrame:
    groups = details.groupby(
        ["library_id", "polynomial_degree", "include_sin_cos", "stlsq_threshold", "system_id", "source_initial_condition_set"],
        dropna=False,
    )
    rows = []
    for keys, group in groups:
        first = group.iloc[0]
        rows.append(
            {
                "library_id": keys[0],
                "polynomial_degree": keys[1],
                "include_sin_cos": keys[2],
                "stlsq_threshold": keys[3],
                "system_id": keys[4],
                "source_initial_condition_set": keys[5],
                "dimension": int(first["dimension"]),
                "phasec_representability_threeway": first["phasec_representability_threeway"],
                "n_target_regressions": int(first["dimension"]),
                "n_evaluation_integrations": 2,
                "fit_elapsed_s_context": float(first["fit_elapsed_s_context"]),
                "elapsed_s_evidence_role": "context_not_evidence",
            }
        )
    return pd.DataFrame(rows)


def run_sindy(
    config_path: Path,
    trajectory_export_dir: Path,
    output_data_dir: str = "",
    output_table_dir: str = "",
) -> dict[str, Path]:
    config = load_config(config_path)
    if output_data_dir:
        config["output_data_dir"] = output_data_dir
    if output_table_dir:
        config["output_table_dir"] = output_table_dir
    benchmark = load_benchmark(resolve_path(config.get("benchmark_path", "../benchmarks/data/strogatz_extended.json"), config_path))
    support = load_phase_c_support(resolve_path(config.get("phase_c_support_path", "../studies/regression/phase_c_support.json"), config_path))
    support_by_id = support.set_index("system_id")
    t_grid, trajectories, trajectory_check = load_exported_trajectories(trajectory_export_dir, benchmark)

    detail_rows: list[dict[str, Any]] = []
    for cfg in library_grid(config):
        for system in benchmark:
            detail_rows.extend(fit_eval_rows(system, cfg, t_grid, trajectories, support_by_id))

    details = pd.DataFrame(detail_rows)
    frames = {
        "trajectory_check": trajectory_check,
        "trajectory_hashes": trajectory_hash_rows(benchmark, t_grid, trajectories),
        "details": details,
        "summary": summarize(details),
        "costs": cost_table(details),
    }
    data_dir = phasec_output_path(config.get("output_data_dir", "data/paper1_phaseC_v1/phasec_sindy_baseline"), config_path)
    table_dir = phasec_output_path(config.get("output_table_dir", "tables/paper1_phaseC_v1/phasec_sindy_baseline"), config_path)
    data_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, frame in frames.items():
        path = data_dir / f"{name}.csv"
        frame.to_csv(path, index=False)
        paths[name] = path
    for name in ["summary", "costs", "trajectory_hashes"]:
        csv_path = table_dir / f"phasec_sindy_{name}.csv"
        tex_path = table_dir / f"phasec_sindy_{name}.tex"
        frames[name].to_csv(csv_path, index=False)
        frames[name].to_latex(tex_path, index=False, escape=True)
        paths[f"table_{name}_csv"] = csv_path
        paths[f"table_{name}_tex"] = tex_path
    return paths


def read_records_dir(records_dir: Path) -> list[dict[str, Any]]:
    if not records_dir.is_dir():
        fail(f"EvoGrow records directory does not exist: {records_dir}")
    records = []
    for path in sorted(p for p in records_dir.glob("cell_*.jsonl") if not p.name.endswith(".heartbeat.jsonl")):
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(lines) != 1:
            fail(f"{path} contains {len(lines)} records, expected exactly 1")
        record = json.loads(lines[0])
        record["_source_file"] = str(path)
        records.append(record)
    if not records:
        fail(f"no EvoGrow JSONL records found in {records_dir}")
    return records


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def validate_evogrow_registry(
    evogrow: pd.DataFrame,
    expected_systems: set[int],
    expected_ics: set[int],
    expected_seeds: set[int],
    args: argparse.Namespace,
) -> None:
    if "experiment_id" not in evogrow.columns or set(evogrow["experiment_id"]) != {CAMPAIGN_ID}:
        fail(f"EvoGrow input must be Phase-C only ({CAMPAIGN_ID})")
    for column, expected in [
        ("git_hash", args.expected_git_hash),
        ("config_fingerprint", args.expected_config_fingerprint),
        ("stage_cap_behavior_fingerprint", args.expected_stage_cap_behavior_fingerprint),
    ]:
        values = {str(value) for value in evogrow[column] if str(value) != ""}
        if len(values) != 1:
            fail(f"EvoGrow {column} must be unique; got {sorted(values)}")
        if expected and values != {expected}:
            fail(f"EvoGrow {column} {sorted(values)} does not match expected {expected!r}")
    if not (evogrow["basis_name"] == "staged_polynomial_basis_with_constant").all():
        fail("EvoGrow records are not all staged_polynomial_basis_with_constant")

    systems = expected_systems or {int(value) for value in evogrow["system_id"]}
    ics = expected_ics or {int(value) for value in evogrow["initial_condition_set"]}
    seeds = expected_seeds or {int(value) for value in evogrow["seed"]}
    seed_condition_pairs = {
        (int(row["seed"]), str(row["condition"]))
        for _, row in evogrow[["seed", "condition"]].drop_duplicates().iterrows()
    }
    groups = evogrow.groupby(["system_id", "initial_condition_set"], dropna=False)
    for system_id in systems:
        for ic_set in ics:
            key = (system_id, ic_set)
            if key not in groups.groups:
                fail(f"EvoGrow input incomplete: missing system_id={system_id}, initial_condition_set={ic_set}")
            cell_group = groups.get_group(key)
            got_seeds = {int(value) for value in cell_group["seed"]}
            if got_seeds != seeds:
                fail(f"EvoGrow input incomplete for {key}: seeds {sorted(got_seeds)} != expected {sorted(seeds)}")
            got_seed_condition_pairs = {
                (int(row["seed"]), str(row["condition"]))
                for _, row in cell_group[["seed", "condition"]].drop_duplicates().iterrows()
            }
            if got_seed_condition_pairs != seed_condition_pairs:
                fail(
                    f"EvoGrow input incomplete for {key}: seed-condition pairs "
                    f"{sorted(got_seed_condition_pairs)} != expected {sorted(seed_condition_pairs)}"
                )


def build_evogrow_cell_rows(evogrow: pd.DataFrame) -> pd.DataFrame:
    rows = []
    metric_bool = ["exact_support_match_raw", "exact_support_match_pruned"]
    for (system_id, ic_set), group in evogrow.groupby(["system_id", "initial_condition_set"], dropna=False):
        r2_values = pd.to_numeric(group["r2"], errors="coerce")
        rows.append(
            {
                "system_id": int(system_id),
                "initial_condition_set": int(ic_set),
                "evogrow_seed_policy": "mean_rate_over_available_phasec_seeds",
                "evogrow_seed_count": int(group["seed"].nunique()),
                "evogrow_seeds": ",".join(str(int(seed)) for seed in sorted(group["seed"].astype(int).unique())),
                "evogrow_structure_hit_raw_rate": float(group["exact_support_match_raw"].map(as_bool).mean()),
                "evogrow_structure_hit_pruned_rate": float(group["exact_support_match_pruned"].map(as_bool).mean()),
                "evogrow_r2_gt_0_9_rate": float((r2_values > R2_THRESHOLD).mean()),
                "evogrow_r2_mean": float(r2_values.mean()),
                "git_hash": single_value(group["git_hash"], "git_hash"),
                "config_fingerprint": single_value(group["config_fingerprint"], "config_fingerprint"),
                "stage_cap_behavior_fingerprint": single_value(
                    group["stage_cap_behavior_fingerprint"], "stage_cap_behavior_fingerprint"
                ),
            }
        )
        for column in metric_bool:
            if column not in group.columns:
                fail(f"EvoGrow records missing {column}")
    return pd.DataFrame(rows)


def single_value(series: pd.Series, column: str) -> str:
    values = {str(value) for value in series if str(value) != ""}
    if len(values) != 1:
        fail(f"{column} is not unique in EvoGrow group: {sorted(values)}")
    return next(iter(values))


def valid_sindy_for_pairing(details: pd.DataFrame) -> pd.DataFrame:
    generalization = details[
        (details["regime"] == "generalization")
        & (details["valid_for_analysis"].astype(bool))
        & (details["reconstruction_control_valid"].astype(bool))
    ].copy()
    if generalization.empty:
        fail("SINDy details contain no valid generalization rows")
    return generalization


def pair_sindy_evogrow(args: argparse.Namespace) -> Path:
    sindy = pd.read_csv(args.sindy_details)
    records = read_records_dir(Path(args.evogrow_records_dir))
    evogrow = pd.DataFrame([row_from_record(record, CAMPAIGN_ID) for record in records])
    expected_systems = parse_int_set(args.expected_systems)
    expected_ics = parse_int_set(args.expected_ic_sets)
    expected_seeds = parse_int_set(args.expected_seeds)
    validate_evogrow_registry(evogrow, expected_systems, expected_ics, expected_seeds, args)
    evogrow_cells = build_evogrow_cell_rows(evogrow)
    available_keys = evogrow_cells[["system_id", "initial_condition_set"]].drop_duplicates()
    sindy_for_keys = sindy.merge(available_keys, on=["system_id", "initial_condition_set"], how="inner")
    if sindy_for_keys.empty:
        fail("no SINDy rows match the EvoGrow input keys")
    sindy_gen = valid_sindy_for_pairing(sindy_for_keys)
    paired = sindy_gen.merge(evogrow_cells, on=["system_id", "initial_condition_set"], how="inner", validate="many_to_one")
    required = len(sindy_gen)
    if len(paired) != required:
        missing = sindy_gen.merge(evogrow_cells, on=["system_id", "initial_condition_set"], how="left", indicator=True)
        missing = missing[missing["_merge"] == "left_only"][["system_id", "initial_condition_set"]].drop_duplicates()
        fail(f"pairing incomplete: {len(paired)} paired rows for {required} SINDy rows; missing {missing.to_dict('records')}")
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    paired.to_csv(output, index=False)

    PAIR_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    paired_summary(paired).to_csv(PAIR_TABLE_DIR / "phasec_sindy_paired_summary.csv", index=False)
    return output


def paired_summary(paired: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "library_id",
        "direction",
        "dimension",
        "phasec_representability_threeway",
        "evogrow_seed_policy",
    ]
    rows = []
    for keys, group in paired.groupby(group_columns, dropna=False):
        n_cells = int(len(group))
        rows.append(
            {
                **dict(zip(group_columns, keys)),
                "aggregation_scope": "dimension_by_phasec_representability_threeway",
                "n_cells": n_cells,
                "sindy_structure_hit_raw_rate": float(group["sindy_structure_hit_raw"].mean()),
                "sindy_structure_hit_pruned_rate": float(group["sindy_structure_hit_pruned"].mean()),
                "sindy_r2_gt_0_9_rate": float(group["r2_gt_0_9"].mean()),
                "evogrow_structure_hit_raw_rate": float(group["evogrow_structure_hit_raw_rate"].mean()),
                "evogrow_structure_hit_pruned_rate": float(group["evogrow_structure_hit_pruned_rate"].mean()),
                "evogrow_r2_gt_0_9_rate": float(group["evogrow_r2_gt_0_9_rate"].mean()),
            }
        )
    return pd.DataFrame(rows)


def values_equal(reference: Any, candidate: Any) -> bool:
    if pd.isna(reference) and pd.isna(candidate):
        return True
    return reference == candidate


def compare_csv_byte_identical(reference: Path, candidate: Path) -> list[str]:
    if reference.read_bytes() == candidate.read_bytes():
        return []
    return [f"{reference.name}: expected byte-identical output"]


def compare_reported_csv(
    reference: Path,
    candidate: Path,
    runtime_columns: set[str],
    allow_diverged_r2_differences: bool = False,
) -> list[str]:
    reference_frame = pd.read_csv(reference)
    candidate_frame = pd.read_csv(candidate)
    failures: list[str] = []
    if list(reference_frame.columns) != list(candidate_frame.columns):
        return [
            f"{reference.name}: columns changed from {list(reference_frame.columns)} "
            f"to {list(candidate_frame.columns)}"
        ]
    if len(reference_frame) != len(candidate_frame):
        return [f"{reference.name}: row count changed from {len(reference_frame)} to {len(candidate_frame)}"]

    for column in reference_frame.columns:
        if column in runtime_columns:
            continue
        for row_index, (reference_value, candidate_value) in enumerate(
            zip(reference_frame[column], candidate_frame[column], strict=True),
            start=2,
        ):
            if values_equal(reference_value, candidate_value):
                continue
            if (
                allow_diverged_r2_differences
                and column == "r2"
                and str(reference_frame.at[row_index - 2, "integration_status"]) == "diverged"
                and str(candidate_frame.at[row_index - 2, "integration_status"]) == "diverged"
            ):
                continue
            failures.append(
                f"{reference.name}: reported column {column!r} changed at CSV row {row_index} "
                f"from {reference_value!r} to {candidate_value!r}"
            )
            break
    return failures


def compare_wpn6_outputs(
    reference_data: Path,
    reference_tables: Path,
    candidate_data: Path,
    candidate_tables: Path,
) -> list[str]:
    failures: list[str] = []
    for name in ["trajectory_check.csv", "summary.csv"]:
        failures.extend(compare_csv_byte_identical(reference_data / name, candidate_data / name))
    for name in ["wp_n6_trajectory_check.csv", "wp_n6_summary.csv", "wp_n6_trajectory_check.tex", "wp_n6_summary.tex"]:
        failures.extend(compare_csv_byte_identical(reference_tables / name, candidate_tables / name))
    failures.extend(
        compare_reported_csv(
            reference_data / "details.csv",
            candidate_data / "details.csv",
            WPN6_DETAILS_RUNTIME_COLUMNS,
            allow_diverged_r2_differences=True,
        )
    )
    failures.extend(
        compare_reported_csv(
            reference_data / "costs.csv",
            candidate_data / "costs.csv",
            WPN6_COST_RUNTIME_COLUMNS,
            allow_diverged_r2_differences=False,
        )
    )
    failures.extend(
        compare_reported_csv(
            reference_tables / "wp_n6_costs.csv",
            candidate_tables / "wp_n6_costs.csv",
            WPN6_COST_RUNTIME_COLUMNS,
            allow_diverged_r2_differences=False,
        )
    )
    return failures


def compare_phasec_details(reference_path: Path, candidate_path: Path, output_path: Path) -> Path:
    reference = pd.read_csv(reference_path)
    candidate = pd.read_csv(candidate_path)
    key_columns = [
        "library_id",
        "polynomial_degree",
        "include_sin_cos",
        "stlsq_threshold",
        "system_id",
        "source_initial_condition_set",
        "target_initial_condition_set",
        "initial_condition_set",
        "direction",
        "regime",
    ]
    merged = reference.merge(candidate, on=key_columns, suffixes=("_reference", "_candidate"), validate="one_to_one")
    if len(merged) != len(reference) or len(merged) != len(candidate):
        fail(
            f"Phase-C details are not one-to-one comparable: "
            f"reference={len(reference)}, candidate={len(candidate)}, paired={len(merged)}"
        )
    r2_reference = pd.to_numeric(merged["r2_reference"], errors="coerce")
    r2_candidate = pd.to_numeric(merged["r2_candidate"], errors="coerce")
    r2_abs_delta = (r2_candidate - r2_reference).abs()
    finite_delta = r2_abs_delta[np.isfinite(r2_abs_delta)]
    quantiles = finite_delta.quantile([0.0, 0.25, 0.5, 0.75, 1.0]) if len(finite_delta) else pd.Series(dtype=float)
    summary = pd.DataFrame(
        [
            {
                "n_rows_reference": int(len(reference)),
                "n_rows_candidate": int(len(candidate)),
                "n_rows_paired": int(len(merged)),
                "r2_gt_0_9_changed_count": int(
                    (merged["r2_gt_0_9_reference"].astype(bool) != merged["r2_gt_0_9_candidate"].astype(bool)).sum()
                ),
                "sindy_structure_hit_raw_changed_count": int(
                    (
                        merged["sindy_structure_hit_raw_reference"].astype(bool)
                        != merged["sindy_structure_hit_raw_candidate"].astype(bool)
                    ).sum()
                ),
                "sindy_structure_hit_pruned_changed_count": int(
                    (
                        merged["sindy_structure_hit_pruned_reference"].astype(bool)
                        != merged["sindy_structure_hit_pruned_candidate"].astype(bool)
                    ).sum()
                ),
                "r2_abs_delta_finite_count": int(len(finite_delta)),
                "r2_abs_delta_q000": float(quantiles.loc[0.0]) if len(finite_delta) else float("nan"),
                "r2_abs_delta_q025": float(quantiles.loc[0.25]) if len(finite_delta) else float("nan"),
                "r2_abs_delta_q050": float(quantiles.loc[0.5]) if len(finite_delta) else float("nan"),
                "r2_abs_delta_q075": float(quantiles.loc[0.75]) if len(finite_delta) else float("nan"),
                "r2_abs_delta_q100": float(quantiles.loc[1.0]) if len(finite_delta) else float("nan"),
            }
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)
    return output_path


def check_wpn6_bitidentical(args: argparse.Namespace) -> None:
    from scripts.aggregate.run_wp_n6_sindy_baseline import main as wpn6_main

    config_path = Path(args.config).resolve()
    original = load_config(config_path)
    with tempfile.TemporaryDirectory(prefix="wpn6_bitcheck_") as tmp:
        tmp_root = Path(tmp)
        temp_config = dict(original)
        temp_config["output_data_dir"] = str(tmp_root / "data")
        temp_config["output_table_dir"] = str(tmp_root / "tables")
        temp_config_path = tmp_root / "wpn6_config.json"
        temp_config_path.write_text(json.dumps(temp_config), encoding="utf-8")
        old_argv = sys.argv[:]
        try:
            sys.argv = ["run_wp_n6_sindy_baseline.py", "--config", str(temp_config_path)]
            wpn6_main()
        finally:
            sys.argv = old_argv
        reference_data = Path(args.reference_data_dir)
        reference_tables = Path(args.reference_table_dir)
        mismatches = compare_wpn6_outputs(reference_data, reference_tables, tmp_root / "data", tmp_root / "tables")
        if mismatches:
            fail("WP-N6 reported-measure check failed:\n- " + "\n- ".join(mismatches))


def main() -> int:
    args = parse_args()
    try:
        if args.command == "run-sindy":
            paths = run_sindy(
                Path(args.config).resolve(),
                Path(args.trajectory_export_dir).resolve(),
                args.output_data_dir,
                args.output_table_dir,
            )
            print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))
        elif args.command == "pair":
            path = pair_sindy_evogrow(args)
            print(f"Wrote {path}")
        elif args.command == "check-wpn6-bitidentical":
            check_wpn6_bitidentical(args)
            print("WP-N6 bit-identical check passed")
        elif args.command == "compare-details":
            path = compare_phasec_details(
                Path(args.reference_details),
                Path(args.candidate_details),
                Path(args.output),
            )
            print(f"Wrote {path}")
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
