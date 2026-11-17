"""Runtime context (not evidence) for the WISP draft: Orion solve seconds of the Q9 C1000 fits.

Sums the recorded per-fit solve time over the candidates of each noisy cell (one core per cell on
the Orion cluster) and reports medians per stratum; adds the recorded SINDy-family fit times
(WP-N47, also Orion) for the same cells as context.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
REC = ROOT / 'outputs/c6_vs_wisp_2026-11-17/out'  # Q9 records, image cdfaa7d (collected 17.11.)
D = Path(__file__).resolve().parent / 'data'
pat = re.compile(r"'solve_time_s': ([0-9.eE+-]+)")
rows = []
for fn in REC.glob('index_*.jsonl'):
    for line in fn.open():
        if '"C1000"' not in line:
            continue
        r = json.loads(line)
        if r.get('arm') != 'C1000' or not r.get('sigma'):
            continue
        meta = r['fit_meta']
        if isinstance(meta, dict):
            v = meta.get('solve_time_s', float('nan'))
        else:
            m = pat.search(meta)
            v = float(m.group(1)) if m else float('nan')
        rows.append(dict(cell_id=r['cell_id'], solve_s=float(v)))
fits = pd.DataFrame(rows)
cells = pd.read_csv(D / 'per_cell_all_methods.csv')
cells = cells[(cells.method == 'C1000') & cells.noisy][['cell_id', 'stratum', 'system_id']]
per_cell = fits.groupby('cell_id').agg(fits=('solve_s', 'size'), solve_s=('solve_s', 'sum')).reset_index()
per_cell = per_cell.merge(cells, on='cell_id')
out = per_cell.groupby('stratum').agg(cells=('cell_id', 'size'), median_fit_s=('solve_s', lambda s: None),
                                      median_cell_s=('solve_s', 'median'), q90_cell_s=('solve_s', lambda s: s.quantile(.9)))
out['median_fit_s'] = fits.merge(cells, on='cell_id').groupby('stratum').solve_s.median()
ref = pd.read_csv(ROOT / 'outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv', low_memory=False,
                  usecols=['method', 'polynomial_degree', 'include_sin_cos', 'noise_sigma', 'fit_elapsed_s_context'])
ref = ref[(ref.polynomial_degree == 3) & ref.include_sin_cos.astype(str).str.lower().eq('true') & (ref.noise_sigma > 0)]
print(out.round(2).to_string())
print(ref.groupby('method').fit_elapsed_s_context.median().round(4).to_string())
out.to_csv(D / 'runtime_context.csv')
