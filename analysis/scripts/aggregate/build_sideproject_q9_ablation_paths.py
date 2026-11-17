"""Q9-ABL paths (docs/sideproject_residual_growth_protocol_q9_ablation.md): the five Figure-6 arms on the noisy
dim-1/2 data sets of Q9; no fits, no truth scoring.

Reuses the frozen Q8 path code unchanged (`build_path`, the forward-only `FORWARD` via `no_foba=True`, `ARMS`).
The non-`no_foba` arms take the Q9 candidate lists as they are (C1000's paths do not depend on the arm's fit
settings); `no_foba` paths are built here. One shard is one data set with all five arms.

Controls written to technical.json: (1) every Q9 path rebuilt for a sample equals the stored Q9 path; (2) on the Q8
data sets, every arm's candidate list equals the Q8 one (no_foba included).
"""
from __future__ import annotations
import argparse
import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
import build_sideproject_q8_paths as q8

q6 = q8.q6
ROOT, EXPORT = q8.ROOT, q8.EXPORT
OUTPUT = ROOT/'outputs/sideproject_q9abl_inputs'
PROTOCOL = ROOT/'docs/sideproject_residual_growth_protocol_q9_ablation.md'
Q9_PATHS = ROOT/'outputs/sideproject_q9_inputs/grid/q9_paths.json'
Q8_GRID = ROOT/'outputs/sideproject_q8_inputs/grid'
Q8_RECORDS = ROOT/'outputs/sideproject_q8_512dd5bd534530327b1f5fed3e7892a1e0950016/out_final/out'
ARMS = ('no_foba', 'random_start', 'no_refit', 'C10', 'A1000')
KEYS = ('ic_mode', 'coefficient_bound', 'start', 'refit')


def candidate_key(cell):
    return q6.canonical([(k['candidate_id'], k['active_idxs'], k['p0']) for k in cell['candidates']])


def measured_seconds():
    """Mean Q8 solve seconds per candidate, per arm and system (planning only)."""
    tot, cnt = {}, {}
    for p in sorted(Q8_RECORDS.glob('index_*.jsonl')):
        for line in p.read_text().splitlines():
            r = json.loads(line)
            key = (r['arm'], int(r['cell_id'][3:7]))
            s = float(r['fit_meta'].get('solve_time_s', 0.0) or 0.0) if isinstance(r['fit_meta'], dict) else 0.0
            tot[key] = tot.get(key, 0.) + s
            cnt[key] = cnt.get(key, 0) + 1
    return {k: tot[k]/cnt[k] for k in tot}


