"""Build Q7 significance-ended paths and inputs for the unchanged Q5 fitter."""
from __future__ import annotations
import argparse
import ast
import pickle
import subprocess
import sys
import uuid
import hashlib
import json
from pathlib import Path
import csv
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import build_sideproject_q6_paths as q6

ROOT = q6.ROOT
OUTPUT = ROOT/'outputs/sideproject_q7_inputs'
PROTOCOL = ROOT/'docs/sideproject_residual_growth_protocol_q7.md'
EXPLORATORY = ROOT/'analysis/exploratory/sideproject_q7_gain_test/q7_gain_test.py'
THRESHOLDS = {'chi2_0.01': 6.635, 'chi2_0.001': 10.828}


def significance_end(designs, operators, threshold):
    """An equation ends iff every remaining gain/noise is strictly below threshold."""
    cache = {}
    def floor(eq, support):
        key = eq, tuple(sorted(support))
        if key not in cache:
            cache[key] = q6.projected_noise_floor(designs[eq], support, operators[eq])
        return cache[key]
    def end(eq, fit, support):
        sse, noise_floor = fit.sse(support), floor(eq, support)
        for term in sorted(set(range(fit.p))-set(support)):
            extended = set(support) | {term}
            noise = noise_floor-floor(eq, extended)
            if noise <= 0 or (sse-fit.sse(extended))/noise >= threshold:
                return None
        return sse
    return end


def exploratory_supports(cell, export):
    """Execute the original job's path arithmetic, excluding its truth evaluation.

    Remove only the equation-reporting loop and capture growth_path_with_end's
    returned supports. The threshold and closure come from the actual source.
    """
    tree = ast.parse(EXPLORATORY.read_text(encoding='utf8'))
    job = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'job')
    rule_loop = next(n for n in job.body if isinstance(n, ast.For))
    rule_loop.body = [n for n in rule_loop.body if not isinstance(n, ast.For)]
    captured = []
    class Proxy:
        def __getattr__(self, name):
            if name == 'growth_path_with_end':
                def capture(*args, **kwargs):
                    result = q6.growth_path_with_end(*args, **kwargs)
                    captured.append([p['support'] for p in result[0]])
                    return result
                return capture
            return getattr(q6, name)
    threshold_node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'THRESHOLDS' for t in n.targets))
    exploratory_thresholds = ast.literal_eval(threshold_node.value)
    if exploratory_thresholds != THRESHOLDS:
        raise ValueError('Exploratory thresholds changed')
    ns = dict(q6=Proxy(), np=np, pd=pd, THRESHOLDS=exploratory_thresholds)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[job], type_ignores=[])), str(EXPLORATORY), 'exec'), ns)
    ns['job']((cell, export, None))
    return dict(zip(THRESHOLDS, captured))


def support_key(candidate):
    return tuple(tuple(eq) for eq in candidate['active_idxs'])


def build_cell(cell, export=q6.EXPORT, compare=True):
    time, state = q6.read_index_cell(export, pd.Series(cell['export']))
    if q6.data_sha(pd.Series(cell['export'])) != cell['observed_data_sha256']:
        raise ValueError('Q5 observed hash mismatch')
    terms = q6.phasec_basis(cell['dim'])
    designs, targets = zip(*(q6.build_design(time, state, eq, 'weak', terms)[:2] for eq in range(cell['dim'])))
    control, _, _ = q6.growth_path_with_end(designs, targets, cap=6)
    regenerated = [q6.candidate(designs, targets, terms, p['support'], f"path_{p['step']:03d}",
                               step=p['step'], origin=p['origin']) for p in control]
    if q6.canonical(regenerated) != q6.canonical(cell['candidates']):
        raise ValueError('Q5 candidate identity mismatch')
    variance = q6.estimate_noise_variance(time, state)
    incidence, _ = q6.weak_noise_operators(time)
    operators = [incidence.multiply(np.sqrt(variance[:, eq])[None, :]).tocsr() for eq in range(cell['dim'])]
    old = {support_key(k): k for k in cell['candidates']+cell['upper_candidates']}
    exploratory = exploratory_supports(cell, export) if compare else None
    paths, rows = {}, []
    for rule, threshold in THRESHOLDS.items():
        path, _, ends = q6.growth_path_with_end(designs, targets, significance_end(designs, operators, threshold))
        if compare and q6.canonical([p['support'] for p in path]) != q6.canonical(exploratory[rule]):
            raise ValueError('Exploratory support mismatch: '+cell['cell_id'])
        candidates = []
        for p in path:
            k = q6.candidate(designs, targets, terms, p['support'], f"q7_{p['step']:03d}",
                             step=p['step'], origin=p['origin'])
            reused = old.get(support_key(k))
            if reused is not None:
                if q6.canonical(k['p0']) != q6.canonical(reused['p0']):
                    raise ValueError('Reused p0 mismatch')
                k['reuse_q5_candidate_id'] = reused['candidate_id']
                k['new'] = False
            else:
                k['new'] = True
            candidates.append(k)
        paths[rule] = dict(cell, candidates=candidates, upper_candidates=[], ended_at_cap=False,
                           end_condition=rule, equation_paths=ends, path_end=[e['end_reason'] for e in ends])
        for end in ends:
            rows.append(dict(cell_id=cell['cell_id'], unit_id=cell['unit_id'], stratum=cell['stratum'],
                             sigma=cell['sigma'], rho=cell['rho'], realization=cell['realization'], rule=rule, **end))
    return paths, rows


