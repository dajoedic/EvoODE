"""Build frozen Q3 weak warm starts on the true Phase-C support."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis"))
from scripts.aggregate.run_sideproject_residual_growth import (
    WeakFit, phasec_basis, build_design, load_exact_supports,
    load_exported_trajectories, verify_basis_consistency, stratum_for, SUPPORT, EXPORT,
)

DEFAULT_OUTPUT = ROOT / "analysis/data/sideproject_residual_growth/q3_weak_starts.json"
PROTOCOL = Path("docs/sideproject_residual_growth_protocol_q3.md")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def flatten_parameters(active_idxs, coefficients):
    """Mirror build_rhs: equation order, then each stored active_idxs order.

    StructureSpec does not sort its input. Coefficient maps use 1-based indices.
    """
    if len(active_idxs) != len(coefficients):
        raise ValueError("Equation count mismatch")
    return [float(coefficients[eq][idx])
            for eq, indices in enumerate(active_idxs) for idx in indices]


def weak_coefficients(design, target, indices):
    """Reuse FA2 augmented QR and SVD solver, undoing column normalization."""
    indices = list(indices)
    fit = WeakFit(design, target)
    norms = np.linalg.norm(design, axis=0)
    scales = np.where(norms > 0, norms, 1.0)
    scaled_coef = np.linalg.lstsq(fit.A[:, indices], fit.b, rcond=None)[0]
    coef = scaled_coef / scales[indices]
    if not np.isfinite(coef).all():
        raise ValueError("Nonfinite weak coefficients")
    return coef, fit.sse(indices)


def build(repo=ROOT, output=DEFAULT_OUTPUT):
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    basis_name, systems = load_exact_supports(repo / SUPPORT)
    verify_basis_consistency(systems)
    trajectories = load_exported_trajectories(repo / EXPORT, [s["system_id"] for s in systems])
    with (repo / EXPORT / "trajectory_manifest.csv").open(encoding="utf-8", newline="") as handle:
        manifest = {(int(r["system_id"]), int(r["initial_condition_set"])): r for r in csv.DictReader(handle)}
    inputs = {SUPPORT, PROTOCOL, EXPORT / "trajectory_manifest.csv",
              Path("analysis/scripts/aggregate/run_sideproject_residual_growth.py"),
              Path("analysis/exploratory/term_relevance/term_relevance.py"),
              Path("src/basis/interface.jl"), Path("src/structure/interface.jl"),
              Path("analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py")}
    units = []
    for system in systems:
        sid, dim = int(system["system_id"]), int(system["dim"])
        terms = phasec_basis(dim)
        names = [t.name for t in terms]
        active = [sorted(map(int, eq)) for eq in system["support_idxs"]]
        for ic in (1, 2):
            trajectory = trajectories[sid, ic]
            equations, maps = [], []
            for eq, indices in enumerate(active):
                design, target, _ = build_design(trajectory.time, trajectory.state, eq, "weak", terms)
                coef, sse = weak_coefficients(design, target, [i - 1 for i in indices])
                maps.append(dict(zip(indices, coef)))
                equations.append(dict(equation_index=eq + 1, basis_indices=indices,
                                      term_names=[names[i - 1] for i in indices],
                                      coefficients=coef.tolist(), weak_sse=sse))
            export = manifest[sid, ic]
            for field in ("time_path", "state_path"):
                inputs.add(EXPORT / export[field])
            units.append(dict(unit_id=f"sys{sid:04d}_ic{ic}", system_id=sid,
                              initial_condition_set=ic, dim=dim, stratum=stratum_for(sid, dim),
                              active_idxs=active, equations=equations,
                              p0=flatten_parameters(active, maps),
                              trajectory_sha256=trajectory.sha256, export=export))
    if len(units) != 60 or len({u["unit_id"] for u in units}) != 60:
        raise ValueError("Expected exactly 60 unique units")
    payload = dict(protocol_commit="c81e7c6", basis_name=basis_name, units=units,
                   parameter_order="src/basis/interface.jl:24 build_rhs; equation then stored active_idxs order",
                   solver="FA2 WeakFit augmented QR, subset SVD lstsq, undo unit-column scaling",
                   input_sha256={p.as_posix(): sha256(repo / p) for p in sorted(inputs)})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)
        handle.write("\n")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payload = build(output=args.output.resolve())
    print(json.dumps(dict(units=len(payload["units"]), equations=sum(u["dim"] for u in payload["units"]),
                          output=str(args.output))))


if __name__ == "__main__":
    main()
