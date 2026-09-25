import argparse
import contextlib
import errno
import functools
import hashlib
import importlib
import importlib.metadata
import json
import math
import os
import random
import re
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from functools import partial
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
ODEFORMER_PARAM_OPTIMIZER_NORMALIZED_SHA256 = "31e4a6cabf2b180118c6ee47286a537968720710b420c1dc17bc8d670ceb0bea"
R2_THRESHOLD = 0.9
PREDICTION_OUTCOMES = {
    "finite",
    "none",
    "odeformer_nan_sentinel",
    "wrong_shape",
    "nonfinite",
}
R2_DIMENSION_STATUSES = {
    "regular",
    "zero_convention",
}
R2_ZERO_REASONS = {
    "",
    "prediction_none",
    "prediction_odeformer_nan_sentinel",
    "prediction_wrong_shape",
    "prediction_nonfinite",
    "nonfinite_score",
    "reference_no_variance",
}
ERROR_MESSAGE_LIMIT = 240
REGISTERED_INACTIVE = {
    "pysr": "PySR dependency is not installed; it carries an isolated Julia runtime.",
    "proged": "ProGED dependency is not installed in the baseline image.",
    "ffx": "FFX dependency is not installed in the baseline image.",
    "ellyn": "ellyn dependency is not installed in the baseline image.",
}
ODEFORMER_TIMEOUT_COUNT_KEYS = [
    "fit_candidate_ranking",
    "reconstruction_before_optimization",
    "generalization_before_optimization",
    "reconstruction_after_optimization",
    "generalization_after_optimization",
    "constant_optimization",
    "unclassified",
]


def empty_odeformer_timeout_counts() -> dict[str, int]:
    return {key: 0 for key in ODEFORMER_TIMEOUT_COUNT_KEYS}


ODEFORMER_INTEGRATION_OUTCOMES = [
    "call",
    "trajectory",
    "none",
    "nan_sentinel",
    "none_after_timeout",
    "nan_sentinel_after_timeout",
]
_NO_INTEGRATION_RESULT = object()


def empty_odeformer_integration_outcome_counts() -> dict[str, dict[str, int]]:
    return {
        phase: {outcome: 0 for outcome in ODEFORMER_INTEGRATION_OUTCOMES}
        for phase in ODEFORMER_TIMEOUT_COUNT_KEYS
    }


def odeformer_timeout_with_hook(
    seconds: float = 10,
    on_timeout: Any | None = None,
    error_type: type[BaseException] | None = None,
    error_message: str = os.strerror(errno.ETIME),
):
    if error_type is None:
        error_type = TimeoutError

    def decorator(func):
        def _handle_timeout(repeat_id, signum, frame):
            if on_timeout is not None:
                on_timeout()
            signal.signal(signal.SIGALRM, partial(_handle_timeout, repeat_id + 1))
            signal.setitimer(signal.ITIMER_REAL, seconds)
            raise error_type(error_message)

        def wrapper(*args, **kwargs):
            old_signal = signal.signal(signal.SIGALRM, partial(_handle_timeout, 0))
            old_time_left = signal.getitimer(signal.ITIMER_REAL)[0]
            assert type(old_time_left) is float and old_time_left >= 0
            if 0 < old_time_left < seconds:
                signal.setitimer(signal.ITIMER_REAL, old_time_left)
            else:
                signal.setitimer(signal.ITIMER_REAL, seconds)
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
            finally:
                if old_time_left == 0:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                else:
                    time_elapsed = time.time() - start_time
                    signal.signal(signal.SIGALRM, old_signal)
                    signal.setitimer(signal.ITIMER_REAL, max(0, old_time_left - time_elapsed))
            return result

        return functools.wraps(func)(wrapper)

    return decorator


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


class ODEFormerInfrastructureError(RuntimeError):
    """Raised when required ODEFormer infrastructure files or imports are missing."""


