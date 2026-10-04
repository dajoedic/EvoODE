"""Frozen constants for Gate 2A."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

R_MAX = 6
D_MAX = 6
PINV_REL_TOL = 1e-12
ORACLE_REL_TOL = 1e-35
ORACLE_DIGITS = 60
ORACLE_POINTS = 120
F10_REL_TOL = 1e-25


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


@dataclass(frozen=True)
class Settings:
    variant: str = "standard"
    n: int = 2000
    blocks: int = 8
    modes: int = 16
    q: int = 8
    alpha: float = 0.01
    sigma_floor_factor: float = 1e-8
    boot_reps: int = 50
    boot_threshold: float = 0.8
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


VARIANT_OVERRIDES = {
    "S1": {"n": 1000},
    "S2": {"n": 4000},
    "S3": {"blocks": 12},
    "S4": {"modes": 24},
    "S5": {"q": 10},
    "S6": {"alpha": 0.05},
    "S7": {"alpha": 0.001},
    "S8": {"sigma_floor_factor": 1e-10},
    "S9": {"sigma_floor_factor": 1e-6},
    "S10": {"boot_threshold": 0.7},
    "S11": {"boot_threshold": 0.9},
}


def class_order() -> list[tuple[int, int]]:
    return sorted(((r, d) for r in range(1, R_MAX + 1) for d in range(D_MAX + 1)), key=lambda rd: ((rd[0] + 1) * (rd[1] + 1), rd[0], rd[1]))


CLASSES = tuple(class_order())


def class_columns(r: int, d: int) -> list[tuple[int, int]]:
    return [(k, j) for k in range(r + 1) for j in range(d + 1)]


def settings_for_variant(variant: str) -> Settings:
    if variant == "standard":
        return Settings()
    if variant not in VARIANT_OVERRIDES:
        raise ValueError(f"unknown variant {variant!r}")
    return replace(Settings(variant=variant), **VARIANT_OVERRIDES[variant])


def domain_for(spec: FunctionSpec, name: str) -> Domain:
    if name == "wide":
        return spec.wide
    if name == "narrow":
        return spec.narrow
    raise ValueError(f"unknown domain {name!r}")
