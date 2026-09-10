import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from scipy.stats import wilcoxon


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.io import load_run_registry  # noqa: E402
from utils.campaign import require_single_campaign_id  # noqa: E402
from utils.metrics import check_required_columns  # noqa: E402
from utils.paired_stats import (  # noqa: E402
    cluster_bootstrap_ci,
    cluster_permutation_p,
    cluster_values,
    coerce_bool,
    contingency_table,
    exact_binomial_two_sided,
    fail,
    mean,
    median,
    pair_registry_by_conditions,
)


PRETUNE_ON = "evogrow_v2_2_stage_capped_pretune_on"
PRETUNE_OFF = "evogrow_v2_2_stage_capped_pretune_off"
SENTINEL_LOSS = 1e6

# Fixed seed and repetition counts make the only allowed randomization reproducible.
RANDOM_SEED = 20260907
PERMUTATION_COUNT = 100_000
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_ALPHA = 0.05

REQUIRED_COLUMNS = [
    "experiment_id",
    "variant_slug",
    "system_id",
    "system_name",
    "system_dim",
    "system_representability",
    "seed",
    "initial_condition_set",
    "loss",
    "exact_support_match",
    "r2",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze the paired Phase-B pretuning contrast."
    )
    parser.add_argument("--campaign")
    parser.add_argument("--config", required=True, help="Path to config JSON.")
    parser.add_argument(
        "--input",
        help="Optional run_registry.csv override, used for fixtures and error-path checks.",
    )
    parser.add_argument("--output", help="Optional JSON output path override.")
    parser.add_argument("--expected-total-pairs", type=int, default=378)
    parser.add_argument("--expected-exact-pairs", type=int, default=120)
    parser.add_argument("--expected-surrogate-pairs", type=int, default=258)
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


def coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    coerced = df.copy()
    for column in columns:
        coerced[column] = pd.to_numeric(coerced[column], errors="coerce")
    return coerced

def condition_from_variant(variant_slug: str) -> str:
    if variant_slug == PRETUNE_ON:
        return "pretune_on"
    if variant_slug == PRETUNE_OFF:
        return "pretune_off"
    fail(f"Unexpected variant_slug for pretuning contrast: {variant_slug}")
    raise AssertionError("unreachable")


def validate_registry(df: pd.DataFrame, campaign_id: str) -> pd.DataFrame:
    check_required_columns(df, REQUIRED_COLUMNS)
    require_single_campaign_id(df, campaign_id, "run_registry")
    registry = coerce_numeric(df, ["system_id", "system_dim", "loss", "r2"])
    registry["condition"] = registry["variant_slug"].astype(str).map(condition_from_variant)

    if registry["loss"].isna().any():
        fail("loss is missing or non-numeric in at least one row")
    if (registry["loss"] == SENTINEL_LOSS).any():
        fail(f"sentinel loss {SENTINEL_LOSS:g} found in run_registry.csv")
    if registry["r2"].isna().any():
        fail("r2 is missing or non-numeric in at least one row")
    if (registry["loss"] <= 0).any():
        fail("loss must be positive for log10 analysis")
    return registry


