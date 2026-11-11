"""Per-cell evaluation tables for the WISP manuscript draft (Q8 evidence state, 2026-11-07).

Joins WISP (Q8 arms, size rule (c)) with the reference rows on identical cells:
SINDy / Weak-SINDy / E-SINDy (WP-N47, library poly_deg3_sin_cos, better of the two
STLSQ thresholds per stratum x sigma x metric, chosen in the reference's favour) and
the original MATLAB WSINDy (library L-Q5; W1 on rho = 0, W1-interp on rho = 0.5).
Writes tidy CSVs into paper/wisp/data/.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
Q8 = Path('C:/Users/joedicke/AppData/Local/Temp/claude/4da8ff96f3389fae/'
          '74de8444-749b-46d9-b373-f84449c9b174/scratchpad/q8_eval_1107')
OUT = Path(__file__).resolve().parent / 'data'
OUT.mkdir(exist_ok=True)
METRICS = {'structure': ('pruned_exact', 'sindy_structure_hit_pruned'),
           'raw': ('raw_exact', 'sindy_structure_hit_raw'),
           'rec': ('reconstruction_variance_weighted_hit', 'reconstruction_r2_variance_weighted_gt_0_9'),
           'gen': ('generalization_variance_weighted_hit', 'generalization_r2_variance_weighted_gt_0_9')}
KEY = ['system_id', 'initial_condition_set', 'sigma', 'rho', 'realization']


def boolean(v):
    if isinstance(v, str):
        return v.strip().lower() == 'true'
    return bool(v) if v == v else False


def stratum_of(system_id, dim_stratum, rep):
    if dim_stratum.startswith('dim3'):
        return 'dim3_feasible' if system_id in (52, 61) else 'dim3_infeasible'
    return dim_stratum


paths = {(c['cell_id'], c['arm']): c for c in
         json.loads((ROOT / 'outputs/sideproject_q8_inputs/grid/q8_paths.json').read_bytes())['cells']}
ch = pd.read_csv(Q8 / 'choices.csv', low_memory=False)
ch['q8_stratum'] = [paths[a, b]['stratum'] for a, b in zip(ch.cell_id, ch.arm)]
ch['stratum'] = [stratum_of(s, q, None) for s, q in zip(ch.system_id, ch.q8_stratum)]
ch['representability'] = [paths[a, b]['representability'] for a, b in zip(ch.cell_id, ch.arm)]
for m, (w, _) in METRICS.items():
    ch[m] = ch[w].map(boolean) if w in ch else False
ch.loc[ch.representability != 'exact', ['structure', 'raw']] = np.nan
wisp = ch.rename(columns={'arm': 'method'})
wisp.to_csv(OUT / 'wisp_choices_all_rules.csv', index=False)
c = wisp[wisp.size_rule == 'c'].copy()
cells = c[c.method == 'C1000'][KEY + ['stratum', 'representability', 'cell_id', 'unit_id']].drop_duplicates()

# --- SINDy family ---------------------------------------------------------
ref = pd.read_csv(ROOT / 'outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv', low_memory=False)
ref = ref[ref.method.isin(['sindy', 'weak_sindy', 'e_sindy']) & ref.include_sin_cos.map(boolean)
          & (ref.polynomial_degree == 3)]
ref = ref.rename(columns={'source_initial_condition_set': 'initial_condition_set', 'noise_sigma': 'sigma',
                          'subsample_rho': 'rho', 'noise_realization': 'realization'})
ref = ref.merge(cells, on=KEY, validate='many_to_one')
rows = []
for (method, stratum, sigma), g in ref.groupby(['method', 'stratum', 'sigma']):
    # sigma = 0 holds the clean cell and (0, 0.5); clean is reported on its own.
    for clean in ((True, False) if sigma == 0 else (False,)):
        gg = g if sigma else g[(g.rho == 0) == clean]
        if gg.empty:
            continue
        out = gg[KEY + ['stratum', 'cell_id']].drop_duplicates().set_index('cell_id')
        for m, (_, field) in METRICS.items():
            best = max(gg.groupby('method_config_id'), key=lambda kv: (kv[1][field].map(boolean).mean(), kv[0]))
            out[m] = best[1].set_index('cell_id')[field].map(boolean)
            out[m + '_config'] = best[0]
        out['method'] = method
        rows.append(out.reset_index())
sindy = pd.concat(rows, ignore_index=True)

# --- MATLAB WSINDy ----------------------------------------------------------
base = ROOT / 'outputs/sideproject_q5w_wsindy'
ws = pd.concat([pd.read_csv(base / d / 'details.csv', low_memory=False)
                for d in ('full_matlab', 'w1_interp_full_matlab')], ignore_index=True)
ws = ws[ws.q5w_configuration.str.endswith(':L-Q5')]
ws = ws[((ws.method == 'W1') & (ws.subsample_rho == 0)) | ((ws.method != 'W1') & (ws.subsample_rho == 0.5))]
ws = ws.rename(columns={'source_initial_condition_set': 'initial_condition_set', 'noise_sigma': 'sigma',
                        'subsample_rho': 'rho', 'noise_realization': 'realization'})
ws = ws.merge(cells, on=KEY, validate='one_to_one')
for m, (_, field) in METRICS.items():
    ws[m] = ws[field].map(boolean)
ws['method'] = 'wsindy'

keep = KEY + ['stratum', 'representability', 'cell_id', 'method', 'structure', 'raw', 'rec', 'gen']
sindy = sindy.merge(cells[['cell_id', 'representability']], on='cell_id')
allm = pd.concat([c[keep], sindy[keep], ws[keep]], ignore_index=True)
allm.loc[allm.representability != 'exact', ['structure', 'raw']] = np.nan
allm['condition'] = np.where((allm.sigma == 0) & (allm.rho == 0), 'clean',
                             np.where(allm.sigma == 0, 'sub', 's' + allm.sigma.astype(str) + '_r' + allm.rho.astype(str)))
allm['noisy'] = allm.sigma > 0
allm.to_csv(OUT / 'per_cell_all_methods.csv', index=False)
print(allm.groupby(['method', 'condition']).size().unstack())

# --- cluster bootstrap over systems -----------------------------------------
rng = np.random.default_rng(20261107)
B = 4000


def rate_ci(g, m):
    g = g.dropna(subset=[m])
    if g.empty:
        return np.nan, np.nan, np.nan, 0, 0
    per = g.groupby('system_id')[m].agg(['sum', 'count'])
    s, n = per['sum'].to_numpy(float), per['count'].to_numpy(float)
    idx = rng.integers(0, len(s), size=(B, len(s)))
    boot = s[idx].sum(1) / n[idx].sum(1)
    return s.sum() / n.sum(), np.quantile(boot, .025), np.quantile(boot, .975), int(n.sum()), len(s)


summary = []
for (method, stratum), g in allm[allm.noisy].groupby(['method', 'stratum']):
    for m in ('structure', 'raw', 'rec', 'gen'):
        r, lo, hi, n, k = rate_ci(g, m)
        summary.append(dict(method=method, stratum=stratum, metric=m, rate=r, lo=lo, hi=hi, n_cells=n, n_systems=k))
summary = pd.DataFrame(summary)
summary.to_csv(OUT / 'summary_noisy.csv', index=False)

bycond = []
for (method, stratum, cond), g in allm.groupby(['method', 'stratum', 'condition']):
    for m in ('structure', 'rec', 'gen'):
        r, lo, hi, n, k = rate_ci(g, m)
        bycond.append(dict(method=method, stratum=stratum, condition=cond, metric=m, rate=r, lo=lo, hi=hi, n_cells=n))
pd.DataFrame(bycond).to_csv(OUT / 'by_condition.csv', index=False)

# --- paired sign-flip permutation over systems (WISP C1000 vs each reference) --
perm = []
w = allm[(allm.method == 'C1000') & allm.noisy]
for ref_m in ('sindy', 'weak_sindy', 'e_sindy', 'wsindy'):
    r = allm[(allm.method == ref_m) & allm.noisy]
    j = w.merge(r, on='cell_id', suffixes=('_w', '_r'))
    for stratum, g in j.groupby('stratum_w'):
        for m in ('structure', 'gen', 'rec'):
            gg = g.dropna(subset=[m + '_w', m + '_r'])
            if gg.empty:
                continue
            d = (gg[m + '_w'].astype(float) - gg[m + '_r'].astype(float)).groupby(gg.system_id_w).sum().to_numpy()
            obs = d.sum()
            signs = rng.choice([-1, 1], size=(20000, len(d)))
            p = ((np.abs((signs * d).sum(1)) >= abs(obs) - 1e-9).sum() + 1) / 20001
            perm.append(dict(reference=ref_m, stratum=stratum, metric=m, n_cells=len(gg), n_systems=len(d),
                             wisp_hits=int(gg[m + '_w'].sum()), ref_hits=int(gg[m + '_r'].sum()),
                             systems_wisp_ahead=int((d > 0).sum()), systems_ref_ahead=int((d < 0).sum()), p=p))
pd.DataFrame(perm).to_csv(OUT / 'paired_permutation.csv', index=False)

# --- per-system generalization rates (noisy) ---------------------------------
ps = allm[allm.noisy].groupby(['method', 'system_id', 'stratum', 'representability'])[['gen', 'structure', 'rec']].mean().reset_index()
ps.to_csv(OUT / 'per_system_noisy.csv', index=False)

# --- ablations and arms (noisy, rule c) ---------------------------------------
arms = []
for (method, stratum), g in c[c.sigma > 0].groupby(['method', 'stratum']):
    for m in ('structure', 'rec', 'gen'):
        r, lo, hi, n, k = rate_ci(g, m)
        arms.append(dict(method=method, stratum=stratum, metric=m, rate=r, lo=lo, hi=hi, n_cells=n))
pd.DataFrame(arms).to_csv(OUT / 'arms_noisy.csv', index=False)

# --- size rules (a) weak BIC, (b) EvoGrow objective, (c) trajectory BIC -------
sr = wisp[(wisp.method == 'C1000') & (wisp.representability == 'exact')].copy()
sr.to_csv(OUT / 'size_rules_exact_C1000.csv', index=False,
          columns=['cell_id', 'system_id', 'stratum', 'sigma', 'rho', 'size_rule', 'k', 'k_true', 'size_error',
                   'structure', 'raw', 'rec', 'gen', 'truth_on_path', 'n_candidates', 'total_loss_evals',
                   'total_ode_solves'])
print(pd.DataFrame(arms).query("method=='C1000'"))
print(summary.query("stratum=='dim2_exact'"))
