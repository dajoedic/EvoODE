import sympy as sp

from experiments.annihilator_odebench_smoke.catalog import check_init_constraint, derive_test_initial_conditions, load_systems, training_domain


def test_catalog_parser_matches_smoke_document_formulas():
    x = sp.Symbol("x")
    expected = {
        3: sp.Rational(79, 100) * x * (1 - x / sp.Rational(743, 10)),
        7: sp.Rational(4, 125) * x * sp.log(sp.Rational(229, 100) * x),
        19: x * (1 - x) - sp.Rational(2, 25) * x / (sp.Rational(4, 5) + x),
        21: sp.Rational(6, 5) - sp.Rational(1, 5) * x - sp.exp(-x),
    }
    systems = load_systems()
    assert set(systems) == {3, 7, 19, 21}
    for sid, expr in expected.items():
        assert abs(float((systems[sid].sympy_expr - expr).subs(x, sp.Rational(6, 5)))) < 1e-12


def test_test_initial_condition_rule_and_replacement_cases():
    systems = load_systems()
    for system in systems.values():
        domain = training_domain(system)
        ics = derive_test_initial_conditions(system, domain)
        assert check_init_constraint(system, float(ics["mid"]))
        assert check_init_constraint(system, float(ics["hi"]))
        assert check_init_constraint(system, float(ics["lo"]))
        if system.system_id == 21:
            assert ics["lo_rule"] == "xmax_plus_R_over_2"
