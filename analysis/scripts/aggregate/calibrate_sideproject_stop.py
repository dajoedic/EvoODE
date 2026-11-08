"""Q-Cal: calibration of the WISP chi-square stop at the true support (protocol _qcal.md).

Report only. No path, no fit, no simulation. Writes per-pair rows and stratum tables to
analysis/data/sideproject_residual_growth/stop_calibration/.
"""
from __future__ import annotations
import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd

import build_sideproject_q6_paths as q6

ROOT = q6.ROOT
PATHS = ROOT / 'outputs/sideproject_q9_inputs/grid/q9_paths.json'
SUPPORT = ROOT / 'studies/regression/phase_c_support.json'
OUT = ROOT / 'analysis/data/sideproject_residual_growth/stop_calibration'
T1, T2 = 6.635, 10.828


def stratum(system_id, dim):
    if dim == 3:
        return 'dim3_feasible' if system_id in (52, 61) else 'dim3_infeasible'
    return f'dim{dim}'


def unit(a):
    n = np.linalg.norm(a, axis=0)
    return a / np.where(n > 0, n, 1.)


def sse(design, target, support):
    if not support:
        return float(target @ target)
    a = unit(design[:, sorted(support)])
    coef, *_ = np.linalg.lstsq(a, target, rcond=None)
    r = target - a @ coef
    return float(r @ r)


def col_r2(design, j, support):
    y = unit(design[:, [j]])[:, 0]
    if not support:
        return 0.
    a = unit(design[:, sorted(support)])
    coef, *_ = np.linalg.lstsq(a, y, rcond=None)
    r = y - a @ coef
    return 1. - float(r @ r)


def ratios(design, target, op, support, j):
    gain = sse(design, target, support) - sse(design, target, support | {j})
    noise = q6.projected_noise_floor(design, sorted(support), op) - \
        q6.projected_noise_floor(design, sorted(support | {j}), op)
    return np.inf if noise <= 0 else gain / noise


def job(args):
    cell, clean, truth = args
    t, x = q6.read_index_cell(q6.EXPORT, pd.Series(cell['export']))
    if q6.data_sha(pd.Series(cell['export'])) != cell['observed_data_sha256']:
        raise ValueError('hash mismatch ' + cell['cell_id'])
    ct, cx = q6.read_index_cell(q6.EXPORT, pd.Series(clean['export']))
    idx = np.searchsorted(ct, t)
    if not np.allclose(ct[idx], t, rtol=0, atol=1e-12):
        raise ValueError('observed times not on clean grid ' + cell['cell_id'])
    dim = cell['dim']
    terms = q6.phasec_basis(dim)
    names = [tm.name for tm in terms]
    var_hat = q6.estimate_noise_variance(t, x)
    var_true = (cell['sigma'] * cx[idx]) ** 2
    incidence, _ = q6.weak_noise_operators(t)
    rows = []
    for e in range(dim):
        design, target = q6.build_design(t, x, e, 'weak', terms)[:2]
        ops = {'hat': incidence.multiply(np.sqrt(var_hat[:, e])[None, :]).tocsr(),
               'oracle': incidence.multiply(np.sqrt(var_true[:, e])[None, :]).tocsr()}
        s_true = {i - 1 for i in truth['support_idxs'][e]}
        assert [names[i] for i in sorted(s_true)] == sorted(truth['support_terms'][e], key=names.index)
        base = dict(cell_id=cell['cell_id'], system_id=cell['system_id'], dim=dim,
                    stratum=stratum(cell['system_id'], dim), ic=cell['initial_condition_set'], sigma=cell['sigma'],
                    rho=cell['rho'], realization=cell['realization'], equation=e + 1, p=len(terms), k_true=len(s_true))
        for j in sorted(set(range(len(terms))) - s_true):
            rows.append(dict(base, kind='null', term=names[j], col_r2=col_r2(design, j, s_true),
                             **{f'r_{a}': ratios(design, target, op, s_true, j) for a, op in ops.items()}))
        for i in sorted(s_true):
            rest = s_true - {i}
            rows.append(dict(base, kind='true', term=names[i], col_r2=col_r2(design, i, rest),
                             **{f'r_{a}': ratios(design, target, op, rest, i) for a, op in ops.items()}))
    return rows


