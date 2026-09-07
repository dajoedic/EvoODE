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
from utils.metrics import check_required_columns  # noqa: E402


SENTINEL_LOSS = 1e6
QUANTILES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
R2_THRESHOLDS = [0.5, 0.9, 0.99, 0.999]
SUPPORT_RATE_THRESHOLDS = [0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0]
EXPECTED_ROW_COUNT = 756
EXPECTED_EXACT_ROWS = 240
EXPECTED_SURROGATE_ROWS = 516

RETCODE_COLUMNS = ["solver_retcodes", "optimizer_retcodes"]
ROBUSTNESS_COUNTER_COLUMNS = [
    "total_diverged_solves",
    "total_invalid_solves",
    "total_nonfinite_solves",
    "total_solver_unstable_solves",
    "total_step_limit_solves",
    "total_optimizer_limit_hits",
    "total_optimizer_budget_stop_fits",
]
BASE_REQUIRED_COLUMNS = [
    "system_id",
    "system_name",
    "system_dim",
    "system_representability",
    "seed",
    "initial_condition_set",
    "condition",
    "success",
    "failure_reason",
    "loss",
    "r2",
    "exact_support_match",
    "final_stage",
    "stage_caps",
    "eq_final_stages",
    "n_levels",
    "total_loss_evals",
    "total_ode_solves",
    "total_parameter_fits",
    "stage_overshoot",
    "wasted_levels",
    "eq_overshoot",
    *RETCODE_COLUMNS,
    *ROBUSTNESS_COUNTER_COLUMNS,
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate descriptive Phase-B table inputs."
    )
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    parser.add_argument(
        "--input",
        help="Optional run_registry.csv override, used for fixture error-path checks.",
    )
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
        return analysis_relative.resolve()
    config_relative = config_path.parent / path
    if config_relative.exists():
        return config_relative.resolve()
    return analysis_relative.resolve()


def fail(message: str) -> None:
    raise ValueError(message)


def parse_json_cell(
    value: Any, column: str, row_number: int, allow_null_value: bool = False
) -> Any:
    if pd.isna(value):
        if allow_null_value:
            return None
        fail(f"{column} is missing at row {row_number}")
    text = str(value).strip()
    if not text:
        fail(f"{column} is empty at row {row_number}")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"{column} is not valid JSON at row {row_number}: {exc}")


def coerce_bool_series(series: pd.Series, column: str) -> pd.Series:
    mapping = {
        "true": True,
        "1": True,
        "yes": True,
        "y": True,
        "false": False,
        "0": False,
        "no": False,
        "n": False,
    }
    coerced = series.astype(str).str.strip().str.lower().map(mapping)
    if coerced.isna().any():
        fail(f"{column} contains non-boolean values")
    return coerced


def coerce_optional_bool_series(series: pd.Series, column: str) -> pd.Series:
    mapping = {
        "true": 1,
        "1": 1,
        "yes": 1,
        "y": 1,
        "false": 0,
        "0": 0,
        "no": 0,
        "n": 0,
    }
    text = series.astype(str).str.strip().str.lower()
    missing = series.isna() | text.isin(["", "nan", "none", "null"])
    coerced = text.map(mapping)
    invalid = coerced.isna() & ~missing
    if invalid.any():
        fail(f"{column} contains non-boolean values")
    return coerced.mask(missing)


