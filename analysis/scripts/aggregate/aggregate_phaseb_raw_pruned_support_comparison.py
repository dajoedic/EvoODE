import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.metrics import check_required_columns  # noqa: E402
from utils.support_match_definition import (  # noqa: E402
    PRUNED_SUPPORT_MATCH,
    infer_exact_support_match_definition,
)


DEFAULT_REGISTRY = REPO_ROOT / "experiments" / "paper1_phaseB_v1" / "run_registry.csv"
DEFAULT_STRUCTURE_METRICS = (
    ANALYSIS_ROOT / "data" / "paper1_phaseB_v1" / "phaseb_structure_metrics_by_cell.csv"
)
DEFAULT_OUTPUT = (
    ANALYSIS_ROOT
    / "data"
    / "paper1_phaseB_v1"
    / "phaseb_raw_pruned_support_comparison.csv"
)

EXPECTED_EXACT_CELLS = 240
EXPECTED_PRUNED_MATCHES = 110
EXPECTED_RAW_MATCHES = 70
EXPECTED_PRUNING_RESCUED_MATCHES = 40


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare raw and pruned Phase-B exact support matches."
    )
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--structure-metrics", default=str(DEFAULT_STRUCTURE_METRICS))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


def coerce_optional_bool(value: Any, column: str) -> bool | None:
    if pd.isna(value) or str(value).strip() == "":
        return None
    lowered = str(value).strip().lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"{column} contains non-boolean value: {value}")


def summarize(group: pd.DataFrame, level: str, keys: dict[str, Any]) -> dict[str, Any]:
    n_exact_cells = int(len(group))
    raw_matches = int(group["raw_exact_support_match"].sum())
    pruned_matches = int(group["pruned_exact_support_match"].sum())
    rescued = int(group["pruning_rescued_support_match"].sum())
    return {
        "aggregation_level": level,
        "system_dim": keys.get("system_dim", ""),
        "condition": keys.get("condition", ""),
        "initial_condition_set": keys.get("initial_condition_set", ""),
        "n_exact_cells": n_exact_cells,
        "raw_exact_support_match_count": raw_matches,
        "pruned_exact_support_match_count": pruned_matches,
        "pruning_rescued_support_match_count": rescued,
        "raw_exact_support_match_rate": raw_matches / n_exact_cells,
        "pruned_exact_support_match_rate": pruned_matches / n_exact_cells,
        "pruning_rescued_support_match_rate": rescued / n_exact_cells,
    }


def build_comparison(registry: pd.DataFrame, metrics: pd.DataFrame) -> pd.DataFrame:
    check_required_columns(
        registry,
        [
            "run_id",
            "experiment_id",
            "system_representability",
            "system_dim",
            "condition",
            "initial_condition_set",
            "exact_support_match",
        ],
    )
    check_required_columns(
        metrics,
        [
            "run_id",
            "structural_exact_support_match",
            "n_missing_true_terms",
        ],
    )
    definition = infer_exact_support_match_definition(registry, "Phase-B run_registry")
    if definition.definition != PRUNED_SUPPORT_MATCH:
        raise ValueError(
            "Phase-B raw/pruned comparison requires pruned registry "
            f"exact_support_match, got {definition.definition}"
        )

    exact = registry.loc[
        registry["system_representability"].astype(str).str.lower().eq("exact")
    ].copy()
    exact["pruned_exact_support_match"] = exact["exact_support_match"].map(
        lambda value: coerce_optional_bool(value, "exact_support_match")
    )
    if exact["pruned_exact_support_match"].isna().any():
        raise ValueError("exact_support_match is missing for exact Phase-B cells")

    merged = exact.merge(
        metrics[["run_id", "structural_exact_support_match", "n_missing_true_terms"]],
        on="run_id",
        how="left",
        validate="one_to_one",
    )
    if merged["structural_exact_support_match"].isna().any():
        raise ValueError("Missing structure metrics for exact Phase-B cells")

    merged["raw_exact_support_match"] = merged["structural_exact_support_match"].map(bool)
    merged["pruned_exact_support_match"] = merged["pruned_exact_support_match"].map(bool)
    merged["pruning_rescued_support_match"] = (
        merged["pruned_exact_support_match"] & ~merged["raw_exact_support_match"]
    )

    totals = summarize(merged, "overall", {})
    expected = {
        "n_exact_cells": EXPECTED_EXACT_CELLS,
        "pruned_exact_support_match_count": EXPECTED_PRUNED_MATCHES,
        "raw_exact_support_match_count": EXPECTED_RAW_MATCHES,
        "pruning_rescued_support_match_count": EXPECTED_PRUNING_RESCUED_MATCHES,
    }
    mismatches = {
        column: (totals[column], expected[column])
        for column in expected
        if totals[column] != expected[column]
    }
    if mismatches:
        raise ValueError(f"Unexpected raw/pruned support totals: {mismatches}")

    rows = [totals]
    for column, level in [
        ("system_dim", "by_dimension"),
        ("condition", "by_condition"),
        ("initial_condition_set", "by_initial_condition_set"),
    ]:
        for key, group in merged.groupby(column, sort=True):
            rows.append(summarize(group, level, {column: key}))
    for keys, group in merged.groupby(
        ["system_dim", "condition", "initial_condition_set"], sort=True
    ):
        dim, condition, ic_set = keys
        rows.append(
            summarize(
                group,
                "by_dimension_condition_initial_condition_set",
                {
                    "system_dim": int(dim),
                    "condition": condition,
                    "initial_condition_set": int(ic_set),
                },
            )
        )
    return pd.DataFrame(rows)


def run(registry_path: Path, metrics_path: Path, output_path: Path) -> dict[str, Any]:
    table = build_comparison(
        pd.read_csv(registry_path),
        pd.read_csv(metrics_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_path, index=False, float_format="%.12g")
    totals = table.loc[table["aggregation_level"].eq("overall")].iloc[0].to_dict()
    return {"output_path": output_path, "rows": len(table), "totals": totals}


def main() -> int:
    args = parse_args()
    try:
        result = run(Path(args.registry), Path(args.structure_metrics), Path(args.output))
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {result['output_path'].relative_to(REPO_ROOT)}")
    print(f"Rows: {result['rows']}")
    totals = result["totals"]
    print(
        "Totals: "
        f"exact={int(totals['n_exact_cells'])}, "
        f"pruned={int(totals['pruned_exact_support_match_count'])}, "
        f"raw={int(totals['raw_exact_support_match_count'])}, "
        f"rescued={int(totals['pruning_rescued_support_match_count'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
