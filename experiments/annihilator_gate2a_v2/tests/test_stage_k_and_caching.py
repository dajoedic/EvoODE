import numpy as np

from experiments.annihilator_gate2a_v2.acceptance import stage_k_calibration as stage_k
from experiments.annihilator_gate2a_v2.config import APPENDIX_A_JSON, FUNCTIONS, Settings, domain_for
from experiments.annihilator_gate2a_v2.functions import grid, numeric_values
from experiments.annihilator_gate2a_v2.weak_operator import WeightContext


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
