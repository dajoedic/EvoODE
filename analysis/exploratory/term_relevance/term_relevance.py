from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sympy as sp


STUDY_ID = "wp_t1_term_relevance"
BASIS_NAME = "staged_polynomial_basis_with_constant"
NOISE_SEEDS = [2026092201, 2026092202, 2026092203, 2026092204, 2026092205]
NULL_SEED = 2026092291
PERMUTATION_SEED = 2026092292
SINGULAR_RELATIVE_THRESHOLD = 1.0e-10
DEGENERATE_STD_TOL = 1.0e-12
RANDOM_PERMUTATIONS = 10_000
THRESHOLDS = [0, 1, 2, 3, 5, 10]
QUANTILES = [0.10, 0.25, 0.50, 0.75, 0.90]


@dataclass(frozen=True)
class BasisTerm:
    name: str
    kind: str
    powers: tuple[int, ...] = ()
    var: int | None = None


@dataclass(frozen=True)
class Trajectory:
    time: np.ndarray
    state: np.ndarray
    sha256: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def phasec_basis(dim: int) -> list[BasisTerm]:
    terms: list[BasisTerm] = [BasisTerm("1", "constant", (0,) * dim)]
    for i in range(dim):
        powers = [0] * dim
        powers[i] = 1
        terms.append(BasisTerm(f"u{i + 1}", "monomial", tuple(powers)))
    for i in range(dim):
        powers = [0] * dim
        powers[i] = 2
        terms.append(BasisTerm(f"u{i + 1}^2", "monomial", tuple(powers)))
    for i in range(dim):
        for j in range(i + 1, dim):
            powers = [0] * dim
            powers[i] = 1
            powers[j] = 1
            terms.append(BasisTerm(f"u{i + 1}*u{j + 1}", "monomial", tuple(powers)))
    for i in range(dim):
        powers = [0] * dim
        powers[i] = 3
        terms.append(BasisTerm(f"u{i + 1}^3", "monomial", tuple(powers)))
    for i in range(dim):
        terms.append(BasisTerm(f"sin(u{i + 1})", "sin", var=i))
        terms.append(BasisTerm(f"cos(u{i + 1})", "cos", var=i))
    return terms


def evaluate_basis(state: np.ndarray, terms: list[BasisTerm]) -> np.ndarray:
    out = np.empty((state.shape[0], len(terms)), dtype=float)
    for col, term in enumerate(terms):
        if term.kind == "constant":
            out[:, col] = 1.0
        elif term.kind == "monomial":
            values = np.ones(state.shape[0], dtype=float)
            for axis, power in enumerate(term.powers):
                if power:
                    values *= state[:, axis] ** power
            out[:, col] = values
        elif term.kind == "sin":
            out[:, col] = np.sin(state[:, int(term.var)])
        elif term.kind == "cos":
            out[:, col] = np.cos(state[:, int(term.var)])
        else:
            raise ValueError(f"unknown basis term kind: {term.kind}")
    return out


