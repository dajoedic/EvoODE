"""Frozen WP-FA2 weak-space subset identification and residual guidance."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "analysis"))
from exploratory.term_relevance.term_relevance import (
    phasec_basis, evaluate_basis, build_design, load_exported_trajectories,
    verify_basis_consistency, load_exact_supports,
)
from scripts.aggregate.aggregate_c1_structure_inventory import classify, stratum_for, git_head, STRATA

INVENTORY = Path("analysis/data/paper1_phaseC_v1/c1_structure_inventory/equations.csv")
SUPPORT = Path("studies/regression/phase_c_support.json")
EXPORT = Path("outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export")
PROTOCOL = Path("docs/sideproject_residual_growth_protocol.md")
DEFAULT_OUTPUT = Path("analysis/data/sideproject_residual_growth")
PRIMARY = frozenset(STRATA[:3])


class WeakFit:
    """Orthogonally compress [unit-norm A, b], preserving every residual norm.

    All subset fits use SVD least squares on the compressed design, never a
    Gram matrix. Keeping the augmented target row avoids subtracting nearly
    equal squared norms when the fit is very accurate.
    """

    def __init__(self, design, target):
        design = np.asarray(design, dtype=float)
        target = np.asarray(target, dtype=float)
        if not np.isfinite(design).all() or not np.isfinite(target).all():
            raise ValueError("Nonfinite weak design or target")
        norms = np.linalg.norm(design, axis=0)
        scaled = design / np.where(norms > 0, norms, 1.0)
        reduced = np.linalg.qr(np.column_stack((scaled, target)), mode="r")
        self.A, self.b = reduced[:, :-1], reduced[:, -1]
        self.p = design.shape[1]
        self.b_norm2 = float(target @ target)
        self.condition_number = float(np.linalg.cond(self.A))
        self.cache = {}

    def residual(self, support):
        support = tuple(sorted(support))
        if not support:
            return self.b.copy()
        matrix = self.A[:, support]
        coef = np.linalg.lstsq(matrix, self.b, rcond=None)[0]
        return self.b - matrix @ coef

    def sse(self, support):
        key = tuple(sorted(support))
        if key not in self.cache:
            residual = self.residual(key)
            self.cache[key] = float(residual @ residual)
        return self.cache[key]

    def additions(self, support, method="g"):
        support = set(support)
        candidates = sorted(set(range(self.p)) - support)
        if method == "g":
            return sorted(candidates, key=lambda j: (self.sse(support | {j}), j))
        if method != "omp":
            raise ValueError(method)
        residual = self.residual(support)
        norms = np.linalg.norm(self.A, axis=0)
        scores = np.abs(self.A.T @ residual) / np.where(norms > 0, norms, 1.0)
        return sorted(candidates, key=lambda j: (-scores[j], j))

    def forward(self, initial, steps, method="g"):
        current, added = set(initial), []
        for _ in range(steps):
            order = self.additions(current, method)
            if not order:
                raise ValueError("Forward step count exceeds available candidates")
            added.append(order[0])
            current.add(order[0])
        return added, current

    def backward(self, initial, size):
        current = set(initial)
        while len(current) > size:
            chosen = min(current, key=lambda j: (self.sse(current - {j}), j))
            current.remove(chosen)
        return current


def q1_metrics(fit, truth):
    truth = frozenset(truth)
    truth_sse = fit.sse(truth)
    rank, count, best = 1, 0, None
    for subset in itertools.combinations(range(fit.p), len(truth)):
        count += 1
        if frozenset(subset) == truth:
            continue
        sse = fit.sse(subset)
        # No data-dependent tolerance: exact numeric ties count against truth.
        rank += int(sse <= truth_sse)
        if best is None or (sse, subset) < best:
            best = (sse, subset)
    if count != math.comb(fit.p, len(truth)):
        raise ValueError("Incomplete Q1 enumeration")
    other_sse = best[0] if best else math.nan
    with np.errstate(divide="ignore", invalid="ignore"):
        margin = float(np.log10(np.divide(other_sse, truth_sse)))
    return dict(k_star=len(truth), subset_count=count, q1_rank=rank,
                truth_sse=truth_sse, best_other_sse=other_sse,
                best_other_indices=list(best[1]) if best else [], q1b=margin,
                b_norm2=fit.b_norm2, condition_number=fit.condition_number)


def q2_metrics(fit, truth, initial, f0=None):
    truth, initial = set(truth), set(initial)
    missing, extra = truth - initial, initial - truth
    m = len(missing)
    result = dict(m=m, random_addition_probability=1.0 / math.comb(fit.p - len(initial), m))
    for method in ("g", "omp"):
        first = fit.additions(initial, method)
        added, current = fit.forward(initial, m, method)
        final = fit.backward(current, len(truth))
        result.update({method + "_added_indices": added,
                       method + "_q2a": missing <= set(added),
                       method + "_first_missing_ranks": {str(j): first.index(j) + 1 for j in sorted(missing)},
                       method + "_final_indices": sorted(final),
                       method + "_q2b": final == truth})
    if f0 is None:
        _, f0 = fit.forward([], len(truth))
    first = fit.additions(initial)
    sse0 = fit.sse(initial)
    reduction = sse0 - fit.sse(initial | {first[0]}) if first else 0.0
    result.update(f0_indices=sorted(f0), f0_exact=set(f0) == truth,
                  sse0=sse0, best_addition_reduction=reduction,
                  rho=reduction / fit.b_norm2 if fit.b_norm2 else math.nan,
                  rho_prime=reduction / sse0 if sse0 else math.nan)
    return result


def auc_counts(positive, negative):
    """Return pairwise wins (ties are half wins), pairs, and AUC."""
    positive, negative = list(positive), list(negative)
    pairs = len(positive) * len(negative)
    if not all(math.isfinite(x) for x in positive + negative):
        return math.nan, pairs, math.nan
    wins = sum(float(p > n) + 0.5 * float(p == n) for p in positive for n in negative)
    return wins, pairs, wins / pairs if pairs else math.nan


def load_starts(repo, supports):
    systems = {int(s["system_id"]): s for s in supports}
    rows = pd.read_csv(repo / INVENTORY).to_dict("records")
    groups, identities = {}, set()
    for row in rows:
        sid, ic, eq = (int(row[k]) for k in ("system_id", "initial_condition_set", "equation_index"))
        kind = row["kind"]
        system = systems[sid]
        names = [term.name for term in phasec_basis(int(system["dim"]))]
        truth = set(system["support_terms"][eq - 1])
        missing, extra = set(json.loads(row["missing_terms"])), set(json.loads(row["extra_terms"]))
        if not missing <= truth or extra & truth or not (missing | extra) <= set(names):
            raise ValueError("Invalid inventory term differences")
        initial = (truth - missing) | extra
        expected = classify(truth, initial)
        if any(row[k] != expected[k] for k in ("class", "n_true", "missing", "extra", "needs_add", "needs_remove")):
            raise ValueError("Inventory classification mismatch")
        stratum = stratum_for(sid, int(system["dim"]))
        if row["stratum"] != stratum or int(row["system_dim"]) != int(system["dim"]) or kind not in ("pruned", "raw") or ic not in (1, 2):
            raise ValueError("Invalid inventory identity/stratum")
        if kind == "pruned" and row["class"] == "exact" and initial != truth:
            raise ValueError("Pruned exact S0 differs from truth")
        identity = (row["run_id"], eq, kind)
        if identity in identities:
            raise ValueError("Duplicate inventory cell equation")
        identities.add(identity)
        indices = tuple(i for i, name in enumerate(names) if name in initial)
        key = sid, ic, eq, kind, indices
        if key not in groups:
            groups[key] = dict(system_id=sid, initial_condition_set=ic, equation_index=eq,
                               stratum=stratum, kind=kind, wp_fa1_class=row["class"],
                               cells_collapsed=0, s0=list(indices),
                               missing_terms=[n for n in names if n in missing],
                               extra_terms=[n for n in names if n in extra])
        groups[key]["cells_collapsed"] += 1
    if len(rows) != 708 or len({r["run_id"] for r in rows}) != 180:
        raise ValueError("Expected 708 inventory equations from 180 cells")
    return list(groups.values())


def summarize(q1, q2, by_system=False):
    rows = []
    groups = [(stratum, None) for stratum in STRATA]
    if by_system:
        groups = sorted({(r["stratum"], r["system_id"]) for r in q1})
    for stratum, sid in groups:
        one = [r for r in q1 if r["stratum"] == stratum and (sid is None or r["system_id"] == sid)]
        for kind in ("pruned", "raw"):
            two = [r for r in q2 if r["stratum"] == stratum and r["kind"] == kind and (sid is None or r["system_id"] == sid)]
            need = [r for r in two if r["m"] > 0]
            negative = [r for r in two if r["wp_fa1_class"] in ("exact", "superset")]
            wins, pairs, auc = auc_counts([r["rho"] for r in need], [r["rho"] for r in negative])
            wins2, pairs2, auc2 = auc_counts([r["rho_prime"] for r in need], [r["rho_prime"] for r in negative])
            specs = [("R1", sum(r["q1_rank"] == 1 for r in one), len(one), .8),
                     ("R2", sum(r["g_q2a"] for r in need), len(need), .7),
                     ("R3", sum(r["g_q2b"] for r in need), len(need), sum(r["f0_exact"] for r in need)),
                     ("R4", wins, pairs, .8)]
            for rule, numerator, denominator, threshold in specs:
                value = numerator / denominator if denominator else math.nan
                if rule == "R3":
                    value = numerator
                passed = bool(math.isfinite(value) and value >= threshold)
                row = dict(stratum=stratum, kind=kind, rule=rule, numerator=numerator,
                           denominator=denominator, value=value, threshold=threshold,
                           passed=passed, decision=("pass" if passed else "fail") if stratum in PRIMARY else "reported_only",
                           q1_units=len(one), q2_units=len(two), addition_units=len(need),
                           negative_units=len(negative), f0_exact_count=sum(r["f0_exact"] for r in need),
                           omp_q2a_count=sum(r["omp_q2a"] for r in need),
                           omp_q2b_count=sum(r["omp_q2b"] for r in need),
                           rho_prime_auc_numerator=wins2, rho_prime_auc_denominator=pairs2,
                           rho_prime_auc=auc2,
                           condition_number_min=min(r["condition_number"] for r in one),
                           condition_number_max=max(r["condition_number"] for r in one))
                if sid is not None:
                    row["system_id"] = sid
                rows.append(row)
    return pd.DataFrame(rows)


def names_for(indices, names):
    return [names[i] for i in indices]


def run(repo, output):
    started = time.perf_counter()
    targets = [output / n for n in ("q1_units.csv", "q2_units.csv", "rules_by_stratum.csv", "by_system.csv", "run_metadata.json")]
    if any(p.exists() for p in targets):
        raise FileExistsError("Refusing to overwrite existing results")
    _, systems = load_exact_supports(repo / SUPPORT)
    verify_basis_consistency(systems)
    starts = load_starts(repo, systems)
    trajectories = load_exported_trajectories(repo / EXPORT, [int(s["system_id"]) for s in systems])
    q1, q2 = [], []
    starts_by_unit = {}
    for row in starts:
        key = tuple(row[k] for k in ("system_id", "initial_condition_set", "equation_index"))
        starts_by_unit.setdefault(key, []).append(row)
    total_subsets = sum(2 * sum(math.comb(len(phasec_basis(int(s["dim"]))), len(t)) for t in s["support_terms"]) for s in systems)
    completed = 0
    for system in systems:
        sid, dim = int(system["system_id"]), int(system["dim"])
        terms = phasec_basis(dim)
        names = [term.name for term in terms]
        for ic in (1, 2):
            trajectory = trajectories[sid, ic]
            for eq, truth_names in enumerate(system["support_terms"], 1):
                design, target, _ = build_design(trajectory.time, trajectory.state, eq - 1, "weak", terms)
                fit = WeakFit(design, target)
                truth = {names.index(n) for n in truth_names}
                base = dict(system_id=sid, initial_condition_set=ic, equation_index=eq,
                            stratum=stratum_for(sid, dim))
                metrics = q1_metrics(fit, truth)
                metrics["best_other_terms"] = names_for(metrics.pop("best_other_indices"), names)
                q1.append({**base, **metrics})
                _, f0 = fit.forward([], len(truth))
                for row in starts_by_unit.pop((sid, ic, eq), []):
                    result = q2_metrics(fit, truth, row["s0"], f0)
                    for method in ("g", "omp"):
                        result[method + "_added_terms"] = names_for(result.pop(method + "_added_indices"), names)
                        result[method + "_final_terms"] = names_for(result.pop(method + "_final_indices"), names)
                        ranks = result[method + "_first_missing_ranks"]
                        result[method + "_first_missing_ranks"] = {names[int(j)]: rank for j, rank in ranks.items()}
                    result["f0_terms"] = names_for(result.pop("f0_indices"), names)
                    q2.append({**row, "s0": names_for(row["s0"], names), **result})
                completed += metrics["subset_count"]
                elapsed = time.perf_counter() - started
                estimate = elapsed * total_subsets / completed
                print(json.dumps(dict(unit=len(q1), total_units=118, elapsed_seconds=elapsed, estimated_seconds=estimate)), flush=True)
                if elapsed > 15 * 60 or estimate > 30 * 60:
                    raise RuntimeError("Runtime control: exceeds 15 minutes elapsed or 30 minutes estimated")
    if len(q1) != 118 or starts_by_unit:
        raise ValueError("Q1 count / Q2 identity control failed")
    tables = {"q1_units.csv": pd.DataFrame(q1), "q2_units.csv": pd.DataFrame(q2),
              "rules_by_stratum.csv": summarize(q1, q2), "by_system.csv": summarize(q1, q2, True)}
    inputs = [SUPPORT, INVENTORY, PROTOCOL, Path("analysis/exploratory/term_relevance/term_relevance.py"), EXPORT / "trajectory_manifest.csv"]
    with (repo / EXPORT / "trajectory_manifest.csv").open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if int(row["system_id"]) in {int(s["system_id"]) for s in systems}:
                inputs.extend([EXPORT / row["time_path"], EXPORT / row["state_path"]])
    metadata = dict(protocol_commit="e61f48f", git_head=git_head(repo),
                    git_head_source="Read-only HEAD/ref files; no Git command",
                    input_sha256={p.as_posix(): hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in sorted(set(inputs))},
                    runtime_seconds=time.perf_counter() - started,
                    controls=dict(exact_systems=30, basis_consistency=True, trajectory_hashes=True,
                                  q1_units=len(q1), q2_units=len(q2), q2_identity=True, pruned_exact_consistency=True),
                    solver="Unit-norm columns; augmented QR; subset SVD lstsq; no centering or Gram matrix",
                    ties="Exact floating-point equality; lowest basis index for selection; Q1 ties against truth",
                    r3_counting="Addition-needing Q2 units, F0 evaluated on each same unit (repeated across distinct S0)",
                    no_addition_units="m=0; Q2a vacuously true, backward elimination still runs; excluded from R2/R3",
                    undefined_metrics="NaN for zero denominators or AUC lacking either class; nonfinite AUC input yields NaN")
    output.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        for column in frame:
            if frame[column].map(lambda v: isinstance(v, (list, dict))).any():
                frame[column] = frame[column].map(lambda v: json.dumps(v, separators=(",", ":")))
        frame.to_csv(output / name, index=False, lineterminator="\n")
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else repo / args.output_dir
    print(json.dumps(run(repo, output.resolve()), indent=2))


if __name__ == "__main__":
    main()
