"""Frozen Q4 normalised forward/backward weak growth paths."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
from build_sideproject_q3_weak_starts import (
    ROOT, WeakFit, phasec_basis, build_design, load_exact_supports,
    load_exported_trajectories, verify_basis_consistency, stratum_for,
    SUPPORT, EXPORT, flatten_parameters, weak_coefficients, sha256,
)
import numpy as np

OUTPUT = ROOT / "analysis/data/sideproject_residual_growth/q4_paths.json"


def growth_path(designs, targets):
    fits = [WeakFit(a, b) for a, b in zip(designs, targets)]
    active = [set() for _ in fits]
    candidates, log, seen = [], [], set()
    step = 0
    while True:
        gains = []
        for eq, fit in enumerate(fits):
            if len(active[eq]) >= 6 or fit.b_norm2 == 0 or fit.sse(active[eq]) / fit.b_norm2 < 1e-14:
                continue
            for term in sorted(set(range(fit.p)) - active[eq]):
                gain = (fit.sse(active[eq]) - fit.sse(active[eq] | {term})) / fit.b_norm2
                gains.append((gain, eq, term))
        if not gains:
            break
        gain, eq, term = min(gains, key=lambda x: (-x[0], x[1], x[2]))
        if gain <= 0:
            raise ValueError("No positive gain before protocol stop")
        step += 1
        active[eq].add(term)
        entry = dict(step=step, addition=dict(equation=eq+1, basis_index=term+1, gain=gain),
                     gains=[dict(equation=e+1, basis_index=t+1, gain=g) for g,e,t in gains],
                     backward_checks=[])
        removed = False
        while True:
            checks = []
            for e, fit in enumerate(fits):
                for t in sorted(active[e]):
                    cost = (fit.sse(active[e] - {t}) - fit.sse(active[e])) / fit.b_norm2 if fit.b_norm2 else 0.
                    checks.append((cost, e, t))
            eligible = [x for x in checks if x[0] < .5 * gain]
            chosen = min(eligible) if eligible else None
            entry['backward_checks'].append(dict(
                checks=[dict(cost=c, equation=e+1, basis_index=t+1, qualifies=c < .5*gain) for c,e,t in checks],
                removed=None if chosen is None else dict(cost=chosen[0], equation=chosen[1]+1, basis_index=chosen[2]+1)))
            if chosen is None:
                break
            active[chosen[1]].remove(chosen[2])
            removed = True
        key = tuple(tuple(sorted(eq)) for eq in active)
        if key in seen:
            raise ValueError("Repeated FoBa model")
        seen.add(key)
        candidates.append(dict(step=step, origin='removal' if removed else 'addition', support=[list(eq) for eq in key]))
        log.append(entry)
    return candidates, log


def build(output=OUTPUT):
    if output.exists():
        raise FileExistsError(output)
    basis_name, systems = load_exact_supports(ROOT / SUPPORT)
    verify_basis_consistency(systems)
    trajectories = load_exported_trajectories(ROOT / EXPORT, [s['system_id'] for s in systems])
    with (ROOT / EXPORT / 'trajectory_manifest.csv').open(newline='', encoding='utf8') as f:
        manifest = {(int(r['system_id']), int(r['initial_condition_set'])): r for r in csv.DictReader(f)}
    with (ROOT / 'analysis/data/sideproject_residual_growth/q1_units.csv').open(newline='', encoding='utf8') as f:
        q1 = {(int(r['system_id']), int(r['initial_condition_set']), int(r['equation_index'])): r for r in csv.DictReader(f)}
    units = []
    inputs = {SUPPORT, EXPORT / 'trajectory_manifest.csv', Path('docs/sideproject_residual_growth_protocol_q4.md'),
              Path(__file__).relative_to(ROOT), Path('analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py'),
              Path('analysis/scripts/aggregate/run_sideproject_residual_growth.py'),
              Path('analysis/exploratory/term_relevance/term_relevance.py')}
    inputs.add(Path('analysis/data/sideproject_residual_growth/q1_units.csv'))
    for system in systems:
        sid, dim = int(system['system_id']), int(system['dim'])
        terms = phasec_basis(dim)
        for ic in (1, 2):
            trajectory = trajectories[sid, ic]
            matrices = [build_design(trajectory.time, trajectory.state, eq, 'weak', terms)[:2] for eq in range(dim)]
            designs, targets = zip(*matrices)
            path, log = growth_path(designs, targets)
            repeat, repeat_log = growth_path(designs, targets)
            if path != repeat or log != repeat_log:
                raise AssertionError('Path determinism failed')
            candidates = []
            for item in path:
                equations, maps = [], []
                for eq, indices in enumerate(item['support']):
                    coef, sse = weak_coefficients(designs[eq], targets[eq], indices)
                    idx = [i+1 for i in indices]
                    maps.append(dict(zip(idx, coef)))
                    equations.append(dict(equation_index=eq+1, basis_indices=idx,
                        term_names=[terms[i].name for i in indices], coefficients=coef.tolist(),
                        weak_sse=sse, n_rows=len(targets[eq])))
                active = [e['basis_indices'] for e in equations]
                bic = sum(e['n_rows'] * (math.log(e['weak_sse']/e['n_rows']) if e['weak_sse'] > 0 else -math.inf)
                          + len(e['basis_indices'])*math.log(e['n_rows']) for e in equations)
                candidates.append(dict(candidate_id=f"path_{item['step']:03d}", step=item['step'],
                    origin=item['origin'], active_idxs=active, equations=equations,
                    p0=flatten_parameters(active, maps), weak_bic=bic if math.isfinite(bic) else '-Infinity', k=sum(map(len, active))))
            upper_eqs, upper_maps = [], []
            for eq in range(dim):
                record = q1[sid, ic, eq+1]
                names = system['support_terms'][eq] if int(record['q1_rank']) == 1 else json.loads(record['best_other_terms'])
                indices = sorted(i for i,t in enumerate(terms) if t.name in names)
                coef, sse = weak_coefficients(designs[eq], targets[eq], indices)
                idx = [i+1 for i in indices]
                upper_maps.append(dict(zip(idx, coef)))
                upper_eqs.append(dict(basis_indices=idx, term_names=[terms[i].name for i in indices],
                    coefficients=coef.tolist(), weak_sse=sse, n_rows=len(targets[eq])))
            upper_active = [e['basis_indices'] for e in upper_eqs]
            upper = dict(candidate_id='upper_subset', active_idxs=upper_active, equations=upper_eqs,
                         p0=flatten_parameters(upper_active, upper_maps), k=sum(map(len, upper_active)))
            info = manifest[sid, ic]
            for field in ('time_path', 'state_path'):
                inputs.add(EXPORT / info[field])
            units.append(dict(unit_id=f'sys{sid:04d}_ic{ic}', system_id=sid, initial_condition_set=ic,
                dim=dim, stratum=stratum_for(sid, dim), export=info, trajectory_sha256=trajectory.sha256,
                candidates=candidates, upper_candidates=[upper], step_log=log))
    if len(units) != 60 or len({u['unit_id'] for u in units}) != 60:
        raise ValueError('Expected 60 unique units')
    payload = dict(protocol_commit='24ede2d', basis_name=basis_name, determinism_checked=True, units=units,
                   tie_rule='gain descending then equation/index; removal cost ascending then equation/index',
                   input_sha256={p.as_posix(): sha256(ROOT/p) for p in sorted(inputs)})
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf8') as f:
        json.dump(payload, f, indent=2, allow_nan=False)
        f.write('\n')
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({u['unit_id']: len(u['candidates']) for u in result['units']}))
