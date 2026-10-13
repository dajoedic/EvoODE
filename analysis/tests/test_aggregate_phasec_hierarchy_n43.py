import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


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


def test_c6_sindy_loader_asserts_clean_realization_identity() -> None:
    rows = []
    for realization, gen_r2 in [(1, 0.95), (2, 0.95), (3, 0.80)]:
        rows.append(
            {
                "method": "sindy",
                "library_id": "poly",
                "system_id": 1,
                "system_name": "system 1",
                "dimension": 1,
                "source_initial_condition_set": 1,
                "target_initial_condition_set": 2,
                "noise_sigma": 0.0,
                "subsample_rho": 0.0,
                "noise_realization": realization,
                "fit_status": "success",
                "reconstruction_integration_status": "success",
                "generalization_integration_status": "success",
                "reconstruction_diverged_or_nonfinite": False,
                "generalization_diverged_or_nonfinite": False,
                "reconstruction_r2_arithmetic_mean": 0.99,
                "reconstruction_r2_variance_weighted": 0.99,
                "generalization_r2_arithmetic_mean": gen_r2,
                "generalization_r2_variance_weighted": gen_r2,
                "reconstruction_r2_arithmetic_mean_gt_0_9": True,
                "reconstruction_r2_variance_weighted_gt_0_9": True,
                "generalization_r2_arithmetic_mean_gt_0_9": gen_r2 > 0.9,
                "generalization_r2_variance_weighted_gt_0_9": gen_r2 > 0.9,
                "sindy_structure_hit_raw": True,
                "sindy_structure_hit_pruned": True,
                "active_terms_raw": '[["x0"]]',
                "active_terms_pruned": '[["x0"]]',
                "sindy_structure_precision_pruned": 1.0,
                "sindy_structure_recall_pruned": 1.0,
                "sindy_structure_f1_pruned": 1.0,
            }
        )

    with pytest.raises(ValueError, match="realizations differ"):
        n43.assert_clean_realization_identity(pd.DataFrame(rows))


def test_c6_loader_keeps_sindy_family_methods_separate() -> None:
    rows = []
    for method in ["sindy", "weak_sindy", "e_sindy"]:
        for realization in [1, 2, 3]:
            rows.append(
                {
                    "method": method,
                    "library_id": "poly",
                    "system_id": 1,
                    "system_name": "system 1",
                    "dimension": 1,
                    "source_initial_condition_set": 1,
                    "target_initial_condition_set": 2,
                    "noise_sigma": 0.0,
                    "subsample_rho": 0.0,
                    "noise_realization": realization,
                    "fit_status": "success",
                    "reconstruction_integration_status": "success",
                    "generalization_integration_status": "success",
                    "reconstruction_diverged_or_nonfinite": False,
                    "generalization_diverged_or_nonfinite": False,
                    "reconstruction_r2_arithmetic_mean": 0.99,
                    "reconstruction_r2_variance_weighted": 0.99,
                    "generalization_r2_arithmetic_mean": 0.95,
                    "generalization_r2_variance_weighted": 0.95,
                    "reconstruction_r2_arithmetic_mean_gt_0_9": True,
                    "reconstruction_r2_variance_weighted_gt_0_9": True,
                    "generalization_r2_arithmetic_mean_gt_0_9": True,
                    "generalization_r2_variance_weighted_gt_0_9": True,
                    "sindy_structure_hit_raw": True,
                    "sindy_structure_hit_pruned": True,
                    "active_terms_raw": '[["x0"]]',
                    "active_terms_pruned": '[["x0"]]',
                    "sindy_structure_precision_pruned": 1.0,
                    "sindy_structure_recall_pruned": 1.0,
                    "sindy_structure_f1_pruned": 1.0,
                }
            )
    classes = pd.DataFrame(
        [
            {
                "system_id": 1,
                "threeway_class": "fully_representable",
                "phasec_true_threeway_basis_name": n43.TRUE_BASIS,
            }
        ]
    )

    loaded = n43.load_sindy_wide(pd.DataFrame(rows), classes)

    assert set(loaded["method"]) == {"SINDy", "Weak-SINDy", "E-SINDy"}
    assert len(loaded[loaded["method"].eq("SINDy")]) == 1
    assert len(loaded[loaded["method"].eq("Weak-SINDy")]) == 3
    assert len(loaded[loaded["method"].eq("E-SINDy")]) == 3


def write_clean_shard_tree(tmp_path: Path, *, drop_last_cell: bool = False, noisy_row: bool = False) -> Path:
    rows = []
    cells = [
        (system_id, source_ic, realization)
        for system_id in range(1, 64)
        for source_ic in [1, 2]
        for realization in [1, 2, 3]
    ]
    if drop_last_cell:
        cells = cells[:-1]
    for system_id, source_ic, realization in cells:
        for method in ["sindy", "weak_sindy", "e_sindy"]:
            for library_id in [f"lib_{index}" for index in range(10)]:
                rows.append(
                    {
                        "system_id": system_id,
                        "source_initial_condition_set": source_ic,
                        "noise_sigma": 0.0,
                        "subsample_rho": 0.0,
                        "noise_realization": realization,
                        "method": method,
                        "library_id": library_id,
                    }
                )
    if noisy_row:
        row = rows[0].copy()
        row["noise_sigma"] = 0.01
        rows.append(row)
    shard = tmp_path / "shard_0"
    shard.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(shard / "details.csv", index=False)
    pd.DataFrame([{"hash_verified": True}]).to_csv(shard / "export_checks.csv", index=False)
    return tmp_path


