"""Strict Q8 aggregation. Production results are never evaluated by tests.

Q5 candidate conversion, selection and reporting are imported. Surrogate rows
have no truth support and only trajectory metrics are emitted. R2 precedes R1;
R3 uses the best of three matching-library references plus preliminary WSINDy.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import pandas as pd
import aggregate_sideproject_q5 as q5
import aggregate_sideproject_q7 as q7
import build_sideproject_q8_paths as builder

ROOT=builder.ROOT
R2_METRICS={k:v for k,v in q5.METRICS.items() if 'exact' not in k}


def rows_for_cells(cells, records):
    """Q5 schema adapter: no upper diagnostic, optional truth, estimated-IC loss.

    Adding d to every candidate's BIC penalty is constant within a cell, hence
    imported Q5 selection has exactly the same ordering without altering k.
    """
    _,systems=q5.load_exact_supports(ROOT/q5.SUPPORT)
    truth={s['system_id']:[set(eq) for eq in s['support_terms']] for s in systems}
    candidates,choices=[],[]
    for c in cells:
        exact=c['representability']=='exact'
        pool=[]
        for k in c['candidates']:
            r=records[c['cell_id'],c['arm'],k['candidate_id']]
            row=q5.candidate_row(c,k,r,truth[c['system_id']] if exact else None)
            for kind in ('arithmetic','variance_weighted'):
                value=r['reconstruction']['r2_'+kind]
                row['reconstruction_r2_'+kind]=value
                row['reconstruction_'+kind+'_hit']=value is not None and math.isfinite(value) and value>.9 and not r['reconstruction']['diverged']
            row.update({key:c[key] for key in ('cell_id','arm','sigma','rho','realization','ended_at_cap','representability')})
            row.update(observed_start_mse=row['mse'],clean_start_mse=r['clean_ic_observed_mse'],
                ode_solves=int(r['fit_meta']['ode_solves']),evaluation_ode_solves=int(r['evaluation_ode_solves']),
                fitted_initial_state=r.get('fitted_initial_state'),
                estimated_ic_training_mse=r.get('estimated_ic_training_mse'),
                estimated_clean_ic_distance=r.get('estimated_clean_ic_distance'))
            if not exact:
                row.pop('raw_exact');row.pop('pruned_exact')
            pool.append(row)
        candidates.extend(pool)
        base={key:c[key] for key in ('cell_id','unit_id','system_id','initial_condition_set','stratum','sigma','rho','realization','ended_at_cap','arm','representability')}
        base.update(n_candidates=len(pool),total_loss_evals=sum(r['loss_evals'] for r in pool),
            total_ode_solves=sum(r['ode_solves'] for r in pool),total_evaluation_ode_solves=sum(r['evaluation_ode_solves'] for r in pool),
            upper_loss_evals=0,upper_ode_solves=0,last_path_state=False,
            truth_on_path=any(r['raw_exact'] for r in pool) if exact else None,
            k_true=sum(map(len,truth[c['system_id']])) if exact else None)
        for rule in ('a','b','c'):
            chosen=q5.select(pool,rule)
            row=dict(base,size_rule=rule)
            if chosen is None:
                row.update({m:False for m in (q5.METRICS if exact else R2_METRICS)})
                row.update(candidate_id=None,k=None,observed_start_mse=None,clean_start_mse=None)
            else: row.update(chosen)
            row['last_path_state']=chosen is not None and chosen['candidate_id']==pool[-1]['candidate_id']
            row['size_error']=row['k']-row['k_true'] if exact and row['k'] is not None else None
            if not exact:
                for key in ('truth_on_path','k_true','size_error'):row.pop(key)
            choices.append(row)
    return candidates,choices


def report_tables(choices, references):
    rates,diagnostics=[],[]
    frame=pd.DataFrame(choices)
    for (arm,representation),group in frame.groupby(['arm','representability']):
        rows=group.to_dict('records')
        exact=representation=='exact'
        # Q5 diagnostics have a fixed schema. None is an availability marker,
        # never a truth estimate; remove these columns before surrogate output.
        if not exact:
            rows=[dict(r,truth_on_path=False,k_true=None,size_error=None) for r in rows]
        r,d=q5.report_tables(rows,references,q5.METRICS if exact else R2_METRICS)
        for row in r:
            row.update(arm=arm,representability=representation)
            if row['method']=='Q5':row['method']='Q8'
        for row in d:
            row.update(arm=arm,representability=representation)
            if not exact:
                for key in ('D3_truth_numerator','D3_denominator','D3_truth_rate','D4_size_errors'):row.pop(key,None)
        rates.extend(r);diagnostics.extend(d)
    return rates,diagnostics


def decision_rules(choices, reference_rates):
    frame=pd.DataFrame(choices)
    frame=frame[(frame.size_rule=='c') & (frame.sigma>0)]
    rows=[]
    def compare(rule,left,right):
        passing=True
        for stratum,g in frame.groupby('stratum'):
            if not stratum.startswith(('dim1_','dim2_')):continue
            exact=g.representability.iloc[0]=='exact'
            a,b=(g[g.arm==arm] for arm in (left,right))
            if a.empty or set(a.cell_id)!=set(b.cell_id):raise ValueError('Incomplete adoption cells')
            for metric in (('pruned_exact','generalization_variance_weighted_hit') if exact else ('generalization_variance_weighted_hit',)):
                num_a,num_b,n=int(a[metric].sum()),int(b[metric].sum()),len(a)
                ok=20*(num_a-num_b)>=-n
                passing &= ok
                rows.append(dict(rule=rule,stratum=stratum,metric=metric,left=left,right=right,numerator_left=num_a,
                    numerator_right=num_b,denominator=n,margin_pp=5,noninferior=ok,decision_scope='dim12'))
        return passing
    bound=1000 if compare('R2','C1000','C10') else 10
    variant='C' if compare('R1',f'C{bound}',f'A{bound}') else 'A'
    adopted=f'{variant}{bound}'
    refs=pd.DataFrame(reference_rates)
    for stratum,g in frame[(frame.arm==adopted)&(frame.representability=='surrogate')].groupby('stratum'):
        if not stratum.startswith(('dim1_','dim2_')):continue
        # Reference thresholds were selected per sigma by imported Q5 reporting.
        eligible=refs[(refs.stratum==stratum)&(refs.metric=='generalization_variance_weighted_hit')&
            (refs.rho=='pooled')&(refs.sigma>0)&(refs.method!='Q8')&(refs.configuration!='all_ten')].drop_duplicates(['stratum','sigma','rho','method','configuration','metric','numerator','denominator'])
        scores=[]
        for method,part in eligible.groupby('method'):
            if set(part.sigma)!=set(g.sigma):raise ValueError('Incomplete R3 sigma coverage')
            scores.append((int(part.numerator.sum()),int(part.denominator.sum()),method))
        if {s[2] for s in scores}!={'sindy','weak_sindy','e_sindy','wsindy_preliminary'}:
            raise ValueError('All four references required for R3')
        if any(n!=len(g) for _,n,_ in scores):raise ValueError('R3 denominators differ')
        num,n,method=max(scores,key=lambda r:(r[0]/r[1],r[2]))
        wisp=int(g.generalization_variance_weighted_hit.sum())
        rows.append(dict(rule='R3',stratum=stratum,metric='generalization_variance_weighted_hit',left=adopted,
            right=method,numerator_left=wisp,numerator_right=num,denominator=n,
            clearly_behind=20*(wisp-num)<-n,margin_pp=5,preliminary=True,decision_scope='dim12'))
    return dict(adopted_bound=bound,adopted_variant=variant,adopted_arm=adopted,order=['R2','R1','R3']),rows


def wsindy_rates(cells, details):
    """Q7 completeness/hash/library checks; W1/W1-interp at the declared rho.

    Use its reporting implementation on synthetic zero WISP placeholders. Only
    reference rows survive; no substitute WISP scientific result is emitted.
    """
    placeholders=[dict(cell_id=c['cell_id'],unit_id=c['unit_id'],size_rule='c',**{k:False for k in q5.METRICS}) for c in cells]
    exact=[c for c in cells if c['representability']=='exact']
    # q7's function iterates structure metrics. Surrogate structure flags are
    # absent in real detail records, so use explicit unavailable placeholders.
    details=details.copy()
    for field in ('sindy_structure_hit_raw','sindy_structure_hit_pruned'):
        details[field]=details[field].fillna(False) if field in details else False
    raw=q7.wsindy_tables(placeholders,details,cells)
    rows=[]
    for stratum in sorted({c['stratum'] for c in cells}):
        representation=next(c['representability'] for c in cells if c['stratum']==stratum)
        selected=[r for r in raw if r['stratum']==stratum and r['method']!='Q7' and r['primary_reference'] and
                  r['comparison'].endswith(':L-Q5') and (representation=='exact' or r['metric'] in R2_METRICS)]
        for r in selected:
            rows.append(dict(stratum=stratum,sigma=r['sigma'],rho=r['rho'],method='wsindy_preliminary',configuration=r['comparison'],
                             reference_coefficient_source=r['reference_coefficient_source'],
                             metric=r['metric'],numerator=r['numerator'],denominator=r['denominator'],rate=r['rate'],preliminary=True))
        frame=pd.DataFrame(selected)
        for (sigma,metric),g in frame.groupby(['sigma','metric']):
            num,den=int(g.numerator.sum()),int(g.denominator.sum())
            rows.append(dict(stratum=stratum,sigma=sigma,rho='pooled',method='wsindy_preliminary',configuration='W1/W1-interp:L-Q5',
                reference_coefficient_source=','.join(sorted(set(g.reference_coefficient_source))),
                metric=metric,numerator=num,denominator=den,rate=num/den,preliminary=True))
    return rows



def settings_fingerprint(settings):
    """Julia canonical_value for this flat, typed settings dictionary.

    Float tolerances use Julia's mandatory decimal mantissa and unpadded
    exponent. Nonfinite settings are already strings, as in q4_settings.
    """
    def value(v):
        if isinstance(v, bool): return 'true' if v else 'false'
        if isinstance(v, str): return json.dumps(v,ensure_ascii=False)
        if isinstance(v, float):
            text=repr(v)
            if 'e' in text:
                mantissa,exponent=text.split('e')
                if '.' not in mantissa:mantissa+='.0'
                text=mantissa+'e'+str(int(exponent))
            return text
        if isinstance(v, int):return str(v)
        raise ValueError('Unexpected settings type')
    canonical='{'+','.join(k+'='+value(v) for k,v in sorted(settings.items()))+'}'
    return hashlib.sha256(canonical.encode()).hexdigest()


def validate_records(cells, records, fit_path, base_settings):
    expected={(c['cell_id'],c['arm'],k['candidate_id']):c for c in cells for k in c['candidates']}
    bykey={}; fingerprints={}; inventories={}
    for r in records:
        key=r['cell_id'],r['arm'],r['candidate_id']
        if key not in expected:raise ValueError('Unexpected Q8 candidate')
        if key in bykey and q5.canonical_bits(r)!=q5.canonical_bits(bykey[key]):raise ValueError('Duplicate Q8 records differ')
        c=expected[key];settings=dict(base_settings,clamp_val=float(c['coefficient_bound']),
            **{k:c[k] for k in ('arm','ic_mode','coefficient_bound','start','refit')},fixed_initial_state_control=False)
        p=r['provenance']
        if r['optimizer_settings']!=settings or p['paths_sha256']!=q5.sha256(fit_path) or p['protocol']!='Q8':
            raise ValueError('Q8 provenance/settings mismatch')
        if p['runner_sha256'] not in source_hashes(ROOT/'studies/regression/sideproject_q8_fits.jl'):
            raise ValueError('Q8 runner mismatch')
        if p['index_sha256']!=q5.sha256(builder.EXPORT/'index.csv') or not all(r['trajectory_control'].values()):
            raise ValueError('Q8 data control failed')
        if p['settings_fingerprint']!=settings_fingerprint(settings):raise ValueError('Settings fingerprint mismatch')
        previous=fingerprints.setdefault(c['arm'],p['settings_fingerprint'])
        if previous!=p['settings_fingerprint']:raise ValueError('Arm settings fingerprint differs')
        if set(p['source_sha256'])!=set(base_settings_source())|{'studies/regression/sideproject_q8_fits.jl'}:
            raise ValueError('Q8 source inventory mismatch')
        for name,digest in p['source_sha256'].items():
            # New fits must use CURRENT source, never the legacy exception.
            if digest not in source_hashes(ROOT/name):raise ValueError('Q8 source changed: '+name)
        for name in ('unit_id','sigma','rho','realization','observed_data_sha256','ic_mode','coefficient_bound','start','refit'):
            if r[name]!=c[name]:raise ValueError('Q8 record identity mismatch')
        if len(r['fitted_initial_state'])!=c['dim']:raise ValueError('Fitted IC dimension')
        bykey[key]=r
    if set(bykey)!=set(expected):raise ValueError('Incomplete Q8 records')
    return bykey


def source_hashes(path):
    raw=path.read_bytes()
    return {hashlib.sha256(raw).hexdigest(),hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()}


def base_settings_source():
    metadata=json.loads((ROOT/'analysis/data/sideproject_residual_growth/q5_grid/q5_run_metadata.json').read_bytes())
    return metadata['source_sha256']




def validate_scope(payload):
    source={c['cell_id']:c for c in builder.source_cells()}
    expected=set()
    for cid,c in source.items():
        for arm,(_,bound,_,_) in builder.ARMS.items():
            if c['dim']==3 and (arm in ('no_foba','random_start','no_refit') or
                (c['system_id'] not in (52,61) and bound==10)):continue
            expected.add((cid,arm))
    actual=[(c['cell_id'],c['arm']) for c in payload['cells']]
    if len(actual)!=len(set(actual)) or set(actual)!=expected:
        raise ValueError('Incomplete or duplicate Q8 cell/arm scope')
    for c in payload['cells']:
        original=source[c['cell_id']]
        if any(c[k]!=v for k,v in original.items()):raise ValueError('Q8 source cell identity differs')
        if tuple(c[k] for k in ('ic_mode','coefficient_bound','start','refit'))!=builder.ARMS[c['arm']]:
            raise ValueError('Q8 arm settings differ')
        if c['shard_id']!=c['cell_id']+'__'+c['arm']:raise ValueError('Q8 shard identity differs')
        ids=[k['candidate_id'] for k in c['candidates']]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate Q8 candidate')
        should_reuse=c['arm']=='A10' and c['representability']=='exact'
        if c['reuse_q7']!=should_reuse:raise ValueError('Q8 reuse scope differs')
        if c['upper_candidates'] or (c['representability']=='surrogate' and any('truth' in k for k in c)):
            raise ValueError('Unexpected upper/truth fields')


def reference_hash_controls(cells, references):
    keys=['system_id','source_initial_condition_set','noise_sigma','subsample_rho','noise_realization']
    grouped={key:g for key,g in references.groupby(keys)}
    for c in cells:
        key=(c['system_id'],c['initial_condition_set'],c['sigma'],c['rho'],c['realization'])
        g=grouped.get(key)
        if g is None or set(g.observed_data_sha256)!={c['observed_data_sha256']}:
            raise ValueError('WP-N47 observed data hash mismatch')
        if any(g.target_initial_condition_set!=3-c['initial_condition_set']):
            raise ValueError('WP-N47 target IC mismatch')


def smoke_controls(path):
    control=json.loads(Path(path).read_bytes())
    if not all(control.get(key) is True for key in ('passed','default_bit_control','fixed_ic_bit_control')):
        raise ValueError('Julia smoke controls have not passed')
    if control.get('cells')!=2 or control.get('candidates')!=19:
        raise ValueError('Unexpected Julia smoke scope')
    sources=control.get('source_sha256',{})
    names={'src/optimize/bfgs.jl','studies/regression/sideproject_q8_fits.jl',
           'studies/regression/sideproject_q8_smoke.jl'}
    if set(sources)!=names or any(digest not in source_hashes(ROOT/name) for name,digest in sources.items()):
        raise ValueError('Julia smoke is stale or lacks source hashes')
    return control


def bound_controls(choices):
    # Informational: looser bounds can change optimizer paths and selected support.
    smoke=json.loads((builder.OUTPUT/'smoke.json').read_bytes())
    ids={c['cell_id'] for c in smoke['cells']}
    selected={(r['cell_id'],r['arm']):r for r in choices if r['size_rule']=='c' and r['cell_id'] in ids}
    rows=[]
    for cid in sorted(ids):
        for variant in ('A','C'):
            low,high=(selected[cid,variant+str(bound)] for bound in (10,1000))
            params=json.loads(high['params']) if high['candidate_id'] is not None else []
            rows.append(dict(cell_id=cid,variant=variant,support_equal=low.get('active_idxs')==high.get('active_idxs'),
                bound1000_coefficients_within10=bool(params) and all(abs(p)<=10 for p in params),
                required_to_equal=False))
    return rows


def run(inputs,q5_inputs,q7_inputs,wsindy_inputs,output,paths=builder.OUTPUT/'grid/q8_paths.json',fit_paths=builder.OUTPUT/'grid/q8_fit_paths.json',smoke_path=ROOT/'outputs/sideproject_q8_smoke/controls.json',wsindy_source='matlab',wsindy_matlab_inputs=None):
    output=Path(output)
    if output.exists():raise FileExistsError('Refusing to overwrite Q8 output')
    smoke=smoke_controls(smoke_path)
    payload=json.loads(Path(paths).read_bytes());fit=json.loads(Path(fit_paths).read_bytes())
    if payload['mode']!='grid' or fit['mode']!='grid' or len(payload['cells'])!=3770:raise ValueError('Complete Q8 grid required')
    validate_scope(payload)
    if payload['q8_protocol_sha256']!=q5.sha256(builder.PROTOCOL):raise ValueError('Q8 protocol changed')
    for name,digest in payload['input_sha256'].items():
        if q5.sha256(ROOT/name)!=digest:raise ValueError('Q8 input changed: '+name)
    if q5.canonical_bits(fit['cells'])!=q5.canonical_bits([c for c in payload['cells'] if not c['reuse_q7']]):
        raise ValueError('Q8 fit scope differs')
    ws=pd.concat([pd.read_csv(p,low_memory=False) for p in q5.result_files(wsindy_inputs)],ignore_index=True)
    ws=q7.select_rows(ws,wsindy_source,wsindy_matlab_inputs)
    # Reuse Q7's strict Q5 controls and manifest-bound join without evaluating
    # real-data metrics or writing any intermediate Q5/Q7 report.
    old=json.loads(builder.q6.Q5.read_bytes());oldrecords=q7.read_records(q5_inputs)
    refs=pd.read_csv(q5.REFERENCE,low_memory=False)
    oldmap,_=q5.controls(old,oldrecords,builder.q6.Q5,refs,q7.read_records(q5.Q4_RESULTS),json.loads(q5.Q4.read_bytes()))
    qp=json.loads(builder.Q7_PATHS.read_bytes());fp_path=builder.Q7_PATHS.with_name('q7_fit_paths.json')
    fp=json.loads(fp_path.read_bytes())
    _,joined,reuse=q7.join_records(qp,fp,old,oldrecords,q7.read_records(q7_inputs),fp_path,builder.q6.Q5)
    new=validate_records(fit['cells'],q7.read_records(inputs),fit_paths,oldrecords[0]['optimizer_settings'])
    originals={c['cell_id']:c for c in qp['cells']}
    for c in payload['cells']:
        if not c['reuse_q7']:continue
        builder.reuse_control(copy.deepcopy(c),originals[c['cell_id']])
        for candidate,previous in zip(c['candidates'],originals[c['cell_id']]['candidates']):
            for field in ('active_idxs','p0','k','equations','weak_bic','step','origin'):
                if q5.canonical_bits(candidate[field])!=q5.canonical_bits(previous[field]):
                    raise ValueError('A10 Q7 candidate list differs')
        for k in c['candidates']:new[c['cell_id'],'A10',k['candidate_id']]=joined[c['cell_id'],k['reuse_q7_candidate_id']]
    candidates,choices=rows_for_cells(payload['cells'],new)
    rates,diagnostics=report_tables(choices,refs)
    unique={c['cell_id']:c for c in payload['cells']}
    reference_hash_controls(list(unique.values()),refs)
    wr=wsindy_rates(list(unique.values()),ws)
    decision,decision_rows=decision_rules(choices,[*rates,*wr])
    costs=[]
    for c in payload['cells']:
        rs=[new[c['cell_id'],c['arm'],k['candidate_id']] for k in c['candidates']]
        costs.append(dict(cell_id=c['cell_id'],arm=c['arm'],stratum=c['stratum'],candidates=len(rs),reused=c['reuse_q7'],
            fits=0 if c['reuse_q7'] or not c['refit'] else len(rs),
            **{field:sum(r['fit_meta'][field] for r in rs) for field in ('loss_evals','ode_solves','solve_time_s')},
            evaluation_ode_solves=sum(r['evaluation_ode_solves'] for r in rs)))
    output.mkdir(parents=True)
    tables=dict(candidates=candidates,units=choices,rates=rates,diagnostics=diagnostics,decision_inputs=decision_rows,
        wsindy_comparison=wr,cost=costs,reuse_control=reuse,bound_control=bound_controls(choices),
        ablations=[r for r in rates if r['arm'] in ('C1000','no_foba','random_start','no_refit')])
    for name,rows in tables.items():pd.DataFrame(rows).to_csv(output/f'q8_{name}.csv',index=False)
    (output/'q8_run_metadata.json').write_text(json.dumps(dict(complete=True,decision=decision,
        paths_sha256=q5.sha256(paths),fit_paths_sha256=q5.sha256(fit_paths),
        controls=dict(a10_q7_support_p0=True,observed_hashes=True,fixed_ic_smoke=smoke),
        wsindy='preliminary',wsindy_source=wsindy_source,selection='Q5 (c) primary; (a)/(b) reported'),indent=2)+'\n')
    return dict(complete=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('input','q5-input','q7-input','wsindy-input'):p.add_argument('--'+key,nargs='+',required=True)
    p.add_argument('--wsindy-source',choices=('matlab','port'),default='matlab')
    p.add_argument('--wsindy-matlab-input',nargs='+')
    p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--paths',type=Path,default=builder.OUTPUT/'grid/q8_paths.json')
    p.add_argument('--fit-paths',type=Path,default=builder.OUTPUT/'grid/q8_fit_paths.json')
    p.add_argument('--smoke-controls',type=Path,default=ROOT/'outputs/sideproject_q8_smoke/controls.json')
    a=p.parse_args();print(json.dumps(run(a.input,a.q5_input,a.q7_input,a.wsindy_input,a.output_dir,a.paths,a.fit_paths,a.smoke_controls,a.wsindy_source,a.wsindy_matlab_input)))
