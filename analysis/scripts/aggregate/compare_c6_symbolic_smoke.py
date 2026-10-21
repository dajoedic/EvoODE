"""Compare declared platform controls against local records, emitting PASS/FAIL."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from baselines import harness

R2_FIELDS = [f"{regime}_r2_{kind}" for regime in ("reconstruction", "generalization")
             for kind in ("arithmetic_mean", "variance_weighted")]
# The existing laptop vs Orion clean reference differs by 1.858e-12 in generalization R2.
ODE_R2_ATOL = 2e-12


def records_at(path):
    path = Path(path)
    files = [path] if path.is_file() else sorted(path.glob("shard_*/records.jsonl"))
    if not files and path.is_dir() and (path / "records.jsonl").is_file():
        files = [path / "records.jsonl"]
    if not files:
        raise ValueError(f"Missing reference/candidate records: {path}")
    return [json.loads(line) for file in files for line in file.read_text(encoding="utf-8").splitlines() if line.strip()]


def coefficient_map(record):
    import sympy as sp
    dim = int(record["dimension"])
    expression = record["pysr_model_canonical"]
    # Reuse the harness parser and expansion, including its variable conventions.
    maps = []
    for part in harness.pysr_expression_parts(expression, dim):
        expanded = sp.expand(harness.parse_pysr_expr(part, dim))
        maps.append({str(body): float(coefficient) for body, coefficient in expanded.as_coefficients_dict().items()
                     if float(coefficient) != 0.0})
    return maps


def compare_records(reference, candidate, method):
    findings = []
    def exact(field, left, right):
        if left != right:
            findings.append(dict(field=field, reference=left, candidate=right))
    for side, record in (("reference", reference), ("candidate", candidate)):
        if record.get("status") != "success":
            findings.append(dict(field="status", side=side, value=record.get("status")))
    try:
        for field in ("time_sha256", "fit_state_sha256"):
            exact(field, reference[field], candidate[field])
        if method == "odeformer":
            exact("odeformer_model_canonical", reference["odeformer_model_canonical"], candidate["odeformer_model_canonical"])
            for field in R2_FIELDS:
                left, right = float(reference[field]), float(candidate[field])
                if not (math.isfinite(left) and math.isfinite(right) and math.isclose(left, right, rel_tol=0, abs_tol=ODE_R2_ATOL)):
                    findings.append(dict(field=field, reference=left, candidate=right, abs_tol=ODE_R2_ATOL))
        else:
            exact("pysr_api", reference["pysr_api"], candidate["pysr_api"])
            if candidate["pysr_api"] != "legacy_0x":
                findings.append(dict(field="pysr_api", expected="legacy_0x"))
            left, right = coefficient_map(reference), coefficient_map(candidate)
            exact("canonical_support", [sorted(eq) for eq in left], [sorted(eq) for eq in right])
            if len(left) == len(right):
                for i, (lhs, rhs) in enumerate(zip(left, right)):
                    for term in lhs.keys() & rhs.keys():
                        a, b = lhs[term], rhs[term]
                        if not (math.isfinite(a) and math.isfinite(b) and math.isclose(a, b, rel_tol=0, abs_tol=1e-6)):
                            findings.append(dict(field="coefficient", equation=i, term=term, reference=a, candidate=b, abs_tol=1e-6))
    except (KeyError, TypeError, ValueError) as exc:
        findings.append(dict(field="required_field_or_expression", error=str(exc)))
    return dict(result="FAIL" if findings else "PASS", findings=findings,
                fields=(["status", "time_sha256", "fit_state_sha256", "odeformer_model_canonical", *R2_FIELDS]
                        if method == "odeformer" else ["status", "time_sha256", "fit_state_sha256", "pysr_api", "canonical_support", "coefficients"]))


def select(records, control, variant, candidate=False):
    sigma, rho = {"odeformer-clean": (0, 0), "odeformer-stage": (0.05, 0.5), "pysr": (0.01, 0)}[control]
    result = []
    for record in records:
        if int(record.get("system_id", -1)) != 1 or int(record.get("source_initial_condition_set", record.get("fit_initial_condition_set", -1))) != 1:
            continue
        if int(record.get("target_initial_condition_set", record.get("generalization_initial_condition_set", -1))) != 2:
            continue
        method = "pysr" if control == "pysr" else "odeformer"
        if record.get("method") != (variant if method == "pysr" else "odeformer"):
            continue
        if method == "odeformer" and record.get("odeformer_config_id") != "beam10_noopt":
            continue
        if method == "pysr" and int(record.get("pysr_seed", -1)) != 1:
            continue
        repetition = record.get("odeformer_noise_repetition", record.get("odeformer_grid_repetition", 1))
        if method == "odeformer" and int(repetition) != 1:
            continue
        # Clean grid references predate the noise schema; clean laptop records use realization 0.
        if control != "odeformer-clean" or candidate:
            if int(record.get("noise_realization", -1)) != 1:
                continue
        if not math.isclose(float(record.get("noise_sigma", 0)), sigma, rel_tol=0, abs_tol=1e-14):
            continue
        if not math.isclose(float(record.get("subsample_rho", 0)), rho, rel_tol=0, abs_tol=1e-14):
            continue
        result.append(record)
    return result


def compare_control(reference_records, candidate_records, control):
    variants = ["pysr", "pysr_poly"] if control == "pysr" else ["beam10_noopt"]
    results = []
    for variant in variants:
        left = select(reference_records, control, variant)
        right = select(candidate_records, control, variant, candidate=True)
        if len(left) != 1 or len(right) != 1:
            result = dict(result="FAIL", findings=[dict(field="record_presence", reference=len(left), candidate=len(right))])
        else:
            result = compare_records(left[0], right[0], "pysr" if control == "pysr" else "odeformer")
        results.append(dict(control=control, variant=variant, **result))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", required=True, choices=["odeformer-clean", "odeformer-stage", "pysr"])
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--reference", required=True, action="append", type=Path)
    args = parser.parse_args()
    results = []
    for path in args.reference:
        try:
            results.extend(dict(reference=str(path), **r) for r in compare_control(records_at(path), records_at(args.candidate), args.control))
        except (OSError, ValueError) as exc:
            results.append(dict(reference=str(path), result="FAIL", findings=[dict(field="record_presence", error=str(exc))]))
    print(json.dumps(results, indent=2))
    return 0 if all(r["result"] == "PASS" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
