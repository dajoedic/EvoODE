"""Frozen constants and cell definitions for Gate 2A v2."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
APPENDIX_A_JSON = RESULTS / "calibration" / "appendix_A.json"

R_MAX = 6
D_MAX = 6
PINV_REL_TOL = 1e-12
FNS_ANGLE_TOL = 1e-12
FNS_MAX_ITER = 100
A3_TRACE_THRESHOLD = 0.1
ORACLE_REL_TOL = 1e-60
ORACLE_DIGITS = 100
ORACLE_POINTS = 220
K_MATRIX_THRESHOLD = 1e-8
TAU_MAX = 1e-4


@dataclass(frozen=True)
class Domain:
    name: str
    a: float
    b: float

    @property
    def mu(self) -> float:
        return 0.5 * (self.a + self.b)

    @property
    def scale(self) -> float:
        return 0.5 * (self.b - self.a)


@dataclass(frozen=True)
class FunctionSpec:
    key: str
    expression: str
    wide: Domain
    narrow: Domain
    reference_class: tuple[int, int]
    reference_operator_x: str
    group: str = "F"


@dataclass(frozen=True)
class Settings:
    variant: str = "standard"
    n: int = 2000
    modes: int = 8
    q: int = 14
    ell_max: int | None = None
    alpha: float = 0.01
    sigma_floor_factor: float | None = None
    boot_reps: int = 50
    boot_threshold: float = 0.8
    a3_trace_threshold: float = A3_TRACE_THRESHOLD
    noise_levels: tuple[float, ...] = (0.0, 0.01, 0.05)
    noisy_seeds: tuple[int, ...] = tuple(range(20))
    clean_seeds: tuple[int, ...] = (0,)


FUNCTIONS: dict[str, FunctionSpec] = {
    "F1": FunctionSpec("F1", "x**2", Domain("wide", -2.0, 2.0), Domain("narrow", 1.0, 1.4), (1, 1), "xD - 2"),
    "F2": FunctionSpec("F2", "exp(1.5*x)", Domain("wide", -2.0, 2.0), Domain("narrow", 0.0, 0.4), (1, 0), "D - 3/2"),
    "F3": FunctionSpec("F3", "x**1.5", Domain("wide", 0.2, 4.0), Domain("narrow", 1.0, 1.38), (1, 1), "2xD - 3"),
    "F4": FunctionSpec("F4", "log(x)", Domain("wide", 0.2, 4.0), Domain("narrow", 1.0, 1.38), (2, 1), "xD^2 + D"),
    "F5": FunctionSpec("F5", "x*log(x)", Domain("wide", 0.2, 4.0), Domain("narrow", 1.0, 1.38), (3, 1), "xD^3 + D^2"),
    "F6": FunctionSpec("F6", "exp(-x**2)", Domain("wide", -2.5, 2.5), Domain("narrow", 0.5, 1.0), (1, 1), "D + 2x"),
    "F7": FunctionSpec("F7", "sin(2*x + 1/2)", Domain("wide", -3.0, 3.0), Domain("narrow", 0.0, 0.6), (2, 0), "D^2 + 4"),
    "F8": FunctionSpec("F8", "x/(2+x)", Domain("wide", 0.1, 6.0), Domain("narrow", 1.0, 1.59), (1, 2), "x(x+2)D - 2"),
    "F9": FunctionSpec("F9", "x**2 + exp(x)", Domain("wide", -2.0, 2.0), Domain("narrow", 0.0, 0.4), (4, 0), "D^4 - D^3"),
    "F10": FunctionSpec("F10", "sin(x) + exp(-x**2)", Domain("wide", -3.0, 3.0), Domain("narrow", 0.0, 0.6), (5, 1), "oracle"),
}

CALIBRATION_FUNCTIONS: dict[str, FunctionSpec] = {
    "K1": FunctionSpec("K1", "cosh(x)", Domain("wide", -2.0, 2.0), Domain("narrow", 0.5, 0.9), (2, 0), "D^2 - 1", "K"),
    "K2": FunctionSpec("K2", "x**3", Domain("wide", -2.0, 2.0), Domain("narrow", 0.8, 1.2), (1, 1), "xD - 3", "K"),
    "K3": FunctionSpec("K3", "airyai(x)", Domain("wide", -4.0, 2.0), Domain("narrow", -1.0, -0.4), (2, 1), "D^2 - x", "K"),
    "K4": FunctionSpec("K4", "besselj(0,x)", Domain("wide", 0.5, 8.0), Domain("narrow", 2.0, 2.75), (2, 1), "xD^2 + D + x", "K"),
    "K5": FunctionSpec("K5", "x + sin(x)", Domain("wide", -3.0, 3.0), Domain("narrow", 0.5, 1.1), (4, 0), "D^4 + D^2", "K"),
    "K6": FunctionSpec("K6", "x*exp(x) + exp(-x)", Domain("wide", -2.0, 2.0), Domain("narrow", -0.2, 0.2), (3, 0), "(D-1)^2(D+1)", "K"),
    "K7": FunctionSpec("K7", "1 + sin(x) + cos(2*x)", Domain("wide", -3.0, 3.0), Domain("narrow", 0.3, 0.9), (5, 0), "D(D^2+1)(D^2+4)", "K"),
    "K8": FunctionSpec("K8", "sin(x) + sin(2*x) + sin(3*x)", Domain("wide", -3.0, 3.0), Domain("narrow", 0.3, 0.9), (6, 0), "(D^2+1)(D^2+4)(D^2+9)", "K"),
}

ALL_FUNCTIONS = {**FUNCTIONS, **CALIBRATION_FUNCTIONS}

VARIANT_OVERRIDES = {
    "S1": {"n": 1000},
    "S2": {"n": 4000},
    "S3": {"modes": 6},
    "S4": {"modes": 12},
    "S5": {"q": 12},
    "S6": {"q": 16},
    "S7": {"ell_delta": -1},
    "S8": {"ell_delta": 1},
    "S9": {"alpha": 0.05},
    "S10": {"alpha": 0.001},
    "S11": {"tau_factor": 0.1},
    "S12": {"tau_factor": 10.0},
    "S13": {"boot_threshold": 0.7},
    "S14": {"boot_threshold": 0.9},
    "S15": {"a3_trace_threshold": 0.05},
    "S16": {"a3_trace_threshold": 0.2},
}


def class_order() -> list[tuple[int, int]]:
    return sorted(((r, d) for r in range(1, R_MAX + 1) for d in range(D_MAX + 1)), key=lambda rd: ((rd[0] + 1) * (rd[1] + 1), rd[0], rd[1]))


CLASSES = tuple(class_order())


def class_columns(r: int, d: int) -> list[tuple[int, int]]:
    return [(k, j) for k in range(r + 1) for j in range(d + 1)]


def appendix_parameters(required: bool = False) -> tuple[int | None, float | None]:
    if not APPENDIX_A_JSON.exists():
        if required:
            raise FileNotFoundError(f"appendix A not found: {APPENDIX_A_JSON}")
        return None, None
    data = json.loads(APPENDIX_A_JSON.read_text())
    return int(data["ell_max"]), float(data["tau"])


def settings_for_variant(variant: str, *, ell_max: int | None = None, tau: float | None = None, require_appendix: bool = False) -> Settings:
    appendix_ell, appendix_tau = appendix_parameters(required=require_appendix) if ell_max is None or tau is None else (None, None)
    base = Settings(ell_max=ell_max if ell_max is not None else appendix_ell, sigma_floor_factor=tau if tau is not None else appendix_tau)
    if variant == "standard":
        return base
    if variant not in VARIANT_OVERRIDES:
        raise ValueError(f"unknown variant {variant!r}")
    overrides = dict(VARIANT_OVERRIDES[variant])
    ell_delta = overrides.pop("ell_delta", 0)
    tau_factor = overrides.pop("tau_factor", 1.0)
    if base.ell_max is not None:
        overrides["ell_max"] = max(3, base.ell_max + ell_delta)
    if base.sigma_floor_factor is not None:
        overrides["sigma_floor_factor"] = base.sigma_floor_factor * tau_factor
    return replace(base, variant=variant, **overrides)


def domain_for(spec: FunctionSpec, name: str) -> Domain:
    if name == "wide":
        return spec.wide
    if name == "narrow":
        return spec.narrow
    raise ValueError(f"unknown domain {name!r}")


def calibration_reference_coeffs(function_key: str, domain_name: str) -> tuple[tuple[int, int], list[float]]:
    """Return the specified K-set reference operator in z-coordinates."""
    spec = CALIBRATION_FUNCTIONS[function_key]
    domain = domain_for(spec, domain_name)
    s = domain.scale
    mu = domain.mu
    if function_key == "K1":
        return (2, 0), [-s**2, 0.0, 1.0]
    if function_key == "K2":
        return (1, 1), [-3.0, 0.0, mu / s, 1.0]
    if function_key == "K3":
        return (2, 1), [-(s**2) * mu, -(s**3), 0.0, 0.0, 1.0, 0.0]
    if function_key == "K4":
        return (2, 1), [(s**2) * mu, s**3, s, 0.0, mu, s]
    if function_key == "K5":
        return (4, 0), [0.0, 0.0, s**2, 0.0, 1.0]
    if function_key == "K6":
        return (3, 0), [s**3, -(s**2), -s, 1.0]
    if function_key == "K7":
        return (5, 0), [0.0, 4.0 * s**4, 0.0, 5.0 * s**2, 0.0, 1.0]
    if function_key == "K8":
        return (6, 0), [36.0 * s**6, 0.0, 49.0 * s**4, 0.0, 14.0 * s**2, 0.0, 1.0]
    raise KeyError(function_key)
