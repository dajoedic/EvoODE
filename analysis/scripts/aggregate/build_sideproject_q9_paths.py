"""Q9 (final WISP run) paths: all 63 systems, arm C1000, Q7 stop; no fits, no truth scoring.

Reuses the frozen Q8 path function unchanged. Planning cost comes from measured
Q8 C1000 solve seconds per candidate per system (planning only, never evidence).
"""
from __future__ import annotations
import argparse
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import build_sideproject_q8_paths as q8
from build_sideproject_q5_paths import cell_id, read_export_index

q6 = q8.q6
ROOT, EXPORT = q8.ROOT, q8.EXPORT
OUTPUT = ROOT/'outputs/sideproject_q9_inputs'
PROTOCOL = ROOT/'docs/sideproject_residual_growth_protocol_q9.md'
Q8_RECORDS = ROOT/'outputs/sideproject_q8_512dd5bd534530327b1f5fed3e7892a1e0950016/out_sneak_2026-11-07'
ARM = 'C1000'
SETTINGS = dict(zip(('ic_mode', 'coefficient_bound', 'start', 'refit'), q8.ARMS[ARM]))
NOISY = [(s, r) for s in (.01, .02, .03, .04, .05) for r in (0., .5)] + [(0., .5)]


def block(c):
    if c['dim'] == 3 and c['representability'] == 'exact':
        return 'dim3_exact_52_61' if c['system_id'] in (52, 61) else 'dim3_exact_54_59'
    return f"dim{c['dim']}_{c['representability']}"


def source_cells():
    support = json.loads((ROOT/'studies/regression/phase_c_support.json').read_bytes())
    systems = {s['system_id']: {k: s[k] for k in ('dim', 'representability')} for s in support['systems']}
    if len(systems) != 63:
        raise ValueError('Expected 63 systems')
    index = read_export_index(EXPORT/'index.csv')
    cells = []
    for row in index.to_dict('records'):
        sid, real = int(row['system_id']), int(row['noise_realization'])
        sigma, rho = float(row['noise_sigma']), float(row['subsample_rho'])
        if not ((sigma, rho) in NOISY or ((sigma, rho) == (0., 0.) and real == 1)):
            continue
        dim = systems[sid]['dim']
        uid = f"sys{sid:04d}_ic{int(row['initial_condition_set'])}"
        c = dict(unit_id=uid, cell_id=cell_id(uid, sigma, rho, real), system_id=sid,
                 initial_condition_set=int(row['initial_condition_set']), dim=dim,
                 representability=systems[sid]['representability'],
                 stratum=f'dim{dim}_'+systems[sid]['representability'], sigma=sigma, rho=rho, realization=real,
                 observed_data_sha256=q6.data_sha(pd.Series(row)), export=row,
                 n_observed_points=int(row['n_observed_points']))
        c['block'] = block(c)
        cells.append(c)
    cells.sort(key=lambda c: c['cell_id'])
    if len(cells) != 4284 or len({c['cell_id'] for c in cells}) != 4284:
        raise ValueError('Expected exactly 4,284 Q9 cells')
    return cells


def measured_seconds():
    """Mean Q8 C1000 solve seconds per candidate, per system; dimension maximum for systems without timing."""
    tot, cnt = {}, {}
    files = sorted(Q8_RECORDS.glob('index_*.jsonl'))
    for p in files:
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if r['arm'] != ARM:
                continue
            sid = int(r['cell_id'][3:7])
            s = float(r['fit_meta']['solve_time_s'])
            if not np.isfinite(s) or s < 0:
                raise ValueError('Invalid solve time')
            tot[sid] = tot.get(sid, 0.) + s
            cnt[sid] = cnt.get(sid, 0) + 1
    return {s: tot[s]/cnt[s] for s in tot}, dict(files=len(files), candidates=sum(cnt.values()), systems=len(cnt))


