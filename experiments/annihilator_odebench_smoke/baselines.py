"""SINDy and W-SINDy baseline helpers."""

from __future__ import annotations

import numpy as np
import pysindy as ps

from .config import SINDY_LIBRARY_TERMS, SINDY_THRESHOLDS


PYSINDY_PARAMETERS = {
    "version_requirement": "pysindy 2.1",
    "optimizer": "STLSQ",
    "threshold_grid": list(SINDY_THRESHOLDS),
    "normalize_columns": True,
    "sindy_derivative": "SmoothedFiniteDifference(defaults)",
    "wsindy_library": "WeakPDELibrary(defaults, K=200, spatiotemporal_grid=t)",
    "model_selection": "minimum AICc on regression residual",
}

TERM_FUNCTIONS = {
    "1": lambda x: np.ones_like(x),
    "x": lambda x: x,
    "x^2": lambda x: x**2,
    "x^3": lambda x: x**3,
    "log(x)": lambda x: np.log(x),
    "x log(x)": lambda x: x * np.log(x),
    "exp(-x)": lambda x: np.exp(-x),
    "sin(x)": lambda x: np.sin(x),
    "cos(x)": lambda x: np.cos(x),
}


class CaptureSTLSQ(ps.STLSQ):
    """STLSQ variant that keeps the regression target used by PySINDy."""

    def fit(self, x, y, sample_weight=None):
        self.regression_target_ = np.asarray(y, dtype=float).copy()
        return super().fit(x, y, sample_weight=sample_weight)


def library_matrix(x: np.ndarray, allowed_terms: tuple[str, ...] | None = None) -> tuple[np.ndarray, list[str]]:
    x = np.asarray(x, dtype=float)
    candidates = allowed_terms or SINDY_LIBRARY_TERMS
    cols = []
    names = []
    with np.errstate(all="ignore"):
        values = {
            "1": np.ones_like(x),
            "x": x,
            "x^2": x**2,
            "x^3": x**3,
            "log(x)": np.log(x),
            "x log(x)": x * np.log(x),
            "exp(-x)": np.exp(-x),
            "sin(x)": np.sin(x),
            "cos(x)": np.cos(x),
        }
    for name in candidates:
        col = np.asarray(values[name], dtype=float)
        if np.all(np.isfinite(col)):
            cols.append(col)
            names.append(name)
    return np.vstack(cols).T, names


def aicc(rss: float, n: int, k: int) -> float:
    if n <= k + 1:
        return float("inf")
    rss = max(float(rss), np.finfo(float).tiny)
    return float(n * np.log(rss / n) + 2 * k + (2 * k * (k + 1)) / (n - k - 1))


def allowed_library_terms(x_values: np.ndarray) -> tuple[str, ...]:
    _, names = library_matrix(np.asarray(x_values, dtype=float))
    return tuple(names)


def make_custom_library(terms: tuple[str, ...]) -> ps.CustomLibrary:
    functions = [TERM_FUNCTIONS[name] for name in terms]
    names = [(lambda _x, name=name: name) for name in terms]
    return ps.CustomLibrary(functions, names, include_bias=False)


def _jsonable(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    try:
        return repr(value)
    except Exception:
        return f"<{type(value).__module__}.{type(value).__name__}>"


def object_parameters(obj) -> dict:
    try:
        params = obj.get_params(deep=False)
    except Exception:
        params = getattr(obj, "__dict__", {})
    return {str(k): _jsonable(v) for k, v in params.items() if not str(k).endswith("_")}


def fit_pysindy_baseline(noisy_trajectories: list[np.ndarray], t: np.ndarray, method: str):
    x_list = [np.asarray(values, dtype=float).reshape(-1, 1) for values in noisy_trajectories]
    terms = allowed_library_terms(np.concatenate(noisy_trajectories))
    best = None
    for threshold in SINDY_THRESHOLDS:
        function_library = make_custom_library(terms)
        optimizer = CaptureSTLSQ(threshold=float(threshold), normalize_columns=True)
        if method == "sindy":
            differentiation = ps.SmoothedFiniteDifference()
            feature_library = function_library
            model = ps.SINDy(
                optimizer=optimizer,
                feature_library=feature_library,
                differentiation_method=differentiation,
            )
        elif method == "wsindy":
            differentiation = ps.FiniteDifference()
            feature_library = ps.WeakPDELibrary(
                function_library=function_library,
                spatiotemporal_grid=np.asarray(t, dtype=float),
                K=200,
            )
            model = ps.SINDy(
                optimizer=optimizer,
                feature_library=feature_library,
                differentiation_method=differentiation,
            )
        else:
            raise ValueError(f"unknown baseline method: {method}")
        model.fit(x_list, t=np.asarray(t, dtype=float), feature_names=["x"])
        coef = np.asarray(model.coefficients()[0], dtype=float)
        active = np.abs(coef) > 0.0
        theta = np.asarray(model.optimizer.Theta_, dtype=float)
        target = np.asarray(model.optimizer.regression_target_, dtype=float)
        residual = target - theta @ coef.reshape(-1, 1)
        rss = float(np.sum(residual**2))
        score = aicc(rss, target.shape[0], int(np.sum(active)))
        if best is None or score < best["aicc"]:
            best = {
                "model": model,
                "coefficients": coef,
                "active": active,
                "terms": tuple(model.get_feature_names()),
                "threshold": float(threshold),
                "aicc": score,
                "rss": rss,
                "n_regression_rows": int(target.shape[0]),
                "residual_source": "PySINDy optimizer regression target captured during fit",
                "parameters": {
                    "pysindy_version": ps.__version__,
                    "library_terms": list(terms),
                    "threshold_grid": list(SINDY_THRESHOLDS),
                    "model": object_parameters(model),
                    "optimizer": object_parameters(optimizer),
                    "differentiation_method": object_parameters(model.differentiation_method),
                    "feature_library": object_parameters(feature_library),
                    "function_library": object_parameters(function_library),
                },
            }
    assert best is not None
    return best
