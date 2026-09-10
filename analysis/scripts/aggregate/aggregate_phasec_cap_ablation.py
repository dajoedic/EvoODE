import argparse
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.campaign import campaign_data_dir, campaign_registry_path, require_single_campaign_id  # noqa: E402
from utils.io import load_run_registry  # noqa: E402
from utils.metrics import check_required_columns  # noqa: E402
from utils.paired_stats import (  # noqa: E402
    cluster_bootstrap_ci,
    cluster_permutation_p,
    cluster_values,
    coerce_bool,
    fail,
    pair_registry_by_conditions,
    percentile,
    share,
)


CAPPED_VARIANT = "evogrow_v2_2_stage_capped"
UNCAPPED_VARIANT = "evogrow_v2_2_stage_local"
SENTINEL_LOSS = 1e6

RANDOM_SEED = 20260910
PERMUTATION_COUNT = 100_000
BOOTSTRAP_REPLICATES = 10_000
QUANTILE_PROBABILITIES = [0.05, 0.10, 0.25, 0.75, 0.90, 0.95]

COST_THRESHOLD_GRID = [0.0, 0.10, 0.25, 0.50, 0.75]
LOSS_FOLD_THRESHOLD_GRID = [1.1, 2.0, 10.0, 100.0]
QUALITY_DELTA_THRESHOLD_GRID = [0.001, 0.01, 0.05, 0.10]
R2_THRESHOLD = 0.9

KEY_COLUMNS = ["system_id", "seed", "initial_condition_set"]
EXECUTED_LEVELS_COLUMN = "executed_levels"

REQUIRED_COLUMNS = [
    "experiment_id",
    "variant_slug",
    "system_id",
    "system_name",
    "system_dim",
    "system_representability",
    "system_expected_stage",
    "seed",
    "initial_condition_set",
    "loss",
    "r2",
    "exact_support_match_raw",
    "exact_support_match_pruned",
    "structural_f1",
    "term_precision",
    "term_recall",
    "coefficient_relative_error_mean",
    "total_parameter_fits",
    "total_parameter_fit_attempts",
    "total_loss_evals",
    "total_ode_solves",
    "final_stage",
    EXECUTED_LEVELS_COLUMN,
]

NUMERIC_COLUMNS = [
    "system_id",
    "system_dim",
    "system_expected_stage",
    "loss",
    "r2",
    "structural_f1",
    "term_precision",
    "term_recall",
    "coefficient_relative_error_mean",
    "total_parameter_fits",
    "total_parameter_fit_attempts",
    "total_loss_evals",
    "total_ode_solves",
    "final_stage",
    EXECUTED_LEVELS_COLUMN,
]

COST_COLUMNS = [
    "total_parameter_fits",
    "total_parameter_fit_attempts",
    "total_loss_evals",
    "total_ode_solves",
    "final_stage",
    EXECUTED_LEVELS_COLUMN,
]

QUALITY_COLUMNS = [
    "log10_loss",
    "r2",
    "exact_support_match_raw",
    "exact_support_match_pruned",
    "structural_f1",
    "term_precision",
    "term_recall",
    "coefficient_relative_error_mean",
]

OPTIONAL_GENERALIZATION_COLUMNS = [
    "generalization_r2",
    "generalization_loss",
    "generalization_mse",
    "test_r2",
    "test_loss",
    "test_mse",
]