def pair_registry(
    registry: pd.DataFrame,
    expected_total_pairs: int,
    expected_exact_pairs: int,
    expected_surrogate_pairs: int,
) -> pd.DataFrame:
    key_columns = ["system_id", "seed", "initial_condition_set"]
    pairs = pair_registry_by_conditions(
        registry,
        key_columns=key_columns,
        condition_column="condition",
        left_condition="pretune_on",
        right_condition="pretune_off",
        expected_total_pairs=expected_total_pairs,
    )
    pair_rows: list[dict[str, Any]] = []
    for key, on, off in pairs:
        if on["system_representability"] != off["system_representability"]:
            fail(f"representability mismatch within pair {key}")
        if int(on["system_dim"]) != int(off["system_dim"]):
            fail(f"system_dim mismatch within pair {key}")
        pair_rows.append(
            {
                "system_id": int(on["system_id"]),
                "system_name": str(on["system_name"]),
                "system_dim": int(on["system_dim"]),
                "system_representability": str(on["system_representability"]).strip(),
                "seed": str(on["seed"]),
                "initial_condition_set": str(on["initial_condition_set"]),
                "exact_support_match_on": coerce_bool(on["exact_support_match"]),
                "exact_support_match_off": coerce_bool(off["exact_support_match"]),
                "r2_on": float(on["r2"]),
                "r2_off": float(off["r2"]),
                "loss_on": float(on["loss"]),
                "loss_off": float(off["loss"]),
            }
        )

    paired = pd.DataFrame(pair_rows)
    if len(paired) != expected_total_pairs:
        fail(f"total pairs expected {expected_total_pairs}, got {len(paired)}")

    counts = paired["system_representability"].value_counts().to_dict()
    exact_pairs = int(counts.get("exact", 0))
    surrogate_pairs = int(counts.get("surrogate", 0))
    if exact_pairs != expected_exact_pairs or surrogate_pairs != expected_surrogate_pairs:
        fail(
            "pair counts expected "
            f"exact={expected_exact_pairs}, surrogate={expected_surrogate_pairs}; "
            f"got exact={exact_pairs}, surrogate={surrogate_pairs}"
        )
    return paired

def analyze_exact_support(pairs: pd.DataFrame, rng: random.Random) -> dict[str, Any]:
    exact = pairs.loc[pairs["system_representability"] == "exact"].copy()
    if exact.empty:
        fail("exact_support_match target is empty for exact systems")
    if exact["exact_support_match_on"].isna().any() or exact["exact_support_match_off"].isna().any():
        fail("exact_support_match is missing or non-binary for exact systems")

    exact["support_diff"] = (
        exact["exact_support_match_on"] - exact["exact_support_match_off"]
    )
    table = contingency_table(exact)
    discordant = table["off_0_on_1"] + table["off_1_on_0"]
    naive_p = exact_binomial_two_sided(discordant, table["off_1_on_0"])
    clusters = cluster_values(exact, "support_diff")
    effect = mean(exact["support_diff"].astype(float).tolist())
    ci = cluster_bootstrap_ci(clusters, mean, rng, BOOTSTRAP_REPLICATES)
    cluster_p = cluster_permutation_p(clusters, sum, rng, PERMUTATION_COUNT)

    dimension_rows = []
    for dim, group in exact.groupby("system_dim", sort=True):
        dim_table = contingency_table(group)
        dimension_rows.append({"system_dim": int(dim), "n_pairs": int(len(group)), **dim_table})

    return {
        "target": "exact_support_match",
        "system_representability": "exact",
        "n_pairs": int(len(exact)),
        "n_systems": int(exact["system_id"].nunique()),
        "contingency_table": table,
        "test_statistic": {
            "hit_count_difference_on_minus_off": int(exact["support_diff"].sum()),
            "discordant_pairs": int(discordant),
        },
        "naive_exact_mcnemar_p": naive_p,
        "cluster_permutation_p": cluster_p,
        "effect_size": {
            "paired_proportion_difference_on_minus_off": effect,
            "cluster_bootstrap_ci95": list(ci),
        },
        "dimension_contingency": dimension_rows,
    }


def analyze_continuous(
    pairs: pd.DataFrame,
    representability: str,
    target: str,
    diff_column: str,
    rng: random.Random,
) -> dict[str, Any]:
    subset = pairs.loc[pairs["system_representability"] == representability].copy()
    if subset.empty:
        fail(f"{target} target is empty for {representability} systems")
    if subset[diff_column].isna().any():
        fail(f"{diff_column} is missing for {representability} systems")

    diffs = [float(value) for value in subset[diff_column].tolist()]
    clusters = cluster_values(subset, diff_column)
    wilcoxon_result = wilcoxon(diffs, alternative="two-sided", zero_method="wilcox")
    effect = median(diffs)
    ci = cluster_bootstrap_ci(clusters, median, rng, BOOTSTRAP_REPLICATES)
    cluster_p = cluster_permutation_p(clusters, median, rng, PERMUTATION_COUNT)
    result: dict[str, Any] = {
        "target": target,
        "system_representability": representability,
        "n_pairs": int(len(subset)),
        "n_systems": int(subset["system_id"].nunique()),
        "test_statistic": {"median_pair_difference": effect},
        "naive_wilcoxon": {
            "statistic": float(wilcoxon_result.statistic),
            "p": float(wilcoxon_result.pvalue),
        },
        "cluster_permutation_p": cluster_p,
        "effect_size": {
            "median_pair_difference": effect,
            "cluster_bootstrap_ci95": list(ci),
        },
    }
    if target == "log10_loss":
        result["effect_size"]["median_fold_change_on_over_off"] = 10.0**effect
        result["effect_size"]["fold_change_ci95"] = [10.0 ** ci[0], 10.0 ** ci[1]]
    return result


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def fmt(value: float) -> str:
    if value == 0:
        return "0"
    if abs(value) < 0.001 or abs(value) >= 10000:
        return f"{value:.6e}"
    return f"{value:.6g}"


