import argparse
import json
import sys
from pathlib import Path
from typing import Any

ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

import numpy as np
import pandas as pd

from utils.io import load_run_registry
from utils.metrics import check_required_columns, filter_valid_runs


REQUIRED_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "seed",
    "loss",
    "exact_support_match",
    "final_stage",
    "stage_overshoot",
    "wasted_levels",
    "total_invalid_evals",
    "elapsed_s",
]

OUTPUT_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "n_seeds",
    "n_valid",
    "mean_loss",
    "std_loss",
    "exact_match_rate",
    "mean_final_stage",
    "mean_stage_overshoot",
    "mean_wasted_levels",
    "mean_elapsed_s",
    "mean_invalid_evals",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate run_registry.csv by variant and system."
    )
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(path_value: str, analysis_root: Path, config_path: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path

    analysis_relative = analysis_root / path
    if analysis_relative.exists():
        return analysis_relative

    config_relative = config_path.parent / path
    if config_relative.exists():
        return config_relative

    return analysis_relative


def normalize_registry_columns(df: pd.DataFrame) -> pd.DataFrame:
    if "variant_slug" in df.columns or "variant" not in df.columns:
        return df

    normalized = df.copy()
    normalized["variant_slug"] = normalized["variant"]
    return normalized


def coerce_exact_support_match(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series) or pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    normalized = series.astype(str).str.strip().str.lower()
    mapped = normalized.map({"true": 1.0, "false": 0.0, "1": 1.0, "0": 0.0})
    return pd.to_numeric(mapped, errors="coerce")


def mean_final_stage(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if numeric.empty or (numeric == -1).all():
        return np.nan
    return float(numeric.mean())


def aggregate_group(group: pd.DataFrame) -> pd.Series:
    valid = filter_valid_runs(group)
    exact_match = coerce_exact_support_match(valid["exact_support_match"])

    return pd.Series(
        {
            "system_name": group["system_name"].iloc[0],
            "n_seeds": len(group),
            "n_valid": len(valid),
            "mean_loss": valid["loss"].mean(),
            "std_loss": valid["loss"].std() if len(valid) >= 2 else np.nan,
            "exact_match_rate": exact_match.mean(),
            "mean_final_stage": mean_final_stage(valid["final_stage"]),
            "mean_stage_overshoot": valid["stage_overshoot"].mean(),
            "mean_wasted_levels": valid["wasted_levels"].mean(),
            "mean_elapsed_s": valid["elapsed_s"].mean(),
            "mean_invalid_evals": valid["total_invalid_evals"].mean(),
        }
    )


def aggregate_registry(df: pd.DataFrame) -> pd.DataFrame:
    aggregated = (
        df.groupby(["variant_slug", "system_id"], sort=True, dropna=False)
        .apply(aggregate_group, include_groups=False)
        .reset_index()
    )
    return aggregated.loc[:, OUTPUT_COLUMNS]


def display_path(path: Path, analysis_root: Path) -> str:
    try:
        relative = path.resolve().relative_to(analysis_root.parent.resolve())
        return relative.as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    analysis_root = Path.cwd()
    config_path = (analysis_root / args.config).resolve()

    try:
        config = load_config(config_path)
        experiment_id = config["experiment_id"]
        run_registry_path = resolve_path(
            config["run_registry_path"], analysis_root, config_path
        )
        output_dir = analysis_root / config["output_dir"]

        registry = normalize_registry_columns(load_run_registry(run_registry_path))
        check_required_columns(registry, REQUIRED_COLUMNS)

        total_rows = len(registry)
        valid_rows = len(filter_valid_runs(registry))
        aggregated = aggregate_registry(registry)
        zero_valid_cells = int((aggregated["n_valid"] == 0).sum())

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "aggregate_by_variant_system.csv"
        aggregated.to_csv(output_path, index=False, float_format="%.6g")

        print(f"Aggregated {experiment_id}")
        print(
            f"  Input:  {display_path(run_registry_path, analysis_root)}"
            f"  ({total_rows} rows, {valid_rows} valid)"
        )
        print(
            f"  Output: {display_path(output_path, analysis_root)}"
            f"  ({len(aggregated)} rows)"
        )
        print(f"  Cells with 0 valid runs: {zero_valid_cells}")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
