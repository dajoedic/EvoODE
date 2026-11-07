"""Preliminary results for the WISP story page (part C), from the Q8 interim evaluation.

WISP = arm C1000 (final configuration), size rule c, noisy cells (sigma 0.01 and 0.05), pooled over rho.
SINDy / Weak-SINDy / E-SINDy = matching library (degree 3 + sin/cos), better of two thresholds per
stratum x sigma x metric, exactly as the frozen Q5 report tables choose them (in the baselines' favour).
WSINDy = MATLAB original, configuration L-Q5, W1 on rho = 0 and W1-interp on rho = 0.5, same cells.

Inputs: the per-stratum rate table and choices of the 2026-11-07 Q8 interim evaluation (3,533/3,540 shards;
all dim-1/2 C1000 cells complete). Replaced by Q9 after W-4.
"""
import argparse, json, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'analysis/scripts/aggregate'))
from q5w_row_sources import SOURCE, uniform_rows  # noqa: E402

STRATA = ['dim1_exact', 'dim1_surrogate', 'dim2_exact', 'dim2_surrogate', 'dim3_exact']
METRICS = {'structure': 'pruned_exact', 'reconstruction': 'reconstruction_variance_weighted_hit',
           'generalization': 'generalization_variance_weighted_hit'}
WS_FIELDS = {'structure': 'sindy_structure_hit_pruned', 'reconstruction': 'reconstruction_r2_variance_weighted_gt_0_9',
             'generalization': 'generalization_r2_variance_weighted_gt_0_9'}


def truthy(v):
    return str(v).strip().lower() in ('true', '1', '1.0')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--eval-dir', type=Path, required=True, help='Q8 interim evaluation directory (rates.csv, choices.csv)')
    p.add_argument('--output', type=Path, default=ROOT / 'explainer/wisp/story/data/results_q8_prelim.json')
    a = p.parse_args()
    rates = pd.read_csv(a.eval_dir / 'rates.csv', low_memory=False)
    r = rates[(rates.arm == 'C1000') & (rates.rho == 'pooled') & (rates.configuration != 'all_ten')]
    r = r[(r.method != 'Q5') | (r.configuration == 'c')]
    out = {}
    for s in STRATA:
        block = {}
        for method, label in (('Q5', 'wisp'), ('sindy', 'sindy'), ('weak_sindy', 'weak_sindy'), ('e_sindy', 'e_sindy')):
            block[label] = {}
            for name, metric in METRICS.items():
                if name == 'structure' and not s.endswith('exact'):
                    continue
                g = r[(r.stratum == s) & (r.method == method) & (r.metric == metric)]
                if g.empty:
                    continue
                assert g.sigma.nunique() == len(g), (s, method, metric)
                block[label][name] = [int(g.numerator.sum()), int(g.denominator.sum())]
        out[s] = block

    # WSINDy (MATLAB original) on exactly the WISP C1000 noisy cells of each stratum.
    paths = {(c['cell_id'], c['arm']): c for c in
             json.loads((ROOT / 'outputs/sideproject_q8_inputs/grid/q8_paths.json').read_bytes())['cells']}
    ch = pd.read_csv(a.eval_dir / 'choices.csv', low_memory=False)
    ch = ch[(ch.arm == 'C1000') & (ch.size_rule == 'c') & (ch.sigma > 0)]
    base = ROOT / 'outputs/sideproject_q5w_wsindy'
    ws = pd.concat([pd.read_csv(base / d / 'details.csv', low_memory=False) for d in ('full_matlab', 'w1_interp_full_matlab')],
                   ignore_index=True)
    assert uniform_rows(ws).all() and ws.q5w_coefficient_source.eq(SOURCE).all()
    ws = ws[ws.q5w_configuration.str.endswith(':L-Q5')].set_index(
        ['system_id', 'source_initial_condition_set', 'noise_sigma', 'subsample_rho', 'noise_realization'])
    for s in STRATA:
        cells = [paths[cid, 'C1000'] for cid in ch.cell_id if paths[cid, 'C1000']['stratum'] == s]
        counts, n = {k: 0 for k in WS_FIELDS}, 0
        for c in cells:
            key = (c['system_id'], c['initial_condition_set'], c['sigma'], c['rho'], c['realization'])
            if key not in ws.index:
                continue
            row = ws.loc[key]
            assert row.observed_data_sha256 == c['observed_data_sha256']
            n += 1
            for k, f in WS_FIELDS.items():
                counts[k] += truthy(row[f])
        if n:
            out[s]['wsindy'] = {k: [v, n] for k, v in counts.items() if k != 'structure' or s.endswith('exact')}
    systems = sorted({paths[cid, 'C1000']['system_id'] for cid in ch.cell_id
                      if paths[cid, 'C1000']['stratum'].startswith(('dim1', 'dim2'))})
    meta = dict(source='Q8 interim evaluation 2026-11-07, arm C1000, size rule c, noisy cells pooled over rho',
                eval_dir=str(a.eval_dir), n_systems_dim12=len(systems), status='preliminary')
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(dict(meta=meta, strata=out), indent=1), encoding='utf8')
    print(json.dumps(dict(meta=meta, strata=out), indent=1))


if __name__ == '__main__':
    main()