def require_no_missing(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        text = df[column].astype(str).str.strip().str.lower()
        missing = df[column].isna() | text.isin(["", "nan", "none", "null"])
        if missing.any():
            fail(f"{column} is missing or empty in {int(missing.sum())} rows")


def add_quantiles(rows: list[dict[str, Any]], prefix: str, values: pd.Series) -> None:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.isna().any() or numeric.empty:
        fail(f"{prefix} has missing, non-numeric, or empty values")
    quantiles = numeric.quantile(QUANTILES)
    target = rows[-1]
    for probability, value in quantiles.items():
        target[f"{prefix}_q{int(round(probability * 100)):02d}"] = float(value)


def proportion(numerator: int, denominator: int) -> float:
    if denominator == 0:
        fail("cannot compute proportion with zero denominator")
    return float(numerator / denominator)


def summarize_quantile_group(
    group: pd.DataFrame,
    value_column: str,
    prefix: str,
    extra: dict[str, Any],
) -> dict[str, Any]:
    row = {**extra, "n_cells": int(len(group))}
    rows = [row]
    add_quantiles(rows, prefix, group[value_column])
    return rows[0]


def serialize_stage_value(value: Any) -> str:
    parsed = value
    if isinstance(value, str):
        parsed = json.loads(value)
    return json.dumps(parsed, ensure_ascii=True, separators=(",", ":"))


def validate_registry(df: pd.DataFrame) -> pd.DataFrame:
    check_required_columns(df, BASE_REQUIRED_COLUMNS)
    registry = df.copy()

    for row_number, row in enumerate(registry.itertuples(index=False), start=2):
        row_dict = row._asdict()
        for column in RETCODE_COLUMNS:
            parsed = parse_json_cell(row_dict[column], column, row_number)
            if not isinstance(parsed, list):
                fail(f"{column} must decode to a JSON array at row {row_number}")
        for column in ["stage_caps", "eq_final_stages"]:
            parsed = parse_json_cell(row_dict[column], column, row_number)
            if not isinstance(parsed, list):
                fail(f"{column} must decode to a JSON array at row {row_number}")
        eq_overshoot = parse_json_cell(
            row_dict["eq_overshoot"], "eq_overshoot", row_number, allow_null_value=True
        )
        if eq_overshoot is not None and not isinstance(eq_overshoot, list):
            fail(f"eq_overshoot must decode to null or a JSON array at row {row_number}")

    if len(registry) != EXPECTED_ROW_COUNT:
        fail(f"row count expected {EXPECTED_ROW_COUNT}, got {len(registry)}")

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
        *ROBUSTNESS_COUNTER_COLUMNS,
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
            "success",
            "loss",
            "r2",
            "final_stage",
            "n_levels",
            "total_loss_evals",
            "total_ode_solves",
            "total_parameter_fits",
            *ROBUSTNESS_COUNTER_COLUMNS,
        ],
    )
    if registry["loss"].eq(SENTINEL_LOSS).any():
        fail(f"sentinel loss {SENTINEL_LOSS:g} found in run_registry.csv")
    if registry["loss"].le(0).any():
        fail("loss must be positive for log10 summaries")

    registry["success_bool"] = coerce_bool_series(registry["success"], "success")
    registry["exact_support_match_num"] = coerce_optional_bool_series(
        registry["exact_support_match"], "exact_support_match"
    )
    registry["system_representability"] = (
        registry["system_representability"].astype(str).str.strip().str.lower()
    )
    registry["condition"] = registry["condition"].astype(str).str.strip()
    registry["initial_condition_set"] = registry["initial_condition_set"].astype(int)
    registry["system_dim"] = registry["system_dim"].astype(int)
    registry["system_id"] = registry["system_id"].astype(int)
    registry["log10_loss"] = registry["loss"].map(math.log10)

    counts = registry["system_representability"].value_counts().to_dict()
    exact_rows = int(counts.get("exact", 0))
    surrogate_rows = int(counts.get("surrogate", 0))
    if exact_rows != EXPECTED_EXACT_ROWS or surrogate_rows != EXPECTED_SURROGATE_ROWS:
        fail(
            "representability counts expected "
            f"exact={EXPECTED_EXACT_ROWS}, surrogate={EXPECTED_SURROGATE_ROWS}; "
            f"got exact={exact_rows}, surrogate={surrogate_rows}"
        )

    exact = registry["system_representability"].eq("exact")
    surrogate = registry["system_representability"].eq("surrogate")
    if registry.loc[exact, "exact_support_match_num"].isna().any():
        fail("exact_support_match is missing for exact systems")
    if registry.loc[surrogate, "exact_support_match_num"].notna().any():
        fail("exact_support_match is populated for surrogate systems")
    for column in ["stage_overshoot", "wasted_levels"]:
        registry[column] = pd.to_numeric(registry[column], errors="coerce")
        if registry.loc[exact, column].isna().any():
            fail(f"{column} is missing for exact systems")

    identities = registry[["system_id", "seed", "initial_condition_set", "condition"]]
    if identities.duplicated().any():
        fail("duplicate cells found for system_id, seed, initial_condition_set, condition")

    return registry


