"""Structural categories and decision-rule evaluation."""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

from .config import SPEC_VERSION, STRUCT_NRMSE_F_MAX, TRUE_BASELINE_TERMS


ANNIHILATOR_EXACT = {"CORRECT"}
ANNIHILATOR_SUPERSET = {"TRUE_NOT_REF"}
BASELINE_EXACT = {"TRUE_STRUCTURE"}
BASELINE_SUPERSET = {"TRUE_PLUS"}


def annihilator_struct_ok(state: str, nrmse_f: float) -> bool:
    return state in ANNIHILATOR_EXACT and nrmse_f <= STRUCT_NRMSE_F_MAX


def baseline_category(system_id: int, selected_terms: set[str] | None, failed: bool = False) -> str:
    if failed or not selected_terms:
        return "FAIL"
    true_terms = TRUE_BASELINE_TERMS[system_id]
    if true_terms is None:
        return "SURROGATE"
    if selected_terms == true_terms:
        return "TRUE_STRUCTURE"
    if true_terms.issubset(selected_terms):
        return "TRUE_PLUS"
    return "SURROGATE"


def baseline_struct_ok(category: str, nrmse_f: float) -> bool:
    return category in BASELINE_EXACT and nrmse_f <= STRUCT_NRMSE_F_MAX


def record_struct_ok(record: dict) -> bool:
    if record["method"] == "annihilator":
        return annihilator_struct_ok(record.get("state", "NONE"), float(record.get("nrmse_f", float("inf"))))
    return baseline_struct_ok(record.get("category", "FAIL"), float(record.get("nrmse_f", float("inf"))))


def require_spec_version_2(records: list[dict]) -> None:
    bad = [index for index, record in enumerate(records, start=1) if record.get("spec_version") != SPEC_VERSION]
    if bad:
        raise ValueError(f"record(s) without spec_version == {SPEC_VERSION}: lines {bad[:5]}")


def system_ok(records: list[dict], method: str, eta: float, system_id: int) -> bool:
    subset = [r for r in records if r["method"] == method and float(r["eta"]) == eta and int(r["system_id"]) == system_id]
    if not subset:
        return False
    if eta == 0.0:
        return record_struct_ok(subset[0])
    return sum(record_struct_ok(r) for r in subset) >= 3


def median_value(records: list[dict], key: str) -> float:
    values = [float(r[key]) for r in records if key in r]
    return float(statistics.median(values)) if values else float("inf")


def evaluate_decision(records: list[dict]) -> dict:
    require_spec_version_2(records)
    systems = sorted({int(r["system_id"]) for r in records})
    counts = {
        method: {
            str(eta): sum(system_ok(records, method, eta, sid) for sid in systems)
            for eta in (0.0, 0.01)
        }
        for method in ("annihilator", "sindy", "wsindy")
    }
    if counts["annihilator"]["0.0"] < 3:
        return {"decision": "end", "rule": "A", "struct_ok_counts": counts}
    if counts["annihilator"]["0.01"] <= 2 and counts["wsindy"]["0.01"] >= 3:
        return {"decision": "end", "rule": "B", "struct_ok_counts": counts}
    c_hits = 0
    for sid in systems:
        ann = [r for r in records if r["method"] == "annihilator" and float(r["eta"]) == 0.01 and int(r["system_id"]) == sid]
        ws = [r for r in records if r["method"] == "wsindy" and float(r["eta"]) == 0.01 and int(r["system_id"]) == sid]
        if not ann or not ws:
            continue
        wrong_majority = Counter(r.get("state") for r in ann)["WRONG"] >= 3
        ann_train = median_value(ann, "train_nrmse_x_median")
        ann_test = median_value(ann, "test_nrmse_x_median")
        ws_test = median_value(ws, "test_nrmse_x_median")
        if wrong_majority and ann_train <= 0.05 and ann_test > 2.0 * ws_test:
            c_hits += 1
    if c_hits >= 2:
        return {"decision": "end", "rule": "C", "struct_ok_counts": counts, "c_systems": c_hits}
    comparable = 0
    for sid in systems:
        ann = [r for r in records if r["method"] == "annihilator" and float(r["eta"]) == 0.01 and int(r["system_id"]) == sid]
        sindy = [r for r in records if r["method"] == "sindy" and float(r["eta"]) == 0.01 and int(r["system_id"]) == sid]
        ws = [r for r in records if r["method"] == "wsindy" and float(r["eta"]) == 0.01 and int(r["system_id"]) == sid]
        if ann and sindy and ws and median_value(ann, "test_nrmse_x_median") <= 2.0 * min(median_value(sindy, "test_nrmse_x_median"), median_value(ws, "test_nrmse_x_median")):
            comparable += 1
    if counts["annihilator"]["0.01"] >= 3 and comparable >= 3:
        return {"decision": "discuss", "rule": "weiter diskutieren", "struct_ok_counts": counts, "comparable_systems": comparable}
    return {"decision": "end", "rule": "otherwise", "struct_ok_counts": counts, "comparable_systems": comparable}


def grouped_table(records: list[dict]) -> list[dict]:
    require_spec_version_2(records)
    groups = defaultdict(list)
    for record in records:
        groups[(record["method"], float(record["eta"]), int(record["system_id"]))].append(record)
    rows = []
    for (method, eta, system_id), subset in sorted(groups.items()):
        rows.append({
            "method": method,
            "eta": eta,
            "system_id": system_id,
            "n": len(subset),
            "struct_ok": sum(record_struct_ok(r) for r in subset),
            "median_nrmse_f": median_value(subset, "nrmse_f"),
            "median_test_nrmse_x": median_value(subset, "test_nrmse_x_median"),
        })
    return rows
