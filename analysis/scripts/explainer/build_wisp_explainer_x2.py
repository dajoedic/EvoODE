"""WP-X2 presentation extension; frozen scientific and WP-X1 exporters stay unchanged."""
from pathlib import Path
import argparse
import csv
import json
import math
import sys
import numpy as np
import build_wisp_explainer_data as legacy

ROOT, BASE = legacy.ROOT, legacy.ROOT / 'explainer/wisp'
sys.path.insert(0, str(ROOT / 'analysis/scripts/aggregate'))
from build_sideproject_q7_paths import significance_end
from build_sideproject_q6_paths import estimate_noise_variance, weak_noise_operators, growth_path_with_end
from threadpoolctl import threadpool_limits

RULE = ('Rule c; sigma=0.03, rho=0, realization=1; order numeric system_id, initial_condition_set, cell_id. '
        'First dim2 raw_exact=True; first dim1 truth_on_path=False; first dim1 reconstruction variance-weighted R2>=0.99 and generalization R2<0.5. '
        'Plus mandatory running example. Roles may overlap.')


def rows(name):
    with (legacy.GRID / name).open(encoding='utf8', newline='') as f:
        return list(csv.DictReader(f))


def select_featured(units):
    pool = sorted((r for r in units if r['size_rule'] == 'c' and float(r['sigma']) == .03
                   and float(r['rho']) == 0 and r['realization'] == '1'),
                  key=lambda r: (int(r['system_id']), int(r['initial_condition_set']), r['cell_id']))
    tests = {
        'exact_dim2': lambda r: r['stratum'] == 'dim2' and r['raw_exact'] == 'True',
        'missing_truth': lambda r: r['stratum'] == 'dim1' and r['truth_on_path'] == 'False',
        'generalization_failure': lambda r: r['stratum'] == 'dim1' and
            float(r['reconstruction_r2_variance_weighted'] or '-inf') >= .99 and
            float(r['generalization_r2_variance_weighted'] or 'inf') < .5,
    }
    return dict(running='sys0003_ic1_s0.03_r0_n1', **{k: next(r['cell_id'] for r in pool if test(r)) for k, test in tests.items()})


def read_julia(path):
    """One JSONL row per (cell_id,candidate_id); no silent duplicate replacement."""
    result = {}
    if path.is_file():
        for line in path.read_text(encoding='utf8').splitlines():
            row = json.loads(line)
            key = row['cell_id'], row['candidate_id']
            if key in result:
                raise ValueError('Duplicate Julia display record')
            result[key] = row
    return result


def julia_bundle(record, row, targets):
    try:
        return _julia_bundle(record, row, targets)
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return None, 'Malformed Julia record: '+str(exc)


def _julia_bundle(record, row, targets):
    """Gate all four full-grid scores and the complete target arrays before thinning."""
    if record.get('passed') is False:
        return None, record.get('reason') or 'Julia evaluation failed'
    errors, bundles = [], {}
    for kind, (t, truth) in targets.items():
        raw = record.get(kind, {})
        prediction = np.asarray(raw.get('model', []), dtype=float)
        if not np.array_equal(raw.get('t'), t) or not np.array_equal(raw.get('truth'), truth):
            return None, 'Julia target/grid mismatch'
        if prediction.shape != truth.shape or not np.isfinite(prediction).all():
            return None, 'Julia prediction absent or nonfinite'
        scores = legacy.r2_scores(truth, prediction)[:2]
        for weight, score in zip(('arithmetic', 'variance_weighted'), scores):
            stored = row.get(f'{kind}_r2_{weight}', '')
            reported = raw.get('scores', {}).get(weight)
            if stored == '' or reported is None or not math.isfinite(reported):
                return None, 'Missing stored or Julia score'
            errors.append(abs(reported-float(stored)))
        bundles[kind] = legacy.display_arrays(t, truth=truth, model=prediction)
    if max(errors) > 1e-12:
        return None, f'Julia R2 mismatch: {max(errors):.17g}'
    return {**bundles['reconstruction'], 'generalization': bundles['generalization']}, None


