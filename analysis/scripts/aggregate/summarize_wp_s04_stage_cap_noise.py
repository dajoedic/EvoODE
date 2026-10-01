import argparse
import math
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import check_required_columns  # noqa: E402


REQUIRED_COLUMNS = [
    "system_id",
    "dimension",
    "equation_index",
    "initial_condition_set",
    "sigma",
    "rho",
    "realization",
    "cap",
    "clean_cap",
    "reference_clean_cap",
    "cap_change_class",
    "required_stage",
    "truncates_true_terms",
    "rebuild_cap_matches_estimate",
    "clean_reference_matches_c1",
    "f4_true_sigma_prediction",
    "f4_estimated_sigma_prediction",
    "f4_measured_derivative_error",
    "f4_true_stage_residual",
    "f4_true_pred_to_measured_deriv",
    "f4_est_pred_to_measured_deriv",
    "f4_true_pred_to_true_stage_residual",
    "f4_est_pred_to_true_stage_residual",
]

RESIDUAL_COLUMNS = [f"residual_stage_{stage}" for stage in range(1, 6)]
FLOOR_COLUMNS = [f"floor_stage_{stage}" for stage in range(1, 6)]
USABLE_COLUMNS = [f"usable_splits_stage_{stage}" for stage in range(1, 6)]
RATIO_COLUMNS = [
    "f4_true_pred_to_measured_deriv",
    "f4_est_pred_to_measured_deriv",
    "f4_true_pred_to_true_stage_residual",
    "f4_est_pred_to_true_stage_residual",
]
QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize WP-S04 stage-cap noise diagnostics.")
    parser.add_argument("--input", required=True, help="Detail CSV from wp_s04_stage_cap_noise_thinning.jl.")
    parser.add_argument("--output-dir", required=True, help="Directory for F1-F4 summary tables.")
    return parser.parse_args()


