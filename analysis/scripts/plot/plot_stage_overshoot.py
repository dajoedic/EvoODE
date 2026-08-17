import argparse
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.io import load_aggregate
from utils.metrics import check_required_columns
from utils.style import apply_style, ordered_variants, variant_color, variant_label


REQUIRED_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
    "mean_stage_overshoot",
    "n_valid",
]

VARIANT_ORDER = [
    "evogrow_v1",
    "evogrow_v2_1",
    "evogrow_v2_2_stage_local",
    "evogrow_v2_2_passive",
    "evogrow_v2_2_soft",
]

SURROGATE_SYSTEM_IDS = {23, 37}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot mean stage overshoot.")
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def prepare_plot_data(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, list[tuple[int, str]], list[str]]:
    exact_df = df.loc[~df["system_id"].isin(SURROGATE_SYSTEM_IDS)].copy()
    exact_df = exact_df.loc[exact_df["variant_slug"] != "gp_baseline"].copy()

    systems = (
        exact_df.loc[:, ["system_id", "system_name"]]
        .drop_duplicates()
        .sort_values("system_id")
    )
    system_order = list(systems.itertuples(index=False, name=None))
    variant_order = ordered_variants(
        exact_df["variant_slug"].dropna().unique(),
        VARIANT_ORDER,
    )

    full_index = pd.MultiIndex.from_product(
        [variant_order, [system_id for system_id, _ in system_order]],
        names=["variant_slug", "system_id"],
    )

    indexed = exact_df.set_index(["variant_slug", "system_id"])
    reindexed = indexed.reindex(full_index).reset_index()
    reindexed["mean_stage_overshoot"] = reindexed["mean_stage_overshoot"].fillna(0.0)

    return reindexed, system_order, variant_order


def y_limits(values: pd.Series) -> tuple[float, float]:
    finite_values = values.dropna().to_numpy(dtype=float)
    if finite_values.size == 0 or np.all(finite_values == 0):
        return -1.0, 2.0

    return float(np.floor(finite_values.min()) - 0.5), float(
        np.ceil(finite_values.max()) + 0.5
    )


def draw_plot(
    plot_data: pd.DataFrame,
    system_order: list[tuple[int, str]],
    variant_order: list[str],
    experiment_id: str,
) -> plt.Figure:
    apply_style()

    fig, ax = plt.subplots(figsize=(10, 4))
    x_positions = np.arange(len(system_order))
    bar_width = 0.14
    group_width = bar_width * len(variant_order)
    first_bar_offset = -group_width / 2 + bar_width / 2

    ax.axhline(0, color="black", linewidth=0.8, zorder=0)

    for variant_index, variant_slug in enumerate(variant_order):
        variant_data = plot_data.loc[plot_data["variant_slug"] == variant_slug]
        heights = variant_data["mean_stage_overshoot"].to_numpy(dtype=float)
        n_valid = variant_data["n_valid"]
        bar_positions = x_positions + first_bar_offset + variant_index * bar_width

        bars = ax.bar(
            bar_positions,
            heights,
            width=bar_width,
            color=variant_color(variant_slug),
            label=variant_label(variant_slug),
            zorder=2,
        )

        for bar, valid_count in zip(bars, n_valid):
            if pd.isna(valid_count):
                continue

            height = bar.get_height()
            if height >= 0:
                label_y = height + 0.1
                vertical_alignment = "bottom"
            else:
                label_y = height - 0.1
                vertical_alignment = "top"

            ax.text(
                bar.get_x() + bar.get_width() / 2,
                label_y,
                str(int(valid_count)),
                ha="center",
                va=vertical_alignment,
                fontsize=7,
            )

    ax.set_title(f"Stage overshoot - {experiment_id}")
    ax.set_ylabel("Mean stage overshoot")
    ax.set_ylim(*y_limits(plot_data["mean_stage_overshoot"]))
    ax.set_xticks(x_positions)
    ax.set_xticklabels(
        [system_name for _, system_name in system_order],
        rotation=20,
        ha="right",
    )
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

    return fig


def main() -> int:
    args = parse_args()
    analysis_root = Path.cwd()
    config_path = (analysis_root / args.config).resolve()

    try:
        config = load_config(config_path)
        experiment_id = config["experiment_id"]
        aggregate_path = analysis_root / config["output_dir"] / "aggregate_by_variant_system.csv"
        output_dir = analysis_root / "figures" / experiment_id

        aggregate = load_aggregate(aggregate_path)
        check_required_columns(aggregate, REQUIRED_COLUMNS)
        plot_data, system_order, variant_order = prepare_plot_data(aggregate)

        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = output_dir / "stage_overshoot.pdf"
        png_path = output_dir / "stage_overshoot.png"

        fig = draw_plot(plot_data, system_order, variant_order, experiment_id)
        fig.savefig(pdf_path, metadata={"CreationDate": None, "ModDate": None})
        fig.savefig(png_path, dpi=150, metadata={"Software": None})
        plt.close(fig)

        print(f"Saved: figures/{experiment_id}/stage_overshoot.pdf")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
