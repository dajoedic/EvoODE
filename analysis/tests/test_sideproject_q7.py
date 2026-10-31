"""Q7 path controls and aggregation using fixtures derived from actual Q5 data."""
import copy
import json
import sys
import uuid
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from threadpoolctl import threadpool_limits
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/aggregate'))
import build_sideproject_q7_paths as b
import aggregate_sideproject_q7 as a
from phase1_diagnostic import prune_terms


@pytest.fixture(scope='module',autouse=True)
def single_blas():
    with threadpool_limits(limits=1): yield


@pytest.fixture(scope='module')
def derived():
    payload=json.loads(b.q6.Q5.read_bytes())
    for cell in (c for c in payload['cells'] if c['dim']==2 and c['sigma']==.05 and c['rho']==.5):
        paths,rows=b.build_cell(cell)
        if any(k['new'] for k in paths['chi2_0.01']['candidates']): break
    else: raise AssertionError('No real dim2 cell with new states')
    # Keep one original reused state and one genuinely new state.
    current=copy.deepcopy(paths['chi2_0.01'])
    reused=next(k for k in current['candidates'] if not k['new'])
    new=next(k for k in current['candidates'] if k['new'])
    current['candidates']=[reused,new]
    old=dict(payload,cells=[cell])
    q7=dict(protocol_commit='f737939',q7_protocol={'fixture':True},cells=[current],input_sha256=payload['input_sha256'])
    fit=dict(q7,cells=[dict(current,candidates=[new])])
    folder=b.OUTPUT/'tests'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    oldpath,fitpath=folder/'old.json',folder/'fit.json'
    b.dump(oldpath,old); b.dump(fitpath,fit)
    # Start with an actual record; visibly replace fit-dependent fields.
    source=next((b.ROOT/'outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/out').glob('*.jsonl'))
    template=json.loads(source.read_text(encoding='utf8').splitlines()[0])
    def record(k,path):
        r=copy.deepcopy(template)
        for name in ('cell_id','unit_id','sigma','rho','realization','observed_data_sha256'): r[name]=cell[name]
        r['candidate_id']=k['candidate_id']; r['params']=k['p0']
        r['provenance']['paths_sha256']=b.q6.sha256(path)
        r['provenance']['runner_sha256']=b.q6.sha256(b.ROOT/'studies/regression/sideproject_q5_noise_fits.jl')
        for name in r['provenance']['source_sha256']:
            r['provenance']['source_sha256'][name]=b.q6.sha256(b.ROOT/name)
        kept=[]; offset=0
        for eq in k['equations']:
            n=len(eq['term_names'])
            names=prune_terms(dict(zip(eq['term_names'],r['params'][offset:offset+n])))
            kept.append([i for i,name in zip(eq['basis_indices'],eq['term_names']) if name in names]); offset+=n
        r['pruned_active_idxs']=kept
        return r
    oldrecords=[record(k,oldpath) for k in cell['candidates']+cell['upper_candidates']]
    newrecords=[record(new,fitpath)]
    return q7,fit,old,oldrecords,newrecords,fitpath,oldpath,rows


def test_rule_boundary_and_nonpositive_noise(monkeypatch):
    class Fit:
        p=1
        def sse(self,s): return 20. if not s else 13.365
    monkeypatch.setattr(b.q6,'projected_noise_floor',lambda d,s,o: 2. if not s else 1.)
    end=b.significance_end([None],[None],6.635)
    assert end(0,Fit(),set()) is None
    assert b.significance_end([None],[None],6.636)(0,Fit(),set())==20.
    monkeypatch.setattr(b.q6,'projected_noise_floor',lambda *args: 1.)
    assert b.significance_end([None],[None],1e99)(0,Fit(),set()) is None


def test_real_path_comparison_both_thresholds_and_determinism(derived):
    old=derived[2]['cells'][0]
    first=b.build_cell(old); second=b.build_cell(old)
    assert b.q6.canonical(first)==b.q6.canonical(second)
    assert len(first[0])==2
    assert all('classification' not in r for r in first[1])
    for cell in first[0].values():
        assert cell['upper_candidates']==[]
        assert all(k['candidate_id'].startswith('q7_') for k in cell['candidates'])


