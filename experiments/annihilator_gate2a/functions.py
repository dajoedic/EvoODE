"""Numeric and symbolic test functions for Gate 2A."""

from __future__ import annotations

import numpy as np
import sympy as sp

from .config import FUNCTIONS, Domain, FunctionSpec


def numeric_values(function_key: str, x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    if function_key == "F1":
        return x**2
    if function_key == "F2":
        return np.exp(1.5 * x)
    if function_key == "F3":
        return x**1.5
    if function_key == "F4":
        return np.log(x)
    if function_key == "F5":
        return x * np.log(x)
    if function_key == "F6":
        return np.exp(-(x**2))
    if function_key == "F7":
        return np.sin(2.0 * x + 0.5)
    if function_key == "F8":
        return x / (2.0 + x)
    if function_key == "F9":
        return x**2 + np.exp(x)
    if function_key == "F10":
        return np.sin(x) + np.exp(-(x**2))
    raise KeyError(function_key)


def symbolic_x(function_key: str) -> tuple[sp.Symbol, sp.Expr]:
    x = sp.Symbol("x")
    table = {
        "F1": x**2,
        "F2": sp.exp(sp.Rational(3, 2) * x),
        "F3": x ** sp.Rational(3, 2),
        "F4": sp.log(x),
        "F5": x * sp.log(x),
        "F6": sp.exp(-(x**2)),
        "F7": sp.sin(2 * x + sp.Rational(1, 2)),
        "F8": x / (2 + x),
        "F9": x**2 + sp.exp(x),
        "F10": sp.sin(x) + sp.exp(-(x**2)),
    }
    return x, table[function_key]


def symbolic_z(function_key: str, domain: Domain) -> tuple[sp.Symbol, sp.Expr]:
    z = sp.Symbol("z")
    x, expr = symbolic_x(function_key)
    mu = sp.Rational(str(domain.mu))
    scale = sp.Rational(str(domain.scale))
    return z, expr.subs(x, mu + scale * z)


def grid(domain: Domain, n: int) -> tuple[np.ndarray, np.ndarray]:
    x = np.linspace(domain.a, domain.b, n)
    z = (x - domain.mu) / domain.scale
    return x, z


def noisy_sample(function_key: str, domain: Domain, n: int, eta: float, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    x, z = grid(domain, n)
    exact = numeric_values(function_key, x)
    if eta == 0:
        return x, z, exact.copy(), 0.0
    sigma = eta * float(np.sqrt(np.mean(exact**2)))
    rng = np.random.default_rng(seed)
    return x, z, exact + sigma * rng.standard_normal(n), sigma


def sigma_eff(values: np.ndarray, eta: float, floor_factor: float) -> float:
    rms = float(np.sqrt(np.mean(np.asarray(values, dtype=float) ** 2)))
    return float(np.sqrt((eta * rms) ** 2 + (floor_factor * rms) ** 2))

