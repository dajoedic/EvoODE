"""Exploratory (not a protocol run): stop an equation's growth when no remaining term's weak-SSE gain
exceeds a chi-square(1) quantile times the expected gain of a pure-noise term. Reuses Q6 machinery unchanged."""
import json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, 'analysis/scripts/aggregate')
import build_sideproject_q6_paths as q6

THRESHOLDS = {'chi2_0.01': 6.635, 'chi2_0.001': 10.828}


def job(args):
    cell, export, truth = args
    time, state = q6.read_index_cell(export, pd.Series(cell['export']))
    terms = q6.phasec_basis(cell['dim'])
    designs, targets = zip(*(q6.build_design(time, state, eq, 'weak', terms)[:2] for eq in range(cell['dim'])))
    variance = q6.estimate_noise_variance(time, state)
    incidence, _ = q6.weak_noise_operators(time)
    ops = [incidence.multiply(np.sqrt(variance[:, eq])[None, :]).tocsr() for eq in range(cell['dim'])]
    rows = []
    for name, thr in THRESHOLDS.items():
        fcache = {}

        def F(eq, s):
            k = (eq, tuple(sorted(s)))
            if k not in fcache:
                fcache[k] = q6.projected_noise_floor(designs[eq], s, ops[eq])
            return fcache[k]

        def end(eq, fit, support):
            base_sse, base_f = fit.sse(support), F(eq, support)
            best = 0.
            for j in set(range(fit.p)) - set(support):
                gain = base_sse - fit.sse(set(support) | {j})
                noise = base_f - F(eq, set(support) | {j})
                ratio = np.inf if noise <= 0 else gain / noise
                best = max(best, ratio)
                if best >= thr:
                    return None
            return base_sse  # stop: makes sse <= floor true
        path, _, ends = q6.growth_path_with_end(designs, targets, end)
        for eq in range(cell['dim']):
            true = set(truth[eq])
            hist = [{i+1 for i in p['support'][eq]} for p in path]
            reached = next((i for i, s in enumerate(hist) if true <= s), None)
            final = hist[-1] if hist else set()
            rows.append(dict(cell_id=cell['cell_id'], stratum=cell['stratum'], sigma=cell['sigma'], rho=cell['rho'],
                             rule=name, eq=eq+1, end_reason=ends[eq]['end_reason'], states=len(path),
                             superset=reached is not None, exact=any(true == s for s in hist),
                             extra_at_end=len(final - true), final_size=len(final)))
    return rows


if __name__ == '__main__':
    payload = json.loads(q6.Q5.read_text(encoding='utf8'))
    export = next((q6.ROOT/n).parent for n in payload['input_sha256'] if n.endswith('/index.csv'))
    sup = json.loads((q6.ROOT/'studies/regression/phase_c_support.json').read_text(encoding='utf8'))
    truth = {s['system_id']: s['support_idxs'] for s in sup['systems'] if s.get('representability') == 'exact'}
    jobs = [(c, export, truth[c['system_id']]) for c in payload['cells']]
    with ProcessPoolExecutor(10) as ex:
        out = [r for rs in ex.map(job, jobs, chunksize=4) for r in rs]
    pd.DataFrame(out).to_csv(sys.argv[1], index=False)
    print('rows', len(out))
