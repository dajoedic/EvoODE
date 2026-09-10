import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Callable

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.io import load_run_registry  # noqa: E402
from utils.campaign import require_single_campaign_id  # noqa: E402
from utils.metrics import check_required_columns  # noqa: E402


PRETUNE_ON = "evogrow_v2_2_stage_capped_pretune_on"
PRETUNE_OFF = "evogrow_v2_2_stage_capped_pretune_off"
SENTINEL_LOSS = 1e6

RANDOM_SEED = 20260907
PERMUTATION_COUNT = 100_000
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_ALPHA = 0.05

QUANTILE_PROBABILITIES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]
R2_THRESHOLDS = [1e-4, 1e-3, 1e-2, 1e-1]
LOSS_FOLD_THRESHOLDS = [1.1, 2.0, 10.0, 100.0]

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
    "r2",
    "support_terms",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze Phase-B pretuning distributions and seed collapse."
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
    parser.add_argument("--expected-collapse-groups-per-condition", type=int, default=126)
    parser.add_argument("--collapse-rtol", type=float, default=1e-12)
    parser.add_argument("--collapse-atol", type=float, default=0.0)
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


def percentile(values: list[float], probability: float) -> float:
    if not values:
        fail("cannot compute percentile of an empty value set")
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = probability * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return float(ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction)


def exact_binomial_two_sided(discordant: int, off_only: int) -> float:
    if discordant == 0:
        return 1.0
    tail = min(off_only, discordant - off_only)
    probability = sum(math.comb(discordant, k) for k in range(tail + 1)) / (2**discordant)
    return min(1.0, 2.0 * probability)


def cluster_bootstrap_ci(
    clusters: dict[int, list[float]],
    statistic: Callable[[list[float]], float],
    rng: random.Random,
) -> tuple[float, float]:
    system_ids = list(clusters)
    if not system_ids:
        fail("no clusters available for bootstrap")
    estimates = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled_values: list[float] = []
        for _ in system_ids:
            sampled_values.extend(clusters[rng.choice(system_ids)])
        estimates.append(statistic(sampled_values))
    return (
        percentile(estimates, BOOTSTRAP_ALPHA / 2.0),
        percentile(estimates, 1.0 - BOOTSTRAP_ALPHA / 2.0),
    )


def cluster_permutation_p(
    clusters: dict[int, list[float]],
    statistic: Callable[[list[float]], float],
    rng: random.Random,
) -> float:
    observed_values = [value for values in clusters.values() for value in values]
    observed = statistic(observed_values)
    threshold = abs(observed)
    extreme = 0
    system_items = list(clusters.items())
    for _ in range(PERMUTATION_COUNT):
        permuted_values: list[float] = []
        for _, values in system_items:
            sign = -1.0 if rng.random() < 0.5 else 1.0
            permuted_values.extend(sign * value for value in values)
        if abs(statistic(permuted_values)) >= threshold - 1e-15:
            extreme += 1
    return (extreme + 1.0) / (PERMUTATION_COUNT + 1.0)


def condition_from_variant(variant_slug: str) -> str:
    if variant_slug == PRETUNE_ON:
        return "pretune_on"
    if variant_slug == PRETUNE_OFF:
        return "pretune_off"
    fail(f"Unexpected variant_slug for pretuning contrast: {variant_slug}")
    raise AssertionError("unreachable")


def canonical_support(value: Any) -> str:
    if pd.isna(value):
        fail("support_terms is missing")
    try:
        parsed = json.loads(str(value))
    except json.JSONDecodeError as exc:
        raise ValueError(f"support_terms is not valid JSON: {value}") from exc
    if not isinstance(parsed, list):
        fail("support_terms JSON must be a list")
    normalized: list[list[str]] = []
    for eq_index, equation_terms in enumerate(parsed):
        if not isinstance(equation_terms, list):
            fail(f"support_terms equation {eq_index} is not a list")
        normalized.append(sorted(str(term) for term in equation_terms))
    return json.dumps(normalized, ensure_ascii=True, separators=(",", ":"))


def validate_registry(df: pd.DataFrame, campaign_id: str) -> pd.DataFrame:
    check_required_columns(df, REQUIRED_COLUMNS)
    require_single_campaign_id(df, campaign_id, "run_registry")
    registry = df.copy()
    for column in ["system_id", "system_dim", "loss", "r2"]:
        registry[column] = pd.to_numeric(registry[column], errors="coerce")
    registry["condition"] = registry["variant_slug"].astype(str).map(condition_from_variant)
    registry["support_key"] = registry["support_terms"].map(canonical_support)

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
    pair_rows: list[dict[str, Any]] = []
    key_columns = ["system_id", "seed", "initial_condition_set"]
    for key, group in registry.groupby(key_columns, sort=True, dropna=False):
        by_condition = {row["condition"]: row for _, row in group.iterrows()}
        if set(by_condition) != {"pretune_on", "pretune_off"} or len(group) != 2:
            fail(
                "incomplete or duplicate pair for "
                f"system_id={key[0]}, seed={key[1]}, initial_condition_set={key[2]}"
            )
        on = by_condition["pretune_on"]
        off = by_condition["pretune_off"]
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
                "r2_on": float(on["r2"]),
                "r2_off": float(off["r2"]),
                "loss_on": float(on["loss"]),
                "loss_off": float(off["loss"]),
                "support_on": str(on["support_key"]),
                "support_off": str(off["support_key"]),
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


