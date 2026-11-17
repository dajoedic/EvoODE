"""Per-cell evaluation tables for the WISP manuscript (Q9 evidence state).

Reads the per-cell tables written by `analysis/scripts/aggregate/build_wisp_paper_cells.py` (cells.csv,
wisp_choices.csv, reference_cells.csv) and picks each reference's configuration exactly as protocol Q9-A does
(`q9a_claims.in_favour`: per method x stratum x sigma x metric, in the reference's favour; WSINDy has no choice).
The LaTeX number macros come from `q9a_claims.py` directly (data/results_macros.tex); this script writes the tables
the figures read. Rates use the same cluster bootstrap over systems (10,000 resamples, seed of Q9-A).

Not regenerated here: data/arms_noisy.csv (ablation arms exist only in the Q8 grid; written by the Q8 version of this
script, git 3835b4e).

Usage: python make_data.py [<q9 cells dir>]
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'analysis/scripts/aggregate'))
import q9a_claims as qa  # noqa: E402

CELLS = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'outputs/c6_vs_wisp_2026-11-17/q9_cells'
OUT = Path(__file__).resolve().parent / 'data'
OUT.mkdir(exist_ok=True)
DIM3 = {'dim3_exact_5261': 'dim3_feasible', 'dim3_exact_5459': 'dim3_infeasible'}
METRICS = ['structure', 'raw', 'rec', 'gen']

cells, choices, refs, meta = qa.load(CELLS)
cells['stratum'] = cells.stratum.replace(DIM3)
print('Q9 cells:', len(cells), '| complete WISP cells:', meta.get('complete_cells'))

# --- WISP choices, all size rules ------------------------------------------------
wc = choices.merge(cells, on='cell_id', validate='many_to_one')
wc['method'] = 'C1000'
wc.to_csv(OUT / 'wisp_choices_all_rules.csv', index=False)
sr = wc[wc.representability == 'exact']
sr.to_csv(OUT / 'size_rules_exact_C1000.csv', index=False,
          columns=['cell_id', 'system_id', 'stratum', 'sigma', 'rho', 'size_rule', 'k', 'k_true', 'size_error',
                   'structure', 'raw', 'rec', 'gen', 'truth_on_path', 'n_candidates', 'total_loss_evals',
                   'total_ode_solves'])

# --- WISP (rule c) and every reference at its in-favour configuration --------------
allm = qa.long_table(cells, choices, refs)
allm['method'] = allm.method.replace({'WISP': 'C1000'})
allm.loc[allm.representability != 'exact', ['structure', 'raw']] = np.nan
allm['noisy'] = allm.sigma > 0
allm['group'] = [qa.sigma_group(s, r) for s, r in zip(allm.sigma, allm.rho)]
allm.to_csv(OUT / 'per_cell_all_methods.csv', index=False)
print(allm.groupby(['method', 'condition']).size().unstack())

rng = np.random.default_rng(qa.SEED)


def rate(g, m):
    return qa.rate_ci(g, m, rng)


summary = []
for (method, stratum), g in allm[allm.noisy].groupby(['method', 'stratum']):
    for m in METRICS:
        summary.append(dict(method=method, stratum=stratum, metric=m, **rate(g, m)))
pd.DataFrame(summary).to_csv(OUT / 'summary_noisy.csv', index=False)

# by condition: clean, subsampling only, and each sigma (both rho pooled) and each sigma x rho
bycond = []
for (method, stratum, group), g in allm.groupby(['method', 'stratum', 'group']):
    for m in ('structure', 'rec', 'gen'):
        bycond.append(dict(method=method, stratum=stratum, condition=group, metric=m, **rate(g, m)))
for (method, stratum, cond), g in allm[allm.noisy].groupby(['method', 'stratum', 'condition']):
    for m in ('structure', 'rec', 'gen'):
        bycond.append(dict(method=method, stratum=stratum, condition=cond, metric=m, **rate(g, m)))
pd.DataFrame(bycond).to_csv(OUT / 'by_condition.csv', index=False)

ps = (allm[allm.noisy].groupby(['method', 'system_id', 'stratum', 'representability'])[['gen', 'structure', 'rec']]
      .mean().reset_index())
ps.to_csv(OUT / 'per_system_noisy.csv', index=False)

stale = OUT / 'paired_permutation.csv'
if stale.exists():
    stale.unlink()  # Q8-only table; the paired tests are now q9a_claims.py's primary/secondary outputs
print(pd.DataFrame(summary).query("stratum in ['dim1_exact','dim2_exact'] and metric in ['structure','gen']")
      .pivot_table(index='method', columns=['stratum', 'metric'], values='rate').round(3))
