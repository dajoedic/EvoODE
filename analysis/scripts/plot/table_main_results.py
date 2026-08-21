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
from utils.style import ordered_variants, variant_label


REQUIRED_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "mean_loss",
    "std_loss",
    "exact_match_rate",
    "n_valid",
]

CLASSIFICATION_REQUIRED_COLUMNS = [
    "system_id",
    "representability",
]

VARIANT_ORDER = [
    "evogrow_v1",
    "evogrow_v2_1",
    "evogrow_v2_2_stage_local",
    "evogrow_v2_2_passive",
    "evogrow_v2_2_soft",
    "gp_baseline",
]

CSV_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "mean_loss",
    "std_loss",
    "exact_match_rate",
    "n_valid",
]

EXACT_CSV_COLUMNS = CSV_COLUMNS
SURROGATE_CSV_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "mean_loss",
    "std_loss",
    "mean_r2",
    "n_r2",
    "n_valid",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write Paper 1 main results table.")
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


def observed_system_ids(df: pd.DataFrame) -> set[int]:
    return {
        int(system_id)
        for system_id in pd.to_numeric(df["system_id"], errors="raise").astype(int).unique()
    }


def classify_from_file(path: Path, aggregate: pd.DataFrame) -> tuple[list[int], list[int], str]:
    if not path.exists():
        raise FileNotFoundError(f"System classification CSV does not exist: {path}")

    classification = pd.read_csv(path)
    check_required_columns(classification, CLASSIFICATION_REQUIRED_COLUMNS)

    classification = classification.copy()
    classification["system_id"] = pd.to_numeric(
        classification["system_id"], errors="raise"
    ).astype(int)
    classification["representability"] = (
        classification["representability"].astype(str).str.strip().str.lower()
    )

    by_system = classification.groupby("system_id")["representability"].agg(list)
    exact_ids = {
        int(system_id)
        for system_id, values in by_system.items()
        if all(value == "exact" for value in values)
    }
    classified_ids = set(int(system_id) for system_id in by_system.index)
    surrogate_ids = classified_ids.difference(exact_ids)

    observed_ids = observed_system_ids(aggregate)
    overlap = observed_ids.intersection(classified_ids)
    if not overlap:
        raise ValueError(
            "System classification does not cover any observed system. "
            f"Observed systems: {sorted(observed_ids)}; classified systems: "
            f"{sorted(classified_ids)}."
        )

    missing = observed_ids.difference(classified_ids)
    if missing:
        raise ValueError(
            "Observed systems without classification entry: "
            f"{sorted(missing)}. Observed systems: {sorted(observed_ids)}."
        )

    return (
        sorted(observed_ids.intersection(exact_ids)),
        sorted(observed_ids.intersection(surrogate_ids)),
        "classification",
    )


def classify_from_phase_a_support(aggregate: pd.DataFrame) -> tuple[list[int], list[int], str]:
    observed_ids = observed_system_ids(aggregate)
    exact_ids: list[int] = []
    surrogate_ids: list[int] = []
    for system_id in sorted(observed_ids):
        system_rows = aggregate.loc[aggregate["system_id"] == system_id]
        if system_rows["exact_match_rate"].notna().any():
            exact_ids.append(system_id)
        else:
            surrogate_ids.append(system_id)

    return exact_ids, surrogate_ids, "phase_a_support_fallback"


def classify_systems(
    config: dict[str, Any], config_path: Path, analysis_root: Path, aggregate: pd.DataFrame
) -> tuple[list[int], list[int], str]:
    classification_value = config.get("system_classification_path")
    if classification_value:
        return classify_from_file(
            resolve_path(str(classification_value), analysis_root, config_path), aggregate
        )
    return classify_from_phase_a_support(aggregate)


def require_non_empty_selection(
    aggregate: pd.DataFrame,
    exact_systems: list[tuple[int, str]],
    surrogate_systems: list[tuple[int, str]],
    variant_order: list[str],
) -> None:
    observed_ids = sorted(observed_system_ids(aggregate))
    observed_variants = sorted(str(variant) for variant in aggregate["variant_slug"].dropna().unique())
    if not variant_order:
        raise ValueError(
            "No variants selected for main results table. "
            f"Observed variants: {observed_variants}."
        )
    if not exact_systems and not surrogate_systems:
        raise ValueError(
            "No systems selected for main results table. "
            f"Observed systems: {observed_ids}."
        )


def reindex_table_data(
    df: pd.DataFrame,
    systems: list[tuple[int, str]],
    variant_order: list[str],
) -> pd.DataFrame:
    full_index = pd.MultiIndex.from_product(
        [variant_order, [system_id for system_id, _ in systems]],
        names=["variant_slug", "system_id"],
    )
    indexed = df.set_index(["variant_slug", "system_id"])
    reindexed = indexed.reindex(full_index).reset_index()

    system_names = {system_id: system_name for system_id, system_name in systems}
    reindexed["system_name"] = reindexed["system_id"].map(system_names)
    return reindexed


def build_csv_table(
    df: pd.DataFrame, exact_ids: list[int], surrogate_ids: list[int]
) -> pd.DataFrame:
    variant_order = ordered_variants(df["variant_slug"].dropna().unique(), VARIANT_ORDER)
    ordered_frames = []
    for system_ids in (exact_ids, surrogate_ids):
        systems = ordered_systems(df, system_ids)
        if systems:
            ordered_frames.append(reindex_table_data(df, systems, variant_order))

    if not ordered_frames:
        raise ValueError("No systems selected for CSV table.")
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


