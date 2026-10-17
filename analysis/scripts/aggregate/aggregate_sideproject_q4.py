"""Aggregate frozen Q4 fits; incomplete inputs fail before writing any table."""
from __future__ import annotations
import argparse
import csv
import glob
import hashlib
import struct
import json
import math
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_sideproject_q4_paths import ROOT, OUTPUT, sha256, load_exact_supports, SUPPORT
from run_sideproject_residual_growth import PRIMARY
from phase1_diagnostic import prune_terms

REFERENCE = ROOT / 'analysis/data/paper1_phaseC_v1/hierarchy_n47_e935c37/per_run.csv'
RESULTS = ROOT / 'outputs/sideproject_q4_path_fits/results.jsonl'
# Only the frozen laptop runner and the CLI-only Orion revision are accepted.
Q4_RUNNER_PRE_FA4B_SHA256 = 'dfce09c938459c318250be60f792e9b46264e702628a902cbb0a79d1202cf648'
Q4_RUNNER_POST_FA4B_SHA256 = '2725a2927c9197fe103a4b21d8a9aad0dea111220ace5eaf99bbcd6ac56933e4'
Q4_RUNNER_HASHES = (Q4_RUNNER_PRE_FA4B_SHA256, Q4_RUNNER_POST_FA4B_SHA256)


def check_source_hash(name, digest, source_digests):
    """Accept raw bytes or CRLF-to-LF bytes, counting matches before deduplication."""
    if name not in source_digests:
        data = (ROOT/name).read_bytes()
        source_digests[name] = {
            'raw_sha256': hashlib.sha256(data).hexdigest(),
            'lf_sha256': hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest(),
            'raw_matches': 0, 'lf_matches': 0,
        }
    entry = source_digests[name]
    raw_match = digest == entry['raw_sha256']
    lf_match = digest == entry['lf_sha256']
    if not (raw_match or lf_match):
        raise ValueError(f'Julia source changed: {name}')
    # When both hashes coincide, the record matches both variants.
    entry['raw_matches'] += int(raw_match)
    entry['lf_matches'] += int(lf_match)


def result_files(inputs):
    """Expand each path/glob in order; unmatched inputs are errors."""
    specs = [inputs] if isinstance(inputs, (str, Path)) else list(inputs)
    files = []
    for spec in specs:
        text = str(spec)
        matches = [Path(p) for p in sorted(glob.glob(text))] if glob.has_magic(text) else [Path(spec)]
        if not matches or any(not p.is_file() for p in matches):
            raise FileNotFoundError(f'No result file for {text}')
        files.extend(matches)
    if not files:
        raise ValueError('No result files')
    return files


def loss_bits(record):
    """Compare Float64 losses, including the sign of zero, across platforms."""
    losses = [struct.pack('>d', float(record[regime]['loss']))
              for regime in ('training', 'generalization')]
    losses.append(struct.pack('>d', float(record['optimizer_loss'])))
    return tuple(losses)


def select(candidates, rule):
    usable = candidates if rule == 'a' else [c for c in candidates if not c['sentinel'] and not c['diverged']]
    if not usable:
        return None
    def score(c):
        if rule == 'a':
            return float(c['weak_bic'])
        if rule == 'b':
            return c['mse'] + 1e-3*c['k']
        return c['n_samples']*math.log(c['mse']) + c['k']*math.log(c['n_samples']) if c['mse'] > 0 else -math.inf
    return min(usable, key=lambda c: (score(c), c['step']))


