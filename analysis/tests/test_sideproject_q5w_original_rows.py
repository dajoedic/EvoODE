"""Small fixtures derived from actual MATLAB/port records, no full evaluation."""
import copy
import json
import sys
import uuid
import time
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis/scripts/aggregate'))
import evaluate_sideproject_q5w_matlab as evaluation
import q5w_row_sources as sources
from diagnose_sideproject_q5w_lstsq import qr_basic


@pytest.fixture
def real_fixture():
    base=evaluation.runner.OUTPUT
    cell=next(c for c in json.loads((base/'matlab_inputs/manifest.json').read_text())['cells'] if 'seed' not in c['cell_key'])
    original=json.loads((base/'matlab_outputs'/(cell['cell_id']+'.json')).read_text())
    port=pd.read_csv(base/'full/details.csv',nrows=1,float_precision='round_trip')
    folder=base/'test_original_rows'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    (folder/(cell['cell_id']+'.json')).write_text(json.dumps(original))
    return cell,original,port,folder


def test_manifest_bijection_hash_and_equation_controls(real_fixture):
    cell,original,_,folder=real_fixture
    inputs=evaluation.runner.OUTPUT/'matlab_inputs'
    manifest=dict(cells=[cell])
    assert evaluation.validate_outputs(manifest,folder,inputs)[cell['cell_id']]==original
    altered=copy.deepcopy(original);altered['state_sha256']='explicit-corruption'
    (folder/(cell['cell_id']+'.json')).write_text(json.dumps(altered))
    with pytest.raises(ValueError,match='identity mismatch'):evaluation.validate_outputs(manifest,folder,inputs)
    altered_cell=copy.deepcopy(cell);altered_cell['state_sha256']='explicit-corruption'
    with pytest.raises(ValueError,match='binary input hash'):evaluation.validate_outputs(dict(cells=[altered_cell]),folder,inputs)
    (folder/(cell['cell_id']+'.json')).unlink()
    with pytest.raises(ValueError,match='bijection'):evaluation.validate_outputs(manifest,folder,inputs)
    (folder/(cell['cell_id']+'.json')).write_text(json.dumps(original))
    (folder/'unexpected.json').write_text('{}')
    with pytest.raises(ValueError,match='bijection'):evaluation.validate_outputs(manifest,folder,inputs)


def test_original_coefficients_use_same_evaluator_and_original_observations(real_fixture,monkeypatch):
    cell,original,port,_=real_fixture
    t,x=object(),object()
    calls=[]
    def evaluate(model,system,support,row,actual_t,actual_x,ct,clean):
        calls.append(model)
        assert actual_t is t and actual_x is x
        assert model.get_feature_names()==cell['column_names']
        np.testing.assert_array_equal(model.coefficients(),[e['coefficients_original_scale'] for e in original['equations']])
        return dict(port.iloc[0])
    monkeypatch.setattr(evaluation.runner,'evaluate',evaluate)
    row=evaluation.make_row(original,{},None,None,t,x,None,None,port.columns)
    assert len(calls)==1 and set(port.columns)<=set(row)
    assert row['q5w_coefficient_source']==evaluation.SOURCE
    assert all(row[c]=='' for c in evaluation.COST_FIELDS)
    assert row['q5w_input_state_sha256']==cell['state_sha256']
    assert json.loads(row['q5w_equations'])==original['equations']


def test_evaluation_control_names_every_difference(real_fixture):
    _,_,port,_=real_fixture
    before=port.iloc[0].to_dict(); after=copy.deepcopy(before)
    assert evaluation.differences(before,before,evaluation.evaluation_fields(port.columns))==[]
    empty=copy.deepcopy(before);empty['fit_error']=''
    assert evaluation.differences(empty,before,evaluation.evaluation_fields(port.columns))==[]
    after['reconstruction_r2_variance_weighted']+=1e-10
    after['active_terms_raw']='[]'
    result=evaluation.differences(after,before,evaluation.evaluation_fields(port.columns))
    assert {r['field'] for r in result}=={'active_terms_raw','reconstruction_r2_variance_weighted'}


