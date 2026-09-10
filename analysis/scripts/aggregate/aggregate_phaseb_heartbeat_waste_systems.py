import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.io import load_run_registry  # noqa: E402
from utils.campaign import (  # noqa: E402
    DEFAULT_CAMPAIGN_ID,
    campaign_config_path,
    campaign_data_dir,
    campaign_registry_path,
    require_single_campaign_id,
)
from utils.metrics import check_required_columns  # noqa: E402


QUANTILES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
SILENT_FRACTION_THRESHOLDS = [0.25, 0.50, 0.75, 0.90]
EXPECTED_ROW_COUNT = 756
SENTINEL_LOSS = 1e6

REQUIRED_COLUMNS = [
    "experiment_id",
    "system_id",
    "system_name",
    "system_dim",
    "system_representability",
    "seed",
    "initial_condition_set",
    "condition",
    "loss",
    "r2",
    "exact_support_match",
    "final_stage",
    "stage_caps",
    "n_levels",
    "total_loss_evals",
    "total_ode_solves",
    "total_parameter_fits",
    "campaign_manifest_index",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate Phase-B heartbeat silent-level waste and per-system tables."
    )
    parser.add_argument("--campaign", default=DEFAULT_CAMPAIGN_ID)
    parser.add_argument(
        "--config",
        help="Path to config JSON. Defaults to analysis/configs/<campaign>.json when present.",
    )
    parser.add_argument("--input", help="Optional run_registry.csv override.")
    parser.add_argument(
        "--heartbeat-dir",
        help="Optional heartbeat directory override.",
    )
    parser.add_argument("--output-dir", help="Optional aggregate output directory override.")
    parser.add_argument("--expected-row-count", type=int, default=EXPECTED_ROW_COUNT)
    parser.add_argument(
        "--relative-improvement-threshold",
        type=float,
        default=0.0,
        help="Relative best_loss decrease required to count as an improvement.",
    )
    parser.add_argument(
        "--substantial-relative-improvement-threshold",
        type=float,
        default=0.01,
        help="Additional relative best_loss decrease reported as a substantive threshold.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_path(path_value: str, analysis_root: Path, config_path: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    analysis_relative = analysis_root / path
    if analysis_relative.exists():
        return analysis_relative.resolve()
    config_relative = config_path.parent / path
    if config_relative.exists():
        return config_relative.resolve()
    return analysis_relative.resolve()


def require_no_missing(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        text = df[column].astype(str).str.strip().str.lower()
        missing = df[column].isna() | text.isin(["", "nan", "none", "null"])
        if missing.any():
            fail(f"{column} is missing or empty in {int(missing.sum())} rows")


def coerce_optional_bool(value: Any) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip().lower()
    if text in {"", "nan", "none", "null"}:
        return None
    if text in {"true", "1", "yes", "y"}:
        return 1.0
    if text in {"false", "0", "no", "n"}:
        return 0.0
    fail(f"exact_support_match contains non-boolean value: {value}")
    raise AssertionError("unreachable")


def validate_registry(
    df: pd.DataFrame,
    expected_row_count: int,
    campaign_id: str = DEFAULT_CAMPAIGN_ID,
) -> pd.DataFrame:
    check_required_columns(df, REQUIRED_COLUMNS)
    registry = df.copy()
    require_single_campaign_id(registry, campaign_id, "run_registry")
    for column in [
        "system_id",
        "system_dim",
        "seed",
        "initial_condition_set",
        "loss",
        "r2",
        "final_stage",
        "n_levels",
        "total_loss_evals",
        "total_ode_solves",
        "total_parameter_fits",
        "campaign_manifest_index",
    ]:
        registry[column] = pd.to_numeric(registry[column], errors="coerce")

    require_no_missing(
        registry,
        [
            "system_id",
            "system_name",
            "system_dim",
            "system_representability",
            "seed",
            "initial_condition_set",
            "condition",
            "loss",
            "r2",
            "final_stage",
            "stage_caps",
            "n_levels",
            "total_loss_evals",
            "total_ode_solves",
            "total_parameter_fits",
            "campaign_manifest_index",
        ],
    )
    if len(registry) != expected_row_count:
        fail(f"row count expected {expected_row_count}, got {len(registry)}")
    if registry["loss"].eq(SENTINEL_LOSS).any():
        fail(f"sentinel loss {SENTINEL_LOSS:g} found in run_registry.csv")
    if registry["loss"].le(0).any():
        fail("loss must be positive")

    registry["system_id"] = registry["system_id"].astype(int)
    registry["system_dim"] = registry["system_dim"].astype(int)
    registry["seed"] = registry["seed"].astype(int)
    registry["initial_condition_set"] = registry["initial_condition_set"].astype(int)
    registry["final_stage"] = registry["final_stage"].astype(int)
    registry["n_levels"] = registry["n_levels"].astype(int)
    registry["campaign_manifest_index"] = registry["campaign_manifest_index"].astype(int)
    registry["system_representability"] = (
        registry["system_representability"].astype(str).str.strip().str.lower()
    )
    registry["condition"] = registry["condition"].astype(str).str.strip()
    registry["exact_support_match_num"] = registry["exact_support_match"].map(
        coerce_optional_bool
    )

    identity_columns = ["system_id", "seed", "initial_condition_set", "condition"]
    if registry[identity_columns].duplicated().any():
        fail("duplicate registry identity found for system_id, seed, initial_condition_set, condition")
    if registry["campaign_manifest_index"].duplicated().any():
        fail("duplicate campaign_manifest_index found in run_registry.csv")
    return registry


def parse_heartbeat_file(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    start: dict[str, Any] | None = None
    complete: dict[str, Any] | None = None
    levels: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                event = json.loads(text)
            except json.JSONDecodeError as exc:
                fail(f"{path} is not valid JSONL at line {line_number}: {exc}")
            event_type = event.get("event")
            if event_type == "start":
                if start is not None:
                    fail(f"{path} contains multiple start events")
                start = event
            elif event_type == "level":
                levels.append(event)
            elif event_type == "complete":
                if complete is not None:
                    fail(f"{path} contains multiple complete events")
                complete = event
    if start is None:
        fail(f"{path} has no start event")
    if complete is None:
        fail(f"{path} has no complete event")
    if not levels:
        fail(f"{path} has no level events")
    return start, levels, complete


def event_identity(event: dict[str, Any], path: Path) -> tuple[int, int, int, str]:
    try:
        return (
            int(event["system_id"]),
            int(event["seed"]),
            int(event["initial_condition_set"]),
            str(event["condition"]).strip(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        fail(f"{path} heartbeat identity is incomplete or invalid")
        raise AssertionError("unreachable") from exc


def improvement_summary(
    levels: list[dict[str, Any]], relative_threshold: float, path: Path
) -> dict[str, Any]:
    if relative_threshold < 0:
        fail("relative improvement threshold must be non-negative")
    best = math.inf
    last_improvement_position = 0
    last_improvement_level = 0
    improvement_count = 0
    equal_best_count = 0
    nonmonotone_best_loss_count = 0
    previous_best_loss = math.inf
    for position, event in enumerate(levels, start=1):
        try:
            level = int(event["level"])
            best_loss = float(event["best_loss"])
        except (KeyError, TypeError, ValueError) as exc:
            fail(f"{path} has a level event without numeric level and best_loss")
            raise AssertionError("unreachable") from exc
        if not math.isfinite(best_loss):
            fail(f"{path} has a non-finite best_loss at level {level}")
        if best_loss > previous_best_loss:
            nonmonotone_best_loss_count += 1
        elif best_loss == previous_best_loss:
            equal_best_count += 1
        if math.isinf(best) or best_loss < best * (1.0 - relative_threshold):
            best = best_loss
            last_improvement_position = position
            last_improvement_level = level
            improvement_count += 1
        previous_best_loss = best_loss
    if last_improvement_position == 0:
        fail(f"{path} has no usable improvement event")
    silent_levels = len(levels) - last_improvement_position
    return {
        "last_improvement_level": int(last_improvement_level),
        "last_improvement_position": int(last_improvement_position),
        "improvement_count": int(improvement_count),
        "silent_levels": int(silent_levels),
        "silent_fraction": float(silent_levels / len(levels)),
        "equal_best_loss_transitions": int(equal_best_count),
        "nonmonotone_best_loss_transitions": int(nonmonotone_best_loss_count),
    }


def load_heartbeat_metrics(
    registry: pd.DataFrame,
    heartbeat_dir: Path,
    relative_threshold: float,
    substantial_threshold: float,
) -> pd.DataFrame:
    if not heartbeat_dir.exists():
        fail(f"Heartbeat directory does not exist: {heartbeat_dir}")
    heartbeat_paths = sorted(heartbeat_dir.glob("*.heartbeat.jsonl"))
    if len(heartbeat_paths) != len(registry):
        fail(f"heartbeat stream count expected {len(registry)}, got {len(heartbeat_paths)}")

    by_identity = {
        (
            int(row.system_id),
            int(row.seed),
            int(row.initial_condition_set),
            str(row.condition).strip(),
        ): row
        for row in registry.itertuples(index=False)
    }
    rows: list[dict[str, Any]] = []
    seen_identities: set[tuple[int, int, int, str]] = set()
    for path in heartbeat_paths:
        start, levels, complete = parse_heartbeat_file(path)
        start_key = event_identity(start, path)
        complete_key = event_identity(complete, path)
        if start_key != complete_key:
            fail(f"{path} start and complete identities differ")
        if start_key not in by_identity:
            fail(f"{path} identity does not match exactly one registry row: {start_key}")
        if start_key in seen_identities:
            fail(f"{path} duplicates heartbeat identity: {start_key}")
        seen_identities.add(start_key)
        registry_row = by_identity[start_key]
        manifest_index = int(start.get("manifest_index", -1))
        if manifest_index != int(registry_row.campaign_manifest_index):
            fail(
                f"{path} manifest_index {manifest_index} does not match registry "
                f"campaign_manifest_index {int(registry_row.campaign_manifest_index)}"
            )

        base = improvement_summary(levels, relative_threshold, path)
        substantial = improvement_summary(levels, substantial_threshold, path)
        rows.append(
            {
                "heartbeat_file": path.name,
                "campaign_manifest_index": int(registry_row.campaign_manifest_index),
                "system_id": int(registry_row.system_id),
                "seed": int(registry_row.seed),
                "initial_condition_set": int(registry_row.initial_condition_set),
                "condition": str(registry_row.condition),
                "level_event_count": int(len(levels)),
                **base,
                "substantial_relative_threshold": float(substantial_threshold),
                "substantial_last_improvement_level": int(
                    substantial["last_improvement_level"]
                ),
                "substantial_silent_levels": int(substantial["silent_levels"]),
                "substantial_silent_fraction": float(substantial["silent_fraction"]),
            }
        )
    if seen_identities != set(by_identity):
        fail("heartbeat identities do not match registry identities one-to-one")
    return pd.DataFrame(rows)


def add_quantiles(row: dict[str, Any], prefix: str, values: pd.Series) -> None:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.isna().any() or numeric.empty:
        fail(f"{prefix} has missing, non-numeric, or empty values")
    quantiles = numeric.quantile(QUANTILES)
    for probability, value in quantiles.items():
        row[f"{prefix}_q{int(round(probability * 100)):02d}"] = float(value)


def build_waste_summary(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_columns = ["system_representability", "condition", "initial_condition_set", "system_dim"]
    for keys, group in cells.groupby(group_columns, sort=True):
        representability, condition, ic_set, dim = keys
        row: dict[str, Any] = {
            "system_representability": representability,
            "condition": condition,
            "initial_condition_set": int(ic_set),
            "system_dim": int(dim),
            "n_cells": int(len(group)),
        }
        add_quantiles(row, "silent_levels", group["silent_levels"])
        add_quantiles(row, "silent_fraction", group["silent_fraction"])
        rows.append(row)
    return pd.DataFrame(rows)


def build_waste_threshold_grid(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_columns = ["system_representability", "condition", "initial_condition_set", "system_dim"]
    for keys, group in cells.groupby(group_columns, sort=True):
        representability, condition, ic_set, dim = keys
        for threshold in SILENT_FRACTION_THRESHOLDS:
            rows.append(
                {
                    "system_representability": representability,
                    "condition": condition,
                    "initial_condition_set": int(ic_set),
                    "system_dim": int(dim),
                    "threshold": threshold,
                    "n_cells": int(len(group)),
                    "cells_above_threshold": int(group["silent_fraction"].gt(threshold).sum()),
                    "share_above_threshold": float(group["silent_fraction"].gt(threshold).mean()),
                }
            )
    return pd.DataFrame(rows)


def build_level_event_count_summary(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    counts = cells["level_event_count"].value_counts().sort_index()
    for event_count, cell_count in counts.items():
        rows.append({"level_event_count": int(event_count), "n_cells": int(cell_count)})
    return pd.DataFrame(rows)


def build_last_improvement_level1_by_dim(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim, group in cells.groupby("system_dim", sort=True):
        count = int(group["last_improvement_level"].eq(1).sum())
        rows.append(
            {
                "system_dim": int(dim),
                "n_cells": int(len(group)),
                "last_improvement_level1_cells": count,
                "share": float(count / len(group)),
            }
        )
    return pd.DataFrame(rows)


def merge_cells(registry: pd.DataFrame, heartbeat_metrics: pd.DataFrame) -> pd.DataFrame:
    cells = registry.merge(
        heartbeat_metrics,
        on=["campaign_manifest_index", "system_id", "seed", "initial_condition_set", "condition"],
        how="inner",
        validate="one_to_one",
    )
    if len(cells) != len(registry):
        fail(f"merged cell count expected {len(registry)}, got {len(cells)}")
    cells["level_count_diff_from_registry"] = cells["level_event_count"] - cells["n_levels"]
    cells["log10_loss"] = cells["loss"].map(math.log10)
    return cells


def build_system_table(cells: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_columns = [
        "system_id",
        "system_name",
        "system_dim",
        "system_representability",
        "initial_condition_set",
        "condition",
    ]
    for keys, group in cells.groupby(group_columns, sort=True):
        system_id, system_name, dim, representability, ic_set, condition = keys
        row: dict[str, Any] = {
            "system_id": int(system_id),
            "system_name": system_name,
            "system_dim": int(dim),
            "system_representability": representability,
            "initial_condition_set": int(ic_set),
            "condition": condition,
            "n_cells": int(len(group)),
            "exact_support_match_rate": "",
            "r2_median": "",
            "loss_q50": float(group["loss"].quantile(0.50)),
            "loss_q90": float(group["loss"].quantile(0.90)),
            "final_stage_q50": float(group["final_stage"].quantile(0.50)),
            "stage_caps": str(group["stage_caps"].iloc[0]),
            "total_loss_evals_q50": float(group["total_loss_evals"].quantile(0.50)),
            "total_ode_solves_q50": float(group["total_ode_solves"].quantile(0.50)),
            "total_parameter_fits_q50": float(group["total_parameter_fits"].quantile(0.50)),
            "silent_levels_q50": float(group["silent_levels"].quantile(0.50)),
            "silent_levels_sum": int(group["silent_levels"].sum()),
            "silent_fraction_q50": float(group["silent_fraction"].quantile(0.50)),
            "silent_fraction_q90": float(group["silent_fraction"].quantile(0.90)),
            "level_event_count_q50": float(group["level_event_count"].quantile(0.50)),
        }
        if representability == "exact":
            if group["exact_support_match_num"].isna().any():
                fail(f"exact_support_match is missing for exact system {system_id}")
            row["exact_support_match_rate"] = float(group["exact_support_match_num"].mean())
        elif representability == "surrogate":
            row["r2_median"] = float(group["r2"].median())
        else:
            fail(f"unexpected system_representability: {representability}")
        rows.append(row)
    table = pd.DataFrame(rows)
    if len(table) != 252:
        fail(f"system table row count expected 252, got {len(table)}")
    return table


def build_system_extracts(cells: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    group_columns = [
        "system_id",
        "system_name",
        "system_dim",
        "system_representability",
    ]
    for keys, group in cells.groupby(group_columns, sort=True):
        system_id, system_name, dim, representability = keys
        row: dict[str, Any] = {
            "system_id": int(system_id),
            "system_name": system_name,
            "system_dim": int(dim),
            "system_representability": representability,
            "n_cells": int(len(group)),
            "silent_levels_sum": int(group["silent_levels"].sum()),
            "silent_fraction_q50": float(group["silent_fraction"].quantile(0.50)),
            "silent_fraction_q90": float(group["silent_fraction"].quantile(0.90)),
            "exact_support_match_rate": "",
            "r2_median": "",
            "class_target": "",
        }
        if representability == "exact":
            row["exact_support_match_rate"] = float(group["exact_support_match_num"].mean())
            row["class_target"] = row["exact_support_match_rate"]
        elif representability == "surrogate":
            row["r2_median"] = float(group["r2"].median())
            row["class_target"] = row["r2_median"]
        else:
            fail(f"unexpected system_representability: {representability}")
        rows.append(row)
    system_extract_base = pd.DataFrame(rows)
    waste_top = (
        system_extract_base.sort_values(
            ["system_representability", "silent_levels_sum", "silent_fraction_q50", "system_id"],
            ascending=[True, False, False, True],
        )
        .groupby("system_representability", group_keys=False)
        .head(10)
        .reset_index(drop=True)
    )
    worst_target = (
        system_extract_base.sort_values(
            ["system_representability", "class_target", "system_id"],
            ascending=[True, True, True],
        )
        .groupby("system_representability", group_keys=False)
        .head(10)
        .reset_index(drop=True)
    )
    return waste_top, worst_target


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.12g")


def main() -> int:
    args = parse_args()
    config_path = (
        Path(args.config).resolve()
        if args.config
        else campaign_config_path(ANALYSIS_ROOT, args.campaign).resolve()
    )
    try:
        config = load_config(config_path) if config_path.exists() else {}
        campaign_id = str(config.get("experiment_id", args.campaign))
        if campaign_id != args.campaign:
            fail(
                f"config experiment_id {campaign_id!r} does not match "
                f"requested campaign {args.campaign!r}"
            )
        input_path = (
            Path(args.input).resolve()
            if args.input
            else (
                resolve_path(config["run_registry_path"], ANALYSIS_ROOT, config_path)
                if "run_registry_path" in config
                else campaign_registry_path(ANALYSIS_ROOT.parent, args.campaign).resolve()
            )
        )
        heartbeat_dir = (
            Path(args.heartbeat_dir).resolve()
            if args.heartbeat_dir
            else (input_path.parent / "runs" / "heartbeats").resolve()
        )
        output_dir = (
            Path(args.output_dir).resolve()
            if args.output_dir
            else (
                (ANALYSIS_ROOT / config["output_dir"]).resolve()
                if "output_dir" in config
                else campaign_data_dir(ANALYSIS_ROOT, args.campaign).resolve()
            )
        )
        registry = validate_registry(
            load_run_registry(input_path), args.expected_row_count, args.campaign
        )
        heartbeat_metrics = load_heartbeat_metrics(
            registry,
            heartbeat_dir,
            args.relative_improvement_threshold,
            args.substantial_relative_improvement_threshold,
        )
        cells = merge_cells(registry, heartbeat_metrics)
        waste_summary = build_waste_summary(cells)
        waste_threshold_grid = build_waste_threshold_grid(cells)
        level_event_counts = build_level_event_count_summary(cells)
        last_level1 = build_last_improvement_level1_by_dim(cells)
        system_table = build_system_table(cells)
        waste_top, worst_target = build_system_extracts(cells)

        outputs = {
            "heartbeat_waste_cells.csv": cells,
            "heartbeat_waste_summary.csv": waste_summary,
            "heartbeat_waste_threshold_grid.csv": waste_threshold_grid,
            "heartbeat_level_event_counts.csv": level_event_counts,
            "heartbeat_last_improvement_level1_by_dim.csv": last_level1,
            "phaseb_system_table.csv": system_table,
            "phaseb_system_waste_top10_by_class.csv": waste_top,
            "phaseb_system_worst_target_top10_by_class.csv": worst_target,
        }
        for filename, table in outputs.items():
            write_csv(table, output_dir / filename)

        mismatch_count = int(cells["level_count_diff_from_registry"].ne(0).sum())
        print("Aggregated Phase-B heartbeat waste and system tables")
        print(f"  Input: {input_path}")
        print(f"  Heartbeats: {heartbeat_dir}")
        print(f"  Output: {output_dir}")
        print(f"  Heartbeat streams: {len(heartbeat_metrics)}")
        print(f"  Level-event count values: {level_event_counts.to_dict(orient='records')}")
        print(f"  Cells where level_event_count != n_levels: {mismatch_count}")
        print(f"  System table rows: {len(system_table)}")
        print(
            "  Equal best_loss transitions: "
            f"{int(cells['equal_best_loss_transitions'].sum())}; "
            "nonmonotone best_loss transitions: "
            f"{int(cells['nonmonotone_best_loss_transitions'].sum())}"
        )
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
