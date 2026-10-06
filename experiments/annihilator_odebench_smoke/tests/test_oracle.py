from experiments.annihilator_gate2a_v3.config import FUNCTIONS, domain_for
from experiments.annihilator_gate2a_v3.functions import symbolic_x
from experiments.annihilator_gate2a_v3.oracle import n_exact as v3_n_exact
from experiments.annihilator_gate2a_v3.oracle import reference_for as v3_reference_for
from experiments.annihilator_odebench_smoke.oracle import oracle_for_expr


def test_generalized_oracle_matches_v3_for_f4_f5_on_v3_wide_domain():
    for key in ("F4", "F5"):
        _, expr = symbolic_x(key)
        result = oracle_for_expr(expr, domain_for(FUNCTIONS[key], "wide"))
        v3_class, _ = v3_reference_for(key, "wide")
        assert result.reference_class == v3_class
        assert result.reference_n_exact == v3_n_exact(key, "wide", *v3_class)
        assert result.verification["passed"] is True

