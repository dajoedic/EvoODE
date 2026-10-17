import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "analysis"))
from scripts.aggregate import aggregate_c1_structure_inventory as inventory


@pytest.mark.parametrize("truth,found,label,missing,extra", [
    ({"x"}, {"x"}, "exact", 0, 0),
    ({"x"}, {"y"}, "disjoint", 1, 1),
    ({"x", "y"}, {"x"}, "subset", 1, 0),
    ({"x"}, {"x", "y"}, "superset", 0, 1),
    ({"x", "y"}, {"x", "z"}, "mixed", 1, 1),
    (set(), set(), "exact", 0, 0),
    ({"x"}, set(), "disjoint", 1, 0),
    (set(), {"x"}, "disjoint", 0, 1),
])
def test_classification_and_check_order(truth, found, label, missing, extra):
    result = inventory.classify(truth, found)
    assert result == {"class": label, "n_true": len(truth), "missing": missing,
                      "extra": extra, "needs_add": missing > 0, "needs_remove": extra > 0}


def test_cell_pairs_keep_equation_identity():
    truth = inventory.cell_support_pairs([["u1"], ["u1"]])
    assert truth == {(1, "u1"), (2, "u1")}
    result = inventory.classify(truth, inventory.cell_support_pairs([["u1"], []]))
    assert result["class"] == "subset"
    assert result["missing"] == 1
    swapped = inventory.classify(inventory.cell_support_pairs([["u1"], ["u2"]]),
                                 inventory.cell_support_pairs([["u2"], ["u1"]]))
    assert swapped["class"] == "disjoint"
    assert swapped["missing"] == swapped["extra"] == 2


@pytest.fixture
def real_inputs():
    # Derive error cases from the frozen C-1 registry, retaining the actual schema.
    registry = pd.read_csv(REPO_ROOT / inventory.REGISTRY)
    support = json.loads((REPO_ROOT / inventory.SUPPORT).read_text(encoding="utf-8"))
    return registry, support


@pytest.mark.parametrize("kind", inventory.KINDS)
def test_exact_flag_disagreement_aborts(real_inputs, kind):
    registry, support = real_inputs
    column = f"exact_support_match_{kind}"
    registry.loc[0, column] = not bool(registry.loc[0, column])
    with pytest.raises(ValueError, match="Exact-match control diverging rows"):
        inventory.build_inventory(registry, support)


def test_wrong_row_count_aborts(real_inputs):
    registry, support = real_inputs
    with pytest.raises(ValueError, match="Expected 378 C-1 rows / 180 exact rows"):
        inventory.build_inventory(registry.iloc[1:], support)


@pytest.mark.parametrize("column", ["support_terms", "pruned_support_terms"])
def test_equation_count_mismatch_aborts(real_inputs, column):
    registry, support = real_inputs
    registry.loc[0, column] = "[]"
    with pytest.raises(ValueError, match="expected 1 equations, found 0"):
        inventory.build_inventory(registry, support)


def test_frozen_acceptance_counts(real_inputs):
    equations, cells = inventory.build_inventory(*real_inputs)
    assert len(cells) == 180
    assert len(equations) == 708
    expected = {
        "pruned": [(31, 10, 9, 16), (49, 37, 2, 32), (0, 1, 1, 34), (9, 38, 5, 56), (4, 0, 5, 15)],
        "raw": [(21, 24, 6, 15), (19, 67, 2, 32), (0, 1, 1, 34), (8, 39, 4, 57), (4, 0, 5, 15)],
    }
    for kind, strata in expected.items():
        for stratum, counts in zip(inventory.STRATA, strata):
            group = equations.loc[(equations.kind == kind) & (equations.stratum == stratum)]
            actual = tuple(int(((group.needs_add == a) & (group.needs_remove == r)).sum())
                           for a, r in ((False, False), (False, True), (True, False), (True, True)))
            assert actual == counts, (kind, stratum, actual, counts)
    for kind, expected_cells in {
        "pruned": {"exact": 53, "subset": 10, "superset": 22, "mixed": 89, "disjoint": 6},
        "raw": {"exact": 24, "subset": 7, "superset": 55, "mixed": 88, "disjoint": 6},
    }.items():
        assert cells[f"{kind}_class"].value_counts().to_dict() == expected_cells
    assert int(((cells.raw_class == "superset") & (cells.pruned_class == "exact")).sum()) == 29
    tables = inventory.summaries(equations, cells)
    assert tables["summary_equations_by_stratum.csv"].groupby("summary_type")["count"].sum().to_dict() == {
        "class": 708, "two_axis": 708}
    assert tables["summary_cells_by_stratum.csv"]["count"].sum() == 360
    assert tables["summary_by_system.csv"].groupby("level")["count"].sum().to_dict() == {
        "cell": 360, "equation": 708}
    assert tables["transition_raw_to_pruned_cells.csv"]["count"].sum() == 180
    assert tables["r2_by_class_cells.csv"]["total"].sum() == 180