def test_consumer_switch_all_arms_and_unavailable_costs(real_fixture):
    _,_,port,folder=real_fixture
    records=[]
    for arm,rho in [('W1',0),('W1',.5),('W1-interp',.5),('W1-cap',0),('W2',0)]:
        record=port.iloc[0].to_dict()
        record.update(q5w_configuration=arm+':L-C6',subsample_rho=rho)
        records.append(record)
    frame=pd.DataFrame(records)
    matlab=frame[sources.uniform_rows(frame)].copy()
    matlab['q5w_coefficient_source']=sources.SOURCE
    matlab['q5w_least_squares_solves']=np.nan
    target=folder/'details.csv';matlab.to_csv(target,index=False)
    (folder/'controls.json').write_text(json.dumps(dict(complete=True)))
    selected=sources.select_rows(frame,matlab_inputs=[target])
    assert len(selected)==len(frame)
    assert set(selected.loc[sources.uniform_rows(selected),'q5w_coefficient_source'])=={sources.SOURCE}
    assert set(selected.loc[~sources.uniform_rows(selected),'q5w_coefficient_source'])=={'port'}
    assert sources.known_cost(selected[sources.uniform_rows(selected)],'q5w_least_squares_solves') is None
    legacy=sources.select_rows(frame,'port')
    assert legacy.drop(columns='q5w_coefficient_source').equals(frame)
    matlab.iloc[:1].to_csv(target,index=False)
    with pytest.raises(ValueError,match='Missing MATLAB'):sources.select_rows(frame,matlab_inputs=[target])
    (folder/'controls.json').write_text(json.dumps(dict(complete=False)))
    with pytest.raises(ValueError,match='incomplete'):sources.select_rows(frame,matlab_inputs=[target])


def test_qr_candidate_is_basic_for_dependent_columns():
    g=np.array([[1.,1.],[2.,2.],[3.,3.]])
    coefficient,_,rank,_=qr_basic(g,g[:,0])
    assert rank==1 and np.count_nonzero(coefficient)==1
    np.testing.assert_allclose(g@coefficient,g[:,0])


def test_file_workers_equal_serial_on_two_real_records(real_fixture):
    cell,original,port,folder=real_fixture
    index=evaluation.runner.baseline.read_export_index(evaluation.runner.EXPORT/'index.csv')
    row=index[[evaluation.runner.key(r)==evaluation.runner.key(cell['cell_key']) for _,r in index.iterrows()]].iloc[0]
    payload=(original,row.to_dict(),list(port.columns))
    task=(evaluation.runner.key(row),cell['library'])
    evaluation.initialize_worker()
    expected=evaluation.evaluate_task(payload)
    actual=list(evaluation.file_workers([(task,payload),(task,payload)],folder,2,time.monotonic()+60))
    assert len(actual)==2
    for returned_task,result in actual:
        assert returned_task==task
        assert evaluation.differences(result,expected,evaluation.evaluation_fields(port.columns))==[]
        assert result['sindy_coefficients_full']==expected['sindy_coefficients_full']


def test_complete_small_pipeline_and_resume_provenance(real_fixture,monkeypatch):
    cell,original,port,folder=real_fixture
    real_base=evaluation.runner.OUTPUT
    for name in ('matlab_inputs','matlab_outputs','matlab_identity','full'):
        (folder/name).mkdir()
    (folder/'matlab_inputs/manifest.json').write_text(json.dumps(dict(cells=[cell])))
    shutil.copyfile(real_base/'matlab_inputs'/cell['input_file'],folder/'matlab_inputs'/cell['input_file'])
    (folder/'matlab_outputs'/(cell['cell_id']+'.json')).write_text(json.dumps(original))
    (folder/'matlab_identity/verdicts.json').write_text(json.dumps([dict(cell=cell['cell_id'],passed=True)]))
    port.to_csv(folder/'full/details.csv',index=False)
    monkeypatch.setattr(evaluation.runner,'OUTPUT',folder)
    monkeypatch.setattr(evaluation.runner,'reference_rows',lambda:port)
    output=folder/'evaluated'
    controls=evaluation.run(output=output,workers=1)
    assert controls['complete'] and controls['completed_c6_rows']==1
    assert controls['passing_identity_tasks_checked']==1
    assert controls['evaluation_exception_tasks']==0
    assert evaluation.run(output=output,controls_only=True)['complete']
    selected=sources.select_rows(port,matlab_inputs=[output/'details.csv'])
    assert set(selected.q5w_coefficient_source)=={sources.SOURCE}
    altered=pd.read_csv(output/'details.csv')
    altered['q5w_input_state_sha256']='explicit-corruption'
    altered.to_csv(output/'details.csv',index=False)
    with pytest.raises(ValueError,match='provenance differs'):
        evaluation.run(output=output,controls_only=True)
    assert not json.loads((output/'controls.json').read_text())['complete']


def test_legacy_port_resume_refuses_schema_mixing_before_fitting(real_fixture,monkeypatch):
    cell,_,port,folder=real_fixture
    port.to_csv(folder/'details.csv',index=False)
    rows=pd.DataFrame([cell['cell_key']])
    def unexpected():
        raise AssertionError('Reference loading must not precede the schema guard')
    monkeypatch.setattr(evaluation.runner,'reference_rows',unexpected)
    with pytest.raises(ValueError,match='Legacy CSV schema'):
        evaluation.runner.run(rows,configurations=('W1:L-Q5',),output=folder)
