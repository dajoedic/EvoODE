import numpy as np

from experiments.annihilator_odebench_smoke.catalog import Domain
from experiments.annihilator_odebench_smoke.fhat import basis_ivp_fhat
from experiments.annihilator_odebench_smoke.metrics import nrmse


def test_basis_ivp_fhat_reproduces_quadratic_for_d3_operator_on_production_interval():
    domain = Domain("unit", -1.0, 1.0)
    x = np.linspace(-1.0, 1.0, 25)
    truth = 2.0 - 3.0 * x + 0.5 * x**2
    fhat, fail = basis_ivp_fhat(np.array([0.0, 0.0, 0.0, 1.0]), 3, 0, domain, x, truth, (-5.0, 11.0))
    assert fail is None
    assert nrmse(fhat(x), truth) < 1e-12


def test_basis_ivp_fhat_limits_gompertz_operator_before_zero_outside_training_domain():
    domain = Domain("gompertz", 1.7, 30.0)
    x = np.linspace(domain.a, domain.b, 80)
    truth = 2.0 * x * np.log(x) + 3.0 * x
    coeffs = np.array([0.0, 0.0, 0.0, 0.0, domain.scale, 0.0, domain.mu, domain.scale])
    fhat, fail = basis_ivp_fhat(coeffs, 3, 1, domain, x, truth, (-10.0, 300.0))
    assert fail is None
    assert fhat.effective_interval[0] == np.float64(0.001 * (domain.b - domain.a))
    assert nrmse(fhat(x), truth) < 1e-10


def test_basis_ivp_fhat_reports_leading_zero_in_training_domain():
    domain = Domain("unit", -1.0, 1.0)
    x = np.linspace(-1.0, 1.0, 9)
    fhat, fail = basis_ivp_fhat(np.array([0.0, 0.0, 0.0, 1.0, 0.0, 1.0]), 2, 1, domain, x, x, (-3.0, 3.0))
    assert fhat is None
    assert fail == "LEADING_ZERO_IN_TRAINING_DOMAIN"
