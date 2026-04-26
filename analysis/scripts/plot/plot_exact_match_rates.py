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
from utils.style import VARIANT_COLORS, VARIANT_LABELS, apply_style


REQUIRED_COLUMNS = [
    "variant_slug",
    "system_id",
    "system_name",
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

SURROGATE_SYSTEM_IDS = {23, 37}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot exact match rates.")
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def prepare_plot_data(df: pd.DataFrame) -> tuple[pd.DataFrame, list[tuple[int, str]]]:
    exact_df = df.loc[~df["system_id"].isin(SURROGATE_SYSTEM_IDS)].copy()
    systems = (
        exact_df.loc[:, ["system_id", "system_name"]]
        .drop_duplicates()
        .sort_values("system_id")
    )
    system_order = list(systems.itertuples(index=False, name=None))

    full_index = pd.MultiIndex.from_product(
        [VARIANT_ORDER, [system_id for system_id, _ in system_order]],
        names=["variant_slug", "system_id"],
    )

    indexed = exact_df.set_index(["variant_slug", "system_id"])
    reindexed = indexed.reindex(full_index).reset_index()
    reindexed["exact_match_rate"] = reindexed["exact_match_rate"].fillna(0.0)

    return reindexed, system_order


def draw_plot(
    plot_data: pd.DataFrame,
    system_order: list[tuple[int, str]],
    experiment_id: str,
) -> plt.Figure:
    apply_style()

    fig, ax = plt.subplots(figsize=(10, 4))
    x_positions = np.arange(len(system_order))
    bar_width = 0.12
    group_width = bar_width * len(VARIANT_ORDER)
    first_bar_offset = -group_width / 2 + bar_width / 2

    for variant_index, variant_slug in enumerate(VARIANT_ORDER):
        variant_data = plot_data.loc[plot_data["variant_slug"] == variant_slug]
        heights = variant_data["exact_match_rate"].to_numpy(dtype=float)
        n_valid = variant_data["n_valid"]
        bar_positions = x_positions + first_bar_offset + variant_index * bar_width

        bars = ax.bar(
            bar_positions,
            heights,
            width=bar_width,
            color=VARIANT_COLORS[variant_slug],
            label=VARIANT_LABELS[variant_slug],
        )

        for bar, valid_count in zip(bars, n_valid):
            if pd.isna(valid_count):
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.015,
                str(int(valid_count)),
                ha="center",
                va="bottom",
                fontsize=7,
            )

    ax.set_title(f"Exact match rate - {experiment_id}")
    ax.set_ylabel("Exact match rate")
    ax.set_ylim(0.0, 1.0)
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
        plot_data, system_order = prepare_plot_data(aggregate)

        output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = output_dir / "exact_match_rates.pdf"
        png_path = output_dir / "exact_match_rates.png"

        fig = draw_plot(plot_data, system_order, experiment_id)
        fig.savefig(pdf_path, metadata={"CreationDate": None, "ModDate": None})
        fig.savefig(png_path, dpi=150, metadata={"Software": None})
        plt.close(fig)

        print(f"Saved: figures/{experiment_id}/exact_match_rates.pdf")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
