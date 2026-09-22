from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from exploratory.term_relevance import term_relevance as tr  # noqa: E402
from scripts.aggregate.run_phasec_sindy_baseline import load_phase_c_support  # noqa: E402
from scripts.aggregate.run_wp_n6_sindy_baseline import (  # noqa: E402
    R2_THRESHOLD,
    SUPPORT_ABS,
    SUPPORT_REL,
    active_terms_by_equation,
    r2_score,
    simulate_model,
    support_hit,
)


STUDY_ID = "wp_t1b_standalone_ranking"
SIGNALS = ("weak", "fd")
SIGMA_REPLICATES = {0.0: [0], 0.01: [1, 2, 3, 4, 5], 0.05: [1, 2, 3, 4, 5]}
BIC_FORMULA = "n * log(SSE / n) + k * log(n), with n equal to design rows"
MAX_PROJECTED_INTEGRATIONS = 40_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run WP-T1b standalone ranking discovery.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--limit-systems", default="", help="Comma-separated system ids for smoke tests.")
    parser.add_argument("--smoke-only", action="store_true")
    return parser.parse_args()


def term_raw_name(term: tr.BasisTerm) -> str:
    if term.kind == "constant":
        return "1"
    if term.kind == "sin":
        return f"sin(1 x{int(term.var)})"
    if term.kind == "cos":
        return f"cos(1 x{int(term.var)})"
    pieces = []
    for idx, power in enumerate(term.powers):
        if power == 1:
            pieces.append(f"x{idx}")
        elif power > 1:
            pieces.append(f"x{idx}^{power}")
    return " ".join(pieces) if pieces else "1"


def support_term_to_model_name(name: str) -> str:
    if name == "1":
        return name
    if name.startswith("sin(u") and name.endswith(")"):
        return f"sin(1*x{int(name[5:-1]) - 1})"
    if name.startswith("cos(u") and name.endswith(")"):
        return f"cos(1*x{int(name[5:-1]) - 1})"
    pieces = []
    for piece in name.split("*"):
        if "^" in piece:
            var, power = piece.split("^", 1)
        else:
            var, power = piece, ""
        if not var.startswith("u"):
            raise ValueError(f"unsupported support term: {name}")
        converted = f"x{int(var[1:]) - 1}"
        pieces.append(f"{converted}^{power}" if power else converted)
    return "*".join(pieces)


def phasec_support_maps(path: Path) -> tuple[pd.DataFrame, dict[int, list[set[str]]]]:
    support_frame = load_phase_c_support(path).set_index("system_id")
    payload = json.loads(path.read_text(encoding="utf-8"))
    true_terms: dict[int, list[set[str]]] = {}
    for system in payload["systems"]:
        system_id = int(system["system_id"])
        dim = int(system["dim"])
        if system.get("representability") == "exact":
            true_terms[system_id] = [
                {support_term_to_model_name(str(term)) for term in equation_terms}
                for equation_terms in system["support_terms"]
            ]
        else:
            true_terms[system_id] = [set() for _ in range(dim)]
    return support_frame, true_terms


def parse_limit(text: str) -> set[int] | None:
    if not text.strip():
        return None
    return {int(piece.strip()) for piece in text.split(",") if piece.strip()}


def add_noise_by_replicate(state: np.ndarray, sigma_rel: float, replicate: int, ic: int) -> np.ndarray:
    if sigma_rel == 0.0:
        return np.array(state, copy=True)
    seed = tr.NOISE_SEEDS[replicate - 1] + ic
    return tr.add_relative_noise(state, sigma_rel, seed)


def fit_coefficients(A: np.ndarray, y: np.ndarray, selected: list[int]) -> np.ndarray:
    coef = np.zeros(A.shape[1], dtype=float)
    if selected:
        values, *_ = np.linalg.lstsq(A[:, selected], y, rcond=None)
        coef[selected] = values
    return coef


def bic_for(A: np.ndarray, y: np.ndarray, selected: list[int]) -> float:
    coef = fit_coefficients(A, y, selected)
    resid = y - A @ coef
    sse = max(float(resid @ resid), np.finfo(float).tiny)
    n = max(int(A.shape[0]), 1)
    k = len(selected)
    return float(n * math.log(sse / n) + k * math.log(n))