def run(output, workers=1, limit=None):
    output = Path(output).resolve()
    if not output.is_relative_to(OUTPUT.resolve()):
        raise ValueError('Output outside Q9 workspace')
    if output.exists():
        raise FileExistsError(output)
    cells = source_cells()
    if limit is not None:
        cells = cells[:limit]
    per_system, timing = measured_seconds()
    support = json.loads((ROOT/'studies/regression/phase_c_support.json').read_bytes())
    dims = {s['system_id']: s['dim'] for s in support['systems']}
    dim_max = {d: max(v for s, v in per_system.items() if dims[s] == d) for d in set(dims[s] for s in per_system)}
    dim_max[4] = max(dim_max.values())

    def job(cell):
        return q8.build_path(cell, 'q7')
    with threadpool_limits(limits=1):
        if workers == 1:
            built = list(map(job, cells))
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                built = list(pool.map(job, cells))
    allcells = []
    for c in built:
        c = copy.deepcopy(c)
        c.update(arm=ARM, **SETTINGS, shard_id=c['cell_id']+'__'+ARM, reuse_q7=False)
        for k in c['candidates']:
            k['new'] = True
        measured = c['system_id'] in per_system
        rate = per_system[c['system_id']] if measured else dim_max[c['dim']]
        c.update(planned_seconds=rate*len(c['candidates']),
                 timing_proxy='Q8 C1000 mean solve s/candidate, this system' if measured
                 else f"Q8 C1000 maximum mean solve s/candidate over dim {c['dim']} (no timing for this system)")
        allcells.append(c)
    header = dict(protocol='Q9', mode='grid' if limit is None else 'technical_limit', path_end='q7', arm=ARM,
                  q9_protocol_sha256=q6.sha256(PROTOCOL),
                  input_sha256={p.relative_to(ROOT).as_posix(): q6.sha256(p) for p in
                                (EXPORT/'index.csv', PROTOCOL, Path(__file__), Path(q8.__file__),
                                 Path(q8.q7.__file__), Path(q6.__file__))})
    ordered = sorted(allcells, key=lambda c: (-c['planned_seconds'], c['shard_id']))
    probe = []
    for name in sorted({c['block'] for c in allcells}):
        group = [c for c in allcells if c['block'] == name]
        unit_cost = {}
        for c in group:
            unit_cost[c['unit_id']] = unit_cost.get(c['unit_id'], 0.) + c['planned_seconds']
        units = sorted(unit_cost, key=lambda u: (unit_cost[u], u))
        median = units[len(units)//2]
        probe.append(min((c for c in group if c['unit_id'] == median), key=lambda c: (c['planned_seconds'], c['cell_id'])))
    probe.sort(key=lambda c: (-c['planned_seconds'], c['shard_id']))
    output.mkdir(parents=True)
    q8.dump(output/'q9_paths.json', dict(header, cells=ordered))
    q8.dump(output/'q9_probe_paths.json', dict(header, cells=probe))
    for name, items in (('grid', ordered), ('probe', probe)):
        (output/f'q9_{name}.shards_cost_desc.txt').write_text(''.join(c['shard_id']+'\n' for c in items), encoding='utf8')
    hours = pd.DataFrame([dict(block=c['block'], system_id=c['system_id'], h=c['planned_seconds']/3600,
                               states=len(c['candidates'])) for c in allcells])
    summary = dict(cells=len(allcells), shards=len(allcells), probe_shards=len(probe),
                   probe=[c['shard_id'] for c in probe], states=int(hours.states.sum()), timing=timing,
                   planned_core_h=float(hours.h.sum()), longest_shard_h=float(hours.h.max()),
                   blocks={b: dict(cells=int(len(g)), states=int(g.states.sum()), core_h=float(g.h.sum()))
                           for b, g in hours.groupby('block')},
                   systems_without_timing=sorted({c['system_id'] for c in allcells if c['system_id'] not in per_system}))
    q8.dump(output/'technical.json', summary)
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=OUTPUT/'grid')
    p.add_argument('--workers', type=int, default=1)
    p.add_argument('--limit', type=int)
    a = p.parse_args()
    print(json.dumps(run(a.output, a.workers, a.limit), sort_keys=True))