ALLOWED_DIFFERENCE_COLUMNS = {
    "variant",
    "variant_slug",
    "condition",
    # Each arm has its own campaign manifest row; this is bookkeeping, not a condition.
    "campaign_manifest_index",
    "run_id",
    "status",
    "inferred_status",
    "success",
    "failure_reason",
    "started_at",
    "finished_at",
    "loss",
    "objective",
    "r2",
    "r2_by_dim",
    "exact_support_match",
    "exact_support_match_raw",
    "exact_support_match_pruned",
    "exact_support_match_definition",
    "support_terms",
    "pruned_support_terms",
    "model_terms",
    "coefficients",
    "coefficient_errors",
    "coefficient_relative_error_mean",
    "coefficient_relative_error_max",
    "structural_f1",
    "structural_f1_micro",
    "structural_f1_macro",
    "term_precision",
    "term_precision_micro",
    "term_precision_macro",
    "term_recall",
    "term_recall_micro",
    "term_recall_macro",
    "final_stage",
    "eq_final_stages",
    "stage_caps",
    # Capped and uncapped arms intentionally differ in whether the stage-cap policy is active.
    "stage_cap_policy_active",
    "stage_overshoot",
    "eq_overshoot",
    "wasted_levels",
    "partial",
    "metrics_available",
    "total_parameter_fits",
    "total_parameter_fit_attempts",
    "total_loss_evals",
    "total_invalid_evals",
    "total_ode_solves",
    "elapsed_s",
    "core_hours",
    "solver_retcodes",
    "optimizer_retcodes",
    "total_diverged_solves",
    "total_invalid_solves",
    "total_nonfinite_solves",
    "total_solver_unstable_solves",
    "total_step_limit_solves",
    "total_optimizer_limit_hits",
    "total_optimizer_budget_stop_fits",
    EXECUTED_LEVELS_COLUMN,
    *OPTIONAL_GENERALIZATION_COLUMNS,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate the paired Phase-C capped versus uncapped ablation."
    )
    parser.add_argument("--campaign", default="paper1_phaseC_v1")
    parser.add_argument("--input", help="Optional run_registry.csv override.")
    parser.add_argument("--output-dir", help="Optional output directory override.")
    parser.add_argument("--expected-total-pairs", type=int, required=True)
    parser.add_argument("--permutations", type=int, default=PERMUTATION_COUNT)
    parser.add_argument("--bootstrap-replicates", type=int, default=BOOTSTRAP_REPLICATES)
    return parser.parse_args()


def condition_from_variant(variant_slug: str) -> str:
    if variant_slug == CAPPED_VARIANT:
        return "capped"
    if variant_slug == UNCAPPED_VARIANT:
        return "uncapped"
    fail(
        "aggregate_phasec_cap_ablation.py only accepts the capped/uncapped "
        f"Phase-C cap-ablation arms; got variant_slug={variant_slug!r}"
    )
    raise AssertionError("unreachable")


def coerce_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    coerced = df.copy()
    for column in columns:
        coerced[column] = pd.to_numeric(coerced[column], errors="coerce")
    return coerced


def validate_registry(df: pd.DataFrame, campaign_id: str) -> pd.DataFrame:
    if EXECUTED_LEVELS_COLUMN not in df.columns:
        fail(
            "run_registry is missing required executed-level count column "
            f"{EXECUTED_LEVELS_COLUMN!r}; do not substitute n_levels, which is the configured budget"
        )
    check_required_columns(df, REQUIRED_COLUMNS)
    require_single_campaign_id(df, campaign_id, "run_registry")
    registry = coerce_numeric(df, NUMERIC_COLUMNS)
    registry["condition"] = registry["variant_slug"].astype(str).map(condition_from_variant)

    for column in NUMERIC_COLUMNS:
        if registry[column].isna().any():
            fail(f"{column} is missing or non-numeric in at least one row")
    if (registry["loss"] <= 0).any():
        fail("loss must be positive for log10 analysis")
    if (registry["loss"] == SENTINEL_LOSS).any():
        fail(f"sentinel loss {SENTINEL_LOSS:g} found in run_registry.csv")
    return registry


