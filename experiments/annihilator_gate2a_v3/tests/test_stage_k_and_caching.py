import numpy as np

from experiments.annihilator_gate2a_v3.acceptance import accept_01_oracle
from experiments.annihilator_gate2a_v3.acceptance import appendix_b
from experiments.annihilator_gate2a_v3.acceptance import stage_k_calibration as stage_k
from experiments.annihilator_gate2a_v3.config import APPENDIX_A_JSON, CALIBRATION_FUNCTIONS, CLASSES, FUNCTIONS, Settings, domain_for
from experiments.annihilator_gate2a_v3.functions import grid, numeric_values
from experiments.annihilator_gate2a_v3.oracle import ORACLE_METADATA
from experiments.annihilator_gate2a_v3.weak_operator import WeightContext


class DummySelection:
    def __init__(self, selected_class, a1=False, a2=False, a3=False):
        self.selected_class = selected_class
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3


def test_stage_k_part_path_does_not_overwrite_appendix():
    assert stage_k._part_path("0/4", False) != APPENDIX_A_JSON
    assert stage_k._part_path("0/4", False).name == "appendix_A_part_0_of_4.json"


def test_stage_k_clean_state_reports_ambiguous_before_wrong():
    state, sources = stage_k._state_for_clean(None, "K1", "wide", DummySelection((1, 0), a3=True), (2, 0), True)
    assert state == "AMBIGUOUS"
    assert sources == ["A3"]


def test_stage_k_mc_non_identifiable_cell_is_not_checked():
    acc = stage_k._empty_mc_accumulator("K3", "N2")
    record = stage_k._finish_mc_record(acc, np.asarray([1.0, 0.0]))
    assert record["checked"] is False
    assert record["passed"] is None


def test_stage_k_clean_cells_are_distributed_across_parts(monkeypatch):
    monkeypatch.setattr(stage_k, "_mc_accumulators", lambda *args, **kwargs: {"K1": {"function": "K1"}})
    monkeypatch.setattr(stage_k, "_reference", lambda *args, **kwargs: ((1, 0), np.asarray([1.0])))
    monkeypatch.setattr(stage_k, "_finish_mc_record", lambda acc, coeffs: {"function": acc["function"], "passed": True})
    monkeypatch.setattr(
        stage_k,
        "_clean_records",
        lambda ell, tau, n, limit, part: {f"{function}_{domain}": {"passed": True} for function, domain in stage_k._selected_clean_cell_keys(part, limit)},
    )

    part0 = stage_k.stage_k_c(3, 1e-12, 20, 4, "0/2", {}, True)
    part1 = stage_k.stage_k_c(3, 1e-12, 20, 4, "1/2", {}, True)

    assert part0["clean_search_executed"] is True
    assert part0["clean"] == {"K1_wide": {"passed": True}}
    assert part1["clean_search_executed"] is True
    assert part1["clean"] == {"K1_narrow": {"passed": True}}


def test_oracle_worker_cache_requires_matching_function_list():
    classes = {_class_key: {"n_exact": 0} for _class_key in (f"{r},{d}" for r, d in CLASSES)}
    data = {
        "metadata": ORACLE_METADATA,
        "classes": [list(c) for c in CLASSES],
        "functions": {
            "K3": {
                "wide": {"classes": classes},
                "narrow": {"classes": classes},
            }
        },
    }
    assert accept_01_oracle._worker_cache_is_complete(data, ["K3"])
    assert not accept_01_oracle._worker_cache_is_complete(data, ["K3", "K4"])


def test_weight_context_reuses_split_arrays():
    settings = Settings(n=120, modes=6, ell_max=3, sigma_floor_factor=1e-8)
    domain = domain_for(FUNCTIONS["F2"], "wide")
    x, z = grid(domain, settings.n)
    values = numeric_values("F2", x)
    context = WeightContext(z, values, settings)
    first = context.split(1, 0)
    second = context.split(1, 0)
    assert first[0] is second[0]
    assert first[2] is second[2]


def test_appendix_b_cell_contains_required_fields():
    record = stage_k.ex_ante_cell("F1", FUNCTIONS["F1"], "wide", 0.01, 3, 1e-8, 80)

    assert record["function"] == "F1"
    assert record["domain"] == "wide"
    assert record["eta"] == 0.01
    assert record["class"] in {"I", "N1", "N2"}
    assert isinstance(record["theta_hat_c"], float)
    assert record["earlier"]
    assert {"class", "beta", "lambda", "dof", "critical"} <= set(record["earlier"][0])
    assert record["weakest_earlier"] in record["earlier"]


def test_appendix_b_shared_function_matches_stage_k_for_k2_wide(monkeypatch):
    monkeypatch.setattr(stage_k, "CALIBRATION_FUNCTIONS", {"K2": CALIBRATION_FUNCTIONS["K2"]})
    from_shared = stage_k.ex_ante_cell("K2", CALIBRATION_FUNCTIONS["K2"], "wide", 0.01, 3, 1e-8, 80)
    from_stage_k = stage_k.ex_ante_k_classes(3, 1e-8, 80)["K2"]["wide"]

    assert from_shared["class"] == from_stage_k["class"]
    assert np.isclose(from_shared["theta_hat_c"], from_stage_k["theta_hat_c"])
    assert [item["class"] for item in from_shared["earlier"]] == [item["class"] for item in from_stage_k["earlier"]]
    assert np.allclose(
        [item["beta"] for item in from_shared["earlier"]],
        [item["beta"] for item in from_stage_k["earlier"]],
    )


def test_appendix_b_k6_diagnostic_counts_wide_low_order_n_cells():
    records = {
        function_key: {
            "wide": {"0.01": {"class": "I", "reference_class": list(FUNCTIONS[function_key].reference_class), "theta_hat_c": 0.0, "weakest_earlier": None}},
            "narrow": {"0.01": {"class": "N2", "reference_class": list(FUNCTIONS[function_key].reference_class), "theta_hat_c": 1.0, "weakest_earlier": None}},
        }
        for function_key in FUNCTIONS
    }
    records["F1"]["wide"]["0.01"]["class"] = "N1"
    records["F4"]["wide"]["0.01"]["class"] = "N2"
    records["F9"]["wide"]["0.01"]["class"] = "N1"

    diagnostic = appendix_b.k6_diagnostic(records)

    assert diagnostic["affected_count"] == 2
    assert diagnostic["would_trigger"] is True
    assert [cell["function"] for cell in diagnostic["affected_cells"]] == ["F1", "F4"]
