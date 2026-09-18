import argparse
import csv
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

from utils.campaign import campaign_registry_path  # noqa: E402


R2_THRESHOLD = 0.9
ARITHMETIC_CONTROL_TOLERANCE = 1e-12
ONE_DIMENSION_TOLERANCE = 1e-12
QUANTILES = [0.0, 0.25, 0.5, 0.75, 1.0]
DEFAULT_TRAJECTORY_EXPORT = (
    REPO_ROOT / "outputs" / "phase_c_trajectory_hashes" / "wp_c4c" / "trajectory_export"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate arithmetic and variance-weighted R2 rates."
    )
    parser.add_argument("--campaign", required=True, help="Campaign identifier for input defaults and output names.")
    parser.add_argument(
        "--input",
        help="Input CSV or JSONL. Defaults to experiments/<campaign>/run_registry.csv.",
    )
    parser.add_argument(
        "--input-format",
        choices=["auto", "run_registry", "phasec_external_baseline"],
        default="auto",
    )
    parser.add_argument(
        "--trajectory-export",
        default=str(DEFAULT_TRAJECTORY_EXPORT),
        help="Trajectory export directory containing trajectory_manifest.csv and raw float64 cells.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory. Defaults to analysis/data/<campaign>/variance_weighted_r2.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def read_jsonl(path: Path) -> pd.DataFrame:
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


def read_input(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".jsonl":
        return read_jsonl(path)
    return pd.read_csv(path)


def parse_json_list(value: Any, column: str, row_number: int) -> list[float]:
    if pd.isna(value):
        fail(f"{column} is missing at row {row_number}")
    if isinstance(value, list):
        parsed = value
    else:
        text = str(value).strip()
        if not text:
            fail(f"{column} is empty at row {row_number}")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            fail(f"{column} is not valid JSON at row {row_number}: {exc}")
    if not isinstance(parsed, list) or not parsed:
        fail(f"{column} must be a non-empty JSON array at row {row_number}")
    try:
        values = [float(item) for item in parsed]
    except (TypeError, ValueError) as exc:
        fail(f"{column} contains non-numeric values at row {row_number}: {exc}")
    if not all(math.isfinite(value) for value in values):
        fail(f"{column} contains non-finite values at row {row_number}")
    return values


def parse_shape(value: Any, column: str, row_number: int) -> list[int]:
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError as exc:
        fail(f"{column} is not valid JSON at manifest row {row_number}: {exc}")
    if not isinstance(parsed, list) or not all(isinstance(item, int) for item in parsed):
        fail(f"{column} must be a JSON integer array at manifest row {row_number}")
    return parsed


def load_variance_weights(trajectory_export: Path) -> dict[tuple[int, int], np.ndarray]:
    manifest_path = trajectory_export / "trajectory_manifest.csv"
    if not manifest_path.exists():
        fail(f"missing trajectory export manifest: {manifest_path}")

    weights: dict[tuple[int, int], np.ndarray] = {}
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            system_id = int(row["system_id"])
            ic_set = int(row["initial_condition_set"])
            if row["dtype"] != "float64" or row["byte_order"] != "little_endian":
                fail(f"unsupported trajectory dtype/byte order at manifest row {row_number}")
            if row["state_axis_order"] != "time_by_dimension_c_order":
                fail(f"unsupported state axis order at manifest row {row_number}")

            state_shape = parse_shape(row["state_shape"], "state_shape", row_number)
            state_path = trajectory_export / Path(str(row["state_path"]))
            if not state_path.exists():
                fail(f"missing trajectory state file at manifest row {row_number}: {state_path}")
            state_bytes = state_path.read_bytes()
            state_hash = hashlib.sha256(state_bytes).hexdigest()
            if state_hash != row["state_sha256"]:
                fail(f"trajectory state hash mismatch at manifest row {row_number}: {state_path}")

            state = np.frombuffer(state_bytes, dtype="<f8").reshape(state_shape, order="C")
            if state.ndim != 2:
                fail(f"state_shape must be two-dimensional at manifest row {row_number}")
            variance = np.var(state, axis=0)
            if len(variance) != int(row["dimension"]):
                fail(f"state_shape dimension does not match manifest dimension at row {row_number}")
            if float(np.sum(variance)) <= 0.0:
                fail(f"all trajectory variances are zero at manifest row {row_number}")
            weights[(system_id, ic_set)] = variance

    if not weights:
        fail(f"trajectory manifest contains no rows: {manifest_path}")
    return weights


def auto_input_format(df: pd.DataFrame, requested: str) -> str:
    if requested != "auto":
        return requested
    if "r2_by_dim" in df.columns and "r2" in df.columns:
        return "run_registry"
    if {
        "reconstruction_r2_arithmetic_mean",
        "reconstruction_r2_variance_weighted",
        "generalization_r2_arithmetic_mean",
        "generalization_r2_variance_weighted",
    }.issubset(df.columns):
        return "phasec_external_baseline"
    fail("could not infer input format")


def choose_arm(row: pd.Series) -> str:
    for column in ["condition", "variant_slug", "variant", "method"]:
        if column in row.index and not pd.isna(row[column]) and str(row[column]).strip():
            return str(row[column]).strip()
    return "unknown"


def weighted_average(values: list[float], weights: np.ndarray, row_number: int) -> float:
    if len(values) != len(weights):
        fail(
            f"r2_by_dim length {len(values)} does not match trajectory dimension "
            f"{len(weights)} at row {row_number}"
        )
    return float(np.average(np.asarray(values, dtype=float), weights=weights))


def build_run_registry_cells(
    df: pd.DataFrame,
    weights: dict[tuple[int, int], np.ndarray],
    campaign: str,
    source_path: Path,
) -> pd.DataFrame:
    required = ["system_id", "initial_condition_set", "r2", "r2_by_dim"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        fail(f"run registry input is missing required columns: {missing}")

    rows: list[dict[str, Any]] = []
    control_errors: list[str] = []
    for index, row in df.iterrows():
        row_number = int(index) + 2
        r2_by_dim = parse_json_list(row["r2_by_dim"], "r2_by_dim", row_number)
        arithmetic = float(np.mean(r2_by_dim))
        stored_r2 = float(row["r2"])
        control_error = abs(arithmetic - stored_r2)
        if control_error > ARITHMETIC_CONTROL_TOLERANCE:
            control_errors.append(
                f"row {row_number}: mean(r2_by_dim)={arithmetic:.17g}, r2={stored_r2:.17g}"
            )

        system_id = int(row["system_id"])
        ic_set = int(row["initial_condition_set"])
        trajectory_key = (system_id, ic_set)
        if trajectory_key not in weights:
            fail(f"missing trajectory weights for system_id={system_id}, initial_condition_set={ic_set}")
        variance_weighted = weighted_average(r2_by_dim, weights[trajectory_key], row_number)
        dimension = len(r2_by_dim)
        arithmetic_gt = bool(arithmetic > R2_THRESHOLD)
        variance_weighted_gt = bool(variance_weighted > R2_THRESHOLD)
        if dimension == 1 and abs(arithmetic - variance_weighted) > ONE_DIMENSION_TOLERANCE:
            fail(f"one-dimensional aggregation mismatch at row {row_number}")
        diff = variance_weighted - arithmetic
        rows.append(
            {
                "campaign": campaign,
                "source_path": str(source_path),
                "source_format": "run_registry",
                "record_index": int(index),
                "metric_scope": "record",
                "system_id": system_id,
                "dimension": dimension,
                "arm": choose_arm(row),
                "initial_condition_set": ic_set,
                "r2_arithmetic_mean": arithmetic,
                "r2_variance_weighted": variance_weighted,
                "r2_arithmetic_mean_gt_0_9": arithmetic_gt,
                "r2_variance_weighted_gt_0_9": variance_weighted_gt,
                "r2_difference_variance_weighted_minus_arithmetic": diff,
                "threshold_flip": arithmetic_gt != variance_weighted_gt,
                "threshold_flip_direction": flip_direction(arithmetic_gt, variance_weighted_gt),
                "arithmetic_control_abs_error": control_error,
                "one_dim_abs_delta": abs(arithmetic - variance_weighted) if dimension == 1 else math.nan,
                "aggregation_source": "reconstructed_from_r2_by_dim",
            }
        )

    if control_errors:
        preview = "; ".join(control_errors[:5])
        fail(
            f"arithmetic control failed for {len(control_errors)} rows at tolerance "
            f"{ARITHMETIC_CONTROL_TOLERANCE}: {preview}"
        )
    return pd.DataFrame(rows)


def build_external_baseline_cells(df: pd.DataFrame, campaign: str, source_path: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, row in df.iterrows():
        for scope, ic_column in [
            ("reconstruction", "fit_initial_condition_set"),
            ("generalization", "generalization_initial_condition_set"),
        ]:
            arithmetic = float(row[f"{scope}_r2_arithmetic_mean"])
            variance_weighted = float(row[f"{scope}_r2_variance_weighted"])
            arithmetic_gt = bool(arithmetic > R2_THRESHOLD)
            variance_weighted_gt = bool(variance_weighted > R2_THRESHOLD)
            dimension = int(row["dimension"])
            if dimension == 1 and abs(arithmetic - variance_weighted) > ONE_DIMENSION_TOLERANCE:
                fail(f"one-dimensional aggregation mismatch at input row {index + 2}, scope {scope}")
            rows.append(
                {
                    "campaign": campaign,
                    "source_path": str(source_path),
                    "source_format": "phasec_external_baseline",
                    "record_index": int(index),
                    "metric_scope": scope,
                    "system_id": int(row["system_id"]),
                    "dimension": dimension,
                    "arm": choose_arm(row),
                    "initial_condition_set": int(row[ic_column]),
                    "r2_arithmetic_mean": arithmetic,
                    "r2_variance_weighted": variance_weighted,
                    "r2_arithmetic_mean_gt_0_9": arithmetic_gt,
                    "r2_variance_weighted_gt_0_9": variance_weighted_gt,
                    "r2_difference_variance_weighted_minus_arithmetic": variance_weighted - arithmetic,
                    "threshold_flip": arithmetic_gt != variance_weighted_gt,
                    "threshold_flip_direction": flip_direction(arithmetic_gt, variance_weighted_gt),
                    "arithmetic_control_abs_error": math.nan,
                    "one_dim_abs_delta": abs(arithmetic - variance_weighted) if dimension == 1 else math.nan,
                    "aggregation_source": "precomputed_external_baseline_fields",
                }
            )
    return pd.DataFrame(rows)


def flip_direction(arithmetic_gt: bool, variance_weighted_gt: bool) -> str:
    if arithmetic_gt == variance_weighted_gt:
        return "none"
    if not arithmetic_gt and variance_weighted_gt:
        return "arithmetic_le_0_9_to_variance_weighted_gt_0_9"
    return "arithmetic_gt_0_9_to_variance_weighted_le_0_9"


def rate_rows(cells: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_columns = ["dimension", "arm", "initial_condition_set"]
    for key, group in cells.groupby(group_columns, dropna=False, sort=True):
        dimension, arm, ic_set = key
        denominator = int(len(group))
        arithmetic_hits = int(group["r2_arithmetic_mean_gt_0_9"].sum())
        weighted_hits = int(group["r2_variance_weighted_gt_0_9"].sum())
        rows.append(
            {
                "dimension": int(dimension),
                "arm": arm,
                "initial_condition_set": int(ic_set),
                "n_cells": denominator,
                "r2_arithmetic_mean_gt_0_9_count": arithmetic_hits,
                "r2_arithmetic_mean_gt_0_9_rate": arithmetic_hits / denominator,
                "r2_variance_weighted_gt_0_9_count": weighted_hits,
                "r2_variance_weighted_gt_0_9_rate": weighted_hits / denominator,
            }
        )
    return pd.DataFrame(rows)


def flip_rows(cells: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_columns = ["dimension", "arm", "initial_condition_set"]
    for key, group in cells.groupby(group_columns, dropna=False, sort=True):
        dimension, arm, ic_set = key
        denominator = int(len(group))
        flip_count = int(group["threshold_flip"].sum())
        up = int((group["threshold_flip_direction"] == "arithmetic_le_0_9_to_variance_weighted_gt_0_9").sum())
        down = int((group["threshold_flip_direction"] == "arithmetic_gt_0_9_to_variance_weighted_le_0_9").sum())
        rows.append(
            {
                "dimension": int(dimension),
                "arm": arm,
                "initial_condition_set": int(ic_set),
                "n_cells": denominator,
                "threshold_flip_count": flip_count,
                "threshold_flip_rate": flip_count / denominator,
                "threshold_flip_up_count": up,
                "threshold_flip_up_rate": up / denominator,
                "threshold_flip_down_count": down,
                "threshold_flip_down_rate": down / denominator,
            }
        )
    return pd.DataFrame(rows)


def quantile_rows(cells: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_columns = ["dimension", "arm", "initial_condition_set"]
    for key, group in cells.groupby(group_columns, dropna=False, sort=True):
        dimension, arm, ic_set = key
        quantiles = group["r2_difference_variance_weighted_minus_arithmetic"].quantile(QUANTILES)
        row = {
            "dimension": int(dimension),
            "arm": arm,
            "initial_condition_set": int(ic_set),
            "n_cells": int(len(group)),
        }
        for probability, value in quantiles.items():
            row[f"diff_q{int(round(probability * 1000)):03d}"] = float(value)
        rows.append(row)
    return pd.DataFrame(rows)


def control_rows(cells: pd.DataFrame) -> pd.DataFrame:
    one_dim = cells[cells["dimension"] == 1]
    multi_dim = cells[cells["dimension"] > 1]
    return pd.DataFrame(
        [
            {
                "control": "arithmetic_mean_reproduces_r2",
                "n_checked": int(cells["arithmetic_control_abs_error"].notna().sum()),
                "n_failed": int((cells["arithmetic_control_abs_error"] > ARITHMETIC_CONTROL_TOLERANCE).sum()),
                "max_abs_error": float(cells["arithmetic_control_abs_error"].max(skipna=True))
                if cells["arithmetic_control_abs_error"].notna().any()
                else math.nan,
                "tolerance": ARITHMETIC_CONTROL_TOLERANCE,
            },
            {
                "control": "one_dimensional_aggregations_identical",
                "n_checked": int(len(one_dim)),
                "n_failed": int((one_dim["one_dim_abs_delta"] > ONE_DIMENSION_TOLERANCE).sum()),
                "max_abs_error": float(one_dim["one_dim_abs_delta"].max(skipna=True)) if len(one_dim) else math.nan,
                "tolerance": ONE_DIMENSION_TOLERANCE,
            },
            {
                "control": "multi_dimensional_aggregations_differ",
                "n_checked": int(len(multi_dim)),
                "n_failed": int(
                    (
                        multi_dim["r2_difference_variance_weighted_minus_arithmetic"].abs()
                        <= ONE_DIMENSION_TOLERANCE
                    ).sum()
                ),
                "max_abs_error": float(
                    multi_dim["r2_difference_variance_weighted_minus_arithmetic"].abs().max(skipna=True)
                )
                if len(multi_dim)
                else math.nan,
                "tolerance": ONE_DIMENSION_TOLERANCE,
            },
        ]
    )


def write_outputs(cells: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "cells": output_dir / "variance_weighted_r2_cells.csv",
        "rates": output_dir / "variance_weighted_r2_rates.csv",
        "flips": output_dir / "variance_weighted_r2_flip_rates.csv",
        "quantiles": output_dir / "variance_weighted_r2_difference_quantiles.csv",
        "controls": output_dir / "variance_weighted_r2_controls.csv",
    }
    cells.to_csv(outputs["cells"], index=False)
    rate_rows(cells).to_csv(outputs["rates"], index=False)
    flip_rows(cells).to_csv(outputs["flips"], index=False)
    quantile_rows(cells).to_csv(outputs["quantiles"], index=False)
    control_rows(cells).to_csv(outputs["controls"], index=False)
    return outputs


def aggregate(args: argparse.Namespace) -> dict[str, Path]:
    input_path = Path(args.input) if args.input else campaign_registry_path(REPO_ROOT, args.campaign)
    if not input_path.is_absolute():
        input_path = (REPO_ROOT / input_path).resolve()
    if not input_path.exists():
        fail(f"input does not exist: {input_path}")

    df = read_input(input_path)
    input_format = auto_input_format(df, args.input_format)
    if input_format == "run_registry":
        weights = load_variance_weights(Path(args.trajectory_export))
        cells = build_run_registry_cells(df, weights, args.campaign, input_path)
    elif input_format == "phasec_external_baseline":
        cells = build_external_baseline_cells(df, args.campaign, input_path)
    else:
        fail(f"unsupported input format: {input_format}")

    output_dir = Path(args.output_dir) if args.output_dir else ANALYSIS_ROOT / "data" / args.campaign / "variance_weighted_r2"
    if not output_dir.is_absolute():
        output_dir = (REPO_ROOT / output_dir).resolve()
    return write_outputs(cells, output_dir)


def main() -> None:
    outputs = aggregate(parse_args())
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
