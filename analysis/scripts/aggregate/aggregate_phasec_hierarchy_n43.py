import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_variance_weighted_r2 import load_variance_weights, parse_json_list  # noqa: E402
from scripts.aggregate.run_phasec_noise_sindy_baselines import build_summary  # noqa: E402
from scripts.aggregate.run_phasec_sindy_baseline import (  # noqa: E402
    C1_VARIANT,
    R2_THRESHOLD,
    as_bool,
    load_true_threeway,
    require_columns,
)


DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "phase_c_campaign_221a3a7" / "agg" / "hierarchy_n43b"
DEFAULT_C6_SINDY_DIR = REPO_ROOT / "outputs" / "c6_sindy_baselines_5dd1df8"
DEFAULT_C6_MERGED_DIR = DEFAULT_C6_SINDY_DIR / "merged"
DEFAULT_C4C_SINDY_DETAILS = (
    REPO_ROOT / "analysis" / "data" / "paper1_phaseC_v1" / "phasec_sindy_baseline_wp_c4c_export" / "details.csv"
)
DEFAULT_OLD_SINDY_DETAILS = REPO_ROOT / "analysis" / "data" / "paper1_phaseC_v1" / "phasec_sindy_baseline" / "details.csv"
TRUE_BASIS = "staged_polynomial_basis_with_constant"
FEASIBLE_BOUND_10 = {system_id: (system_id not in {54, 55, 56, 57, 58, 59}) for system_id in range(1, 64)}
RATE_COLUMNS = [
    "reconstruction_r2_arithmetic_gt_0_9",
    "reconstruction_r2_variance_weighted_gt_0_9",
    "generalization_r2_arithmetic_gt_0_9",
    "generalization_r2_variance_weighted_gt_0_9",
    "raw_exact_support_match",
    "pruned_exact_support_match",
]
CONTINUOUS_COLUMNS = [
    "reconstruction_r2_arithmetic",
    "reconstruction_r2_variance_weighted",
    "generalization_r2_arithmetic",
    "generalization_r2_variance_weighted",
    "structural_f1_pruned",
    "structural_precision_pruned",
    "structural_recall_pruned",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate Phase-C methods under the plan 9.3 hierarchy.")
    parser.add_argument("--evogrow-registry", default="analysis/data/paper1_phaseC_v1/final_2026-10-05/phasec_analysis_registry_c1.csv")
    parser.add_argument("--evogrow-generalization", default="outputs/wp_n5_ic_generalization_phase_c/shard_001_of_001/results.jsonl")
    parser.add_argument("--sindy-details", default=str(DEFAULT_C6_MERGED_DIR / "details.csv"))
    parser.add_argument("--sindy-shards-dir", default=str(DEFAULT_C6_SINDY_DIR))
    parser.add_argument("--sindy-merged-dir", default=str(DEFAULT_C6_MERGED_DIR))
    parser.add_argument("--sindy-c4c-details", default=str(DEFAULT_C4C_SINDY_DETAILS))
    parser.add_argument("--sindy-old-details", default=str(DEFAULT_OLD_SINDY_DETAILS))
    parser.add_argument(
        "--odeformer-reference",
        default="analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records_structure_recomputed.csv",
    )
    parser.add_argument(
        "--odeformer-candidate",
        default="analysis/data/paper1_phaseC_v1/odeformer_baseline/candidate_orion_8e0e699/records_structure_recomputed.csv",
    )
    parser.add_argument(
        "--representability-threeway",
        default="analysis/data/paper1_phaseC_v1/representability_threeway/representability_threeway_by_system.csv",
    )
    parser.add_argument("--trajectory-export", default="outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export")
    parser.add_argument("--sindy-control-summary", default="outputs/phase_c_campaign_221a3a7/agg/sindy_n31/phasec_sindy_paired_summary.csv")
    parser.add_argument(
        "--odeformer-control-summary",
        default="outputs/phase_c_campaign_221a3a7/agg/odeformer_n40_reference/phasec_odeformer_paired_summary.csv",
    )
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args()


def resolve(path: str | Path) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def fail(message: str) -> None:
    raise ValueError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                try:
                    rows.append(json.loads(text))
                except json.JSONDecodeError as exc:
                    fail(f"{path} line {line_number} is not valid JSON: {exc}")
        if not rows:
            fail(f"{path} contains no JSON records")
        return pd.DataFrame(rows)
    return pd.read_csv(path)


def merge_sindy_shards(shards_dir: Path, merged_dir: Path) -> dict[str, Path]:
    shard_paths = sorted(shards_dir.glob("shard_*/details.csv"))
    if not shard_paths:
        fail(f"no SINDy shard details found under {shards_dir}")
    frames = []
    for path in shard_paths:
        frame = pd.read_csv(path)
        frame["source_shard"] = path.parent.name
        frames.append(frame)
    details = pd.concat(frames, ignore_index=True, sort=False)
    cell_keys = ["system_id", "source_initial_condition_set", "noise_sigma", "subsample_rho", "noise_realization"]
    run_keys = cell_keys + ["method", "library_id"]
    duplicate = details.duplicated(run_keys, keep=False)
    if bool(duplicate.any()):
        fail(f"C-6 SINDy shards contain duplicate run keys: {details.loc[duplicate, run_keys].head().to_dict('records')}")
    n_cells = int(details[cell_keys].drop_duplicates().shape[0])
    if n_cells != 4536:
        fail(f"C-6 SINDy merge expected 4,536 distinct cells, found {n_cells}")
    counts = details.groupby(cell_keys, dropna=False).agg(
        method_count=("method", "nunique"), configuration_count=("library_id", "nunique"), row_count=("library_id", "size")
    )
    bad = counts[(counts["method_count"] != 2) | (counts["configuration_count"] != 10) | (counts["row_count"] != 20)]
    if len(bad):
        fail(f"C-6 SINDy merge has incomplete configurations for {len(bad)} cells")
    checks = []
    for path in sorted(shards_dir.glob("shard_*/export_checks.csv")):
        frame = pd.read_csv(path)
        frame["source_shard"] = path.parent.name
        checks.append(frame)
    export_checks = pd.concat(checks, ignore_index=True, sort=False) if checks else pd.DataFrame()
    if export_checks.empty or "hash_verified" not in export_checks.columns:
        fail("C-6 SINDy export hash checks are missing")
    if not export_checks["hash_verified"].map(as_bool).all():
        fail("C-6 SINDy export hash check failed in at least one row")
    merged_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "details": merged_dir / "details.csv",
        "summary": merged_dir / "summary.csv",
        "export_checks": merged_dir / "export_checks.csv",
        "merge_checks": merged_dir / "merge_checks.csv",
    }
    details.to_csv(outputs["details"], index=False)
    build_summary(details).to_csv(outputs["summary"], index=False)
    export_checks.to_csv(outputs["export_checks"], index=False)
    pd.DataFrame(
        [
            {
                "n_shards": len(shard_paths),
                "n_rows": len(details),
                "n_distinct_cells": n_cells,
                "duplicate_run_keys": int(duplicate.sum()),
                "hash_check_rows": len(export_checks),
                "hash_check_passed_rows": int(export_checks["hash_verified"].map(as_bool).sum()),
                "cells_with_all_configurations": n_cells - len(bad),
            }
        ]
    ).to_csv(outputs["merge_checks"], index=False)
    return outputs