def load_exact_supports(path: Path) -> tuple[str, list[dict[str, object]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    systems = [
        item
        for item in payload["systems"]
        if item.get("representability") == "exact" and item.get("status") == "ok"
    ]
    if len(systems) != 30:
        raise ValueError(f"expected 30 exact ok systems, got {len(systems)}")
    return str(payload["basis_name"]), systems


def verify_basis_consistency(support_systems: list[dict[str, object]]) -> None:
    expected_sizes = {1: 6, 2: 12, 3: 19, 4: 27}
    for dim, expected in expected_sizes.items():
        actual = len(phasec_basis(dim))
        if actual != expected:
            raise ValueError(f"basis size mismatch for dim {dim}: {actual} != {expected}")
    for system in support_systems:
        dim = int(system["dim"])
        names = [term.name for term in phasec_basis(dim)]
        for eq_idx, (idxs, terms) in enumerate(zip(system["support_idxs"], system["support_terms"]), start=1):
            idx_names = [names[int(idx) - 1] for idx in idxs]
            if idx_names != list(terms):
                raise ValueError(
                    f"support index/name drift for system {system['system_id']} equation {eq_idx}: "
                    f"{idx_names} != {terms}"
                )


def load_benchmark(path: Path) -> dict[int, dict[str, object]]:
    systems = json.loads(path.read_text(encoding="utf-8"))
    return {int(item["id"]): item for item in systems}


def _parse_shape(text: str) -> tuple[int, ...]:
    value = json.loads(text)
    return tuple(int(v) for v in value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_exported_trajectories(export_dir: Path, expected_systems: Iterable[int] | None = None) -> dict[tuple[int, int], Trajectory]:
    manifest_path = export_dir / "trajectory_manifest.csv"
    if not manifest_path.exists():
        raise ValueError(f"missing trajectory export manifest: {manifest_path}")
    expected = set(int(x) for x in expected_systems) if expected_systems is not None else None
    trajectories: dict[tuple[int, int], Trajectory] = {}
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            system_id = int(row["system_id"])
            if expected is not None and system_id not in expected:
                continue
            ic_set = int(row["initial_condition_set"])
            if row["dtype"] != "float64" or row["byte_order"] != "little_endian":
                raise ValueError(f"unsupported trajectory dtype/byte order for system {system_id} ic{ic_set}")
            if row["time_axis_order"] != "time" or row["state_axis_order"] != "time_by_dimension_c_order":
                raise ValueError(f"unsupported trajectory axis order for system {system_id} ic{ic_set}")
            time_path = export_dir / row["time_path"]
            state_path = export_dir / row["state_path"]
            time_hash = _sha256(time_path)
            state_hash = _sha256(state_path)
            if time_hash != row["time_sha256"] or state_hash != row["state_sha256"]:
                raise ValueError(f"hash mismatch for system {system_id} ic{ic_set}")
            time = np.fromfile(time_path, dtype="<f8").reshape(_parse_shape(row["time_shape"]), order="C")
            state = np.fromfile(state_path, dtype="<f8").reshape(_parse_shape(row["state_shape"]), order="C")
            trajectories[(system_id, ic_set)] = Trajectory(time=time, state=state, sha256=state_hash)
    if expected is not None:
        missing = [(sid, ic) for sid in expected for ic in (1, 2) if (sid, ic) not in trajectories]
        if missing:
            raise ValueError(f"missing exported trajectories: {missing[:5]}")
    return trajectories


def add_relative_noise(state: np.ndarray, sigma_rel: float, seed: int | None) -> np.ndarray:
    if sigma_rel == 0.0:
        return np.array(state, copy=True)
    rng = np.random.default_rng(seed)
    scale = np.std(state, axis=0, ddof=0) * sigma_rel
    return state + rng.normal(0.0, scale, size=state.shape)


def build_design(time: np.ndarray, state: np.ndarray, equation_idx0: int, signal: str, terms: list[BasisTerm]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    phi = evaluate_basis(state, terms)
    if signal == "fd":
        y = np.gradient(state[:, equation_idx0], time, edge_order=2)
        return phi, y, phi
    if signal != "weak":
        raise ValueError(f"unknown signal: {signal}")
    rows: list[np.ndarray] = []
    targets: list[float] = []
    for length in (1, 2, 4, 8, 16):
        for start in range(0, len(time) - length):
            stop = start + length
            rows.append(np.trapz(phi[start : stop + 1], x=time[start : stop + 1], axis=0))
            targets.append(float(state[stop, equation_idx0] - state[start, equation_idx0]))
    return np.vstack(rows), np.asarray(targets, dtype=float), phi


def standardize_design(
    A: np.ndarray,
    y: np.ndarray,
    *,
    explicit_intercept: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    means = np.mean(A, axis=0)
    stds = np.std(A, axis=0, ddof=0)
    degenerate = stds <= DEGENERATE_STD_TOL
    if explicit_intercept and A.shape[1] > 0 and np.allclose(A[:, 0], A[0, 0], rtol=0.0, atol=DEGENERATE_STD_TOL):
        means = means.copy()
        stds = stds.copy()
        degenerate = degenerate.copy()
        means[0] = 0.0
        stds[0] = 1.0
        degenerate[0] = False
    safe_stds = np.where(degenerate, 1.0, stds)
    A_std = (A - means) / safe_stds
    A_std[:, degenerate] = 0.0
    y_centered = y if explicit_intercept else y - np.mean(y)
    return A_std, y_centered, means, stds, degenerate


def rank_marginal(A: np.ndarray, y: np.ndarray, degenerate: np.ndarray) -> tuple[list[int], np.ndarray]:
    y_norm = float(np.linalg.norm(y))
    scores = np.zeros(A.shape[1], dtype=float)
    if y_norm > 0.0:
        scores = np.abs(A.T @ y) / max(y_norm, np.finfo(float).eps)
    scores[degenerate] = -np.inf
    order = sorted(range(A.shape[1]), key=lambda j: (-scores[j], j))
    return order, scores


def rank_forward(A: np.ndarray, y: np.ndarray, degenerate: np.ndarray) -> tuple[list[int], np.ndarray]:
    p = A.shape[1]
    selected: list[int] = []
    remaining = set(range(p))
    scores = np.full(p, -np.inf, dtype=float)
    gram = A.T @ A
    rhs = A.T @ y
    y_sse = float(y @ y)
    current_sse = y_sse
    for step in range(p):
        best: tuple[float, int, float] | None = None
        for j in sorted(remaining):
            if degenerate[j]:
                reduction = -np.inf
                candidate_sse = current_sse
            else:
                cols = selected + [j]
                ix = np.ix_(cols, cols)
                coef, *_ = np.linalg.lstsq(gram[ix], rhs[cols], rcond=None)
                candidate_sse = y_sse - float(rhs[cols] @ coef)
                reduction = current_sse - candidate_sse
            if best is None or reduction > best[0] + 1e-14 or (abs(reduction - best[0]) <= 1e-14 and j < best[1]):
                best = (reduction, j, candidate_sse)
        assert best is not None
        reduction, chosen, current_sse = best
        selected.append(chosen)
        remaining.remove(chosen)
        scores[chosen] = reduction
    return selected, scores


def metrics_from_order(order: list[int], true_idxs0: set[int], k_values: Iterable[int] = (1, 2, 3, 5, 10)) -> dict[str, object]:
    ranks = {idx: rank for rank, idx in enumerate(order, start=1)}
    true_ranks = [ranks[idx] for idx in sorted(true_idxs0)]
    worst = max(true_ranks)
    false_before = sum(1 for idx in order[:worst] if idx not in true_idxs0)
    mrr = float(np.mean([1.0 / r for r in true_ranks]))
    out: dict[str, object] = {
        "n_false_before_last_true": int(false_before),
        "rank_worst_true": int(worst),
        "mrr_true": mrr,
    }
    for k in k_values:
        out[f"recall_at_{k}"] = sum(1 for idx in order[:k] if idx in true_idxs0) / len(true_idxs0)
    return out


def matrix_diagnostics(A_std: np.ndarray, raw_phi: np.ndarray, true_idxs0: set[int], false_idxs0: set[int], coefficients: dict[int, float]) -> dict[str, object]:
    singular = np.linalg.svd(A_std, compute_uv=False)
    max_singular = float(np.max(singular)) if singular.size else 0.0
    if max_singular <= 0.0:
        condition = math.inf
        effective_rank = 0
    else:
        positive = singular[singular > max_singular * SINGULAR_RELATIVE_THRESHOLD]
        condition = float(max_singular / positive[-1]) if positive.size else math.inf
        effective_rank = int(positive.size)
    norms = np.linalg.norm(A_std, axis=0)
    cosines: list[float] = []
    for true_idx in sorted(true_idxs0):
        values = []
        for false_idx in sorted(false_idxs0):
            denom = norms[true_idx] * norms[false_idx]
            values.append(0.0 if denom == 0.0 else abs(float(A_std[:, true_idx] @ A_std[:, false_idx] / denom)))
        cosines.append(max(values) if values else 0.0)
    excitation = {
        "std": np.std(raw_phi, axis=0, ddof=0).astype(float).tolist(),
        "mean_abs": np.mean(np.abs(raw_phi), axis=0).astype(float).tolist(),
    }
    contribution = {
        str(idx + 1): abs(float(coefficients.get(idx, 0.0))) * float(np.std(raw_phi[:, idx], ddof=0))
        for idx in sorted(true_idxs0)
    }
    return {
        "condition_number": condition,
        "effective_rank": effective_rank,
        "max_cosine_true_vs_false": max(cosines) if cosines else 0.0,
        "column_excitation": excitation,
        "true_term_contribution": contribution,
    }


def coefficient_map(substituted_expr: str, terms: list[BasisTerm]) -> dict[int, float]:
    dim = len(terms[0].powers)
    variables = sp.symbols(" ".join(f"x_{i}" for i in range(dim)))
    if dim == 1:
        variables = (variables,)
    locals_map = {f"x_{i}": variables[i] for i in range(dim)}
    expr = sp.sympify(substituted_expr, locals=locals_map)
    mapping: dict[int, float] = {}
    zero_subs = {var: 0 for var in variables}
    for idx, term in enumerate(terms):
        if term.kind == "constant":
            value = expr.subs(zero_subs)
        elif term.kind == "monomial":
            monomial = sp.prod(variables[i] ** power for i, power in enumerate(term.powers))
            value = sp.expand(expr).coeff(monomial)
        elif term.kind == "sin":
            value = sp.expand(expr).coeff(sp.sin(variables[int(term.var)]))
        elif term.kind == "cos":
            value = sp.expand(expr).coeff(sp.cos(variables[int(term.var)]))
        else:
            value = 0
        try:
            numeric = float(value)
        except TypeError:
            numeric = 0.0
        if abs(numeric) > 0.0:
            mapping[idx] = numeric
    return mapping


def ranking_for(
    A: np.ndarray,
    y: np.ndarray,
    method: str,
    *,
    explicit_intercept: bool = False,
) -> tuple[list[int], np.ndarray, np.ndarray, np.ndarray]:
    A_std, y_centered, _means, _stds, degenerate = standardize_design(A, y, explicit_intercept=explicit_intercept)
    if method == "marginal":
        order, scores = rank_marginal(A_std, y_centered, degenerate)
    elif method == "forward":
        order, scores = rank_forward(A_std, y_centered, degenerate)
    else:
        raise ValueError(f"unknown ranking method: {method}")
    return order, scores, degenerate, A_std


def run_records(
    support_systems: list[dict[str, object]],
    benchmark: dict[int, dict[str, object]],
    trajectories: dict[tuple[int, int], Trajectory],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for system in support_systems:
        system_id = int(system["system_id"])
        dim = int(system["dim"])
        terms = phasec_basis(dim)
        candidate_names = [term.name for term in terms]
        substituted = list(benchmark[system_id]["substituted"][0])
        equation_meta = []
        for eq_idx0, support_terms in enumerate(system["support_terms"]):
            true_idxs0 = {candidate_names.index(name) for name in support_terms}
            false_idxs0 = set(range(len(terms))) - true_idxs0
            coeffs = coefficient_map(substituted[eq_idx0], terms)
            equation_meta.append((eq_idx0, support_terms, true_idxs0, false_idxs0, coeffs))
        for sigma_rel in (0.0, 0.01, 0.05):
            replicate_items = [(0, None)] if sigma_rel == 0.0 else list(enumerate(NOISE_SEEDS, start=1))
            for noise_replicate, noise_seed in replicate_items:
                noisy: dict[int, np.ndarray] = {}
                for ic in (1, 2):
                    noisy[ic] = add_relative_noise(trajectories[(system_id, ic)].state, sigma_rel, noise_seed + ic if noise_seed else None)
                for ic_strategy in ("ic1", "ic2", "ic1_ic2"):
                    if ic_strategy == "ic1":
                        parts = [(trajectories[(system_id, 1)].time, noisy[1])]
                        sha = trajectories[(system_id, 1)].sha256
                    elif ic_strategy == "ic2":
                        parts = [(trajectories[(system_id, 2)].time, noisy[2])]
                        sha = trajectories[(system_id, 2)].sha256
                    else:
                        parts = [(trajectories[(system_id, 1)].time, noisy[1]), (trajectories[(system_id, 2)].time, noisy[2])]
                        sha = trajectories[(system_id, 1)].sha256 + ";" + trajectories[(system_id, 2)].sha256
                    for eq_idx0, support_terms, true_idxs0, false_idxs0, coeffs in equation_meta:
                        for signal in ("weak", "fd"):
                            matrices = [build_design(time, state, eq_idx0, signal, terms) for time, state in parts]
                            A = np.vstack([item[0] for item in matrices])
                            y = np.concatenate([item[1] for item in matrices])
                            raw_phi = np.vstack([item[2] for item in matrices])
                            for method in ("marginal", "forward"):
                                order, scores, degenerate, A_std = ranking_for(A, y, method)
                                ranks = [0] * len(order)
                                for rank, idx in enumerate(order, start=1):
                                    ranks[idx] = rank
                                metric = metrics_from_order(order, true_idxs0)
                                diag = matrix_diagnostics(A_std, raw_phi, true_idxs0, false_idxs0, coeffs)
                                records.append(
                                    {
                                        "system_id": system_id,
                                        "system_name": str(benchmark[system_id].get("eq_description", f"system {system_id}")),
                                        "dimension": dim,
                                        "equation_idx": eq_idx0 + 1,
                                        "ic_strategy": ic_strategy,
                                        "signal": signal,
                                        "ranking_method": method,
                                        "sigma_rel": sigma_rel,
                                        "noise_replicate": noise_replicate,
                                        "noise_seed": noise_seed if noise_seed is not None else "",
                                        "basis_name": BASIS_NAME,
                                        "library_size": len(terms),
                                        "true_support_terms": list(support_terms),
                                        "true_support_size": len(true_idxs0),
                                        "candidate_names": candidate_names,
                                        "candidate_scores": [None if not np.isfinite(x) else float(x) for x in scores],
                                        "candidate_ranks": ranks,
                                        **metric,
                                        **diag,
                                        "degenerate_column_count": int(np.sum(degenerate)),
                                        "degenerate_columns": [candidate_names[i] for i, flag in enumerate(degenerate) if flag],
                                        "trajectory_source": "campaign_export",
                                        "trajectory_sha256": sha,
                                    }
                                )
    return records


def random_false_before(p: int, s: int, rng: np.random.Generator, n: int = RANDOM_PERMUTATIONS) -> np.ndarray:
    values = np.empty(n, dtype=float)
    true = set(range(s))
    for i in range(n):
        order = rng.permutation(p)
        worst = max(np.where(np.isin(order, list(true)))[0])
        values[i] = sum(1 for item in order[: worst + 1] if item not in true)
    return values


def analytic_null_mean(p: int, s: int) -> float:
    return (p - s) * s / (s + 1)


def cluster_sign_permutation_p(diffs_by_system: dict[int, float]) -> float:
    values = np.asarray(list(diffs_by_system.values()), dtype=float)
    observed = float(np.sum(values))
    if observed <= 0:
        return 1.0
    if len(values) <= 20:
        totals = []
        for signs in itertools.product((-1.0, 1.0), repeat=len(values)):
            totals.append(float(np.sum(values * np.asarray(signs))))
        totals_arr = np.asarray(totals)
        return float((np.sum(totals_arr >= observed - 1e-15) + 1.0) / (len(totals_arr) + 1.0))
    rng = np.random.default_rng(PERMUTATION_SEED)
    extreme = 0
    for _ in range(100_000):
        signs = rng.choice([-1.0, 1.0], size=len(values))
        if float(np.sum(values * signs)) >= observed - 1e-15:
            extreme += 1
    return float((extreme + 1.0) / 100_001.0)


def summarize_outputs(records: list[dict[str, object]]) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.DataFrame(records)
    keys = ["signal", "ranking_method", "sigma_rel", "noise_replicate", "ic_strategy", "dimension"]
    summary_rows: list[dict[str, object]] = []
    null_rows: list[dict[str, object]] = []
    rng = np.random.default_rng(NULL_SEED)
    empirical_cache: dict[tuple[int, int], np.ndarray] = {}
    for group_key, group in df.groupby(keys, dropna=False):
        row = dict(zip(keys, group_key))
        values = group["n_false_before_last_true"].to_numpy(dtype=float)
        row["n_equations"] = int(len(group))
        for q in QUANTILES:
            row[f"q{int(q * 100):03d}"] = float(np.quantile(values, q))
        for threshold in THRESHOLDS:
            row[f"le_{threshold}_count"] = int(np.sum(values <= threshold))
            row[f"le_{threshold}_rate"] = float(np.mean(values <= threshold))
        summary_rows.append(row)
        null_means = []
        empirical_means = []
        empirical_deviations = []
        for _, item in group.iterrows():
            p = int(item["library_size"])
            s = int(item["true_support_size"])
            analytic = analytic_null_mean(p, s)
            null_means.append(analytic)
            if (p, s) not in empirical_cache:
                empirical_cache[(p, s)] = random_false_before(p, s, rng)
            empirical = float(np.mean(empirical_cache[(p, s)]))
            empirical_means.append(empirical)
            empirical_deviations.append(abs(empirical - analytic))
        group_with_null = group.copy()
        group_with_null["analytic_null"] = null_means
        diffs = group_with_null.groupby("system_id").apply(
            lambda x: float(np.mean(x["analytic_null"].to_numpy(dtype=float) - x["n_false_before_last_true"].to_numpy(dtype=float))),
            include_groups=False,
        )
        null_rows.append(
            {
                **row,
                "analytic_null_mean": float(np.mean(null_means)),
                "empirical_null_mean": float(np.mean(empirical_means)),
                "max_empirical_analytic_abs_deviation": float(np.max(empirical_deviations)),
                "cluster_robust_p": cluster_sign_permutation_p(diffs.to_dict()),
                "cluster_count": int(group["system_id"].nunique()),
                "permutation_unit": "system_id",
                "random_permutations_per_equation": RANDOM_PERMUTATIONS,
            }
        )
    return pd.DataFrame(summary_rows), pd.DataFrame(null_rows)


def gate_decision(df: pd.DataFrame, null_df: pd.DataFrame) -> dict[str, object]:
    mask = (
        (df["signal"] == "weak")
        & (df["ranking_method"] == "forward")
        & (df["sigma_rel"] == 0.0)
        & (df["noise_replicate"] == 0)
        & (df["ic_strategy"] == "ic1")
        & (df["dimension"].isin([2, 3]))
    )
    decision = df[mask].copy()
    values = decision["n_false_before_last_true"].to_numpy(dtype=float)
    null_mask = (
        (null_df["signal"] == "weak")
        & (null_df["ranking_method"] == "forward")
        & (null_df["sigma_rel"] == 0.0)
        & (null_df["noise_replicate"] == 0)
        & (null_df["ic_strategy"] == "ic1")
        & (null_df["dimension"].isin([2, 3]))
    )
    # Recompute the primary cluster test on the pooled dim 2+3 decision cell.
    pooled = decision.copy()
    pooled["analytic_null"] = [analytic_null_mean(int(p), int(s)) for p, s in zip(pooled["library_size"], pooled["true_support_size"])]
    diffs = pooled.groupby("system_id").apply(
        lambda x: float(np.mean(x["analytic_null"].to_numpy(dtype=float) - x["n_false_before_last_true"].to_numpy(dtype=float))),
        include_groups=False,
    )
    p_value = cluster_sign_permutation_p(diffs.to_dict())
    median_ok = float(np.median(values)) <= 2.0
    level_ok = float(np.mean(values <= 3.0)) >= 0.60
    null_ok = p_value < 0.01
    ic2_mask = mask.copy() if hasattr(mask, "copy") else mask
    ic2_decision = df[
        (df["signal"] == "weak")
        & (df["ranking_method"] == "forward")
        & (df["sigma_rel"] == 0.0)
        & (df["noise_replicate"] == 0)
        & (df["ic_strategy"] == "ic2")
        & (df["dimension"].isin([2, 3]))
    ].copy()
    ic2_decision["analytic_null"] = [
        analytic_null_mean(int(p), int(s)) for p, s in zip(ic2_decision["library_size"], ic2_decision["true_support_size"])
    ]
    ic2_diffs = ic2_decision.groupby("system_id").apply(
        lambda x: float(np.mean(x["analytic_null"].to_numpy(dtype=float) - x["n_false_before_last_true"].to_numpy(dtype=float))),
        include_groups=False,
    )
    ic2_p = cluster_sign_permutation_p(ic2_diffs.to_dict())
    replication_same_direction = bool(float(np.sum(ic2_diffs.to_numpy())) > 0 and ic2_p < 0.05)
    if null_ok and median_ok and level_ok and replication_same_direction:
        judgment = "positive"
    elif null_ok and replication_same_direction:
        judgment = "conditional"
    elif null_ok:
        judgment = "conditional"
    else:
        judgment = "negative"
    return {
        "decision_cell": {
            "signal": "weak",
            "ranking_method": "forward",
            "sigma_rel": 0.0,
            "ic_strategy": "ic1",
            "stratum": "dimension 2 and dimension 3",
            "systems": int(decision["system_id"].nunique()),
            "equations": int(len(decision)),
        },
        "conditions": {
            "median_n_false_before_last_true_le_2": median_ok,
            "median_n_false_before_last_true": float(np.median(values)),
            "share_n_false_before_last_true_le_3_ge_0_60": level_ok,
            "share_n_false_before_last_true_le_3": float(np.mean(values <= 3.0)),
            "cluster_robust_null_p_lt_0_01": null_ok,
            "cluster_robust_null_p": p_value,
        },
        "replication_condition": {
            "ic2_same_direction": replication_same_direction,
            "ic2_cluster_robust_p": ic2_p,
        },
        "judgment": judgment,
        "threshold_policy": "The levels 2 and 3 are pre-declared human design thresholds, not data-derived thresholds.",
        "effective_cluster_count": int(decision["system_id"].nunique()),
    }


def _jsonable_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    for record in records:
        item = {}
        for key, value in record.items():
            if isinstance(value, (list, dict)):
                item[key] = json.dumps(value, separators=(",", ":"))
            elif isinstance(value, float) and not np.isfinite(value):
                item[key] = "inf" if value > 0 else "-inf"
            else:
                item[key] = value
        out.append(item)
    return out


def write_outputs(records: list[dict[str, object]], summary: pd.DataFrame, nulls: pd.DataFrame, gate: dict[str, object], data_dir: Path, figure_dir: Path, config: dict[str, object]) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(_jsonable_records(records)).to_csv(data_dir / "records.csv", index=False)
    summary.to_csv(data_dir / "aggregate_by_configuration_dimension.csv", index=False)
    nulls.to_csv(data_dir / "null_model_by_configuration_dimension.csv", index=False)
    (data_dir / "gate_decision.json").write_text(json.dumps(gate, indent=2), encoding="utf-8")
    (data_dir / "run_metadata.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    df = pd.DataFrame(records)
    clean = df[df["noise_replicate"] == 0].copy()
    clean["configuration"] = clean["signal"] + "/" + clean["ranking_method"] + "/" + clean["ic_strategy"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
    for ax, dim in zip(axes.ravel(), [1, 2, 3, 4]):
        sub = clean[(clean["dimension"] == dim) & (clean["sigma_rel"] == 0.0)]
        configs = sorted(sub["configuration"].unique())
        data = [sub[sub["configuration"] == cfg]["n_false_before_last_true"].to_numpy(dtype=float) for cfg in configs]
        ax.boxplot(data, labels=list(range(1, len(configs) + 1)), showfliers=False)
        null_ref = np.mean([analytic_null_mean(int(p), int(s)) for p, s in zip(sub["library_size"], sub["true_support_size"])]) if len(sub) else 0.0
        ax.axhline(null_ref, color="black", linestyle="--", linewidth=1)
        ax.set_title(f"dim {dim}")
        ax.set_xlabel("configuration index")
        ax.set_ylabel("false before last true")
    fig.tight_layout()
    fig.savefig(figure_dir / "distribution_by_dimension_configuration.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    decision = clean[(clean["signal"] == "weak") & (clean["ranking_method"] == "forward") & (clean["ic_strategy"].isin(["ic1", "ic2"]))]
    axes[0].scatter(decision["max_cosine_true_vs_false"], decision["n_false_before_last_true"], s=12, alpha=0.7)
    axes[0].set_xlabel("max true-vs-false cosine")
    axes[0].set_ylabel("false before last true")
    axes[1].scatter(np.log10(decision["condition_number"].replace([np.inf, -np.inf], np.nan)), decision["n_false_before_last_true"], s=12, alpha=0.7)
    axes[1].set_xlabel("log10 condition number")
    axes[1].set_ylabel("false before last true")
    fig.tight_layout()
    fig.savefig(figure_dir / "diagnostics_cosine_condition.png", dpi=160)
    plt.close(fig)


def input_hashes(paths: Iterable[Path]) -> dict[str, str]:
    return {str(path): _sha256(path) for path in paths if path.exists() and path.is_file()}


def run_wp_t1(args: argparse.Namespace) -> dict[str, object]:
    root = Path(args.repo_root).resolve()
    support_path = root / "studies" / "regression" / "phase_c_support.json"
    benchmark_path = root / "benchmarks" / "data" / "strogatz_extended.json"
    export_dir = root / "outputs" / "phase_c_trajectory_hashes" / "wp_c4c" / "trajectory_export"
    basis_name, supports = load_exact_supports(support_path)
    if basis_name != BASIS_NAME:
        raise ValueError(f"unexpected basis name: {basis_name}")
    verify_basis_consistency(supports)
    benchmark = load_benchmark(benchmark_path)
    trajectories = load_exported_trajectories(export_dir, [int(item["system_id"]) for item in supports])
    records = run_records(supports, benchmark, trajectories)
    summary, nulls = summarize_outputs(records)
    gate = gate_decision(pd.DataFrame(records), nulls)
    config = {
        "study_id": STUDY_ID,
        "basis_name": BASIS_NAME,
        "trajectory_source": "campaign_export",
        "noise_seeds": NOISE_SEEDS,
        "null_seed": NULL_SEED,
        "permutation_seed": PERMUTATION_SEED,
        "singular_relative_threshold": SINGULAR_RELATIVE_THRESHOLD,
        "degenerate_std_tol": DEGENERATE_STD_TOL,
        "random_permutations_per_equation": RANDOM_PERMUTATIONS,
        "configuration_hash": hashlib.sha256(json.dumps(
            {
                "signals": ["weak", "fd"],
                "methods": ["marginal", "forward"],
                "sigma_rel": [0.0, 0.01, 0.05],
                "ic_strategy": ["ic1", "ic2", "ic1_ic2"],
                "noise_seeds": NOISE_SEEDS,
            },
            sort_keys=True,
        ).encode("utf-8")).hexdigest(),
        "input_hashes": input_hashes([support_path, benchmark_path, export_dir / "trajectory_manifest.csv"]),
    }
    data_dir = root / "analysis" / "data" / STUDY_ID
    figure_dir = root / "analysis" / "figures" / STUDY_ID
    write_outputs(records, summary, nulls, gate, data_dir, figure_dir, config)
    return {
        "records": len(records),
        "summary_rows": len(summary),
        "null_rows": len(nulls),
        "gate": gate,
        "data_dir": str(data_dir),
        "figure_dir": str(figure_dir),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run WP-T1 trajectory-derived term relevance study.")
    parser.add_argument("--repo-root", default=str(repo_root()))
    return parser


def main(argv: list[str] | None = None) -> None:
    result = run_wp_t1(build_parser().parse_args(argv))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