def verify_inputs(payload):
    """Verify current inputs and recover the historic protocol before its execution amendment.

    The Q5 protocol was amended after its paths were frozen. No git subprocess
    or repository operation is needed to verify the original bytes.
    """
    for name, expected in payload['input_sha256'].items():
        raw = (ROOT/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() == expected:
            continue
        if name == q6.Q5_PROTOCOL:
            # The execution-only amendment was inserted before section 1.
            start = raw.find(b'## Amendment 2026-10-28')
            stop = raw.find(b'## 1. Question', start)
            historical = raw[:start]+raw[stop:] if start >= 0 and stop > start else raw
            if any(hashlib.sha256(v).hexdigest() == expected
                   for v in (historical, historical.replace(b'\r\n', b'\n'))):
                continue
        raise ValueError('Q5 input hash mismatch: '+name)


def dump(path, value):
    path.write_bytes(q6.canonical(value)+b'\n')


def run(output=OUTPUT, limit=None, workers=1, classify=False):
    output = Path(output).resolve()
    if not output.is_relative_to(OUTPUT.resolve()):
        raise ValueError('Output must stay under outputs/sideproject_q7_inputs')
    if output.exists():
        raise FileExistsError(output)
    payload = json.loads(q6.Q5.read_bytes())
    verify_inputs(payload)
    if len(payload['cells']) != 1632 or len({c['cell_id'] for c in payload['cells']}) != 1632:
        raise ValueError('Expected 1632 distinct Q5 cells')
    if workers < 1 or (limit is not None and limit < 1) or (limit is not None and classify):
        raise ValueError('Invalid workers/limit; truth fields require a full run')
    cells = payload['cells'] if limit is None else payload['cells'][:limit]
    inputs = dict(payload['input_sha256'])
    for p in (q6.Q5, PROTOCOL, Path(__file__), Path(q6.__file__), EXPLORATORY,
              ROOT/'studies/regression/phase_c_support.json',
              ROOT/'analysis/exploratory/term_relevance/term_relevance.py',
              ROOT/'analysis/scripts/aggregate/run_sideproject_residual_growth.py',
              ROOT/'analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py',
              ROOT/'analysis/scripts/aggregate/build_sideproject_q4_paths.py',
              ROOT/'analysis/scripts/aggregate/run_phasec_noise_sindy_baselines.py'):
        inputs[p.relative_to(ROOT).as_posix()] = q6.sha256(p)
    header = dict(protocol='Q7', protocol_commit='f737939', mode='grid' if limit is None else 'technical_limit',
                  q7_protocol=dict(path=PROTOCOL.relative_to(ROOT).as_posix(), sha256=q6.sha256(PROTOCOL)),
                  input_sha256=inputs)
    results = build_all(cells, workers)
    byrule = {r:[p[r] for p, _ in results] for r in THRESHOLDS}
    rows = [row for _, rs in results for row in rs]
    if classify:
        support = json.loads((ROOT/'studies/regression/phase_c_support.json').read_bytes())
        truth = {s['system_id']:s['support_idxs'] for s in support['systems'] if s.get('representability') == 'exact'}
        for c in cells:
            t, x = q6.read_index_cell(q6.EXPORT, pd.Series(c['export']))
            terms = q6.phasec_basis(c['dim'])
            a, b = zip(*(q6.build_design(t,x,e,'weak',terms)[:2] for e in range(c['dim'])))
            ref, _, _ = q6.growth_path_with_end(a,b)
            for row in (r for r in rows if r['cell_id'] == c['cell_id']):
                eq = row['equation_index']-1
                true = set(truth[c['system_id']][eq])
                cell = next(k for k in byrule[row['rule']] if k['cell_id'] == c['cell_id'])
                history = [set(k['active_idxs'][eq]) for k in cell['candidates']]
                reached = next((i for i,s in enumerate(history) if true <= s),None)
                final = history[-1] if history else set()
                row.update(classification='R' if reached is not None else 'T' if any(true <= {i+1 for i in p['support'][eq]} for p in ref) else 'P',
                           first_truth_step=None if reached is None else reached+1,
                           extra_terms_at_end=None if reached is None else len(final-true),
                           extra_terms_first_truth=None if reached is None else len(history[reached]-true),
                           true_term_recall_at_end=len(final & true)/len(true))
    primary = byrule['chi2_0.01']
    fits = [dict(c, candidates=[k for k in c['candidates'] if k['new']]) for c in primary if any(k['new'] for k in c['candidates'])]
    # Q5's method: Q5 planned mean candidate time per unit times candidate count,
    # descending total planned shard cost, with cell ID as deterministic tie break.
    costs = measured_costs()
    shards = sorted(fits, key=lambda c:(-costs[c['unit_id']]*len(c['candidates']), c['cell_id']))
    output.mkdir(parents=True)
    dump(output/'q7_paths.json',dict(header,cells=primary))
    dump(output/'q7_alpha_0_001_paths.json',dict(header,cells=byrule['chi2_0.001']))
    dump(output/'q7_fit_paths.json',dict(header,cells=fits))
    (output/'q7_fit_paths.shards_cost_desc.txt').write_text(''.join(c['cell_id']+'\n' for c in shards),encoding='utf8')
    with (output/'equations.csv').open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (output/'controls.csv').open('w',newline='',encoding='utf8') as f:
        writer = csv.DictWriter(f,fieldnames=['cell_id','hash_control','q5_identity_control','exploratory_support_control'])
        writer.writeheader()
        writer.writerows(dict(cell_id=c['cell_id'],hash_control=True,q5_identity_control=True,exploratory_support_control=True) for c in cells)
    # A separate two-state input avoids --limit (which limits cells, not states).
    smoke_pool = [c for c in fits if c['dim']==2 and len(c['candidates'])>=2]
    smoke_cell = min(smoke_pool, key=lambda c:(costs[c['unit_id']],c['cell_id'])) if smoke_pool else None
    smoke = None if smoke_cell is None else dict(smoke_cell,candidates=smoke_cell['candidates'][:2])
    if smoke:
        dump(output/'q7_smoke_two_states.json',dict(header,mode='technical_smoke',cells=[smoke]))
    summary = dict(cells=len(cells), states=sum(len(c['candidates']) for c in primary),
                   cells_with_new_states=len(fits), new_states=sum(len(c['candidates']) for c in fits),
                   new_states_by_dimension={str(d):sum(len(c['candidates']) for c in fits if c['dim']==d) for d in (1,2,3,4)},
                   hash_control=True,q5_identity_control=True,exploratory_support_control=True,
                   truth_fields=classify,smoke_cell_id=None if smoke is None else smoke['cell_id'])
    dump(output/'technical.json',summary)
    return summary


def build_all(cells, workers):
    if workers == 1:
        with threadpool_limits(limits=1):
            return [build_cell(c) for c in cells]
    # Windows' managed sandbox can deny multiprocessing Pipe creation. Use
    # independent interpreters with workspace files, never IPC pipes.
    folder = OUTPUT/'work'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    children = []
    handles = []
    try:
        for worker in range(min(workers,len(cells))):
            jobs = [(i,c) for i,c in enumerate(cells) if i % workers == worker]
            source = folder/f'{worker}.json'
            dump(source,jobs)
            handle = (folder/f'{worker}.log').open('wb')
            handles.append(handle)
            process = subprocess.Popen([sys.executable,str(Path(__file__).resolve()),
                                        '--worker-input',str(source)],
                                       stdin=subprocess.DEVNULL,stdout=handle,stderr=handle)
            children.append((process,source))
        indexed = []
        for process,source in children:
            if process.wait() != 0:
                raise RuntimeError('Q7 worker failed; see '+str(source.with_suffix('.log')))
            with source.with_suffix('.pickle').open('rb') as f:
                indexed.extend(pickle.load(f))
        return [result for _,result in sorted(indexed)]
    finally:
        for process,_ in children:
            if process.poll() is None:
                process.terminate()
                process.wait()
        for handle in handles: handle.close()


def worker_main(source):
    source = Path(source).resolve()
    if not source.is_relative_to((OUTPUT/'work').resolve()):
        raise ValueError('Worker input outside Q7 workspace')
    jobs = json.loads(source.read_bytes())
    results = []
    with threadpool_limits(limits=1):
        for index,cell in jobs:
            results.append((index,build_cell(cell)))
            if len(results) % 100 == 0:
                print(json.dumps(dict(completed_cells=len(results))),flush=True)
    with source.with_suffix('.pickle').open('xb') as f: pickle.dump(results,f)


def measured_costs():
    """Q5's frozen planning method: measured Q4 mean candidate time per unit.

    Only probe fits are present locally; the complete per-unit planning inputs
    are already frozen inside the Q5 manifest. No unavailable grid timing is
    imputed from a different system or stratum.
    """
    return json.loads(q6.Q5.read_bytes())['q4_seconds_per_candidate']


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker-input',type=Path,help=argparse.SUPPRESS)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--limit',type=int)
    parser.add_argument('--workers',type=int,default=1)
    parser.add_argument('--classify',action='store_true',help='Truth fields, full run only; for later authorized use')
    args=parser.parse_args()
    if args.worker_input:
        worker_main(args.worker_input)
    else:
        print(json.dumps(run(args.output,args.limit,args.workers,args.classify),sort_keys=True))
