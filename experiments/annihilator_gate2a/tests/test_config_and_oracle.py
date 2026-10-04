import numpy as np

from experiments.annihilator_gate2a.config import CLASSES, FUNCTIONS, class_columns, settings_for_variant
from experiments.annihilator_gate2a.oracle import build_reference, reference_for, symbolic_residual


def test_class_order_and_variants():
    assert len(CLASSES) == 42
    assert CLASSES[0] == (1, 0)
    assert CLASSES[1] == (2, 0)
    assert settings_for_variant("S1").n == 1000
    assert settings_for_variant("S11").boot_threshold == 0.9


def test_oracle_reference_classes():
    ref = build_reference(force=False)
    for key, spec in FUNCTIONS.items():
        for domain in ("wide", "narrow"):
            assert tuple(ref["functions"][key][domain]["reference_class"]) == spec.reference_class
            cls = ref["functions"][key][domain]["classes"][f"{spec.reference_class[0]},{spec.reference_class[1]}"]
            assert cls["n_exact"] == 1


def test_symbolic_residuals_f1_to_f9_are_small():
    for key in [f"F{i}" for i in range(1, 10)]:
        (r, d), coeffs = reference_for(key, "wide")
        residual = symbolic_residual(key, "wide", r, d, coeffs)
        values = [float(abs(residual.subs({"z": z}))) for z in np.linspace(-0.8, 0.8, 7)]
        assert max(values) < 1e-8
