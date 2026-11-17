"""Results numbers for the closing slide of the WISP process page (explainer/wisp/process/results.json).

Source: the paper tables under paper/wisp/data/ (Q9 evidence; `paper/wisp/make_data.py`). Main comparison: noisy data
sets of dimensions 1 and 2 plus the two dimension-3 strata (systems 52/61 and 54-59) of the same summary table.
WeakIdent is the native arm at its in-favour configuration, as in the paper; its structure rate is scored only on the
data sets whose true support its dictionary contains, with WISP's rate on the same data sets beside it.
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
D = ROOT / 'paper/wisp/data'
OUT = ROOT / 'explainer/wisp/process/results.json'
SRC = {'C1000': 'C1000', 'wsindy': 'wsindy', 'weakident': 'weakident_native', 'sindy': 'sindy', 'e_sindy': 'e_sindy'}
STRATA = ['dim1_exact', 'dim2_exact', 'dim1_surrogate', 'dim2_surrogate', 'dim3_feasible', 'dim3_infeasible']
METRICS = ['structure', 'rec', 'gen']


def main():
    s = pd.read_csv(D / 'summary_noisy.csv')
    rates = {}
    for m, src in SRC.items():
        for st in STRATA:
            for me in METRICS:
                r = s[(s.method == src) & (s.stratum == st) & (s.metric == me)]
                if len(r) != 1:
                    raise ValueError(f'missing row {src} {st} {me}')
                r = r.iloc[0]
                rates[f'{m}|{st}|{me}'] = None if pd.isna(r.rate) else [float(r.rate), float(r.lo), float(r.hi)]
    first = lambda st, col: int(s[(s.method == 'C1000') & (s.stratum == st) & (s.metric == 'rec')][col].iloc[0])
    cells = {st: first(st, 'n_cells') for st in STRATA}
    systems = {st: first(st, 'n_systems') for st in STRATA}

    # Systems as units: per-system generalization of WISP against each reference (all noisy systems).
    p = pd.read_csv(D / 'per_system_noisy.csv')
    w = p[p.method == 'C1000'].set_index('system_id')
    tally = {}
    for ref in ['wsindy', 'weak_sindy']:
        r = p[p.method == ref].set_index('system_id')
        d = (w['gen'] - r['gen']).dropna()
        tally[ref] = dict(ahead=int((d > 0).sum()), behind=int((d < 0).sum()), tied=int((d == 0).sum()))

    # WISP on exactly the data sets on which WeakIdent's structure is scored
    pc = pd.read_csv(D / 'per_cell_all_methods.csv', low_memory=False)
    pc = pc[pc.noisy == True]  # noqa: E712
    wi = pc[pc.method == 'weakident_native'][['cell_id', 'structure']].rename(columns={'structure': 'wi'})
    ww = pc[pc.method == 'C1000'][['cell_id', 'stratum', 'structure']].merge(wi, on='cell_id', validate='one_to_one')
    n, wisp_scored = {}, {}
    for st in STRATA:
        if 'surrogate' in st:
            continue
        sc = ww[(ww.stratum == st) & ww.wi.notna()]
        n[f'weakident|{st}|structure'] = int(len(sc))
        wisp_scored[st] = [float(sc.structure.mean()), float(sc.wi.mean()), int(len(sc))]

    out = dict(source='paper/wisp/data (Q9 interim, 4,275 of 4,284 data sets, 2026-11-17)', methods=list(SRC),
               strata=STRATA, cells=cells, systems=systems, rates=rates, n=n, wisp_on_weakident_scored=wisp_scored,
               tally_gen=tally)
    OUT.write_text(json.dumps(out, separators=(',', ':')), encoding='utf8')
    print('wrote', OUT, OUT.stat().st_size, 'bytes', tally, cells)


if __name__ == '__main__':
    main()