def ranking_and_path(A: np.ndarray, y: np.ndarray, signal: str) -> tuple[list[int], list[float], list[np.ndarray]]:
    explicit_intercept = signal == "fd"
    order, _scores, _degenerate, _A_std = tr.ranking_for(A, y, "forward", explicit_intercept=explicit_intercept)
    bics = []
    coefs = []
    for k in range(1, A.shape[1] + 1):
        selected = order[:k]
        bics.append(bic_for(A, y, selected))
        coefs.append(fit_coefficients(A, y, selected))
    return order, bics, coefs


def active_from_coefficients(coef: np.ndarray, normalized_names: list[str]) -> list[set[str]]:
    return active_terms_by_equation(coef, normalized_names)


def eval_model(
    coefficients: np.ndarray,
    raw_names: list[str],
    trajectories: dict[tuple[int, int], tr.Trajectory],
    system_id: int,
    source_ic: int,
    target_ic: int,
    regime: str,
) -> tuple[float, bool, str, bool]:
    eval_ic = source_ic if regime == "reconstruction" else target_ic
    reference = trajectories[(system_id, eval_ic)].state
    prediction, status = simulate_model(coefficients, raw_names, reference[0, :], trajectories[(system_id, eval_ic)].time)
    score = float("nan") if prediction is None else r2_score(reference, prediction)
    diverged = status not in {"success"}
    return score, bool(math.isfinite(score) and score > R2_THRESHOLD), status, diverged


def selected_ks_for_operating_point(point: str, bics_by_eq: list[list[float]], true_terms: list[set[str]]) -> list[int]:
    if point == "bic":
        return [int(np.argmin(bics)) + 1 for bics in bics_by_eq]
    if point == "oracle_size":
        return [max(1, len(terms)) for terms in true_terms]
    raise ValueError(point)


