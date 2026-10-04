import csv

from experiments.annihilator_gate2a_v2.config import FUNCTIONS, Settings, domain_for
from experiments.annihilator_gate2a_v2.evaluate_gate2a import k2_wrong_majority, summarize
from experiments.annihilator_gate2a_v2.functions import noisy_sample
from experiments.annihilator_gate2a_v2.operator_search import search_once


def test_single_clean_search_smoke():
    settings = Settings(n=300, modes=6, ell_max=3, sigma_floor_factor=1e-8, boot_reps=2)
    domain = domain_for(FUNCTIONS["F2"], "wide")
    _, z, values, _ = noisy_sample("F2", domain, settings.n, 0.0, 0)
    selection = search_once(z, values, 0.0, settings)
    assert selection.selected_class is not None
    assert selection.tested_classes >= 1


def test_cell_summary_keeps_states_separate():
    rows = [
        {"function": "F2", "domain": "wide", "eta": "0.01", "state": "CORRECT"},
        {"function": "F2", "domain": "wide", "eta": "0.01", "state": "TRUE_NOT_REF"},
        {"function": "F2", "domain": "wide", "eta": "0.01", "state": "WRONG"},
    ]
    cells = summarize(rows)
    assert cells[0]["CORRECT"] == 1
    assert cells[0]["TRUE_NOT_REF"] == 1
    assert cells[0]["WRONG"] == 1


def test_k2_ignores_five_percent_wrong_majority():
    rows = [
        {
            "function": "F2",
            "domain": "wide",
            "eta": "0.05",
            "seed": str(seed),
            "state": "WRONG",
            "selected_r": "2",
            "selected_d": "0",
        }
        for seed in range(10)
    ]
    assert k2_wrong_majority(rows) is None
