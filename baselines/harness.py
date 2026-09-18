import argparse
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.run_wp_n6_sindy_baseline import (  # noqa: E402
    LibraryConfig,
    active_terms_by_equation,
    fit_sindy,
    load_benchmark,
    polynomial_true_terms,
    simulate_model,
    support_hit,
)


ODEFORMER_COMMIT = "c9193012ad07a97186290b98d8290d1a177f4609"
R2_THRESHOLD = 0.9
REGISTERED_INACTIVE = {
    "pysr": "PySR dependency is not installed; it carries an isolated Julia runtime.",
    "proged": "ProGED dependency is not installed in the baseline image.",
    "ffx": "FFX dependency is not installed in the baseline image.",
    "ellyn": "ellyn dependency is not installed in the baseline image.",
}


@dataclass(frozen=True)
class TrajectoryCell:
    system_id: int
    initial_condition_set: int
    dimension: int
    time: np.ndarray
    state: np.ndarray
    time_sha256: str
    state_sha256: str


def fail(message: str) -> None:
    raise ValueError(message)


def resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path.resolve()
    return (REPO_ROOT / path).resolve()


def parse_shape(text: Any, label: str) -> tuple[int, ...]:
    try:
        values = json.loads(str(text))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON shape: {text!r}") from exc
    if not isinstance(values, list) or not all(isinstance(value, int) and value >= 0 for value in values):
        fail(f"{label} must be a JSON integer list, got {text!r}")
    return tuple(int(value) for value in values)


def read_float64_file(path: Path, shape: tuple[int, ...], expected_hash: str, label: str) -> np.ndarray:
    payload = path.read_bytes()
    actual_hash = hashlib.sha256(payload).hexdigest()
    if actual_hash != str(expected_hash):
        fail(f"hash mismatch for {label}: expected {expected_hash}, got {actual_hash}")
    expected_bytes = int(np.prod(shape, dtype=np.int64)) * 8
    if len(payload) != expected_bytes:
        fail(f"wrong byte length for {label}: expected {expected_bytes}, got {len(payload)}")
    return np.frombuffer(payload, dtype="<f8").reshape(shape, order="C").copy()


