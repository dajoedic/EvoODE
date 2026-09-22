from __future__ import annotations

import argparse
import hashlib
import json
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


STUDY_ID = "wp_t1c_prior_generator"
SIGNALS = ("weak", "fd")
METHODS = ("forward", "stlsq_path")
IC_STRATEGIES = ("ic1", "ic2")
SIGMA_REPLICATES = {0.0: [0], 0.01: [1, 2, 3, 4, 5], 0.05: [1, 2, 3, 4, 5]}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run WP-T1c prior-generator ranking comparison.")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--limit-systems", default="", help="Comma-separated system ids for smoke tests.")
    return parser.parse_args()


def parse_limit(text: str) -> set[int] | None:
    if not text.strip():
        return None
    return {int(piece.strip()) for piece in text.split(",") if piece.strip()}


def add_noise_by_replicate(state: np.ndarray, sigma_rel: float, replicate: int, ic: int) -> np.ndarray:
    if sigma_rel == 0.0:
        return np.array(state, copy=True)
    return tr.add_relative_noise(state, sigma_rel, tr.NOISE_SEEDS[replicate - 1] + ic)


def ranking_with_metadata(A: np.ndarray, y: np.ndarray, method: str) -> tuple[list[int], np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    A_std, y_centered, _means, _stds, degenerate = tr.standardize_design(A, y, explicit_intercept=True)
    if method == "forward":
        order, scores = tr.rank_forward(A_std, y_centered, degenerate)
        metadata: dict[str, Any] = {}
    elif method == "stlsq_path":
        order, scores, metadata = tr.stlsq_path(A_std, y_centered, tr.STLSQ_THRESHOLD_GRID)
    else:
        raise ValueError(method)
    return order, scores, degenerate, A_std, metadata


def build_records(
    support_systems: list[dict[str, Any]],
    benchmark: dict[int, dict[str, Any]],
    trajectories: dict[tuple[int, int], tr.Trajectory],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for system in support_systems:
        system_id = int(system["system_id"])
        dim = int(system["dim"])
        terms = tr.phasec_basis(dim)
        candidate_names = [term.name for term in terms]
        substituted = list(benchmark[system_id]["substituted"][0])
        equation_meta = []
        for eq_idx0, support_terms in enumerate(system["support_terms"]):
            true_idxs0 = {candidate_names.index(str(name)) for name in support_terms}
            false_idxs0 = set(range(len(terms))) - true_idxs0
            coeffs = tr.coefficient_map(str(substituted[eq_idx0]), terms)
            equation_meta.append((eq_idx0, list(support_terms), true_idxs0, false_idxs0, coeffs))

        for sigma_rel, replicates in SIGMA_REPLICATES.items():
            for replicate in replicates:
                noisy = {
                    ic: add_noise_by_replicate(trajectories[(system_id, ic)].state, sigma_rel, replicate, ic)
                    for ic in (1, 2)
                }
                for ic_strategy in IC_STRATEGIES:
                    ic = 1 if ic_strategy == "ic1" else 2
                    time = trajectories[(system_id, ic)].time
                    state = noisy[ic]
                    sha = trajectories[(system_id, ic)].sha256
                    for eq_idx0, support_terms, true_idxs0, false_idxs0, coeffs in equation_meta:
                        for signal in SIGNALS:
                            A, y, raw_phi = tr.build_design(time, state, eq_idx0, signal, terms)
                            for method in METHODS:
                                order, scores, degenerate, A_std, metadata = ranking_with_metadata(A, y, method)
                                ranks = [0] * len(order)
                                for rank, idx in enumerate(order, start=1):
                                    ranks[idx] = rank
                                metric = tr.metrics_from_order(order, true_idxs0)
                                diag = tr.matrix_diagnostics(A_std, raw_phi, true_idxs0, false_idxs0, coeffs)
                                record = {
                                    "system_id": system_id,
                                    "system_name": str(benchmark[system_id].get("eq_description", f"system {system_id}")),
                                    "dimension": dim,
                                    "equation_idx": eq_idx0 + 1,
                                    "equation_key": f"{system_id}:{eq_idx0 + 1}",
                                    "ic_strategy": ic_strategy,
                                    "signal": signal,
                                    "ranking_method": method,
                                    "sigma_rel": sigma_rel,
                                    "noise_replicate": replicate,
                                    "noise_seed": "" if sigma_rel == 0.0 else tr.NOISE_SEEDS[replicate - 1] + ic,
                                    "basis_name": tr.BASIS_NAME,
                                    "library_size": len(terms),
                                    "true_support_terms": support_terms,
                                    "true_support_size": len(true_idxs0),
                                    "candidate_names": candidate_names,
                                    "candidate_scores": [None if not np.isfinite(x) else float(x) for x in scores],
                                    "candidate_ranks": ranks,
                                    "stlsq_threshold_grid": metadata.get("threshold_grid", ""),
                                    "stlsq_dropout_threshold": metadata.get("dropout_threshold", ""),
                                    "stlsq_active_counts": metadata.get("active_counts", ""),
                                    **metric,
                                    **diag,
                                    "degenerate_column_count": int(np.sum(degenerate)),
                                    "degenerate_columns": [candidate_names[i] for i, flag in enumerate(degenerate) if flag],
                                    "trajectory_source": "campaign_export",
                                    "trajectory_sha256": sha,
                                }
                                records.append(record)
    return records


def summarize(records: pd.DataFrame) -> pd.DataFrame:
    keys = ["signal", "ranking_method", "sigma_rel", "noise_replicate", "ic_strategy", "dimension"]
    rows: list[dict[str, Any]] = []
    for group_key, group in records.groupby(keys, dropna=False):
        values = group["n_false_before_last_true"].to_numpy(dtype=float)
        row = dict(zip(keys, group_key))
        row["n_equations"] = int(len(group))
        for q in tr.QUANTILES:
            row[f"q{int(q * 100):03d}"] = float(np.quantile(values, q))
        for threshold in tr.THRESHOLDS:
            row[f"le_{threshold}_count"] = int(np.sum(values <= threshold))
            row[f"le_{threshold}_rate"] = float(np.mean(values <= threshold))
        rows.append(row)
    return pd.DataFrame(rows)


def paired_comparison(records: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["signal", "sigma_rel", "noise_replicate", "ic_strategy", "dimension", "system_id", "equation_idx"]
    wide = records.pivot_table(
        index=key_cols,
        columns="ranking_method",
        values="n_false_before_last_true",
        aggfunc="first",
    ).reset_index()
    wide["diff_stlsq_minus_forward"] = wide["stlsq_path"] - wide["forward"]
    rows: list[dict[str, Any]] = []
    group_cols = ["signal", "sigma_rel", "noise_replicate", "ic_strategy", "dimension"]
    for keys, group in wide.groupby(group_cols, dropna=False):
        row = dict(zip(group_cols, keys))
        diff = group["diff_stlsq_minus_forward"].to_numpy(dtype=float)
        row.update(
            {
                "n_pairs": int(len(group)),
                "forward_median": float(group["forward"].median()),
                "stlsq_path_median": float(group["stlsq_path"].median()),
                "forward_le_3_count": int(np.sum(group["forward"].to_numpy(dtype=float) <= 3)),
                "forward_le_3_rate": float(np.mean(group["forward"].to_numpy(dtype=float) <= 3)),
                "stlsq_path_le_3_count": int(np.sum(group["stlsq_path"].to_numpy(dtype=float) <= 3)),
                "stlsq_path_le_3_rate": float(np.mean(group["stlsq_path"].to_numpy(dtype=float) <= 3)),
                "diff_q000": float(np.quantile(diff, 0.0)),
                "diff_q010": float(np.quantile(diff, 0.10)),
                "diff_q025": float(np.quantile(diff, 0.25)),
                "diff_q050": float(np.quantile(diff, 0.50)),
                "diff_q075": float(np.quantile(diff, 0.75)),
                "diff_q090": float(np.quantile(diff, 0.90)),
                "diff_q100": float(np.quantile(diff, 1.0)),
                "diff_le_0_count": int(np.sum(diff <= 0)),
                "diff_le_0_rate": float(np.mean(diff <= 0)),
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def _candidate_values(records: pd.DataFrame, ic_strategy: str) -> dict[str, Any]:
    cell = records[
        records["signal"].eq("weak")
        & records["sigma_rel"].eq(0.0)
        & records["noise_replicate"].eq(0)
        & records["ic_strategy"].eq(ic_strategy)
        & records["dimension"].isin([2, 3])
    ].copy()
    values: dict[str, Any] = {}
    for method, group in cell.groupby("ranking_method"):
        arr = group["n_false_before_last_true"].to_numpy(dtype=float)
        values[str(method)] = {
            "median_n_false_before_last_true": float(np.median(arr)),
            "le_3_count": int(np.sum(arr <= 3)),
            "le_3_rate": float(np.mean(arr <= 3)),
            "n_equations": int(len(group)),
            "n_systems": int(group["system_id"].nunique()),
        }
    return values


def winner_for(values: dict[str, Any]) -> str:
    forward = values["forward"]
    stlsq = values["stlsq_path"]
    if stlsq["median_n_false_before_last_true"] < forward["median_n_false_before_last_true"]:
        return "stlsq_path"
    if forward["median_n_false_before_last_true"] < stlsq["median_n_false_before_last_true"]:
        return "forward"
    if stlsq["le_3_rate"] > forward["le_3_rate"]:
        return "stlsq_path"
    if forward["le_3_rate"] > stlsq["le_3_rate"]:
        return "forward"
    return "no_winner"


def generator_decision(records: pd.DataFrame) -> dict[str, Any]:
    primary = _candidate_values(records, "ic1")
    replication = _candidate_values(records, "ic2")
    primary_winner = winner_for(primary)
    replication_winner = winner_for(replication)
    same_direction = bool(primary_winner != "no_winner" and primary_winner == replication_winner)
    final = primary_winner if same_direction else "no_winner"
    prioritizer = final if final != "no_winner" else "forward"
    return {
        "decision_cell": {
            "signal": "weak",
            "sigma_rel": 0.0,
            "noise_replicate": 0,
            "ic_strategy": "ic1",
            "stratum": "dimension 2 and dimension 3",
            "systems": primary["forward"]["n_systems"],
            "equations": primary["forward"]["n_equations"],
        },
        "candidate_values": primary,
        "replication_condition": {
            "ic_strategy": "ic2",
            "candidate_values": replication,
            "primary_winner": primary_winner,
            "ic2_winner": replication_winner,
            "same_direction": same_direction,
        },
        "winner": final,
        "prioritizer_for_wp_t2a": prioritizer,
        "rule": (
            "Winner is the method with smaller median n_false_before_last_true in weak/sigma=0/ic1 "
            "over dimensions 2 and 3. If medians tie, higher share <= 3 wins. If that also ties, "
            "there is no winner. The direction must replicate on ic2; otherwise there is no winner. "
            "When there is no winner, forward remains the incumbent prioritizer."
        ),
    }


def write_figures(records: pd.DataFrame, figure_dir: Path) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    key_cols = ["signal", "sigma_rel", "noise_replicate", "ic_strategy", "dimension", "system_id", "equation_idx"]
    wide = records.pivot_table(
        index=key_cols,
        columns="ranking_method",
        values="n_false_before_last_true",
        aggfunc="first",
    ).reset_index()
    wide["diff_stlsq_minus_forward"] = wide["stlsq_path"] - wide["forward"]
    clean = wide[wide["sigma_rel"].eq(0.0) & wide["noise_replicate"].eq(0)]
    fig, axes = plt.subplots(2, 4, figsize=(14, 6), sharey=True)
    for row_idx, signal in enumerate(SIGNALS):
        for ax, dim in zip(axes[row_idx], [1, 2, 3, 4]):
            sub = clean[clean["signal"].eq(signal) & clean["dimension"].eq(dim)]
            data = [
                sub[sub["ic_strategy"].eq("ic1")]["diff_stlsq_minus_forward"].to_numpy(dtype=float),
                sub[sub["ic_strategy"].eq("ic2")]["diff_stlsq_minus_forward"].to_numpy(dtype=float),
            ]
            ax.boxplot(data, tick_labels=["ic1", "ic2"], showfliers=True)
            ax.axhline(0.0, color="black", linewidth=1)
            ax.set_title(f"{signal}, dim {dim}")
            ax.set_ylabel("STLSQ - forward")
    fig.tight_layout()
    fig.savefig(figure_dir / "paired_difference_by_dimension.png", dpi=160)
    plt.close(fig)


def jsonable_frame(records: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(tr._jsonable_records(records))


def run(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    support_path = root / "studies" / "regression" / "phase_c_support.json"
    benchmark_path = root / "benchmarks" / "data" / "strogatz_extended.json"
    export_dir = root / "outputs" / "phase_c_trajectory_hashes" / "wp_c4c" / "trajectory_export"
    basis_name, supports = tr.load_exact_supports(support_path)
    if basis_name != tr.BASIS_NAME:
        raise ValueError(f"unexpected basis name: {basis_name}")
    tr.verify_basis_consistency(supports)
    limit = parse_limit(args.limit_systems)
    if limit is not None:
        supports = [item for item in supports if int(item["system_id"]) in limit]
    benchmark = tr.load_benchmark(benchmark_path)
    trajectories = tr.load_exported_trajectories(export_dir, [int(item["system_id"]) for item in supports])

    records = build_records(supports, benchmark, trajectories)
    frame = pd.DataFrame(records)
    summary = summarize(frame)
    comparison = paired_comparison(frame)
    decision = generator_decision(frame)
    threshold_coverage = (
        frame[frame["ranking_method"].eq("stlsq_path")][["dimension", "signal", "ic_strategy", "sigma_rel", "noise_replicate", "stlsq_active_counts"]]
        .copy()
    )
    threshold_coverage["stlsq_active_counts"] = threshold_coverage["stlsq_active_counts"].apply(
        lambda value: json.dumps(value, separators=(",", ":"))
    )
    threshold_coverage = threshold_coverage.drop_duplicates()

    data_dir = root / "analysis" / "data" / STUDY_ID
    figure_dir = root / "analysis" / "figures" / STUDY_ID
    data_dir.mkdir(parents=True, exist_ok=True)
    jsonable_frame(records).to_csv(data_dir / "records.csv", index=False)
    summary.to_csv(data_dir / "aggregate_by_configuration_dimension.csv", index=False)
    comparison.to_csv(data_dir / "paired_method_comparison_by_dimension.csv", index=False)
    threshold_coverage.to_csv(data_dir / "stlsq_threshold_coverage.csv", index=False)
    (data_dir / "generator_decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    metadata = {
        "study_id": STUDY_ID,
        "basis_name": tr.BASIS_NAME,
        "signals": SIGNALS,
        "methods": METHODS,
        "sigma_replicates": SIGMA_REPLICATES,
        "ic_strategies": IC_STRATEGIES,
        "noise_seeds": tr.NOISE_SEEDS,
        "stlsq_threshold_grid": tr.STLSQ_THRESHOLD_GRID,
        "stlsq_max_iterations": tr.STLSQ_MAX_ITERATIONS,
        "stlsq_tie_break_rule": (
            "Ties at the same dropout threshold are resolved by the absolute standardized coefficient "
            "at the last threshold where both terms were active, then by ascending basis index."
        ),
        "explicit_intercept": True,
        "configuration_hash": hashlib.sha256(
            json.dumps(
                {
                    "signals": SIGNALS,
                    "methods": METHODS,
                    "sigma_replicates": SIGMA_REPLICATES,
                    "ic_strategies": IC_STRATEGIES,
                    "noise_seeds": tr.NOISE_SEEDS,
                    "stlsq_threshold_grid": tr.STLSQ_THRESHOLD_GRID,
                    "explicit_intercept": True,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest(),
        "input_hashes": tr.input_hashes([support_path, benchmark_path, export_dir / "trajectory_manifest.csv"]),
    }
    (data_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_figures(frame, figure_dir)
    return {
        "records": len(frame),
        "summary_rows": len(summary),
        "comparison_rows": len(comparison),
        "decision": decision,
        "data_dir": str(data_dir),
        "figure_dir": str(figure_dir),
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