def build_pairs(registry: pd.DataFrame, expected_total_pairs: int) -> pd.DataFrame:
    pair_rows: list[dict[str, Any]] = []
    for _, capped, uncapped in pair_registry_by_conditions(
        registry,
        key_columns=KEY_COLUMNS,
        condition_column="condition",
        left_condition="capped",
        right_condition="uncapped",
        expected_total_pairs=expected_total_pairs,
        allowed_difference_columns=ALLOWED_DIFFERENCE_COLUMNS,
    ):
        row: dict[str, Any] = {
            "system_id": int(capped["system_id"]),
            "system_name": str(capped["system_name"]),
            "system_dim": int(capped["system_dim"]),
            "system_representability": str(capped["system_representability"]).strip(),
            "system_expected_stage": int(capped["system_expected_stage"]),
            "seed": str(capped["seed"]),
            "initial_condition_set": str(capped["initial_condition_set"]),
        }
        for column in COST_COLUMNS:
            capped_value = float(capped[column])
            uncapped_value = float(uncapped[column])
            row[f"{column}_capped"] = capped_value
            row[f"{column}_uncapped"] = uncapped_value
            row[f"{column}_saving_uncapped_minus_capped"] = uncapped_value - capped_value
            row[f"{column}_saving_fraction_of_uncapped"] = (
                (uncapped_value - capped_value) / uncapped_value
                if uncapped_value != 0.0
                else math.nan
            )
        for column in QUALITY_COLUMNS:
            if column == "log10_loss":
                capped_value = math.log10(float(capped["loss"]))
                uncapped_value = math.log10(float(uncapped["loss"]))
            elif column.startswith("exact_support_match"):
                capped_value = coerce_bool(capped[column])
                uncapped_value = coerce_bool(uncapped[column])
                if capped_value is None or uncapped_value is None:
                    fail(f"{column} is missing or non-binary in at least one pair")
            else:
                capped_value = float(capped[column])
                uncapped_value = float(uncapped[column])
            row[f"{column}_capped"] = capped_value
            row[f"{column}_uncapped"] = uncapped_value
            row[f"{column}_delta_capped_minus_uncapped"] = capped_value - uncapped_value
        for column in OPTIONAL_GENERALIZATION_COLUMNS:
            if column not in registry.columns:
                continue
            capped_value = pd.to_numeric(pd.Series([capped[column]]), errors="coerce").iloc[0]
            uncapped_value = pd.to_numeric(pd.Series([uncapped[column]]), errors="coerce").iloc[0]
            row[f"{column}_capped"] = capped_value
            row[f"{column}_uncapped"] = uncapped_value
            row[f"{column}_delta_capped_minus_uncapped"] = capped_value - uncapped_value
        pair_rows.append(row)
    return pd.DataFrame(pair_rows)


def quantile_rows(values: list[float]) -> list[dict[str, float]]:
    return [
        {"probability": probability, "value": percentile(values, probability)}
        for probability in QUANTILE_PROBABILITIES
    ]


def summarize_signed_delta(
    pairs: pd.DataFrame,
    column: str,
    thresholds: list[float],
    rng: random.Random,
    permutations: int,
    bootstrap_replicates: int,
) -> dict[str, Any]:
    if pairs[column].isna().any():
        fail(f"{column} contains missing values")
    values = [float(value) for value in pairs[column].tolist()]
    work = pairs[["system_id"]].copy()
    work["delta"] = values
    clusters = cluster_values(work, "delta")
    sign_work = pairs[["system_id"]].copy()
    sign_work["sign"] = [1.0 if value > 0 else -1.0 if value < 0 else 0.0 for value in values]
    sign_clusters = cluster_values(sign_work, "sign")

    threshold_rows = []
    for threshold in thresholds:
        above = (pairs[column] >= threshold).astype(float)
        below = (pairs[column] <= -threshold).astype(float)
        above_work = pairs[["system_id"]].copy()
        below_work = pairs[["system_id"]].copy()
        above_work["hit"] = above
        below_work["hit"] = below
        threshold_rows.append(
            {
                "threshold": threshold,
                "capped_higher_count": int(above.sum()),
                "capped_higher_share": float(above.mean()),
                "capped_higher_cluster_bootstrap_ci95": list(
                    cluster_bootstrap_ci(
                        cluster_values(above_work, "hit"),
                        share,
                        rng,
                        bootstrap_replicates,
                    )
                ),
                "uncapped_higher_count": int(below.sum()),
                "uncapped_higher_share": float(below.mean()),
                "uncapped_higher_cluster_bootstrap_ci95": list(
                    cluster_bootstrap_ci(
                        cluster_values(below_work, "hit"),
                        share,
                        rng,
                        bootstrap_replicates,
                    )
                ),
            }
        )

    return {
        "difference_column": column,
        "n_pairs": int(len(pairs)),
        "n_systems": int(pairs["system_id"].nunique()),
        "quantiles": quantile_rows(values),
        "sign_counts": {
            "capped_higher": int(sum(value > 0 for value in values)),
            "uncapped_higher": int(sum(value < 0 for value in values)),
            "exact_zero": int(sum(value == 0 for value in values)),
        },
        "cluster_bootstrap_quantile_ci95": {
            "q25": list(
                cluster_bootstrap_ci(clusters, lambda vals: percentile(vals, 0.25), rng, bootstrap_replicates)
            ),
            "q75": list(
                cluster_bootstrap_ci(clusters, lambda vals: percentile(vals, 0.75), rng, bootstrap_replicates)
            ),
        },
        "cluster_permutation_p": cluster_permutation_p(sign_clusters, sum, rng, permutations),
        "threshold_grid": threshold_rows,
    }


