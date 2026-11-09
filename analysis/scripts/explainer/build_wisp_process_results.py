"""Results numbers for the closing slide of the WISP process page (explainer/wisp/process/results.json).

Source: the frozen paper tables under paper/wisp/data/ (Q8 evidence, manuscript draft of 7 November 2026).
Main comparison: noisy data sets of dimensions 1 and 2 (paper Figure 3 and Table 1) plus the two dimension-3 strata
(systems 52/61 and 54-59) of the same summary table.
WeakIdent (Q-B B2, native arm, authors' tau) is not in the manuscript yet: its rates are computed here on exactly the
noisy Q8 cells of the summary table (pooled data-set shares, as the summary); structure only on the cells whose true
support its dictionary contains ('scored'), with WISP's rate on the same cells beside it.
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / 'paper/wisp/data'
OUT = ROOT / 'explainer/wisp/process/results.json'
METHODS = ['C1000', 'wsindy', 'sindy', 'e_sindy']
WEAKIDENT = ROOT / 'analysis/data/sideproject_residual_growth/qb2_weakident/details.csv'
STRATA = ['dim1_exact', 'dim2_exact', 'dim1_surrogate', 'dim2_surrogate', 'dim3_feasible', 'dim3_infeasible']
METRICS = ['structure', 'rec', 'gen']


def main():
    s = pd.read_csv(D / 'summary_noisy.csv')
    rates = {}
    for m in METHODS:
        for st in STRATA:
            for me in METRICS:
                r = s[(s.method == m) & (s.stratum == st) & (s.metric == me)]
                if len(r) != 1:
                    raise ValueError(f'missing row {m} {st} {me}')
                r = r.iloc[0]
                rates[f'{m}|{st}|{me}'] = None if pd.isna(r.rate) else [float(r.rate), float(r.lo), float(r.hi)]
    cells = {st: int(s[(s.method == 'C1000') & (s.stratum == st) & (s.metric == 'rec')].n_cells.iloc[0]) for st in STRATA}
    systems = {st: int(s[(s.method == 'C1000') & (s.stratum == st) & (s.metric == 'rec')].n_systems.iloc[0]) for st in STRATA}
    if sum(cells[st] for st in STRATA[:4]) != 408:
        raise ValueError('expected the 408 noisy dim-1/2 data sets of the manuscript')

    # Systems as units: per-system rate of WISP against each reference (all noisy systems, as in paper Fig. 5A).
    p = pd.read_csv(D / 'per_system_noisy.csv')
    w = p[p.method == 'C1000'].set_index('system_id')
    tally = {}
    for ref in ['wsindy', 'weak_sindy']:
        r = p[p.method == ref].set_index('system_id')
        d = (w['gen'] - r['gen']).dropna()
        tally[ref] = dict(ahead=int((d > 0).sum()), behind=int((d < 0).sum()), tied=int((d == 0).sum()))
    if tally['wsindy'] != dict(ahead=33, behind=3, tied=23):
        raise ValueError(f'system tally differs from the manuscript: {tally}')

    # WeakIdent on the same noisy cells
    pc = pd.read_csv(D / 'per_cell_all_methods.csv')
    wc = pc[(pc.method == 'C1000') & (pc.noisy == True)]
    wi = pd.read_csv(WEAKIDENT, low_memory=False)
    wi = wi[wi.method == 'weakident_native'].rename(columns={'source_initial_condition_set': 'initial_condition_set', 'noise_sigma': 'sigma',
                                                             'subsample_rho': 'rho', 'noise_realization': 'realization'})
    k = ['system_id', 'initial_condition_set', 'sigma', 'rho', 'realization']
    m = wc.merge(wi[k + ['structure_status', 'sindy_structure_hit_pruned', 'reconstruction_r2_variance_weighted_gt_0_9',
                         'generalization_r2_variance_weighted_gt_0_9']], on=k, how='left', validate='one_to_one')
    if m.structure_status.isna().any():
        raise ValueError('WeakIdent row missing for a noisy Q8 cell')
    yes = lambda col: col.astype(str).eq('True')
    n, wisp_scored = {}, {}
    for st in STRATA:
        g = m[m.stratum == st]
        if len(g) != cells[st]:
            raise ValueError(f'cell count differs in {st}')
        rates[f'weakident|{st}|rec'] = [float(yes(g.reconstruction_r2_variance_weighted_gt_0_9).mean()), None, None]
        rates[f'weakident|{st}|gen'] = [float(yes(g.generalization_r2_variance_weighted_gt_0_9).mean()), None, None]
        if 'surrogate' in st:
            rates[f'weakident|{st}|structure'] = None
            continue
        sc = g[g.structure_status == 'scored']
        rates[f'weakident|{st}|structure'] = [float(yes(sc.sindy_structure_hit_pruned).mean()), None, None]
        n[f'weakident|{st}|structure'] = int(len(sc))
        wisp_scored[st] = [float(yes(sc.structure).mean()), float(yes(sc.sindy_structure_hit_pruned).mean()), int(len(sc))]
    methods = ['C1000', 'wsindy', 'weakident', 'sindy', 'e_sindy']

    out = dict(source='paper/wisp/data (Q8, manuscript draft 2026-11-07) + Q-B B2 WeakIdent', methods=methods, strata=STRATA,
               cells=cells, systems=systems, rates=rates, n=n, wisp_on_weakident_scored=wisp_scored, tally_gen=tally)
    OUT.write_text(json.dumps(out, separators=(',', ':')), encoding='utf8')
    print('wrote', OUT, OUT.stat().st_size, 'bytes', tally)


if __name__ == '__main__':
    main()