def load_exported_cells(export_dir: Path, benchmark: list[dict[str, Any]]) -> tuple[dict[tuple[int, int], TrajectoryCell], pd.DataFrame]:
    manifest_path = export_dir / "trajectory_manifest.csv"
    if not manifest_path.is_file():
        fail(f"missing trajectory export manifest: {manifest_path}")
    manifest = pd.read_csv(manifest_path)
    required = {
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
    missing = sorted(required - set(manifest.columns))
    if missing:
        fail(f"trajectory manifest missing columns: {missing}")
    dims = {int(row["id"]): int(row["dim"]) for row in benchmark}
    cells: dict[tuple[int, int], TrajectoryCell] = {}
    check_rows: list[dict[str, Any]] = []
    for _, row in manifest.sort_values(["system_id", "initial_condition_set"]).iterrows():
        system_id = int(row["system_id"])
        ic_set = int(row["initial_condition_set"])
        if system_id not in dims:
            fail(f"manifest contains unknown system_id={system_id}")
        dim = int(row["dimension"])
        if dim != dims[system_id]:
            fail(f"dimension mismatch for system_id={system_id}: manifest {dim}, benchmark {dims[system_id]}")
        if str(row["hash_format"]) != "sha256_raw_little_endian_float64":
            fail(f"unsupported hash_format for system_id={system_id}, ic={ic_set}")
        if str(row["dtype"]) != "float64" or str(row["byte_order"]) != "little_endian":
            fail(f"unsupported dtype/byte_order for system_id={system_id}, ic={ic_set}")
        if str(row["time_axis_order"]) != "time" or str(row["state_axis_order"]) != "time_by_dimension_c_order":
            fail(f"unsupported axis order for system_id={system_id}, ic={ic_set}")
        time_shape = parse_shape(row["time_shape"], f"time_shape system_id={system_id}, ic={ic_set}")
        state_shape = parse_shape(row["state_shape"], f"state_shape system_id={system_id}, ic={ic_set}")
        if len(time_shape) != 1 or state_shape != (time_shape[0], dim):
            fail(f"shape mismatch for system_id={system_id}, ic={ic_set}: time={time_shape}, state={state_shape}")
        time_values = read_float64_file(export_dir / str(row["time_path"]), time_shape, str(row["time_sha256"]), f"system_id={system_id}, ic={ic_set} time")
        state_values = read_float64_file(export_dir / str(row["state_path"]), state_shape, str(row["state_sha256"]), f"system_id={system_id}, ic={ic_set} state")
        cells[(system_id, ic_set)] = TrajectoryCell(
            system_id=system_id,
            initial_condition_set=ic_set,
            dimension=dim,
            time=time_values,
            state=state_values,
            time_sha256=str(row["time_sha256"]),
            state_sha256=str(row["state_sha256"]),
        )
        check_rows.append(
            {
                "system_id": system_id,
                "initial_condition_set": ic_set,
                "dimension": dim,
                "time_sha256": str(row["time_sha256"]),
                "state_sha256": str(row["state_sha256"]),
                "hash_verified": True,
            }
        )
    return cells, pd.DataFrame(check_rows)


def r2_by_dimension(reference: np.ndarray, prediction: np.ndarray | None) -> list[float]:
    if prediction is None or reference.shape != prediction.shape or not np.all(np.isfinite(prediction)):
        return [0.0 for _ in range(reference.shape[1])]
    scores = []
    for idx in range(reference.shape[1]):
        y = reference[:, idx]
        yhat = prediction[:, idx]
        denom = float(np.sum((y - np.mean(y)) ** 2))
        if denom == 0.0:
            scores.append(0.0)
        else:
            score = 1.0 - float(np.sum((y - yhat) ** 2)) / denom
            scores.append(float(score) if math.isfinite(score) else 0.0)
    return scores


def aggregate_r2(reference: np.ndarray, prediction: np.ndarray | None) -> dict[str, float]:
    scores = r2_by_dimension(reference, prediction)
    variances = np.var(reference, axis=0)
    arithmetic = float(np.mean(scores)) if scores else 0.0
    if float(np.sum(variances)) == 0.0:
        weighted = arithmetic
    else:
        weighted = float(np.average(scores, weights=variances))
    return {
        "r2_arithmetic_mean": arithmetic,
        "r2_variance_weighted": weighted,
    }


def package_versions() -> dict[str, str]:
    names = ["numpy", "pandas", "scipy", "sympy", "pysindy", "torch", "gdown", "scikit-learn"]
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not_installed"
    return versions


def git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    except Exception:
        return "unknown"


def base_record(method: str, config: dict[str, Any], fit_cell: TrajectoryCell, target_cell: TrajectoryCell) -> dict[str, Any]:
    return {
        "record_schema": "phasec_external_baseline_v1",
        "git_hash": git_hash(),
        "odeformer_commit": ODEFORMER_COMMIT,
        "environment": json.dumps(package_versions(), sort_keys=True, separators=(",", ":")),
        "method": method,
        "method_config": json.dumps(config, sort_keys=True, separators=(",", ":")),
        "system_id": fit_cell.system_id,
        "dimension": fit_cell.dimension,
        "fit_initial_condition_set": fit_cell.initial_condition_set,
        "generalization_initial_condition_set": target_cell.initial_condition_set,
        "time_sha256": fit_cell.time_sha256,
        "fit_state_sha256": fit_cell.state_sha256,
        "generalization_state_sha256": target_cell.state_sha256,
        "status": "success",
        "error_type": "",
        "error_message": "",
    }


def r2_threshold_flags(prefix: str, scores: dict[str, float]) -> dict[str, bool]:
    return {f"{prefix}_{name}_gt_0_9": value > R2_THRESHOLD for name, value in scores.items()}


def zero_r2_scores() -> dict[str, float]:
    return {"r2_arithmetic_mean": 0.0, "r2_variance_weighted": 0.0}


def record_failure(record: dict[str, Any], exc: Exception) -> dict[str, Any]:
    reconstruction_r2 = zero_r2_scores()
    generalization_r2 = zero_r2_scores()
    failed = dict(record)
    failed.update(
        {
            "status": "error",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "model": "{}",
            "active_terms_raw": "[]",
            "active_terms_pruned": "[]",
            "true_terms": "[]",
            "structure_hit_raw": False,
            "structure_hit_pruned": False,
            **{f"reconstruction_{key}": value for key, value in reconstruction_r2.items()},
            **{f"generalization_{key}": value for key, value in generalization_r2.items()},
            **r2_threshold_flags("reconstruction", reconstruction_r2),
            **r2_threshold_flags("generalization", generalization_r2),
        }
    )
    return failed


def run_sindy_record(system: dict[str, Any], fit_cell: TrajectoryCell, target_cell: TrajectoryCell, config: dict[str, Any]) -> dict[str, Any]:
    record = base_record("sindy", config, fit_cell, target_cell)
    start = time.perf_counter()
    try:
        cfg = LibraryConfig(
            library_id=f"pysindy_poly_deg{int(config['polynomial_degree'])}_stlsq_{float(config['threshold']):g}",
            polynomial_degree=int(config["polynomial_degree"]),
            include_trig=bool(config.get("include_trig", False)),
            threshold=float(config["threshold"]),
        )
        names = [f"x{idx}" for idx in range(fit_cell.dimension)]
        model = fit_sindy(fit_cell.state, fit_cell.time, names, cfg)
        feature_names = model.get_feature_names()
        coefficients = model.coefficients()
        raw_terms = active_terms_by_equation(coefficients, feature_names)
        true_terms = polynomial_true_terms(system)
        reconstruction, reconstruction_status = simulate_model(coefficients, feature_names, fit_cell.state[0, :], fit_cell.time)
        generalization, generalization_status = simulate_model(coefficients, feature_names, target_cell.state[0, :], target_cell.time)
        reconstruction_r2 = aggregate_r2(fit_cell.state, reconstruction)
        generalization_r2 = aggregate_r2(target_cell.state, generalization)
        record.update(
            {
                "model": json.dumps(
                    {
                        "feature_names": feature_names,
                        "coefficients": np.asarray(coefficients, dtype=float).tolist(),
                    },
                    separators=(",", ":"),
                ),
                "active_terms_raw": json.dumps([sorted(terms) for terms in raw_terms], separators=(",", ":")),
                "active_terms_pruned": json.dumps([sorted(terms) for terms in raw_terms], separators=(",", ":")),
                "true_terms": json.dumps([sorted(terms) for terms in true_terms], separators=(",", ":")),
                "structure_hit_raw": support_hit(raw_terms, true_terms),
                "structure_hit_pruned": support_hit(raw_terms, true_terms),
                "reconstruction_status": reconstruction_status,
                "generalization_status": generalization_status,
                "fit_elapsed_s_context": time.perf_counter() - start,
                **{f"reconstruction_{key}": value for key, value in reconstruction_r2.items()},
                **{f"generalization_{key}": value for key, value in generalization_r2.items()},
                **r2_threshold_flags("reconstruction", reconstruction_r2),
                **r2_threshold_flags("generalization", generalization_r2),
            }
        )
        return record
    except Exception as exc:
        return record_failure(record, exc)


def run_odeformer_record(_system: dict[str, Any], fit_cell: TrajectoryCell, target_cell: TrajectoryCell, config: dict[str, Any]) -> dict[str, Any]:
    record = base_record("odeformer", config, fit_cell, target_cell)
    try:
        import odeformer  # type: ignore  # noqa: F401
    except Exception as exc:
        return record_failure(record, RuntimeError(f"ODEFormer is not importable in this environment: {exc}"))
    return record_failure(record, NotImplementedError("ODEFormer adapter requires the upstream inference entry point and weights."))


def inactive_record(method: str, fit_cell: TrajectoryCell, target_cell: TrajectoryCell) -> dict[str, Any]:
    record = base_record(method, {"active": False}, fit_cell, target_cell)
    return record_failure(record, RuntimeError(REGISTERED_INACTIVE[method]))


def optional_int_set(values: Any, label: str) -> set[int] | None:
    if values is None:
        return None
    if not isinstance(values, list):
        fail(f"{label} must be a list of integers")
    result: set[int] = set()
    for value in values:
        if isinstance(value, bool):
            fail(f"{label} must contain integers, got {value!r}")
        result.add(int(value))
    return result


def selected_systems(benchmark: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    dimensions = optional_int_set(config.get("dimensions"), "dimensions")
    system_ids = optional_int_set(config.get("system_ids"), "system_ids")
    max_systems = config.get("max_systems")
    selected = []
    for system in sorted(benchmark, key=lambda item: int(item["id"])):
        if dimensions is not None and int(system["dim"]) not in dimensions:
            continue
        if system_ids is not None and int(system["id"]) not in system_ids:
            continue
        selected.append(system)
    if max_systems is not None:
        selected = selected[: int(max_systems)]
    return selected


def selected_manifest_rows(manifest: pd.DataFrame, system_ids: set[int]) -> pd.DataFrame:
    selected = manifest[manifest["system_id"].astype(int).isin(system_ids)].copy()
    return selected.sort_values(["system_id", "initial_condition_set"]).reset_index(drop=True)


def run(config_path: Path, output_dir: str | None = None, corrupt_manifest_hash: bool = False, force_sindy_failure: bool = False) -> Path:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    benchmark = load_benchmark(resolve_path(config["benchmark_path"]))
    export_dir = resolve_path(config["trajectory_export_dir"])
    if corrupt_manifest_hash:
        manifest = pd.read_csv(export_dir / "trajectory_manifest.csv")
        manifest.loc[0, "state_sha256"] = "0" * 64
        temp_dir = resolve_path("outputs/wp_n19_corrupt_manifest_probe")
        temp_dir.mkdir(parents=True, exist_ok=True)
        manifest["time_path"] = manifest["time_path"].map(lambda value: str((export_dir / str(value)).resolve()))
        manifest["state_path"] = manifest["state_path"].map(lambda value: str((export_dir / str(value)).resolve()))
        manifest.to_csv(temp_dir / "trajectory_manifest.csv", index=False)
        export_dir = temp_dir
    cells, trajectory_check = load_exported_cells(export_dir, benchmark)
    out_dir = resolve_path(output_dir or config["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    systems = selected_systems(benchmark, config)
    selected_ids = {int(system["id"]) for system in systems}
    manifest = pd.read_csv(export_dir / "trajectory_manifest.csv")
    selection_rows = selected_manifest_rows(manifest, selected_ids)
    selection_path = out_dir / "selected_systems.json"
    selection_path.write_text(
        json.dumps(
            {
                "selection": {
                    "dimensions": config.get("dimensions"),
                    "system_ids": config.get("system_ids"),
                    "max_systems": config.get("max_systems"),
                },
                "system_count": len(systems),
                "trajectory_manifest_row_count": int(len(selection_rows)),
                "systems": [
                    {"system_id": int(system["id"]), "dimension": int(system["dim"])}
                    for system in systems
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    records: list[dict[str, Any]] = []
    methods = list(config.get("methods", ["sindy", "odeformer"]))
    for system in systems:
        system_id = int(system["id"])
        for fit_ic, target_ic in [(1, 2), (2, 1)]:
            fit_cell = cells[(system_id, fit_ic)]
            target_cell = cells[(system_id, target_ic)]
            for method in methods:
                if method == "sindy":
                    method_config = dict(config["sindy"])
                    if force_sindy_failure:
                        method_config["threshold"] = "not_a_float"
                    records.append(run_sindy_record(system, fit_cell, target_cell, method_config))
                elif method == "odeformer":
                    records.append(run_odeformer_record(system, fit_cell, target_cell, config["odeformer"]))
                elif method in REGISTERED_INACTIVE:
                    records.append(inactive_record(method, fit_cell, target_cell))
                else:
                    records.append(record_failure(base_record(method, {}, fit_cell, target_cell), RuntimeError("unknown method")))
    records_path = out_dir / "records.jsonl"
    records_path.write_text("\n".join(json.dumps(record, sort_keys=True) for record in records) + "\n", encoding="utf-8")
    pd.DataFrame(records).to_csv(out_dir / "records.csv", index=False)
    trajectory_check.to_csv(out_dir / "trajectory_check.csv", index=False)
    return records_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run external ODE discovery baselines on exported EvoODE trajectories.")
    parser.add_argument("--config", default="baselines/configs/wp_n19_smoke.json")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--corrupt-manifest-hash", action="store_true")
    parser.add_argument("--force-sindy-failure", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        path = run(
            resolve_path(args.config),
            args.output_dir or None,
            corrupt_manifest_hash=args.corrupt_manifest_hash,
            force_sindy_failure=args.force_sindy_failure,
        )
        print(path)
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