def true_classes(path: Path) -> pd.DataFrame:
    frame = load_true_threeway(path)
    return frame.rename(columns={"phasec_true_threeway_class": "threeway_class"})[
        ["system_id", "threeway_class", "phasec_true_threeway_basis_name"]
    ]


def attach_classes(frame: pd.DataFrame, classes: pd.DataFrame) -> pd.DataFrame:
    merged = frame.merge(classes, on="system_id", how="left", validate="many_to_one")
    if merged["threeway_class"].isna().any():
        missing = sorted(int(value) for value in merged.loc[merged["threeway_class"].isna(), "system_id"].unique())
        fail(f"missing three-way classes for systems: {missing}")
    merged["is_exact_system"] = merged["threeway_class"].astype(str).eq("fully_representable")
    merged["feasible_bound_10"] = merged["system_id"].map(lambda value: FEASIBLE_BOUND_10.get(int(value), False))
    return merged


def finite_or_nan(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result if math.isfinite(result) else math.nan


def parse_r2_list(value: Any, column: str, row_number: int) -> list[float]:
    if isinstance(value, (list, tuple, np.ndarray)):
        values = [float(item) for item in value]
        if not values or not all(math.isfinite(item) for item in values):
            fail(f"{column} must be a non-empty finite numeric array at row {row_number}")
        return values
    return parse_json_list(value, column, row_number)


def pass_r2(value: Any, diverged: bool = False, available: bool = True) -> bool:
    value = finite_or_nan(value)
    return bool(available and not diverged and math.isfinite(value) and value > R2_THRESHOLD)


def prune_structure_for_surrogates(frame: pd.DataFrame) -> pd.DataFrame:
    structure_columns = [
        "raw_exact_support_match",
        "pruned_exact_support_match",
        "structural_f1_pruned",
        "structural_precision_pruned",
        "structural_recall_pruned",
    ]
    surrogate = ~frame["is_exact_system"].astype(bool)
    for column in structure_columns:
        frame[column] = frame[column].astype("object")
        frame.loc[surrogate, column] = np.nan
    return frame


def load_evogrow(registry_path: Path, cells_path: Path, weights: dict[tuple[int, int], np.ndarray], classes: pd.DataFrame) -> pd.DataFrame:
    registry = pd.read_csv(registry_path)
    cells = read_table(cells_path)
    require_columns(
        registry,
        {
            "system_id",
            "system_name",
            "system_dim",
            "variant_slug",
            "condition",
            "use_pretuning",
            "seed",
            "initial_condition_set",
            "r2",
            "r2_by_dim",
            "exact_support_match_raw",
            "exact_support_match_pruned",
            "structural_f1_micro",
            "term_precision_micro",
            "term_recall_micro",
            "total_diverged_solves",
        },
        "EvoGrow registry",
    )
    require_columns(
        cells,
        {
            "system_id",
            "source_initial_condition_set",
            "target_initial_condition_set",
            "direction",
            "seed",
            "reconstruction_r2",
            "reconstruction_diverged_or_nonfinite",
            "generalization_r2",
            "generalization_r2_by_dim",
            "generalization_diverged_or_nonfinite",
        },
        "EvoGrow generalization cells",
    )
    registry = registry[
        (registry["variant_slug"].astype(str) == C1_VARIANT)
        & (registry["condition"].astype(str) == "capped")
        & (~registry["use_pretuning"].map(as_bool))
    ].copy()
    cells = cells[(cells["variant"].astype(str) == C1_VARIANT) & (cells["condition"].astype(str) == "capped")].copy()
    merged = cells.merge(
        registry,
        left_on=["system_id", "seed", "source_initial_condition_set"],
        right_on=["system_id", "seed", "initial_condition_set"],
        how="inner",
        validate="one_to_one",
        suffixes=("", "_record"),
    )
    if len(merged) != len(cells):
        fail(f"EvoGrow registry/cells join incomplete: cells={len(cells)}, joined={len(merged)}")

    rows: list[dict[str, Any]] = []
    for index, row in merged.iterrows():
        system_id = int(row["system_id"])
        source_ic = int(row["source_initial_condition_set"])
        r2_by_dim = parse_r2_list(row["r2_by_dim"], "r2_by_dim", int(index) + 2)
        arithmetic = float(np.mean(r2_by_dim))
        reconstruction_r2 = finite_or_nan(row["reconstruction_r2"])
        if abs(arithmetic - reconstruction_r2) > 1e-12:
            fail(f"EvoGrow reconstruction arithmetic mismatch for system {system_id}, seed {row['seed']}, ic {source_ic}")
        variance_weighted = float(np.average(np.asarray(r2_by_dim, dtype=float), weights=weights[(system_id, source_ic)]))
        generalization_arithmetic = finite_or_nan(row["generalization_r2"])
        generalization_diverged = as_bool(row["generalization_diverged_or_nonfinite"]) or not math.isfinite(generalization_arithmetic)
        if not generalization_diverged:
            gen_r2_by_dim = parse_r2_list(row["generalization_r2_by_dim"], "generalization_r2_by_dim", int(index) + 2)
            gen_arithmetic_from_dims = float(np.mean(gen_r2_by_dim))
            if abs(gen_arithmetic_from_dims - generalization_arithmetic) > 1e-12:
                fail(f"EvoGrow generalization arithmetic mismatch for system {system_id}, seed {row['seed']}, ic {source_ic}")
            gen_variance_weighted = float(
                np.average(np.asarray(gen_r2_by_dim, dtype=float), weights=weights[(system_id, int(row["target_initial_condition_set"]))])
            )
        else:
            if math.isfinite(generalization_arithmetic):
                fail(f"EvoGrow diverged generalization unexpectedly has finite R2 for system {system_id}, seed {row['seed']}")
            gen_variance_weighted = math.nan
        reconstruction_diverged = as_bool(row["reconstruction_diverged_or_nonfinite"])
        rows.append(
            {
                "method": "EvoGrow",
                "method_family": "EvoGrow",
                "configuration": "C-1_capped",
                "arm": "canonical",
                "system_id": system_id,
                "system_name": row["system_name"],
                "dimension": int(row["dimension"]),
                "direction": row["direction"],
                "source_initial_condition_set": source_ic,
                "target_initial_condition_set": int(row["target_initial_condition_set"]),
                "run_id": int(row["seed"]),
                "seed": int(row["seed"]),
                "repetition": 0,
                "noise_level": 0.0,
                "subsampling_ratio": 1.0,
                "realization": 0,
                "initial_condition_set": source_ic,
                "reconstruction_r2_arithmetic": reconstruction_r2,
                "reconstruction_r2_arithmetic_available": True,
                "reconstruction_r2_variance_weighted": variance_weighted,
                "reconstruction_r2_variance_weighted_available": True,
                "generalization_r2_arithmetic": generalization_arithmetic,
                "generalization_r2_arithmetic_available": True,
                "generalization_r2_variance_weighted": gen_variance_weighted,
                "generalization_r2_variance_weighted_available": not generalization_diverged,
                "reconstruction_diverged_or_nonfinite": reconstruction_diverged,
                "generalization_diverged_or_nonfinite": generalization_diverged,
                "divergence_flag": bool(reconstruction_diverged or generalization_diverged),
                "raw_exact_support_match": as_bool(row["exact_support_match_raw"]),
                "pruned_exact_support_match": as_bool(row["exact_support_match_pruned"]),
                "structural_f1_pruned": finite_or_nan(row["structural_f1_micro"]),
                "structural_precision_pruned": finite_or_nan(row["term_precision_micro"]),
                "structural_recall_pruned": finite_or_nan(row["term_recall_micro"]),
            }
        )
    frame = attach_classes(pd.DataFrame(rows), classes)
    return add_pass_columns(prune_structure_for_surrogates(frame))


def assert_clean_realization_identity(details: pd.DataFrame) -> pd.DataFrame:
    clean = details[
        (details["method"].astype(str) == "sindy")
        & (pd.to_numeric(details["noise_sigma"], errors="coerce") == 0.0)
        & (pd.to_numeric(details["subsample_rho"], errors="coerce") == 0.0)
    ].copy()
    identity_columns = [
        "fit_status",
        "reconstruction_integration_status",
        "generalization_integration_status",
        "reconstruction_diverged_or_nonfinite",
        "generalization_diverged_or_nonfinite",
        "reconstruction_r2_arithmetic_mean_gt_0_9",
        "reconstruction_r2_variance_weighted_gt_0_9",
        "generalization_r2_arithmetic_mean_gt_0_9",
        "generalization_r2_variance_weighted_gt_0_9",
        "sindy_structure_hit_raw",
        "sindy_structure_hit_pruned",
        "active_terms_raw",
        "active_terms_pruned",
        "sindy_structure_precision_pruned",
        "sindy_structure_recall_pruned",
        "sindy_structure_f1_pruned",
    ]
    group_columns = ["method", "library_id", "system_id", "source_initial_condition_set", "target_initial_condition_set"]
    for keys, group in clean.groupby(group_columns, dropna=False, sort=True):
        if set(pd.to_numeric(group["noise_realization"], errors="coerce").astype(int)) != {1, 2, 3}:
            fail(f"C-6 clean SINDy group must contain realizations 1, 2 and 3: {keys}")
        first = group.sort_values("noise_realization").iloc[0]
        for _, row in group.iterrows():
            for column in identity_columns:
                left = first[column]
                right = row[column]
                if pd.isna(left) and pd.isna(right):
                    continue
                if isinstance(left, (float, np.floating)) or isinstance(right, (float, np.floating)):
                    if np.isclose(float(left), float(right), rtol=1e-12, atol=1e-12, equal_nan=True):
                        continue
                if str(left) != str(right):
                    fail(f"C-6 clean SINDy realizations differ for {keys}, column {column}")
    return clean[pd.to_numeric(clean["noise_realization"], errors="coerce").astype(int) == 1].copy()


def clean_sindy_realization_deltas(details: pd.DataFrame) -> pd.DataFrame:
    clean = details[
        (details["method"].astype(str) == "sindy")
        & (pd.to_numeric(details["noise_sigma"], errors="coerce") == 0.0)
        & (pd.to_numeric(details["subsample_rho"], errors="coerce") == 0.0)
    ].copy()
    rows: list[dict[str, Any]] = []
    value_columns = [
        "reconstruction_r2_arithmetic_mean",
        "reconstruction_r2_variance_weighted",
        "generalization_r2_arithmetic_mean",
        "generalization_r2_variance_weighted",
    ]
    group_columns = ["library_id", "system_id", "source_initial_condition_set", "target_initial_condition_set"]
    for keys, group in clean.groupby(group_columns, dropna=False, sort=True):
        row = dict(zip(group_columns, keys))
        row["n_realizations"] = int(group["noise_realization"].nunique())
        for column in value_columns:
            values = pd.to_numeric(group[column], errors="coerce")
            row[f"{column}_range"] = float(values.max() - values.min()) if values.notna().any() else math.nan
        rows.append(row)
    return pd.DataFrame(rows)


def load_sindy_wide(details: pd.DataFrame, classes: pd.DataFrame) -> pd.DataFrame:
    require_columns(
        details,
        {
            "method",
            "library_id",
            "system_id",
            "system_name",
            "dimension",
            "source_initial_condition_set",
            "target_initial_condition_set",
            "noise_sigma",
            "subsample_rho",
            "noise_realization",
            "fit_status",
            "reconstruction_integration_status",
            "generalization_integration_status",
            "reconstruction_diverged_or_nonfinite",
            "generalization_diverged_or_nonfinite",
            "reconstruction_r2_arithmetic_mean",
            "reconstruction_r2_variance_weighted",
            "generalization_r2_arithmetic_mean",
            "generalization_r2_variance_weighted",
            "sindy_structure_hit_raw",
            "sindy_structure_hit_pruned",
            "sindy_structure_precision_pruned",
            "sindy_structure_recall_pruned",
            "sindy_structure_f1_pruned",
        },
        "C-6 SINDy details",
    )
    details = assert_clean_realization_identity(details)
    rows: list[dict[str, Any]] = []
    for _, row in details.iterrows():
        rec_diverged = (
            as_bool(row["reconstruction_diverged_or_nonfinite"])
            or str(row["fit_status"]) != "success"
            or str(row["reconstruction_integration_status"]) != "success"
        )
        gen_diverged = (
            as_bool(row["generalization_diverged_or_nonfinite"])
            or str(row["fit_status"]) != "success"
            or str(row["generalization_integration_status"]) != "success"
        )
        if str(row["method"]) != "sindy":
            continue
        method = "SINDy"
        rows.append(
            {
                "method": method,
                "method_family": method,
                "configuration": str(row["library_id"]),
                "arm": "canonical",
                "system_id": int(row["system_id"]),
                "system_name": row["system_name"],
                "dimension": int(row["dimension"]),
                "direction": f"IC{int(row['source_initial_condition_set'])}_to_IC{int(row['target_initial_condition_set'])}",
                "source_initial_condition_set": int(row["source_initial_condition_set"]),
                "target_initial_condition_set": int(row["target_initial_condition_set"]),
                "run_id": 0,
                "seed": 0,
                "repetition": 0,
                "noise_level": 0.0,
                "subsampling_ratio": 1.0,
                "realization": 1,
                "initial_condition_set": int(row["source_initial_condition_set"]),
                "reconstruction_r2_arithmetic": finite_or_nan(row["reconstruction_r2_arithmetic_mean"]),
                "reconstruction_r2_arithmetic_available": True,
                "reconstruction_r2_variance_weighted": finite_or_nan(row["reconstruction_r2_variance_weighted"]),
                "reconstruction_r2_variance_weighted_available": True,
                "generalization_r2_arithmetic": finite_or_nan(row["generalization_r2_arithmetic_mean"]),
                "generalization_r2_arithmetic_available": True,
                "generalization_r2_variance_weighted": finite_or_nan(row["generalization_r2_variance_weighted"]),
                "generalization_r2_variance_weighted_available": True,
                "reconstruction_diverged_or_nonfinite": rec_diverged,
                "generalization_diverged_or_nonfinite": gen_diverged,
                "divergence_flag": bool(rec_diverged or gen_diverged),
                "raw_exact_support_match": as_bool(row["sindy_structure_hit_raw"]),
                "pruned_exact_support_match": as_bool(row["sindy_structure_hit_pruned"]),
                "structural_f1_pruned": finite_or_nan(row["sindy_structure_f1_pruned"]),
                "structural_precision_pruned": finite_or_nan(row["sindy_structure_precision_pruned"]),
                "structural_recall_pruned": finite_or_nan(row["sindy_structure_recall_pruned"]),
            }
        )
    frame = attach_classes(pd.DataFrame(rows), classes)
    return add_pass_columns(prune_structure_for_surrogates(frame))


def load_sindy(details_path: Path, classes: pd.DataFrame) -> pd.DataFrame:
    details = pd.read_csv(details_path)
    if "reconstruction_r2_arithmetic_mean" in details.columns:
        return load_sindy_wide(details, classes)
    require_columns(
        details,
        {
            "library_id",
            "system_id",
            "system_name",
            "dimension",
            "source_initial_condition_set",
            "target_initial_condition_set",
            "direction",
            "regime",
            "r2",
            "diverged_or_nonfinite",
            "valid_for_analysis",
            "sindy_structure_hit_raw",
            "sindy_structure_hit_pruned",
        },
        "SINDy details",
    )
    rows: list[dict[str, Any]] = []
    group_columns = ["library_id", "system_id", "source_initial_condition_set", "target_initial_condition_set", "direction"]
    for keys, group in details.groupby(group_columns, dropna=False, sort=True):
        library_id, system_id, source_ic, target_ic, direction = keys
        rec = group[group["regime"].astype(str) == "reconstruction"]
        gen = group[group["regime"].astype(str) == "generalization"]
        if len(rec) != 1 or len(gen) != 1:
            fail(f"SINDy group must have one reconstruction and one generalization row: {keys}")
        rec_row = rec.iloc[0]
        gen_row = gen.iloc[0]
        rec_diverged = as_bool(rec_row["diverged_or_nonfinite"]) or not as_bool(rec_row["valid_for_analysis"])
        gen_diverged = as_bool(gen_row["diverged_or_nonfinite"]) or not as_bool(gen_row["valid_for_analysis"])
        rows.append(
            {
                "method": "SINDy",
                "method_family": "SINDy",
                "configuration": str(library_id),
                "arm": "canonical",
                "system_id": int(system_id),
                "system_name": rec_row["system_name"],
                "dimension": int(rec_row["dimension"]),
                "direction": direction,
                "source_initial_condition_set": int(source_ic),
                "target_initial_condition_set": int(target_ic),
                "run_id": 0,
                "seed": 0,
                "repetition": 0,
                "noise_level": 0.0,
                "subsampling_ratio": 1.0,
                "realization": 0,
                "initial_condition_set": int(source_ic),
                "reconstruction_r2_arithmetic": finite_or_nan(rec_row["r2"]),
                "reconstruction_r2_arithmetic_available": True,
                "reconstruction_r2_variance_weighted": math.nan,
                "reconstruction_r2_variance_weighted_available": False,
                "generalization_r2_arithmetic": finite_or_nan(gen_row["r2"]),
                "generalization_r2_arithmetic_available": True,
                "generalization_r2_variance_weighted": math.nan,
                "generalization_r2_variance_weighted_available": False,
                "reconstruction_diverged_or_nonfinite": rec_diverged,
                "generalization_diverged_or_nonfinite": gen_diverged,
                "divergence_flag": bool(rec_diverged or gen_diverged),
                "raw_exact_support_match": as_bool(rec_row["sindy_structure_hit_raw"]),
                "pruned_exact_support_match": as_bool(rec_row["sindy_structure_hit_pruned"]),
                "structural_f1_pruned": math.nan,
                "structural_precision_pruned": math.nan,
                "structural_recall_pruned": math.nan,
            }
        )
    frame = attach_classes(pd.DataFrame(rows), classes)
    return add_pass_columns(prune_structure_for_surrogates(frame))


def load_odeformer(path: Path, arm: str, classes: pd.DataFrame) -> pd.DataFrame:
    records = pd.read_csv(path)
    require_columns(
        records,
        {
            "odeformer_config_id",
            "system_id",
            "dimension",
            "fit_initial_condition_set",
            "generalization_initial_condition_set",
            "odeformer_grid_repetition",
            "status",
            "timeout_enforced",
            "reconstruction_status",
            "generalization_status",
            "reconstruction_r2_arithmetic_mean",
            "reconstruction_r2_variance_weighted",
            "generalization_r2_arithmetic_mean",
            "generalization_r2_variance_weighted",
            "structure_hit_raw",
            "structure_hit_pruned",
        },
        f"ODEFormer {arm}",
    )
    rows: list[dict[str, Any]] = []
    for _, row in records.iterrows():
        status_ok = str(row["status"]) == "success" and not as_bool(row["timeout_enforced"])
        rec_diverged = (not status_ok) or str(row["reconstruction_status"]) != "success"
        gen_diverged = (not status_ok) or str(row["generalization_status"]) != "success"
        source_ic = int(row["fit_initial_condition_set"])
        target_ic = int(row["generalization_initial_condition_set"])
        rows.append(
            {
                "method": "ODEFormer",
                "method_family": "ODEFormer",
                "configuration": str(row["odeformer_config_id"]),
                "arm": arm,
                "system_id": int(row["system_id"]),
                "system_name": f"system_{int(row['system_id']):03d}",
                "dimension": int(row["dimension"]),
                "direction": f"IC{source_ic}_to_IC{target_ic}",
                "source_initial_condition_set": source_ic,
                "target_initial_condition_set": target_ic,
                "run_id": int(row["odeformer_grid_repetition"]),
                "seed": 0,
                "repetition": int(row["odeformer_grid_repetition"]),
                "noise_level": 0.0,
                "subsampling_ratio": 1.0,
                "realization": 0,
                "initial_condition_set": source_ic,
                "reconstruction_r2_arithmetic": finite_or_nan(row["reconstruction_r2_arithmetic_mean"]),
                "reconstruction_r2_arithmetic_available": True,
                "reconstruction_r2_variance_weighted": finite_or_nan(row["reconstruction_r2_variance_weighted"]),
                "reconstruction_r2_variance_weighted_available": True,
                "generalization_r2_arithmetic": finite_or_nan(row["generalization_r2_arithmetic_mean"]),
                "generalization_r2_arithmetic_available": True,
                "generalization_r2_variance_weighted": finite_or_nan(row["generalization_r2_variance_weighted"]),
                "generalization_r2_variance_weighted_available": True,
                "reconstruction_diverged_or_nonfinite": rec_diverged,
                "generalization_diverged_or_nonfinite": gen_diverged,
                "divergence_flag": bool(rec_diverged or gen_diverged),
                "raw_exact_support_match": as_bool(row["structure_hit_raw"]),
                "pruned_exact_support_match": as_bool(row["structure_hit_pruned"]),
                "structural_f1_pruned": finite_or_nan(row.get("odeformer_structure_f1_pruned", math.nan)),
                "structural_precision_pruned": finite_or_nan(row.get("odeformer_structure_precision_pruned", math.nan)),
                "structural_recall_pruned": finite_or_nan(row.get("odeformer_structure_recall_pruned", math.nan)),
            }
        )
    frame = attach_classes(pd.DataFrame(rows), classes)
    return add_pass_columns(prune_structure_for_surrogates(frame))


def add_pass_columns(frame: pd.DataFrame) -> pd.DataFrame:
    for regime in ["reconstruction", "generalization"]:
        for aggregation in ["arithmetic", "variance_weighted"]:
            value_column = f"{regime}_r2_{aggregation}"
            available_column = f"{value_column}_available"
            passed = []
            for value, diverged, available in zip(
                frame[value_column],
                frame[f"{regime}_diverged_or_nonfinite"],
                frame[available_column],
                strict=True,
            ):
                passed.append(pass_r2(value, diverged, available) if available else np.nan)
            frame[f"{value_column}_gt_0_9"] = passed
    return frame


def numeric_mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce")
    return float(values.mean()) if values.notna().any() else math.nan


def numeric_median(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce")
    return float(values.median()) if values.notna().any() else math.nan


def direction_level(per_run: pd.DataFrame, extra_keys: list[str] | None = None) -> pd.DataFrame:
    keys = ["method", "configuration", "arm", "system_id", "direction"]
    if extra_keys:
        keys.extend(extra_keys)
    rows: list[dict[str, Any]] = []
    for key, group in per_run.groupby(keys, dropna=False, sort=True):
        row = dict(zip(keys, key))
        first = group.iloc[0]
        row.update(
            {
                "method_family": first["method_family"],
                "dimension": int(first["dimension"]),
                "threeway_class": first["threeway_class"],
                "is_exact_system": bool(first["is_exact_system"]),
                "feasible_bound_10": bool(first["feasible_bound_10"]),
                "n_runs": int(len(group)),
                "divergent_run_count": int(group["divergence_flag"].astype(bool).sum()),
            }
        )
        for column in RATE_COLUMNS:
            row[column] = numeric_mean(group[column])
        for column in CONTINUOUS_COLUMNS:
            row[column] = numeric_median(group[column])
        rows.append(row)
    return pd.DataFrame(rows)


def system_level(per_run: pd.DataFrame) -> pd.DataFrame:
    directions = direction_level(per_run)
    keys = ["method", "configuration", "arm", "system_id"]
    rows: list[dict[str, Any]] = []
    for key, group in directions.groupby(keys, dropna=False, sort=True):
        row = dict(zip(keys, key))
        first = group.iloc[0]
        row.update(
            {
                "method_family": first["method_family"],
                "dimension": int(first["dimension"]),
                "threeway_class": first["threeway_class"],
                "is_exact_system": bool(first["is_exact_system"]),
                "feasible_bound_10": bool(first["feasible_bound_10"]),
                "n_directions": int(group["direction"].nunique()),
                "n_runs": int(pd.to_numeric(group["n_runs"], errors="coerce").sum()),
                "divergent_run_count": int(pd.to_numeric(group["divergent_run_count"], errors="coerce").sum()),
            }
        )
        for column in RATE_COLUMNS + CONTINUOUS_COLUMNS:
            row[column] = numeric_mean(group[column])
        rows.append(row)
    return pd.DataFrame(rows)


def benchmark_rows(per_system: pd.DataFrame) -> pd.DataFrame:
    strata: list[tuple[str, list[str], pd.Series]] = [
        ("overall", [], pd.Series([True] * len(per_system), index=per_system.index)),
        ("dimension", ["dimension"], pd.Series([True] * len(per_system), index=per_system.index)),
        ("threeway_class", ["threeway_class"], pd.Series([True] * len(per_system), index=per_system.index)),
        ("dim3_feasible_bound_10", ["feasible_bound_10"], per_system["dimension"].astype(int).eq(3)),
    ]
    rows: list[dict[str, Any]] = []
    method_keys = ["method", "configuration", "arm"]
    for stratum_name, stratum_keys, mask in strata:
        subset = per_system.loc[mask].copy()
        if subset.empty:
            continue
        group_keys = method_keys + stratum_keys
        for key, group in subset.groupby(group_keys, dropna=False, sort=True):
            row = dict(zip(group_keys, key))
            row["stratum"] = stratum_name
            row["n_systems"] = int(group["system_id"].nunique())
            row["divergent_run_count"] = int(pd.to_numeric(group["divergent_run_count"], errors="coerce").sum())
            exact = group["is_exact_system"].astype(bool)
            for column in RATE_COLUMNS + CONTINUOUS_COLUMNS:
                values = group.loc[exact, column] if column in {
                    "raw_exact_support_match",
                    "pruned_exact_support_match",
                    "structural_f1_pruned",
                    "structural_precision_pruned",
                    "structural_recall_pruned",
                } else group[column]
                row[column] = numeric_mean(values)
            rows.append(row)
    return pd.DataFrame(rows)


def sensitivity_rows(per_run: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for (method, configuration, arm, dimension), group in per_run.groupby(
        ["method", "configuration", "arm", "dimension"], dropna=False, sort=True
    ):
        row = {"method": method, "configuration": configuration, "arm": arm, "dimension": int(dimension), "n_runs": int(len(group))}
        for regime in ["reconstruction", "generalization"]:
            available = group[f"{regime}_r2_arithmetic_available"].astype(bool) & group[
                f"{regime}_r2_variance_weighted_available"
            ].astype(bool)
            flips = group.loc[available, f"{regime}_r2_arithmetic_gt_0_9"].astype(bool) != group.loc[
                available, f"{regime}_r2_variance_weighted_gt_0_9"
            ].astype(bool)
            row[f"{regime}_available_run_count"] = int(available.sum())
            row[f"{regime}_threshold_cross_count"] = int(flips.sum())
        rows.append(row)
    return pd.DataFrame(rows)


def backcompat_unit_rates(per_run: pd.DataFrame) -> pd.DataFrame:
    units = direction_level(per_run)
    rows: list[dict[str, Any]] = []
    group_keys = ["method", "configuration", "arm", "dimension", "threeway_class"]
    for key, group in units.groupby(group_keys, dropna=False, sort=True):
        row = dict(zip(group_keys, key))
        row["n_units"] = int(len(group))
        for column in [
            "reconstruction_r2_arithmetic_gt_0_9",
            "generalization_r2_arithmetic_gt_0_9",
            "raw_exact_support_match",
            "pruned_exact_support_match",
        ]:
            row[column] = numeric_mean(group[column])
        rows.append(row)
    return pd.DataFrame(rows)


def control_rows(per_run: pd.DataFrame, per_system: pd.DataFrame, sindy_summary: Path, odeformer_summary: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    units = direction_level(per_run)
    evogrow = units[(units["method"] == "EvoGrow") & (units["arm"] == "canonical")]
    expected = {
        "overall_reconstruction": 0.823,
        "overall_generalization": 0.373,
        "dim1_reconstruction": 0.978,
        "dim1_generalization": 0.703,
        "dim2_reconstruction": 0.917,
        "dim2_generalization": 0.256,
        "dim3_reconstruction": 0.283,
        "dim3_generalization": 0.017,
    }
    actual = {
        "overall_reconstruction": float(evogrow["reconstruction_r2_arithmetic_gt_0_9"].mean()),
        "overall_generalization": float(evogrow["generalization_r2_arithmetic_gt_0_9"].mean()),
    }
    for dim in [1, 2, 3]:
        dim_group = evogrow[evogrow["dimension"] == dim]
        actual[f"dim{dim}_reconstruction"] = float(dim_group["reconstruction_r2_arithmetic_gt_0_9"].mean())
        actual[f"dim{dim}_generalization"] = float(dim_group["generalization_r2_arithmetic_gt_0_9"].mean())
    for name, expected_value in expected.items():
        got = actual[name]
        rows.append(
            {
                "control": f"evogrow_backcompat_{name}",
                "n_checked": int(len(evogrow)),
                "expected": expected_value,
                "actual": got,
                "abs_error": abs(got - expected_value),
                "passed": abs(got - expected_value) <= 0.0005,
                "note": "rounded published percentage",
            }
        )

    dim1 = per_run[per_run["dimension"] == 1]
    for method, group in dim1.groupby("method", dropna=False):
        for regime in ["reconstruction", "generalization"]:
            available = group[f"{regime}_r2_variance_weighted_available"].astype(bool)
            delta = (
                pd.to_numeric(group.loc[available, f"{regime}_r2_arithmetic"], errors="coerce")
                - pd.to_numeric(group.loc[available, f"{regime}_r2_variance_weighted"], errors="coerce")
            ).abs()
            max_delta = float(delta.max()) if len(delta) else math.nan
            rows.append(
                {
                    "control": f"dim1_variance_equals_arithmetic_{method}_{regime}",
                    "n_checked": int(available.sum()),
                    "expected": 0.0,
                    "actual": max_delta,
                    "abs_error": max_delta,
                    "passed": bool(len(delta) == 0 or max_delta <= 1e-12),
                    "note": "no rows checked means variance-weighted input unavailable",
                }
            )

    bench = benchmark_rows(per_system)
    overall = bench[bench["stratum"] == "overall"]
    for _, row in overall.iterrows():
        group = per_system[
            (per_system["method"] == row["method"])
            & (per_system["configuration"] == row["configuration"])
            & (per_system["arm"] == row["arm"])
        ]
        for column in [
            "reconstruction_r2_arithmetic_gt_0_9",
            "reconstruction_r2_variance_weighted_gt_0_9",
            "generalization_r2_arithmetic_gt_0_9",
            "generalization_r2_variance_weighted_gt_0_9",
        ]:
            if pd.isna(row[column]):
                continue
            got = float(row[column])
            expected_value = float(group[column].mean())
            rows.append(
                {
                    "control": f"equal_system_weight_{row['method']}_{row['configuration']}_{row['arm']}_{column}",
                    "n_checked": int(len(group)),
                    "expected": expected_value,
                    "actual": got,
                    "abs_error": abs(got - expected_value),
                    "passed": abs(got - expected_value) <= 1e-15,
                    "note": "benchmark equals unweighted mean of per-system rows",
                }
            )

    if sindy_summary.exists():
        rows.extend(compare_sindy_summary(per_run, pd.read_csv(sindy_summary)))
    if odeformer_summary.exists():
        rows.extend(compare_odeformer_summary(per_run, pd.read_csv(odeformer_summary)))
    return pd.DataFrame(rows)


def compare_sindy_summary(per_run: pd.DataFrame, summary: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sindy = per_run[per_run["method"] == "SINDy"].copy()
    unit = direction_level(sindy)
    grouped = unit.groupby(["configuration", "direction", "dimension", "threeway_class"], dropna=False)
    for _, ref in summary.iterrows():
        key = (ref["library_id"], ref["direction"], int(ref["dimension"]), ref["phasec_true_threeway_class"])
        if key not in grouped.groups:
            continue
        group = grouped.get_group(key)
        for regime in ["reconstruction", "generalization"]:
            ref_col = f"sindy_{regime}_r2_gt_0_9_rate_over_cells"
            if ref_col not in ref or pd.isna(ref[ref_col]):
                continue
            actual = float(group[f"{regime}_r2_arithmetic_gt_0_9"].mean())
            expected = float(ref[ref_col])
            rows.append(
                {
                    "control": f"sindy_backcompat_{key}_{regime}",
                    "n_checked": int(len(group)),
                    "expected": expected,
                    "actual": actual,
                    "abs_error": abs(actual - expected),
                    "passed": True,
                    "note": "old source comparison reported as delta, not a stop condition",
                }
            )
    return rows


def sindy_backcompat_delta_table(per_run: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    sindy = per_run[per_run["method"] == "SINDy"].copy()
    unit = direction_level(sindy)
    grouped = unit.groupby(["configuration", "direction", "dimension", "threeway_class"], dropna=False)
    for _, ref in summary.iterrows():
        key = (ref["library_id"], ref["direction"], int(ref["dimension"]), ref["phasec_true_threeway_class"])
        if key not in grouped.groups:
            continue
        group = grouped.get_group(key)
        for regime in ["reconstruction", "generalization"]:
            ref_col = f"sindy_{regime}_r2_gt_0_9_rate_over_cells"
            if ref_col not in ref or pd.isna(ref[ref_col]):
                continue
            new_rate = float(group[f"{regime}_r2_arithmetic_gt_0_9"].mean())
            old_rate = float(ref[ref_col])
            rows.append(
                {
                    "library_id": ref["library_id"],
                    "direction": ref["direction"],
                    "dimension": int(ref["dimension"]),
                    "threeway_class": ref["phasec_true_threeway_class"],
                    "regime": regime,
                    "n_units": int(len(group)),
                    "old_unit_rate": old_rate,
                    "new_unit_rate": new_rate,
                    "difference_new_minus_old": new_rate - old_rate,
                }
            )
    return pd.DataFrame(rows)


def wide_sindy_long(details: pd.DataFrame, realization: int = 1) -> pd.DataFrame:
    clean = details[
        (details["method"].astype(str) == "sindy")
        & (pd.to_numeric(details["noise_sigma"], errors="coerce") == 0.0)
        & (pd.to_numeric(details["subsample_rho"], errors="coerce") == 0.0)
        & (pd.to_numeric(details["noise_realization"], errors="coerce").astype(int) == realization)
    ].copy()
    rows: list[dict[str, Any]] = []
    for _, row in clean.iterrows():
        for regime in ["reconstruction", "generalization"]:
            r2 = finite_or_nan(row[f"{regime}_r2_arithmetic_mean"])
            rows.append(
                {
                    "library_id": row["library_id"],
                    "system_id": int(row["system_id"]),
                    "source_initial_condition_set": int(row["source_initial_condition_set"]),
                    "target_initial_condition_set": int(row["target_initial_condition_set"]),
                    "regime": regime,
                    "r2_gt_0_9": bool(math.isfinite(r2) and r2 > R2_THRESHOLD),
                    "active_terms_raw": row["active_terms_raw"],
                    "active_terms_pruned": row["active_terms_pruned"],
                    "sindy_structure_hit_raw": as_bool(row["sindy_structure_hit_raw"]),
                    "sindy_structure_hit_pruned": as_bool(row["sindy_structure_hit_pruned"]),
                }
            )
    return pd.DataFrame(rows)


def compare_sindy_to_c4c(c6_details: pd.DataFrame, c4c_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    c4c = pd.read_csv(c4c_path)
    keys = ["library_id", "system_id", "source_initial_condition_set", "target_initial_condition_set", "regime"]
    require_columns(
        c4c,
        set(keys + ["r2_gt_0_9", "active_terms_raw", "active_terms_pruned", "sindy_structure_hit_raw", "sindy_structure_hit_pruned"]),
        "WP-C4c SINDy details",
    )
    c6 = wide_sindy_long(c6_details)
    merged = c6.merge(c4c[keys + ["r2_gt_0_9", "active_terms_raw", "active_terms_pruned", "sindy_structure_hit_raw", "sindy_structure_hit_pruned"]], on=keys, how="outer", validate="one_to_one", suffixes=("_c6", "_c4c"), indicator=True)
    merged["r2_verdict_changed"] = merged["r2_gt_0_9_c6"].map(as_bool) != merged["r2_gt_0_9_c4c"].map(as_bool)
    for column in ["active_terms_raw", "active_terms_pruned"]:
        merged[f"{column}_changed"] = merged[f"{column}_c6"].astype(str) != merged[f"{column}_c4c"].astype(str)
    for column in ["sindy_structure_hit_raw", "sindy_structure_hit_pruned"]:
        merged[f"{column}_changed"] = merged[f"{column}_c6"].map(as_bool) != merged[f"{column}_c4c"].map(as_bool)
    changed = merged[
        (merged["_merge"].astype(str) != "both")
        | merged["r2_verdict_changed"]
        | merged["active_terms_raw_changed"]
        | merged["active_terms_pruned_changed"]
        | merged["sindy_structure_hit_raw_changed"]
        | merged["sindy_structure_hit_pruned_changed"]
    ].copy()
    control = pd.DataFrame(
        [
            {
                "control": "sindy_new_source_matches_wp_c4c_verdicts_and_supports",
                "n_checked": int(len(merged)),
                "expected": 0,
                "actual": int(len(changed)),
                "abs_error": int(len(changed)),
                "passed": int(len(changed)) == 0 and int(len(merged)) == 2520,
                "note": "compares C-6 clean sindy realization 1 against WP-C4c",
            }
        ]
    )
    return control, changed


def compare_sindy_old_source_changed_rows(c6_details: pd.DataFrame, old_path: Path) -> pd.DataFrame:
    old = pd.read_csv(old_path)
    keys = ["library_id", "system_id", "source_initial_condition_set", "target_initial_condition_set", "regime"]
    require_columns(
        old,
        set(keys + ["r2_gt_0_9", "sindy_structure_hit_raw", "sindy_structure_hit_pruned"]),
        "old SINDy details",
    )
    new = wide_sindy_long(c6_details)
    merged = new.merge(
        old[keys + ["r2_gt_0_9", "sindy_structure_hit_raw", "sindy_structure_hit_pruned"]],
        on=keys,
        how="outer",
        validate="one_to_one",
        suffixes=("_new", "_old"),
        indicator=True,
    )
    merged["r2_verdict_changed"] = merged["r2_gt_0_9_new"].map(as_bool) != merged["r2_gt_0_9_old"].map(as_bool)
    merged["raw_support_hit_changed"] = merged["sindy_structure_hit_raw_new"].map(as_bool) != merged["sindy_structure_hit_raw_old"].map(as_bool)
    merged["pruned_support_hit_changed"] = merged["sindy_structure_hit_pruned_new"].map(as_bool) != merged[
        "sindy_structure_hit_pruned_old"
    ].map(as_bool)
    return merged[
        (merged["_merge"].astype(str) != "both")
        | merged["r2_verdict_changed"]
        | merged["raw_support_hit_changed"]
        | merged["pruned_support_hit_changed"]
    ].copy()


def compare_odeformer_summary(per_run: pd.DataFrame, summary: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ode = per_run[(per_run["method"] == "ODEFormer") & (per_run["arm"] == "reference")].copy()
    unit = direction_level(ode)
    grouped = unit.groupby(["configuration", "dimension", "threeway_class"], dropna=False)
    for _, ref in summary.iterrows():
        key = (ref["odeformer_config_id"], int(ref["dimension"]), ref["phasec_true_threeway_class"])
        if key not in grouped.groups:
            continue
        group = grouped.get_group(key)
        regime = str(ref["regime"])
        actual = float(group[f"{regime}_r2_arithmetic_gt_0_9"].mean())
        expected = float(ref["odeformer_r2_gt_0_9_rate_over_units"])
        rows.append(
            {
                "control": f"odeformer_backcompat_{key}_{regime}",
                "n_checked": int(len(group)),
                "expected": expected,
                "actual": actual,
                "abs_error": abs(actual - expected),
                "passed": abs(actual - expected) <= 1e-12,
                "note": "compared with WP-N40 reference paired summary",
            }
        )
    return rows


def metadata(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "inputs": {name: {"path": str(path), "sha256": sha256(path)} for name, path in paths.items() if path.is_file()},
        "r2_threshold": R2_THRESHOLD,
        "hierarchy": "equation -> run -> seeds/repetitions within direction -> both directions -> system -> benchmark",
        "missing_fields": [],
    }


def run(args: argparse.Namespace) -> dict[str, Path]:
    paths = {
        "evogrow_registry": resolve(args.evogrow_registry),
        "evogrow_generalization": resolve(args.evogrow_generalization),
        "sindy_details": resolve(args.sindy_details),
        "sindy_c4c_details": resolve(args.sindy_c4c_details),
        "sindy_old_details": resolve(args.sindy_old_details),
        "odeformer_reference": resolve(args.odeformer_reference),
        "odeformer_candidate": resolve(args.odeformer_candidate),
        "representability_threeway": resolve(args.representability_threeway),
        "trajectory_export_manifest": resolve(args.trajectory_export) / "trajectory_manifest.csv",
        "sindy_control_summary": resolve(args.sindy_control_summary),
        "odeformer_control_summary": resolve(args.odeformer_control_summary),
    }
    merge_outputs = merge_sindy_shards(resolve(args.sindy_shards_dir), resolve(args.sindy_merged_dir))
    paths["sindy_details"] = merge_outputs["details"]
    for name, path in paths.items():
        if "summary" in name:
            continue
        if not path.exists():
            fail(f"input path does not exist ({name}): {path}")
    classes = true_classes(paths["representability_threeway"])
    weights = load_variance_weights(resolve(args.trajectory_export))
    sindy_details = pd.read_csv(paths["sindy_details"])
    per_run = pd.concat(
        [
            load_evogrow(paths["evogrow_registry"], paths["evogrow_generalization"], weights, classes),
            load_sindy_wide(sindy_details, classes),
            load_odeformer(paths["odeformer_reference"], "reference", classes),
            load_odeformer(paths["odeformer_candidate"], "candidate", classes),
        ],
        ignore_index=True,
        sort=False,
    )
    per_system = system_level(per_run)
    benchmark = benchmark_rows(per_system)
    sensitivity = sensitivity_rows(per_run)
    controls = control_rows(per_run, per_system, paths["sindy_control_summary"], paths["odeformer_control_summary"])
    c4c_control, c4c_changed = compare_sindy_to_c4c(sindy_details, paths["sindy_c4c_details"])
    controls = pd.concat([controls, c4c_control], ignore_index=True, sort=False)
    realization_deltas = clean_sindy_realization_deltas(sindy_details)
    old_source_changed = compare_sindy_old_source_changed_rows(sindy_details, paths["sindy_old_details"])
    sindy_deltas = (
        sindy_backcompat_delta_table(per_run, pd.read_csv(paths["sindy_control_summary"]))
        if paths["sindy_control_summary"].exists()
        else pd.DataFrame()
    )

    output_dir = resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "per_run": output_dir / "per_run.csv",
        "per_system": output_dir / "per_system.csv",
        "benchmark": output_dir / "benchmark.csv",
        "sensitivity": output_dir / "sensitivity.csv",
        "controls": output_dir / "controls.csv",
        "sindy_old_vs_new_deltas": output_dir / "sindy_old_vs_new_deltas.csv",
        "sindy_old_vs_new_changed_rows": output_dir / "sindy_old_vs_new_changed_rows.csv",
        "sindy_c4c_changed_rows": output_dir / "sindy_c4c_changed_rows.csv",
        "sindy_clean_realization_deltas": output_dir / "sindy_clean_realization_deltas.csv",
        "metadata": output_dir / "metadata.json",
    }
    per_run.to_csv(outputs["per_run"], index=False)
    per_system.to_csv(outputs["per_system"], index=False)
    benchmark.to_csv(outputs["benchmark"], index=False)
    sensitivity.to_csv(outputs["sensitivity"], index=False)
    controls.to_csv(outputs["controls"], index=False)
    sindy_deltas.to_csv(outputs["sindy_old_vs_new_deltas"], index=False)
    old_source_changed.to_csv(outputs["sindy_old_vs_new_changed_rows"], index=False)
    c4c_changed.to_csv(outputs["sindy_c4c_changed_rows"], index=False)
    realization_deltas.to_csv(outputs["sindy_clean_realization_deltas"], index=False)
    outputs["metadata"].write_text(json.dumps(metadata(paths), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not controls["passed"].map(as_bool).all():
        failed = controls[~controls["passed"].map(as_bool)]
        fail(f"controls failed: {failed[['control', 'expected', 'actual']].to_dict('records')[:10]}")
    return outputs


def main() -> int:
    try:
        outputs = run(parse_args())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    for name, path in outputs.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