def clusters_from(df: pd.DataFrame, value_column: str) -> dict[int, list[float]]:
    return {
        int(system_id): [float(value) for value in group[value_column].tolist()]
        for system_id, group in df.groupby("system_id", sort=True)
    }


def share(values: list[float]) -> float:
    if not values:
        fail("cannot compute share of an empty value set")
    return float(sum(values) / len(values))


def sign_statistic(values: list[float]) -> float:
    return float(sum(1 if value > 0 else -1 if value < 0 else 0 for value in values))


def analyze_distribution(
    pairs: pd.DataFrame,
    representability: str,
    target: str,
    diff_column: str,
    thresholds: list[float],
    rng: random.Random,
) -> dict[str, Any]:
    subset = pairs.loc[pairs["system_representability"] == representability].copy()
    if subset.empty:
        fail(f"{target} target is empty for {representability} systems")
    diffs = [float(value) for value in subset[diff_column].tolist()]
    quantiles = [
        {"probability": probability, "value": percentile(diffs, probability)}
        for probability in QUANTILE_PROBABILITIES
    ]

    threshold_rows = []
    for threshold in thresholds:
        if target == "r2":
            favor_on = (subset[diff_column] >= threshold).astype(float)
            favor_off = (subset[diff_column] <= -threshold).astype(float)
            threshold_label = threshold
        else:
            log_threshold = math.log10(threshold)
            favor_on = (subset[diff_column] <= -log_threshold).astype(float)
            favor_off = (subset[diff_column] >= log_threshold).astype(float)
            threshold_label = threshold

        work = subset[["system_id"]].copy()
        work["favor_on"] = favor_on
        work["favor_off"] = favor_off
        on_clusters = clusters_from(work, "favor_on")
        off_clusters = clusters_from(work, "favor_off")
        on_ci = cluster_bootstrap_ci(on_clusters, share, rng)
        off_ci = cluster_bootstrap_ci(off_clusters, share, rng)
        threshold_rows.append(
            {
                "threshold": threshold_label,
                "favor_pretune_on_count": int(favor_on.sum()),
                "favor_pretune_on_share": float(favor_on.mean()),
                "favor_pretune_on_cluster_bootstrap_ci95": list(on_ci),
                "favor_pretune_off_count": int(favor_off.sum()),
                "favor_pretune_off_share": float(favor_off.mean()),
                "favor_pretune_off_cluster_bootstrap_ci95": list(off_ci),
            }
        )

    signs = [1 if value > 0 else -1 if value < 0 else 0 for value in diffs]
    if target == "log10_loss":
        favor_on_count = signs.count(-1)
        favor_off_count = signs.count(1)
        sign_values = [-float(sign) for sign in signs]
    else:
        favor_on_count = signs.count(1)
        favor_off_count = signs.count(-1)
        sign_values = [float(sign) for sign in signs]
    sign_work = subset[["system_id"]].copy()
    sign_work["sign_value"] = sign_values
    sign_clusters = clusters_from(sign_work, "sign_value")

    return {
        "target": target,
        "system_representability": representability,
        "difference": (
            "pretune_on - pretune_off"
            if target == "r2"
            else "log10(loss_on) - log10(loss_off)"
        ),
        "n_pairs": int(len(subset)),
        "n_systems": int(subset["system_id"].nunique()),
        "quantiles": quantiles,
        "threshold_grid": threshold_rows,
        "sign_asymmetry": {
            "favor_pretune_on": int(favor_on_count),
            "favor_pretune_off": int(favor_off_count),
            "exact_zero": int(signs.count(0)),
            "cluster_permutation_p": cluster_permutation_p(
                sign_clusters, sign_statistic, rng
            ),
        },
    }


def all_close_to_first(values: list[float], rtol: float, atol: float) -> bool:
    first = values[0]
    return all(abs(value - first) <= (atol + rtol * abs(first)) for value in values[1:])