def test_input_hash_and_observation_hash_failures(derived,monkeypatch):
    payload=json.loads(b.q6.Q5.read_bytes()); b.verify_inputs(payload)
    payload['input_sha256']['outputs/phase_c_c6_data_conditions_5dd1df8/index.csv']='wrong'
    with pytest.raises(ValueError,match='hash mismatch'): b.verify_inputs(payload)
    cell=copy.deepcopy(derived[2]['cells'][0]); cell['observed_data_sha256']='wrong'
    with pytest.raises(ValueError,match='observed hash mismatch'): b.build_cell(cell)


def test_join_and_imported_selection(derived):
    cells,joined,controls=a.join_records(*derived[:7])
    assert len(controls)==1 and controls[0]['p0_equal'] and controls[0]['support_equal']
    for k in cells[0]['candidates']:
        source=derived[3][next(i for i,r in enumerate(derived[3]) if r['candidate_id']==k['reuse_q5_candidate_id'])] if not k['new'] else derived[4][0]
        assert joined[cells[0]['cell_id'],k['candidate_id']] is source
    _,choices=a.q5.rows_for_cells(cells,joined)
    costs=a.cost_rows(derived[0]['cells'],joined)
    assert costs[0]['candidate_states']==2 and costs[0]['new_fits']==1 and costs[0]['reused_states']==1
    assert {'a','b','c'} <= {r['size_rule'] for r in choices}
    assert a.q5.select.__module__=='aggregate_sideproject_q4'


@pytest.mark.parametrize('failure',['missing_old','missing_new','duplicate','p0','support','observed','fingerprint','runner','source','fit_extra','marker'])
def test_join_rejects_bad_inputs(derived,failure):
    args=copy.deepcopy(list(derived[:7]))
    if failure=='missing_old': args[3].pop()
    elif failure=='missing_new': args[4].clear()
    elif failure=='duplicate':
        duplicate=copy.deepcopy(args[4][0]); duplicate['optimizer_loss']+=1; args[4].append(duplicate)
    elif failure in ('p0','support','marker'):
        k=args[0]['cells'][0]['candidates'][0]
        if failure=='p0': k['p0'][0]+=1
        elif failure=='support': k['active_idxs'][0].append(999)
        else: k['new']=True
    elif failure=='observed': args[4][0]['observed_data_sha256']='wrong'
    elif failure=='fingerprint': args[4][0]['provenance']['settings_fingerprint']='wrong'
    elif failure=='runner': args[4][0]['provenance']['runner_sha256']='wrong'
    elif failure=='source':
        key=next(iter(args[4][0]['provenance']['source_sha256'])); args[4][0]['provenance']['source_sha256'][key]='wrong'
    else: args[1]['cells'][0]['upper_candidates']=[args[1]['cells'][0]['candidates'][0]]
    with pytest.raises(ValueError): a.join_records(*args)


def test_decision_exact_margin_and_dim4():
    rows=[dict(stratum=s,cell_id=f'{s}_{i}',unit_id='fixture',sigma=.01,size_rule='c',
               pruned_exact=i<19,generalization_variance_weighted_hit=i<19) for s in ('dim2','dim4') for i in range(20)]
    old=[dict(r,pruned_exact=True,generalization_variance_weighted_hit=True) for r in rows]
    out=a.decision_inputs(rows,old)
    assert all(r['noninferior'] is True for r in out if r['stratum']=='dim2')
    assert all(r['noninferior'] is None for r in out if r['stratum']=='dim4')
    rows[0]['pruned_exact']=False
    assert not a.decision_inputs(rows,old)[0]['noninferior']


def test_wsindy_complete_cells_and_both_libraries(derived):
    c=derived[0]['cells'][0]
    choices=[dict(c,size_rule='c',**{m:False for m in a.q5.METRICS})]
    refs=[]
    for config in ('W1:L-C6','W1:L-Q5','W1-interp:L-C6','W1-interp:L-Q5'):
        refs.append(dict(system_id=c['system_id'],initial_condition_set=c['initial_condition_set'],
                         noise_sigma=c['sigma'],subsample_rho=c['rho'],noise_realization=c['realization'],
                         q5w_library_evaluations=1,q5w_least_squares_solves=1,q5w_configuration=config,observed_data_sha256=c['observed_data_sha256'],fit_status='success',
                         **{f:False for f in a.q5.METRICS.values()}))
    assert a.wsindy_tables(choices,pd.DataFrame(refs),[c])
    with pytest.raises(ValueError,match='Incomplete'): a.wsindy_tables(choices,pd.DataFrame(refs[:1]),[c])
    with pytest.raises(ValueError,match='Incomplete'): a.wsindy_tables(choices,pd.DataFrame(refs+refs),[c])