def run(output, workers=1, limit=None, rebuild_sample=20):
    output = Path(output).resolve()
    if not output.is_relative_to(OUTPUT.resolve()):
        raise ValueError('Output outside Q9-ABL workspace')
    if output.exists():
        raise FileExistsError(output)
    q9 = json.loads(Q9_PATHS.read_bytes())
    if q9['protocol'] != 'Q9' or q9['arm'] != 'C1000':
        raise ValueError('Unexpected Q9 path file')
    cells = sorted((c for c in q9['cells'] if c['dim'] <= 2 and c['sigma'] > 0), key=lambda c: c['cell_id'])
    if len(cells) != 3060:
        raise ValueError(f'Expected 3,060 noisy dim-1/2 Q9 cells, found {len(cells)}')
    if limit is not None:
        cells = cells[:limit]

    def job(cell):
        base = {k: cell[k] for k in ('unit_id', 'cell_id', 'system_id', 'initial_condition_set', 'dim',
                                     'representability', 'stratum', 'sigma', 'rho', 'realization',
                                     'observed_data_sha256', 'export', 'n_observed_points')}
        return q8.build_path(base, 'q7', True)
    with threadpool_limits(limits=1):
        if workers == 1:
            forward = list(map(job, cells))
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool:
                forward = list(pool.map(job, cells))

    # Control 1: the Q8 path function rebuilds the stored Q9 paths (sample, evenly spaced).
    step = max(1, len(cells)//max(1, rebuild_sample))
    rebuilt_ok = 0
    for c in cells[::step][:rebuild_sample]:
        base = {k: c[k] for k in ('unit_id', 'cell_id', 'system_id', 'initial_condition_set', 'dim',
                                  'representability', 'stratum', 'sigma', 'rho', 'realization',
                                  'observed_data_sha256', 'export', 'n_observed_points')}
        if candidate_key(q8.build_path(base, 'q7')) != candidate_key(c):
            raise ValueError(f'Q9 path not reproduced: {c["cell_id"]}')
        rebuilt_ok += 1

    seconds = measured_seconds()
    out = []
    for c, f in zip(cells, forward):
        for arm in ARMS:
            ic, bound, start, refit = q8.ARMS[arm]
            x = copy.deepcopy(f if arm == 'no_foba' else c)
            for k in ('block', 'planned_seconds', 'timing_proxy', 'shard_id', 'arm'):
                x.pop(k, None)
            x.update(arm=arm, ic_mode=ic, coefficient_bound=bound, start=start, refit=refit, reuse_q7=False,
                     shard_id=c['cell_id']+'__abl')
            for k in x['candidates']:
                k['new'] = True
            rate = seconds.get((arm, c['system_id']), 0.0)
            x['planned_seconds'] = rate*len(x['candidates']) if refit else 0.0
            out.append(x)

    # Control 2: on Q8's data sets every arm's candidate list equals Q8's.
    q8_identical, q8_compared = 0, 0
    for arm in ARMS:
        old = {c['cell_id']: c for c in json.loads((Q8_GRID/f'q8_{arm}_paths.json').read_bytes())['cells']}
        for x in (y for y in out if y['arm'] == arm and y['cell_id'] in old):
            q8_compared += 1
            if candidate_key(x) != candidate_key(old[x['cell_id']]):
                raise ValueError(f'Q8 path identity failed: {arm} {x["cell_id"]}')
            for k in KEYS:
                if q6.canonical(x[k]) != q6.canonical(old[x['cell_id']][k]):
                    raise ValueError(f'Q8 settings differ: {arm} {k}')
            q8_identical += 1

    shard_cost = {}
    for x in out:
        shard_cost[x['shard_id']] = shard_cost.get(x['shard_id'], 0.) + x['planned_seconds']
    order = sorted(shard_cost, key=lambda s: (-shard_cost[s], s))
    header = dict(protocol='Q9-ABL', mode='grid' if limit is None else 'technical_limit', path_end='q7',
                  arms=list(ARMS), q9abl_protocol_sha256=q6.sha256(PROTOCOL), q9_paths_sha256=q6.sha256(Q9_PATHS),
                  input_sha256={p.relative_to(ROOT).as_posix(): q6.sha256(p) for p in
                                (EXPORT/'index.csv', PROTOCOL, Q9_PATHS, Path(__file__), Path(q8.__file__),
                                 Path(q8.q7.__file__), Path(q6.__file__))})
    output.mkdir(parents=True)
    q8.dump(output/'q9abl_paths.json', dict(header, cells=out))
    (output/'q9abl_grid.shards_cost_desc.txt').write_text(''.join(s+'\n' for s in order), encoding='utf8')
    hours = {arm: sum(x['planned_seconds'] for x in out if x['arm'] == arm)/3600 for arm in ARMS}
    summary = dict(cells=len(cells), cell_arms=len(out), shards=len(order),
                   states={arm: sum(len(x['candidates']) for x in out if x['arm'] == arm) for arm in ARMS},
                   planned_core_h=hours, planned_core_h_total=sum(hours.values()),
                   longest_shard_h=shard_cost[order[0]]/3600 if order else 0,
                   control_q9_rebuilt=rebuilt_ok, control_q8_identical=q8_identical, control_q8_compared=q8_compared,
                   empty_no_foba_paths=sum(1 for x in out if x['arm'] == 'no_foba' and not x['candidates']))
    q8.dump(output/'technical.json', summary)
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=OUTPUT/'grid')
    p.add_argument('--workers', type=int, default=1)
    p.add_argument('--limit', type=int)
    a = p.parse_args()
    print(json.dumps(run(a.output, a.workers, a.limit), sort_keys=True))