def reference_join(frame, units, complete=True):
    frame = frame[(frame.noise_level == 0) & (frame.subsampling_ratio == 1) &
                  (((frame.method == 'EvoGrow') & (frame.configuration == 'C-1_capped')) |
                   (frame.method == 'Weak-SINDy'))].copy()
    identities = {(u['system_id'], u['initial_condition_set']) for u in units}
    frame = frame[[ (int(r.system_id), int(r.source_initial_condition_set)) in identities
                   for r in frame.itertuples() ]].copy()
    for r in frame.itertuples():
        source, target = int(r.source_initial_condition_set), int(r.target_initial_condition_set)
        if source not in (1,2) or target != 3-source or r.direction != f'IC{source}_to_IC{target}' or int(r.initial_condition_set) != source:
            raise ValueError('Reference IC/direction mismatch')
    if complete:
        for sid, ic in identities:
            group = frame[(frame.system_id == sid) & (frame.source_initial_condition_set == ic)]
            evo = group[group.method == 'EvoGrow']
            weak = group[group.method == 'Weak-SINDy']
            if len(evo) != 3 or evo.seed.nunique() != 3 or weak.configuration.nunique() != 10:
                raise ValueError('Missing reference unit/configuration')
            if not (weak.groupby('configuration').size() == 3).all():
                raise ValueError('Missing Weak-SINDy realisation')
            if weak.duplicated(['configuration','realization']).any():
                raise ValueError('Duplicate Weak-SINDy realisation')
    for column in frame.columns:
        if column.endswith('_gt_0_9'):
            regime = column.split('_r2_')[0]
            missing = frame[column].isna()
            availability = column.removesuffix('_gt_0_9') + '_available'
            if availability in frame and any(boolean(v) for v in frame.loc[missing,availability]):
                raise ValueError('Available reference metric has missing success flag')
            frame.loc[missing,column] = False
    return frame


def boolean(value):
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if str(value).lower() in ('true','1'):
        return True
    if str(value).lower() in ('false','0'):
        return False
    raise ValueError(f'Invalid boolean {value}')


def candidate_row(unit, candidate, result, truth):
    params = result['params']
    if len(params) != candidate['k'] or not all(math.isfinite(v) for v in params):
        raise ValueError('Invalid fitted parameters')
    raw = [set(eq['term_names']) for eq in candidate['equations']]
    pruned, offset = [], 0
    for eq in candidate['equations']:
        n = len(eq['term_names'])
        pruned.append(prune_terms(dict(zip(eq['term_names'], params[offset:offset+n]))))
        offset += n
    expected_indices = [[i for i,n in zip(eq['basis_indices'],eq['term_names']) if n in kept]
                        for eq,kept in zip(candidate['equations'],pruned)]
    if result['pruned_active_idxs'] != expected_indices:
        raise ValueError('Campaign/Python pruning mismatch')
    train, test = result['training'], result['generalization']
    row = dict(unit_id=unit['unit_id'], system_id=unit['system_id'],
        initial_condition_set=unit['initial_condition_set'], stratum=unit['stratum'],
        candidate_id=candidate['candidate_id'], step=candidate.get('step',0),
        origin=candidate.get('origin','upper_subset'), k=candidate['k'],
        weak_bic=candidate.get('weak_bic',math.nan), mse=train['loss'], n_samples=train['n_samples'],
        sentinel=boolean(train['sentinel']), diverged=boolean(train['diverged']),
        raw_exact=raw == truth, pruned_exact=pruned == truth,
        loss_evals=int(result['fit_meta']['loss_evals']),
        active_idxs=json.dumps(candidate['active_idxs']), params=json.dumps(params))
    for regime, record in [('reconstruction',train),('generalization',test)]:
        for kind in ('variance_weighted','arithmetic'):
            value = record['r2_'+kind]
            row[regime+'_r2_'+kind] = value
            row[regime+'_'+kind+'_hit'] = value is not None and math.isfinite(value) and value > .9 and not record['diverged']
    return row


