import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate import analyze_pretuning_distribution_collapse as collapse  # noqa: E402


def row(variant_slug: str, use_pretuning: bool) -> dict[str, object]:
    return {
        "experiment_id": "paper1_phaseC_v1",
        "variant_slug": variant_slug,
        "use_pretuning": use_pretuning,
        "system_id": 1,
        "system_name": "system_1",
        "system_dim": 1,
        "system_representability": "exact",
        "seed": 42,
        "initial_condition_set": 1,
        "loss": 0.1,
        "r2": 0.9,
        "support_terms": '[["u1"]]',
    }


def phasec_mapping() -> dict[str, dict[str, object]]:
    return {
        "pretune_on": {
            "variant_slug": "evogrow_v2_2_stage_capped_pretune_on",
            "use_pretuning": True,
        },
        "pretune_off": {
            "variant_slug": "evogrow_v2_2_stage_capped",
            "use_pretuning": False,
        },
    }


def test_pretuning_condition_mapping_comes_from_config_and_uses_pretuning_flag() -> None:
    frame = pd.DataFrame(
        [
            row("evogrow_v2_2_stage_capped", False),
            row("evogrow_v2_2_stage_capped_pretune_on", True),
        ]
    )

    registry = collapse.validate_registry(frame, "paper1_phaseC_v1", phasec_mapping())

    assert set(registry["condition"]) == {"pretune_off", "pretune_on"}


def test_pretuning_mapping_rejects_matching_slug_with_wrong_use_pretuning() -> None:
    frame = pd.DataFrame([row("evogrow_v2_2_stage_capped_pretune_on", False)])

    try:
        collapse.validate_registry(frame, "paper1_phaseC_v1", phasec_mapping())
    except ValueError as exc:
        assert "variant/use_pretuning" in str(exc)
    else:
        raise AssertionError("wrong use_pretuning flag should fail")
