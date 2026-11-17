"""Where WISP fails to reconstruct and EvoGrow (C-6) does not: path failure or selection failure?

Input: the paired C-6 / Q9 cells (`compare_c6_evogrow_vs_wisp_q9.py`), the Q9 records (one per candidate) and the
WISP choices (rule c). For every paired cell with EvoGrow reconstruction R2_vw > 0.9 and WISP's choice <= 0.9:
  path      - no candidate on WISP's path reconstructs (R2_vw > 0.9 from the clean IC)
  selection - at least one candidate does, rule c chose another one
For selection cells the best reconstructing candidate is compared with the chosen one on size k and training loss
(observed data), which is what rule c sees. Read-only; no fits.

Usage: python diagnose_wisp_surrogate_reconstruction_failures.py <work_dir> [system ids ...]
"""
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

W = Path(sys.argv[1])
SYSTEMS = {int(s) for s in sys.argv[2:]}

pairs = pd.read_csv(W / 'paired_cells.csv')
pairs = pairs[pairs.e_rec & ~pairs.w_rec]
if SYSTEMS:
    pairs = pairs[pairs.system_id.isin(SYSTEMS)]
cells = pd.read_csv(W / 'q9_cells' / 'cells.csv')
ch = pd.read_csv(W / 'q9_cells' / 'wisp_choices.csv')
ch = ch[ch.size_rule == 'c'].merge(cells[['cell_id', 'system_id', 'initial_condition_set', 'sigma', 'rho', 'realization']],
                                   on='cell_id')
KEY = ['system_id', 'initial_condition_set', 'sigma', 'rho', 'realization']
pairs = pairs.merge(ch[KEY + ['cell_id', 'candidate_id', 'k']], on=KEY, validate='1:1')
want = set(pairs.cell_id)

recs = defaultdict(dict)
print("cells to diagnose:", len(want), flush=True)
for f in glob.glob(str(W / 'out' / 'index_*.jsonl')):
    for line in open(f, encoding='utf8'):
        r = json.loads(line)
        if r['cell_id'] in want:
            recs[r['cell_id']][r['candidate_id']] = r

print("records read:", sum(len(v) for v in recs.values()), flush=True)
paths = {c['cell_id']: c for c in json.loads(Path(W.parents[0] / 'sideproject_q9_inputs/grid/q9_paths.json').read_bytes())['cells']
         if c['cell_id'] in want}

rows = []
for _, p in pairs.iterrows():
    cand = recs[p.cell_id]
    ksize = {k['candidate_id']: k['k'] for k in paths[p.cell_id]['candidates']}
    def rec(c):
        x = c['reconstruction']
        return -1e9 if x['sentinel'] or x['diverged'] else x['r2_variance_weighted']
    good = [cid for cid, c in cand.items() if rec(c) > 0.9]
    chosen = cand[p.candidate_id]
    best = max(cand, key=lambda cid: rec(cand[cid]))
    rows.append(dict(cell_id=p.cell_id, system_id=p.system_id, sigma=p.sigma, rho=p.rho,
                     n_candidates=len(cand), n_good=len(good), kind='selection' if good else 'path',
                     chosen=p.candidate_id, chosen_k=ksize[p.candidate_id], chosen_rec=round(rec(chosen), 3),
                     chosen_train_loss=chosen['training']['loss'],
                     best=best, best_k=ksize[best], best_rec=round(rec(cand[best]), 3),
                     best_train_loss=cand[best]['training']['loss'],
                     best_beats_chosen_on_training=cand[best]['training']['loss'] < chosen['training']['loss']))
d = pd.DataFrame(rows)
d.to_csv(W / 'wisp_rec_failure_diagnosis.csv', index=False)
print('cells (EvoGrow rec hit, WISP rec miss):', len(d))
print(d.groupby('system_id').kind.value_counts().unstack(fill_value=0).to_string())
print('\nper system: chosen k, best k, best rec (median), best beats chosen on training loss (share)')
print(d.groupby('system_id').agg(chosen_k=('chosen_k', 'median'), best_k=('best_k', 'median'),
                                 chosen_rec=('chosen_rec', 'median'), best_rec=('best_rec', 'median'),
                                 best_wins_train=('best_beats_chosen_on_training', 'mean'),
                                 n_good=('n_good', 'median'), n_cand=('n_candidates', 'median')).round(3).to_string())
