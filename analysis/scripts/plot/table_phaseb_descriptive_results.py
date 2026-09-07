import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.io import load_aggregate  # noqa: E402


TABLE_SPECS = [
    (
        "descriptive_t1_surrogate_r2",
        "descriptive_t1_surrogate_r2.csv",
        "T1. Surrogate fit quality. R2 quantiles and the complete R2 threshold grid are grouped by condition, initial-condition set, and system dimension.",
    ),
    (
        "descriptive_t2_exact_fit_quality",
        "descriptive_t2_exact_fit_quality.csv",
        "T2. Exact-system fit quality. log10 loss and R2 are reported as separate metrics by condition, initial-condition set, and system dimension.",
    ),
    (
        "descriptive_t3_exact_support",
        "descriptive_t3_exact_support.csv",
        "T3. Exact-system support recovery. Counts and rates are descriptive; dimension rows keep the dim 3 and dim 4 entries visible.",
    ),
    (
        "descriptive_t4_stage_economy",
        "descriptive_t4_stage_economy.csv",
        "T4. Stage economy. elapsed_s is excluded. stage_overshoot, wasted_levels, and eq_overshoot are only shown for exact systems because surrogate expected stages are nominal.",
    ),
    (
        "descriptive_t5_robustness",
        "descriptive_t5_robustness.csv",
        "T5. Robustness and failure modes. Retcode frequencies and robustness counters are grouped by condition and exact/surrogate class.",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write descriptive Phase-B result tables as CSV and LaTeX."
    )
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def latex_escape(value: Any) -> str:
    text = "" if pd.isna(value) else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def format_value(value: Any) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:.6g}"
    return str(value)


def column_alignment(columns: list[str]) -> str:
    return "l" + ("r" * max(0, len(columns) - 1))


def dataframe_to_latex(df: pd.DataFrame, caption: str) -> str:
    columns = list(df.columns)
    lines = [
        r"% Requires: \usepackage{booktabs}",
        rf"\begin{{table}}[htbp]",
        r"\centering",
        rf"\caption{{{latex_escape(caption)}}}",
        rf"\begin{{tabular}}{{{column_alignment(columns)}}}",
        r"\toprule",
        " & ".join(latex_escape(column) for column in columns) + r" \\",
        r"\midrule",
    ]
    for _, row in df.iterrows():
        cells = [latex_escape(format_value(row[column])) for column in columns]
        lines.append(" & ".join(cells) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()

    try:
        config = load_config(config_path)
        experiment_id = config["experiment_id"]
        input_dir = (ANALYSIS_ROOT / config["output_dir"]).resolve()
        output_dir = (ANALYSIS_ROOT / "tables" / experiment_id).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        for table_name, input_name, caption in TABLE_SPECS:
            source = input_dir / input_name
            table = load_aggregate(source)
            csv_path = output_dir / f"{table_name}.csv"
            tex_path = output_dir / f"{table_name}.tex"
            table.to_csv(csv_path, index=False, float_format="%.12g")
            tex_path.write_text(dataframe_to_latex(table, caption), encoding="utf-8")
            print(f"Saved: tables/{experiment_id}/{table_name}.csv")
            print(f"Saved: tables/{experiment_id}/{table_name}.tex")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
