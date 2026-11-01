"""Q8 synthetic aggregation fixtures derive their field inventory from a real Q5 row."""
import copy
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/aggregate'))
import build_sideproject_q8_paths as b
import aggregate_sideproject_q8 as a
import aggregate_sideproject_q5 as q5
from phase1_diagnostic import prune_terms


@pytest.fixture
def derived():
    c=copy.deepcopy(json.loads(b.q6.Q5.read_bytes())['cells'][0])
    c.update(arm='C1000',ic_mode='estimated',coefficient_bound=1000,start='weak',refit=True,representability='exact',stratum='dim1_exact')
    c['candidates']=c['candidates'][:2];c['upper_candidates']=[]
    template=json.loads(next(b.Q5_RECORDS.glob('index_*.jsonl')).read_text().splitlines()[0])
    records={}
    for k in c['candidates']:
        r=copy.deepcopy(template)
        for key in ('cell_id','unit_id','sigma','rho','realization','observed_data_sha256','arm','ic_mode','coefficient_bound','start','refit'):r[key]=c[key]
        r.update(candidate_id=k['candidate_id'],params=[.1]*k['k'],fitted_initial_state=[1.],estimated_ic_training_mse=.01,estimated_clean_ic_distance=.1)
        offset=0;pruned=[]
        for eq in k['equations']:
            n=len(eq['term_names']);kept=prune_terms(dict(zip(eq['term_names'],r['params'][offset:offset+n])))
            pruned.append([i for i,name in zip(eq['basis_indices'],eq['term_names']) if name in kept]);offset+=n
        r['pruned_active_idxs']=pruned
        for regime in ('training','reconstruction','generalization'):
            r[regime].update(loss=.01,r2_arithmetic=.95,r2_variance_weighted=.95,sentinel=False,diverged=False)
        r['optimizer_loss']=.01
        records[c['cell_id'],c['arm'],k['candidate_id']]=r
    return c,records


def test_selection_uses_estimated_training_not_clean(derived):
    c,records=derived
    rs=list(records.values());rs[0]['training']['loss']=.000001;rs[1]['training']['loss']=1.
    rs[0]['clean_ic_observed_mse']=1e9;rs[1]['clean_ic_observed_mse']=0.
    candidates,choices=a.rows_for_cells([c],records)
    assert next(r for r in choices if r['size_rule']=='c')['candidate_id']==c['candidates'][0]['candidate_id']
    assert next(r for r in choices if r['size_rule']=='a')['candidate_id']==q5.select(candidates,'a')['candidate_id']


def test_surrogate_has_no_truth_or_upper_fields(derived):
    c,records=derived;c['representability']='surrogate';c['system_id']=999;c['stratum']='dim1_surrogate'
    candidates,choices=a.rows_for_cells([c],records)
    assert {r['size_rule'] for r in choices}=={'a','b','c'}
    assert all(not {'raw_exact','pruned_exact','k_true','size_error','truth_on_path'} & r.keys() for r in candidates+choices)


def test_empty_path_uses_q5_empty_selection(derived):
    c,records=derived;c['candidates']=[]
    _,choices=a.rows_for_cells([c],{})
    assert len(choices)==3 and all(r['candidate_id'] is None for r in choices)


def test_forward_only_reuses_frozen_forward_arithmetic():
    rng=np.random.default_rng(13)
    design=rng.normal(size=(40,6));target=design@np.array([1.,2.,0.,0.,0.,0.])
    paths,logs,_=b.FORWARD([design],[target])
    assert all(not log['backward_checks'] for log in logs)
    assert all(p['origin']=='addition' for p in paths)
    assert all(set(x['support'][0])<set(y['support'][0]) for x,y in zip(paths,paths[1:]))
    assert b.q6.canonical(b.FORWARD([design],[target]))==b.q6.canonical(b.FORWARD([design],[target]))


def test_reuse_support_and_signed_zero_controls(derived):
    c,_=derived;old=copy.deepcopy(c)
    b.reuse_control(c,old)
    assert c['reuse_q7'] and all(not k['new'] for k in c['candidates'])
    old['candidates'][0]['p0'][0]+=1
    with pytest.raises(ValueError,match='support/p0'):b.reuse_control(c,old)


