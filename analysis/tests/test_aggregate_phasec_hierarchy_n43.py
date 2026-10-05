import math
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate import aggregate_phasec_hierarchy_n43 as n43  # noqa: E402


def fixture_per_run() -> pd.DataFrame:
    rows = []
    for system_id, direction, values in [
        (1, "IC1_to_IC2", [1, 1, 1]),
        (1, "IC2_to_IC1", [0, 0, 0]),
        (2, "IC1_to_IC2", [1, 0, 0]),
        (2, "IC2_to_IC1", [1, 0, 0]),
    ]:
        for seed, passed in enumerate(values, start=1):
            rows.append(
                {
                    "method": "Fixture",
                    "method_family": "Fixture",
                    "configuration": "cfg",
                    "arm": "canonical",
                    "system_id": system_id,
                    "system_name": f"system {system_id}",
                    "dimension": 1,
                    "direction": direction,
                    "source_initial_condition_set": 1 if direction == "IC1_to_IC2" else 2,
                    "target_initial_condition_set": 2 if direction == "IC1_to_IC2" else 1,
                    "run_id": seed,
                    "seed": seed,
                    "repetition": 0,
                    "noise_level": 0.0,
                    "subsampling_ratio": 1.0,
                    "realization": 0,
                    "initial_condition_set": 1,
                    "threeway_class": "fully_representable",
                    "is_exact_system": True,
                    "feasible_bound_10": True,
                    "reconstruction_r2_arithmetic": 1.0 if passed else 0.0,
                    "reconstruction_r2_arithmetic_available": True,
                    "reconstruction_r2_variance_weighted": 1.0 if passed else 0.0,
                    "reconstruction_r2_variance_weighted_available": True,
                    "generalization_r2_arithmetic": 1.0 if passed else 0.0,
                    "generalization_r2_arithmetic_available": True,
                    "generalization_r2_variance_weighted": 1.0 if passed else 0.0,
                    "generalization_r2_variance_weighted_available": True,
                    "reconstruction_diverged_or_nonfinite": False,
                    "generalization_diverged_or_nonfinite": False,
                    "divergence_flag": False,
                    "raw_exact_support_match": bool(passed),
                    "pruned_exact_support_match": bool(passed),
                    "structural_f1_pruned": float(passed),
                    "structural_precision_pruned": float(passed),
                    "structural_recall_pruned": float(passed),
                }
            )
    frame = pd.DataFrame(rows)
    return n43.add_pass_columns(frame)


def test_hierarchy_order_differs_from_naive_pooled_rate() -> None:
    per_run = fixture_per_run()
    extra = per_run[(per_run["system_id"] == 1) & (per_run["direction"] == "IC1_to_IC2")].copy()
    extra["run_id"] = extra["run_id"] + 100
    per_run = pd.concat([per_run, extra], ignore_index=True)

    naive = float(per_run["reconstruction_r2_arithmetic_gt_0_9"].mean())
    per_system = n43.system_level(per_run)
    hierarchical = float(
        per_system[
            (per_system["method"] == "Fixture")
            & (per_system["configuration"] == "cfg")
            & (per_system["arm"] == "canonical")
        ]["reconstruction_r2_arithmetic_gt_0_9"].mean()
    )

    assert naive == 8 / 15
    assert abs(hierarchical - (5 / 12)) < 1e-15
    system_1 = per_system[per_system["system_id"] == 1].iloc[0]
    system_2 = per_system[per_system["system_id"] == 2].iloc[0]
    assert system_1["reconstruction_r2_arithmetic_gt_0_9"] == 0.5
    assert system_2["reconstruction_r2_arithmetic_gt_0_9"] == 1 / 3


def test_equal_system_weight_not_run_weight() -> None:
    per_run = fixture_per_run()
    extra = per_run[(per_run["system_id"] == 1) & (per_run["direction"] == "IC1_to_IC2")].copy()
    extra["run_id"] = extra["run_id"] + 100
    per_run = pd.concat([per_run, extra], ignore_index=True)

    naive = float(per_run["reconstruction_r2_arithmetic_gt_0_9"].mean())
    per_system = n43.system_level(per_run)
    benchmark = n43.benchmark_rows(per_system)
    overall = benchmark[
        (benchmark["method"] == "Fixture")
        & (benchmark["configuration"] == "cfg")
        & (benchmark["arm"] == "canonical")
        & (benchmark["stratum"] == "overall")
    ].iloc[0]

    assert naive != overall["reconstruction_r2_arithmetic_gt_0_9"]
    assert overall["reconstruction_r2_arithmetic_gt_0_9"] == per_system["reconstruction_r2_arithmetic_gt_0_9"].mean()


def test_divergent_run_counts_as_failed_threshold() -> None:
    per_run = fixture_per_run()
    per_run.loc[0, "reconstruction_diverged_or_nonfinite"] = True
    per_run.loc[0, "divergence_flag"] = True
    per_run = n43.add_pass_columns(per_run)

    assert not bool(per_run.loc[0, "reconstruction_r2_arithmetic_gt_0_9"])
    per_system = n43.system_level(per_run)
    assert int(per_system["divergent_run_count"].sum()) == 1


def test_missing_variance_weighted_metric_sets_nan_and_available_false() -> None:
    per_run = fixture_per_run()
    per_run.loc[:, "generalization_r2_variance_weighted"] = math.nan
    per_run.loc[:, "generalization_r2_variance_weighted_available"] = False
    per_run = n43.add_pass_columns(per_run)

    assert per_run["generalization_r2_variance_weighted"].isna().all()
    assert not per_run["generalization_r2_variance_weighted_available"].any()
    assert per_run["generalization_r2_variance_weighted_gt_0_9"].isna().all()