def summarize(rows, references):
    output = []
    for stratum in sorted({r['stratum'] for r in rows}):
        group = [r for r in rows if r['stratum'] == stratum]
        primary = [r for r in group if r['size_rule'] == 'c']
        weak_choice = [r for r in group if r['size_rule'] == 'a']
        units = {(r['system_id'],r['initial_condition_set']) for r in primary}
        refs = references[[(int(r.system_id),int(r.source_initial_condition_set)) in units for r in references.itertuples()]]
        metrics = {'pruned_exact':'pruned_exact_support_match','raw_exact':'raw_exact_support_match',
                   'reconstruction_variance_weighted_hit':'reconstruction_r2_variance_weighted_gt_0_9',
                   'generalization_variance_weighted_hit':'generalization_r2_variance_weighted_gt_0_9',
                   'reconstruction_arithmetic_hit':'reconstruction_r2_arithmetic_gt_0_9',
                   'generalization_arithmetic_hit':'generalization_r2_arithmetic_gt_0_9'}
        stats = {}
        for metric, field in metrics.items():
            evo = refs[refs.method == 'EvoGrow']
            weak = refs[refs.method == 'Weak-SINDy']
            rates = [sum(boolean(v) for v in g[field])/len(g) for _,g in weak.groupby('configuration')]
            stats[metric+'_c1_numerator'] = sum(boolean(v) for v in evo[field])
            stats[metric+'_c1_denominator'] = len(evo)
            stats[metric+'_c1_rate'] = stats[metric+'_c1_numerator']/len(evo)
            stats[metric+'_ws_median'] = float(np.median(rates))
            stats[metric+'_ws_min'], stats[metric+'_ws_max'] = min(rates),max(rates)
            stats[metric+'_ws_configuration_counts'] = json.dumps({
                str(c): dict(numerator=sum(boolean(v) for v in g[field]),denominator=len(g))
                for c,g in weak.groupby('configuration')},sort_keys=True)
            for rule in ('a','b','c','upper_path','upper_subset'):
                selected = [r for r in group if r['size_rule'] == rule]
                stats[metric+'_'+rule+'_numerator'] = sum(r[metric] for r in selected)
                stats[metric+'_'+rule+'_denominator'] = len(selected)
        den = len(primary)
        structure = sum(r['pruned_exact'] for r in primary)
        general = sum(r['generalization_variance_weighted_hit'] for r in primary)
        passed = {
            'R7': structure/den >= stats['pruned_exact_c1_rate']+.1 and general/den >= stats['generalization_variance_weighted_hit_c1_rate'],
            'R8': structure/den >= stats['pruned_exact_ws_median'] and general/den >= stats['generalization_variance_weighted_hit_ws_median'],
            'R9': structure >= sum(r['pruned_exact'] for r in weak_choice)}
        for rule in ('R7','R8','R9'):
            output.append(dict(stratum=stratum, rule=rule, numerator=structure, denominator=den,
                generalization_numerator=general, generalization_denominator=den,
                passed=passed[rule] if stratum in PRIMARY else None,
                decision=('pass' if passed[rule] else 'fail') if stratum in PRIMARY else 'reported_only',
                total_loss_evals=sum(r['total_loss_evals'] for r in primary),
                **stats))
    return output