def extend(base=BASE, julia_path=ROOT/'outputs/wisp_explainer_julia/trajectories.jsonl'):
    data = {n: json.loads((base/'data'/f'{n}.json').read_text(encoding='utf8')) for n in ('live','manifest','results')}
    live, manifest, results = (data[n] for n in ('live','manifest','results'))
    units, candidates = rows('q5_units.csv'), rows('q5_candidates.csv')
    selected = select_featured(units)
    payload = json.loads((legacy.INPUTS/'q5_grid_paths.json').read_text(encoding='utf8'))
    byid = {c['cell_id']: c for c in payload['cells']}
    details = {c['row']['cell_id']: c for c in results['cells']}
    records = read_julia(julia_path)
    checks = []
    def targets(c):
        return {kind: legacy.read_observations(byid[cid], set()) for kind, cid in (
            ('reconstruction', f"{c['unit_id']}_s0_r0_n1"),
            ('generalization', f"sys{c['system_id']:04d}_ic{3-c['initial_condition_set']}_s0_r0_n1"))}
    def consume(record, row, cell):
        if record is None:
            return None, 'Missing Julia record'
        try:
            return julia_bundle(record, row, targets(cell))
        except (OSError, ValueError) as exc:
            return None, 'Missing or invalid clean evaluation target: '+str(exc)

    # When a Julia export exists, it is authoritative: missing/failed records withhold curves.
    if julia_path.is_file():
        for entry in results['cells']:
            row, cid = entry['row'], entry['row']['cell_id']
            record = records.get((cid, row['candidate_id']))
            bundle, reason = consume(record, row, byid[cid])
            entry.update(curves=bundle, unavailable=reason)
            checks.append(dict(cell_id=cid, candidate_id=row['candidate_id'], passed=bundle is not None, reason=reason, max_r2_error=None if record is None else record.get('max_r2_error')))
    featured = []
    for cid in dict.fromkeys(selected.values()):
        c, detail = byid[cid], details[cid]
        pool = [r for r in candidates if r['cell_id'] == cid and r['candidate_id'] in {k['candidate_id'] for k in c['candidates']}]
        true = next(json.loads(r['active_idxs']) for r in candidates if r['system_id'] == str(c['system_id']) and r['raw_exact'] == 'True')
        feature = dict(cell_id=cid, roles=[k for k,v in selected.items() if v==cid], chosen=detail['row']['candidate_id'],
                       truth_support=true, path=c['candidates'], candidates=[], detail=detail)
        for row in pool:
            n, k, mse = int(row['n_samples']), int(row['k']), float(row['mse'])
            bic = n*math.log(mse)+k*math.log(n) if mse>0 else None
            record = records.get((cid, row['candidate_id']))
            bundle, reason = (None, 'Julia display export pending') if not julia_path.is_file() else consume(record, row, c)
            feature['candidates'].append(dict(row=row, bic=bic, penalty=k*math.log(n), curves=bundle, unavailable=reason))
            checks.append(dict(cell_id=cid,candidate_id=row['candidate_id'],passed=bundle is not None,reason=reason))
        if c['dim'] == 1:
            t, x = legacy.read_observations(c, set())
            a,b,_ = legacy.build_design(t,x,0,'weak',legacy.phasec_basis(1))
            variance = estimate_noise_variance(t,x)
            incidence,_ = weak_noise_operators(t)
            operators = [incidence.multiply(np.sqrt(variance[:,0])[None,:]).tocsr()]
            path,_,ends = growth_path_with_end([a],[b],significance_end([a],operators,6.635))
            feature['stop_reference'] = dict(t=t.tolist(),x=x[:,0].tolist(),variance=variance[:,0].tolist(),
                supports=[p['support'][0] for p in path],stop_step=len(path),reason=ends[0]['end_reason'],threshold=6.635)
        featured.append(feature)
    live.update(featured=featured, gate_status=json.loads((base/'src/gates.json').read_text(encoding='utf-8-sig')),
                i18n={lang:json.loads((base/'src/i18n'/f'{lang}.json').read_text(encoding='utf8')) for lang in ('en','de')})
    manifest['inputs'][(legacy.GRID/'q5_candidates.csv').relative_to(ROOT).as_posix()]=legacy.digest(legacy.GRID/'q5_candidates.csv')
    manifest['x2_sources']={str(path.relative_to(ROOT)).replace('\\','/'):legacy.digest(path) for path in [Path(__file__),ROOT/'studies/explainer/export_wisp_display_trajectories.jl',ROOT/'analysis/scripts/aggregate/build_sideproject_q7_paths.py',ROOT/'analysis/scripts/aggregate/build_sideproject_q6_paths.py',BASE/'src/i18n/en.json',BASE/'src/i18n/de.json',BASE/'src/gates.json']}
    manifest.update(featured_selection=dict(rule=RULE,cells=selected), julia_display=dict(present=julia_path.is_file(),
        sha256=legacy.digest(julia_path) if julia_path.is_file() else None, tolerance=1e-12, checks=checks))
    # Detailed feature references are already in live; avoid duplicating their detail object.
    for feature in live['featured']:
        feature.pop('detail')
    for name, value in data.items():
        legacy.write_json(base/'data'/f'{name}.json',value)
    print(json.dumps({'featured':selected,'julia_records':len(records),'display_checks':len(checks)}))

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extend-only', action='store_true')
    args=parser.parse_args()
    with threadpool_limits(limits=1):
        if not args.extend_only:
            legacy.build()
        extend()
