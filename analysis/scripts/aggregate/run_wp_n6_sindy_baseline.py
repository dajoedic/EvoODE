import argparse
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sympy as sp
from scipy.integrate import solve_ivp

try:
    import pysindy as ps
except ImportError as exc:  # pragma: no cover - exercised only in broken environments
    raise SystemExit("pysindy is required for WP-N6") from exc


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
R2_THRESHOLD = 0.9
SUPPORT_ABS = 1e-6
SUPPORT_REL = 1e-3
INTEGRATION_LIMIT = 1e9


@dataclass(frozen=True)
class LibraryConfig:
    library_id: str
    polynomial_degree: int
    include_trig: bool
    threshold: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run WP-N6 SINDy baseline on Phase-B data.")
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if not isinstance(config, dict):
        fail("config root must be a JSON object")
    return config


def resolve_path(path_value: str, config_path: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path.resolve()
    candidates = [Path.cwd() / path, ANALYSIS_ROOT / path, REPO_ROOT / path, config_path.parent / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (ANALYSIS_ROOT / path).resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def load_benchmark(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        fail(f"benchmark_path does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        rows = json.load(handle)
    if not isinstance(rows, list) or len(rows) != 63:
        fail(f"benchmark_path must contain 63 systems, got {len(rows) if isinstance(rows, list) else 'non-list'}")
    return sorted(rows, key=lambda row: int(row["id"]))


def sympy_context(dim: int) -> dict[str, Any]:
    context: dict[str, Any] = {
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "cot": sp.cot,
        "exp": sp.exp,
        "log": sp.log,
        "sqrt": sp.sqrt,
        "Abs": sp.Abs,
        "abs": sp.Abs,
        "t": sp.Symbol("t"),
    }
    for idx in range(dim):
        context[f"x_{idx}"] = sp.Symbol(f"x_{idx}")
    return context


def parse_expr(text: str, dim: int) -> sp.Expr:
    return sp.sympify(text.replace("^", "**"), locals=sympy_context(dim))


def rhs_function(exprs: list[sp.Expr], dim: int):
    variables = [sp.Symbol(f"x_{idx}") for idx in range(dim)]
    t_symbol = sp.Symbol("t")
    funcs = [sp.lambdify([t_symbol, *variables], expr, modules=["numpy", "math"]) for expr in exprs]

    def rhs(t: float, x: np.ndarray) -> np.ndarray:
        values = [func(t, *x) for func in funcs]
        return np.asarray(values, dtype=float)

    return rhs


def integrate_truth(system: dict[str, Any], ic_index: int, t_grid: np.ndarray) -> tuple[np.ndarray, str]:
    dim = int(system["dim"])
    exprs = [parse_expr(str(expr), dim) for expr in system["substituted"][0]]
    y0 = np.asarray(system["init"][ic_index], dtype=float)
    sol = solve_ivp(
        rhs_function(exprs, dim),
        (float(t_grid[0]), float(t_grid[-1])),
        y0,
        t_eval=t_grid,
        rtol=1e-9,
        atol=1e-9,
        method="DOP853",
    )
    if not sol.success or sol.y.shape[1] != len(t_grid):
        return np.full((len(t_grid), dim), np.nan), sol.message
    return sol.y.T, "success"


def shipped_trajectory(system: dict[str, Any], ic_index: int) -> tuple[np.ndarray, np.ndarray]:
    solution = system["solutions"][0][ic_index]
    t = np.asarray(solution["t"], dtype=float)
    y = np.asarray(solution["y"], dtype=float).T
    return t, y


def validate_phase_b_inputs(benchmark: list[dict[str, Any]], config: dict[str, Any]) -> pd.DataFrame:
    expected_points = int(config.get("time_points", 512))
    expected_start = float(config.get("t_start", 0.0))
    expected_end = float(config.get("t_end", 10.0))
    rows: list[dict[str, Any]] = []
    for system in benchmark:
        system_id = int(system["id"])
        dim = int(system["dim"])
        if len(system.get("init", [])) < 2:
            fail(f"system {system_id} has fewer than two initial conditions")
        for ic_index in (0, 1):
            shipped_t, shipped_y = shipped_trajectory(system, ic_index)
            t_grid = np.linspace(expected_start, expected_end, expected_points)
            self_y, message = integrate_truth(system, ic_index, t_grid)
            if shipped_t.shape != t_grid.shape:
                fail(f"system {system_id} IC{ic_index + 1} shipped grid has wrong length")
            rows.append(
                {
                    "system_id": system_id,
                    "initial_condition_set": ic_index + 1,
                    "dimension": dim,
                    "grid_points": int(len(t_grid)),
                    "t_start": float(t_grid[0]),
                    "t_end": float(t_grid[-1]),
                    "grid_matches_phase_b": bool(np.allclose(shipped_t, t_grid, rtol=0.0, atol=1e-14)),
                    "self_integration_status": message,
                    "self_vs_shipped_max_abs": float(np.nanmax(np.abs(self_y - shipped_y))),
                    "self_vs_shipped_mse": float(np.nanmean((self_y - shipped_y) ** 2)),
                }
            )
    return pd.DataFrame(rows)


def build_library(config: LibraryConfig):
    poly = ps.PolynomialLibrary(degree=config.polynomial_degree, include_bias=True)
    if not config.include_trig:
        return poly
    trig = ps.FourierLibrary(n_frequencies=1, include_sin=True, include_cos=True)
    return ps.ConcatLibrary([poly, trig])


def library_grid(config: dict[str, Any]) -> list[LibraryConfig]:
    degrees = [int(value) for value in config.get("polynomial_degrees", [2, 3, 4, 5])]
    thresholds = [float(value) for value in config.get("thresholds", [0.01, 0.1])]
    rows = [
        LibraryConfig(f"poly_deg{degree}_stlsq_{threshold:g}", degree, False, threshold)
        for degree in degrees
        for threshold in thresholds
    ]
    trig_degree = int(config.get("trig_polynomial_degree", 3))
    rows.extend(
        LibraryConfig(f"poly_deg{trig_degree}_sin_cos_stlsq_{threshold:g}", trig_degree, True, threshold)
        for threshold in thresholds
    )
    return rows


def normalize_feature_name(name: str) -> str:
    return name.replace(" ", "*")


def term_name_from_monomial(monom: tuple[int, ...]) -> str:
    pieces = []
    for idx, power in enumerate(monom):
        if power == 1:
            pieces.append(f"x{idx}")
        elif power > 1:
            pieces.append(f"x{idx}^{power}")
    return "*".join(pieces) if pieces else "1"


def polynomial_true_terms(system: dict[str, Any]) -> list[set[str]]:
    dim = int(system["dim"])
    variables = [sp.Symbol(f"x_{idx}") for idx in range(dim)]
    true_terms: list[set[str]] = []
    for expr_text in system["substituted"][0]:
        expr = sp.expand(parse_expr(str(expr_text), dim))
        try:
            poly = sp.Poly(expr, *variables)
        except sp.PolynomialError:
            true_terms.append(set())
            continue
        eq_terms = set()
        for monom, coeff in poly.terms():
            if coeff != 0:
                eq_terms.add(term_name_from_monomial(tuple(int(v) for v in monom)))
        true_terms.append(eq_terms)
    return true_terms


def active_terms_by_equation(coef: np.ndarray, feature_names: list[str]) -> list[set[str]]:
    active: list[set[str]] = []
    for row in coef:
        max_abs = float(np.max(np.abs(row))) if row.size else 0.0
        threshold = max(SUPPORT_ABS, SUPPORT_REL * max_abs)
        terms = {
            normalize_feature_name(feature)
            for feature, value in zip(feature_names, row)
            if abs(float(value)) > threshold
        }
        active.append(terms)
    return active


def support_hit(predicted: list[set[str]], truth: list[set[str]]) -> bool:
    return len(predicted) == len(truth) and all(lhs == rhs for lhs, rhs in zip(predicted, truth))


def r2_score(reference: np.ndarray, prediction: np.ndarray) -> float:
    if reference.shape != prediction.shape or not np.all(np.isfinite(prediction)):
        return float("nan")
    scores = []
    for idx in range(reference.shape[1]):
        y = reference[:, idx]
        yhat = prediction[:, idx]
        denom = float(np.sum((y - np.mean(y)) ** 2))
        if denom == 0.0:
            return float("nan")
        scores.append(1.0 - float(np.sum((y - yhat) ** 2)) / denom)
    return float(np.mean(scores))


def feature_value(name: str, y: np.ndarray) -> float:
    if name == "1":
        return 1.0
    if name.startswith("sin(1 x") and name.endswith(")"):
        idx = int(name[len("sin(1 x") : -1])
        return float(np.sin(y[idx]))
    if name.startswith("cos(1 x") and name.endswith(")"):
        idx = int(name[len("cos(1 x") : -1])
        return float(np.cos(y[idx]))
    value = 1.0
    for piece in name.split(" "):
        if not piece:
            continue
        if "^" in piece:
            var, power_text = piece.split("^", 1)
            power = int(power_text)
        else:
            var, power = piece, 1
        if not var.startswith("x"):
            raise ValueError(f"unsupported feature name: {name}")
        value *= float(y[int(var[1:])]) ** power
    return value


def simulate_model(
    coefficients: np.ndarray,
    raw_feature_names: list[str],
    y0: np.ndarray,
    t_grid: np.ndarray,
) -> tuple[np.ndarray | None, str]:
    def rhs(_t: float, y: np.ndarray) -> np.ndarray:
        if not np.all(np.isfinite(y)) or float(np.max(np.abs(y))) > INTEGRATION_LIMIT:
            raise FloatingPointError("diverged")
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            features = np.asarray([feature_value(name, y) for name in raw_feature_names], dtype=float)
            values = features @ coefficients.T
        if not np.all(np.isfinite(values)):
            raise FloatingPointError("nonfinite_rhs")
        return values

    prediction = np.empty((len(t_grid), len(y0)), dtype=float)
    prediction[0, :] = np.asarray(y0, dtype=float)
    try:
        for idx in range(len(t_grid) - 1):
            t0 = float(t_grid[idx])
            dt = float(t_grid[idx + 1] - t_grid[idx])
            y = prediction[idx, :]
            k1 = rhs(t0, y)
            prediction[idx + 1, :] = y + dt * k1
            if not np.all(np.isfinite(prediction[idx + 1, :])):
                return prediction, "nonfinite"
            if float(np.max(np.abs(prediction[idx + 1, :]))) > INTEGRATION_LIMIT:
                return prediction, "diverged"
    except FloatingPointError as exc:
        if str(exc) == "diverged":
            return prediction, "diverged"
        return prediction, "nonfinite"
    except Exception as exc:  # PySINDy raises several exception types for invalid predictions.
        return None, type(exc).__name__
    if prediction.shape != (len(t_grid), len(y0)):
        return None, "shape_mismatch"
    if not np.all(np.isfinite(prediction)):
        return prediction, "nonfinite"
    if float(np.max(np.abs(prediction))) > INTEGRATION_LIMIT:
        return prediction, "diverged"
    return prediction, "success"


def fit_sindy(train_x: np.ndarray, t_grid: np.ndarray, names: list[str], cfg: LibraryConfig):
    model = ps.SINDy(
        optimizer=ps.STLSQ(threshold=cfg.threshold, alpha=1e-6, normalize_columns=False),
        feature_library=build_library(cfg),
        differentiation_method=ps.FiniteDifference(order=2),
    )
    model.fit(train_x, t=t_grid, feature_names=names)
    return model


def run_measurement(
    benchmark: list[dict[str, Any]],
    adequacy: pd.DataFrame,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    t_grid = np.linspace(float(config.get("t_start", 0.0)), float(config.get("t_end", 10.0)), int(config.get("time_points", 512)))
    trajectories = {
        (int(system["id"]), ic + 1): integrate_truth(system, ic, t_grid)[0]
        for system in benchmark
        for ic in (0, 1)
    }
    system_by_id = {int(system["id"]): system for system in benchmark}
    adequacy_by_id = adequacy.set_index("system_id")
    detail_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    start = time.perf_counter()

    for cfg in library_grid(config):
        for system_id, system in system_by_id.items():
            dim = int(system["dim"])
            names = [f"x{idx}" for idx in range(dim)]
            true_terms = polynomial_true_terms(system)
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
                active_terms: list[set[str]] = [set() for _ in range(dim)]
                if model is not None:
                    feature_names = [normalize_feature_name(name) for name in model.get_feature_names()]
                    active_terms = active_terms_by_equation(model.coefficients(), feature_names)

                for regime, eval_ic in [("reconstruction", source_ic), ("generalization", target_ic)]:
                    reference = trajectories[(system_id, eval_ic)]
                    prediction, sim_status = (None, "fit_failed")
                    if model is not None:
                        prediction, sim_status = simulate_model(
                            model.coefficients(),
                            model.get_feature_names(),
                            reference[0, :],
                            t_grid,
                        )
                    score = float("nan") if prediction is None else r2_score(reference, prediction)
                    detail_rows.append(
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
                            "direction": direction,
                            "regime": regime,
                            "fit_status": fit_status,
                            "integration_status": sim_status,
                            "diverged_or_nonfinite": sim_status not in {"success"},
                            "r2": score,
                            "r2_gt_0_9": bool(math.isfinite(score) and score > R2_THRESHOLD),
                            "evoode_staged_representable": adequacy_by_id.loc[system_id, "evoode_staged"] == "Y",
                            "sindy_poly_representable": adequacy_by_id.loc[system_id, "sindy_poly"] == "Y",
                            "structure_hit": support_hit(active_terms, true_terms),
                            "active_terms": json.dumps([sorted(terms) for terms in active_terms], separators=(",", ":")),
                            "true_terms": json.dumps([sorted(terms) for terms in true_terms], separators=(",", ":")),
                            "n_library_terms": len(feature_names),
                            "fit_elapsed_s_non_evidence": elapsed,
                        }
                    )

            cost_rows.append(
                {
                    "library_id": cfg.library_id,
                    "polynomial_degree": cfg.polynomial_degree,
                    "include_sin_cos": cfg.include_trig,
                    "stlsq_threshold": cfg.threshold,
                    "dimension": dim,
                    "n_library_terms": len(feature_names),
                    "fit_cells": 2,
                    "target_regressions": 2 * dim,
                }
            )

    details = pd.DataFrame(detail_rows)
    costs = pd.DataFrame(cost_rows)
    costs = (
        costs.groupby(["library_id", "polynomial_degree", "include_sin_cos", "stlsq_threshold", "dimension", "n_library_terms"], as_index=False)
        .agg(fit_cells=("fit_cells", "sum"), target_regressions=("target_regressions", "sum"))
    )
    costs["elapsed_s_non_evidence_total"] = time.perf_counter() - start
    return details, summarize(details), costs


def summarize(details: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    groups = details.groupby(
        ["library_id", "polynomial_degree", "include_sin_cos", "stlsq_threshold", "direction", "regime"],
        dropna=False,
    )
    for keys, group in groups:
        base = dict(zip(["library_id", "polynomial_degree", "include_sin_cos", "stlsq_threshold", "direction", "regime"], keys))
        for subset_name, subset in [
            ("all_63", group),
            ("evoode_staged_20", group[group["evoode_staged_representable"]]),
            ("sindy_poly_40", group[group["sindy_poly_representable"]]),
        ]:
            valid_r2 = group if subset_name == "all_63" else subset
            n_cells = int(len(valid_r2))
            rows.append(
                {
                    **base,
                    "subset": subset_name,
                    "n_cells": n_cells,
                    "structure_hit_count": int(valid_r2["structure_hit"].sum()),
                    "structure_hit_rate": float(valid_r2["structure_hit"].mean()) if n_cells else float("nan"),
                    "diverged_or_nonfinite_count": int(valid_r2["diverged_or_nonfinite"].sum()),
                    "r2_valid_count": int(valid_r2["r2"].apply(math.isfinite).sum()),
                    "r2_gt_0_9_count": int(valid_r2["r2_gt_0_9"].sum()),
                    "r2_gt_0_9_rate_over_cells": float(valid_r2["r2_gt_0_9"].sum() / n_cells) if n_cells else float("nan"),
                    "r2_median_valid": float(valid_r2.loc[valid_r2["r2"].apply(math.isfinite), "r2"].median()) if int(valid_r2["r2"].apply(math.isfinite).sum()) else float("nan"),
                }
            )
    return pd.DataFrame(rows)


def write_outputs(config: dict[str, Any], config_path: Path, frames: dict[str, pd.DataFrame]) -> dict[str, Path]:
    output_data_dir = resolve_path(config.get("output_data_dir", "data/wp_n6_sindy_baseline"), config_path)
    output_table_dir = resolve_path(config.get("output_table_dir", "tables/wp_n6_sindy_baseline"), config_path)
    output_data_dir.mkdir(parents=True, exist_ok=True)
    output_table_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, frame in frames.items():
        target = output_data_dir / f"{name}.csv"
        frame.to_csv(target, index=False)
        paths[name] = target
    for name in ["summary", "costs", "trajectory_check"]:
        csv_target = output_table_dir / f"wp_n6_{name}.csv"
        tex_target = output_table_dir / f"wp_n6_{name}.tex"
        frames[name].to_csv(csv_target, index=False)
        frames[name].to_latex(tex_target, index=False, escape=True)
        paths[f"table_{name}_csv"] = csv_target
        paths[f"table_{name}_tex"] = tex_target
    return paths


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    benchmark = load_benchmark(resolve_path(config.get("benchmark_path", "../benchmarks/data/strogatz_extended.json"), config_path))
    adequacy = pd.read_csv(resolve_path(config.get("representational_adequacy_path", "data/paper1_phaseB_v1/representational_adequacy.csv"), config_path))
    trajectory_check = validate_phase_b_inputs(benchmark, config)
    details, summary, costs = run_measurement(benchmark, adequacy, config)
    paths = write_outputs(
        config,
        config_path,
        {
            "trajectory_check": trajectory_check,
            "details": details,
            "summary": summary,
            "costs": costs,
        },
    )
    print(json.dumps({key: str(value) for key, value in paths.items()}, indent=2))


if __name__ == "__main__":
    main()