def summarize_cost_saving(
    pairs: pd.DataFrame,
    column: str,
    rng: random.Random,
    permutations: int,
    bootstrap_replicates: int,
) -> dict[str, Any]:
    saving_column = f"{column}_saving_uncapped_minus_capped"
    fraction_column = f"{column}_saving_fraction_of_uncapped"
    return {
        "counter": column,
        "saving_definition": "uncapped - capped; positive values favor the capped arm",
        "saving": summarize_signed_delta(
            pairs,
            saving_column,
            COST_THRESHOLD_GRID,
            rng,
            permutations,
            bootstrap_replicates,
        ),
        "saving_fraction_of_uncapped": summarize_signed_delta(
            pairs.dropna(subset=[fraction_column]).copy(),
            fraction_column,
            COST_THRESHOLD_GRID,
            rng,
            permutations,
            bootstrap_replicates,
        ),
    }


def summarize_loss_delta(
    pairs: pd.DataFrame,
    rng: random.Random,
    permutations: int,
    bootstrap_replicates: int,
) -> dict[str, Any]:
    column = "log10_loss_delta_capped_minus_uncapped"
    values = [float(value) for value in pairs[column].tolist()]
    threshold_rows = []
    for fold in LOSS_FOLD_THRESHOLD_GRID:
        log_threshold = math.log10(fold)
        capped_worse = (pairs[column] >= log_threshold).astype(float)
        capped_better = (pairs[column] <= -log_threshold).astype(float)
        worse_work = pairs[["system_id"]].copy()
        better_work = pairs[["system_id"]].copy()
        worse_work["hit"] = capped_worse
        better_work["hit"] = capped_better
        threshold_rows.append(
            {
                "fold_threshold": fold,
                "capped_worse_count": int(capped_worse.sum()),
                "capped_worse_share": float(capped_worse.mean()),
                "capped_worse_cluster_bootstrap_ci95": list(
                    cluster_bootstrap_ci(cluster_values(worse_work, "hit"), share, rng, bootstrap_replicates)
                ),
                "capped_better_count": int(capped_better.sum()),
                "capped_better_share": float(capped_better.mean()),
                "capped_better_cluster_bootstrap_ci95": list(
                    cluster_bootstrap_ci(cluster_values(better_work, "hit"), share, rng, bootstrap_replicates)
                ),
            }
        )
    sign_work = pairs[["system_id"]].copy()
    sign_work["sign"] = [-1.0 if value > 0 else 1.0 if value < 0 else 0.0 for value in values]
    return {
        "target": "log10_loss",
        "difference": "log10(loss_capped) - log10(loss_uncapped); negative values favor capped",
        "n_pairs": int(len(pairs)),
        "n_systems": int(pairs["system_id"].nunique()),
        "quantiles": quantile_rows(values),
        "sign_counts": {
            "capped_better": int(sum(value < 0 for value in values)),
            "uncapped_better": int(sum(value > 0 for value in values)),
            "exact_zero": int(sum(value == 0 for value in values)),
        },
        "cluster_permutation_p": cluster_permutation_p(
            cluster_values(sign_work, "sign"), sum, rng, permutations
        ),
        "threshold_grid": threshold_rows,
    }


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    input_path = (
        Path(args.input).resolve()
        if args.input
        else campaign_registry_path(REPO_ROOT, args.campaign).resolve()
    )
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else campaign_data_dir(ANALYSIS_ROOT, args.campaign).resolve()
    )
    return input_path, output_dir