def print_summary(output_path: Path, results: dict[str, Any]) -> None:
    counts = results["pair_counts"]
    print("Pretuning contrast analysis completed")
    print(
        "  Pairs: "
        f"total={counts['total']}, exact={counts['exact']}, surrogate={counts['surrogate']}"
    )
    print(f"  Output: {output_path}")
    for item in results["analyses"]:
        effect = item["effect_size"]
        naive_key = "naive_exact_mcnemar_p" if "naive_exact_mcnemar_p" in item else "naive_wilcoxon"
        naive_p = item[naive_key] if isinstance(item[naive_key], float) else item[naive_key]["p"]
        print(
            "  "
            f"{item['target']} ({item['system_representability']}): "
            f"n={item['n_pairs']}, effect={fmt(effect[next(iter(effect))])}, "
            f"naive_p={fmt(float(naive_p))}, cluster_p={fmt(float(item['cluster_permutation_p']))}"
        )


def main() -> int:
    args = parse_args()
    analysis_root = ANALYSIS_ROOT
    config_path = Path(args.config).resolve()

    try:
        config = load_config(config_path)
        experiment_id = config["experiment_id"]
        campaign_id = args.campaign or experiment_id
        if experiment_id != campaign_id:
            fail(
                f"config experiment_id {experiment_id!r} does not match "
                f"requested campaign {campaign_id!r}"
            )
        input_path = (
            Path(args.input).resolve()
            if args.input
            else resolve_path(config["run_registry_path"], analysis_root, config_path)
        )
        output_path = (
            Path(args.output).resolve()
            if args.output
            else (analysis_root / config["output_dir"] / "pretuning_contrast.json").resolve()
        )

        registry = validate_registry(load_run_registry(input_path), campaign_id)
        pairs = pair_registry(
            registry,
            args.expected_total_pairs,
            args.expected_exact_pairs,
            args.expected_surrogate_pairs,
        )
        pairs["r2_diff"] = pairs["r2_on"] - pairs["r2_off"]
        pairs["log10_loss_diff"] = pairs["loss_on"].map(math.log10) - pairs["loss_off"].map(math.log10)

        rng = random.Random(RANDOM_SEED)
        analyses = [
            analyze_exact_support(pairs, rng),
            analyze_continuous(pairs, "surrogate", "r2", "r2_diff", rng),
            analyze_continuous(pairs, "exact", "log10_loss", "log10_loss_diff", rng),
            analyze_continuous(pairs, "surrogate", "log10_loss", "log10_loss_diff", rng),
        ]

        results = {
            "experiment_id": experiment_id,
            "input_path": str(input_path),
            "randomization": {
                "seed": RANDOM_SEED,
                "permutation_count": PERMUTATION_COUNT,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "permutation_unit": "system_id",
                "bootstrap_unit": "system_id",
            },
            "loss_analysis_note": (
                "Loss is analyzed as log10(on) - log10(off), because raw loss spans many "
                "orders of magnitude; negative values favor pretuning."
            ),
            "pair_counts": {
                "total": int(len(pairs)),
                "exact": int((pairs["system_representability"] == "exact").sum()),
                "surrogate": int((pairs["system_representability"] == "surrogate").sum()),
            },
            "analyses": analyses,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(json_safe(results), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print_summary(output_path, results)
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