def odeformer_source_root() -> tuple[Path, str]:
    env_value = os.environ.get("ODEFORMER_SOURCE_ROOT")
    if env_value:
        return Path(env_value).resolve(), "env"
    return (REPO_ROOT / "outputs" / "third_party" / "odeformer").resolve(), "default"


def normalized_text_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def odeformer_source_metadata() -> dict[str, str]:
    source_root, source = odeformer_source_root()
    param_optimizer_path = source_root / "param_optimizer.py"
    sha256 = ""
    if param_optimizer_path.is_file():
        sha256 = normalized_text_sha256(param_optimizer_path)
    return {
        "odeformer_source_root": str(source_root),
        "odeformer_source_root_source": source,
        "odeformer_param_optimizer_normalized_sha256": sha256,
    }


def import_odeformer_param_optimizer() -> Any:
    source_root, source = odeformer_source_root()
    param_optimizer_path = source_root / "param_optimizer.py"
    if not param_optimizer_path.is_file():
        raise ODEFormerInfrastructureError(
            f"ODEFormer source root from {source} does not contain param_optimizer.py: {param_optimizer_path}"
        )
    actual = normalized_text_sha256(param_optimizer_path)
    if actual != ODEFORMER_PARAM_OPTIMIZER_NORMALIZED_SHA256:
        raise ODEFormerInfrastructureError(
            "ODEFormer param_optimizer.py normalized hash mismatch: "
            f"expected {ODEFORMER_PARAM_OPTIMIZER_NORMALIZED_SHA256}, got {actual} at {param_optimizer_path}"
        )
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    existing = sys.modules.get("param_optimizer")
    if existing is not None:
        existing_file = getattr(existing, "__file__", "")
        try:
            if existing_file and Path(existing_file).resolve().is_relative_to(source_root):
                return existing
        except OSError:
            pass
        del sys.modules["param_optimizer"]
    try:
        return importlib.import_module("param_optimizer")
    except ImportError as exc:
        raise ODEFormerInfrastructureError(
            f"ODEFormer constant optimization imports failed from {source_root}: {type(exc).__name__}: {exc}"
        ) from exc


def preflight_odeformer_constant_optimization() -> None:
    import_odeformer_param_optimizer()


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


def manifest_relative_path(value: Any) -> Path:
    # The export manifest is written on Windows and stores "cells\file.bin"; inside a Linux
    # container a backslash is not a separator. The hash check on the bytes stays unchanged.
    return Path(str(value).replace("\\", "/"))


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
        time_values = read_float64_file(export_dir / manifest_relative_path(row["time_path"]), time_shape, str(row["time_sha256"]), f"system_id={system_id}, ic={ic_set} time")
        state_values = read_float64_file(export_dir / manifest_relative_path(row["state_path"]), state_shape, str(row["state_sha256"]), f"system_id={system_id}, ic={ic_set} state")
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


def short_error_message(exc: BaseException, limit: int = ERROR_MESSAGE_LIMIT) -> str:
    text = str(exc).replace("\r", " ").replace("\n", " ")
    return text[:limit]


def prediction_outcome(reference: np.ndarray, prediction: np.ndarray | None) -> str:
    if prediction is None:
        return "none"
    if is_odeformer_nan_sentinel(reference, prediction):
        return "odeformer_nan_sentinel"
    if reference.shape != prediction.shape:
        return "wrong_shape"
    if not np.all(np.isfinite(prediction)):
        return "nonfinite"
    return "finite"


def is_odeformer_nan_sentinel(reference: np.ndarray, prediction: np.ndarray | None) -> bool:
    if prediction is None:
        return False
    array = np.asarray(prediction)
    return array.ndim == 1 and array.shape == (reference.shape[0],) and bool(np.all(np.isnan(array)))


