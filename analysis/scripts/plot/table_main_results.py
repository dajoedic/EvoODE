import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import pandas as pd

ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.io import load_aggregate
from utils.metrics import check_required_columns
from utils.style import VARIANT_LABELS


REQUIRED_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "mean_loss",
    "std_loss",
    "exact_match_rate",
    "n_valid",
]

VARIANT_ORDER = [
    "evogrow_v1",
    "evogrow_v2_1",
    "evogrow_v2_2_stage_local",
    "evogrow_v2_2_passive",
    "evogrow_v2_2_soft",
    "gp_baseline",
]

EXACT_SYSTEM_IDS = [2, 3, 11, 24, 26, 31, 54, 63]
SURROGATE_SYSTEM_IDS = [23, 37]

CSV_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "mean_loss",
    "std_loss",
    "exact_match_rate",
    "n_valid",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write Paper 1 main results table.")
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def format_scientific(value: float, significant_digits: int = 2) -> str:
    if pd.isna(value):
        return "--"
    if float(value) == 0.0:
        return "0"

    exponent = math.floor(math.log10(abs(float(value))))
    mantissa = float(value) / (10**exponent)
    decimals = max(significant_digits - 1, 0)
    mantissa_text = f"{mantissa:.{decimals}f}"
    return rf"{mantissa_text} \times 10^{{{exponent}}}"


def ordered_systems(df: pd.DataFrame, system_ids: list[int]) -> list[tuple[int, str]]:
    systems = (
        df.loc[df["system_id"].isin(system_ids), ["system_id", "system_name"]]
        .drop_duplicates()
        .sort_values("system_id")
    )
    return list(systems.itertuples(index=False, name=None))


def reindex_table_data(
    df: pd.DataFrame,
    systems: list[tuple[int, str]],
) -> pd.DataFrame:
    full_index = pd.MultiIndex.from_product(
        [VARIANT_ORDER, [system_id for system_id, _ in systems]],
        names=["variant_slug", "system_id"],
    )
    indexed = df.set_index(["variant_slug", "system_id"])
    reindexed = indexed.reindex(full_index).reset_index()

    system_names = {system_id: system_name for system_id, system_name in systems}
    reindexed["system_name"] = reindexed["system_id"].map(system_names)
    return reindexed


def build_csv_table(df: pd.DataFrame) -> pd.DataFrame:
    ordered_frames = []
    for system_ids in (EXACT_SYSTEM_IDS, SURROGATE_SYSTEM_IDS):
        systems = ordered_systems(df, system_ids)
        ordered_frames.append(reindex_table_data(df, systems))

    output = pd.concat(ordered_frames, ignore_index=True)
    return output.loc[:, CSV_COLUMNS]


def abbreviate(text: str, max_length: int = 12) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3]}..."


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
    }
    return "".join(replacements.get(char, char) for char in text)


def latex_cell(row: pd.Series, include_exact_match: bool) -> str:
    n_valid = row["n_valid"]
    if pd.isna(n_valid) or int(n_valid) == 0:
        return "--"

    mean_text = format_scientific(row["mean_loss"])
    std_text = format_scientific(row["std_loss"])
    if std_text == "--":
        loss_line = rf"${mean_text}$"
    else:
        loss_line = rf"${mean_text} \pm {std_text}$"

    if not include_exact_match:
        return rf"\makecell{{{loss_line}}}"

    exact_match_rate = row["exact_match_rate"]
    exact_match_text = "--" if pd.isna(exact_match_rate) else f"{round(exact_match_rate * 100):.0f}\\%"
    return rf"\makecell{{{loss_line}\\EM: {exact_match_text}}}"


def latex_tabular(
    title: str,
    table_data: pd.DataFrame,
    systems: list[tuple[int, str]],
    include_exact_match: bool,
) -> str:
    alignment = "l" + ("c" * len(systems))
    lines = [
        rf"% {title}",
        rf"\begin{{tabular}}{{{alignment}}}",
        r"\toprule",
    ]

    headers = ["Variant"] + [latex_escape(abbreviate(system_name)) for _, system_name in systems]
    lines.append(" & ".join(headers) + r" \\")
    lines.append(r"\midrule")

    for variant_slug in VARIANT_ORDER:
        row_cells = [latex_escape(VARIANT_LABELS[variant_slug])]
        variant_data = table_data.loc[table_data["variant_slug"] == variant_slug]
        for system_id, _ in systems:
            cell_row = variant_data.loc[variant_data["system_id"] == system_id].iloc[0]
            row_cells.append(latex_cell(cell_row, include_exact_match))
        lines.append(" & ".join(row_cells) + r" \\")

    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines)


def write_latex(df: pd.DataFrame, path: Path) -> None:
    exact_systems = ordered_systems(df, EXACT_SYSTEM_IDS)
    surrogate_systems = ordered_systems(df, SURROGATE_SYSTEM_IDS)
    exact_data = reindex_table_data(df, exact_systems)
    surrogate_data = reindex_table_data(df, surrogate_systems)

    content = "\n\n".join(
        [
            r"% Requires: \usepackage{booktabs, makecell}",
            latex_tabular("Exact systems", exact_data, exact_systems, True),
            latex_tabular("Surrogate systems", surrogate_data, surrogate_systems, False),
        ]
    )
    path.write_text(content + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    analysis_root = Path.cwd()
    config_path = (analysis_root / args.config).resolve()

    try:
        config = load_config(config_path)
        experiment_id = config["experiment_id"]
        aggregate_path = analysis_root / config["output_dir"] / "aggregate_by_variant_system.csv"
        output_dir = analysis_root / "tables" / experiment_id

        aggregate = load_aggregate(aggregate_path)
        check_required_columns(aggregate, REQUIRED_COLUMNS)

        output_dir.mkdir(parents=True, exist_ok=True)
        tex_path = output_dir / "main_results.tex"
        csv_path = output_dir / "main_results.csv"

        write_latex(aggregate, tex_path)
        build_csv_table(aggregate).to_csv(csv_path, index=False, float_format="%.6g")

        print(f"Saved: tables/{experiment_id}/main_results.tex")
        print(f"Saved: tables/{experiment_id}/main_results.csv")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
