"""Make Lotka-Volterra (system 27) the running example of the WISP explorable.

Replaces, in explainer/wisp/data/live.json, only what the chapters read about the running example:
- `teaching`: the observed and clean series of cell sys0027_ic2_s0.03_r0_n2 (target = hares H, with both states);
- `featured[0]` (role `running`): the recorded Q9 path of that cell, split into the hare-equation path that
  chapters 1-4 replay and the joint path, plus every candidate refitted with the frozen Q9 runner (C1000);
- `illustrations[1]`: the benchmark LV trajectory from its first initial condition (hook / meadow).
Everything else in live.json stays as it is. Observations are read only from the C-6 export at the paths the Q9
path file declares, and only when their SHA-256 matches. Display curves are re-integrated from the recorded
parameters (scipy, 1e-10); every score comes from the records.
"""
import argparse, json, math, sys
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_wisp_explainer_data import read_observations, display_arrays  # noqa: E402

CELL = 'sys0027_ic2_s0.03_r0_n2'
PATHS = ROOT / 'outputs/sideproject_q9_inputs/grid/q9_paths.json'
REFIT = ROOT / 'explainer/wisp/data/lv_c1000_refit_sys0027_ic2_s0.03_r0_n2.jsonl'
LIVE = ROOT / 'explainer/wisp/data/live.json'
TERMS = ['1', 'H', 'F', 'H²', 'F²', 'H·F', 'H³', 'F³', 'sin H', 'cos H', 'sin F', 'cos F']
FUNCS = [lambda h, f: 1.0, lambda h, f: h, lambda h, f: f, lambda h, f: h * h, lambda h, f: f * f, lambda h, f: h * f,
         lambda h, f: h ** 3, lambda h, f: f ** 3, lambda h, f: math.sin(h), lambda h, f: math.cos(h),
         lambda h, f: math.sin(f), lambda h, f: math.cos(f)]


def simulate(support, params, x0, t):
    coefs, i = [], 0
    for eq in support:
        coefs.append([(j, params[i + n]) for n, j in enumerate(eq)])
        i += len(eq)
    sol = solve_ivp(lambda _, u: [sum(c * FUNCS[j - 1](u[0], u[1]) for j, c in eq) for eq in coefs],
                    (t[0], t[-1]), list(x0), t_eval=t, rtol=1e-10, atol=1e-10, method='DOP853')
    y = np.full((len(t), 2), np.nan)
    y[:sol.y.shape[1]] = sol.y.T
    return y


def sig5(a):
    """Presentation only: five significant digits for display curves (scores always come from the records)."""
    return [[float(f'{v:.5g}') if math.isfinite(v) else None for v in row] for row in np.asarray(a, dtype=float)]