def r2_dimension_diagnostics(reference: np.ndarray, prediction: np.ndarray | None) -> tuple[str, list[str], list[str]]:
    outcome = prediction_outcome(reference, prediction)
    if outcome != "finite":
        reason = f"prediction_{outcome}"
        return (
            outcome,
            ["zero_convention" for _ in range(reference.shape[1])],
            [reason for _ in range(reference.shape[1])],
        )
    statuses = []
    reasons = []
    for idx in range(reference.shape[1]):
        y = reference[:, idx]
        yhat = prediction[:, idx]
        denom = float(np.sum((y - np.mean(y)) ** 2))
        if denom == 0.0:
            statuses.append("zero_convention")
            reasons.append("reference_no_variance")
        else:
            score = 1.0 - float(np.sum((y - yhat) ** 2)) / denom
            if math.isfinite(score):
                statuses.append("regular")
                reasons.append("")
            else:
                statuses.append("zero_convention")
                reasons.append("nonfinite_score")
    return outcome, statuses, reasons


def r2_diagnostic_fields(prefix: str, reference: np.ndarray, prediction: np.ndarray | None) -> dict[str, Any]:
    outcome, statuses, reasons = r2_dimension_diagnostics(reference, prediction)
    return {
        f"{prefix}_prediction_outcome": outcome,
        f"{prefix}_r2_dimension_status": json.dumps(statuses, separators=(",", ":")),
        f"{prefix}_r2_zero_reason": json.dumps(reasons, separators=(",", ":")),
    }


def empty_r2_diagnostic_fields(prefix: str, dimension: int, outcome: str = "none") -> dict[str, Any]:
    if outcome not in PREDICTION_OUTCOMES:
        outcome = "none"
    reason = f"prediction_{outcome}" if outcome != "finite" else ""
    status = "regular" if outcome == "finite" else "zero_convention"
    return {
        f"{prefix}_prediction_outcome": outcome,
        f"{prefix}_r2_dimension_status": json.dumps([status for _ in range(dimension)], separators=(",", ":")),
        f"{prefix}_r2_zero_reason": json.dumps([reason for _ in range(dimension)], separators=(",", ":")),
    }


def integration_error_fields(prefix: str, exc: BaseException | None = None) -> dict[str, str]:
    return {
        f"{prefix}_integration_error_type": type(exc).__name__ if exc is not None else "",
        f"{prefix}_integration_error_message": short_error_message(exc) if exc is not None else "",
    }


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
        head = (REPO_ROOT / ".git" / "HEAD").read_text(encoding="utf-8").strip()
        if head.startswith("ref: "):
            ref_path = REPO_ROOT / ".git" / head.removeprefix("ref: ").strip()
            return ref_path.read_text(encoding="utf-8").strip()
        return head
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
            **empty_r2_diagnostic_fields("reconstruction", record["dimension"]),
            **empty_r2_diagnostic_fields("generalization", record["dimension"]),
            **integration_error_fields("reconstruction", exc),
            **integration_error_fields("generalization", exc),
            **r2_threshold_flags("reconstruction", reconstruction_r2),
            **r2_threshold_flags("generalization", generalization_r2),
        }
    )
    return failed


def odeformer_schema_defaults(config: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "config_id",
        "environment_id",
        "beam_size",
        "beam_temperature",
        "beam_type",
        "beam_length_penalty",
        "beam_early_stopping",
        "max_input_points",
        "max_generated_output_len",
        "rescale",
        "sort_metric",
        "eval_subsample_ratio",
        "parameter_optimization",
        "parameter_optimization_iterations",
        "constant_optimization_enabled",
        "constant_optimization_init_random",
        "constant_optimization_objective",
        "constant_optimization_eval_objective",
        "constant_optimization_track_eval_history",
        "weight_sha256",
        "weights_path",
    ]
    defaults = {f"odeformer_{key}": config.get(key, "") for key in keys}
    defaults.update(odeformer_source_metadata())
    integration_timeout = config.get("integration_timeout_seconds", 1.0)
    if integration_timeout is None:
        integration_timeout = 1.0
    defaults["odeformer_integration_timeout_seconds"] = float(integration_timeout)
    defaults["odeformer_integration_timeout_count_total"] = 0
    defaults.update({f"odeformer_integration_timeout_count_{key}": 0 for key in empty_odeformer_timeout_counts()})
    for phase, counts in empty_odeformer_integration_outcome_counts().items():
        for outcome, value in counts.items():
            defaults[f"odeformer_integration_{phase}_{outcome}_count"] = value
    return defaults


