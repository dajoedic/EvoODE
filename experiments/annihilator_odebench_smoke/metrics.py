"""Metrics for ODEBench smoke-test records."""

from __future__ import annotations

import math

import numpy as np
from scipy.integrate import solve_ivp

from .catalog import ODESystem


def rms(values: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.asarray(values, dtype=float) ** 2)))


def nrmse(pred: np.ndarray, truth: np.ndarray) -> float:
    pred = np.asarray(pred, dtype=float)
    truth = np.asarray(truth, dtype=float)
    denom = rms(truth)
    if denom == 0.0:
        return float("inf") if rms(pred - truth) > 0 else 0.0
    return float(rms(pred - truth) / denom)


def r2_score(pred: np.ndarray, truth: np.ndarray) -> float:
    pred = np.asarray(pred, dtype=float)
    truth = np.asarray(truth, dtype=float)
    denom = float(np.sum((truth - np.mean(truth)) ** 2))
    if denom == 0.0:
        return float("-inf")
    return float(1.0 - np.sum((pred - truth) ** 2) / denom)


def trajectory_metrics(system: ODESystem, fhat, x0: float, truth: np.ndarray) -> dict:
    try:
        def rhs(_t, y):
            value = np.asarray(fhat(float(y[0])), dtype=float).reshape(-1)[0]
            return [float(value)]

        sol = solve_ivp(rhs, (float(system.t[0]), float(system.t[-1])), [x0], t_eval=system.t, method="LSODA", rtol=1e-8, atol=1e-10)
        if not sol.success or not np.all(np.isfinite(sol.y[0])):
            raise RuntimeError("trajectory integration failed")
        pred = np.asarray(sol.y[0], dtype=float)
        return {"nrmse_x": nrmse(pred, truth), "r2": r2_score(pred, truth), "fail_reason": None}
    except Exception as exc:
        return {"nrmse_x": math.inf, "r2": -math.inf, "fail_reason": type(exc).__name__}
