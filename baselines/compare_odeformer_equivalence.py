import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ABS_TOL = 1e-8
REL_TOL = 1e-8
R2_FIELDS = [
    "reconstruction_r2_arithmetic_mean",
    "reconstruction_r2_variance_weighted",
    "generalization_r2_arithmetic_mean",
    "generalization_r2_variance_weighted",
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def key(record: dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(record["system_id"]),
        int(record["fit_initial_condition_set"]),
        int(record["generalization_initial_condition_set"]),
    )


def close(left: float, right: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=REL_TOL, abs_tol=ABS_TOL)


def compare(reference_path: Path, candidate_path: Path) -> dict[str, Any]:
    reference = {key(record): record for record in read_jsonl(reference_path)}
    candidate = {key(record): record for record in read_jsonl(candidate_path)}
    all_keys = sorted(set(reference) | set(candidate))
    findings = []
    for item in all_keys:
        left = reference.get(item)
        right = candidate.get(item)
        if left is None or right is None:
            findings.append({"cell": item, "field": "record_presence", "reference": left is not None, "candidate": right is not None})
            continue
        if left.get("status") != right.get("status"):
            findings.append({"cell": item, "field": "status", "reference": left.get("status"), "candidate": right.get("status")})
        if left.get("odeformer_model_canonical") != right.get("odeformer_model_canonical"):
            findings.append(
                {
                    "cell": item,
                    "field": "odeformer_model_canonical",
                    "reference": left.get("odeformer_model_canonical"),
                    "candidate": right.get("odeformer_model_canonical"),
                }
            )
        if left.get("odeformer_fitted_constants") != right.get("odeformer_fitted_constants"):
            left_constants = json.loads(str(left.get("odeformer_fitted_constants", "[]")))
            right_constants = json.loads(str(right.get("odeformer_fitted_constants", "[]")))
            if len(left_constants) != len(right_constants) or any(not close(a, b) for a, b in zip(left_constants, right_constants)):
                findings.append(
                    {
                        "cell": item,
                        "field": "odeformer_fitted_constants",
                        "reference": left_constants,
                        "candidate": right_constants,
                    }
                )
        for field in R2_FIELDS:
            if not close(float(left.get(field, 0.0)), float(right.get(field, 0.0))):
                findings.append({"cell": item, "field": field, "reference": left.get(field), "candidate": right.get(field)})
    return {
        "comparison_rule": {
            "canonical_expression": "exact string match",
            "constants": {"abs_tol": ABS_TOL, "rel_tol": REL_TOL},
            "r2": {"abs_tol": ABS_TOL, "rel_tol": REL_TOL},
        },
        "reference_record_count": len(reference),
        "candidate_record_count": len(candidate),
        "finding_count": len(findings),
        "findings": findings,
        "passed": len(findings) == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare WP-N21 ODEFormer reference and candidate records.")
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = compare(Path(args.reference), Path(args.candidate))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "finding_count": result["finding_count"]}, sort_keys=True))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    sys.exit(main())
