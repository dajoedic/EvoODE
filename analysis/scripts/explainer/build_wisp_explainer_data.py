"""Export the whitelisted Q5 evidence without reading any other campaign.

Missing observations are explicit, never reconstructed from a noise seed.
Original observations are read only at Q5-declared paths in the approved C-6
data-condition export, and only when their recorded SHA-256 matches.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis/scripts/aggregate"))
from build_sideproject_q4_paths import growth_path, weak_coefficients
from run_sideproject_residual_growth import build_design, phasec_basis
from run_phasec_noise_sindy_baselines import r2_scores

GRID = ROOT / "analysis/data/sideproject_residual_growth/q5_grid"
INPUTS = ROOT / "outputs/sideproject_q5_inputs"
CAMPAIGN = ROOT / "outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31"
EXPORT = ROOT / "outputs/phase_c_c6_data_conditions_5dd1df8"
COMPARISON = ROOT / "analysis/data/sideproject_residual_growth/q7_q5w_comparison.csv"
DEST = ROOT / "explainer/wisp/data"
DISPLAY_POINTS = 48
DISPLAY_DIGITS = 5
EVALUATION_TOL = 1e-6


def display_arrays(t, **arrays):
    """Presentation only: retain endpoints, at most 48 samples, five significant digits."""
    indices = np.unique(np.linspace(0, len(t)-1, min(DISPLAY_POINTS, len(t))).round().astype(int))
    def rounded(a):
        return np.vectorize(lambda v: float(format(v, f".{DISPLAY_DIGITS}g")))(np.asarray(a)[indices]).tolist()
    return dict(t=rounded(t), **{key: rounded(value) for key, value in arrays.items()})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_observations(cell, used):
    """Read only this Q5 cell's named files; never search for a substitute."""
    exp, arrays = cell["export"], []
    for key in ("time", "state"):
        path = (EXPORT / exp["cell_dir"].replace("\\", "/") /
                exp[f"{key}_path"].replace("\\", "/")).resolve()
        if not path.is_relative_to(EXPORT.resolve()):
            raise ValueError("Observation path escapes the approved export")
        if path.is_file():
            used.add(path)
        if digest(path) != exp[f"{key}_sha256"]:
            raise ValueError(f"{key} SHA-256 mismatch")
        arrays.append(np.fromfile(path, dtype="<f8").reshape(json.loads(exp[f"{key}_shape"])))
    return tuple(arrays)


def head_hash():
    """Read repository identity without invoking any Git operation."""
    git = ROOT / ".git"
    if git.is_file():
        git = (ROOT / git.read_text().strip().split(": ", 1)[1]).resolve()
    head = (git / "HEAD").read_text().strip()
    if not head.startswith("ref: "):
        return head
    ref = head[5:]
    if (git / ref).exists():
        return (git / ref).read_text().strip()
    for line in (git / "packed-refs").read_text().splitlines():
        if line.endswith(" " + ref):
            return line.split()[0]
    raise ValueError("Cannot resolve repository HEAD")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, ensure_ascii=False, sort_keys=True,
                                separators=(",", ":"), allow_nan=False) + "\n").encode("utf8"))


def rhs_for(system):
    expressions = system["substituted"][0]
    # The benchmark expressions are trusted repository inputs, not user code.
    codes = [compile(s.replace("^", "**"), "<benchmark equation>", "eval") for s in expressions]

    def rhs(t, x):
        scope = {"sin": np.sin, "cos": np.cos, "exp": np.exp, "sqrt": np.sqrt,
                 "pi": np.pi, **{f"x_{i}": v for i, v in enumerate(x)}}
        return [eval(c, {"__builtins__": {}}, scope) for c in codes]
    return rhs


def reference(t, x):
    terms = phasec_basis(1)
    a, b, _ = build_design(np.asarray(t), np.asarray(x).reshape(-1, 1), 0, "weak", terms)
    path, log = growth_path([a], [b])
    for item in path:
        coef, sse = weak_coefficients(a, b, item["support"][0])
        item.update(coefficients=coef.tolist(), sse=sse)
    return dict(path=path, log=log, design=a.tolist(), target=b.tolist())


