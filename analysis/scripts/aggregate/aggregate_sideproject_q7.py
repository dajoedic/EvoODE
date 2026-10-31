"""Aggregate complete Q7 fits with unchanged Q5 selection and reporting rules.

No incomplete mode exists. This module is tested with derived synthetic records;
production execution must wait for every Q5 and Q7 candidate.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import pandas as pd
import aggregate_sideproject_q5 as q5
import build_sideproject_q7_paths as builder

ROOT = builder.ROOT


def read_records(inputs):
    return [json.loads(line) for p in q5.result_files(inputs)
            for line in p.read_text(encoding='utf8').splitlines() if line.strip()]


def unique_records(records, expected):
    bykey = {}
    for r in records:
        key = r['cell_id'], r['candidate_id']
        if key in bykey and q5.canonical_bits(r) != q5.canonical_bits(bykey[key]):
            raise ValueError('Duplicate records differ')
        bykey[key] = r
    if set(bykey) != expected:
        raise ValueError('Incomplete or unexpected records')
    return bykey


def expected_keys(cells):
    return {(c['cell_id'],k['candidate_id']) for c in cells for k in c['candidates']+c['upper_candidates']}


def join_records(q7_payload, fit_payload, old_payload, old_records, new_records, fit_path, old_path):
    """Join only manifest-linked records; p0/support live in the hashed manifest.

    Q5's actual records do not store p0 or the raw support. Their paths_sha256
    binds these values to the original Q5 candidate, which is compared here.
    """
    old_cells = {c['cell_id']:c for c in old_payload['cells']}
    if len(old_cells) != len(old_payload['cells']) or set(old_cells) != {c['cell_id'] for c in q7_payload['cells']}:
        raise ValueError('Cell scope differs')
    if len({c['cell_id'] for c in q7_payload['cells']}) != len(q7_payload['cells']):
        raise ValueError('Duplicate Q7 cell')
    old = unique_records(old_records,expected_keys(old_payload['cells']))
    new = unique_records(new_records,expected_keys(fit_payload['cells']))
    expected_fit = [dict(c,candidates=[k for k in c['candidates'] if k['new']]) for c in q7_payload['cells'] if any(k['new'] for k in c['candidates'])]
    if builder.q6.canonical(expected_fit) != builder.q6.canonical(fit_payload['cells']):
        raise ValueError('Fit manifest does not contain exactly new Q7 states')
    if q7_payload['q7_protocol'] != fit_payload['q7_protocol'] or fit_payload['protocol_commit'] != 'f737939':
        raise ValueError('Q7 fit protocol differs')
    reference = next(iter(old.values()))
    runner = ROOT/'studies/regression/sideproject_q5_noise_fits.jl'
    raw = runner.read_bytes()
    runner_hashes = {hashlib.sha256(raw).hexdigest(),hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()}
    inventories = {}
    for records, path in ((old,old_path),(new,fit_path)):
        for r in records.values():
            p = r['provenance']
            if (p['paths_sha256'] != q5.sha256(path) or p['protocol_commit'] != 'f737939'
                or p['index_sha256'] != fit_payload['input_sha256']['outputs/phase_c_c6_data_conditions_5dd1df8/index.csv']
                or p['runner_sha256'] not in runner_hashes
                or p['settings_fingerprint'] != reference['provenance']['settings_fingerprint']
                or r['optimizer_settings'] != reference['optimizer_settings']
                or set(p['source_sha256']) != set(reference['provenance']['source_sha256'])
                or not r['trajectory_control']['passed'] or not r['trajectory_control']['hash_identical']):
                raise ValueError('Fit provenance differs')
            for name,digest in p['source_sha256'].items():
                q5.check_source_hash(name,digest,inventories)
    joined, controls = {}, []
    for cell in q7_payload['cells']:
        original = old_cells[cell['cell_id']]
        for field in ('unit_id','system_id','initial_condition_set','stratum','dim','sigma','rho','realization','observed_data_sha256','export'):
            if cell[field] != original[field]:
                raise ValueError('Q7 cell identity differs')
        candidates = {k['candidate_id']:k for k in original['candidates']+original['upper_candidates']}
        for k in cell['candidates']:
            if k['candidate_id'] in candidates or not k['candidate_id'].startswith('q7_'):
                raise ValueError('Candidate ID collides')
            reused = k.get('reuse_q5_candidate_id')
            if k['new'] == (reused is not None):
                raise ValueError('Ambiguous reuse marker')
            if reused is not None:
                source = candidates[reused]
                if (q5.canonical_bits(source['active_idxs']) != q5.canonical_bits(k['active_idxs'])
                    or q5.canonical_bits(source['p0']) != q5.canonical_bits(k['p0'])):
                    raise ValueError('Reuse support/p0 differs')
                record = old[cell['cell_id'],reused]
                controls.append(dict(cell_id=cell['cell_id'],candidate_id=k['candidate_id'],reuse_q5_candidate_id=reused,
                                     support_equal=True,p0_equal=True,record_paths_sha256=record['provenance']['paths_sha256']))
            else:
                if any(builder.support_key(k)==builder.support_key(v) for v in candidates.values()):
                    raise ValueError('New state should reuse Q5')
                record = new[cell['cell_id'],k['candidate_id']]
            if any(record[field] != cell[field] for field in ('cell_id','unit_id','sigma','rho','realization','observed_data_sha256')):
                raise ValueError('Record cell identity differs')
            joined[cell['cell_id'],k['candidate_id']] = record
        # Reuse the unchanged Q5 best-subset diagnostic. It is never in the
        # Q7 selection pool or fit manifest; Q5's reporting expects this row.
        for k in original['upper_candidates']:
            joined[cell['cell_id'],k['candidate_id']] = old[cell['cell_id'],k['candidate_id']]
    reporting = [dict(c,upper_candidates=old_cells[c['cell_id']]['upper_candidates']) for c in q7_payload['cells']]
    return reporting, joined, controls


def rows_for_q7_cells(cells, joined, old_candidates, old_choices):
    """Q5 reporting unchanged, with an explicit empty-path schema adapter.

    Q5 cannot emit an empty pool: its upper-subset diagnostic indexes pool[-1].
    Empty Q7 pools use imported selection on [], plus the already computed Q5
    upper diagnostic. No candidate is inserted into the empty selection pool.
    """
    populated=[c for c in cells if c['candidates']]
    candidates,choices=q5.rows_for_cells(populated,joined) if populated else ([],[])
    old_upper={r['cell_id']:r for r in old_choices if r['size_rule']=='upper_subset'}
    old_rows={r['cell_id']:r for r in old_candidates if r['candidate_id']=='upper_subset'}
    for c in cells:
        if c['candidates']: continue
        previous=old_upper[c['cell_id']]
        base={name:c[name] for name in ('unit_id','system_id','initial_condition_set','stratum','cell_id','sigma','rho','realization','ended_at_cap')}
        base.update(n_candidates=0,total_loss_evals=0,total_ode_solves=0,
                    total_evaluation_ode_solves=sum(int(joined[c['cell_id'],k['candidate_id']]['evaluation_ode_solves']) for k in c['upper_candidates']),
                    upper_loss_evals=previous['upper_loss_evals'],upper_ode_solves=previous['upper_ode_solves'],
                    truth_on_path=False,k_true=previous['k_true'])
        for rule in ('a','b','c','upper_path'):
            if rule!='upper_path' and q5.select([],rule) is not None:
                raise ValueError('Q5 empty selection semantics changed')
            choices.append(dict(base,size_rule=rule,**{m:False for m in q5.METRICS},
                                candidate_id=None,k=None,observed_start_mse=None,clean_start_mse=None,
                                last_path_state=False,size_error=None))
        choices.append(dict(previous,**base,last_path_state=False))
        candidates.append(dict(old_rows[c['cell_id']],ended_at_cap=False))
    order={c['cell_id']:i for i,c in enumerate(cells)}
    candidates.sort(key=lambda r:order[r['cell_id']])
    choices.sort(key=lambda r:order[r['cell_id']])
    return candidates,choices


def decision_inputs(q7_choices, q5_choices):
    """Frozen margin, noisy sigma only; dim4 is reported without a verdict."""
    frames = [pd.DataFrame(rows) for rows in (q7_choices,q5_choices)]
    frames = [f[(f.size_rule=='c') & (f.sigma>0)] for f in frames]
    rows = []
    for stratum, current in frames[0].groupby('stratum'):
        previous=frames[1][frames[1].stratum==stratum]
        if set(current.cell_id)!=set(previous.cell_id):
            raise ValueError('Decision cells differ')
        for metric in ('pruned_exact','generalization_variance_weighted_hit'):
            a,b=int(current[metric].sum()),int(previous[metric].sum())
            n=len(current)
            rows.append(dict(stratum=stratum,metric=metric,n_cells=n,n_units=current.unit_id.nunique(),
                             q7_numerator=a,q5_numerator=b,q7_rate=a/n,q5_rate=b/n,
                             difference_pp=100*(a-b)/n,margin_pp=5,
                             noninferior=None if stratum=='dim4' else 20*(a-b)>=-n,
                             decision_scope='reported_only' if stratum=='dim4' else 'decided'))
    return rows


def wsindy_tables(choices, details, cells):
    """Both libraries: W1 at rho=0; W1-interp primary and W1 beside it at .5."""
    frame=pd.DataFrame(choices)
    lookup={(c['system_id'],c['initial_condition_set'],c['sigma'],c['rho'],c['realization']):c for c in cells}
    selected=[]
    for row in details.to_dict('records'):
        key=(row['system_id'],row.get('initial_condition_set',row.get('source_initial_condition_set')),
             row['noise_sigma'],row['subsample_rho'],row['noise_realization'])
        cell=lookup.get(key)
        if cell is None or (cell['sigma']==cell['rho']==0):
            continue
        arm=row['q5w_configuration'].split(':')[0]
        if arm not in (('W1',) if cell['rho']==0 else ('W1','W1-interp')):
            continue
        if row['observed_data_sha256'] != cell['observed_data_sha256'] or row['fit_status'] != 'success':
            raise ValueError('Q5-W data identity/fit status failed')
        selected.append(dict(row,cell_id=cell['cell_id'],stratum=cell['stratum'],sigma=cell['sigma'],rho=cell['rho']))
    refs=pd.DataFrame(selected)
    expected={(c['cell_id'],a+':'+lib) for c in cells if c['sigma']!=0 or c['rho']!=0
              for a in (('W1',) if c['rho']==0 else ('W1','W1-interp')) for lib in ('L-C6','L-Q5')}
    if refs.empty or refs.duplicated(['cell_id','q5w_configuration']).any() or set(zip(refs.cell_id,refs.q5w_configuration))!=expected:
        raise ValueError('Incomplete Q5-W comparison')
    rows=[]
    for (stratum,sigma,rho,config),g in refs.groupby(['stratum','sigma','rho','q5w_configuration']):
        primary=frame[(frame.size_rule=='c') & frame.cell_id.isin(g.cell_id)]
        if len(primary)!=len(g):
            raise ValueError('Q5-W comparison cells differ')
        for metric,field in q5.METRICS.items():
            for method,num in (('Q7',int(primary[metric].sum())),(config,sum(q5.boolean(v) for v in g[field]))):
                rows.append(dict(stratum=stratum,sigma=sigma,rho=rho,comparison=config,method=method,metric=metric,
                                 n_units=primary.unit_id.nunique(),numerator=num,denominator=len(g),rate=num/len(g),
                                 primary_reference=config.startswith('W1-interp:') if rho==.5 else True,
                                 reference_library_evaluations=int(g.q5w_library_evaluations.sum()),
                                 reference_least_squares_solves=int(g.q5w_least_squares_solves.sum())))
    return rows


def cost_rows(cells, joined):
    rows=[]
    for c in cells:
        reused=[k for k in c['candidates'] if not k['new']]
        new=[k for k in c['candidates'] if k['new']]
        row={name:c[name] for name in ('cell_id','unit_id','stratum','sigma','rho','realization')}
        row.update(candidate_states=len(c['candidates']),reused_states=len(reused),new_fits=len(new))
        for label,states in (('reused',reused),('new',new)):
            for field in ('loss_evals','ode_solves'):
                row[label+'_'+field]=sum(int(joined[c['cell_id'],k['candidate_id']]['fit_meta'][field]) for k in states)
        rows.append(row)
    return rows


def run(q5_inputs,q7_inputs,wsindy_inputs,paths=builder.OUTPUT/'validated/q7_paths.json',
        fit_paths=builder.OUTPUT/'validated/q7_fit_paths.json',output=ROOT/'analysis/data/sideproject_residual_growth',
        q5_paths=builder.q6.Q5,reference=q5.REFERENCE,q4_inputs=q5.Q4_RESULTS):
    paths,fit_paths,output=Path(paths),Path(fit_paths),Path(output)
    names=('candidates','units','rates','diagnostics','q5_comparison','q5_diagnostics','decision_inputs','reuse_control','q5w_comparison','cost')
    if any((output/f'q7_{n}.csv').exists() for n in names) or (output/'q7_run_metadata.json').exists():
        raise FileExistsError('Refusing to overwrite Q7 tables')
    old=json.loads(Path(q5_paths).read_bytes()); payload=json.loads(paths.read_bytes()); fit=json.loads(fit_paths.read_bytes())
    builder.verify_inputs(old)
    if old['mode']!='grid' or payload['mode']!='grid' or fit['mode']!='grid' or len(old['cells'])!=1632:
        raise ValueError('Full grid required')
    for p in (payload,fit):
        if p['q7_protocol']!=dict(path=builder.PROTOCOL.relative_to(ROOT).as_posix(),sha256=q5.sha256(builder.PROTOCOL)):
            raise ValueError('Q7 protocol changed')
        for name,digest in p['input_sha256'].items():
            if name!=builder.q6.Q5_PROTOCOL and q5.sha256(ROOT/name)!=digest:
                raise ValueError('Q7 input changed: '+name)
    oldrecords=read_records(q5_inputs); records=read_records(q7_inputs)
    refs=pd.read_csv(reference,low_memory=False)
    oldmap,metadata=q5.controls(old,oldrecords,Path(q5_paths),refs,read_records(q4_inputs),json.loads(q5.Q4.read_bytes()))
    cells,joined,reuse=join_records(payload,fit,old,oldrecords,records,fit_paths,Path(q5_paths))
    oldcandidates,oldchoices=q5.rows_for_cells(old['cells'],oldmap)
    candidates,choices=rows_for_q7_cells(cells,joined,oldcandidates,oldchoices)
    rates,diagnostics=q5.report_tables(choices,refs)
    for row in rates:
        if row['method']=='Q5': row['method']='Q7'
    oldrates,olddiag=q5.report_tables(oldchoices,refs)
    ws=pd.concat([pd.read_csv(p,low_memory=False) for p in q5.result_files(wsindy_inputs)],ignore_index=True)
    tables=(candidates,choices,rates,diagnostics,oldrates,olddiag,decision_inputs(choices,oldchoices),reuse,wsindy_tables(choices,ws,payload['cells']),cost_rows(payload['cells'],joined))
    metadata.update(protocol='Q7',cells=len(cells),complete=True,q7_paths_sha256=q5.sha256(paths),
                    fit_paths_sha256=q5.sha256(fit_paths),q7_protocol=payload['q7_protocol'],
                    image='registry.gitlab.scch.at:443/joedicke/evoode:354106398d5e67ffa72c237e2ba83e3feeb25b31',
                    image_provenance='Manifest declaration; runner records do not contain an image digest',
                    reuse_control='Original hashed Q5 candidate manifest supplies support and p0; records do not store them',
                    upper_subset='Unchanged Q5 weak best-subset diagnostic, excluded from Q7 selection')
    output.mkdir(parents=True,exist_ok=True)
    for name,rows in zip(names,tables): pd.DataFrame(rows).to_csv(output/f'q7_{name}.csv',index=False)
    (output/'q7_run_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf8')
    return dict(cells=len(cells),complete=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--q5-input',nargs='+',required=True)
    p.add_argument('--q7-input',nargs='+',required=True)
    p.add_argument('--wsindy-input',nargs='+',required=True)
    p.add_argument('--paths',type=Path,default=builder.OUTPUT/'validated/q7_paths.json')
    p.add_argument('--fit-paths',type=Path,default=builder.OUTPUT/'validated/q7_fit_paths.json')
    p.add_argument('--output-dir',type=Path,default=ROOT/'analysis/data/sideproject_residual_growth')
    a=p.parse_args()
    print(json.dumps(run(a.q5_input,a.q7_input,a.wsindy_input,a.paths,a.fit_paths,a.output_dir)))