def run(results_path=RESULTS, paths_path=OUTPUT, output=None):
    output = output or OUTPUT.parent
    targets = [output/n for n in ('q4_units.csv','q4_candidates.csv','q4_rules_by_stratum.csv','q4_run_metadata.json')]
    if any(p.exists() for p in targets):
        raise FileExistsError('Refusing to overwrite Q4 tables')
    payload = json.loads(paths_path.read_text())
    if payload['protocol_commit'] != '24ede2d' or len(payload['units']) != 60 or len({u['unit_id'] for u in payload['units']}) != 60:
        raise ValueError('Invalid Q4 paths')
    for name,digest in payload['input_sha256'].items():
        if sha256(ROOT/name) != digest:
            raise ValueError(f'Changed input: {name}')
    files = result_files(results_path)
    results = [json.loads(line) for path in files for line in path.read_text().splitlines() if line.strip()]
    duplicates_compared = 0
    paths_digest = sha256(paths_path)
    weak_digest = sha256(ROOT/'analysis/data/sideproject_residual_growth/q3_weak_starts.json')
    q3_digest = sha256(ROOT/'outputs/sideproject_q3_weak_start/results.jsonl')
    source_digests = {}
    bykey = {}
    for r in results:
        key = (r['unit_id'],r['candidate_id'])
        provenance = r['provenance']
        if provenance['paths_sha256'] != paths_digest or provenance['runner_sha256'] not in Q4_RUNNER_HASHES:
            raise ValueError('Fit provenance mismatch')
        if provenance['q3_weak_sha256'] != weak_digest:
            raise ValueError('Q3 weak start source changed')
        if provenance['protocol_commit'] != '24ede2d':
            raise ValueError('Wrong fit protocol')
        if provenance['q3_results_sha256'] != q3_digest:
            raise ValueError('Q3 control source changed')
        for name,digest in provenance['source_sha256'].items():
            check_source_hash(name, digest, source_digests)
        if not r['trajectory_control']['passed']:
            raise ValueError('Trajectory control failed')
        if key in bykey:
            duplicates_compared += 1
            if loss_bits(r) != loss_bits(bykey[key]):
                raise ValueError(f'Duplicate candidate loss is not bit-identical: {key}')
        else:
            bykey[key] = r
    if len({r['provenance']['settings_fingerprint'] for r in results}) != 1:
        raise ValueError('Optimizer settings differ')
    control = bykey.pop(('sys0001_ic1','control_true'),None)
    if not control or not control['control_passed'] or struct.pack('>d', float(control['training']['loss'])) != struct.pack('>d', float(control['expected_loss'])):
        raise ValueError('Missing Q3 W1 control')
    original_control = [json.loads(line) for line in (ROOT/'outputs/sideproject_q3_weak_start/results.jsonl').read_text().splitlines() if line.strip()]
    original_control = [r for r in original_control if r['unit_id'] == 'sys0001_ic1']
    if len(original_control) != 1 or control['expected_loss'] != original_control[0]['W1']['loss']:
        raise ValueError('Q3 W1 control reference mismatch')
    expected = {(u['unit_id'],c['candidate_id']) for u in payload['units'] for c in u['candidates']+u['upper_candidates']}
    if set(bykey) != expected:
        raise ValueError('Missing or unexpected unit/candidate')
    _, systems = load_exact_supports(ROOT/SUPPORT)
    truth_by_id = {int(s['system_id']):[set(eq) for eq in s['support_terms']] for s in systems}
    candidates, units = [], []
    for u in payload['units']:
        truth = truth_by_id[u['system_id']]
        pool = [candidate_row(u,c,bykey[u['unit_id'],c['candidate_id']],truth) for c in u['candidates']]
        upper = candidate_row(u,u['upper_candidates'][0],bykey[u['unit_id'],'upper_subset'],truth)
        candidates.extend(pool+[upper])
        total = sum(r['loss_evals'] for r in pool)
        choices = {rule:select(pool,rule) for rule in ('a','b','c')}
        # Report every state at the oracle size; the protocol does not break repeated-size ties.
        oracle = [r for r in pool if r['k'] == sum(map(len,truth))]
        choices['upper_subset'] = upper
        for rule, chosen in list(choices.items()) + [('upper_path',r) for r in oracle or [None]]:
            base = dict(unit_id=u['unit_id'],system_id=u['system_id'],initial_condition_set=u['initial_condition_set'],
                        stratum=u['stratum'],size_rule=rule,n_candidates=len(pool),total_loss_evals=total)
            if chosen:
                base.update(chosen)
            else:
                base.update(candidate_id=None,raw_exact=False,pruned_exact=False,
                    **{regime+'_'+kind+'_hit':False for regime in ('reconstruction','generalization') for kind in ('variance_weighted','arithmetic')})
            units.append(base)
    references = reference_join(pd.read_csv(REFERENCE),payload['units'])
    rules = summarize(units,references)
    metadata = dict(protocol_commit='24ede2d',units=60,path_candidates=sum(len(u['candidates']) for u in payload['units']),
        upper_path_policy='all matching-size states reported individually, no new oracle tie rule; upper_path summary denominator counts states',
        duplicates_compared=duplicates_compared,
        source_sha256=source_digests,
        runner_sha256_accepted=list(Q4_RUNNER_HASHES),
        runner_sha256_observed=sorted({r['provenance']['runner_sha256'] for r in results}),
        settings_fingerprint=results[0]['provenance']['settings_fingerprint'],
        result_files=[str(p) for p in files],
        input_sha256={(str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)):sha256(p) for p in [paths_path,*files,REFERENCE,ROOT/SUPPORT,
            Path(__file__),ROOT/'docs/sideproject_residual_growth_protocol_q4.md']})
    output.mkdir(parents=True,exist_ok=True)
    for path, records in zip(targets[:3],[units,candidates,rules]):
        pd.DataFrame(records).to_csv(path,index=False)
    targets[3].write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',nargs='+',default=[RESULTS],help='Result file paths and/or quoted globs')
    parser.add_argument('--paths',type=Path,default=OUTPUT)
    parser.add_argument('--output-dir',type=Path,default=OUTPUT.parent)
    args = parser.parse_args()
    print(json.dumps(run(args.input,args.paths,args.output_dir),indent=2))
