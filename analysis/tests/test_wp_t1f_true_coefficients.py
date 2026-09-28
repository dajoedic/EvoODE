import copy
import json

import pytest

from studies.regression.export_wp_t1f_true_coefficients import (
    DEFAULT_CLASSIFICATION,
    DEFAULT_SUPPORT,
    export_coefficients,
)


def test_wp_t1f_export_matches_phase_c_support_terms() -> None:
    data = export_coefficients(DEFAULT_CLASSIFICATION, DEFAULT_SUPPORT)
    with DEFAULT_SUPPORT.open("r", encoding="utf-8") as handle:
        support = json.load(handle)

    selected = [
        system
        for system in support["systems"]
        if system["representability"] == "exact"
        and int(system["dim"]) in (2, 3)
        and int(system["system_id"]) != 63
    ]
    assert len(data["systems"]) == 18
    for system in selected:
        exported = data["systems"][str(system["system_id"])]
        for equation, expected_terms in zip(
            exported["equations"], system["support_terms"], strict=True
        ):
            assert equation["support_terms"] == expected_terms
            assert set(equation["coefficients"]) == set(expected_terms)


def test_wp_t1f_export_aborts_on_wrong_support_term(tmp_path) -> None:
    with DEFAULT_SUPPORT.open("r", encoding="utf-8") as handle:
        broken = copy.deepcopy(json.load(handle))
    for system in broken["systems"]:
        if int(system["system_id"]) == 24:
            system["support_terms"][0] = ["u1"]
            break
    broken_path = tmp_path / "broken_support.json"
    broken_path.write_text(json.dumps(broken), encoding="utf-8")

    with pytest.raises(ValueError, match="do not exactly match"):
        export_coefficients(DEFAULT_CLASSIFICATION, broken_path)
