"""Q5 paths on the original C-6 observations; Q4 algorithms are imported unchanged."""
from __future__ import annotations
import argparse
import itertools
import json
import math
import time
from pathlib import Path
import numpy as np
from build_sideproject_q4_paths import (
    ROOT, WeakFit, phasec_basis, build_design, growth_path, weak_coefficients,
    flatten_parameters, sha256,
)
from run_phasec_noise_sindy_baselines import read_export_index, read_index_cell, data_sha

BASE = ROOT / 'outputs/sideproject_q5_inputs'
EXPORT = ROOT / 'outputs/phase_c_c6_data_conditions_5dd1df8'
Q4 = ROOT / 'analysis/data/sideproject_residual_growth/q4_paths.json'
Q4_RESULTS = [ROOT/'outputs/sideproject_q4_path_fits/results.jsonl',
              *sorted((ROOT/'outputs/sideproject_q4_e70eeea/out').glob('index_*.jsonl'))]
STRATA = ('dim1', 'dim2', 'dim4', 'dim3_feasible')


def q4_costs(files=Q4_RESULTS):
    records = {}
    for path in files:
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if r['candidate_id'] != 'control_true':
                records.setdefault((r['unit_id'], r['candidate_id']), r)
    costs = {}
    for (uid, _), r in records.items():
        costs.setdefault(uid, []).append(float(r['fit_meta']['fit_time_s']))
    return {uid: sum(v)/len(v) for uid, v in costs.items()}


