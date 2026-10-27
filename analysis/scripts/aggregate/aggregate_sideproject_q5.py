"""Frozen Q5 reporting, with mandatory data, Q4 and duplicate controls before output."""
from __future__ import annotations
import argparse
import json
import math
import struct
from pathlib import Path
import numpy as np
import pandas as pd
from aggregate_sideproject_q4 import (
    ROOT, SUPPORT, load_exact_supports, sha256, result_files, select,
    candidate_row, boolean, check_source_hash, loss_bits,
)
from build_sideproject_q5_paths import BASE, Q4, Q4_RESULTS

REFERENCE = ROOT/'outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv'
METRICS = {'raw_exact':'sindy_structure_hit_raw', 'pruned_exact':'sindy_structure_hit_pruned',
    **{f'{r}_{k}_hit':f'{r}_r2_{"arithmetic_mean" if k == "arithmetic" else k}_gt_0_9'
       for r in ('reconstruction','generalization') for k in ('arithmetic','variance_weighted')}}


def canonical_bits(value):
    """Strict duplicate comparison, including signed floating-point zero."""
    if isinstance(value, float):
        return ('float', struct.pack('>d', value))
    if isinstance(value, dict):
        return tuple((k, canonical_bits(v)) for k,v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(canonical_bits(v) for v in value)
    return (type(value).__name__, value)


def controls(payload, records, paths_path, references, q4_records, q4_payload):
    if payload['protocol_commit'] != 'f737939':
        raise ValueError('Wrong Q5 protocol')
    cells = payload['cells']
    if len(cells) != {'probe':9,'controls':48,'grid':1632}.get(payload['mode']):
        raise ValueError('Incomplete Q5 path scope')
    for uid in {c['unit_id'] for c in cells}:
        if not any(c['unit_id']==uid and c['sigma']==c['rho']==0 for c in cells):
            raise ValueError('Missing clean Q4 control cell')
    if len({c['cell_id'] for c in cells}) != len(cells):
        raise ValueError('Duplicate path cell')
    q4map = {}
    for r in q4_records:
        if r['candidate_id'] == 'control_true':
            continue
        key = r['unit_id'], r['candidate_id']
        if key in q4map and loss_bits(r) != loss_bits(q4map[key]):
            raise ValueError('Q4 reference duplicates differ')
        q4map[key] = r
    fingerprints = {r['provenance']['settings_fingerprint'] for r in q4_records}
    if len(fingerprints) != 1:
        raise ValueError('Q4 fingerprint is not unique')
    fingerprint = next(iter(fingerprints))
    settings = q4_records[0]['optimizer_settings']
    bykey, duplicates, sources = {}, 0, {}
    paths_digest = sha256(paths_path)
    runner = ROOT/'studies/regression/sideproject_q5_noise_fits.jl'
    raw = runner.read_bytes()
    import hashlib
    runner_hashes = {hashlib.sha256(raw).hexdigest(), hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest()}
    for r in records:
        p = r['provenance']
        if (p['paths_sha256'] != paths_digest or p['protocol_commit'] != 'f737939'
                or p['settings_fingerprint'] != fingerprint or r['optimizer_settings'] != settings
                or p['runner_sha256'] not in runner_hashes):
            raise ValueError('Optimizer or provenance control failed')
        expected_index = payload['input_sha256']['outputs/phase_c_c6_data_conditions_5dd1df8/index.csv']
        if p['index_sha256'] != expected_index:
            raise ValueError('Export index changed')
        if not r['trajectory_control']['passed']:
            raise ValueError('Clean trajectory control failed')
        if not p['source_sha256']:
            raise ValueError('Missing source inventory')
        if set(p['source_sha256']) != set(q4_records[0]['provenance']['source_sha256']) | {
                'studies/regression/sideproject_q4_path_fits.jl', 'studies/regression/sideproject_q5_noise_fits.jl'}:
            raise ValueError('Source inventory mismatch')
        for name,digest in p['source_sha256'].items():
            check_source_hash(name,digest,sources)
        key = r['cell_id'], r['candidate_id']
        if key in bykey:
            if canonical_bits(r) != canonical_bits(bykey[key]):
                raise ValueError('Duplicate records are not bit-identical')
            duplicates += 1
        bykey[key] = r
    expected = {(c['cell_id'],k['candidate_id']) for c in cells for k in c['candidates']+c['upper_candidates']}
    if set(bykey) != expected:
        raise ValueError('Missing or unexpected candidate')
    q4units = {u['unit_id']:u for u in q4_payload['units']}
    for c in cells:
        ref = references[(references.system_id == c['system_id']) &
            (references.source_initial_condition_set == c['initial_condition_set']) &
            (references.noise_sigma == c['sigma']) & (references.subsample_rho == c['rho']) &
            (references.noise_realization == c['realization'])]
        if ref.empty or set(ref.observed_data_sha256) != {c['observed_data_sha256']}:
            raise ValueError('Baseline data hash mismatch or missing cell')
        if any(ref.target_initial_condition_set != 3-c['initial_condition_set']):
            raise ValueError('Baseline target IC mismatch')
        for candidate in c['candidates']+c['upper_candidates']:
            r = bykey[c['cell_id'], candidate['candidate_id']]
            if (r['unit_id'],r['sigma'],r['rho'],r['realization'],r['observed_data_sha256']) != (
                    c['unit_id'],c['sigma'],c['rho'],c['realization'],c['observed_data_sha256']):
                raise ValueError('Record cell identity mismatch')
        if c['sigma'] == c['rho'] == 0:
            u = q4units[c['unit_id']]
            if c['candidates'] != u['candidates'] or c['upper_candidates'] != u['upper_candidates']:
                raise ValueError('Q4 candidate identity failed')
            for k in c['candidates']+c['upper_candidates']:
                r, ref = bykey[c['cell_id'],k['candidate_id']], q4map[c['unit_id'],k['candidate_id']]
                if loss_bits(r) != loss_bits(ref) or canonical_bits(r['params']) != canonical_bits(ref['params']):
                    raise ValueError('Q4 clean loss/parameter bit identity failed')
                if struct.pack('>d',r['reconstruction']['loss']) != struct.pack('>d',ref['training']['loss']):
                    raise ValueError('Q4 reconstruction identity failed')
            # Same candidate lists and loss bits imply the same deterministic choices;
            # explicitly check the IDs for each of the three rules as well.
            for rule in ('a','b','c'):
                def pool(q5):
                    return [dict(k, mse=(bykey[c['cell_id'],k['candidate_id']] if q5 else q4map[c['unit_id'],k['candidate_id']])['training']['loss'],
                        n_samples=(bykey[c['cell_id'],k['candidate_id']] if q5 else q4map[c['unit_id'],k['candidate_id']])['training']['n_samples'],
                        sentinel=(bykey[c['cell_id'],k['candidate_id']] if q5 else q4map[c['unit_id'],k['candidate_id']])['training']['sentinel'],
                        diverged=(bykey[c['cell_id'],k['candidate_id']] if q5 else q4map[c['unit_id'],k['candidate_id']])['training']['diverged']) for k in c['candidates']]
                a,b = select(pool(True),rule), select(pool(False),rule)
                if (a and a['candidate_id']) != (b and b['candidate_id']):
                    raise ValueError('Q4 chosen model identity failed')
    return bykey, dict(duplicates_compared=duplicates, settings_fingerprint=fingerprint, source_sha256=sources)


def rows_for_cells(cells, bykey):
    _, systems = load_exact_supports(ROOT/SUPPORT)
    truth_by_id = {s['system_id']:[set(e) for e in s['support_terms']] for s in systems}
    allrows, choices = [], []
    for c in cells:
        truth = truth_by_id[c['system_id']]
        pool, upper = [], []
        for k in c['candidates']+c['upper_candidates']:
            result = bykey[c['cell_id'],k['candidate_id']]
            row = candidate_row(c,k,result,truth)
            # Selection uses observed training; reporting uses clean reconstruction.
            for kind in ('variance_weighted','arithmetic'):
                value = result['reconstruction']['r2_'+kind]
                row['reconstruction_r2_'+kind] = value
                row['reconstruction_'+kind+'_hit'] = value is not None and math.isfinite(value) and value > .9 and not result['reconstruction']['diverged']
            row.update({name:c[name] for name in ('cell_id','sigma','rho','realization','ended_at_cap')})
            row.update(ode_solves=int(result['fit_meta']['ode_solves']),
                evaluation_ode_solves=int(result['evaluation_ode_solves']),
                observed_start_mse=row['mse'], clean_start_mse=result['clean_ic_observed_mse'])
            (upper if k['candidate_id']=='upper_subset' else pool).append(row)
        allrows.extend(pool+upper)
        selections = [(rule,select(pool,rule)) for rule in ('a','b','c')]
        selections += [('upper_subset',upper[0])]
        oracle = [r for r in pool if r['k'] == sum(map(len,truth))]
        selections += [('upper_path',r) for r in oracle or [None]]
        for rule, chosen in selections:
            base = {name:c[name] for name in ('unit_id','system_id','initial_condition_set','stratum','cell_id','sigma','rho','realization','ended_at_cap')}
            base.update(size_rule=rule, n_candidates=len(pool), total_loss_evals=sum(r['loss_evals'] for r in pool),
                total_ode_solves=sum(r['ode_solves'] for r in pool),
                total_evaluation_ode_solves=sum(r['evaluation_ode_solves'] for r in pool+upper),
                upper_loss_evals=sum(r['loss_evals'] for r in upper),
                upper_ode_solves=sum(r['ode_solves'] for r in upper),
                truth_on_path=any(r['raw_exact'] for r in pool), k_true=sum(map(len,truth)))
            if chosen is None:
                base.update({m:False for m in METRICS})
                base.update(candidate_id=None, k=None, observed_start_mse=None, clean_start_mse=None)
            else:
                base.update(chosen)
            base['last_path_state'] = chosen is not None and chosen['candidate_id'] == pool[-1]['candidate_id']
            base['size_error'] = None if base['k'] is None else base['k']-base['k_true']
            choices.append(base)
    return allrows, choices


def report_tables(choices, references):
    frame = pd.DataFrame(choices)
    cell_keys = frame[['system_id','initial_condition_set','stratum','sigma','rho','realization']].drop_duplicates()
    references = references.merge(cell_keys, left_on=['system_id','source_initial_condition_set','noise_sigma','subsample_rho','noise_realization'],
        right_on=['system_id','initial_condition_set','sigma','rho','realization'], validate='many_to_one')
    reports, diagnostics = [], []
    # Clean cells are controls only. sigma=0 means subsampling-only.
    frame = frame[(frame.sigma != 0) | (frame.rho != 0)]
    for (stratum,sigma), group in frame.groupby(['stratum','sigma']):
        for rho in [None, *sorted(group.rho.unique())]:
            g = group if rho is None else group[group.rho==rho]
            cells = set(g.cell_id)
            unit_ids = set(g.unit_id)
            primary = g[g.size_rule=='c']
            # All references for precisely these observed cells.
            pooled = references[(references.stratum==stratum) & (references.sigma==sigma)]
            refs = pooled if rho is None else pooled[pooled.rho==rho]
            common = dict(stratum=stratum,sigma=sigma,rho='pooled' if rho is None else rho, n_units=len(unit_ids),n_cells=len(cells))
            for rule, selected in g.groupby('size_rule'):
                for metric in METRICS:
                    num, den = int(selected[metric].sum()), len(selected)
                    reports.append(dict(common,method='Q5',configuration=rule,metric=metric,numerator=num,denominator=den,rate=num/den))
            for metric, field in METRICS.items():
                for method in ('sindy','weak_sindy','e_sindy'):
                    method_refs = refs[refs.method==method]
                    matching = method_refs[method_refs.include_sin_cos.map(boolean) & (method_refs.polynomial_degree==3)]
                    configs = []
                    for config, r in matching.groupby('method_config_id'):
                        if len(r) != len(cells) or r.duplicated(['system_id','source_initial_condition_set','noise_sigma','subsample_rho','noise_realization']).any():
                            raise ValueError('Incomplete matching baseline configuration')
                        num = sum(boolean(v) for v in r[field])
                        configs.append((num/len(r),str(config),num,len(r)))
                    if len(configs) != 2:
                        raise ValueError('Expected two matching-library thresholds')
                    # Threshold chosen per stratum x sigma x metric on pooled rho,
                    # then reused for each rho-specific report.
                    matching_pooled = pooled[(pooled.method==method) & pooled.include_sin_cos.map(boolean) & (pooled.polynomial_degree==3)]
                    best = min([( -sum(boolean(v) for v in r[field])/len(r), str(config)) for config,r in matching_pooled.groupby('method_config_id')])[1]
                    rate, config, num, den = next(v for v in configs if v[1]==best)
                    reports.append(dict(common,method=method,configuration=config,metric=metric,numerator=num,denominator=den,rate=rate))
                    if method == 'weak_sindy':
                        rates = []
                        for config,r in method_refs.groupby('method_config_id'):
                            if len(r) != len(cells) or r.duplicated(['system_id','source_initial_condition_set','noise_sigma','subsample_rho','noise_realization']).any():
                                raise ValueError('Incomplete Weak-SINDy configuration')
                            rates.append(sum(boolean(v) for v in r[field])/len(r))
                        if len(rates) != 10:
                            raise ValueError('Expected ten Weak-SINDy configurations')
                        reports.append(dict(common,method='weak_sindy',configuration='all_ten',metric=metric,
                            denominator=len(cells),rate=float(np.median(rates)),min_rate=min(rates),max_rate=max(rates)))
            diagnostics.append(dict(common,
                D1_cap_numerator=int(primary.ended_at_cap.sum()),D1_denominator=len(primary),
                D1_cap_rate=float(primary.ended_at_cap.mean()),
                D2_last_numerator=int(primary.last_path_state.sum()),D2_denominator=len(primary),
                D2_last_rate=float(primary.last_path_state.mean()),
                D3_truth_numerator=int(primary.truth_on_path.sum()),D3_denominator=len(primary),
                D3_truth_rate=float(primary.truth_on_path.mean()),
                D4_size_errors=json.dumps({str(k):int(v) for k,v in primary.size_error.fillna('unselected').value_counts().items()},sort_keys=True),
                D5_chosen_count=int(primary.candidate_id.notna().sum()),
                D5_observed_start_mse_mean=primary.observed_start_mse.mean(),D5_clean_start_mse_mean=primary.clean_start_mse.mean(),
                candidates=int(primary.n_candidates.sum()),loss_evals=int(primary.total_loss_evals.sum()),
                ode_solves=int(primary.total_ode_solves.sum()),upper_loss_evals=int(primary.upper_loss_evals.sum()),
                upper_ode_solves=int(primary.upper_ode_solves.sum()),evaluation_ode_solves=int(primary.total_evaluation_ode_solves.sum())))
    return reports, diagnostics


def run(inputs, paths_path=BASE/'q5_grid_paths.json', output=ROOT/'analysis/data/sideproject_residual_growth',
        reference=REFERENCE, q4_inputs=Q4_RESULTS):
    targets = [output/f'q5_{name}' for name in ('candidates.csv','units.csv','rates.csv','diagnostics.csv','run_metadata.json')]
    if any(p.exists() for p in targets):
        raise FileExistsError('Refusing to overwrite Q5 tables')
    payload = json.loads(paths_path.read_text())
    for name,digest in payload['input_sha256'].items():
        if sha256(ROOT/name) != digest:
            raise ValueError(f'Changed frozen input: {name}')
    files = result_files(inputs)
    records = [json.loads(line) for p in files for line in p.read_text().splitlines() if line.strip()]
    q4records = [json.loads(line) for p in result_files(q4_inputs) for line in p.read_text().splitlines() if line.strip()]
    refs = pd.read_csv(reference,low_memory=False)
    bykey, metadata = controls(payload,records,paths_path,refs,q4records,json.loads(Q4.read_text()))
    candidates, choices = rows_for_cells(payload['cells'],bykey)
    rates, diagnostics = report_tables(choices,refs)
    metadata.update(protocol_commit='f737939',cells=len(payload['cells']),
        result_files=[str(p) for p in files], paths_sha256=sha256(paths_path), reference_sha256=sha256(reference),
        upper_path_policy='all matching-size states, as Q4; state counts are explicit',
        duplicate_policy='entire parsed record bit-identical, including timing fields')
    output.mkdir(parents=True,exist_ok=True)
    for target, rows in zip(targets,[candidates,choices,rates,diagnostics]):
        pd.DataFrame(rows).to_csv(target,index=False)
    targets[-1].write_text(json.dumps(metadata,indent=2)+'\n')
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',nargs='+',required=True)
    parser.add_argument('--paths',type=Path,default=BASE/'q5_grid_paths.json')
    parser.add_argument('--output-dir',type=Path,default=ROOT/'analysis/data/sideproject_residual_growth')
    args = parser.parse_args()
    print(json.dumps(run(args.input,args.paths,args.output_dir),indent=2))
