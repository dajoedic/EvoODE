"""Worked example for the manuscript: one Q8 C1000 cell traced end to end.

Rebuilds the WISP growth path with the frozen Q8 builder (bit-identity checked
against the stored path), recomputes per step the largest gain/noise ratio per
equation (the Q7 stop statistic), collects the stored C1000 fits of every
candidate, and simulates truth, chosen model and the WSINDy model from the
clean initial conditions for plotting. Writes data/example.json.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis/scripts/aggregate'))
import build_sideproject_q8_paths as q8b  # noqa: E402
import build_sideproject_q6_paths as q6  # noqa: E402
import build_sideproject_q7_paths as q7  # noqa: E402

CELL = sys.argv[1] if len(sys.argv) > 1 else 'sys0027_ic2_s0.05_r0.5_n1'
ARM = 'C1000'
OUT = Path(__file__).resolve().parent / 'data'
REC = ROOT / 'outputs/sideproject_q8_512dd5bd534530327b1f5fed3e7892a1e0950016/out_sneak_2026-11-07'

paths = {(c['cell_id'], c['arm']): c for c in
         json.loads((ROOT / 'outputs/sideproject_q8_inputs/grid/q8_paths.json').read_bytes())['cells']}
cell = paths[CELL, ARM]
rebuilt = q8b.build_path(dict(cell), 'q7')
assert [c['active_idxs'] for c in rebuilt['candidates']] == [c['active_idxs'] for c in cell['candidates']]

t, x = q6.read_index_cell(q8b.EXPORT, pd.Series(cell['export']))
terms = q6.phasec_basis(cell['dim'])
names = None
designs, targets = zip(*(q6.build_design(t, x, e, 'weak', terms)[:2] for e in range(cell['dim'])))
variance = q6.estimate_noise_variance(t, x)
incidence, _ = q6.weak_noise_operators(t)
ops = [incidence.multiply(np.sqrt(variance[:, e])[None, :]).tocsr() for e in range(cell['dim'])]


def sse(eq, support):
    idx = sorted(support)  # 0-based
    b = targets[eq]
    if not idx:
        return float(b @ b)
    a = designs[eq][:, idx]
    coef, *_ = np.linalg.lstsq(a, b, rcond=None)
    r = b - a @ coef
    return float(r @ r)


def stat(eq, support):
    """Largest gain/noise ratio over the remaining terms and its argmax."""
    s0, f0 = sse(eq, support), q6.projected_noise_floor(designs[eq], sorted(support), ops[eq])
    best = (-np.inf, None)
    for j in sorted(set(range(designs[eq].shape[1])) - set(support)):
        ext = set(support) | {j}
        n = f0 - q6.projected_noise_floor(designs[eq], sorted(ext), ops[eq])
        ratio = np.inf if n <= 0 else (s0 - sse(eq, ext)) / n
        best = max(best, (ratio, j))
    return best, s0, f0


steps = []
supports = [[[], []]] + [c['active_idxs'] for c in cell['candidates']]
for i, sup in enumerate(supports):
    row = dict(step=i, support=sup, eq=[])
    for e in range(cell['dim']):
        (ratio, j), s0, f0 = stat(e, [i - 1 for i in sup[e]])  # stored indices are 1-based
        row['eq'].append(dict(max_ratio=float(ratio), best_term=int(j) + 1 if j is not None else None,
                              sse=s0, sse_norm=s0 / float(targets[e] @ targets[e]), floor=f0))
    steps.append(row)

term_names = {}
for c in cell['candidates']:
    for eq in c['equations']:
        for i, n in zip(eq['basis_indices'], eq['term_names']):
            term_names[i] = n

records = {}
for fn in REC.glob('*.jsonl'):
    with fn.open() as fh:
        for line in fh:
            if CELL in line and f'"{ARM}"' in line:
                r = json.loads(line)
                if r['cell_id'] == CELL and r['arm'] == ARM:
                    records[r['candidate_id']] = r
assert len(records) == len(cell['candidates']), (len(records), len(cell['candidates']))

N = records[cell['candidates'][0]['candidate_id']]['training']['n_samples']
cands = []
for c in cell['candidates']:
    r = records[c['candidate_id']]
    k = sum(len(e) for e in c['active_idxs'])
    mse = r['optimizer_loss']
    cands.append(dict(candidate_id=c['candidate_id'], step=c['step'], origin=c['origin'], k=k,
                      support=[[term_names[i] for i in e] for e in c['active_idxs']], active_idxs=c['active_idxs'],
                      weak_bic=c['weak_bic'], mse=mse, traj_bic=N * np.log(mse) + (k + cell['dim']) * np.log(N),
                      params=r['params'], ic=r['fitted_initial_state'],
                      rec_r2=r['reconstruction']['r2_variance_weighted'],
                      gen_r2=r['generalization']['r2_variance_weighted'],
                      train_r2=r['training']['r2_variance_weighted']))
chosen = min(cands, key=lambda c: c['traj_bic'])

# truth and clean ICs
sysdef = json.loads((ROOT / 'benchmarks/data/strogatz_extended.json').read_bytes())[cell['system_id'] - 1]
ic_train = sysdef['init'][cell['initial_condition_set'] - 1]
ic_test = sysdef['init'][2 - cell['initial_condition_set']]
consts = sysdef['consts'][0]


def truth_rhs(_, u):
    x0, x1 = u
    c0, c1, c2, c3 = consts
    return [x0 * (c0 - c1 * x1), -x1 * (c2 - c3 * x0)]


def term_fn(name):
    return lambda u: eval(name.replace('^', '**').replace('u1', 'U[0]').replace('u2', 'U[1]'),
                          {'sin': np.sin, 'cos': np.cos}, {'U': u})


def model_rhs(active, params, namemap):
    fns = [[term_fn(namemap[i]) for i in eq] for eq in active]
    split = np.cumsum([0] + [len(eq) for eq in active])

    def f(_, u):
        return [sum(params[split[e] + j] * fn(u) for j, fn in enumerate(fns[e])) for e in range(len(active))]
    return f


tt = np.linspace(0, 10, 1000)


def sim(rhs, u0):
    s = solve_ivp(rhs, (0, 10), u0, t_eval=tt, rtol=1e-10, atol=1e-10, method='DOP853')
    y = np.full((len(tt), len(u0)), np.nan)
    y[:s.y.shape[1]] = s.y.T
    return y


truth_train, truth_test = sim(truth_rhs, ic_train), sim(truth_rhs, ic_test)
f_w = model_rhs(chosen['active_idxs'], chosen['params'], term_names)
wisp_train, wisp_test = sim(f_w, ic_train), sim(f_w, ic_test)

# WSINDy (MATLAB original, W1-interp because rho = 0.5) on the same cell
ws = pd.read_csv(ROOT / 'outputs/sideproject_q5w_wsindy/w1_interp_full_matlab/details.csv', low_memory=False)
ws = ws[(ws.system_id == cell['system_id']) & (ws.source_initial_condition_set == cell['initial_condition_set'])
        & (ws.noise_sigma == cell['sigma']) & (ws.subsample_rho == cell['rho'])
        & (ws.noise_realization == cell['realization']) & ws.q5w_configuration.str.endswith(':L-Q5')].iloc[0]
ws_coef = json.loads(ws.sindy_coefficients_active)
ws_names = sorted({d['term'] for eq in ws_coef for d in eq})


def ws_term(name):
    expr = name.replace('^', '**').replace('x0', 'U[0]').replace('x1', 'U[1]').replace(' ', '*')
    return lambda u: eval(expr, {'sin': np.sin, 'cos': np.cos}, {'U': u})


def ws_rhs(_, u):
    return [sum(d['coefficient'] * ws_term(d['term'])(u) for d in eq) for eq in ws_coef]


ws_train, ws_test = sim(ws_rhs, ic_train), sim(ws_rhs, ic_test)

out = dict(cell=CELL, arm=ARM, system=sysdef['eq_description'], truth=sysdef['substituted'][0],
           sigma=cell['sigma'], rho=cell['rho'], N=N, observed_t=t.tolist(), observed_x=x.tolist(),
           term_names={str(k): v for k, v in term_names.items()}, steps=steps, candidates=cands,
           chosen=chosen['candidate_id'], tt=tt.tolist(),
           truth_train=truth_train.tolist(), truth_test=truth_test.tolist(),
           wisp_train=wisp_train.tolist(), wisp_test=wisp_test.tolist(),
           ws_train=ws_train.tolist(), ws_test=ws_test.tolist(), ws_coef=ws_coef,
           ws_struct=bool(ws.sindy_structure_hit_pruned), ws_rec=float(ws.reconstruction_r2_variance_weighted),
           ws_gen=float(ws.generalization_r2_variance_weighted), ic_train=ic_train, ic_test=ic_test,
           variance_mean=variance.mean(0).tolist())
(OUT / 'example.json').write_text(json.dumps(out, default=float))
for s in steps:
    print(s['step'], s['support'], [(round(e['max_ratio'], 2), e['best_term']) for e in s['eq']])
for c in cands:
    print(c['candidate_id'], c['k'], c['support'], round(c['traj_bic'], 1), round(c['weak_bic'], 1),
          c['rec_r2'], c['gen_r2'], np.round(c['params'], 3))
print('chosen', chosen['candidate_id'], 'WSINDy', ws_coef, ws.sindy_structure_hit_pruned,
      ws.reconstruction_r2_variance_weighted, ws.generalization_r2_variance_weighted)