def coerce_bool(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    return normalized.map({"true": True, "false": False})


def load_detail(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    check_required_columns(df, REQUIRED_COLUMNS + RESIDUAL_COLUMNS + FLOOR_COLUMNS + USABLE_COLUMNS)
    numeric_columns = [
        "system_id",
        "dimension",
        "equation_index",
        "initial_condition_set",
        "sigma",
        "rho",
        "realization",
        "required_stage",
        *RESIDUAL_COLUMNS,
        *FLOOR_COLUMNS,
        *USABLE_COLUMNS,
        "f4_true_sigma_prediction",
        "f4_estimated_sigma_prediction",
        "f4_measured_derivative_error",
        "f4_true_stage_residual",
        *RATIO_COLUMNS,
    ]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    for column in ["truncates_true_terms", "rebuild_cap_matches_estimate", "clean_reference_matches_c1"]:
        df[column] = coerce_bool(df[column])
        if df[column].isna().any():
            raise ValueError(f"{column} contains non-boolean values")
    if not df["rebuild_cap_matches_estimate"].all():
        raise ValueError("At least one rebuilt cap does not match estimate_stage_caps")
    if not df["clean_reference_matches_c1"].all():
        raise ValueError("At least one clean cap does not match the C-1 reference record")
    if df[numeric_columns].isna().any().any():
        missing = [column for column in numeric_columns if df[column].isna().any()]
        raise ValueError(f"Numeric columns contain missing/non-numeric values: {missing}")
    return df


def quantile_frame(df: pd.DataFrame, group_columns: list[str], value_columns: Iterable[str]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for key, group in df.groupby(group_columns, dropna=False, sort=True):
        if not isinstance(key, tuple):
            key = (key,)
        base = dict(zip(group_columns, key))
        for column in value_columns:
            values = pd.to_numeric(group[column], errors="coerce")
            finite = values[values.map(math.isfinite)]
            if finite.empty:
                for probability in QUANTILES:
                    row = dict(base)
                    row.update({"metric": column, "quantile": probability, "value": math.nan, "n": 0})
                    rows.append(row)
                continue
            for probability in QUANTILES:
                row = dict(base)
                row.update(
                    {
                        "metric": column,
                        "quantile": probability,
                        "value": float(finite.quantile(probability)),
                        "n": int(finite.count()),
                    }
                )
                rows.append(row)
    return pd.DataFrame(rows)


def summarize_f1(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby(["sigma", "rho", "dimension"], dropna=False, sort=True)
    return grouped.agg(
        rows=("truncates_true_terms", "size"),
        truncated_true_terms=("truncates_true_terms", "sum"),
        systems=("system_id", "nunique"),
    ).reset_index()


def summarize_f2(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["sigma", "rho", "dimension", "cap_change_class"], dropna=False, sort=True)
        .size()
        .reset_index(name="rows")
    )


def summarize_f3(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    residuals = quantile_frame(df, ["sigma", "rho", "dimension"], RESIDUAL_COLUMNS)
    floors = quantile_frame(df, ["sigma", "rho", "dimension"], FLOOR_COLUMNS)
    usable = (
        df.groupby(["sigma", "rho", "dimension"], dropna=False, sort=True)[USABLE_COLUMNS]
        .mean()
        .reset_index()
    )
    return residuals, floors, usable


def summarize_f4(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    nonclean = df.loc[(df["sigma"] > 0) | (df["rho"] > 0)].copy()
    ratios = quantile_frame(nonclean, ["sigma", "rho", "dimension"], RATIO_COLUMNS)
    levels = quantile_frame(
        df,
        ["sigma", "rho", "dimension"],
        [
            "f4_true_sigma_prediction",
            "f4_estimated_sigma_prediction",
            "f4_measured_derivative_error",
            "f4_true_stage_residual",
        ],
    )
    return ratios, levels


def markdown_table(df: pd.DataFrame, max_rows: int = 20) -> str:
    if df.empty:
        return "(empty)"
    shown = df.head(max_rows)
    headers = [str(column) for column in shown.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in shown.iterrows():
        lines.append("| " + " | ".join(str(row[column]) for column in shown.columns) + " |")
    return "\n".join(lines)


def write_summary_markdown(output_dir: Path, tables: dict[str, pd.DataFrame]) -> None:
    lines = [
        "# WP-S04 Stage-Cap Noise Summary",
        "",
        "All counts and quantiles are computed from the detail CSV. Controls abort if rebuilt caps differ from `estimate_stage_caps` or clean caps differ from the C-1 reference records.",
        "",
        "## F1 Safety",
        "",
        markdown_table(tables["f1_safety"]),
        "",
        "## F2 Behavior",
        "",
        markdown_table(tables["f2_behavior"]),
        "",
        "## F3 Residuals",
        "",
        markdown_table(tables["f3_residual_quantiles"]),
        "",
        "## F4 Ratios",
        "",
        markdown_table(tables["f4_ratio_quantiles"]),
        "",
    ]
    (output_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_outputs(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    tables: dict[str, pd.DataFrame] = {}
    tables["f1_safety"] = summarize_f1(df)
    tables["f2_behavior"] = summarize_f2(df)
    f3_residuals, f3_floors, f3_usable = summarize_f3(df)
    tables["f3_residual_quantiles"] = f3_residuals
    tables["f3_floor_quantiles"] = f3_floors
    tables["f3_usable_split_means"] = f3_usable
    f4_ratios, f4_levels = summarize_f4(df)
    tables["f4_ratio_quantiles"] = f4_ratios
    tables["f4_level_quantiles"] = f4_levels

    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False)
    write_summary_markdown(output_dir, tables)


def main() -> int:
    args = parse_args()
    try:
        detail = load_detail(Path(args.input))
        write_outputs(detail, Path(args.output_dir))
        print("WP-S04 summary completed")
        print(f"  Rows: {len(detail)}")
        print(f"  Output: {Path(args.output_dir)}")
        return 0
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