def decision_fixture(c_good=True,bound_good=True):
    choices=[];refs=[]
    for stratum,representation in [('dim1_exact','exact'),('dim2_surrogate','surrogate')]:
        for arm in ('A10','C10','A1000','C1000'):
            for i in range(20):
                hit=not ((not bound_good and arm=='C1000' and i<4) or (not c_good and arm.startswith('C') and i<2))
                choices.append(dict(cell_id=f'{stratum}_{i}',unit_id=str(i),stratum=stratum,representability=representation,
                    sigma=.01,rho=0,size_rule='c',arm=arm,pruned_exact=hit,generalization_variance_weighted_hit=hit))
        for method in ('sindy','weak_sindy','e_sindy','wsindy_preliminary'):
            refs.append(dict(stratum=stratum,sigma=.01,rho='pooled',method=method,configuration='best',metric='generalization_variance_weighted_hit',numerator=20,denominator=20))
    return choices,refs


@pytest.mark.parametrize('cg,bg,expected',[(True,True,'C1000'),(True,False,'C10'),(False,True,'A1000'),(False,False,'A10')])
def test_rule_order_and_adopted_bound(cg,bg,expected):
    summary,rows=a.decision_rules(*decision_fixture(cg,bg))
    assert summary['adopted_arm']==expected
    assert summary['order']==['R2','R1','R3']
    assert all(r['left'].endswith(str(summary['adopted_bound'])) for r in rows if r['rule']=='R1')


def test_margin_equality_and_dim3_report_only():
    choices,refs=decision_fixture()
    for r in choices:
        if r['arm']=='C1000' and r['cell_id'].endswith('_0'):r['generalization_variance_weighted_hit']=False
    choices.append(dict(choices[0],stratum='dim3_exact',arm='C1000',generalization_variance_weighted_hit=False))
    summary,rows=a.decision_rules(choices,refs)
    assert summary['adopted_arm']=='C1000'
    assert all(not r['stratum'].startswith('dim3') for r in rows)


def test_missing_reference_refused():
    choices,refs=decision_fixture()
    with pytest.raises(ValueError,match='four references'):a.decision_rules(choices,[r for r in refs if r['method']!='sindy'])


def test_missing_fit_and_overwrite_refused(derived):
    tmp_path=b.OUTPUT/"tests"
    tmp_path.mkdir(exist_ok=True)
    c,_=derived
    with pytest.raises(ValueError,match='Incomplete Q8'):a.validate_records([c],[],tmp_path/'missing',{})
    with pytest.raises(FileExistsError):a.run([],[],[],[],tmp_path)


def test_historical_protocol_strict_scope():
    payload=json.loads(b.q6.Q5.read_bytes())
    q5.verify_frozen_inputs(payload,'f454a32')
    with pytest.raises(ValueError):q5.verify_frozen_inputs(payload)
    with pytest.raises(ValueError):q5.verify_frozen_inputs(payload,'other')
    payload['input_sha256']['outputs/phase_c_c6_data_conditions_5dd1df8/index.csv']='bad'
    with pytest.raises(ValueError):q5.verify_frozen_inputs(payload,'f454a32')


def test_frozen_runners_and_default_optimizer_struct():
    assert b.q6.sha256(b.ROOT/'studies/regression/sideproject_q4_path_fits.jl') in a.source_hashes(b.ROOT/'studies/regression/sideproject_q4_path_fits.jl')
    current=(b.ROOT/'src/optimize/bfgs.jl').read_text()
    legacy=(b.ROOT/'codex/reports/WP_FA9_bfgs_legacy.jl.txt').read_text()
    start='Base.@kwdef struct BFGSOptimizer';end='struct BFGSLossEvalBudgetExceeded'
    assert current[current.index(start):current.index(end)]==legacy[legacy.index(start):legacy.index(end)]
    # Every default clamp and prediction expression remains present verbatim.
    assert '_predict_traj(f!, traj, p, opt; stats = solve_stats)' in current
    assert 'Base.clamp.(Vector{Float64}(p), -opt.clamp_val, opt.clamp_val)' in current

def synthetic_references(cells):
    # Field inventory comes from a real WP-N47 record; every scientific flag
    # below is visibly replaced by a synthetic value.
    template=pd.read_csv(q5.REFERENCE,nrows=1).iloc[0].to_dict()
    refs=[]
    for c in cells:
        for method,nconfigs in (('sindy',2),('weak_sindy',10),('e_sindy',2)):
            for n in range(nconfigs):
                r=dict(template,method=method,method_config_id=f'{method}_{n}',polynomial_degree=3 if n<2 else 2,
                    include_sin_cos=n<2,system_id=c['system_id'],source_initial_condition_set=c['initial_condition_set'],
                    target_initial_condition_set=3-c['initial_condition_set'],noise_sigma=c['sigma'],subsample_rho=c['rho'],
                    noise_realization=1,observed_data_sha256=c['observed_data_sha256'])
                r.update({field:True for field in q5.METRICS.values()})
                refs.append(r)
    return pd.DataFrame(refs)