def main() -> int:
    args = parse_args()
    try:
        input_path, output_dir = resolve_paths(args)
        registry = validate_registry(load_run_registry(input_path), args.campaign)
        pairs = build_pairs(registry, args.expected_total_pairs)

        rng = random.Random(RANDOM_SEED)
        cost_savings = [
            summarize_cost_saving(
                pairs,
                column,
                rng,
                args.permutations,
                args.bootstrap_replicates,
            )
            for column in COST_COLUMNS
        ]
        quality = [
            summarize_loss_delta(pairs, rng, args.permutations, args.bootstrap_replicates),
        ]
        for column in [
            "r2_delta_capped_minus_uncapped",
            "exact_support_match_raw_delta_capped_minus_uncapped",
            "exact_support_match_pruned_delta_capped_minus_uncapped",
            "structural_f1_delta_capped_minus_uncapped",
            "term_precision_delta_capped_minus_uncapped",
            "term_recall_delta_capped_minus_uncapped",
            "coefficient_relative_error_mean_delta_capped_minus_uncapped",
        ]:
            quality.append(
                summarize_signed_delta(
                    pairs,
                    column,
                    QUALITY_DELTA_THRESHOLD_GRID,
                    rng,
                    args.permutations,
                    args.bootstrap_replicates,
                )
            )
        for column in OPTIONAL_GENERALIZATION_COLUMNS:
            delta_column = f"{column}_delta_capped_minus_uncapped"
            if delta_column in pairs.columns and not pairs[delta_column].isna().all():
                quality.append(
                    summarize_signed_delta(
                        pairs.dropna(subset=[delta_column]).copy(),
                        delta_column,
                        QUALITY_DELTA_THRESHOLD_GRID,
                        rng,
                        args.permutations,
                        args.bootstrap_replicates,
                    )
                )

        r2_pass_capped = (pairs["r2_capped"] > R2_THRESHOLD).astype(float)
        r2_pass_uncapped = (pairs["r2_uncapped"] > R2_THRESHOLD).astype(float)
        r2_pass = pairs[["system_id"]].copy()
        r2_pass["diff"] = r2_pass_capped - r2_pass_uncapped

        summary = {
            "experiment_id": args.campaign,
            "input_path": str(input_path),
            "paired_csv": str(output_dir / "phasec_cap_ablation_paired.csv"),
            "randomization": {
                "seed": RANDOM_SEED,
                "permutation_count": args.permutations,
                "bootstrap_replicates": args.bootstrap_replicates,
                "permutation_unit": "system_id",
                "bootstrap_unit": "system_id",
            },
            "pair_counts": {
                "total": int(len(pairs)),
                "systems": int(pairs["system_id"].nunique()),
                "by_representability": {
                    str(key): int(value)
                    for key, value in pairs["system_representability"].value_counts().items()
                },
            },
            "condition_diff_allowlist": sorted(ALLOWED_DIFFERENCE_COLUMNS),
            "required_phasec_record_columns": REQUIRED_COLUMNS,
            "executed_levels_column": EXECUTED_LEVELS_COLUMN,
            "cost_savings": cost_savings,
            "quality": quality,
            "r2_gt_0_9": {
                "threshold": R2_THRESHOLD,
                "capped_count": int(r2_pass_capped.sum()),
                "uncapped_count": int(r2_pass_uncapped.sum()),
                "paired_delta_capped_minus_uncapped": int(r2_pass["diff"].sum()),
                "cluster_permutation_p": cluster_permutation_p(
                    cluster_values(r2_pass, "diff"), sum, rng, args.permutations
                ),
            },
            "core_hours_note": (
                "Core hours, if present, are capacity context only; evidence for saving "
                "is reported from counters and executed levels."
            ),
        }

        output_dir.mkdir(parents=True, exist_ok=True)
        pairs.to_csv(output_dir / "phasec_cap_ablation_paired.csv", index=False)
        (output_dir / "phasec_cap_ablation_summary.json").write_text(
            json.dumps(json_safe(summary), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print("Phase-C cap ablation aggregation completed")
        print(f"  Pairs: {len(pairs)}")
        print(f"  Output: {output_dir / 'phasec_cap_ablation_paired.csv'}")
        print(f"  Summary: {output_dir / 'phasec_cap_ablation_summary.json'}")
        return 0
    except (FileNotFoundError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