def test_reporting_tables_on_synthetic_fixture(derived):
    cells,joined,_=a.join_records(*derived[:7])
    _,choices=a.q5.rows_for_cells(cells,joined)
    c=cells[0]
    references=[]
    for method in ('sindy','weak_sindy','e_sindy'):
        for i in range(10 if method=='weak_sindy' else 2):
            references.append(dict(system_id=c['system_id'],source_initial_condition_set=c['initial_condition_set'],
                noise_sigma=c['sigma'],subsample_rho=c['rho'],noise_realization=c['realization'],
                method=method,include_sin_cos=i<2,polynomial_degree=3,method_config_id=str(i),
                **{f:False for f in a.q5.METRICS.values()}))
    rates,diagnostics=a.q5.report_tables(choices,pd.DataFrame(references))
    assert {r['configuration'] for r in rates if r['method']=='Q5'} >= {'a','b','c'}
    assert {'D1_denominator','D2_denominator','D3_denominator','D4_size_errors','D5_clean_start_mse_mean'} <= diagnostics[0].keys()
    folder=derived[5].parent/'tables'; folder.mkdir()
    for name,rows in (('rates',rates),('diagnostics',diagnostics),('choices',choices)):
        pd.DataFrame(rows).to_csv(folder/(name+'.csv'),index=False)
        assert len(pd.read_csv(folder/(name+'.csv')))==len(rows)


def test_full_aggregation_refuses_partial_scope_before_output(derived):
    q7,fit,old,_,_,fitpath,oldpath,_=derived
    path=fitpath.parent/'q7.json'
    b.dump(path,dict(q7,mode='grid'))
    b.dump(fitpath,dict(fit,mode='grid'))
    output=fitpath.parent/'refused'
    with pytest.raises(ValueError,match='Full grid required'):
        a.run([],[],[],path,fitpath,output,oldpath)
    assert not output.exists()
    # Restore the original fixture bytes for independent tests.
    b.dump(fitpath,fit)


def test_complete_writer_serial_and_file_worker_determinism():
    directory=b.OUTPUT/'tests'/uuid.uuid4().hex
    first=b.run(directory/'serial',limit=2,workers=1)
    second=b.run(directory/'workers',limit=2,workers=2)
    assert first==second
    assert {p.name for p in (directory/'serial').iterdir()}=={p.name for p in (directory/'workers').iterdir()}
    for p in (directory/'serial').iterdir():
        assert p.read_bytes()==(directory/'workers'/p.name).read_bytes()
    fit=json.loads((directory/'serial/q7_fit_paths.json').read_bytes())
    assert fit['protocol_commit']=='f737939'
    assert fit['cells']==[]  # The first two real dim1 cells need no new states.
    controls=pd.read_csv(directory/'serial/controls.csv')
    assert len(controls)==2 and controls.exploratory_support_control.all()


def test_empty_path_keeps_cell_and_imported_unselected_rules(derived):
    cells,joined,_=a.join_records(*derived[:7])
    old=derived[2]['cells']
    oldmap={(r['cell_id'],r['candidate_id']):r for r in derived[3]}
    oldcandidates,oldchoices=a.q5.rows_for_cells(old,oldmap)
    empty=dict(cells[0],candidates=[])
    rows,choices=a.rows_for_q7_cells([empty],joined,oldcandidates,oldchoices)
    assert len(rows)==1 and rows[0]['candidate_id']=='upper_subset'
    assert {r['size_rule'] for r in choices}=={'a','b','c','upper_path','upper_subset'}
    for row in choices:
        assert row['n_candidates']==0 and row['total_loss_evals']==0 and not row['truth_on_path']
        assert not row['ended_at_cap'] and not row['last_path_state']
        if row['size_rule']!='upper_subset':
            assert row['candidate_id'] is None and row['k'] is None
            assert all(row[m] is False for m in a.q5.METRICS)