def odeformer_failure(record: dict[str, Any], config: dict[str, Any], exc: Exception) -> dict[str, Any]:
    failed = record_failure(record, exc)
    failed.update(
        {
            "odeformer_model_raw": "",
            "odeformer_model_canonical": "",
            "odeformer_fitted_constants": "[]",
            "odeformer_candidates_evaluated": 0,
            "odeformer_expression_before_optimization": "",
            "odeformer_expression_after_optimization": "",
            "odeformer_constants_before_optimization": "[]",
            "odeformer_constants_after_optimization": "[]",
            "odeformer_optimization_status": "not_run",
            "odeformer_optimization_error_type": "",
            "odeformer_optimization_error_message": "",
            "odeformer_optimization_nit": 0,
            "odeformer_optimization_nfev": 0,
            "odeformer_optimization_stop_reason": "",
            "reconstruction_before_optimization_r2_arithmetic_mean": 0.0,
            "reconstruction_before_optimization_r2_variance_weighted": 0.0,
            "generalization_before_optimization_r2_arithmetic_mean": 0.0,
            "generalization_before_optimization_r2_variance_weighted": 0.0,
            "reconstruction_after_optimization_r2_arithmetic_mean": 0.0,
            "reconstruction_after_optimization_r2_variance_weighted": 0.0,
            "generalization_after_optimization_r2_arithmetic_mean": 0.0,
            "generalization_after_optimization_r2_variance_weighted": 0.0,
            "elapsed_s_non_evidence": 0.0,
            **odeformer_schema_defaults(config),
        }
    )
    return failed


@contextlib.contextmanager
def temporary_working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def canonicalize_odeformer_expression(expression: str) -> str:
    import sympy

    canonical_parts = []
    for part in expression.split("|"):
        text = part.strip()
        if not text:
            canonical_parts.append("")
            continue
        parsed = sympy.sympify(text.replace("^", "**"))
        canonical_parts.append(str(sympy.simplify(parsed)))
    return " | ".join(canonical_parts)


def numeric_constants(expression: str) -> list[float]:
    constants = []
    for match in re.finditer(r"(?<![_A-Za-z])[-+]?(?:(?:\d*\.\d+)|(?:\d+\.?))(?:[Ee][+-]?\d+)?", expression):
        constants.append(float(match.group(0)))
    return constants


