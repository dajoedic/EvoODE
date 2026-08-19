import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.evaluate_hypotheses import (  # noqa: E402
    campaign_message,
    classify_dataset,
    validate_inputs,
)
from utils.io import load_aggregate  # noqa: E402


def test_phase_a_data_uses_existing_validation_path() -> None:
    aggregate_path = ANALYSIS_ROOT / "data/paper1_phaseA_v1/aggregate_by_variant_system.csv"
    df = load_aggregate(aggregate_path)
    df["system_id"] = pd.to_numeric(df["system_id"], errors="raise").astype(int)

    dataset_kind, reasons = classify_dataset(df, "paper1_phaseA_v1", aggregate_path)

    assert dataset_kind == "phase_a"
    assert "all Phase A variants are present" in reasons
    assert validate_inputs(df) == []


def test_campaign_bridge_data_reports_non_applicable_phase_a_hypotheses() -> None:
    aggregate_path = ANALYSIS_ROOT / "data/wp_a1_campaign_bridge_probe/aggregate_by_variant_system.csv"
    df = load_aggregate(aggregate_path)
    df["system_id"] = pd.to_numeric(df["system_id"], errors="raise").astype(int)

    dataset_kind, reasons = classify_dataset(df, "wp_a2_campaign_bridge_probe", aggregate_path)
    message = campaign_message(df, "wp_a2_campaign_bridge_probe", aggregate_path, reasons)

    assert dataset_kind == "campaign"
    assert "H1-H4 are Phase A hypotheses" in message
    assert "does not define that comparison" in message
    assert "Missing expected variants" not in message