def boot(df, col, rng, b=2000):
    per = df.groupby('system_id')[col].agg(['sum', 'count'])
    s, n = per['sum'].to_numpy(float), per['count'].to_numpy(float)
    i = rng.integers(0, len(s), size=(b, len(s)))
    v = s[i].sum(1) / n[i].sum(1)
    return s.sum() / n.sum(), np.quantile(v, .025), np.quantile(v, .975)


def tables(df):
    rng = np.random.default_rng(20261108)
    out = []
    df = df.copy()
    for a in ('hat', 'oracle'):
        for t, tag in ((T1, '6.635'), (T2, '10.828')):
            df[f'x_{a}_{tag}'] = df[f'r_{a}'] >= t
    keys = [('all', lambda d: d)] + [(f'sigma={s}', (lambda s: lambda d: d[d.sigma == s])(s)) for s in sorted(df.sigma.unique())] \
        + [(f'rho={r}', (lambda r: lambda d: d[d.rho == r])(r)) for r in sorted(df.rho.unique())]
    for st, g0 in [('all', df)] + list(df.groupby('stratum')):
        for kname, f in keys:
            g = f(g0)
            null, true = g[g.kind == 'null'], g[g.kind == 'true']
            row = dict(stratum=st, subset=kname, n_null_pairs=len(null), n_true_pairs=len(true))
            for a in ('hat', 'oracle'):
                for tag in ('6.635', '10.828'):
                    row[f'N1_{a}_{tag}'], row[f'N1_{a}_{tag}_lo'], row[f'N1_{a}_{tag}_hi'] = boot(null, f'x_{a}_{tag}', rng)
                    row[f'P1_{a}_{tag}'] = true[f'x_{a}_{tag}'].mean()
                eq = null.groupby(['cell_id', 'equation']).agg(m=(f'r_{a}', 'max'), p=('p', 'first'), k=('k_true', 'first'),
                                                              system_id=('system_id', 'first'))
                row[f'N2_{a}'] = (eq.m < T1).mean()
                row['N2_nominal'] = (0.99 ** (eq.p - eq.k)).mean()
                row[f'median_null_ratio_{a}'] = null[f'r_{a}'].median()
            out.append(row)
    coll = []
    for b, (lo, hi) in {'<0.9': (-1, .9), '0.9-0.99': (.9, .99), '>=0.99': (.99, 2)}.items():
        g = df[(df.kind == 'null') & (df.col_r2 >= lo) & (df.col_r2 < hi)]
        coll.append(dict(bin=b, n=len(g), **{f'N1_{a}': (g[f'r_{a}'] >= T1).mean() for a in ('hat', 'oracle')}))
    return pd.DataFrame(out), pd.DataFrame(coll)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--limit', type=int)
    a = ap.parse_args()
    cells = json.loads(PATHS.read_bytes())['cells']
    sup = {s['system_id']: s for s in json.loads(SUPPORT.read_bytes())['systems']
           if s.get('representability') == 'exact' and s.get('status') == 'ok'}
    assert len(sup) == 30
    clean = {(c['system_id'], c['initial_condition_set']): c for c in cells if c['sigma'] == 0 and c['rho'] == 0}
    todo = [c for c in cells if c['system_id'] in sup and c['sigma'] > 0]
    todo.sort(key=lambda c: c['cell_id'])
    assert len(todo) == 1800, len(todo)
    if a.limit:
        todo = todo[:a.limit]
    jobs = [(c, clean[c['system_id'], c['initial_condition_set']], sup[c['system_id']]) for c in todo]
    with ProcessPoolExecutor(a.workers) as ex:
        rows = [r for rs in ex.map(job, jobs, chunksize=4) for r in rs]
    df = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = '_smoke' if a.limit else ''
    df.to_csv(OUT / f'pairs{suffix}.csv', index=False)
    t, c = tables(df)
    t.to_csv(OUT / f'rates{suffix}.csv', index=False)
    c.to_csv(OUT / f'collinearity{suffix}.csv', index=False)
    print(len(todo), 'cells', len(df), 'pairs')


if __name__ == '__main__':
    main()