def probe_units(units, costs):
    # Upper middle order statistic for even counts; unit ID breaks cost ties.
    return [sorted([u for u in units if u['stratum'] == s],
                   key=lambda u: (costs[u['unit_id']]*(len(u['candidates'])+len(u['upper_candidates'])), u['unit_id']))[
                       len([u for u in units if u['stratum'] == s])//2]['unit_id']
            for s in ('dim1', 'dim2', 'dim3_feasible')]


def cell_id(uid, sigma, rho, realization):
    return f'{uid}_s{sigma:g}_r{rho:g}_n{realization}'


def candidate(designs, targets, terms, support, cid, **extra):
    equations, maps = [], []
    for eq, indices in enumerate(support):
        coef, sse = weak_coefficients(designs[eq], targets[eq], indices)
        idx = [i+1 for i in indices]
        maps.append(dict(zip(idx, coef)))
        equations.append(dict(equation_index=eq+1, basis_indices=idx,
            term_names=[terms[i].name for i in indices], coefficients=coef.tolist(),
            weak_sse=sse, n_rows=len(targets[eq])))
    active = [e['basis_indices'] for e in equations]
    bic = sum(e['n_rows']*(math.log(e['weak_sse']/e['n_rows']) if e['weak_sse'] > 0 else -math.inf)
              + len(e['basis_indices'])*math.log(e['n_rows']) for e in equations)
    return dict(candidate_id=cid, active_idxs=active, equations=equations,
                p0=flatten_parameters(active, maps), k=sum(map(len, active)),
                weak_bic=bic if math.isfinite(bic) else '-Infinity', **extra)


def build_cell(unit, row, export=EXPORT):
    t, x = read_index_cell(export, row)
    terms = phasec_basis(unit['dim'])
    designs, targets = zip(*(build_design(t, x, eq, 'weak', terms)[:2] for eq in range(unit['dim'])))
    path, _ = growth_path(designs, targets)
    candidates = [candidate(designs, targets, terms, p['support'], f"path_{p['step']:03d}",
                            step=p['step'], origin=p['origin']) for p in path]
    fits = [WeakFit(a, b) for a, b in zip(designs, targets)]
    last = path[-1]['support'] if path else [[] for _ in fits]
    ends = ['cap' if len(s) >= 6 else 'sse' if f.b_norm2 == 0 or f.sse(s)/f.b_norm2 < 1e-14
            else 'invalid' for f, s in zip(fits, last)]
    if 'invalid' in ends:
        raise ValueError('Unexplained path end')
    upper_support = [min(itertools.combinations(range(f.p), len(eq['basis_indices'])),
                         key=lambda s: (f.sse(s), s))
                     for f, eq in zip(fits, unit['upper_candidates'][0]['equations'])]
    upper = candidate(designs, targets, terms, upper_support, 'upper_subset')
    sigma, rho, n = float(row.noise_sigma), float(row.subsample_rho), int(row.noise_realization)
    if sigma == rho == 0:
        if candidates != unit['candidates']:
            raise ValueError(f"Q4 clean candidate identity failed: {unit['unit_id']}")
        # Preserve Q4 upper-bound record schema, also checked below by active support/p0.
        expected = unit['upper_candidates'][0]
        if upper['active_idxs'] != expected['active_idxs'] or upper['p0'] != expected['p0']:
            raise ValueError('Q4 upper subset identity failed')
        upper = expected
    return dict(unit_id=unit['unit_id'], cell_id=cell_id(unit['unit_id'], sigma, rho, n),
        system_id=unit['system_id'], initial_condition_set=unit['initial_condition_set'],
        dim=unit['dim'], stratum=unit['stratum'], sigma=sigma, rho=rho, realization=n,
        observed_data_sha256=data_sha(row), export=row.to_dict(),
        candidates=candidates, upper_candidates=[upper], path_end=ends,
        ended_at_cap=any(e == 'cap' for e in ends), n_observed_points=len(t))


def build(mode='probe', output=None):
    output = output or BASE/f'q5_{mode}_paths.json'
    if output.exists():
        raise FileExistsError(output)
    q4 = json.loads(Q4.read_text())
    units = [u for u in q4['units'] if u['stratum'] in STRATA]
    costs = q4_costs()
    probes = probe_units(units, costs)
    index = read_export_index(EXPORT/'index.csv')
    byunit = {(u['system_id'], u['initial_condition_set']): u for u in units}
    cells, started = [], time.perf_counter()
    for _, row in index.iterrows():
        unit = byunit.get((int(row.system_id), int(row.initial_condition_set)))
        if unit is None:
            continue
        clean = row.noise_sigma == row.subsample_rho == 0
        if clean and row.noise_realization != 1:
            continue
        if mode == 'controls' and not clean:
            continue
        if mode == 'probe' and not (unit['unit_id'] in probes and
                (clean or (row.noise_sigma == .05 and row.noise_realization == 1))):
            continue
        cells.append(build_cell(unit, row))
        print(json.dumps(dict(cell=cells[-1]['cell_id'], candidates=len(cells[-1]['candidates']),
                              elapsed_s=time.perf_counter()-started)), flush=True)
    cells.sort(key=lambda c: (STRATA.index(c['stratum']), c['unit_id'], c['sigma'], c['rho'], c['realization']))
    expected = {'probe':9, 'controls':48, 'grid':1632}[mode]
    if len(cells) != expected:
        raise ValueError(f'Expected {expected} cells, got {len(cells)}')
    inputs = {str(p.relative_to(ROOT)).replace('\\', '/'):sha256(p) for p in
              [Q4, EXPORT/'index.csv', Path(__file__), ROOT/'docs/sideproject_residual_growth_protocol_q5.md']}
    payload = dict(protocol_commit='f737939', mode=mode, cells=cells,
        probe_units=probes, input_sha256=inputs, build_seconds=time.perf_counter()-started,
        q4_seconds_per_candidate=costs)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf8') as f:
        json.dump(payload, f, allow_nan=False)
        f.write('\n')
    # One complete data set per shard; report the maximum alongside the estimate.
    estimates = {c['cell_id']:costs[c['unit_id']]*(len(c['candidates'])+len(c['upper_candidates'])) for c in cells}
    output.with_suffix('.shards.txt').write_text(''.join(c['cell_id']+'\n' for c in cells), encoding='utf8')
    output.with_suffix('.costs.json').write_text(json.dumps(dict(
        seconds=estimates, by_stratum={s:sum(estimates[c['cell_id']] for c in cells if c['stratum']==s)
                                      for s in STRATA}), indent=2)+'\n', encoding='utf8')
    return payload


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['probe','controls','grid'], default='probe')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    build(args.mode, args.output)
