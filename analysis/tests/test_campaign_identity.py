import argparse
import json
import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_phaseb_structure_metrics import (  # noqa: E402
    resolve_paths,
)
from scripts.aggregate.verify_campaign_registry import (  # noqa: E402
    apply_phase_c_support_expectations,
    verify,
)
from utils.campaign import require_single_campaign_id  # noqa: E402


def registry_rows(experiment_ids: list[str]) -> list[dict[str, str]]:
    rows = []
    for index, experiment_id in enumerate(experiment_ids, start=1):
        rows.append(
            {
                "experiment_id": experiment_id,
                "system_id": str(index),
                "seed": "42",
                "variant_slug": "evogrow_v1",
                "condition": "evogrow_v1",
                "initial_condition_set": "1",
                "corrupted": "false",
                "failure_reason": "",
                "git_hash": "91f88c4",
                "git_dirty": "false",
                "config_fingerprint": "604e79733b22d64d",
                "stage_cap_behavior_fingerprint": "ffb0266c7913352c",
                "system_representability": "exact",
                "exact_support_match": "true",
                "r2": "0.99",
            }
        )
    return rows


def verifier_args(
    campaign: str,
    expected_row_count: int,
    expected_unique_identities: int,
) -> argparse.Namespace:
    return argparse.Namespace(
        campaign=campaign,
        expected_row_count=expected_row_count,
        expected_unique_identities=expected_unique_identities,
        expected_rows_per_condition=expected_row_count,
        expected_exact_rows=expected_row_count,
        expected_surrogate_rows=0,
        phase_c_support_table=None,
        expected_git_hash="91f88c4",
        expected_config_fingerprint="604e79733b22d64d",
        expected_stage_cap_behavior_fingerprint="ffb0266c7913352c",
    )


def test_campaign_guard_rejects_mixed_experiment_ids() -> None:
    registry = pd.DataFrame(registry_rows(["paper1_phaseB_v1", "paper1_phaseC_v1"]))

    try:
        require_single_campaign_id(registry, "paper1_phaseB_v1", "fixture registry")
    except ValueError as exc:
        message = str(exc)
        assert "paper1_phaseB_v1" in message
        assert "paper1_phaseC_v1" in message
    else:
        raise AssertionError("Expected mixed experiment_id values to fail")


def test_campaign_guard_rejects_wrong_campaign_id() -> None:
    registry = pd.DataFrame(registry_rows(["paper1_phaseA_v1"]))

    try:
        require_single_campaign_id(registry, "paper1_phaseB_v1", "fixture registry")
    except ValueError as exc:
        message = str(exc)
        assert "paper1_phaseA_v1" in message
        assert "paper1_phaseB_v1" in message
    else:
        raise AssertionError("Expected mismatched experiment_id to fail")


def test_verify_campaign_registry_accepts_matching_campaign(capsys) -> None:
    rows = registry_rows(["paper1_phaseB_v1"])

    result = verify(rows, verifier_args("paper1_phaseB_v1", 1, 1))

    assert result == 0
    assert "Verified campaign registry: 1 rows" in capsys.readouterr().out


def test_verify_campaign_registry_derives_phasec_counts_from_support_table(capsys) -> None:
    work_dir = REPO_ROOT / ".pytest_tmp_phasec_registry_verify"
    work_dir.mkdir(exist_ok=True)
    support_path = work_dir / "phase_c_support.json"
    support_path.write_text(
        json.dumps(
            {
                "basis_name": "staged_polynomial_basis_with_constant",
                "systems": [
                    {"system_id": 1, "representability": "exact"},
                    {"system_id": 2, "representability": "surrogate"},
                ],
            }
        ),
        encoding="utf-8",
    )
    rows = []
    for condition, variant, system_ids in [
        ("capped", "evogrow_v2_2_stage_capped", [1, 2]),
        ("uncapped", "evogrow_v2_2_stage_local", [1, 2]),
        ("pretune_on", "evogrow_v2_2_stage_capped_pretune_on", [1]),
    ]:
        for system_id in system_ids:
            for seed in [42, 123, 7]:
                for ic_set in [1, 2]:
                    row = registry_rows(["paper1_phaseC_v1"])[0]
                    row.update(
                        {
                            "system_id": str(system_id),
                            "seed": str(seed),
                            "variant_slug": variant,
                            "condition": condition,
                            "initial_condition_set": str(ic_set),
                            "system_representability": "exact"
                            if system_id == 1
                            else "surrogate",
                            "exact_support_match": "true" if system_id == 1 else "",
                            "r2": "0.99",
                        }
                    )
                    rows.append(row)

    args = verifier_args("paper1_phaseC_v1", 0, 0)
    args.phase_c_support_table = str(support_path)

    result = verify(rows, apply_phase_c_support_expectations(args))

    assert result == 0
    assert "Representability: exact=18, surrogate=12" in capsys.readouterr().out
    support_path.unlink()
    work_dir.rmdir()


def test_structure_metric_paths_derive_from_campaign_and_allow_overrides() -> None:
    fixture_root = REPO_ROOT / ".pytest_tmp_wp_n13"
    explicit_registry = fixture_root / "registry.csv"
    explicit_output = fixture_root / "out"
    args = argparse.Namespace(
        campaign="paper1_phaseC_v1",
        registry=str(explicit_registry),
        classification=None,
        output_dir=str(explicit_output),
    )

    registry_path, classification_path, output_dir = resolve_paths(args)

    assert registry_path == explicit_registry
    assert classification_path == ANALYSIS_ROOT / "data" / "paper1_phaseC_v1" / "system_classification.csv"
    assert output_dir == explicit_output
