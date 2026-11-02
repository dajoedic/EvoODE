"""Compare the shipped JS with Python; missing Q5 inputs are a failing gate."""
import argparse
import json
import subprocess
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def compare(case, actual):
    expected = case["path"]
    assert len(actual["steps"]) == len(expected), "Path length mismatch"
    largest = 0.
    for step, py, log in zip(actual["steps"], expected, case["log"], strict=True):
        assert step["support"] == py["support"][0], "Support mismatch"
        assert step["addition"] == log["addition"]["basis_index"] - 1, "Addition mismatch"
        removed = [b["removed"]["basis_index"]-1 for b in log["backward_checks"] if b["removed"]]
        assert step["removed"] == removed, "Removal mismatch"
        a, b = np.asarray(step["coefficients"]), np.asarray(py["coefficients"])
        np.testing.assert_allclose(a, b, rtol=1e-8, atol=0)
        if len(a):
            largest = max(largest, float(np.max(np.abs(a-b)/np.maximum(np.abs(b), np.finfo(float).tiny))))
    np.testing.assert_allclose(actual["design"]["A"], case["design"], rtol=2e-14, atol=1e-14)
    np.testing.assert_allclose(actual["design"]["b"], case["target"], rtol=0, atol=0)
    return largest


def main(illustrations_only=False):
    live = json.loads((ROOT / "explainer/wisp/data/live.json").read_text(encoding="utf8"))
    missing = [r["cell_id"] for r in live["references"] if not r["available"]]
    demo = live["illustrations"][0]
    cases = []
    for check in demo["checks"]:
        x = [row[0]*(1+check["sigma"]*z) for row, z in zip(demo["x"], demo["noise_draws"])]
        cases.append({**check, "t": demo["t"], "x": x, "label": f"illustration sigma={check['sigma']}"})
    if not illustrations_only:
        cases += [{**r, "label": r["cell_id"]} for r in live["references"] if r["available"]]
    script = "const fs=require('fs'),W=require(process.argv[1]);const d=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(d.map(c=>W.path(c.t,c.x))));"
    run = subprocess.run(["node", "-e", script, str(ROOT / "explainer/wisp/src/compute.js")],
                         input=json.dumps(cases), capture_output=True, text=True, check=True, timeout=120)
    results = json.loads(run.stdout)
    for case, actual in zip(cases, results, strict=True):
        error = compare(case, actual)
        print(f"PASS {case['label']}: {len(actual['steps'])} steps; max relative coefficient error {error:.3g}")
    if missing and not illustrations_only:
        print("BLOCKED: Q5 observation bytes absent for " + ", ".join(missing))
        return 1
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--illustrations-only", action="store_true", help="Development check; does not satisfy the Q5 gate")
    raise SystemExit(main(parser.parse_args().illustrations_only))
