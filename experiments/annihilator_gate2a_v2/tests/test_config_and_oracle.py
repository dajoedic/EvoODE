import numpy as np

from experiments.annihilator_gate2a_v2.config import CALIBRATION_FUNCTIONS, CLASSES, FUNCTIONS, settings_for_variant
from experiments.annihilator_gate2a_v2.oracle import symbolic_residual


def test_class_order_and_variants():
    assert len(CLASSES) == 42
    assert CLASSES[0] == (1, 0)
    assert CLASSES[1] == (2, 0)
    assert settings_for_variant("S1").n == 1000
    assert settings_for_variant("S14").boot_threshold == 0.9
    assert set(CALIBRATION_FUNCTIONS) == {f"K{i}" for i in range(1, 9)}


def test_symbolic_residual_for_known_f2_wide_operator_is_small():
    residual = symbolic_residual("F2", "wide", 1, 0, np.asarray([-3.0, 1.0]))
    values = [float(abs(residual.subs({"z": z}))) for z in np.linspace(-0.8, 0.8, 7)]
    assert max(values) < 1e-8
