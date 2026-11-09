"""Data for the WISP process page (explainer/wisp/process/), scene by scene.

Every number the page shows is computed here with the frozen Q6/Q7 functions on recorded observations,
or copied from the frozen Q9 runner's C1000 refit records. The page itself only draws.

Running example: system 3 (logistic growth), IC set 1, sigma = 0.03, realization 0.
Coupled example: system 27 (Lotka-Volterra), IC set 2, sigma = 0.03, realization 0.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / 'analysis/scripts/aggregate'))
from build_wisp_explainer_data import read_observations  # noqa: E402
import build_sideproject_q6_paths as q6  # noqa: E402
from build_sideproject_q7_paths import THRESHOLDS  # noqa: E402

PATHS = ROOT / 'outputs/sideproject_q9_inputs/grid/q9_paths.json'
OUT = ROOT / 'explainer/wisp/process/data.json'
THRESHOLD = THRESHOLDS['chi2_0.01']
NU = 0.5
EXAMPLES = {
    'logistic': dict(cell='sys0003_ic1_s0.03_r0_n1', clean='sys0003_ic1_s0_r0_n1', other='sys0003_ic2_s0_r0_n1',
                     refit=ROOT / 'explainer/wisp/data/logistic_c1000_refit_sys0003_ic1_s0.03_r0_n1.jsonl',
                     names=['1', 'u', 'u²', 'u³', 'sin u', 'cos u'], states=['u'],
                     truth=[{'u': 0.79, 'u²': -0.79 * 0.0134589502018843}]),
    'lv': dict(cell='sys0027_ic2_s0.03_r0_n2', clean='sys0027_ic2_s0_r0_n1', other='sys0027_ic1_s0_r0_n1',
               refit=ROOT / 'explainer/wisp/data/lv_c1000_refit_sys0027_ic2_s0.03_r0_n2.jsonl',
               names=['1', 'x', 'y', 'x²', 'y²', 'x·y', 'x³', 'y³', 'sin x', 'cos x', 'sin y', 'cos y'],
               states=['x', 'y'], truth=[{'x': 1.84, 'x·y': -1.45}, {'y': -3.0, 'x·y': 1.62}]),
}
FOCUS_POINT = 140   # noise scene: one observed point with its nine neighbours


def g(v, d=6):
    """Presentation rounding for curves only; decisions are taken on unrounded numbers."""
    return None if v is None or not math.isfinite(v) else float(f'{v:.{d}g}')


def library(names):
    f = {'1': lambda u: 1.0, 'u': lambda u: u[0], 'u²': lambda u: u[0]**2, 'u³': lambda u: u[0]**3,
         'sin u': lambda u: math.sin(u[0]), 'cos u': lambda u: math.cos(u[0]),
         'x': lambda u: u[0], 'y': lambda u: u[1], 'x²': lambda u: u[0]**2, 'y²': lambda u: u[1]**2,
         'x·y': lambda u: u[0]*u[1], 'x³': lambda u: u[0]**3, 'y³': lambda u: u[1]**3,
         'sin x': lambda u: math.sin(u[0]), 'cos x': lambda u: math.cos(u[0]),
         'sin y': lambda u: math.sin(u[1]), 'cos y': lambda u: math.cos(u[1])}
    return [f[n] for n in names]


def simulate(funcs, support, params, x0, t):
    coefs, i = [], 0
    for eq in support:
        coefs.append([(j, params[i + n]) for n, j in enumerate(eq)])
        i += len(eq)
    sol = solve_ivp(lambda _, u: [sum(c * funcs[j](u) for j, c in eq) for eq in coefs], (t[0], t[-1]), list(x0),
                    t_eval=t, rtol=1e-10, atol=1e-10, method='DOP853')
    y = np.full((len(t), len(x0)), np.nan)
    y[:sol.y.shape[1]] = sol.y.T
    return y


def r2(truth, model):
    if not np.isfinite(model).all():
        return None
    return float(1 - np.sum((truth - model)**2) / np.sum((truth - truth.mean(axis=0))**2))


def noise_detail(t, x):
    """The estimator of q6.estimate_noise_variance, unrolled to expose residual and leverage per point."""
    n = len(t)
    rows = []
    for i in range(n):
        start = min(max(i - 4, 0), n - 9)
        z = t[start:start+9] - t[i]
        scale = np.max(np.abs(z))
        a = np.vander(z / scale, 4, increasing=True)
        u, _, _ = np.linalg.svd(a, full_matrices=False)
        fitted = u @ (u.T @ x[start:start+9, 0])
        lev = float(u[i-start] @ u[i-start])
        res = float(x[i, 0] - fitted[i-start])
        rows.append(dict(start=start, r=res, h=lev, corrected=res / math.sqrt(1 - lev)))
    sq = np.array([r['corrected']**2 for r in rows])
    var = np.array([sq[max(i-10, 0):min(i+11, n)].mean() for i in range(n)])
    check = q6.estimate_noise_variance(t, x)[:, 0]
    assert np.allclose(var, check, rtol=1e-12, atol=0), 'unrolled estimator differs from Q6'
    i = FOCUS_POINT
    st = rows[i]['start']
    z = t[st:st+9] - t[i]
    scale = np.max(np.abs(z))
    coef = np.linalg.lstsq(np.vander(z / scale, 4, increasing=True), x[st:st+9, 0], rcond=None)[0]
    fine = np.linspace(t[st], t[st+8], 60)
    poly = np.vander((fine - t[i]) / scale, 4, increasing=True) @ coef
    return dict(r=[r['r'] for r in rows], h=[r['h'] for r in rows], corrected=[r['corrected'] for r in rows],
                variance=var.tolist(), focus=dict(index=i, start=st, poly_t=fine.tolist(), poly=poly.tolist(),
                                                   r=rows[i]['r'], h=rows[i]['h'], corrected=rows[i]['corrected'],
                                                   variance=float(var[i]),
                                                   window21=[max(i-10, 0), min(i+11, n)]))


def path_trace(designs, targets, operators, names):
    """growth_path_with_end with the Q7 stop, plus the stop statistics at every visited state."""
    cache = {}

    def floor(eq, support):
        key = eq, tuple(sorted(support))
        if key not in cache:
            cache[key] = q6.projected_noise_floor(designs[eq], support, operators[eq])
        return cache[key]
    fits = [q6.WeakFit(a, b) for a, b in zip(designs, targets)]

    def stop_table(eq, support):
        sse, fl = fits[eq].sse(support), floor(eq, support)
        out = []
        for term in sorted(set(range(fits[eq].p)) - set(support)):
            ext = set(support) | {term}
            actual, noise = sse - fits[eq].sse(ext), fl - floor(eq, ext)
            out.append(dict(term=names[term], actual=actual, noise=noise,
                            ratio=None if noise <= 0 else actual / noise,
                            passes=bool(noise <= 0 or actual / noise >= THRESHOLD)))
        return dict(sse=sse, floor=fl, stops=not any(r['passes'] for r in out), rows=out)

    def end(eq, fit, support):
        return None if not stop_table(eq, support)['stops'] else fit.sse(support)

    path, log, ends = q6.growth_path_with_end(designs, targets, end)
    states = [[[] for _ in fits]] + [p['support'] for p in path]
    stops = [[stop_table(e, s[e]) for e in range(len(fits))] for s in states]
    weak = []
    for s in states:
        eqs = []
        for e, sup in enumerate(s):
            coef, sse = q6.weak_coefficients(designs[e], targets[e], sorted(sup))
            eqs.append(dict(terms=[names[j] for j in sorted(sup)], coefficients=[float(c) for c in coef],
                            sse=float(sse), share=1 - float(sse) / fits[e].b_norm2))
        weak.append(eqs)
    steps = []
    for entry, p in zip(log, path):
        steps.append(dict(step=p['step'], origin=p['origin'],
                          added=dict(equation=entry['addition']['equation'] - 1,
                                     term=names[entry['addition']['basis_index'] - 1], gain=entry['addition']['gain']),
                          gains=[dict(equation=x['equation'] - 1, term=names[x['basis_index'] - 1], gain=x['gain'])
                                 for x in entry['gains']],
                          backward=[dict(checks=[dict(equation=c['equation'] - 1, term=names[c['basis_index'] - 1],
                                                      cost=c['cost'], qualifies=c['qualifies']) for c in b['checks']],
                                         removed=None if b['removed'] is None else
                                         dict(equation=b['removed']['equation'] - 1,
                                              term=names[b['removed']['basis_index'] - 1], cost=b['removed']['cost']))
                                    for b in entry['backward_checks']],
                          support=[[names[j] for j in sorted(eq)] for eq in p['support']]))
    return path, dict(states=[[[names[j] for j in sorted(eq)] for eq in s] for s in states], weak=weak,
                      stops=stops, steps=steps, ends=ends, b_norm2=[f.b_norm2 for f in fits])


def example(key, spec, cells, used, scenes):
    cell = cells[spec['cell']]
    assert cell['arm'] == 'C1000'
    t, x = read_observations(cell, used)
    _, clean = read_observations(cells[spec['clean']], used)
    _, other = read_observations(cells[spec['other']], used)
    names, dim = spec['names'], len(spec['states'])
    terms = q6.phasec_basis(dim)
    assert len(terms) == len(names)
    designs, targets = zip(*(q6.build_design(t, x, e, 'weak', terms)[:2] for e in range(dim)))
    variance = q6.estimate_noise_variance(t, x)
    incidence, _ = q6.weak_noise_operators(t)
    operators = [incidence.multiply(np.sqrt(variance[:, e])[None, :]).tocsr() for e in range(dim)]
    path, trace = path_trace(designs, targets, operators, names)
    recorded = [[[j - 1 for j in eq] for eq in c['active_idxs']] for c in cell['candidates']]
    computed = [[sorted(eq) for eq in p['support']] for p in path]
    assert computed == [[sorted(eq) for eq in s] for s in recorded], ('path differs from the recorded Q9 path',
                                                                     computed, recorded)

    funcs = library(names)
    refit = {r['candidate_id']: r for r in map(json.loads, spec['refit'].read_text(encoding='utf8').splitlines()) if r}
    N = x.size
    cands = []
    for c in cell['candidates']:
        r = refit[c['candidate_id']]
        assert r['arm'] == 'C1000' and r['ic_mode'] == 'estimated' and r['start'] == 'weak' and r['refit']
        sup = [[j - 1 for j in eq] for eq in c['active_idxs']]
        k = sum(map(len, sup))
        assert len(r['params']) == k
        p0 = [float(v) for eq in c['equations'] for v in eq['coefficients']]
        mse = r['estimated_ic_training_mse']
        start_curve = simulate(funcs, sup, p0, x[0], t)
        fit_curve = simulate(funcs, sup, r['params'], r['fitted_initial_state'], t)
        start_mse = None if not np.isfinite(start_curve).all() else float(np.mean((start_curve - x)**2))
        recon = simulate(funcs, sup, r['params'], clean[0], t)
        gen = simulate(funcs, sup, r['params'], other[0], t)
        cands.append(dict(id=c['candidate_id'], step=c['step'], origin=c['origin'],
                          support=[[names[j] for j in eq] for eq in sup], k=k,
                          weak=p0, params=r['params'], x0=r['fitted_initial_state'], observed_x0=x[0].tolist(),
                          start_mse=start_mse, mse=mse, loss_evals=r['fit_meta']['loss_evals'],
                          bic=N * math.log(mse) + (k + dim) * math.log(N), penalty=(k + dim) * math.log(N),
                          fit_term=N * math.log(mse),
                          start_curve=[[g(v) for v in row] for row in start_curve],
                          fit_curve=[[g(v) for v in row] for row in fit_curve],
                          recon_r2=r2(clean, recon), gen_r2=r2(other, gen),
                          recon_curve=[[g(v) for v in row] for row in recon],
                          gen_curve=[[g(v) for v in row] for row in gen]))
    win = min(cands, key=lambda c: c['bic'])
    out = dict(cell=spec['cell'], sigma=cell['sigma'], names=names, states=spec['states'], truth=spec['truth'],
               t=t.tolist(), y=x.tolist(), clean=clean.tolist(), other=other.tolist(), N=N, n=len(t), dim=dim,
               windows=len(targets[0]), lengths=[1, 2, 4, 8, 16], threshold=THRESHOLD, nu=NU,
               path=trace, candidates=cands, winner=win['id'],
               sources=dict(paths=str(PATHS.relative_to(ROOT)), refit=str(spec['refit'].relative_to(ROOT))))
    if key == 'logistic':
        out['noise'] = noise_detail(t, x)
        a, b = np.asarray(designs[0]), np.asarray(targets[0])
        # Window table of scenes 06-07: the first windows of every length, with their G rows.
        rows, offset = [], 0
        for L in out['lengths']:
            for s in (0, 1, 2):
                rows.append(dict(L=L, start=s, end=s + L, b=float(b[offset + s]), G=a[offset + s].tolist()))
            offset += len(t) - L
        out['window_rows'] = rows
        # Scene 15: one window's target variance from its two endpoints (diagonal of C = D Sigma D').
        i0, i1 = 100, 104
        v = out['noise']['variance']
        out['window_noise'] = dict(start=i0, end=i1, var_start=v[i0], var_end=v[i1], var_b=v[i0] + v[i1])
    return out


def main():
    used, scenes = set(), {}
    cells = {c['cell_id']: c for c in json.loads(PATHS.read_bytes())['cells']}
    data = {k: example(k, s, cells, used, scenes) for k, s in EXAMPLES.items()}
    data['observations'] = sorted(str(p.relative_to(ROOT)) for p in used)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    def clean(o):
        if isinstance(o, float):
            return o if math.isfinite(o) else None
        if isinstance(o, list):
            return [clean(v) for v in o]
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        return o
    OUT.write_text(json.dumps(clean(data), separators=(',', ':')), encoding='utf8')
    for k in EXAMPLES:
        d = data[k]
        print(k, 'states', d['path']['states'], 'winner', d['winner'])
        for c in d['candidates']:
            print('  ', c['id'], c['support'], 'bic', round(c['bic'], 2), 'mse', round(c['mse'], 4), 'recon', c['recon_r2'], 'gen', c['gen_r2'])
    print('wrote', OUT, OUT.stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