def two_equation_example(live, cell, t, x, clean, other, joint, refit):
    """Chapter six: the same cell, both equations, built exactly like wisp_examples_x19 builds its examples."""
    import build_sideproject_q6_paths as q6
    from build_sideproject_q7_paths import significance_end, THRESHOLDS
    from aggregate_phaseb_structure_metrics import true_coefficients_for_phasec_terms
    threshold, dim = THRESHOLDS['chi2_0.01'], 2
    terms = q6.phasec_basis(dim)
    designs, targets_weak = zip(*(q6.build_design(t, x, e, 'weak', terms)[:2] for e in range(dim)))
    variance = q6.estimate_noise_variance(t, x)
    incidence, _ = q6.weak_noise_operators(t)
    operators = [incidence.multiply(np.sqrt(variance[:, e])[None, :]).tocsr() for e in range(dim)]
    path, log, ends = q6.growth_path_with_end(designs, targets_weak, significance_end(designs, operators, threshold))
    actual = [[[j + 1 for j in eq] for eq in p['support']] for p in path]
    assert actual == [c['active_idxs'] for c in joint], 'Q6/Q7 path differs from the recorded Q9 path'
    fits = [q6.WeakFit(a, b) for a, b in zip(designs, targets_weak)]

    def tests(support):
        result = []
        for e, (a, fit, op) in enumerate(zip(designs, fits, operators)):
            active = set(support[e]); floor = q6.projected_noise_floor(a, active, op)
            blocks = []
            for j in sorted(set(range(fit.p)) - active):
                noise = floor - q6.projected_noise_floor(a, active | {j}, op)
                gain = fit.sse(active) - fit.sse(active | {j})
                blocks.append(dict(term=j + 1, gain=gain / fit.b_norm2, noise=noise / fit.b_norm2,
                                   ratio=gain / noise if noise > 0 else None, passes=noise <= 0 or gain / noise >= threshold))
            result.append(dict(equation=e + 1, blocks=blocks, stopped=not any(b['passes'] for b in blocks)))
        return result
    before, rounds = [[] for _ in range(dim)], []
    for state, event in zip(path, log, strict=True):
        rounds.append(dict(**event, before=[[j + 1 for j in eq] for eq in before],
                           support=[[j + 1 for j in eq] for eq in state['support']], tests=tests(before)))
        before = state['support']
    exported = []
    for c in joint:
        r = refit[c['candidate_id']]
        sup, params = c['active_idxs'], r['params']
        k, mse, N = sum(map(len, sup)), r['estimated_ic_training_mse'], x.size
        fit = simulate(sup, params, r['fitted_initial_state'], t)
        recon = simulate(sup, params, clean[0], t)
        gen = simulate(sup, params, other[0], t)
        row = dict(candidate_id=c['candidate_id'], cell_id=cell['cell_id'], active_idxs=json.dumps(sup), params=json.dumps(params),
                   k=str(k), mse=repr(mse), n_samples=str(N), step=str(c['step']), origin=c['origin'],
                   raw_exact=str(sup == [[2, 6], [3, 6]]), pruned_exact=str(sup == [[2, 6], [3, 6]]),
                   fitted_initial_state=json.dumps(r['fitted_initial_state']),
                   **{f'{kind}_r2_{w}': repr(r[kind][f'r2_{w}']) for kind in ('reconstruction', 'generalization')
                      for w in ('arithmetic', 'variance_weighted')})
        curves = dict(t=t.tolist(), truth=sig5(clean), model=sig5(recon),
                      generalization=dict(t=t.tolist(), truth=sig5(other), model=sig5(gen)),
                      training=dict(t=t.tolist(), truth=sig5(x), model=sig5(fit)))
        errors = dict(noisy_initial_clean_mse=float(np.mean((fit - clean) ** 2)), true_initial_clean_mse=float(np.mean((recon - clean) ** 2)),
                      noisy_initial_training_mse=float(np.mean((fit - x) ** 2)), true_initial_training_mse=float(np.mean((recon - x) ** 2)))
        exported.append(dict(row=row, active_idxs=sup, params=params, N=N, k=k, mse=mse, bic=N * math.log(mse) + k * math.log(N),
                             penalty=k * math.log(N), curves=curves, unavailable=None,
                             true_initial=dict(t=t.tolist(), truth=sig5(clean), model=sig5(recon)), curve_errors=errors))
    winner = min(exported, key=lambda c: c['bic'])
    system = next(s for s in json.loads((ROOT / 'benchmarks/data/strogatz_extended.json').read_text(encoding='utf8')) if s['id'] == 27)
    labels = live['catalogues'][dim - 1]['terms']
    truth_support = [[2, 6], [3, 6]]
    coefficients = [true_coefficients_for_phasec_terms(eq, dim, [labels[j - 1] for j in sup])
                    for eq, sup in zip(system['substituted'][0], truth_support, strict=True)]
    ic = cell['initial_condition_set']
    return dict(cell_id=cell['cell_id'], system_id=27, dim=dim, sigma=cell['sigma'], terms=labels,
                observed=dict(t=t.tolist(), x=x.tolist()),
                clean=dict(reconstruction=dict(t=t.tolist(), x=clean.tolist()), generalization=dict(t=t.tolist(), x=other.tolist())),
                truth=dict(equations=system['substituted'][0], constants=system['consts'][0], initial=system['init'][ic - 1],
                           other_initial=system['init'][2 - ic], support=truth_support, coefficients=coefficients),
                path=rounds, stop=dict(threshold=threshold, equations=tests(before), ends=ends),
                candidates=exported, chosen=winner['row']['candidate_id'], seen_range=[float(x.min()), float(x.max())],
                fit_settings=dict(arm='C1000', initial_state='estimated', coefficient_bound=1000))


LOGISTIC = 'sys0003_ic1_s0.03_r0_n1'
LOGISTIC_REFIT = ROOT / 'explainer/wisp/data/logistic_c1000_refit_sys0003_ic1_s0.03_r0_n1.jsonl'


