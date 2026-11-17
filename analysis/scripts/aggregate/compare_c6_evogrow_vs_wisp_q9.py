"""Paired comparison: C-6 EvoGrow (capped, partial) vs WISP Q9 (rule c) on identical cells.

Key: system, IC set, sigma, rho, realization (C-6 noise_realization == Q9 realization). Observed-data hashes must agree.
Metrics: structure (pruned exact, exact systems only), raw exact, reconstruction and generalization
R2_vw > 0.9 against clean targets. Systems are the units: per-system rate, then mean over systems.
"""
import glob
import json
from pathlib import Path

import pandas as pd

W = Path(r'C:\Users\joedicke\Documents\Repositories\EvoODE\outputs\c6_vs_wisp_2026-11-17')

# --- C-6 records
rows = []
for line in open(W / 'c6_history_all.jsonl', encoding='utf8'):
    r = json.loads(line)
    rows.append(dict(system_id=r['system_id'], initial_condition_set=r['initial_condition_set'], sigma=r['noise_sigma'],
                     rho=r['subsample_rho'], realization=r['noise_realization'], seed=r['seed'],
                     representability=r['representability'], dim=len(r['u0']),
                     e_structure=bool(r['exact_support_match_pruned']), e_raw=bool(r['exact_support_match_raw']),
                     e_loss_evals=r['total_loss_evals'], e_ode_solves=r['total_ode_solves'],
                     e_hash=json.dumps(json.loads(r['observed_data_sha256']) if isinstance(r['observed_data_sha256'], str)
                                       else r['observed_data_sha256'], sort_keys=True)))
c6 = pd.DataFrame(rows)

ce = pd.concat([pd.read_csv(f) for f in glob.glob(str(W / 'c6_clean_eval' / '*' / 'cells.csv'))])
ce = ce.rename(columns={'source_initial_condition_set': 'initial_condition_set', 'noise_sigma': 'sigma',
                        'subsample_rho': 'rho', 'noise_realization': 'realization'})
ce['e_rec'] = ce.reconstruction_r2_variance_weighted.astype(float) > 0.9
ce['e_gen'] = ce.generalization_r2_variance_weighted.astype(float) > 0.9
KEY = ['system_id', 'initial_condition_set', 'sigma', 'rho', 'realization']
for k in KEY:
    ce[k] = ce[k].astype(float)
    c6[k] = c6[k].astype(float)
c6 = c6.merge(ce[KEY + ['e_rec', 'e_gen']], on=KEY, how='left', validate='1:1')
assert c6.e_rec.notna().all(), 'clean eval missing for some C-6 cells'

# --- WISP Q9, rule c
cells = pd.read_csv(W / 'q9_cells' / 'cells.csv')
ch = pd.read_csv(W / 'q9_cells' / 'wisp_choices.csv')
ch = ch[(ch.size_rule == 'c') & (ch.status == 'complete')]
wi = cells.merge(ch, on='cell_id')
for k in KEY:
    wi[k] = wi[k].astype(float)
wi['w_hash'] = wi.observed_data_sha256.map(lambda s: json.dumps(json.loads(s), sort_keys=True))
wi = wi.rename(columns={'structure': 'w_structure', 'raw': 'w_raw', 'rec': 'w_rec', 'gen': 'w_gen',
                        'total_loss_evals': 'w_loss_evals', 'total_ode_solves': 'w_ode_solves'})
p = c6.merge(wi[KEY + ['stratum', 'w_hash', 'w_structure', 'w_raw', 'w_rec', 'w_gen', 'w_loss_evals', 'w_ode_solves']],
             on=KEY, how='left', validate='1:1')
print('C-6 cells', len(c6), '| paired with complete WISP cell', p.w_rec.notna().sum())
p = p[p.w_rec.notna()].copy()
bad = (p.e_hash != p.w_hash).sum()
print('observed-data hash mismatches:', bad)
for m in ('structure', 'raw', 'rec', 'gen'):
    p['w_' + m] = p['w_' + m].astype(bool)
p['cond'] = p.apply(lambda r: f"s{r.sigma:g}_r{r.rho:g}", axis=1)
p.to_csv(W / 'paired_cells.csv', index=False)

print('\nsystems by stratum (paired):')
print(p.groupby('stratum').system_id.agg(lambda s: sorted(set(int(x) for x in s))).to_string())
print('\ncells per stratum x condition:')
print(p.pivot_table(index='stratum', columns='cond', values='system_id', aggfunc='size', fill_value=0).to_string())


def table(df, label):
    out = []
    for st, g in df.groupby('stratum'):
        exact = st.endswith('_exact') or 'exact' in st
        for m in (['structure', 'raw'] if exact else []) + ['rec', 'gen']:
            per = g.groupby('system_id')[['e_' + m, 'w_' + m]].mean()
            d = per['w_' + m] - per['e_' + m]
            out.append(dict(stratum=st, metric=m, systems=len(per), cells=len(g),
                            EvoGrow=round(100 * per['e_' + m].mean(), 1), WISP=round(100 * per['w_' + m].mean(), 1),
                            diff_pp=round(100 * d.mean(), 1), sys_WISP_better=int((d > 0).sum()),
                            sys_EvoGrow_better=int((d < 0).sum())))
    t = pd.DataFrame(out)
    print(f'\n=== {label} (rates in %, systems as units) ===')
    print(t.to_string(index=False))
    return t


t_all = table(p, 'all paired conditions')
t_noisy = table(p[p.sigma > 0], 'noisy only (sigma > 0)')
t_sub = table(p[p.sigma == 0], 'sigma 0, rho 0.5 (subsampling only)')
t_all.to_csv(W / 'table_all.csv', index=False)
t_noisy.to_csv(W / 'table_noisy.csv', index=False)

# per condition, pooled over strata, systems as units
print('\n=== per condition (all strata pooled, systems as units; rec / gen) ===')
rows = []
for c, g in p.groupby('cond'):
    per = g.groupby('system_id')[['e_rec', 'w_rec', 'e_gen', 'w_gen']].mean()
    rows.append(dict(cond=c, systems=len(per), EvoGrow_rec=round(100 * per.e_rec.mean(), 1),
                     WISP_rec=round(100 * per.w_rec.mean(), 1), EvoGrow_gen=round(100 * per.e_gen.mean(), 1),
                     WISP_gen=round(100 * per.w_gen.mean(), 1)))
print(pd.DataFrame(rows).to_string(index=False))

# cost
print('\n=== cost per cell (loss evaluations), quantiles by stratum ===')
for st, g in p.groupby('stratum'):
    q = lambda s: '/'.join(f'{v:.3g}' for v in s.quantile([0.1, 0.5, 0.9]))
    ratio = (g.e_loss_evals / g.w_loss_evals)
    print(f'{st:16s} EvoGrow {q(g.e_loss_evals):28s} WISP {q(g.w_loss_evals):28s} ratio EvoGrow/WISP {q(ratio)}')
print('pooled loss evals EvoGrow / WISP:', round(p.e_loss_evals.sum() / p.w_loss_evals.sum(), 2))