class ODEFormerAdapter:
    def __init__(self, config: dict[str, Any]):
        import torch
        from odeformer.model import SymbolicTransformerRegressor

        self.config = dict(config)
        self.torch = torch
        self.integration_timeout_seconds = self._configured_integration_timeout_seconds()
        self._timeout_counts = self.empty_timeout_counts()
        self._integration_outcome_counts = empty_odeformer_integration_outcome_counts()
        self._timeout_phase = "unclassified"
        self._generators_module = None
        self._original_integrate_ode = None
        self._original_integrate_ode_wrapped = None
        seed = int(self.config.get("seed", 2023))
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        torch.set_num_threads(1)
        self.weights_path = resolve_path(self.config.get("weights_path", "odeformer.pt"))
        if not self.weights_path.is_file():
            raise FileNotFoundError(f"ODEFormer weights not found: {self.weights_path}")
        self.actual_hash = hashlib.sha256(self.weights_path.read_bytes()).hexdigest()
        expected_hash = str(self.config.get("weight_sha256", "")).strip()
        if expected_hash and not expected_hash.startswith("TO_BE_FILLED") and self.actual_hash != expected_hash:
            raise ValueError(f"ODEFormer weights hash mismatch: expected {expected_hash}, got {self.actual_hash}")
        os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
        with temporary_working_directory(self.weights_path.parent):
            self.model = SymbolicTransformerRegressor(
                from_pretrained=True,
                max_input_points=int(self.config["max_input_points"]),
                rescale=bool(self.config["rescale"]),
            )
        self._install_integration_timeout_patch()

    @staticmethod
    def empty_timeout_counts() -> dict[str, int]:
        return empty_odeformer_timeout_counts()

    def _configured_integration_timeout_seconds(self) -> float:
        value = self.config.get("integration_timeout_seconds", 1.0)
        if value is None:
            value = 1.0
        timeout_seconds = float(value)
        if timeout_seconds <= 0.0:
            raise ValueError("integration_timeout_seconds must be positive when set")
        return timeout_seconds

    def _install_integration_timeout_patch(self) -> None:
        from odeformer.envs import generators
        from odeformer.utils import MyTimeoutError

        current = generators._integrate_ode
        undecorated = getattr(current, "__wrapped__", current)
        self._generators_module = generators
        self._original_integrate_ode = current
        self._original_integrate_ode_wrapped = undecorated

        call_state = {"timeout_fired": False}

        def record_timeout() -> None:
            call_state["timeout_fired"] = True
            phase = self._timeout_phase if self._timeout_phase in self._timeout_counts else "unclassified"
            self._timeout_counts[phase] += 1

        def counted_integrate_ode(*args: Any, **kwargs: Any) -> Any:
            result = _NO_INTEGRATION_RESULT
            try:
                call_state["timeout_fired"] = False
                result = undecorated(*args, **kwargs)
                return result
            finally:
                self._record_integration_outcome(args, kwargs, result, bool(call_state["timeout_fired"]))

        generators._integrate_ode = odeformer_timeout_with_hook(
            self.integration_timeout_seconds,
            on_timeout=record_timeout,
            error_type=MyTimeoutError,
        )(counted_integrate_ode)

    def _record_integration_outcome(self, args: tuple[Any, ...], kwargs: dict[str, Any], result: Any, timeout_fired: bool) -> None:
        phase = self._timeout_phase if self._timeout_phase in self._integration_outcome_counts else "unclassified"
        counts = self._integration_outcome_counts[phase]
        counts["call"] += 1
        if result is _NO_INTEGRATION_RESULT:
            return
        outcome = self._integration_result_outcome(args, kwargs, result)
        counts[outcome] += 1
        if timeout_fired and outcome in {"none", "nan_sentinel"}:
            counts[f"{outcome}_after_timeout"] += 1

    @staticmethod
    def _integration_result_outcome(args: tuple[Any, ...], kwargs: dict[str, Any], result: Any) -> str:
        if result is None:
            return "none"
        try:
            array = np.asarray(result, dtype=float)
        except (TypeError, ValueError):
            return "trajectory"
        expected_len = kwargs.get("t_eval")
        if expected_len is None and len(args) >= 4:
            expected_len = args[3]
        try:
            expected_shape = (len(expected_len),)
        except TypeError:
            expected_shape = None
        if array.ndim == 1 and bool(np.all(np.isnan(array))) and (expected_shape is None or array.shape == expected_shape):
            return "nan_sentinel"
        return "trajectory"

    def close(self) -> None:
        if self._generators_module is not None and self._original_integrate_ode is not None:
            if getattr(self._generators_module._integrate_ode, "__wrapped__", None) is not self._original_integrate_ode_wrapped:
                self._generators_module._integrate_ode = self._original_integrate_ode
            else:
                self._generators_module._integrate_ode = self._original_integrate_ode
        self._generators_module = None
        self._original_integrate_ode = None
        self._original_integrate_ode_wrapped = None

    def __enter__(self) -> "ODEFormerAdapter":
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        with contextlib.suppress(Exception):
            self.close()

    @contextlib.contextmanager
    def timeout_phase(self, phase: str):
        previous = self._timeout_phase
        self._timeout_phase = phase
        try:
            yield
        finally:
            self._timeout_phase = previous

    def timeout_count_fields(self) -> dict[str, Any]:
        total = int(sum(self._timeout_counts.values()))
        fields = {
            "odeformer_integration_timeout_seconds": self.integration_timeout_seconds,
            "odeformer_integration_timeout_count_total": total,
            **{f"odeformer_integration_timeout_count_{key}": int(value) for key, value in self._timeout_counts.items()},
        }
        for phase, counts in self._integration_outcome_counts.items():
            for outcome, value in counts.items():
                fields[f"odeformer_integration_{phase}_{outcome}_count"] = int(value)
        return fields

    def set_generation_args(self) -> None:
        self.model.set_model_args(
            {
                "beam_size": int(self.config["beam_size"]),
                "beam_temperature": float(self.config["beam_temperature"]),
                "beam_type": str(self.config["beam_type"]),
                "beam_length_penalty": float(self.config["beam_length_penalty"]),
                "beam_early_stopping": bool(self.config["beam_early_stopping"]),
                "max_generated_output_len": int(self.config["max_generated_output_len"]),
            }
        )

    def fit_best_candidate(self, fit_cell: TrajectoryCell) -> tuple[Any, str, str, list[Any]]:
        self.set_generation_args()
        with self.timeout_phase("fit_candidate_ranking"):
            self.model.fit(
                fit_cell.time,
                fit_cell.state,
                sort_candidates=True,
                sort_metric=str(self.config["sort_metric"]),
                rescale=bool(self.config["rescale"]),
                verbose=False,
            )
        candidates = list(self.model.predictions.get(0, []))
        if not candidates or candidates[0] is None:
            raise RuntimeError("ODEFormer produced no candidate expression")
        best = candidates[0]
        model_raw = best.infix() if hasattr(best, "infix") else str(best)
        return best, model_raw, canonicalize_odeformer_expression(model_raw), candidates

    def integrate_expression(self, cell: TrajectoryCell, expression: Any) -> np.ndarray | None:
        prediction = self.model.integrate_prediction(cell.time, cell.state[0, :], prediction=expression)
        if prediction is None:
            return None
        return np.asarray(prediction, dtype=float)

    def optimize_constants(self, expression: str, fit_cell: TrajectoryCell) -> dict[str, Any]:
        """Optimize numeric constants, treating import failures as run-aborting infrastructure errors.

        ImportError anywhere in the ODEFormer constant-optimization import path means the image or
        local checkout is incomplete and must abort the run. Exceptions raised by the optimizer after
        its dependencies are importable remain scientific optimization failures and are recorded by
        the caller as before.
        """
        module = import_odeformer_param_optimizer()
        ConstantOptimizer = module.ConstantOptimizer

        optimizer = ConstantOptimizer(
            eq=expression,
            y0=fit_cell.state[0, :],
            time=fit_cell.time,
            observed_trajectory=fit_cell.state,
            init_random=bool(self.config.get("constant_optimization_init_random", False)),
            optimization_objective=str(self.config.get("constant_optimization_objective", "r2")),
            eval_objective=str(self.config.get("constant_optimization_eval_objective", "r2")),
            track_eval_history=bool(self.config.get("constant_optimization_track_eval_history", True)),
        )
        original_minimize = optimizer.optimize.__globals__["minimize"]
        holder: dict[str, Any] = {}

        def tracked_minimize(*args: Any, **kwargs: Any) -> Any:
            result = original_minimize(*args, **kwargs)
            holder["result"] = result
            return result

        optimizer.optimize.__globals__["minimize"] = tracked_minimize
        try:
            with self.timeout_phase("constant_optimization"):
                optimized_expression, optimized_params, optimized_fit = optimizer.optimize()
        except ImportError as exc:
            raise ODEFormerInfrastructureError(f"ODEFormer constant optimization import failed: {exc}") from exc
        finally:
            optimizer.optimize.__globals__["minimize"] = original_minimize
        info = holder.get("result")
        return {
            "expression": str(optimized_expression),
            "params": np.asarray(optimized_params, dtype=float).tolist(),
            "fit_prediction": None if optimized_fit is None else np.asarray(optimized_fit, dtype=float),
            "nit": int(getattr(info, "nit", 0) or 0),
            "nfev": int(getattr(info, "nfev", 0) or 0),
            "stop_reason": str(getattr(info, "message", "")),
        }


