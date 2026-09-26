import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


ANALYSIS_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = ANALYSIS_ROOT.parent
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from utils.campaign import require_single_campaign_id  # noqa: E402
from utils.io import load_run_registry  # noqa: E402
from utils.metrics import check_required_columns  # noqa: E402


CAMPAIGN_ID = "paper1_phaseC_v1"
C1_VARIANT = "evogrow_v2_2_stage_capped"
C2_VARIANT = "evogrow_v2_2_stage_local"
C3_VARIANT = "evogrow_v2_2_stage_capped_pretune_on"
DEFAULT_REGISTRY = REPO_ROOT / "outputs" / "phase_c_dryrun_2026-09-25" / "run_registry.csv"
DEFAULT_STRUCTURE = (
    REPO_ROOT
    / "outputs"
    / "phase_c_dryrun_2026-09-25"
    / "agg"
    / "structure_n26"
    / "phasec_structure_metrics_by_cell.csv"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "outputs"
    / "phase_c_dryrun_2026-09-25"
    / "agg_n28"
    / "phasec_analysis_registry.csv"
)
DEFAULT_SUPPORT = REPO_ROOT / "studies" / "regression" / "phase_c_support.json"

JOIN_KEY = "run_id"
MICRO_ALIASES = {
    "structural_f1": "structural_f1_micro",
    "term_precision": "term_precision_micro",
    "term_recall": "term_recall_micro",
}
STRUCTURE_COLUMNS = [
    "run_id",
    "structural_f1_micro",
    "structural_f1_macro",
    "term_precision_micro",
    "term_precision_macro",
    "term_recall_micro",
    "term_recall_macro",
    "coefficient_relative_error_mean",
    "coefficient_relative_error_max",
    "n_coefficient_terms",
    "n_equations",
    "n_found_terms_micro",
    "n_true_terms_micro",
    "n_true_positive_terms_micro",
    "n_missing_true_terms",
    "n_extra_found_terms",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Join Phase-C campaign registry rows to per-cell structure metrics."
    )
    parser.add_argument("--campaign", default=CAMPAIGN_ID)
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--structure-metrics", default=str(DEFAULT_STRUCTURE))
    parser.add_argument("--phase-c-support", default=str(DEFAULT_SUPPORT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Write subsets for an incomplete campaign and record expected/actual counts.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    fail(f"use_pretuning is not boolean: {value!r}")
    raise AssertionError("unreachable")


def support_counts(path: Path) -> dict[str, int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    systems = payload.get("systems", [])
    exact = sum(1 for row in systems if row.get("representability") == "exact")
    surrogate = sum(1 for row in systems if row.get("representability") == "surrogate")
    if exact != 30 or surrogate != 33:
        fail(f"unexpected Phase-C support counts: exact={exact}, surrogate={surrogate}")
    return {"all_systems": exact + surrogate, "exact_systems": exact}


def expected_counts(registry: pd.DataFrame, support: dict[str, int]) -> dict[str, int]:
    seeds = int(registry["seed"].nunique())
    ic_sets = int(registry["initial_condition_set"].nunique())
    per_system = seeds * ic_sets
    return {
        "analysis_registry": support["all_systems"] * per_system * 2
        + support["exact_systems"] * per_system,
        "c1_c2": support["all_systems"] * per_system * 2,
        "c1": support["all_systems"] * per_system,
        "pretuning": support["exact_systems"] * per_system * 2,
    }


def assert_unique_run_ids(frame: pd.DataFrame, label: str) -> None:
    if JOIN_KEY not in frame.columns:
        fail(f"{label} is missing {JOIN_KEY!r}")
    duplicates = frame.loc[frame[JOIN_KEY].duplicated(), JOIN_KEY].astype(str).unique().tolist()
    if duplicates:
        fail(f"{label} contains duplicate run_id values: {duplicates[:5]}")


def load_inputs(registry_path: Path, structure_path: Path, campaign_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    registry = load_run_registry(registry_path)
    structure = pd.read_csv(structure_path)
    require_single_campaign_id(registry, campaign_id, "run_registry")
    require_single_campaign_id(structure, campaign_id, "structure_metrics")
    check_required_columns(registry, ["run_id", "variant_slug", "use_pretuning", "system_representability"])
    check_required_columns(structure, STRUCTURE_COLUMNS)
    assert_unique_run_ids(registry, "run_registry")
    assert_unique_run_ids(structure, "structure_metrics")
    return registry, structure


def join_registry(registry: pd.DataFrame, structure: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(registry[JOIN_KEY].astype(str)) - set(structure[JOIN_KEY].astype(str)))
    extra = sorted(set(structure[JOIN_KEY].astype(str)) - set(registry[JOIN_KEY].astype(str)))
    if missing or extra:
        fail(
            "structure metric join is not 1:1 by run_id: "
            f"missing_metrics={missing[:5]}, extra_metrics={extra[:5]}"
        )
    metric_columns = STRUCTURE_COLUMNS
    joined = registry.merge(
        structure[metric_columns],
        on=JOIN_KEY,
        how="inner",
        validate="one_to_one",
        suffixes=("", "_structure"),
    )
    if len(joined) != len(registry):
        fail(f"joined registry row count changed from {len(registry)} to {len(joined)}")
    for alias, source in MICRO_ALIASES.items():
        joined[alias] = joined[source]
    return joined


def subset_c1_c2(df: pd.DataFrame) -> pd.DataFrame:
    use_pretuning = df["use_pretuning"].map(parse_bool)
    return df.loc[
        df["variant_slug"].isin([C1_VARIANT, C2_VARIANT]) & (~use_pretuning)
    ].copy()


def subset_c1(df: pd.DataFrame) -> pd.DataFrame:
    use_pretuning = df["use_pretuning"].map(parse_bool)
    return df.loc[(df["variant_slug"] == C1_VARIANT) & (~use_pretuning)].copy()


def subset_pretuning(df: pd.DataFrame) -> pd.DataFrame:
    use_pretuning = df["use_pretuning"].map(parse_bool)
    c1_exact = (
        (df["variant_slug"] == C1_VARIANT)
        & (~use_pretuning)
        & (df["system_representability"].astype(str) == "exact")
    )
    c3 = (df["variant_slug"] == C3_VARIANT) & use_pretuning
    return df.loc[c1_exact | c3].copy()


def validate_counts(
    subsets: dict[str, pd.DataFrame],
    expected: dict[str, int],
    allow_incomplete: bool,
) -> dict[str, dict[str, Any]]:
    counts = {}
    for name, frame in subsets.items():
        actual = int(len(frame))
        wanted = int(expected[name])
        complete = actual == wanted
        if not complete and not allow_incomplete:
            fail(f"{name} expected {wanted} rows, got {actual}; pass --allow-incomplete for dry-run data")
        counts[name] = {"expected": wanted, "actual": actual, "complete": complete}
    return counts


def write_outputs(output: Path, joined: pd.DataFrame, allow_incomplete: bool, counts: dict[str, dict[str, Any]]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    subsets = {
        "analysis_registry": joined,
        "c1_c2": subset_c1_c2(joined),
        "c1": subset_c1(joined),
        "pretuning": subset_pretuning(joined),
    }
    joined.to_csv(output, index=False)
    stem = output.with_suffix("")
    subsets["c1_c2"].to_csv(Path(f"{stem}_c1_c2.csv"), index=False)
    subsets["c1"].to_csv(Path(f"{stem}_c1.csv"), index=False)
    subsets["pretuning"].to_csv(Path(f"{stem}_pretuning.csv"), index=False)
    metadata = {
        "allow_incomplete": allow_incomplete,
        "counts": counts,
        "micro_aliases": MICRO_ALIASES,
    }
    Path(f"{stem}_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    try:
        registry, structure = load_inputs(
            Path(args.registry).resolve(),
            Path(args.structure_metrics).resolve(),
            args.campaign,
        )
        joined = join_registry(registry, structure)
        subsets = {
            "analysis_registry": joined,
            "c1_c2": subset_c1_c2(joined),
            "c1": subset_c1(joined),
            "pretuning": subset_pretuning(joined),
        }
        counts = validate_counts(
            subsets,
            expected_counts(joined, support_counts(Path(args.phase_c_support).resolve())),
            args.allow_incomplete,
        )
        write_outputs(Path(args.output).resolve(), joined, args.allow_incomplete, counts)
        print("Phase-C analysis registry completed")
        for name, count in counts.items():
            print(f"  {name}: {count['actual']} / {count['expected']}")
        return 0
    except (OSError, KeyError, json.JSONDecodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