def build_rows_for_cell(
    system: dict[str, Any],
    support_row: pd.Series,
    true_terms: list[set[str]],
    trajectories: dict[tuple[int, int], tr.Trajectory],
    signal: str,
    sigma_rel: float,
    replicate: int,
    source_ic: int,
    emit_full_path: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int, int]:
    system_id = int(system["id"])
    dim = int(system["dim"])
    target_ic = 2 if source_ic == 1 else 1
    direction = "IC1_to_IC2" if source_ic == 1 else "IC2_to_IC1"
    terms = tr.phasec_basis(dim)
    raw_names = [term_raw_name(term) for term in terms]
    normalized_names = [name.replace(" ", "*") for name in raw_names]
    noisy = add_noise_by_replicate(trajectories[(system_id, source_ic)].state, sigma_rel, replicate, source_ic)
    time = trajectories[(system_id, source_ic)].time

    orders: list[list[int]] = []
    bics_by_eq: list[list[float]] = []
    coefs_by_eq: list[list[np.ndarray]] = []
    for eq_idx0 in range(dim):
        A, y, _raw_phi = tr.build_design(time, noisy, eq_idx0, signal, terms)
        order, bics, coefs = ranking_and_path(A, y, signal)
        orders.append(order)
        bics_by_eq.append(bics)
        coefs_by_eq.append(coefs)

    detail_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    operating_points: list[tuple[str, list[int]]]
    operating_points = [
        ("bic", selected_ks_for_operating_point("bic", bics_by_eq, true_terms)),
        ("oracle_size", selected_ks_for_operating_point("oracle_size", bics_by_eq, true_terms)),
    ]
    if emit_full_path:
        operating_points.extend((f"path_k_{k}", [k] * dim) for k in range(1, len(terms) + 1))

    integrations = 0
    regressions = dim
    for point, selected_ks in operating_points:
        coef_matrix = np.vstack([coefs_by_eq[eq_idx][selected_ks[eq_idx] - 1] for eq_idx in range(dim)])
        raw_active = active_from_coefficients(coef_matrix, normalized_names)
        pruned_active = raw_active
        structure_raw = support_hit(raw_active, true_terms) if str(support_row["phasec_representability"]) == "exact" else False
        structure_pruned = structure_raw
        selected_k_value: int | str = selected_ks[0] if len(set(selected_ks)) == 1 else json.dumps(selected_ks, separators=(",", ":"))
        for regime in ("reconstruction", "generalization"):
            r2, r2_gt, status, diverged = eval_model(coef_matrix, raw_names, trajectories, system_id, source_ic, target_ic, regime)
            integrations += 1
            detail_rows.append(
                {
                    "system_id": system_id,
                    "system_name": system["eq_description"],
                    "dimension": dim,
                    "source_initial_condition_set": source_ic,
                    "target_initial_condition_set": target_ic,
                    "initial_condition_set": source_ic if regime == "reconstruction" else target_ic,
                    "direction": direction,
                    "regime": regime,
                    "n_library_terms": len(terms),
                    "true_terms": json.dumps([sorted(items) for items in true_terms], separators=(",", ":")),
                    "active_terms_raw": json.dumps([sorted(items) for items in raw_active], separators=(",", ":")),
                    "active_terms_pruned": json.dumps([sorted(items) for items in pruned_active], separators=(",", ":")),
                    "structure_hit_raw": structure_raw,
                    "structure_hit_pruned": structure_pruned,
                    "r2": r2,
                    "r2_gt_0_9": r2_gt,
                    "diverged_or_nonfinite": diverged,
                    "integration_status": status,
                    "fit_status": "success",
                    "n_target_regressions": regressions,
                    "n_evaluation_integrations": 1,
                    "phasec_representability_threeway": support_row["phasec_representability_threeway"],
                    "phasec_basis_name": support_row["phasec_basis_name"],
                    "valid_for_analysis": True,
                    "signal": signal,
                    "operating_point": "full_path" if point.startswith("path_k_") else point,
                    "selected_k": selected_k_value,
                    "sigma_rel": sigma_rel,
                    "noise_replicate": replicate,
                }
            )
        if point.startswith("path_k_"):
            path_rows.append(
                {
                    "system_id": system_id,
                    "dimension": dim,
                    "source_initial_condition_set": source_ic,
                    "direction": direction,
                    "signal": signal,
                    "sigma_rel": sigma_rel,
                    "noise_replicate": replicate,
                    "selected_k": selected_ks[0],
                    "selected_terms": json.dumps(
                        [[normalized_names[idx] for idx in orders[eq_idx][: selected_ks[eq_idx]]] for eq_idx in range(dim)],
                        separators=(",", ":"),
                    ),
                    "bic_by_equation": json.dumps([bics_by_eq[eq_idx][selected_ks[eq_idx] - 1] for eq_idx in range(dim)], separators=(",", ":")),
                    "structure_hit_raw": structure_raw,
                    "structure_hit_pruned": structure_pruned,
                }
            )
    return detail_rows, path_rows, regressions, integrations