def build(destination=DEST):
    used = set()

    def read(path):
        used.add(path)
        return json.loads(path.read_text(encoding="utf8"))

    def rows(path):
        used.add(path)
        with path.open(encoding="utf8", newline="") as f:
            return list(csv.DictReader(f))

    rates = rows(GRID / "q5_rates.csv")  # Strings preserve every CSV value exactly.
    units = rows(GRID / "q5_units.csv")
    metadata = read(GRID / "q5_run_metadata.json")
    payload = read(INPUTS / "q5_grid_paths.json")
    systems = {s["id"]: s for s in read(ROOT / "benchmarks/data/strogatz_extended.json")}
    bycell = {c["cell_id"]: c for c in payload["cells"]}
    observation_cache, observation_errors = {}, {}
    def observations(cell):
        cid = cell["cell_id"]
        if cid in observation_cache:
            return observation_cache[cid]
        try:
            observation_cache[cid] = read_observations(cell, used)
        except (OSError, ValueError) as exc:
            observation_errors[cid] = str(exc)
            observation_cache[cid] = None
        return observation_cache[cid]

    removal = next((c for c in payload["cells"] if c["dim"] == 1 and
                    any(p["origin"] == "removal" for p in c["candidates"])), None)
    first = "sys0003_ic1_s0.03_r0_n1"
    ids = [first, "sys0001_ic1_s0.01_r0_n1", "sys0001_ic1_s0_r0_n1"]
    references = []
    for cid in ids[:3]:
        c = bycell[cid]
        obs = observations(c)
        entry = dict(cell_id=cid, sigma=c["sigma"], rho=c["rho"],
                     stored_candidates=c["candidates"], available=obs is not None)
        if obs is not None:
            t, x = obs
            entry.update(t=t.tolist(), x=x[:, 0].tolist(), **reference(t, x[:, 0]))
            for expected, actual in zip(c["candidates"], entry["path"], strict=True):
                if expected["active_idxs"] != [[i + 1 for i in actual["support"][0]]]:
                    raise AssertionError(f"Stored Q5 path differs: {cid}")
                np.testing.assert_allclose(expected["equations"][0]["coefficients"],
                                           actual["coefficients"], rtol=1e-8, atol=0)
        references.append(entry)

    # Illustrations use the benchmark equation and IC only, never its stored solutions.
    illustrations = []
    for sid in (3, 27):
        s = systems[sid]
        t = np.linspace(0, 10, 160)
        result = solve_ivp(rhs_for(s), (t[0], t[-1]), s["init"][0], t_eval=t,
                           method="DOP853", rtol=1e-11, atol=1e-12)
        if not result.success or result.y.shape[1] != len(t):
            raise ValueError(f"Illustration integration failed: {sid}")
        illustrations.append(dict(system_id=sid, t=t.tolist(), x=result.y.T.tolist(),
                                  equation=s["substituted"][0], constants=s["consts"][0],
                                  initial=s["init"][0], description=s["eq_description"]))
    demo = illustrations[0]
    z = np.random.default_rng(20261102).normal(size=len(demo["t"]))
    demo["noise_draws"] = z.tolist()
    demo["checks"] = []
    for sigma in (0.01, 0.03, 0.05):
        x = np.asarray(demo["x"])[:, 0] * (1 + sigma*z)
        demo["checks"].append(dict(sigma=sigma, **reference(demo["t"], x)))

    real = bycell[first]
    observed_demo = observations(real)
    clean_demo = observations(bycell[f"{real['unit_id']}_s0_r0_n1"])
    teaching = None
    if observed_demo is not None and clean_demo is not None:
        t, x = observed_demo
        clean_t, clean_x = clean_demo
        if not np.array_equal(t, clean_t):
            raise ValueError("Teaching cell and clean control grids differ")
        teaching = dict(cell_id=first, sigma=real["sigma"], t=t.tolist(),
                        truth=clean_x[:, 0].tolist(), observed=x[:, 0].tolist(),
                        noise_draws=((x[:, 0]/clean_x[:, 0]-1)/real["sigma"]).tolist())

    details, verification = [], []
    for row in units:
        if row["size_rule"] != "c":
            continue
        c = bycell[row["cell_id"]]
        s = systems[c["system_id"]]
        entry = dict(row=row, system_id=c["system_id"], description=s["eq_description"],
                     truth=s["substituted"][0], exact=True, terms=[t.name for t in phasec_basis(c["dim"])],
                     observed=None, curves=None, unavailable="Whitelisted observation and clean evaluation binaries are absent.")
        obs = observations(c)
        if obs is not None:
            entry["observed"] = dict(t=obs[0].tolist(), x=obs[1].tolist())
        clean = observations(bycell[f"{c['unit_id']}_s0_r0_n1"])
        target_id = f"sys{c['system_id']:04d}_ic{3-c['initial_condition_set']}_s0_r0_n1"
        target = observations(bycell[target_id])
        check = dict(cell_id=c["cell_id"], passed=False, status="withheld", max_r2_error=None)
        if obs is None or clean is None or target is None:
            check["reason"] = "Missing or hash-mismatched observation/clean target"
            entry["unavailable"] = check["reason"]
        else:
            active = json.loads(row["active_idxs"])
            params = iter(json.loads(row["params"]))
            terms = phasec_basis(c["dim"])
            equations = [[(terms[i-1], float(np.clip(next(params), -10, 10))) for i in eq] for eq in active]

            def rhs(ti, x):
                rhs.calls += 1
                if rhs.calls > 50000:
                    raise RuntimeError("Verification exceeded 50000 RHS evaluations")
                vals = []
                for eq in equations:
                    value = 0.
                    for term, coef in eq:
                        v = (math.sin(x[term.var]) if term.kind == "sin" else
                             math.cos(x[term.var]) if term.kind == "cos" else
                             math.prod(xi**power for xi, power in zip(x, term.powers) if power))
                        value += coef*v
                    vals.append(value)
                return vals
            def integrate(t, truth, tolerance):
                rhs.calls = 0
                try:
                    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                        sol = solve_ivp(rhs, (t[0], t[-1]), truth[0], t_eval=t,
                                        method="RK45", rtol=tolerance, atol=tolerance)
                    if sol.success and sol.y.shape[1] == len(t):
                        return sol.y.T, None
                    return None, sol.message
                except (ValueError, OverflowError, FloatingPointError, RuntimeError) as exc:
                    return None, str(exc)

            errors, scores, curves, missing, integration_failures = [], {}, {}, [], {}
            for kind, (t, truth) in (("reconstruction", clean), ("generalization", target)):
                prediction, failure = integrate(t, truth, EVALUATION_TOL)
                if failure:
                    integration_failures[kind] = failure
                ar, vw, _ = r2_scores(truth, prediction)
                scores[kind] = {}
                for weight, value in (("arithmetic", ar), ("variance_weighted", vw)):
                    field = f"{kind}_r2_{weight}"
                    scores[kind][weight] = float(value) if np.isfinite(value) else None
                    if row[field] == "":
                        missing.append(field)
                    else:
                        errors.append(abs(value-float(row[field])))
                if prediction is not None:
                    curves[kind] = dict(t=t.tolist(), truth=truth.tolist(), model=prediction.tolist())
            finite = bool(np.isfinite(errors).all())
            passed = bool(not missing and finite and max(errors, default=float("inf")) <= 1e-6
                          and len(curves) == 2)
            check.update(passed=passed, status="withheld" if missing else ("passed" if passed else "failed"),
                         max_r2_error=float(max(errors)) if errors and finite else None, scores=scores,
                         integration_failures=integration_failures,
                         reason=("Missing stored scores: " + ", ".join(missing)) if missing else
                         (None if passed else "R² mismatch or nonfinite integration"))
            if passed:
                # Verification above always uses full-resolution float64 arrays.
                compact = {kind: display_arrays(bundle["t"], truth=bundle["truth"], model=bundle["model"])
                           for kind, bundle in curves.items()}
                entry["curves"] = {**compact["reconstruction"], "generalization": compact["generalization"]}
                entry["unavailable"] = None
            else:
                entry["unavailable"] = check["reason"] + "; curve withheld."
            if check["status"] == "failed":
                tightened, changes, tight_failures = {}, [], {}
                for kind, (t, truth) in (("reconstruction", clean), ("generalization", target)):
                    prediction, failure = integrate(t, truth, EVALUATION_TOL/10)
                    ar, vw, _ = r2_scores(truth, prediction)
                    tightened[kind] = {}
                    if failure:
                        tight_failures[kind] = failure
                    for weight, value in (("arithmetic", ar), ("variance_weighted", vw)):
                        value = float(value) if np.isfinite(value) else None
                        tightened[kind][weight] = value
                        original = scores[kind][weight]
                        changes.append(abs(value-original) if value is not None and original is not None else float("inf"))
                movement = max(changes)
                check.update(tightened_scores=tightened, tightened_integration_failures=tight_failures,
                             max_r2_movement=movement if np.isfinite(movement) else None,
                             classification="integrator sensitivity" if movement > 1e-6 else "stable disagreement")
        if obs is not None and c["cell_id"] not in ids:
            entry["observed"] = display_arrays(obs[0], x=obs[1])
        verification.append(check)
        details.append(entry)
        if len(details) % 100 == 0:
            print(f"Re-simulation checked {len(details)} cells", flush=True)

    identity = head_hash()
    provenance = dict(protocol="Q5", protocol_commit=metadata["protocol_commit"], git_hash=identity,
                      campaign=CAMPAIGN.name, status="interim", structure_population="exact systems only",
                      baseline_reference_sha256=metadata["reference_sha256"],
                      baseline_source="outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv",
                      baseline_note="WP-N47: pysindy SINDy, fixed-threshold Weak-SINDy, and E-SINDy; configurations are preserved verbatim.")
    comparison = dict(status="pending", source=COMPARISON.relative_to(ROOT).as_posix(), rates=[])
    # This single future aggregation is the only Q7 read authorized here.
    if COMPARISON.is_file():
        comparison.update(status="available", rates=rows(COMPARISON))
    result = dict(schema_version=2, provenance=provenance, rates=rates, cells=details, primary_method="Q5",
                  score_threshold=0.9, exclude_clean_controls=True, comparison=comparison,
                  method_labels={"Q5": "WISP", "sindy": "SINDy", "weak_sindy": "Weak-SINDy (pysindy, fixed threshold)",
                                 "e_sindy": "E-SINDy"}, axes=[],
                  selected_configuration_methods=["sindy", "weak_sindy", "e_sindy"])
    live = dict(references=references, illustrations=illustrations, teaching=teaching,
                catalogues=[dict(dim=d, terms=[t.name for t in phasec_basis(d)],
                                 count=len(phasec_basis(d)), combinations=str(2**(d*len(phasec_basis(d))))) for d in range(1, 5)],
                windows=[1, 2, 4, 8, 16], cap=6, backward_fraction=0.5, sse_stop=1e-14)
    events = []
    if removal is not None:
        before = set()
        for p in removal["candidates"]:
            after = set(p["active_idxs"][0])
            if p["origin"] == "removal":
                events.append(dict(step=p["step"], removed=sorted(before-after), added=sorted(after-before)))
            before = after
    manifest = dict(git_hash=identity, inputs={p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(used)},
                    foba_cell=None if removal is None else removal["cell_id"],
                    foba_events=events,
                    foba_states=[] if removal is None else [p for p in removal["candidates"] if p["origin"] == "removal"],
                    reference_cells=[r["cell_id"] for r in references],
                    missing_reference_cells=[r["cell_id"] for r in references if not r["available"]],
                    drilldown_cells=len(details), observations_available=sum(e["observed"] is not None for e in details),
                    observation_errors=observation_errors,
                    display=dict(max_points=DISPLAY_POINTS, significant_digits=DISPLAY_DIGITS, full_observation_cells=ids),
                    resimulation=dict(solver="RK45 (Dormand-Prince 5(4)), substitute for Julia Tsit5",
                                      rtol=EVALUATION_TOL, atol=EVALUATION_TOL, pass_tolerance=1e-6,
                                      tightened_tolerance=EVALUATION_TOL/10,
                                      attempted=len(verification), passed=sum(v["passed"] for v in verification),
                                      failed=sum(v["status"] == "failed" for v in verification),
                                      unavailable=sum(v["status"] == "withheld" for v in verification), checks=verification),
                    binary_files_found=sum(p.suffix == ".bin" for p in used))
    for name, data in (("results", result), ("live", live), ("manifest", manifest)):
        write_json(destination / f"{name}.json", data)
    print(json.dumps({"rates": len(rates), "cells": len(details), "missing_references": len(manifest["missing_reference_cells"]),
                      "resimulation_attempted": len(verification), "resimulation_passed": manifest["resimulation"]["passed"]}))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEST)
    args = parser.parse_args()
    build(args.output)
