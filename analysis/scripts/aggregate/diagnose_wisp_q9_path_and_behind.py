"""WISP Q9 (noisy, dim 1/2 exact): failure anatomy of the growth path, and the systems where WISP is behind WSINDy.

Part A - path anatomy. For every noisy exact dim-1/2 cell whose chosen model (rule c) misses the exact structure,
the cell's growth path (all candidates, raw supports) is classified against the true support:
  selection      - the true support is a candidate; rule c chose another one
  never_entered  - at least one true term is in no candidate at all
  superset_only  - every true term enters, and some candidate holds all of them, but always with extra terms
  never_together - every true term enters at some step, but no candidate holds all of them at once
For path cells the spurious terms of the last candidate are counted by name, and the share of cells whose missing true
term is the constant "1" is reported.

Part B - per system (default 1, 12, 17): the chosen model's raw and pruned support against the truth, per noisy cell.

Read-only; no fits. Usage: python diagnose_wisp_q9_path_and_behind.py <q9 cells dir> <q9 records dir> <out dir>
"""
from __future__ import annotations
import glob
import json
import sys
from collections import Counter
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate_sideproject_q4 import ROOT, SUPPORT, load_exact_supports  # noqa: E402
from phase1_diagnostic import prune_terms  # noqa: E402

CELLS, RECS, OUT = (Path(a) for a in sys.argv[1:4])
BEHIND = (1, 12, 17)
OUT.mkdir(parents=True, exist_ok=True)

cells = pd.read_csv(CELLS / 'cells.csv')
ch = pd.read_csv(CELLS / 'wisp_choices.csv')
ch = ch[ch.size_rule == 'c'].merge(cells, on='cell_id')
noisy = ch[(ch.sigma > 0) & ch.stratum.isin(['dim1_exact', 'dim2_exact'])]
paths = {c['cell_id']: c for c in json.loads((ROOT / 'outputs/sideproject_q9_inputs/grid/q9_paths.json').read_bytes())['cells']}
_, systems = load_exact_supports(ROOT / SUPPORT)
truth = {s['system_id']: [set(e) for e in s['support_terms']] for s in systems}


def support(cand):
    return [set(eq['term_names']) for eq in cand['equations']]


def flat(sup):
    return {(i, t) for i, eq in enumerate(sup) for t in eq}


# ----------------------------------------------------------------------------- A: path anatomy
rows = []
for _, c in noisy.iterrows():
    if bool(c.structure):
        continue
    p = paths[c.cell_id]
    tr = flat(truth[c.system_id])
    sups = [flat(support(k)) for k in p['candidates']]
    seen = set().union(*sups) if sups else set()
    if any(s == tr for s in sups):
        kind = 'selection'
    elif not tr <= seen:
        kind = 'never_entered'
    elif any(tr <= s for s in sups):
        kind = 'superset_only'
    else:
        kind = 'never_together'
    last = sups[-1] if sups else set()
    missing = sorted(t for _, t in tr - seen)
    extra_last = sorted(t for _, t in last - tr)
    rows.append(dict(cell_id=c.cell_id, system_id=c.system_id, stratum=c.stratum, sigma=c.sigma, rho=c.rho,
                     kind=kind, n_candidates=len(sups), missing_never_entered=';'.join(missing),
                     extra_in_last=';'.join(extra_last), end_reason=';'.join(e['end_reason'] for e in p['equation_paths'])))
a = pd.DataFrame(rows)
a.to_csv(OUT / 'path_anatomy_cells.csv', index=False)
print('missed cells:', len(a))
print(a.groupby('stratum').kind.value_counts().unstack(fill_value=0).to_string())
print('\nby system (path cells only):')
pc = a[a.kind != 'selection']
print(pc.groupby(['stratum', 'system_id']).kind.value_counts().unstack(fill_value=0).to_string())
ne = pc[pc.kind == 'never_entered']
cnt = Counter(t for s in ne.missing_never_entered for t in s.split(';') if t)
print('\nnever-entered true terms (count of cells):', cnt.most_common(12))
print('share of never_entered cells missing the constant "1":', round((ne.missing_never_entered.str.split(';')
      .map(lambda x: '1' in x)).mean(), 3))
so = pc[pc.kind == 'superset_only']
print('superset_only: spurious terms in the last candidate:',
      Counter(t for s in so.extra_in_last for t in s.split(';') if t).most_common(12))
print('end reasons (path cells):', Counter(e for s in pc.end_reason for e in s.split(';')).most_common())
summ = a.groupby(['stratum', 'kind']).size().rename('cells').reset_index()
summ.to_csv(OUT / 'path_anatomy_summary.csv', index=False)

# ----------------------------------------------------------------------------- B: systems behind WSINDy
want = noisy[noisy.system_id.isin(BEHIND)]
chosen = {(r.cell_id, r.candidate_id) for r in want.itertuples()}
recs = {}
for f in glob.glob(str(RECS / 'index_*.jsonl')):
    for line in open(f, encoding='utf8'):
        if not any(f'sys{s:04d}_' in line[:400] for s in BEHIND):
            pass
        r = json.loads(line)
        if (r['cell_id'], r['candidate_id']) in chosen:
            recs[r['cell_id'], r['candidate_id']] = r
rows = []
for r in want.itertuples():
    p = paths[r.cell_id]
    cand = next(k for k in p['candidates'] if k['candidate_id'] == r.candidate_id)
    rec = recs[r.cell_id, r.candidate_id]
    params, off, pruned = rec['params'], 0, []
    coefs = []
    for eq in cand['equations']:
        n = len(eq['term_names'])
        d = dict(zip(eq['term_names'], params[off:off + n]))
        pruned.append(prune_terms(d))
        coefs.append(';'.join(f'{t}={v:.4g}' for t, v in d.items()))
        off += n
    tr = truth[r.system_id]
    rows.append(dict(cell_id=r.cell_id, system_id=r.system_id, ic=r.initial_condition_set, sigma=r.sigma, rho=r.rho,
                     realization=r.realization, k=r.k, k_true=r.k_true, structure=bool(r.structure),
                     rec=bool(r.rec), gen=bool(r.gen), truth_on_path=bool(r.truth_on_path),
                     raw='|'.join(','.join(sorted(s)) for s in support(cand)),
                     pruned='|'.join(','.join(sorted(s)) for s in pruned),
                     truth='|'.join(','.join(sorted(s)) for s in tr), coefficients='|'.join(coefs),
                     path='>'.join('|'.join(','.join(sorted(s)) for s in support(k)) for k in p['candidates'])))
b = pd.DataFrame(rows)
b.to_csv(OUT / 'behind_systems_cells.csv', index=False)
for sid, g in b.groupby('system_id'):
    print(f'\n=== system {sid}: truth {g.truth.iloc[0]} | structure {g.structure.mean():.2f} gen {g.gen.mean():.2f} '
          f'truth on path {g.truth_on_path.mean():.2f}')
    print('chosen pruned supports:', Counter(g.pruned).most_common(6))
    print('chosen raw supports:', Counter(g.raw).most_common(6))
    print('by IC: structure', g.groupby('ic').structure.mean().round(2).to_dict(), 'gen',
          g.groupby('ic').gen.mean().round(2).to_dict())
    print('by sigma: structure', g.groupby('sigma').structure.mean().round(2).to_dict())
