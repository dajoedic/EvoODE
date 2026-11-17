"""Where WISP Q9 spends its compute (context only; counts are the evidence, seconds are not).

Per candidate fit: loss evaluations, ODE solves, step-limit solves, diverged solves, recorded solve/fit seconds, number
of parameters, stop reason; joined with the rule-(c) choice. Answers: how concentrated the cost is, what the expensive
fits have in common, and whether the expensive fits are ever the chosen model (and then correct).

Usage: python diagnose_wisp_q9_cost.py <q9 cells dir> <q9 records dir> <out dir>
"""
import glob
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

CELLS, RECS, OUT = (Path(a) for a in sys.argv[1:4])
OUT.mkdir(parents=True, exist_ok=True)
rows = []
for f in glob.glob(str(RECS / 'index_*.jsonl')):
    for line in open(f, encoding='utf8'):
        r = json.loads(line)
        m = r['fit_meta'] if isinstance(r['fit_meta'], dict) else {}
        rows.append(dict(cell_id=r['cell_id'], candidate_id=r['candidate_id'], n_params=len(r['params']),
                         loss_evals=m.get('loss_evals'), ode_solves=m.get('ode_solves'),
                         eval_ode_solves=r.get('evaluation_ode_solves'),
                         step_limit=m.get('step_limit_solves', 0), diverged=m.get('diverged_solves', 0),
                         unstable=m.get('solver_unstable_solves', 0), solve_s=m.get('solve_time_s'),
                         fit_s=m.get('fit_time_s'), stop=m.get('stop_reason'), retcode=m.get('retcode'),
                         iter_hits=m.get('optimizer_iteration_limit_hits', 0),
                         train_loss=r['training']['loss'], sentinel=r['training'].get('sentinel')))
d = pd.DataFrame(rows)
cells = pd.read_csv(CELLS / 'cells.csv')
ch = pd.read_csv(CELLS / 'wisp_choices.csv')
ch = ch[ch.size_rule == 'c'][['cell_id', 'candidate_id', 'structure', 'rec', 'gen']]
d = d.merge(cells[['cell_id', 'stratum', 'system_id', 'sigma', 'rho', 'dim']], on='cell_id')
d = d.merge(ch.rename(columns={'candidate_id': 'chosen_id'}), on='cell_id', how='left')
d['chosen'] = d.candidate_id == d.chosen_id
d['evals_per_param'] = d.loss_evals / (d.n_params + 1)
d.to_csv(OUT / 'q9_candidate_cost.csv', index=False)

tot = d.fit_s.sum()
print('candidates', len(d), '| total fit core-h', round(tot / 3600, 1), '| total loss evals', int(d.loss_evals.sum()))
s = d.sort_values('fit_s', ascending=False)
for q in (0.001, 0.01, 0.05, 0.10):
    n = int(len(s) * q)
    print(f'top {100*q:.1f}% of fits ({n}) hold {100*s.fit_s.iloc[:n].sum()/tot:.1f}% of fit time, '
          f'{100*s.loss_evals.iloc[:n].sum()/d.loss_evals.sum():.1f}% of loss evals; chosen among them: '
          f'{int(s.chosen.iloc[:n].sum())}')
top = s.iloc[:int(len(s) * 0.01)]
print('\nthe top 1% by stratum:', top.stratum.value_counts().to_dict())
print('top 1%: share with step-limit solves', round((top.step_limit > 0).mean(), 3), '| with diverged solves',
      round((top.diverged > 0).mean(), 3), '| stop reasons', top.stop.value_counts().to_dict())
print('all: share with step-limit solves', round((d.step_limit > 0).mean(), 3))
print('top 1% chosen and correct (structure/rec/gen):',
      top[top.chosen][['structure', 'rec', 'gen']].sum().to_dict(), 'of', int(top.chosen.sum()))

print('\nper stratum: median loss evals per fit, per param+1, seconds per loss eval (median), core-h share')
g = d.groupby('stratum')
print(pd.DataFrame(dict(fits=g.size(), med_evals=g.loss_evals.median(), med_evals_per_p=g.evals_per_param.median(),
                        med_ms_per_eval=(1000 * d.solve_s / d.loss_evals).groupby(d.stratum).median(),
                        core_h=g.fit_s.sum() / 3600, share=g.fit_s.sum() / tot)).round(3).to_string())
print('\nloss evals per fit vs n_params (median):', d.groupby('n_params').loss_evals.median().head(20).to_dict())
print('stop reasons overall:', d.stop.value_counts().to_dict())
print('fits with optimizer iteration-limit hits:', int((d.iter_hits > 0).sum()))
nch = d[~d.chosen]
print('\nunchosen fits: share of fit time', round(nch.fit_s.sum() / tot, 3))
# Cost of candidates larger than the chosen one (fitted only because the path continued)
d['k'] = d.n_params
kc = d[d.chosen].set_index('cell_id').n_params
d['larger_than_chosen'] = d.n_params > d.cell_id.map(kc)
print('fits larger than the chosen model: share of fit time', round(d[d.larger_than_chosen].fit_s.sum() / tot, 3),
      '| share of fits', round(d.larger_than_chosen.mean(), 3))
