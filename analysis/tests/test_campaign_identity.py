import argparse
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
from scripts.aggregate.verify_campaign_registry import verify  # noqa: E402
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