def test_imported_reporting_clean_filter_and_surrogate_metrics(derived):
    original,records=derived
    cells=[];joined={}
    for i,(sigma,rho) in enumerate(((0,0),(0,.5),(.01,0))):
        c=copy.deepcopy(original);c.update(cell_id=f'synthetic_{i}',sigma=sigma,rho=rho,
            representability='surrogate',system_id=999,stratum='dim1_surrogate')
        cells.append(c)
        for k in c['candidates']:
            joined[c['cell_id'],c['arm'],k['candidate_id']]=records[original['cell_id'],original['arm'],k['candidate_id']]
    _,choices=a.rows_for_cells(cells,joined)
    refs=synthetic_references(cells)
    a.reference_hash_controls(cells,refs)
    rates,diag=a.report_tables(choices,refs)
    assert rates and {r['metric'] for r in rates}==set(a.R2_METRICS)
    assert all(not (r['sigma']==0 and r['rho']==0) for r in rates)
    assert all(not any(k.startswith(('D3','D4')) for k in r) for r in diag)
    with pytest.raises(ValueError,match='hash mismatch'):
        a.reference_hash_controls(cells,refs.assign(observed_data_sha256='bad'))


def test_wsindy_primary_rho_and_missing_coverage(derived):
    c,_=derived;c.update(sigma=.01,rho=.5,stratum='dim1_surrogate',representability='surrogate')
    template=pd.read_csv(b.ROOT/'outputs/sideproject_q5w_wsindy/full/details.csv',nrows=1).iloc[0].to_dict()
    details=[]
    for arm in ('W1','W1-interp'):
        for lib in ('L-C6','L-Q5'):
            r=dict(template,system_id=c['system_id'],source_initial_condition_set=c['initial_condition_set'],
                noise_sigma=c['sigma'],subsample_rho=c['rho'],noise_realization=1,observed_data_sha256=c['observed_data_sha256'],
                q5w_configuration=arm+':'+lib,fit_status='success')
            r.update({field:True for field in q5.METRICS.values()});details.append(r)
    rates=a.wsindy_rates([c],pd.DataFrame(details))
    assert rates and all(r['metric'] in a.R2_METRICS for r in rates)
    assert all(r['configuration'].startswith('W1-interp:') for r in rates if r['rho']==.5)
    assert all(r['preliminary'] for r in rates)
    with pytest.raises(ValueError,match='Incomplete Q5-W'):a.wsindy_rates([c],pd.DataFrame(details[:-1]))


def test_settings_hash_matches_actual_schema(derived):
    _,records=derived
    r=next(iter(records.values()))
    assert a.settings_fingerprint(r['optimizer_settings'])==r['provenance']['settings_fingerprint']
    variants=[]
    for arm,values in b.ARMS.items():
        settings=dict(r['optimizer_settings'],arm=arm,ic_mode=values[0],coefficient_bound=values[1],
                      clamp_val=float(values[1]),start=values[2],refit=values[3],fixed_initial_state_control=False)
        variants.append(a.settings_fingerprint(settings))
    assert len(set(variants))==7


