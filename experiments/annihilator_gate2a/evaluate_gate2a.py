"""Evaluate Gate 2A run CSVs and write cell summaries/verdicts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from .config import FUNCTIONS, RESULTS


STATES = ("CORRECT", "AMBIGUOUS", "TRUE_NOT_REF", "WRONG", "NONE")


def read_rows(path: Path) -> list[dict]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def cell_key(row: dict) -> tuple[str, str, str]:
    return row["function"], row["domain"], row["eta"]


def summarize(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[cell_key(row)].append(row)
    out = []
    for (function, domain, eta), items in sorted(grouped.items()):
        counts = Counter(item["state"] for item in items)
        record = {"function": function, "domain": domain, "eta": eta, "n": len(items)}
        for state in STATES:
            record[state] = counts[state]
        transfer_values = [item["transfer_passed"] for item in items if item.get("transfer_passed") not in ("", None)]
        record["transfer_passed"] = sum(v == "True" for v in transfer_values)
        record["transfer_total"] = len(transfer_values)
        out.append(record)
    return out


def _criterion(value, threshold, passed: bool) -> dict:
    return {"value": value, "threshold": threshold, "passed": bool(passed)}


def _cell_id(cell: dict) -> tuple[str, str, str]:
    return cell["function"], cell["domain"], str(cell["eta"])


def _majority_counts(cells: list[dict], state: str) -> int:
    return sum(1 for c in cells if c[state] > c["n"] / 2)


def k2_wrong_majority(rows: list[dict]) -> dict | None:
    grouped: dict[tuple[str, str, str, str], int] = defaultdict(int)
    for row in rows:
        if abs(float(row["eta"]) - 0.01) >= 1e-12:
            continue
        if row["state"] != "WRONG":
            continue
        selected = f"{row.get('selected_r', '')},{row.get('selected_d', '')}"
        grouped[(row["function"], row["domain"], str(row["eta"]), selected)] += 1
    if not grouped:
        return None
    key, count = max(grouped.items(), key=lambda item: item[1])
    if count >= 10:
        return {"cell": key[:3], "class": key[3], "count": count}
    return None


def k3_result(standard_cells: list[dict], variant_cells: dict[str, list[dict]] | None) -> dict:
    if not variant_cells:
        return {"value": "NOT_EVALUATED", "threshold": "all S1-S11 present", "passed": False}
    expected = {f"S{i}" for i in range(1, 12)}
    if set(variant_cells) != expected:
        return {"value": "NOT_EVALUATED", "available_variants": sorted(variant_cells), "threshold": sorted(expected), "passed": False}
    std = {_cell_id(c): c for c in standard_cells}
    std_clean = {key: c for key, c in std.items() if float(key[2]) == 0.0}
    std_wrong_majority_1pct = _majority_counts([c for c in standard_cells if abs(float(c["eta"]) - 0.01) < 1e-12], "WRONG")
    std_correct_majority_1pct = _majority_counts([c for c in standard_cells if abs(float(c["eta"]) - 0.01) < 1e-12], "CORRECT")
    failures = []
    for variant, cells in variant_cells.items():
        by_key = {_cell_id(c): c for c in cells}
        for key, std_cell in std_clean.items():
            other = by_key.get(key)
            if other is not None and std_cell["CORRECT"] == std_cell["n"] and other["CORRECT"] != other["n"]:
                failures.append({"variant": variant, "cell": key, "reason": "clean_correct_changed"})
        one_pct = [c for c in cells if abs(float(c["eta"]) - 0.01) < 1e-12]
        wrong_delta = abs(_majority_counts(one_pct, "WRONG") - std_wrong_majority_1pct)
        correct_delta = abs(_majority_counts(one_pct, "CORRECT") - std_correct_majority_1pct)
        if wrong_delta > 2 or correct_delta > 2:
            failures.append({"variant": variant, "wrong_delta": wrong_delta, "correct_delta": correct_delta})
    return {"value": failures, "threshold": "no clean CORRECT loss; majority-count deltas <= 2", "passed": not failures}


def verdict_for(rows: list[dict], cells: list[dict], variant_cells: dict[str, list[dict]] | None = None) -> dict:
    clean_wrong = [c for c in cells if float(c["eta"]) == 0.0 and c["WRONG"] > 0]
    wide_clean_wrong = [c for c in clean_wrong if c["domain"] == "wide"]
    k1 = len(clean_wrong) >= 2 or bool(wide_clean_wrong)
    one_pct = [c for c in cells if abs(float(c["eta"]) - 0.01) < 1e-12]
    pass_1pct_wrong = all(c["WRONG"] <= 2 for c in one_pct)
    simple = {"F1", "F2", "F3", "F6", "F7"}
    pass_1pct_simple = all(c["CORRECT"] >= 11 for c in one_pct if c["domain"] == "wide" and c["function"] in simple)
    clean_wide = [c for c in cells if float(c["eta"]) == 0.0 and c["domain"] == "wide"]
    max_clean_angle = max((float(row["coeff_angle"]) for row in rows if row["domain"] == "wide" and float(row["eta"]) == 0.0 and row.get("coeff_angle") not in ("", None)), default=float("inf"))
    pass_clean = len(clean_wide) == 10 and all(c["CORRECT"] == c["n"] for c in clean_wide) and max_clean_angle < 1e-6 and not any(c["WRONG"] for c in cells if float(c["eta"]) == 0.0 and c["domain"] == "narrow")
    k4 = any(c["domain"] == "wide" and c["function"] in simple and c["CORRECT"] < 11 and (c["NONE"] + c["WRONG"]) > (c["n"] - c["CORRECT"]) / 2 for c in one_pct)
    k2 = k2_wrong_majority(rows)
    k3 = k3_result(cells, variant_cells)
    criteria = {
        "clean": _criterion({"wide_clean_cells": len(clean_wide), "max_wide_clean_coeff_angle": max_clean_angle, "narrow_clean_wrong_cells": sum(c["WRONG"] > 0 for c in cells if float(c["eta"]) == 0.0 and c["domain"] == "narrow")}, "10 wide CORRECT cells, angle < 1e-6, 0 narrow WRONG", pass_clean),
        "one_percent_wrong": _criterion(max((c["WRONG"] for c in one_pct), default=None), "<= 2 WRONG per cell", pass_1pct_wrong),
        "one_percent_simple": _criterion({c["function"]: c["CORRECT"] for c in one_pct if c["domain"] == "wide" and c["function"] in simple}, ">= 11 CORRECT for F1,F2,F3,F6,F7 wide", pass_1pct_simple),
        "k1": _criterion({"clean_wrong_cells": len(clean_wrong), "wide_clean_wrong_cells": len(wide_clean_wrong)}, "kill if clean WRONG cells >= 2 or any wide clean WRONG", not k1),
        "k2": _criterion(k2, "kill if a WRONG class reaches >= 10 of 20 in any 1% cell", k2 is None),
        "k3": k3,
        "k4": _criterion(k4, "kill if a simple wide 1% cell has <11 CORRECT and remaining majority NONE/WRONG", not k4),
    }
    if k1 or k2 is not None or k4 or k3["passed"] is False and k3["value"] != "NOT_EVALUATED":
        overall = "KILL"
    elif pass_clean and pass_1pct_wrong and pass_1pct_simple and k3["passed"]:
        overall = "PASS"
    else:
        overall = "USER_DECISION"
    return {
        "criteria": criteria,
        "overall": overall,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", default="standard")
    args = parser.parse_args()
    run_path = RESULTS / args.variant / "runs.csv"
    rows = read_rows(run_path)
    cells = summarize(rows)
    write_csv(RESULTS / args.variant / "cells.csv", cells)
    variant_cells = {}
    if args.variant == "standard":
        for path in sorted(RESULTS.glob("S*/runs.csv")):
            variant_cells[path.parent.name] = summarize(read_rows(path))
    verdict = {args.variant: verdict_for(rows, cells, variant_cells or None)}
    (RESULTS / "gate2a_verdict.json").write_text(json.dumps(verdict, indent=2, sort_keys=True))
    print(f"wrote {len(cells)} cells and verdict")


if __name__ == "__main__":
    main()
