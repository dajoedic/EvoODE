"""Aggregate frozen Q3 arms against the true-structure P-04 reference."""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis"))
from scripts.aggregate.build_sideproject_q3_weak_starts import DEFAULT_OUTPUT, sha256
from scripts.aggregate.aggregate_phasec_restart_curve import (
    best_start, checked_starts, read_jsonl, R2_THRESHOLD, SENTINEL_LOSS,
)
from scripts.aggregate.run_sideproject_residual_growth import STRATA, PRIMARY

P04 = ROOT / "outputs/phase_c_c5_restart_curve_5dd1df8/out"
RESULTS = ROOT / "outputs/sideproject_q3_weak_start/results.jsonl"
CONTROLS = ("sys0001_ic1", "sys0024_ic1", "sys0052_ic1")
REFERENCE = "reference"  # Frozen protocol requires true structure, unlike task's oracle_starts.


def identity(row):
    return int(row["system_id"]), int(row["initial_condition_set"])


def hit(value):
    return value is not None and math.isfinite(float(value)) and float(value) > R2_THRESHOLD


def compare_loss(value, reference):
    if value == reference or abs(value - reference) <= 1e-12 * abs(reference):
        return "equal"
    return "better" if value < reference else "worse"


def load_p04(directory):
    paths = sorted(directory.glob("**/*.jsonl"))
    rows = [r for p in paths for r in read_jsonl(p)]
    keys = [(identity(r), int(r["seed"])) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("Duplicate P-04 cells")
    for r in rows:
        if r.get("error") is not None or ("reference_structure" in r and r["true_structure"] != r["reference_structure"]):
            raise ValueError("Invalid P-04 reference")
        starts = checked_starts(r, REFERENCE, 10)
        if len(starts) != 10 or {s["start_index"] for s in starts} != set(range(1, 11)):
            raise ValueError("Expected exactly ten reference starts")
        for s in starts:
            if not math.isfinite(float(s["loss"])):
                raise ValueError("Nonfinite P-04 loss")
            int(s["fit_meta"]["loss_evals"])
    return rows, paths


def aggregate_units(weak_units, results, references, require_complete=True):
    expected = {identity(u): u for u in weak_units}
    actual = {identity(r): r for r in results}
    if len(actual) != len(results) or set(actual) != set(expected):
        raise ValueError("Missing, extra or duplicate Q3 units")
    if require_complete and len(expected) != 60:
        raise ValueError("Expected 60 Q3 units")
    refs = {}
    for r in references:
        key, seed = identity(r), int(r["seed"])
        if (key, seed) in refs or key not in expected:
            raise ValueError("Duplicate or extra P-04 cell")
        refs[key, seed] = r
    seeds = sorted({seed for _, seed in refs})
    if require_complete and seeds != [7, 42, 123]:
        raise ValueError("Expected P-04 seeds 7, 42, 123")
    if not seeds or set(refs) != {(key, seed) for key in expected for seed in seeds}:
        raise ValueError("Missing P-04 cells")
    rows = []
    for key, unit in sorted(expected.items()):
        r = actual[key]
        if r["unit_id"] != unit["unit_id"] or r["stratum"] != unit["stratum"] or r["dim"] != unit["dim"]:
            raise ValueError("Q3 identity mismatch")
        if r["trajectory_sha256"] != unit["trajectory_sha256"] or not r["trajectory_control"]["passed"]:
            raise ValueError("Trajectory control failed")
        if require_complete and unit["unit_id"] in CONTROLS:
            control = r.get("random_start_control")
            if not control or not control["passed"] or control["seed"] != 7:
                raise ValueError("P-04 start-1 reproduction failed or absent")
            expected_loss = best_start(refs[key, 7], REFERENCE, 1)["loss"]
            if control["expected_loss"] != expected_loss or control["actual_loss"] != expected_loss:
                raise ValueError("P-04 start-1 loss mismatch")
        row = dict(unit_id=unit["unit_id"], system_id=key[0], initial_condition_set=key[1],
                   dim=unit["dim"], stratum=unit["stratum"], trajectory_sha256=unit["trajectory_sha256"],
                   weak_abs_gt_10_count=sum(abs(c) > 10 for c in unit["p0"]))
        for arm in ("W0", "W1"):
            result = r[arm]
            loss = float(result["loss"])
            if not math.isfinite(loss):
                raise ValueError("Nonfinite Q3 loss")
            row[arm + "_loss"] = loss
            row[arm + "_r2"] = result["r2"]
            row[arm + "_success"] = hit(result["r2"])
            row[arm + "_r2_by_dim"] = json.dumps(result["r2_by_dim"])
            row[arm + "_coefficients"] = json.dumps(result["coefficients"])
            row[arm + "_sentinel"] = loss >= SENTINEL_LOSS
        row["W1_loss_evals"] = int(r["W1"]["fit_meta"]["loss_evals"])
        row["W1_fit_meta"] = json.dumps(r["W1"]["fit_meta"], sort_keys=True)
        for k in (1, 3, 10):
            sums = []
            for seed in seeds:
                ref = refs[key, seed]
                if ref["true_structure"] != [eq["term_names"] for eq in unit["equations"]]:
                    raise ValueError("P-04 true structure differs from weak support")
                best = best_start(ref, REFERENCE, k)
                prefix = f"P04_seed{seed}_best{k}"
                row[prefix + "_loss"] = float(best["loss"])
                row[prefix + "_r2"] = best["r2"]
                row[prefix + "_success"] = hit(best["r2"])
                row[prefix + "_start_index"] = int(best["start_index"])
                count = sum(int(s["fit_meta"]["loss_evals"]) for s in checked_starts(ref, REFERENCE, k))
                row[prefix + "_loss_evals_sum"] = count
                sums.append(count)
                if k == 10:
                    row[f"W1_vs_P04_seed{seed}_best10_loss"] = compare_loss(row["W1_loss"], best["loss"])
            row[f"P04_best{k}_loss_evals_median"] = statistics.median(sums)
        rows.append(row)
    return rows, summarize_rules(rows, seeds)


def summarize_rules(rows, seeds):
    rules = []
    for stratum in STRATA:
        group = [r for r in rows if r["stratum"] == stratum]
        if not group:
            continue
        num, den = sum(r["W1_success"] for r in group), len(group)
        for rule, k in (("R5", 10), ("R6", 3)):
            ref_num = sum(r[f"P04_seed{seed}_best{k}_success"] for r in group for seed in seeds)
            ref_den = den * len(seeds)
            passed = num * ref_den >= ref_num * den
            primary = stratum in PRIMARY
            rules.append(dict(stratum=stratum, rule=rule, numerator=num, denominator=den,
                              rate=num / den, reference_numerator=ref_num, reference_denominator=ref_den,
                              reference_rate=ref_num / ref_den,
                              passed=passed if primary else None,
                              decision=("pass" if passed else "fail") if primary else "reported_only",
                              W0_numerator=sum(r["W0_success"] for r in group), W0_denominator=den,
                              W0_rate=sum(r["W0_success"] for r in group) / den,
                              W1_loss_evals_median=statistics.median(r["W1_loss_evals"] for r in group),
                              P04_loss_evals_median=statistics.median(r[f"P04_best{k}_loss_evals_median"] for r in group),
                              weak_abs_gt_10_count=sum(r["weak_abs_gt_10_count"] for r in group),
                              W1_sentinel_units=sum(r["W1_sentinel"] for r in group)))
    return rules


def write_table(path, rows):
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run(results_path=RESULTS, weak_path=DEFAULT_OUTPUT, p04_dir=P04, output=None):
    output = output or ROOT / "analysis/data/sideproject_residual_growth"
    targets = [output / n for n in ("q3_units.csv", "q3_rules_by_stratum.csv", "q3_run_metadata.json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Refusing to overwrite Q3 aggregation")
    payload = json.loads(weak_path.read_text(encoding="utf-8"))
    if payload["protocol_commit"] != "c81e7c6":
        raise ValueError("Wrong frozen protocol")
    # Verify the builder's full input provenance before accepting Julia results.
    for name, digest in payload["input_sha256"].items():
        if sha256(ROOT / name) != digest:
            raise ValueError(f"Weak-start input changed: {name}")
    results = read_jsonl(results_path)
    runner = ROOT / "studies/regression/sideproject_q3_weak_start.jl"
    for r in results:
        if r["weak_starts_sha256"] != sha256(weak_path) or r["runner_sha256"] != sha256(runner):
            raise ValueError("Julia result provenance mismatch")
        for name, digest in r["source_sha256"].items():
            if sha256(ROOT / name) != digest:
                raise ValueError(f"Julia source changed: {name}")
    references, paths = load_p04(p04_dir)
    reference_hashes = {p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p): sha256(p) for p in paths}
    for r in results:
        if r["protocol_commit"] != "c81e7c6" or r["p04_sha256"] != reference_hashes:
            raise ValueError("Julia P-04/protocol provenance mismatch")
    rows, rules = aggregate_units(payload["units"], results, references)
    inputs = paths + [results_path, weak_path, ROOT / "docs/sideproject_residual_growth_protocol_q3.md", runner, Path(__file__).resolve()]
    metadata = dict(protocol_commit="c81e7c6", units=len(rows), reference_cells=len(references),
                    reference_field="reference_starts", task_deviation="oracle_starts is a true subset in 101/180 real P-04 cells; frozen true-structure protocol takes precedence",
                    best_of_k_ties="Imported best_start: first equal-loss entry in stored start order",
                    loss_equality="abs(W1 - P04) <= 1e-12 * abs(P04); exact equality accepted including zero",
                    controls=dict(trajectory_units=60, random_start_units=list(CONTROLS), random_seed=7),
                    input_sha256={str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha256(p) for p in inputs})
    output.mkdir(parents=True, exist_ok=True)
    write_table(targets[0], rows)
    write_table(targets[1], rules)
    with targets[2].open("x", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RESULTS)
    parser.add_argument("--weak-starts", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--p04-dir", type=Path, default=P04)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "analysis/data/sideproject_residual_growth")
    args = parser.parse_args()
    print(json.dumps(run(args.input.resolve(), args.weak_starts.resolve(), args.p04_dir.resolve(), args.output_dir.resolve()), indent=2))


if __name__ == "__main__":
    main()