def summarize(details: pd.DataFrame) -> pd.DataFrame:
    valid = details[details["valid_for_analysis"].astype(bool)].copy()
    rows = []
    group_columns = [
        "signal",
        "operating_point",
        "selected_k",
        "sigma_rel",
        "noise_replicate",
        "direction",
        "regime",
        "dimension",
        "phasec_representability_threeway",
    ]
    for keys, group in valid.groupby(group_columns, dropna=False):
        row = dict(zip(group_columns, keys))
        n_cells = int(len(group))
        finite = group["r2"].apply(math.isfinite)
        clean = finite & ~group["diverged_or_nonfinite"].astype(bool)
        exact = group["phasec_representability_threeway"] == "exact"
        exact_n = int(exact.sum())
        clean_values = group.loc[clean, "r2"]
        row.update(
            {
                "aggregation_scope": "dimension_by_phasec_representability_threeway",
                "n_cells": n_cells,
                "structure_denominator_exact_cells": exact_n,
                "structure_hit_raw_count": int(group.loc[exact, "structure_hit_raw"].sum()),
                "structure_hit_raw_rate": float(group.loc[exact, "structure_hit_raw"].mean()) if exact_n else float("nan"),
                "structure_hit_pruned_count": int(group.loc[exact, "structure_hit_pruned"].sum()),
                "structure_hit_pruned_rate": float(group.loc[exact, "structure_hit_pruned"].mean()) if exact_n else float("nan"),
                "diverged_or_nonfinite_count": int(group["diverged_or_nonfinite"].sum()),
                "r2_finite_nondiverged_count": int(clean.sum()),
                "r2_gt_0_9_count": int(group["r2_gt_0_9"].sum()),
                "r2_gt_0_9_rate_over_cells": float(group["r2_gt_0_9"].sum() / n_cells) if n_cells else float("nan"),
                "r2_median_valid": float(clean_values.median()) if int(clean.sum()) else float("nan"),
                "r2_q000_finite_nondiverged": float(clean_values.quantile(0.0)) if int(clean.sum()) else float("nan"),
                "r2_q025_finite_nondiverged": float(clean_values.quantile(0.25)) if int(clean.sum()) else float("nan"),
                "r2_q075_finite_nondiverged": float(clean_values.quantile(0.75)) if int(clean.sum()) else float("nan"),
                "r2_q100_finite_nondiverged": float(clean_values.quantile(1.0)) if int(clean.sum()) else float("nan"),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def projected_integrations(system_ids: list[int], benchmark: list[dict[str, Any]]) -> int:
    dim_by_id = {int(item["id"]): int(item["dim"]) for item in benchmark}
    total_p = sum(len(tr.phasec_basis(dim_by_id[system_id])) for system_id in system_ids)
    sigma0_full_path = len(SIGNALS) * 2 * 2 * total_p
    operating_points = len(SIGNALS) * 2 * 2 * 2 * len(system_ids) * sum(len(v) for v in SIGMA_REPLICATES.values())
    return sigma0_full_path + operating_points


def write_figures(details: pd.DataFrame, path_df: pd.DataFrame, sindy_path: Path, figure_dir: Path) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    exact_path = path_df[path_df["sigma_rel"].eq(0.0)].copy()
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.5), sharey=True)
    for ax, dim in zip(axes, [1, 2, 3, 4]):
        sub = exact_path[exact_path["dimension"].eq(dim)]
        for signal, group in sub.groupby("signal"):
            by_k = group.groupby("selected_k")["structure_hit_pruned"].mean()
            ax.plot(by_k.index, by_k.values, marker="o", label=signal)
        ax.set_title(f"dim {dim}")
        ax.set_xlabel("k")
        ax.set_ylabel("structure hit")
        ax.set_ylim(-0.05, 1.05)
    axes[-1].legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "structure_hit_path_by_dimension.png", dpi=160)
    plt.close(fig)

    t1b = details[(details["sigma_rel"].eq(0.0)) & (details["operating_point"].isin(["bic", "oracle_size"]))].copy()
    t1b = t1b[t1b["phasec_representability_threeway"].eq("exact")]
    points = []
    for keys, group in t1b.groupby(["dimension", "signal", "operating_point"]):
        dim, signal, point = keys
        points.append(
            {
                "dimension": dim,
                "label": f"{signal}/{point}",
                "structure": float(group["structure_hit_pruned"].mean()),
                "r2": float(group["r2_gt_0_9"].mean()),
            }
        )
    sindy = pd.read_csv(sindy_path)
    sindy = sindy[(sindy["phasec_representability_threeway"].eq("exact")) & (sindy["library_id"].eq("poly_deg3_sin_cos_stlsq_0.1"))]
    for dim, group in sindy.groupby("dimension"):
        points.append(
            {
                "dimension": dim,
                "label": "SINDy",
                "structure": float(group["sindy_structure_hit_pruned"].mean()),
                "r2": float(group["r2_gt_0_9"].mean()),
            }
        )
    point_df = pd.DataFrame(points)
    fig, axes = plt.subplots(1, 4, figsize=(14, 3.5), sharex=True, sharey=True)
    for ax, dim in zip(axes, [1, 2, 3, 4]):
        sub = point_df[point_df["dimension"].eq(dim)]
        for _, row in sub.iterrows():
            ax.scatter(row["structure"], row["r2"], s=30)
            ax.annotate(row["label"], (row["structure"], row["r2"]), fontsize=7)
        ax.set_title(f"dim {dim}")
        ax.set_xlabel("structure hit")
        ax.set_ylabel("R2 > 0.9")
        ax.set_xlim(-0.05, 1.05)
        ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(figure_dir / "structure_vs_r2_rate_against_sindy.png", dpi=160)
    plt.close(fig)


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    support_path = root / "studies" / "regression" / "phase_c_support.json"
    benchmark_path = root / "benchmarks" / "data" / "strogatz_extended.json"
    export_dir = root / "outputs" / "phase_c_trajectory_hashes" / "wp_c4c" / "trajectory_export"
    sindy_details = root / "analysis" / "data" / "paper1_phaseC_v1" / "phasec_sindy_baseline_wp_c4c_export" / "details.csv"
    support_frame, true_terms_map = phasec_support_maps(support_path)
    benchmark = tr.load_benchmark(benchmark_path)
    systems = [benchmark[system_id] for system_id in sorted(benchmark)]
    limit = parse_limit(args.limit_systems)
    if limit is not None:
        systems = [system for system in systems if int(system["id"]) in limit]
    system_ids = [int(system["id"]) for system in systems]
    trajectories = tr.load_exported_trajectories(export_dir, system_ids)
    projection = projected_integrations(system_ids, list(benchmark.values()))
    if projection > MAX_PROJECTED_INTEGRATIONS:
        raise ValueError(f"projected integrations {projection} exceed limit {MAX_PROJECTED_INTEGRATIONS}")
    if args.smoke_only:
        return {"projected_integrations": projection, "systems": len(system_ids)}

    detail_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []
    actual_integrations = 0
    for system in systems:
        system_id = int(system["id"])
        for signal in SIGNALS:
            for sigma_rel, replicates in SIGMA_REPLICATES.items():
                for replicate in replicates:
                    for source_ic in (1, 2):
                        rows, paths, regressions, integrations = build_rows_for_cell(
                            system,
                            support_frame.loc[system_id],
                            true_terms_map[system_id],
                            trajectories,
                            signal,
                            sigma_rel,
                            replicate,
                            source_ic,
                            emit_full_path=sigma_rel == 0.0,
                        )
                        detail_rows.extend(rows)
                        path_rows.extend(paths)
                        actual_integrations += integrations
                        cost_rows.append(
                            {
                                "system_id": system_id,
                                "dimension": int(system["dim"]),
                                "signal": signal,
                                "sigma_rel": sigma_rel,
                                "noise_replicate": replicate,
                                "source_initial_condition_set": source_ic,
                                "n_library_terms": len(tr.phasec_basis(int(system["dim"]))),
                                "n_target_regressions": regressions,
                                "n_path_least_squares": regressions * len(tr.phasec_basis(int(system["dim"]))),
                                "n_evaluation_integrations": integrations,
                                "n_selection_integrations": 0,
                            }
                        )

    data_dir = root / "analysis" / "data" / STUDY_ID
    figure_dir = root / "analysis" / "figures" / STUDY_ID
    data_dir.mkdir(parents=True, exist_ok=True)
    details = pd.DataFrame(detail_rows)
    path_df = pd.DataFrame(path_rows)
    costs = pd.DataFrame(cost_rows)
    summary = summarize(details)
    details.to_csv(data_dir / "details.csv", index=False)
    summary.to_csv(data_dir / "summary.csv", index=False)
    path_df.to_csv(data_dir / "selection_path.csv", index=False)
    costs.to_csv(data_dir / "cost.csv", index=False)
    metadata = {
        "study_id": STUDY_ID,
        "configuration_hash": hashlib.sha256(json.dumps({"signals": SIGNALS, "sigma_replicates": SIGMA_REPLICATES}, sort_keys=True).encode()).hexdigest(),
        "input_hashes": tr.input_hashes([support_path, benchmark_path, export_dir / "trajectory_manifest.csv", sindy_details]),
        "noise_seeds": tr.NOISE_SEEDS,
        "bic_formula": BIC_FORMULA,
        "bic_dependency_limitation": "Weak-form rows include overlapping windows and are not independent.",
        "fd_intercept_treatment": "The repaired fd arm keeps the constant column uncentered and fit as a regular candidate.",
        "projected_integrations_from_smoke": projection,
        "actual_evaluation_integrations": actual_integrations,
        "selection_integrations": 0,
        "support_abs": SUPPORT_ABS,
        "support_rel": SUPPORT_REL,
    }
    (data_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_figures(details, path_df, sindy_details, figure_dir)
    return {
        "details_rows": len(details),
        "summary_rows": len(summary),
        "selection_path_rows": len(path_df),
        "projected_integrations": projection,
        "actual_integrations": actual_integrations,
        "data_dir": str(data_dir),
    }


def main() -> int:
    try:
        print(json.dumps(run(parse_args()), indent=2))
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
