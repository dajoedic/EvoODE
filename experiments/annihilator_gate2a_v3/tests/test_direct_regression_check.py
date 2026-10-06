from __future__ import annotations

import copy
import math

import numpy as np
import pytest

from experiments.annihilator_gate2a_v3.config import FUNCTIONS, Settings, domain_for
from experiments.annihilator_gate2a_v3.diagnostics import direct_regression_check as drc
from experiments.annihilator_gate2a_v3.functions import numeric_values, rms


def test_library_size_and_admissibility_by_domain():
    assert len(drc.LIBRARY) == 23
    excluded = {"sqrt(x)", "x^1.5", "log(x)", "x log(x)", "1/(1+x)", "1/(2+x)"}
    for function_key in ("F3", "F4", "F5", "F8"):
        assert len(drc.admissible_terms(function_key, grid_size=100)) == 23
    for function_key in ("F1", "F2", "F6", "F7", "F9", "F10"):
        names = {term.name for term in drc.admissible_terms(function_key, grid_size=100)}
        assert len(names) == 17
        assert set(drc.TERM_BY_NAME) - names == excluded


@pytest.mark.parametrize("function_key", list(FUNCTIONS))
def test_true_term_sets_reproduce_true_functions(function_key):
    domain = domain_for(FUNCTIONS[function_key], drc.DOMAIN_NAME)
    x = np.linspace(domain.a, domain.b, 1000)
    prediction = np.zeros_like(x)
    for name, coeff in drc.TRUE_COEFFICIENTS[function_key].items():
        prediction += coeff * drc.TERM_BY_NAME[name].evaluate(x)
    error = rms(prediction - numeric_values(function_key, x)) / rms(numeric_values(function_key, x))
    assert error < 1e-12


def test_category_examples():
    assert drc.category_for("F8", ("1", "1/(2+x)")) == ("TRUE_STRUCTURE", None)
    assert drc.category_for("F8", ("1", "x", "1/(2+x)")) == ("TRUE_PLUS", None)
    assert drc.category_for("F8", ("1", "x")) == ("SURROGATE", None)
    assert drc.category_for("F8", None, "no fit") == ("FAIL", "no fit")


def test_best_subset_selects_first_accepted_k_and_lowest_rss(monkeypatch):
    terms = [drc.Term("a", lambda x: x), drc.Term("b", lambda x: x), drc.Term("c", lambda x: x)]
    rss_by_subset = {
        ("a",): 100.0,
        ("b",): 100.0,
        ("c",): 100.0,
        ("a", "b"): 2.0,
        ("a", "c"): 1.0,
        ("b", "c"): 3.0,
    }

    def fake_fit_subset(x, y, subset):
        names = tuple(term.name for term in subset)
        return {name: 1.0 for name in names}, rss_by_subset[names]

    monkeypatch.setattr(drc, "fit_subset", fake_fit_subset)
    monkeypatch.setattr(drc, "chi2_critical", lambda n, k: 10.0)
    fit = drc.best_subset_fit(np.arange(4.0), np.arange(4.0), 1.0, terms)
    assert fit.selected == ("a", "c")
    assert fit.rss == 1.0
    assert fit.fits == 6
    assert fit.accepted_at_k == 3


def _real_baseline_record() -> dict:
    record = drc.run_one("F1", drc.SEED_BASE, "BS", eta=0.0)
    assert set(record) >= {
        "function",
        "seed",
        "method",
        "category",
        "selected_terms",
        "coefficients",
        "k",
        "rss",
        "T",
        "critical",
        "accepted_at_k",
        "fits",
    }
    return record


def _baseline_records(primary_true: int, primary_surr: int, control_true: int) -> list[dict]:
    base = _real_baseline_record()
    records = []
    primary_categories = ["TRUE_STRUCTURE"] * primary_true + ["SURROGATE"] * primary_surr
    primary_categories += ["TRUE_PLUS"] * (60 - len(primary_categories))
    control_categories = ["TRUE_STRUCTURE"] * control_true + ["SURROGATE"] * (60 - control_true)
    for functions, categories in (
        (drc.PRIMARY_FUNCTIONS, primary_categories),
        (drc.CONTROL_FUNCTIONS, control_categories),
    ):
        idx = 0
        for seed in range(drc.SEED_BASE, drc.SEED_END + 1):
            for function_key in functions:
                for method in ("BS", "STLSQ"):
                    record = copy.deepcopy(base)
                    record.update({"function": function_key, "seed": seed, "method": method, "category": categories[idx]})
                    records.append(record)
                idx += 1
    return records


def test_summarize_thresholds_and_real_annihilator_records():
    annihilator_records = drc.load_annihilator_records()
    strong = drc.summarize_records(_baseline_records(primary_true=42, primary_surr=12, control_true=42), annihilator_records)
    assert strong["verdict"] == "STRONG_NEGATIVE"
    assert math.isclose(strong["p_true"], 0.70)
    assert math.isclose(strong["p_surr"], 0.20)
    assert strong["annihilator"]["paired"]["N1"]["wrong_over_unambiguous"] == "25/25"
    assert strong["annihilator"]["paired"]["I"]["wrong_over_unambiguous"] == "0/57"
    assert strong["annihilator"]["reference"]["N1"]["wrong_over_unambiguous"] == "118/118"
    assert strong["annihilator"]["reference"]["I"]["wrong_over_unambiguous"] == "0/297"
    assert strong["annihilator"]["reference"]["N1"]["wrong_given_unambiguous"] == 1.0
    assert strong["annihilator"]["reference"]["I"]["wrong_given_unambiguous"] == 0.0
    assert math.isclose(strong["baseline_false_unique"]["N1"]["BS"], 12 / 60)
    assert math.isclose(strong["baseline_false_unique"]["I"]["BS"], 18 / 60)
    assert math.isclose(strong["baseline_false_unique"]["N1"]["STLSQ"], 12 / 60)
    assert math.isclose(strong["baseline_false_unique"]["I"]["STLSQ"], 18 / 60)

    open_summary = drc.summarize_records(_baseline_records(primary_true=42, primary_surr=13, control_true=42), annihilator_records)
    assert open_summary["verdict"] == "OPEN"

    invalid = drc.summarize_records(_baseline_records(primary_true=60, primary_surr=0, control_true=41), annihilator_records)
    assert invalid["verdict"] == "INVALID"


def test_summarize_requires_complete_primary_seeds():
    records = _baseline_records(primary_true=42, primary_surr=12, control_true=42)
    records = [record for record in records if not (record["function"] == "F4" and record["seed"] == drc.SEED_BASE)]
    with pytest.raises(SystemExit):
        drc.summarize_records(records, drc.load_annihilator_records())


def test_tau_matches_frozen_value():
    assert Settings().n == 2000
    assert drc.tau_from_diagnostic_settings() == 3.386508022297224e-07