def build_t1(registry: pd.DataFrame) -> pd.DataFrame:
    subset = registry.loc[registry["system_representability"].eq("surrogate")]
    rows = []
    for keys, group in subset.groupby(["condition", "initial_condition_set", "system_dim"], sort=True):
        condition, ic_set, dim = keys
        row = summarize_quantile_group(
            group,
            "r2",
            "r2",
            {
                "condition": condition,
                "initial_condition_set": int(ic_set),
                "system_dim": int(dim),
            },
        )
        for threshold in R2_THRESHOLDS:
            row[f"share_r2_gt_{str(threshold).replace('.', '_')}"] = proportion(
                int(group["r2"].gt(threshold).sum()), int(len(group))
            )
        rows.append(row)
    return pd.DataFrame(rows)


def build_t2(registry: pd.DataFrame) -> pd.DataFrame:
    subset = registry.loc[registry["system_representability"].eq("exact")]
    rows = []
    for metric, value_column in [("log10_loss", "log10_loss"), ("r2", "r2")]:
        for keys, group in subset.groupby(
            ["condition", "initial_condition_set", "system_dim"], sort=True
        ):
            condition, ic_set, dim = keys
            rows.append(
                summarize_quantile_group(
                    group,
                    value_column,
                    "value",
                    {
                        "metric": metric,
                        "condition": condition,
                        "initial_condition_set": int(ic_set),
                        "system_dim": int(dim),
                    },
                )
            )
    return pd.DataFrame(rows)


def build_t3(registry: pd.DataFrame) -> pd.DataFrame:
    subset = registry.loc[registry["system_representability"].eq("exact")]
    rows = []
    for keys, group in subset.groupby(
        ["condition", "initial_condition_set", "system_dim", "system_id", "system_name"],
        sort=True,
    ):
        condition, ic_set, dim, system_id, system_name = keys
        n_cells = int(len(group))
        matches = int(group["exact_support_match_num"].sum())
        rows.append(
            {
                "aggregation_level": "system",
                "condition": condition,
                "initial_condition_set": int(ic_set),
                "system_dim": int(dim),
                "system_id": int(system_id),
                "system_name": system_name,
                "n_cells": n_cells,
                "support_match_count": matches,
                "support_match_rate": proportion(matches, n_cells),
            }
        )
    for keys, group in subset.groupby(["condition", "initial_condition_set", "system_dim"], sort=True):
        condition, ic_set, dim = keys
        n_cells = int(len(group))
        matches = int(group["exact_support_match_num"].sum())
        row = {
            "aggregation_level": "dimension",
            "condition": condition,
            "initial_condition_set": int(ic_set),
            "system_dim": int(dim),
            "system_id": "",
            "system_name": "",
            "n_cells": n_cells,
            "support_match_count": matches,
            "support_match_rate": proportion(matches, n_cells),
        }
        system_rates = group.groupby("system_id")["exact_support_match_num"].mean()
        for threshold in SUPPORT_RATE_THRESHOLDS:
            row[f"share_system_rate_ge_{str(round(threshold, 6)).replace('.', '_')}"] = proportion(
                int(system_rates.ge(threshold).sum()), int(len(system_rates))
            )
        rows.append(row)
    return pd.DataFrame(rows)