def build_odeformer_adapter(config: dict[str, Any]) -> ODEFormerAdapter:
    return ODEFormerAdapter(config)


def run_odeformer_record_with_adapter(
    _system: dict[str, Any],
    fit_cell: TrajectoryCell,
    target_cell: TrajectoryCell,
    config: dict[str, Any],
    adapter: ODEFormerAdapter,
) -> dict[str, Any]:
    record = base_record("odeformer", config, fit_cell, target_cell)
    record.update(odeformer_schema_defaults(config))
    start = time.perf_counter()
    try:
        best, model_raw, model_canonical, candidates = adapter.fit_best_candidate(fit_cell)
        reconstruction_error: BaseException | None = None
        generalization_error: BaseException | None = None
        try:
            with adapter.timeout_phase("reconstruction_before_optimization"):
                reconstruction_before = adapter.integrate_expression(fit_cell, best)
        except Exception as exc:
            reconstruction_before = None
            reconstruction_error = exc
        try:
            with adapter.timeout_phase("generalization_before_optimization"):
                generalization_before = adapter.integrate_expression(target_cell, best)
        except Exception as exc:
            generalization_before = None
            generalization_error = exc
        reconstruction_before_r2 = aggregate_r2(fit_cell.state, reconstruction_before)
        generalization_before_r2 = aggregate_r2(target_cell.state, generalization_before)
        expression_after = model_canonical
        optimization_status = "not_requested"
        optimization_error_type = ""
        optimization_error_message = ""
        optimization_nit = 0
        optimization_nfev = 0
        optimization_stop_reason = ""
        reconstruction_after_r2 = reconstruction_before_r2
        generalization_after_r2 = generalization_before_r2
        reconstruction_after = reconstruction_before
        generalization_after = generalization_before
        if bool(config.get("constant_optimization_enabled", False)):
            try:
                optimized = adapter.optimize_constants(model_canonical, fit_cell)
                expression_after = canonicalize_odeformer_expression(str(optimized["expression"]))
                reconstruction_after = optimized["fit_prediction"]
                reconstruction_after_r2 = aggregate_r2(fit_cell.state, reconstruction_after)
                try:
                    with adapter.timeout_phase("generalization_after_optimization"):
                        generalization_after = adapter.integrate_expression(target_cell, expression_after)
                    generalization_error = None
                except Exception as exc:
                    generalization_after = None
                    generalization_error = exc
                generalization_after_r2 = aggregate_r2(target_cell.state, generalization_after)
                optimization_status = "success"
                optimization_nit = int(optimized["nit"])
                optimization_nfev = int(optimized["nfev"])
                optimization_stop_reason = str(optimized["stop_reason"])
            except ODEFormerInfrastructureError:
                raise
            except ImportError as exc:
                raise ODEFormerInfrastructureError(f"ODEFormer constant optimization import failed: {exc}") from exc
            except Exception as exc:
                optimization_status = "error_unoptimized_expression_retained"
                optimization_error_type = type(exc).__name__
                optimization_error_message = str(exc)
        record.update(
            {
                "model": expression_after,
                "active_terms_raw": "[]",
                "active_terms_pruned": "[]",
                "true_terms": "[]",
                "structure_hit_raw": False,
                "structure_hit_pruned": False,
                "reconstruction_status": "success",
                "generalization_status": "success",
                "odeformer_model_raw": model_raw,
                "odeformer_model_canonical": expression_after,
                "odeformer_fitted_constants": json.dumps(numeric_constants(expression_after), separators=(",", ":")),
                "odeformer_weight_sha256": adapter.actual_hash,
                "odeformer_candidates_evaluated": len(candidates),
                "odeformer_parameter_optimization_iterations": optimization_nit,
                "odeformer_expression_before_optimization": model_canonical,
                "odeformer_expression_after_optimization": expression_after,
                "odeformer_constants_before_optimization": json.dumps(numeric_constants(model_canonical), separators=(",", ":")),
                "odeformer_constants_after_optimization": json.dumps(numeric_constants(expression_after), separators=(",", ":")),
                "odeformer_optimization_status": optimization_status,
                "odeformer_optimization_error_type": optimization_error_type,
                "odeformer_optimization_error_message": optimization_error_message,
                "odeformer_optimization_nit": optimization_nit,
                "odeformer_optimization_nfev": optimization_nfev,
                "odeformer_optimization_stop_reason": optimization_stop_reason,
                "elapsed_s_non_evidence": time.perf_counter() - start,
                **{f"reconstruction_before_optimization_{key}": value for key, value in reconstruction_before_r2.items()},
                **{f"generalization_before_optimization_{key}": value for key, value in generalization_before_r2.items()},
                **{f"reconstruction_after_optimization_{key}": value for key, value in reconstruction_after_r2.items()},
                **{f"generalization_after_optimization_{key}": value for key, value in generalization_after_r2.items()},
                **{f"reconstruction_{key}": value for key, value in reconstruction_after_r2.items()},
                **{f"generalization_{key}": value for key, value in generalization_after_r2.items()},
                **r2_diagnostic_fields("reconstruction", fit_cell.state, reconstruction_after),
                **r2_diagnostic_fields("generalization", target_cell.state, generalization_after),
                **integration_error_fields("reconstruction", reconstruction_error),
                **integration_error_fields("generalization", generalization_error),
                **r2_threshold_flags("reconstruction", reconstruction_after_r2),
                **r2_threshold_flags("generalization", generalization_after_r2),
                **adapter.timeout_count_fields(),
            }
        )
        return record
    except ODEFormerInfrastructureError:
        raise
    except Exception as exc:
        return odeformer_failure(record, config, exc)


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
        reconstruction_error = (
            RuntimeError(reconstruction_status)
            if reconstruction is None and reconstruction_status not in {"success", "fit_failed"}
            else None
        )
        generalization_error = (
            RuntimeError(generalization_status)
            if generalization is None and generalization_status not in {"success", "fit_failed"}
            else None
        )
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
                **r2_diagnostic_fields("reconstruction", fit_cell.state, reconstruction),
                **r2_diagnostic_fields("generalization", target_cell.state, generalization),
                **integration_error_fields("reconstruction", reconstruction_error),
                **integration_error_fields("generalization", generalization_error),
                **r2_threshold_flags("reconstruction", reconstruction_r2),
                **r2_threshold_flags("generalization", generalization_r2),
            }
        )
        return record
    except Exception as exc:
        return record_failure(record, exc)


def run_odeformer_record(_system: dict[str, Any], fit_cell: TrajectoryCell, target_cell: TrajectoryCell, config: dict[str, Any]) -> dict[str, Any]:
    try:
        adapter = build_odeformer_adapter(config)
    except Exception as exc:
        record = base_record("odeformer", config, fit_cell, target_cell)
        record.update(odeformer_schema_defaults(config))
        return odeformer_failure(record, config, RuntimeError(f"ODEFormer is not importable in this environment: {exc}"))
    try:
        return run_odeformer_record_with_adapter(_system, fit_cell, target_cell, config, adapter)
    finally:
        adapter.close()


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
