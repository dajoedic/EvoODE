import sys
from pathlib import Path
from shutil import rmtree

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
assert (REPO_ROOT / "CLAUDE.md").is_file()
ANALYSIS_ROOT = REPO_ROOT / "analysis"
if str(ANALYSIS_ROOT) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_ROOT))

from scripts.aggregate.aggregate_phaseb_raw_pruned_support_comparison import (  # noqa: E402
    build_comparison,
)
from scripts.aggregate.aggregate_phaseb_structure_metrics import run as run_structure_metrics  # noqa: E402
from utils.support_match_definition import (  # noqa: E402
    PRUNED_SUPPORT_MATCH,
    RAW_SUPPORT_MATCH,
    infer_exact_support_match_definition,
    require_compatible_exact_support_match_definitions,
)


REGISTRY = REPO_ROOT / "experiments" / "paper1_phaseB_v1" / "run_registry.csv"
CLASSIFICATION = ANALYSIS_ROOT / "data" / "paper1_phaseB_v1" / "system_classification.csv"
TMP_OUTPUT = REPO_ROOT / ".pytest_tmp_wp_n7b"


def run_structure_metrics_in_workspace() -> dict[str, object]:
    if TMP_OUTPUT.exists():
        rmtree(TMP_OUTPUT)
    TMP_OUTPUT.mkdir()
    return run_structure_metrics(REGISTRY, CLASSIFICATION, TMP_OUTPUT)


def test_phaseb_pruned_match_implies_no_missing_true_terms() -> None:
    try:
        result = run_structure_metrics_in_workspace()
        metrics = pd.read_csv(result["cell_path"])
        exact = metrics.loc[metrics["registry_exact_support_match"].notna()]
        pruned_matches = exact.loc[exact["registry_exact_support_match"].astype(bool)]

        assert len(exact) == 240
        assert len(pruned_matches) == 110
        assert int(pruned_matches["n_missing_true_terms"].sum()) == 0
        assert int(exact["n_missing_true_terms"].eq(0).sum()) == 119
    finally:
        if TMP_OUTPUT.exists():
            rmtree(TMP_OUTPUT)


def test_phaseb_raw_pruned_support_comparison_reproduces_checked_totals() -> None:
    try:
        result = run_structure_metrics_in_workspace()
        table = build_comparison(pd.read_csv(REGISTRY), pd.read_csv(result["cell_path"]))
        overall = table.loc[table["aggregation_level"].eq("overall")].iloc[0]

        assert int(overall["n_exact_cells"]) == 240
        assert int(overall["pruned_exact_support_match_count"]) == 110
        assert int(overall["raw_exact_support_match_count"]) == 70
        assert int(overall["pruning_rescued_support_match_count"]) == 40
    finally:
        if TMP_OUTPUT.exists():
            rmtree(TMP_OUTPUT)


def test_support_match_definition_guard_accepts_compatible_phaseb_registries() -> None:
    registry = pd.DataFrame(
        {
            "experiment_id": ["paper1_phaseB_v1"],
            "phase": ["B"],
            "run_type": ["campaign_cell"],
            "exact_support_match": [True],
        }
    )

    definition = require_compatible_exact_support_match_definitions(
        [(registry, "left"), (registry.copy(), "right")]
    )

    assert definition.definition == PRUNED_SUPPORT_MATCH


def test_support_match_definition_guard_rejects_phasea_phaseb_conflict() -> None:
    phase_a = pd.DataFrame(
        {
            "experiment_id": ["paper1_phaseA_v1"],
            "phase": ["A"],
            "exact_support_match": [True],
        }
    )
    phase_b = pd.DataFrame(
        {
            "experiment_id": ["paper1_phaseB_v1"],
            "phase": ["B"],
            "run_type": ["campaign_cell"],
            "exact_support_match": [True],
        }
    )

    try:
        require_compatible_exact_support_match_definitions(
            [(phase_a, "phase_a.csv"), (phase_b, "phase_b.csv")]
        )
    except ValueError as exc:
        message = str(exc)
        assert RAW_SUPPORT_MATCH in message
        assert PRUNED_SUPPORT_MATCH in message
    else:
        raise AssertionError("Expected conflicting exact_support_match definitions")


def test_support_match_definition_can_read_explicit_metadata() -> None:
    registry = pd.DataFrame(
        {
            "exact_support_match_definition": ["raw"],
            "exact_support_match": [False],
        }
    )

    definition = infer_exact_support_match_definition(registry, "explicit.csv")

    assert definition.definition == RAW_SUPPORT_MATCH
