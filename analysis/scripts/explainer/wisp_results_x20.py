"""Copy Q7 aggregation into contract v2; keep teaching evidence on Q5.

Only Julia display evaluations may supply result curves. No fitting or rate
calculation is performed here. Missing comparison evidence remains explicit.
"""
import copy
import csv
import json
from pathlib import Path

import build_wisp_explainer_data as legacy

ROOT = legacy.ROOT
GRID = ROOT / 'analysis/data/sideproject_residual_growth/q7_grid'
DISPLAY = ROOT / 'outputs/wisp_explainer_julia/q7_results.jsonl'


def csv_rows(path):
    with path.open(encoding='utf8', newline='') as stream:
        return list(csv.DictReader(stream))


def model_identity(row):
    """Compare numerical support and coefficients, never candidate names."""
    if not row['active_idxs'] or not row['params']:
        return None
    return (row['cell_id'], json.loads(row['active_idxs']), json.loads(row['params']))


def export_results(data, byid, read_julia, consume, q5_records=None):
    results, manifest = data['results'], data['manifest']
    rates = csv_rows(GRID / 'q7_rates.csv')
    units = csv_rows(GRID / 'q7_units.csv')
    metadata = json.loads((GRID / 'q7_run_metadata.json').read_text(encoding='utf8'))
    # The metadata declares the image commit, not a checkout or inferred run hash.
    commit = metadata['image'].rsplit(':', 1)[1]
    if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('Q7 metadata image has no full commit')
    records = read_julia(DISPLAY)
    units_hash = legacy.digest(GRID / 'q7_units.csv')
    candidates_hash = legacy.digest(GRID / 'q7_candidates.csv')
    previous = {c['row']['cell_id']: c for c in results['cells']}
    old_rows = csv_rows(legacy.GRID / 'q5_candidates.csv')
    old_bycell = {}
    for row in old_rows:
        old_bycell.setdefault(row['cell_id'], []).append(row)
    reused, evaluated, pending, no_model, details, checks = 0, 0, 0, 0, [], []
    for row in units:
        if row['size_rule'] != 'c':
            continue
        cid = row['cell_id']
        entry = copy.deepcopy(previous[cid])
        entry.update(row=row, curves=None, unavailable='Q7 Julia display export pending')
        record = records.get((cid, row['candidate_id']))
        if record is not None and (record.get('source_units_sha256') != units_hash or
                                   record.get('source_candidates_sha256') != candidates_hash):
            bundle, reason = None, 'Q7 Julia source hash mismatch'
        else:
            bundle, reason = consume(record, row, byid[cid])
        if not row['candidate_id']:
            no_model += 1
            bundle, reason = None, 'Q7 selected no candidate for this cell'
        elif record is None:
            reason = 'Q7 Julia display export pending'
        if record is not None and row['candidate_id']:
            if record.get('reused_from'):
                reused += 1
            else:
                evaluated += 1
        elif row['candidate_id']:
            pending += 1
        entry.update(curves=bundle, unavailable=reason)
        details.append(entry)
        checks.append(dict(cell_id=cid, candidate_id=row['candidate_id'],
                           passed=bundle is not None, reason=reason))
    comparison = dict(status='pending', source=legacy.COMPARISON.relative_to(ROOT).as_posix(), rates=[])
    if legacy.COMPARISON.is_file():
        comparison.update(status='available', rates=csv_rows(legacy.COMPARISON))
    comparison['note'] = ('Original MATLAB code, re-run under the JKU licence on 2026-11-05 '
                          '(W-6b), byte-identical to the earlier run.')
    provenance = dict(results['provenance'], protocol='Q7', git_hash=commit,
                      protocol_commit=commit, protocol_sha256=metadata['q7_protocol']['sha256'],
                      campaign=metadata['image'], status='interim',
                      note='Q7 interim results; final numbers come from Q9 after W-4.',
                      q7_protocol_source=metadata['q7_protocol']['path'])
    results.update(primary_method='Q7', provenance=provenance, rates=rates,
                   cells=details, comparison=comparison)
    results['method_labels'].pop('Q5', None)
    results['method_labels']['Q7'] = 'WISP (Q7)'
    for row in comparison['rates']:
        if row['method'] != 'Q7':
            results['method_labels'][row['method']] = 'WSINDy (MATLAB-Original) ' + row['method']
    files = [GRID / f'q7_{name}' for name in ('rates.csv', 'units.csv', 'candidates.csv', 'run_metadata.json')]
    if legacy.COMPARISON.is_file():
        files.append(legacy.COMPARISON)
    if DISPLAY.is_file():
        files.append(DISPLAY)
    manifest['x20_inputs'] = {p.relative_to(ROOT).as_posix(): legacy.digest(p) for p in files}
    manifest['x20_display'] = dict(present=DISPLAY.is_file(), reused=reused, evaluated=evaluated,
                                  pending=pending, no_model=no_model, checks=checks)
    # Count reuse opportunities from actual records without claiming evaluations.
    q5_records = q5_records or {}
    old_units_hash = legacy.digest(legacy.GRID / 'q5_units.csv')
    old_candidates_hash = legacy.digest(legacy.GRID / 'q5_candidates.csv')
    eligible = sum(model_identity(row) is not None and any(model_identity(row) == model_identity(old) and
                       q5_records.get((old['cell_id'], old['candidate_id']), {}).get('passed') is True and
                       q5_records[(old['cell_id'], old['candidate_id'])].get('source_units_sha256') == old_units_hash and
                       q5_records[(old['cell_id'], old['candidate_id'])].get('source_candidates_sha256') == old_candidates_hash and
                       all(row.get(kind+'_r2_'+weight) == old.get(kind+'_r2_'+weight)
                           for kind in ('reconstruction', 'generalization') for weight in ('arithmetic', 'variance_weighted'))
                       for old in old_bycell.get(row['cell_id'], []))
                   for row in units if row['size_rule'] == 'c')
    manifest['x20_display']['reuse_eligible'] = eligible
    print(json.dumps(dict(q7_cells=len(details), comparison_rows=len(comparison['rates']),
                          reuse_eligible=eligible, reused=reused, evaluated=evaluated, pending=pending)))