def collapse_groups(
    registry: pd.DataFrame,
    expected_groups_per_condition: int,
    rtol: float,
    atol: float,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    key_columns = ["system_id", "initial_condition_set", "condition"]
    for key, group in registry.groupby(key_columns, sort=True, dropna=False):
        if len(group) != 3:
            fail(
                "seed-collapse group expected exactly 3 rows for "
                f"system_id={key[0]}, initial_condition_set={key[1]}, condition={key[2]}; "
                f"got {len(group)}"
            )
        seeds = {str(seed) for seed in group["seed"].tolist()}
        if len(seeds) != 3:
            fail(
                "seed-collapse group expected exactly 3 distinct seeds for "
                f"system_id={key[0]}, initial_condition_set={key[1]}, condition={key[2]}"
            )
        r2_values = [float(value) for value in group["r2"].tolist()]
        loss_values = [float(value) for value in group["loss"].tolist()]
        log_losses = [math.log10(value) for value in loss_values]
        support_values = [str(value) for value in group["support_key"].tolist()]
        representabilities = set(str(value).strip() for value in group["system_representability"])
        if len(representabilities) != 1:
            fail(f"representability mismatch within seed-collapse group {key}")
        rows.append(
            {
                "system_id": int(key[0]),
                "initial_condition_set": str(key[1]),
                "condition": str(key[2]),
                "system_representability": next(iter(representabilities)),
                "r2_collapsed": all_close_to_first(r2_values, rtol, atol),
                "loss_collapsed": all_close_to_first(loss_values, rtol, atol),
                "support_terms_collapsed": len(set(support_values)) == 1,
                "r2_range": max(r2_values) - min(r2_values),
                "log10_loss_range": max(log_losses) - min(log_losses),
            }
        )
    collapsed = pd.DataFrame(rows)
    counts = collapsed["condition"].value_counts().to_dict()
    for condition in ["pretune_on", "pretune_off"]:
        if int(counts.get(condition, 0)) != expected_groups_per_condition:
            fail(
                f"seed-collapse groups for {condition} expected "
                f"{expected_groups_per_condition}, got {int(counts.get(condition, 0))}"
            )
    return collapsed


def collapse_pair_table(groups: pd.DataFrame, target_column: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    key_columns = ["system_id", "initial_condition_set"]
    for key, group in groups.groupby(key_columns, sort=True, dropna=False):
        by_condition = {row["condition"]: row for _, row in group.iterrows()}
        if set(by_condition) != {"pretune_on", "pretune_off"} or len(group) != 2:
            fail(
                "incomplete or duplicate seed-collapse condition pair for "
                f"system_id={key[0]}, initial_condition_set={key[1]}"
            )
        on = by_condition["pretune_on"]
        off = by_condition["pretune_off"]
        if on["system_representability"] != off["system_representability"]:
            fail(f"representability mismatch within collapse condition pair {key}")
        rows.append(
            {
                "system_id": int(key[0]),
                "initial_condition_set": str(key[1]),
                "system_representability": str(on["system_representability"]),
                "on": bool(on[target_column]),
                "off": bool(off[target_column]),
            }
        )
    return pd.DataFrame(rows)


def analyze_collapse_target(
    groups: pd.DataFrame,
    target_name: str,
    target_column: str,
    rng: random.Random,
) -> list[dict[str, Any]]:
    paired = collapse_pair_table(groups, target_column)
    results = []
    for representability in ["exact", "surrogate", "all"]:
        subset = (
            paired
            if representability == "all"
            else paired.loc[paired["system_representability"] == representability].copy()
        )
        if subset.empty:
            fail(f"collapse target {target_name} is empty for {representability}")
        off_only = int((subset["off"] & ~subset["on"]).sum())
        on_only = int((~subset["off"] & subset["on"]).sum())
        both_no = int((~subset["off"] & ~subset["on"]).sum())
        both_yes = int((subset["off"] & subset["on"]).sum())
        discordant = off_only + on_only
        diff_work = subset[["system_id"]].copy()
        diff_work["diff"] = subset["on"].astype(float) - subset["off"].astype(float)
        clusters = clusters_from(diff_work, "diff")
        condition_counts = {}
        for condition in ["pretune_off", "pretune_on"]:
            condition_subset = groups.loc[
                (groups["condition"] == condition)
                & (
                    (groups["system_representability"] == representability)
                    if representability != "all"
                    else True
                )
            ]
            collapsed_count = int(condition_subset[target_column].sum())
            total = int(len(condition_subset))
            range_summary: dict[str, Any] = {}
            if target_name == "r2":
                spread_values = [float(value) for value in condition_subset["r2_range"].tolist()]
                range_summary = {
                    "range_quantiles": [
                        {"probability": probability, "value": percentile(spread_values, probability)}
                        for probability in QUANTILE_PROBABILITIES
                    ],
                    "max_range": max(spread_values),
                }
            elif target_name == "loss":
                spread_values = [
                    float(value) for value in condition_subset["log10_loss_range"].tolist()
                ]
                range_summary = {
                    "log10_range_quantiles": [
                        {"probability": probability, "value": percentile(spread_values, probability)}
                        for probability in QUANTILE_PROBABILITIES
                    ],
                    "max_log10_range": max(spread_values),
                }
            condition_counts[condition] = {
                "collapsed_groups": collapsed_count,
                "groups": total,
                "share": collapsed_count / total,
                **range_summary,
            }
        results.append(
            {
                "target": target_name,
                "system_representability": representability,
                "n_condition_pairs": int(len(subset)),
                "n_systems": int(subset["system_id"].nunique()),
                "by_condition": condition_counts,
                "paired_contingency": {
                    "off_no_on_no": both_no,
                    "off_no_on_yes": on_only,
                    "off_yes_on_no": off_only,
                    "off_yes_on_yes": both_yes,
                },
                "naive_exact_mcnemar_p": exact_binomial_two_sided(discordant, off_only),
                "cluster_permutation_p": cluster_permutation_p(clusters, sum, rng),
            }
        )
    return results


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


def print_summary(output_path: Path, results: dict[str, Any]) -> None:
    counts = results["pair_counts"]
    print("Pretuning distribution and seed-collapse analysis completed")
    print(
        "  Pairs: "
        f"total={counts['total']}, exact={counts['exact']}, surrogate={counts['surrogate']}"
    )
    print(
        "  Seed-collapse groups: "
        f"pretune_off={results['collapse_group_counts']['pretune_off']}, "
        f"pretune_on={results['collapse_group_counts']['pretune_on']}"
    )
    print(f"  Output: {output_path}")


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    try:
        config = load_config(config_path)
        campaign_id = args.campaign or config["experiment_id"]
        if config["experiment_id"] != campaign_id:
            fail(
                f"config experiment_id {config['experiment_id']!r} does not match "
                f"requested campaign {campaign_id!r}"
            )
        input_path = (
            Path(args.input).resolve()
            if args.input
            else resolve_path(config["run_registry_path"], ANALYSIS_ROOT, config_path)
        )
        output_path = (
            Path(args.output).resolve()
            if args.output
            else (
                ANALYSIS_ROOT
                / config["output_dir"]
                / "pretuning_distribution_collapse.json"
            ).resolve()
        )
        registry = validate_registry(load_run_registry(input_path), campaign_id)
        pairs = pair_registry(
            registry,
            args.expected_total_pairs,
            args.expected_exact_pairs,
            args.expected_surrogate_pairs,
        )
        pairs["r2_diff"] = pairs["r2_on"] - pairs["r2_off"]
        pairs["log10_loss_diff"] = pairs["loss_on"].map(math.log10) - pairs["loss_off"].map(
            math.log10
        )

        groups = collapse_groups(
            registry,
            args.expected_collapse_groups_per_condition,
            args.collapse_rtol,
            args.collapse_atol,
        )
        rng = random.Random(RANDOM_SEED)
        distributions = [
            analyze_distribution(
                pairs, "surrogate", "r2", "r2_diff", R2_THRESHOLDS, rng
            ),
            analyze_distribution(
                pairs, "exact", "log10_loss", "log10_loss_diff", LOSS_FOLD_THRESHOLDS, rng
            ),
            analyze_distribution(
                pairs,
                "surrogate",
                "log10_loss",
                "log10_loss_diff",
                LOSS_FOLD_THRESHOLDS,
                rng,
            ),
        ]
        collapse_results: list[dict[str, Any]] = []
        for target_name, target_column in [
            ("r2", "r2_collapsed"),
            ("loss", "loss_collapsed"),
            ("support_terms", "support_terms_collapsed"),
        ]:
            collapse_results.extend(
                analyze_collapse_target(groups, target_name, target_column, rng)
            )

        results = {
            "experiment_id": config["experiment_id"],
            "input_path": str(input_path),
            "randomization": {
                "seed": RANDOM_SEED,
                "permutation_count": PERMUTATION_COUNT,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "permutation_unit": "system_id",
                "bootstrap_unit": "system_id",
            },
            "collapse_tolerance": {
                "relative": args.collapse_rtol,
                "absolute": args.collapse_atol,
                "numeric_rule": "abs(value - first) <= absolute + relative * abs(first)",
                "support_rule": (
                    "JSON is parsed, equation order is preserved, and terms within each "
                    "equation are sorted before exact comparison."
                ),
            },
            "pair_counts": {
                "total": int(len(pairs)),
                "exact": int((pairs["system_representability"] == "exact").sum()),
                "surrogate": int((pairs["system_representability"] == "surrogate").sum()),
            },
            "collapse_group_counts": {
                key: int(value) for key, value in groups["condition"].value_counts().items()
            },
            "distributions": distributions,
            "seed_collapse": collapse_results,
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