def latex_cell(row: pd.Series, metric: str) -> str:
    n_valid = row["n_valid"]
    if pd.isna(n_valid) or int(n_valid) == 0:
        return "--"

    mean_text = format_scientific(row["mean_loss"])
    std_text = format_scientific(row["std_loss"])
    if std_text == "--":
        loss_line = rf"${mean_text}$"
    else:
        loss_line = rf"${mean_text} \pm {std_text}$"

    if metric == "none":
        return rf"\makecell{{{loss_line}}}"

    if metric == "exact_match":
        exact_match_rate = row["exact_match_rate"]
        exact_match_text = "--" if pd.isna(exact_match_rate) else f"{round(exact_match_rate * 100):.0f}\\%"
        return rf"\makecell{{{loss_line}\\EM: {exact_match_text}}}"

    r2 = row.get("mean_r2", math.nan)
    n_r2 = row.get("n_r2", 0)
    r2_text = "--" if pd.isna(r2) or int(n_r2) == 0 else f"{float(r2):.3g}"
    return rf"\makecell{{{loss_line}\\$R^2$: {r2_text}}}"


def latex_tabular(
    title: str,
    table_data: pd.DataFrame,
    systems: list[tuple[int, str]],
    variant_order: list[str],
    metric: str,
) -> str:
    if not systems:
        return ""

    alignment = "l" + ("c" * len(systems))
    lines = [
        rf"% {title}",
        rf"\begin{{tabular}}{{{alignment}}}",
        r"\toprule",
    ]

    headers = ["Variant"] + [latex_escape(abbreviate(system_name)) for _, system_name in systems]
    lines.append(" & ".join(headers) + r" \\")
    lines.append(r"\midrule")

    for variant_slug in variant_order:
        row_cells = [latex_escape(variant_label(variant_slug))]
        variant_data = table_data.loc[table_data["variant_slug"] == variant_slug]
        for system_id, _ in systems:
            cell_row = variant_data.loc[variant_data["system_id"] == system_id].iloc[0]
            row_cells.append(latex_cell(cell_row, metric))
        lines.append(" & ".join(row_cells) + r" \\")

    lines.extend([r"\bottomrule", r"\end{tabular}"])
    return "\n".join(lines)


def write_latex(
    df: pd.DataFrame,
    path: Path,
    exact_ids: list[int],
    surrogate_ids: list[int],
) -> None:
    exact_systems = ordered_systems(df, exact_ids)
    surrogate_systems = ordered_systems(df, surrogate_ids)
    variant_order = ordered_variants(df["variant_slug"].dropna().unique(), VARIANT_ORDER)
    require_non_empty_selection(df, exact_systems, surrogate_systems, variant_order)
    exact_data = reindex_table_data(df, exact_systems, variant_order)
    surrogate_data = reindex_table_data(df, surrogate_systems, variant_order)

    tables = [r"% Requires: \usepackage{booktabs, makecell}"]
    if exact_systems:
        tables.append(
            latex_tabular("Exact systems", exact_data, exact_systems, variant_order, "exact_match")
        )
    if surrogate_systems:
        surrogate_metric = "r2" if "mean_r2" in df.columns and "n_r2" in df.columns else "none"
        tables.append(
            latex_tabular(
                "Surrogate systems",
                surrogate_data,
                surrogate_systems,
                variant_order,
                surrogate_metric,
            )
        )
    content = "\n\n".join(tables)
    path.write_text(content + "\n", encoding="utf-8")


def write_split_csv_tables(
    df: pd.DataFrame,
    output_dir: Path,
    exact_ids: list[int],
    surrogate_ids: list[int],
) -> None:
    variant_order = ordered_variants(df["variant_slug"].dropna().unique(), VARIANT_ORDER)
    exact_systems = ordered_systems(df, exact_ids)
    surrogate_systems = ordered_systems(df, surrogate_ids)

    if exact_systems:
        exact_data = reindex_table_data(df, exact_systems, variant_order)
        exact_data.loc[:, EXACT_CSV_COLUMNS].to_csv(
            output_dir / "exact_systems_summary.csv", index=False, float_format="%.6g"
        )
    if surrogate_systems:
        surrogate_data = reindex_table_data(df, surrogate_systems, variant_order)
        columns = [column for column in SURROGATE_CSV_COLUMNS if column in surrogate_data.columns]
        surrogate_data.loc[:, columns].to_csv(
            output_dir / "surrogate_systems_summary.csv", index=False, float_format="%.6g"
        )


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
        exact_ids, surrogate_ids, classification_mode = classify_systems(
            config, config_path, analysis_root, aggregate
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        tex_path = output_dir / "main_results.tex"
        csv_path = output_dir / "main_results.csv"

        write_latex(aggregate, tex_path, exact_ids, surrogate_ids)
        build_csv_table(aggregate, exact_ids, surrogate_ids).to_csv(
            csv_path, index=False, float_format="%.6g"
        )
        if classification_mode == "classification" or "mean_r2" in aggregate.columns:
            write_split_csv_tables(aggregate, output_dir, exact_ids, surrogate_ids)

        print(f"Saved: tables/{experiment_id}/main_results.tex")
        print(f"Saved: tables/{experiment_id}/main_results.csv")
        print(
            f"System classification: {classification_mode}; "
            f"{len(exact_ids)} exact, {len(surrogate_ids)} surrogate"
        )
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
