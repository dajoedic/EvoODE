"""Per-cell tables for the WISP paper (protocol Q9-A §1): WISP choices and every reference on identical cells.

Production input is Q9 (`--protocol Q9`). For the dry run demanded by Q9-A §1.3 the same code reads the Q8 C1000 cells
(`--protocol Q8 --arm C1000`); nothing here depends on which run it reads, except the provenance check.

WISP: the frozen Q8 conversion (`aggregate_sideproject_q8.rows_for_cells`, which imports the Q5 candidate scoring and
selection), size rules (a) weak BIC, (b) EvoGrow objective, (c) trajectory BIC. A cell whose records are not complete
is written with status `missing` and every metric False (Q9-A §1.2). No reference configuration is chosen here; all
configurations are kept and the in-favour choice is made by `q9a_claims.py`.

Outputs (refuses to overwrite): cells.csv, wisp_choices.csv, reference_cells.csv, build_metadata.json.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import aggregate_sideproject_q5 as q5
import aggregate_sideproject_q7 as q7
import aggregate_sideproject_q8 as q8

ROOT = q8.ROOT
KEY = ['system_id', 'initial_condition_set', 'sigma', 'rho', 'realization']
REF_KEY = {'source_initial_condition_set': 'initial_condition_set', 'noise_sigma': 'sigma', 'subsample_rho': 'rho',
           'noise_realization': 'realization'}
# per-cell metric name -> (WISP choice column, reference column)
METRICS = {'structure': ('pruned_exact', 'sindy_structure_hit_pruned'),
           'raw': ('raw_exact', 'sindy_structure_hit_raw'),
           'rec': ('reconstruction_variance_weighted_hit', 'reconstruction_r2_variance_weighted_gt_0_9'),
           'gen': ('generalization_variance_weighted_hit', 'generalization_r2_variance_weighted_gt_0_9')}
N47 = ROOT / 'outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv'
WSINDY = [ROOT / 'outputs/sideproject_q5w_wsindy/full_matlab/details.csv',
          ROOT / 'outputs/sideproject_q5w_wsindy/w1_interp_full_matlab/details.csv']
WEAKIDENT = ROOT / 'analysis/data/sideproject_residual_growth/qb2_weakident_tau/details.csv.gz'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def boolean(v):
    if isinstance(v, str):
        return v.strip().lower() == 'true'
    return bool(v) if v == v and v is not None else False


def paper_stratum(c):
    """Q9 §3 strata; dimension-3 exact split into 52/61 (feasible under bound 10) and 54-59."""
    if c['stratum'] == 'dim3_exact':
        return 'dim3_exact_5261' if c['system_id'] in (52, 61) else 'dim3_exact_5459'
    return c['stratum']


def condition(sigma, rho):
    if sigma == 0:
        return 'clean' if rho == 0 else 'sub'
    return f's{sigma:g}_r{rho:g}'


def load_cells(paths, arm):
    payload = json.loads(Path(paths).read_bytes())
    cells = [c for c in payload['cells'] if c['arm'] == arm]
    if len({c['cell_id'] for c in cells}) != len(cells):
        raise ValueError('Duplicate cell for the arm')
    return payload, cells


def load_records(inputs, cells, protocol, paths_sha):
    want = {c['cell_id'] for c in cells}
    arm = cells[0]['arm']
    bykey, fingerprints = {}, set()
    for r in q7.read_records(inputs):
        if r.get('arm') != arm or r['cell_id'] not in want:
            continue
        p = r['provenance']
        if p['protocol'] != protocol:
            raise ValueError('Record of another protocol: ' + str(p['protocol']))
        if protocol == 'Q9' and p['paths_sha256'] != paths_sha:
            raise ValueError('Q9 record bound to another path file')
        if not all(r['trajectory_control'].values()):
            raise ValueError('Trajectory control failed in ' + r['cell_id'])
        fingerprints.add(p['settings_fingerprint'])
        key = r['cell_id'], r['arm'], r['candidate_id']
        if key in bykey and q5.canonical_bits(r) != q5.canonical_bits(bykey[key]):
            raise ValueError('Duplicate records differ: ' + str(key))
        bykey[key] = r
    if len(fingerprints) > 1:
        raise ValueError('More than one settings fingerprint')
    return bykey, fingerprints


def wisp_choices(cells, records):
    complete = [c for c in cells if all((c['cell_id'], c['arm'], k['candidate_id']) in records for k in c['candidates'])]
    for c in complete:
        for k in c['candidates']:
            if records[c['cell_id'], c['arm'], k['candidate_id']]['observed_data_sha256'] != c['observed_data_sha256']:
                raise ValueError('Observed data hash differs in ' + c['cell_id'])
    _, choices = q8.rows_for_cells(complete, records)
    rows = []
    for r in choices:
        row = {k: r.get(k) for k in ('cell_id', 'size_rule', 'candidate_id', 'k', 'k_true', 'size_error',
                                    'truth_on_path', 'n_candidates', 'total_loss_evals', 'total_ode_solves',
                                    'last_path_state')}
        for m, (w, _) in METRICS.items():
            row[m] = bool(r.get(w, False)) if w in r else np.nan
        row['status'] = 'complete'
        rows.append(row)
    done = {c['cell_id'] for c in complete}
    for c in cells:
        if c['cell_id'] in done:
            continue
        exact = c['representability'] == 'exact'
        for rule in ('a', 'b', 'c'):
            rows.append(dict(cell_id=c['cell_id'], size_rule=rule, status='missing', truth_on_path=None,
                             **{m: (False if exact or m in ('rec', 'gen') else np.nan) for m in METRICS}))
    out = pd.DataFrame(rows)
    surrogate = {c['cell_id'] for c in cells if c['representability'] != 'exact'}
    out.loc[out.cell_id.isin(surrogate), ['structure', 'raw']] = np.nan
    return out


def cell_table(cells):
    return pd.DataFrame([dict(cell_id=c['cell_id'], unit_id=c['unit_id'], system_id=c['system_id'], dim=c['dim'],
                              initial_condition_set=c['initial_condition_set'], sigma=float(c['sigma']),
                              rho=float(c['rho']), realization=int(c['realization']),
                              condition=condition(float(c['sigma']), float(c['rho'])),
                              representability=c['representability'], stratum=paper_stratum(c),
                              observed_data_sha256=c['observed_data_sha256']) for c in cells])


def reference_rows(frame, cells, method_of, config_of, source):
    frame = frame.rename(columns=REF_KEY)
    frame = frame.merge(cells[KEY + ['cell_id', 'representability', 'observed_data_sha256']], on=KEY,
                        suffixes=('', '_cell'), validate='many_to_one')
    bad = frame.observed_data_sha256 != frame.observed_data_sha256_cell
    if bad.any():
        raise ValueError(f'{source}: observed data hash differs on {int(bad.sum())} rows')
    out = pd.DataFrame({'cell_id': frame.cell_id, 'method': method_of(frame), 'config': config_of(frame),
                        'source': source})
    for m, (_, field) in METRICS.items():
        out[m] = frame[field].map(boolean).astype(float).to_numpy()
    exact = frame.representability.eq('exact').to_numpy()
    if 'structure_status' in frame:
        exact &= frame.structure_status.eq('scored').to_numpy()
    out.loc[~exact, ['structure', 'raw']] = np.nan
    if out.duplicated(['cell_id', 'method', 'config']).any():
        raise ValueError(source + ': duplicate reference rows')
    return out


def references(cells, extra):
    parts = []
    n47 = pd.read_csv(N47, low_memory=False)
    n47 = n47[n47.method.isin(['sindy', 'weak_sindy', 'e_sindy']) & n47.include_sin_cos.map(boolean)
              & (n47.polynomial_degree == 3)]
    parts.append(reference_rows(n47, cells, lambda f: f.method, lambda f: f.method_config_id, 'WP-N47'))
    ws = pd.concat([pd.read_csv(p, low_memory=False) for p in WSINDY], ignore_index=True)
    ws = ws[ws.q5w_configuration.str.endswith(':L-Q5')]
    ws = ws[((ws.method == 'W1') & (ws.subsample_rho == 0)) | ((ws.method != 'W1') & (ws.subsample_rho == 0.5))]
    parts.append(reference_rows(ws, cells, lambda f: 'wsindy', lambda f: f.q5w_configuration, 'WSINDy MATLAB'))
    if WEAKIDENT.exists():
        wi = pd.read_csv(WEAKIDENT, low_memory=False)
        wi = wi[wi.dimension.lt(4)]  # dimension 4 is not supported by the reference code: dropped pairwise
        parts.append(reference_rows(wi, cells, lambda f: f.method, lambda f: f.method_config_id, 'Q-B B2'))
    for spec in extra:
        name, path = spec.split('=', 1)
        f = pd.concat([pd.read_csv(p, low_memory=False) for p in sorted(Path(path).glob('**/details*.csv*'))],
                      ignore_index=True)
        parts.append(reference_rows(f, cells, lambda g, n=name: n + ':' + g.method, lambda g: g.method_config_id, name))
    return pd.concat(parts, ignore_index=True)


def run(args):
    out = Path(args.output_dir)
    if out.exists():
        raise FileExistsError('Refusing to overwrite ' + str(out))
    payload, cells = load_cells(args.paths, args.arm)
    records, fingerprints = load_records(args.input, cells, args.protocol, sha256(args.paths))
    choices = wisp_choices(cells, records)
    ct = cell_table(cells)
    refs = references(ct, args.reference or [])
    out.mkdir(parents=True)
    ct.to_csv(out / 'cells.csv', index=False)
    choices.to_csv(out / 'wisp_choices.csv', index=False)
    refs.to_csv(out / 'reference_cells.csv', index=False)
    meta = dict(protocol=args.protocol, arm=args.arm, paths=str(args.paths), paths_sha256=sha256(args.paths),
                cells=len(cells), complete_cells=int(choices[choices.size_rule == 'c'].status.eq('complete').sum()),
                settings_fingerprints=sorted(fingerprints),
                reference_rows=refs.groupby('method').size().to_dict(),
                reference_sources={'WP-N47': str(N47), 'WSINDy': [str(p) for p in WSINDY],
                                   'WeakIdent': str(WEAKIDENT) if WEAKIDENT.exists() else None,
                                   'extra': args.reference or []})
    (out / 'build_metadata.json').write_text(json.dumps(meta, indent=1) + '\n', encoding='utf8')
    return meta


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--paths', type=Path, required=True)
    p.add_argument('--arm', default='C1000')
    p.add_argument('--protocol', choices=('Q8', 'Q9'), required=True)
    p.add_argument('--input', nargs='+', required=True, help='record files or directories')
    p.add_argument('--reference', action='append', help='NAME=dir with details*.csv in the WP-N47 schema (B1, B3)')
    p.add_argument('--output-dir', type=Path, required=True)
    print(json.dumps(run(p.parse_args()), indent=1))