def test_clean_only_merge_accepts_378_clean_cells(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(n43, "build_summary", lambda details: pd.DataFrame([{"n_rows": len(details)}]))
    shards = write_clean_shard_tree(tmp_path / "shards")

    outputs = n43.merge_sindy_shards(
        shards,
        tmp_path / "merged",
        expected_methods={"sindy", "weak_sindy", "e_sindy"},
        expected_cell_count=378,
        clean_only=True,
    )

    checks = pd.read_csv(outputs["merge_checks"])
    assert int(checks.loc[0, "n_distinct_cells"]) == 378
    assert bool(checks.loc[0, "clean_only"])


def test_clean_only_merge_rejects_noisy_row(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(n43, "build_summary", lambda details: pd.DataFrame([{"n_rows": len(details)}]))
    shards = write_clean_shard_tree(tmp_path / "shards", noisy_row=True)

    with pytest.raises(ValueError, match="clean-only merge found 1 non-clean rows"):
        n43.merge_sindy_shards(
            shards,
            tmp_path / "merged",
            expected_methods={"sindy", "weak_sindy", "e_sindy"},
            expected_cell_count=378,
            clean_only=True,
        )


def test_clean_only_merge_rejects_missing_cell(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(n43, "build_summary", lambda details: pd.DataFrame([{"n_rows": len(details)}]))
    shards = write_clean_shard_tree(tmp_path / "shards", drop_last_cell=True)

    with pytest.raises(ValueError, match="expected 378 distinct cells, found 377"):
        n43.merge_sindy_shards(
            shards,
            tmp_path / "merged",
            expected_methods={"sindy", "weak_sindy", "e_sindy"},
            expected_cell_count=378,
            clean_only=True,
        )


def test_evogrow_generalization_variance_weighted_control(tmp_path: Path) -> None:
    registry = pd.DataFrame(
        [
            {
                "system_id": 1,
                "system_name": "system 1",
                "system_dim": 2,
                "dimension": 2,
                "variant_slug": n43.C1_VARIANT,
                "condition": "capped",
                "use_pretuning": False,
                "seed": 123,
                "initial_condition_set": 1,
                "r2": 0.8,
                "r2_by_dim": "[0.6,1.0]",
                "exact_support_match_raw": True,
                "exact_support_match_pruned": True,
                "structural_f1_micro": 1.0,
                "term_precision_micro": 1.0,
                "term_recall_micro": 1.0,
                "total_diverged_solves": 0,
            }
        ]
    )
    cells = pd.DataFrame(
        [
            {
                "system_id": 1,
                "source_initial_condition_set": 1,
                "target_initial_condition_set": 2,
                "direction": "IC1_to_IC2",
                "seed": 123,
                "variant": n43.C1_VARIANT,
                "condition": "capped",
                "reconstruction_r2": 0.8,
                "reconstruction_diverged_or_nonfinite": False,
                "generalization_r2": 0.7,
                "generalization_r2_by_dim": "[0.5,0.9]",
                "generalization_diverged_or_nonfinite": False,
            }
        ]
    )
    classes = pd.DataFrame(
        [
            {
                "system_id": 1,
                "threeway_class": "fully_representable",
                "phasec_true_threeway_basis_name": n43.TRUE_BASIS,
            }
        ]
    )
    registry_path = tmp_path / "registry.csv"
    cells_path = tmp_path / "cells.csv"
    registry.to_csv(registry_path, index=False)
    cells.to_csv(cells_path, index=False)

    loaded = n43.load_evogrow(
        registry_path,
        cells_path,
        {(1, 1): np.asarray([1.0, 3.0]), (1, 2): np.asarray([1.0, 3.0])},
        classes,
    )

    row = loaded.iloc[0]
    assert row["reconstruction_r2_variance_weighted"] == pytest.approx(0.9)
    assert row["generalization_r2_variance_weighted"] == pytest.approx(0.8)
    assert bool(row["generalization_r2_variance_weighted_available"])


def test_old_hierarchy_delta_table_reports_r2_and_structure_columns(tmp_path: Path) -> None:
    old = pd.DataFrame(
        [
            {
                "method": "SINDy",
                "configuration": "poly",
                "stratum": "overall",
                "reconstruction_r2_arithmetic_gt_0_9": 0.4,
                "generalization_r2_arithmetic_gt_0_9": 0.2,
                "raw_exact_support_match": 0.1,
                "pruned_exact_support_match": 0.1,
            }
        ]
    )
    new = old.copy()
    new.loc[0, "reconstruction_r2_arithmetic_gt_0_9"] = 0.7
    new.loc[0, "raw_exact_support_match"] = 0.3
    old_path = tmp_path / "old.csv"
    old.to_csv(old_path, index=False)

    deltas = n43.old_hierarchy_delta_table(new, old_path)

    assert set(deltas["metric"]) == {
        "reconstruction_r2_arithmetic_gt_0_9",
        "generalization_r2_arithmetic_gt_0_9",
        "raw_exact_support_match",
        "pruned_exact_support_match",
    }
    rec = deltas[deltas["metric"].eq("reconstruction_r2_arithmetic_gt_0_9")].iloc[0]
    raw = deltas[deltas["metric"].eq("raw_exact_support_match")].iloc[0]
    assert rec["difference_new_minus_old"] == pytest.approx(0.3)
    assert raw["difference_new_minus_old"] == pytest.approx(0.2)
