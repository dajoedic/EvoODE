from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_CAMPAIGN_ID = "paper1_phaseB_v1"


def campaign_registry_path(repo_root: Path, campaign_id: str) -> Path:
    return repo_root / "experiments" / campaign_id / "run_registry.csv"


def campaign_data_dir(analysis_root: Path, campaign_id: str) -> Path:
    return analysis_root / "data" / campaign_id


def campaign_tables_dir(analysis_root: Path, campaign_id: str) -> Path:
    return analysis_root / "tables" / campaign_id


def campaign_config_path(analysis_root: Path, campaign_id: str) -> Path:
    return analysis_root / "configs" / f"{campaign_id}.json"


def normalized_campaign_value(value: Any) -> str:
    return "" if pd.isna(value) else str(value).strip()


def require_single_campaign_id(
    df: pd.DataFrame, expected_campaign_id: str, source_name: str
) -> str:
    if "experiment_id" not in df.columns:
        raise ValueError(f"{source_name} is missing required column: experiment_id")

    values = sorted(
        {
            normalized_campaign_value(value)
            for value in df["experiment_id"]
            if normalized_campaign_value(value) != ""
        }
    )
    if not values:
        raise ValueError(f"{source_name} has no experiment_id values")
    if len(values) != 1:
        raise ValueError(
            f"{source_name} must contain exactly one experiment_id; got {values}"
        )
    campaign_id = values[0]
    if campaign_id != expected_campaign_id:
        raise ValueError(
            f"{source_name} experiment_id {campaign_id!r} does not match "
            f"requested campaign {expected_campaign_id!r}"
        )
    return campaign_id