def logistic_c1000(live, cells, used):
    """Chapters 1-5 (logistic teaching cell): replace the Q5/Q7 fits by the frozen Q9 runner's C1000 refit.

    The path (weak space) is arm-independent and stays; the candidates become the Q7-rule path states, refitted
    with the estimated initial state and bound 1000. Older cap-era candidates beyond the stop are dropped.
    """
    feature = next(f for f in live['featured'] if 'running' in f.get('roles', []))
    assert feature['cell_id'] == LOGISTIC
    cell = cells[LOGISTIC]
    t, x = read_observations(cell, used)
    _, clean = read_observations(cells['sys0003_ic1_s0_r0_n1'], used)
    _, other = read_observations(cells['sys0003_ic2_s0_r0_n1'], used)
    refit = {r['candidate_id']: r for r in map(json.loads, LOGISTIC_REFIT.read_text(encoding='utf8').splitlines()) if r}
    stop = [[j + 1 for j in s] for s in feature['stop_reference']['supports']]
    funcs = [lambda u: 1.0, lambda u: u, lambda u: u * u, lambda u: u ** 3, math.sin, math.cos]

    def sim(support, params, x0):
        sol = solve_ivp(lambda _, u: [sum(c * funcs[j - 1](u[0]) for j, c in zip(support, params))], (t[0], t[-1]), [x0],
                        t_eval=t, rtol=1e-10, atol=1e-10, method='DOP853')
        y = np.full((len(t), 1), np.nan); y[:sol.y.shape[1], 0] = sol.y[0]
        return y
    out = []
    for c in cell['candidates']:
        sup = c['active_idxs'][0]
        old = next(o for o in feature['candidates'] if json.loads(o['row']['active_idxs'])[0] == sup)
        r = refit[c['candidate_id']]
        assert r['arm'] == 'C1000' and len(r['params']) == len(sup)
        k, mse, N = len(sup), r['estimated_ic_training_mse'], x.size
        row = dict(old['row'], params=json.dumps(r['params']), mse=repr(mse), observed_start_mse=repr(mse),
                   fitted_initial_state=json.dumps(r['fitted_initial_state']), arm='C1000',
                   **{f'{kind}_r2_{w}': repr(r[kind][f'r2_{w}']) for kind in ('reconstruction', 'generalization')
                      for w in ('arithmetic', 'variance_weighted')})
        for kind in ('reconstruction', 'generalization'):
            v = r[kind]['r2_variance_weighted']
            row[f'{kind}_variance_weighted_hit'] = row[f'{kind}_arithmetic_hit'] = str(v is not None and v > .9)
        out.append(dict(old, row=row, bic=N * math.log(mse) + k * math.log(N), penalty=k * math.log(N),
                        curves=dict(**display_arrays(t, truth=clean, model=sim(sup, r['params'], clean[0, 0])),
                                    generalization=display_arrays(t, truth=other, model=sim(sup, r['params'], other[0, 0])))))
    assert [json.loads(o['row']['active_idxs'])[0] for o in out] == stop, 'Q9 path differs from the stop reference'
    feature['candidates'] = out
    win = min(out, key=lambda o: o['bic'])
    feature['chosen'] = win['row']['candidate_id']
    feature['result_row'] = win['row']
    print('logistic C1000:', [(o['row']['candidate_id'], round(o['bic'], 1)) for o in out], 'winner', feature['chosen'])