def test_record_provenance_and_resume_guards(derived):
    c,records=derived
    folder=b.OUTPUT/'tests';folder.mkdir(exist_ok=True)
    path=folder/'synthetic_fit.json';path.write_text('{}\n')
    base=next(iter(records.values()))['optimizer_settings']
    settings=dict(base,clamp_val=float(c['coefficient_bound']),
        **{key:c[key] for key in ('arm','ic_mode','coefficient_bound','start','refit')},fixed_initial_state_control=False)
    records=list(records.values())
    sources={name:b.q6.sha256(b.ROOT/name) for name in a.base_settings_source()}
    sources['studies/regression/sideproject_q8_fits.jl']=b.q6.sha256(b.ROOT/'studies/regression/sideproject_q8_fits.jl')
    for r in records:
        r['optimizer_settings']=settings
        r['provenance']=dict(paths_sha256=b.q6.sha256(path),protocol='Q8',settings_fingerprint=a.settings_fingerprint(settings),
            runner_sha256=b.q6.sha256(b.ROOT/'studies/regression/sideproject_q8_fits.jl'),
            index_sha256=b.q6.sha256(b.EXPORT/'index.csv'),source_sha256=sources)
    assert len(a.validate_records([c],records,path,base))==len(records)
    assert len(a.validate_records([c],records+[copy.deepcopy(records[0])],path,base))==len(records)
    broken=copy.deepcopy(records);broken[0]['provenance']['settings_fingerprint']='0'*64
    with pytest.raises(ValueError,match='fingerprint'):a.validate_records([c],broken,path,base)
    with pytest.raises(ValueError,match='Incomplete Q8'):a.validate_records([c],records[:-1],path,base)
    broken=copy.deepcopy(records[0]);broken['fitted_initial_state']=[-0.]
    with pytest.raises(ValueError,match='Duplicate'):a.validate_records([c],records+[broken],path,base)


def test_missing_or_stale_smoke_refused():
    folder=b.OUTPUT/'tests';folder.mkdir(exist_ok=True)
    path=folder/'smoke_control.json'
    path.write_text(json.dumps(dict(passed=True,default_bit_control=True,fixed_ic_bit_control=True,cells=2,candidates=19)))
    with pytest.raises(ValueError,match='stale'):a.smoke_controls(path)


def test_q8_manifests_and_descending_shards():
    import yaml
    summary=json.loads((b.OUTPUT/'grid/technical.json').read_bytes())
    for kind,filename in [('grid','sideproject_q8_job.yaml'),('probe','sideproject_q8_probe_job.yaml')]:
        job=yaml.safe_load((b.ROOT/'k8s'/filename).read_text())
        spec=job['spec'];container=spec['template']['spec']['containers'][0]
        assert spec['parallelism']==16 and spec['completionMode']=='Indexed'
        assert 'activeDeadlineSeconds' not in spec
        assert spec['completions']==summary['shards' if kind=='grid' else 'probe_shards']
        assert container['image'].endswith(':<COMMIT_SHA>')
        assert 'fallback-export-dir' in container['command'][-1]
        assert container['resources']['limits']=={'cpu':'1','memory':'4Gi'}
    fits=json.loads((b.OUTPUT/'grid/q8_fit_paths.json').read_bytes())['cells']
    order=(b.OUTPUT/'grid/q8_grid.shards_cost_desc.txt').read_text().splitlines()
    assert order==[c['shard_id'] for c in sorted(fits,key=lambda c:(-c['planned_seconds_high'],c['shard_id']))]
    assert len(order)==len(set(order))==3540

def test_no_foba_retains_the_correlated_decoy():
    design=np.column_stack(([1.,1.,.3],[1.,0.,0.],[0.,1.,0.]))
    target=np.array([1.,1.,0.])
    normal,_,_=b.q6.growth_path_with_end([design],[target])
    forward,_,_=b.FORWARD([design],[target])
    assert normal[-1]['support']==[[1,2]]
    assert forward[-1]['support']==[[0,1,2]]
    assert all(p['origin']=='addition' for p in forward)

def test_cell_arm_scope_is_mandatory(monkeypatch,derived):
    c,_=derived
    source={key:c[key] for key in ('cell_id','unit_id','system_id','initial_condition_set','dim','stratum','representability','sigma','rho','realization','observed_data_sha256','export','n_observed_points')}
    monkeypatch.setattr(b,'source_cells',lambda:[source])
    cells=[]
    for arm,settings in b.ARMS.items():
        cells.append(dict(source,arm=arm,ic_mode=settings[0],coefficient_bound=settings[1],start=settings[2],refit=settings[3],
            shard_id=source['cell_id']+'__'+arm,reuse_q7=arm=='A10',candidates=[],upper_candidates=[]))
    a.validate_scope(dict(cells=cells))
    with pytest.raises(ValueError,match='scope'):a.validate_scope(dict(cells=cells[:-1]))
    with pytest.raises(ValueError,match='scope'):a.validate_scope(dict(cells=cells[:-1]+[cells[0]]))
    broken=copy.deepcopy(cells);broken[0]['coefficient_bound']=1000
    with pytest.raises(ValueError,match='arm settings'):a.validate_scope(dict(cells=broken))
