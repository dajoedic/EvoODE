from experiments.annihilator_odebench_smoke.categories import baseline_category, evaluate_decision, record_struct_ok
from experiments.annihilator_odebench_smoke.run import annihilator_state_for_system


def record(method, system_id, eta, seed, *, ok=False, state="CORRECT", category="TRUE_STRUCTURE", train=0.01, test=0.01):
    return {
        "spec_version": 2,
        "method": method,
        "system_id": system_id,
        "eta": eta,
        "seed": seed,
        "state": state,
        "category": category,
        "nrmse_f": 0.01 if ok else 1.0,
        "struct_ok": ok,
        "train_nrmse_x_median": train,
        "test_nrmse_x_median": test,
    }


def test_method_categories_and_struct_ok():
    assert not record_struct_ok(record("annihilator", 3, 0.0, 0, ok=True, state="TRUE_NOT_REF"))
    assert not record_struct_ok(record("annihilator", 3, 0.0, 0, ok=False, state="AMBIGUOUS"))
    assert record_struct_ok({**record("annihilator", 3, 0.0, 0, ok=True, state="CORRECT"), "struct_ok": False})
    assert baseline_category(3, {"x", "x^2"}) == "TRUE_STRUCTURE"
    assert baseline_category(3, {"x", "x^2", "1"}) == "TRUE_PLUS"
    assert not record_struct_ok(record("sindy", 3, 0.0, 0, ok=True, category="TRUE_PLUS"))
    assert record_struct_ok({**record("sindy", 3, 0.0, 0, ok=True, category="TRUE_STRUCTURE"), "struct_ok": False})
    assert baseline_category(19, {"x", "x^2"}) == "SURROGATE"


def test_decision_rejects_unversioned_records():
    bad = record("annihilator", 3, 0.0, 0, ok=True)
    bad.pop("spec_version")
    try:
        evaluate_decision([bad])
    except ValueError as exc:
        assert "spec_version == 2" in str(exc)
    else:
        raise AssertionError("unversioned records must be rejected")


def test_decision_rule_a_b_c_discuss_and_otherwise_from_derived_records():
    systems = [3, 7, 19, 21]
    a_records = [record("annihilator", sid, 0.0, 0, ok=sid in (3, 7)) for sid in systems]
    assert evaluate_decision(a_records)["rule"] == "A"

    b_records = [record("annihilator", sid, 0.0, 0, ok=True) for sid in systems]
    for sid in systems:
        for seed in range(5):
            b_records.append(record("annihilator", sid, 0.01, seed, ok=sid == 3))
            b_records.append(record("wsindy", sid, 0.01, seed, ok=sid != 19))
    assert evaluate_decision(b_records)["rule"] == "B"

    c_records = [record("annihilator", sid, 0.0, 0, ok=True) for sid in systems]
    for sid in systems:
        for seed in range(5):
            c_records.append(record("annihilator", sid, 0.01, seed, ok=sid in (3, 7, 19), state="WRONG" if sid in (3, 7) else "CORRECT", train=0.01, test=0.3))
            c_records.append(record("wsindy", sid, 0.01, seed, ok=sid in (3, 7), test=0.1))
    assert evaluate_decision(c_records)["rule"] == "C"

    discuss_records = [record("annihilator", sid, 0.0, 0, ok=True) for sid in systems]
    for sid in systems:
        for seed in range(5):
            discuss_records.append(record("annihilator", sid, 0.01, seed, ok=sid != 19, test=0.2))
            discuss_records.append(record("sindy", sid, 0.01, seed, ok=sid != 19, test=0.1))
            discuss_records.append(record("wsindy", sid, 0.01, seed, ok=sid != 19, test=0.11))
    assert evaluate_decision(discuss_records)["rule"] == "weiter diskutieren"

    other_records = [record("annihilator", sid, 0.0, 0, ok=True) for sid in systems]
    for sid in systems:
        for seed in range(5):
            other_records.append(record("annihilator", sid, 0.01, seed, ok=sid in (3, 7, 19), test=1.0))
            other_records.append(record("sindy", sid, 0.01, seed, ok=False, test=0.1))
            other_records.append(record("wsindy", sid, 0.01, seed, ok=False, test=0.1))
    assert evaluate_decision(other_records)["rule"] == "otherwise"


def test_annihilator_state_uses_selected_class_n_exact_not_componentwise_rule(monkeypatch):
    class System:
        system_id = 999

    def fake_n_exact(_system, selected):
        assert selected == (4, 4)
        return 0

    monkeypatch.setattr("experiments.annihilator_odebench_smoke.run.n_exact_for_class", fake_n_exact)
    state, n_exact = annihilator_state_for_system(System(), (4, 4), (3, 3), False)
    assert n_exact == 0
    assert state == "WRONG"
