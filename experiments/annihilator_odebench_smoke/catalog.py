"""ODEBench catalog parsing and setup generation."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp

from .config import CATALOG, N_TIME, SYSTEM_IDS, T0, T1, TRAINING_TRAJECTORIES


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
class ODESystem:
    system_id: int
    eq: str
    substituted: str
    constants: tuple[float, ...]
    init: tuple[float, ...]
    init_constraints: str
    t: np.ndarray
    x_train: tuple[np.ndarray, ...]
    sympy_expr: sp.Expr
    numeric_rhs: Callable[[np.ndarray | float], np.ndarray]


def _allowed_catalog_records(path: Path = CATALOG) -> dict[int, dict]:
    data = json.loads(path.read_text())
    found = {int(row["id"]): row for row in data if int(row["id"]) in SYSTEM_IDS}
    missing = set(SYSTEM_IDS) - set(found)
    if missing:
        raise KeyError(f"missing ODEBench systems: {sorted(missing)}")
    return {sid: found[sid] for sid in SYSTEM_IDS}


def _sympify_substituted(text: str) -> sp.Expr:
    x = sp.Symbol("x")
    expr = sp.sympify(text.replace("x_0", "x"), locals={"x": x, "log": sp.log, "exp": sp.exp, "sin": sp.sin, "cos": sp.cos})
    return sp.simplify(expr)


def _lambdify(expr: sp.Expr) -> Callable[[np.ndarray | float], np.ndarray]:
    x = sp.Symbol("x")
    func = sp.lambdify(x, expr, modules=["numpy"])

    def rhs(values: np.ndarray | float) -> np.ndarray:
        return np.asarray(func(values), dtype=float)

    return rhs


def load_systems(path: Path = CATALOG) -> dict[int, ODESystem]:
    systems: dict[int, ODESystem] = {}
    for sid, row in _allowed_catalog_records(path).items():
        if int(row["dim"]) != 1:
            raise ValueError(f"system {sid} is not scalar")
        solutions = row["solutions"][0][:TRAINING_TRAJECTORIES]
        t = np.asarray(solutions[0]["t"], dtype=float)
        if t.size != N_TIME or abs(float(t[0]) - T0) > 1e-12 or abs(float(t[-1]) - T1) > 1e-12:
            raise ValueError(f"system {sid} has unexpected stored time grid")
        x_train = tuple(np.asarray(sol["y"][0], dtype=float) for sol in solutions)
        expr = _sympify_substituted(row["substituted"][0][0])
        systems[sid] = ODESystem(
            system_id=sid,
            eq=str(row["eq"]),
            substituted=str(row["substituted"][0][0]),
            constants=tuple(float(v) for v in row["consts"][0]),
            init=tuple(float(v[0]) for v in row["init"][:TRAINING_TRAJECTORIES]),
            init_constraints=str(row["init_constraints"]),
            t=t,
            x_train=x_train,
            sympy_expr=expr,
            numeric_rhs=_lambdify(expr),
        )
    return systems


def check_init_constraint(system: ODESystem, value: float) -> bool:
    text = system.init_constraints.strip()
    match = re.fullmatch(r"x_0\s*(>=|>|<=|<)\s*([-+0-9.eE]+)", text)
    if match is None:
        raise ValueError(f"unsupported init constraint for system {system.system_id}: {text!r}")
    op, rhs_text = match.groups()
    rhs = float(rhs_text)
    return {
        ">": value > rhs,
        ">=": value >= rhs,
        "<": value < rhs,
        "<=": value <= rhs,
    }[op]


def training_domain(system: ODESystem) -> Domain:
    values = np.concatenate(system.x_train)
    return Domain("training", float(np.min(values)), float(np.max(values)))


def derive_test_initial_conditions(system: ODESystem, domain: Domain) -> dict[str, float | str]:
    x_min, x_max = domain.a, domain.b
    width = x_max - x_min
    x_mid = 0.5 * (x_min + x_max)
    x_hi = x_max + 0.25 * width
    x_lo_raw = x_min - 0.25 * width
    if check_init_constraint(system, x_lo_raw):
        x_lo = x_lo_raw
        rule = "xmin_minus_R_over_4"
    elif x_min > 0:
        x_lo = 0.5 * x_min
        rule = "xmin_over_2"
    else:
        x_lo = x_max + 0.5 * width
        rule = "xmax_plus_R_over_2"
    for value in (x_mid, x_hi, x_lo):
        if not check_init_constraint(system, float(value)):
            raise ValueError(f"derived test initial condition violates constraints for system {system.system_id}: {value}")
    return {"mid": float(x_mid), "hi": float(x_hi), "lo": float(x_lo), "lo_rule": rule}


def integrate_trajectory(system: ODESystem, x0: float, *, rtol: float = 1e-10, atol: float = 1e-12) -> np.ndarray:
    sol = solve_ivp(
        lambda _t, y: [float(system.numeric_rhs(float(y[0])))],
        (T0, T1),
        [float(x0)],
        t_eval=system.t,
        method="LSODA",
        rtol=rtol,
        atol=atol,
    )
    if not sol.success:
        raise RuntimeError(f"integration failed for system {system.system_id}: {sol.message}")
    return np.asarray(sol.y[0], dtype=float)


def build_setup() -> dict:
    systems = load_systems()
    out = {"systems": {}}
    for sid, system in systems.items():
        domain = training_domain(system)
        test_ics = derive_test_initial_conditions(system, domain)
        tests = {name: integrate_trajectory(system, float(value)).tolist() for name, value in test_ics.items() if name != "lo_rule"}
        out["systems"][str(sid)] = {
            "substituted": system.substituted,
            "init_constraints": system.init_constraints,
            "training_initial_conditions": list(system.init),
            "training_domain": {"xmin": domain.a, "xmax": domain.b, "R": domain.b - domain.a, "mu": domain.mu, "scale": domain.scale},
            "test_initial_conditions": test_ics,
            "test_trajectories": tests,
        }
    return out
