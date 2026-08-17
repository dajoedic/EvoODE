import sys
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.plot.table_main_results import build_csv_table  # noqa: E402


def test_unknown_variant_is_not_silently_dropped_from_main_table() -> None:
    rows = []
    for system_id, system_name in [(2, "s2"), (23, "s23")]:
        rows.append(
            {
                "variant_slug": "evogrow_v1",
                "system_id": system_id,
                "system_name": system_name,
                "mean_loss": 1.0,
                "std_loss": 0.1,
                "exact_match_rate": 0.5,
                "n_valid": 1,
            }
        )
        rows.append(
            {
                "variant_slug": "campaign_unknown_variant",
                "system_id": system_id,
                "system_name": system_name,
                "mean_loss": 2.0,
                "std_loss": 0.2,
                "exact_match_rate": 0.25,
                "n_valid": 1,
            }
        )

    table = build_csv_table(pd.DataFrame(rows))

    assert "campaign_unknown_variant" in set(table["variant_slug"])