def build(live_path=LIVE):
    used = set()
    cells = {c['cell_id']: c for c in json.loads(PATHS.read_bytes())['cells']}
    cell = cells[CELL]
    assert cell['arm'] == 'C1000' and cell['system_id'] == 27
    t, x = read_observations(cell, used)
    clean_t, clean = read_observations(cells['sys0027_ic2_s0_r0_n1'], used)
    other_t, other = read_observations(cells['sys0027_ic1_s0_r0_n1'], used)
    assert np.array_equal(t, clean_t) and np.array_equal(t, other_t)
    sigma = cell['sigma']
    truth_support = [[2, 6], [3, 6]]

    # Joint path, and the hare-equation path = the joint states at which equation 1 changes.
    joint = cell['candidates']
    hare, last = [], []
    for c in joint:
        support = c['active_idxs'][0]
        if support != last:
            eq = c['equations'][0]
            hare.append(dict(active_idxs=[support], candidate_id=c['candidate_id'], equations=[eq],
                             k=len(support), origin=c['origin'], p0=eq['coefficients'], step=len(hare) + 1,
                             weak_bic=None, joint_step=c['step']))
            last = support
    assert hare[-1]['active_idxs'][0] == truth_support[0], 'hare path must end at the truth'

    # Candidates: every joint state refitted with the frozen Q9 runner (C1000), display curves re-integrated.
    refit = {r['candidate_id']: r for r in map(json.loads, REFIT.read_text(encoding='utf8').splitlines()) if r}
    assert set(refit) == {c['candidate_id'] for c in joint}, 'refit must cover every path state'
    candidates = []
    for c in joint:
        r = refit[c['candidate_id']]
        assert r['arm'] == 'C1000' and r['ic_mode'] == 'estimated' and r['coefficient_bound'] == 1000
        # Parameters belong to the path state; the record's pruned support only drops tiny coefficients.
        sup = c['active_idxs']
        k, mse, N = sum(map(len, sup)), r['estimated_ic_training_mse'], x.size
        assert len(r['params']) == k, c['candidate_id']
        fit = simulate(sup, r['params'], r['fitted_initial_state'], t)
        recon = simulate(sup, r['params'], clean[0], t)
        gen = simulate(sup, r['params'], other[0], t)
        row = dict(active_idxs=json.dumps(sup), candidate_id=c['candidate_id'], cell_id=CELL, k=str(k),
                   mse=repr(mse), n_samples=str(N), params=json.dumps(r['params']), origin=c['origin'], step=str(c['step']),
                   fitted_initial_state=json.dumps(r['fitted_initial_state']), sigma=str(sigma), rho='0.0', realization='2',
                   system_id='27', initial_condition_set='2', unit_id='sys0027_ic2', weak_bic=repr(c['weak_bic']),
                   raw_exact=str(sup == truth_support), pruned_exact=str(sup == truth_support),
                   **{f'{kind}_r2_{w}': repr(r[kind][f'r2_{w}']) for kind in ('reconstruction', 'generalization', 'training')
                      for w in ('arithmetic', 'variance_weighted')})
        for kind in ('reconstruction', 'generalization'):
            v = r[kind]['r2_variance_weighted']
            row[f'{kind}_variance_weighted_hit'] = row[f'{kind}_arithmetic_hit'] = str(v is not None and v > .9)
        candidates.append(dict(row=row, bic=N * math.log(mse) + k * math.log(N), penalty=k * math.log(N),
                               curves=dict(**display_arrays(t, truth=clean, model=recon),
                                           generalization=display_arrays(t, truth=other, model=gen)),
                               unavailable=None))
    win = min(candidates, key=lambda c: c['bic'])
    running = dict(cell_id=CELL, roles=['running'], chosen=win['row']['candidate_id'], truth_support=truth_support,
                   path=hare, joint_path=joint, candidates=candidates, result_row=win['row'],
                   stop_reference=dict(reason='floor', stop_step=len(hare), threshold=6.635,
                                       supports=[[j - 1 for j in p['active_idxs'][0]] for p in hare]),
                   terms=TERMS, state_names=['H', 'F'])

    live = json.loads(live_path.read_text(encoding='utf8'))
    example = two_equation_example(live, cell, t, x, clean, other, joint, refit)
    live['examples'] = [example] + [e for e in live['examples'] if e['system_id'] != 27]
    live['gate_status'] = json.loads((ROOT / 'explainer/wisp/src/gates.json').read_text(encoding='utf-8-sig'))  # G2 decided: C1000
    logistic_c1000(live, cells, used)
    live['lv_running'] = dict(source=dict(paths=str(PATHS.relative_to(ROOT)), refit=str(REFIT.relative_to(ROOT)),
                                          observations=sorted(str(p.relative_to(ROOT)) for p in used)))
    def finite(o):  # diverged display curves carry NaN; JSON gets null
        if isinstance(o, float):
            return o if math.isfinite(o) else None
        if isinstance(o, list):
            return [finite(v) for v in o]
        if isinstance(o, dict):
            return {k: finite(v) for k, v in o.items()}
        return o
    live_path.write_text(json.dumps(finite(live), ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf8')
    print(json.dumps(dict(cell=CELL, hare_steps=[[TERMS[j - 1] for j in p['active_idxs'][0]] for p in hare],
                          joint_states=len(joint), winner=win['row']['candidate_id'],
                          bic=[round(c['bic'], 1) for c in candidates]), ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live', type=Path, default=LIVE)
    build(p.parse_args().live)
