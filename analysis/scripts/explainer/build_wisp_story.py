"""Build the WISP story page (explainer/wisp/dist/wisp_story.html).

One recorded Lotka-Volterra cell (system 27, IC 1, sigma 0.03, rho 0, realization 1) threads through the page:
- path (weak-form growth, FoBa checks, stop tests) from explainer/wisp/data/live.json (data-only, arm-independent);
- candidate fits from the local C1000 refit of that cell with the frozen Q9 runner
  (explainer/wisp/story/data/lv_c1000_refit_<cell>.jsonl, copied from outputs/wisp_explainer_lv_c1000/);
- part C rates from explainer/wisp/story/data/results_q8_prelim.json (extract_wisp_story_results.py).
Display curves of the candidates are re-integrated here (scipy, 1e-10) from the recorded parameters and fitted
initial states; every score shown on the page comes from the records, never from this re-integration.
"""
import json, math
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[3]
STORY = ROOT / 'explainer/wisp/story'
CELL = 'sys0027_ic1_s0.03_r0_n1'
REFIT = STORY / 'data' / f'lv_c1000_refit_{CELL}.jsonl'  # copy of outputs/wisp_explainer_lv_c1000/<cell>.jsonl (Q9 runner, laptop, 2026-11-07)
OUT = ROOT / 'explainer/wisp/dist/wisp_story.html'

TERMS = ['1', 'H', 'F', 'H²', 'F²', 'H·F', 'H³', 'F³', 'sin H', 'cos H', 'sin F', 'cos F']
FUNCS = [lambda h, f: 1.0, lambda h, f: h, lambda h, f: f, lambda h, f: h * h, lambda h, f: f * f, lambda h, f: h * f,
         lambda h, f: h ** 3, lambda h, f: f ** 3, lambda h, f: math.sin(h), lambda h, f: math.cos(h),
         lambda h, f: math.sin(f), lambda h, f: math.cos(f)]


def r(x, n=5):
    return [round(float(v), n) for v in x]


def simulate(support, params, x0, t):
    coefs, i = [], 0
    for eq in support:
        coefs.append([(j, params[i + n]) for n, j in enumerate(eq)])
        i += len(eq)

    def rhs(_, u):
        return [sum(c * FUNCS[j - 1](u[0], u[1]) for j, c in eq) for eq in coefs]
    sol = solve_ivp(rhs, (t[0], t[-1]), x0, t_eval=t, rtol=1e-10, atol=1e-10, method='DOP853')
    if not sol.success or sol.y.shape[1] != len(t):
        y = np.full((2, len(t)), np.nan)
        y[:, :sol.y.shape[1]] = sol.y
        return y
    return sol.y


def lv_example():
    live = json.loads((ROOT / 'explainer/wisp/data/live.json').read_text(encoding='utf8'))
    ex = next(e for e in live['examples'] if e['cell_id'] == CELL)
    t = np.array(ex['observed']['t'])
    obs = np.array(ex['observed']['x'])
    c1, c2 = np.array(ex['clean']['reconstruction']['x']), np.array(ex['clean']['generalization']['x'])
    path = []
    for p in ex['path']:
        add = p['addition']
        last = p['backward_checks'][-1]
        path.append(dict(step=p['step'], support=p['support'],
                         add=dict(eq=add['equation'], idx=add['basis_index'], gain=add['gain']),
                         gains=[dict(eq=g['equation'], idx=g['basis_index'], gain=g['gain']) for g in p['gains']],
                         checks=[dict(eq=c['equation'], idx=c['basis_index'], cost=c['cost'], out=c['qualifies'])
                                 for c in last['checks']],
                         removed=last['removed'],
                         tests=[[dict(idx=b['term'], ratio=b['ratio']) for b in eq['blocks']] for eq in p['tests']]))
    stop = dict(threshold=ex['stop']['threshold'],
                eqs=[[dict(idx=b['term'], ratio=b['ratio']) for b in eq['blocks']] for eq in ex['stop']['equations']])
    refit = [json.loads(line) for line in REFIT.read_text(encoding='utf8').splitlines() if line.strip()]
    assert [c['candidate_id'] for c in refit] == [c['row']['candidate_id'] for c in ex['candidates']]
    assert all(c['arm'] == 'C1000' and c['ic_mode'] == 'estimated' and c['coefficient_bound'] == 1000 for c in refit)
    truth = ex['truth']
    ic2 = truth['other_initial']
    cands = []
    for c, old in zip(refit, ex['candidates']):
        support = c['pruned_active_idxs']
        support = json.loads(support) if isinstance(support, str) else support
        assert support == json.loads(old['row']['active_idxs'])
        k = sum(map(len, support))
        mse = c['estimated_ic_training_mse']
        fit = simulate(support, c['params'], c['fitted_initial_state'], t)
        pred = simulate(support, c['params'], ic2, t)
        cands.append(dict(id=c['candidate_id'], support=support, params=c['params'], ic=c['fitted_initial_state'],
                          mse=mse, k=k, bic=2 * len(t) * math.log(mse) + k * math.log(2 * len(t)),
                          rec=c['reconstruction']['r2_variance_weighted'], gen=c['generalization']['r2_variance_weighted'],
                          train=c['training']['r2_variance_weighted'],
                          fit=dict(H=r(fit[0], 4), F=r(fit[1], 4)), pred=dict(H=r(pred[0], 4), F=r(pred[1], 4))))
    win = min(range(len(cands)), key=lambda i: cands[i]['bic'])
    return dict(cell=CELL, sigma=ex['sigma'], terms=TERMS, t=r(t, 5),
                obs=dict(H=r(obs[:, 0], 4), F=r(obs[:, 1], 4)),
                clean1=dict(H=r(c1[:, 0], 4), F=r(c1[:, 1], 4)), clean2=dict(H=r(c2[:, 0], 4), F=r(c2[:, 1], 4)),
                truth=dict(constants=truth['constants'], support=truth['support'], ic1=truth['initial'], ic2=ic2),
                backward_fraction=live['backward_fraction'], windows=live['windows'],
                path=path, stop=stop, candidates=cands, winner=win)


def build():
    data = dict(lv=lv_example(),
                results=json.loads((STORY / 'data/results_q8_prelim.json').read_text(encoding='utf8')))
    html = (STORY / 'index.html').read_text(encoding='utf8')
    parts = {'<!--STYLE-->': (STORY / 'style.css').read_text(encoding='utf8'),
             '<!--TEXT-->': (STORY / 'text.js').read_text(encoding='utf8'),
             '<!--APP-->': (STORY / 'app.js').read_text(encoding='utf8'),
             '<!--DATA-->': json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('<', '\\u003c')}
    for key, value in parts.items():
        assert html.count(key) == 1, key
        html = html.replace(key, value)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding='utf8')
    lv = data['lv']
    print(json.dumps(dict(output=str(OUT), bytes=OUT.stat().st_size, winner=lv['candidates'][lv['winner']]['id'],
                          bic=[round(c['bic'], 1) for c in lv['candidates']])))


if __name__ == '__main__':
    build()