def build_t4(registry: pd.DataFrame) -> pd.DataFrame:
    base_metrics = [
        ("final_stage", "final_stage"),
        ("n_levels", "n_levels"),
        ("total_loss_evals", "total_loss_evals"),
        ("total_ode_solves", "total_ode_solves"),
        ("total_parameter_fits", "total_parameter_fits"),
    ]
    exact_only_metrics = [
        ("stage_overshoot", "stage_overshoot"),
        ("wasted_levels", "wasted_levels"),
    ]
    rows = []
    for representability, subset in registry.groupby("system_representability", sort=True):
        metrics = list(base_metrics)
        if representability == "exact":
            metrics.extend(exact_only_metrics)
        for metric, value_column in metrics:
            for keys, group in subset.groupby(
                ["condition", "initial_condition_set", "system_dim"], sort=True
            ):
                condition, ic_set, dim = keys
                row = summarize_quantile_group(
                    group,
                    value_column,
                    "value",
                    {
                        "system_representability": representability,
                        "metric": metric,
                        "condition": condition,
                        "initial_condition_set": int(ic_set),
                        "system_dim": int(dim),
                    },
                )
                if metric == "final_stage":
                    row["stage_caps"] = serialize_stage_value(group["stage_caps"].iloc[0])
                    row["eq_final_stages"] = serialize_stage_value(group["eq_final_stages"].iloc[0])
                else:
                    row["stage_caps"] = ""
                    row["eq_final_stages"] = ""
                rows.append(row)

        if representability == "exact":
            eq_rows = []
            for _, source_row in subset.iterrows():
                parsed = json.loads(str(source_row["eq_overshoot"]))
                if not isinstance(parsed, list):
                    fail("eq_overshoot for exact systems must be a JSON array")
                item = source_row.copy()
                try:
                    item["eq_overshoot_sum"] = sum(float(value) for value in parsed)
                except (TypeError, ValueError) as exc:
                    raise ValueError("eq_overshoot contains non-numeric entries") from exc
                eq_rows.append(item)
            eq_subset = pd.DataFrame(eq_rows)
            for keys, group in eq_subset.groupby(
                ["condition", "initial_condition_set", "system_dim"], sort=True
            ):
                condition, ic_set, dim = keys
                rows.append(
                    summarize_quantile_group(
                        group,
                        "eq_overshoot_sum",
                        "value",
                        {
                            "system_representability": representability,
                            "metric": "eq_overshoot_sum",
                            "condition": condition,
                            "initial_condition_set": int(ic_set),
                            "system_dim": int(dim),
                            "stage_caps": "",
                            "eq_final_stages": "",
                        },
                    )
                )
    return pd.DataFrame(rows)


def count_retcodes(group: pd.DataFrame, column: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in group[column]:
        for retcode in json.loads(str(value)):
            key = str(retcode)
            counts[key] = counts.get(key, 0) + 1
    return counts


def build_t5(registry: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for keys, group in registry.groupby(["condition", "system_representability"], sort=True):
        condition, representability = keys
        n_cells = int(len(group))
        row: dict[str, Any] = {
            "condition": condition,
            "system_representability": representability,
            "n_cells": n_cells,
            "success_true_cells": int(group["success_bool"].sum()),
            "failure_reason_set_cells": int(
                (
                    group["failure_reason"].notna()
                    & ~group["failure_reason"]
                    .astype(str)
                    .str.strip()
                    .isin(["", "nan", "None"])
                ).sum()
            ),
        }
        for column in ROBUSTNESS_COUNTER_COLUMNS:
            values = pd.to_numeric(group[column], errors="coerce")
            if values.isna().any():
                fail(f"{column} has non-numeric values")
            row[f"{column}_sum"] = int(values.sum())
            row[f"{column}_nonzero_cells"] = int(values.ne(0).sum())
        for column in RETCODE_COLUMNS:
            for retcode, count in sorted(count_retcodes(group, column).items()):
                row[f"{column}_{retcode}_count"] = int(count)
        rows.append(row)
    return pd.DataFrame(rows).fillna(0)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.12g")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()

    try:
        config = load_config(config_path)
        input_path = (
            Path(args.input).resolve()
            if args.input
            else resolve_path(config["run_registry_path"], ANALYSIS_ROOT, config_path)
        )
        output_dir = (ANALYSIS_ROOT / config["output_dir"]).resolve()
        registry = validate_registry(load_run_registry(input_path))

        tables = {
            "descriptive_t1_surrogate_r2.csv": build_t1(registry),
            "descriptive_t2_exact_fit_quality.csv": build_t2(registry),
            "descriptive_t3_exact_support.csv": build_t3(registry),
            "descriptive_t4_stage_economy.csv": build_t4(registry),
            "descriptive_t5_robustness.csv": build_t5(registry),
        }
        for filename, table in tables.items():
            write_csv(table, output_dir / filename)

        success_total = int(registry["success_bool"].sum())
        failure_reason_total = int(
            (
                registry["failure_reason"].notna()
                & ~registry["failure_reason"]
                .astype(str)
                .str.strip()
                .isin(["", "nan", "None"])
            ).sum()
        )
        print("Aggregated Phase-B descriptive tables")
        print(f"  Input: {input_path}")
        print(f"  Output: {output_dir}")
        print(f"  Rows: total={len(registry)}, exact={EXPECTED_EXACT_ROWS}, surrogate={EXPECTED_SURROGATE_ROWS}")
        print(f"  Success true cells: {success_total}")
        print(f"  Failure reason cells: {failure_reason_total}")
        for filename, table in tables.items():
            print(f"  {filename}: {len(table)} rows")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
