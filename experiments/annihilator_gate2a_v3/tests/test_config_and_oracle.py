import numpy as np
import mpmath as mp

from experiments.annihilator_gate2a_v3.config import CALIBRATION_FUNCTIONS, CLASSES, FUNCTIONS, settings_for_variant
from experiments.annihilator_gate2a_v3.functions import symbolic_z
from experiments.annihilator_gate2a_v3.oracle import lambdify_mpmath_derivative, lambdify_scipy_derivative, symbolic_residual


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


def test_k3_k4_derivatives_lambdify_to_mpmath_and_scipy():
    mp.mp.dps = 80
    points = [mp.mpf("-0.7"), mp.mpf("-0.05"), mp.mpf("0.6")]
    for function_key in ("K3", "K4"):
        spec = CALIBRATION_FUNCTIONS[function_key]
        for domain_name in ("wide", "narrow"):
            domain = getattr(spec, domain_name)
            z, expr = symbolic_z(function_key, domain)
            mpmath_derivatives = [lambdify_mpmath_derivative(z, expr, order) for order in range(7)]
            scipy_derivatives = [lambdify_scipy_derivative(z, expr, order) for order in range(7)]
            mu = mp.mpf(str(domain.mu))
            scale = mp.mpf(str(domain.scale))
            base = (lambda t: mp.airyai(mu + scale * t)) if function_key == "K3" else (lambda t: mp.besselj(0, mu + scale * t))
            for point in points:
                for order, derivative in enumerate(mpmath_derivatives):
                    expected = mp.diff(base, point, order)
                    assert abs(derivative(point) - expected) < mp.mpf("1e-30")
                    assert abs(float(scipy_derivatives[order](float(point))) - float(expected)) < 1e-9
