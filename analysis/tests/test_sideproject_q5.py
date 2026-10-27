"""Q5 fixtures derive from real export cells and Q4 fit records."""
import copy
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import uuid

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts/aggregate'
sys.path.insert(0,str(SCRIPTS))
import build_sideproject_q5_paths as builder
import aggregate_sideproject_q5 as agg
from phase1_diagnostic import prune_terms


@pytest.fixture
def tmp_path():
    # Windows managed sandbox cannot reopen pytest's mode-0700 directories.
    # Retain derived fixtures in this script's own output directory for review.
    directory = builder.ROOT/'outputs/sideproject_q5_tests'/uuid.uuid4().hex
    directory.mkdir(parents=True)
    return directory


@pytest.fixture(scope='module')
def real():
    q4 = json.loads(builder.Q4.read_text())
    probe = json.loads((builder.BASE/'q5_probe_paths.json').read_text())
    records = [json.loads(line) for p in builder.Q4_RESULTS for line in p.read_text().splitlines()]
    refs = pd.read_csv(agg.REFERENCE,low_memory=False)
    return q4,probe,records,refs


def test_irregular_grid_and_determinism(real):
    q4,probe,_,_ = real
    c = next(c for c in probe['cells'] if c['rho']==.5 and c['dim']==1)
    row = builder.read_export_index(builder.EXPORT/'index.csv')
    row = row[(row.system_id==c['system_id']) & (row.initial_condition_set==c['initial_condition_set']) &
              (row.noise_sigma==c['sigma']) & (row.subsample_rho==c['rho']) & (row.noise_realization==1)].iloc[0]
    unit = next(u for u in q4['units'] if u['unit_id']==c['unit_id'])
    a,b = builder.build_cell(unit,row),builder.build_cell(unit,row)
    assert a == b == c
    t,x = builder.read_index_cell(builder.EXPORT,row)
    assert not np.allclose(np.diff(t),np.diff(t)[0])
    terms = builder.phasec_basis(1)
    design,target,_ = builder.build_design(t,x,0,'weak',terms)
    # First weak window is exactly the actual-time trapezoid and endpoint increment.
    assert target[0] == x[1,0]-x[0,0]
    assert design[0,0] == t[1]-t[0]


def test_all_clean_paths_are_q4_bit_identical(real):
    q4,_,_,_ = real
    controls = json.loads((builder.BASE/'q5_controls_paths.json').read_text())
    byid = {u['unit_id']:u for u in q4['units']}
    assert len(controls['cells']) == 48
    for c in controls['cells']:
        assert agg.canonical_bits(c['candidates']) == agg.canonical_bits(byid[c['unit_id']]['candidates'])
        assert agg.canonical_bits(c['upper_candidates']) == agg.canonical_bits(byid[c['unit_id']]['upper_candidates'])


def synthetic_records(real, paths):
    q4,probe,q4records,refs = real
    payload = copy.deepcopy(probe)
    # Current source inventory is based on an actual Q4 record, with visible Q5 additions.
    base = q4records[0]
    source = {name:builder.sha256(builder.ROOT/name) for name in base['provenance']['source_sha256']}
    for name in ('sideproject_q4_path_fits.jl','sideproject_q5_noise_fits.jl'):
        rel = 'studies/regression/'+name
        source[rel] = builder.sha256(builder.ROOT/rel)
    paths.write_text(json.dumps(payload))
    provenance = dict(paths_sha256=builder.sha256(paths),
        index_sha256=builder.sha256(builder.EXPORT/'index.csv'), protocol_commit='f737939',
        runner_sha256=source['studies/regression/sideproject_q5_noise_fits.jl'],
        settings_fingerprint=base['provenance']['settings_fingerprint'], source_sha256=source)
    q4map = {(r['unit_id'],r['candidate_id']):r for r in q4records}
    results = []
    for c in payload['cells']:
        for k in c['candidates']+c['upper_candidates']:
            original = q4map[c['unit_id'],k['candidate_id']] if c['sigma']==c['rho']==0 else base
            r = copy.deepcopy(original)
            r.pop('control_passed',None)
            r.pop('expected_loss',None)
            r.update(unit_id=c['unit_id'],cell_id=c['cell_id'],candidate_id=k['candidate_id'],
                sigma=c['sigma'],rho=c['rho'],realization=c['realization'],
                observed_data_sha256=c['observed_data_sha256'],provenance=provenance,
                reconstruction=copy.deepcopy(r['training']),clean_ic_observed_mse=r['training']['loss'],evaluation_ode_solves=4)
            if c['sigma'] or c['rho']:
                # Synthetic coefficient output uses the real weak-start vector.
                r['params'] = k['p0']
                r['training']['n_samples'] = c['n_observed_points']*c['dim']
                kept,offset = [],0
                for eq in k['equations']:
                    n = len(eq['term_names'])
                    names = prune_terms(dict(zip(eq['term_names'],r['params'][offset:offset+n])))
                    kept.append([i for i,name in zip(eq['basis_indices'],eq['term_names']) if name in names])
                    offset += n
                r['pruned_active_idxs'] = kept
            results.append(r)
    return payload,results


def test_aggregation_and_no_overwrite(real,tmp_path):
    paths = tmp_path/'paths.json'
    payload,records = synthetic_records(real,paths)
    result = tmp_path/'results.jsonl'
    result.write_text(''.join(json.dumps(r)+'\n' for r in records+[records[0]]))
    metadata = agg.run([result],paths,tmp_path/'tables')
    assert metadata['duplicates_compared']==1
    rates = pd.read_csv(tmp_path/'tables/q5_rates.csv')
    assert {'Q5','sindy','weak_sindy','e_sindy'} == set(rates.method)
    assert (rates.n_units>0).all()
    diagnostics = pd.read_csv(tmp_path/'tables/q5_diagnostics.csv')
    assert {'D1_denominator','D2_denominator','D3_denominator','D4_size_errors','D5_clean_start_mse_mean'} <= set(diagnostics)
    with pytest.raises(FileExistsError):
        agg.run([result],paths,tmp_path/'tables')


@pytest.mark.parametrize('failure',['hash','baseline_hash','fingerprint','source','missing','duplicate','signed_zero','clean_loss','candidate','settings'])
def test_control_failures_abort(real,tmp_path,failure):
    paths = tmp_path/'paths.json'
    payload,records = synthetic_records(real,paths)
    refs = real[3]
    if failure=='baseline_hash':
        refs = refs.copy()
        refs['observed_data_sha256']='wrong'
    elif failure=='source':
        records[0]['provenance']['source_sha256']['studies/regression/sideproject_q5_noise_fits.jl']='wrong'
    elif failure=='hash':
        records[0]['observed_data_sha256']='wrong'
    elif failure=='fingerprint':
        records[0]['provenance']=dict(records[0]['provenance'],settings_fingerprint='wrong')
    elif failure=='missing':
        records.pop()
    elif failure=='duplicate':
        duplicate=copy.deepcopy(records[0]); duplicate['params'][0]+=1; records.append(duplicate)
    elif failure=='signed_zero':
        duplicate=copy.deepcopy(records[0]); records[0]['clean_ic_observed_mse']=0.; duplicate['clean_ic_observed_mse']=-0.; records.append(duplicate)
    elif failure=='clean_loss':
        records[0]['training']['loss']+=1
    elif failure=='candidate':
        payload['cells'][0]['candidates'][0]['p0'][0]+=1
        paths.write_text(json.dumps(payload))
        for r in records:
            r['provenance']['paths_sha256']=builder.sha256(paths)
    elif failure=='settings':
        records[0]['optimizer_settings']['clamp_val']=11
    result=tmp_path/'results.jsonl'
    result.write_text(''.join(json.dumps(r)+'\n' for r in records))
    reference=agg.REFERENCE
    if failure=='baseline_hash':
        reference=tmp_path/'reference.csv'
        refs.to_csv(reference,index=False)
    with pytest.raises(ValueError):
        agg.run([result],paths,tmp_path/'tables',reference=reference)
    assert not (tmp_path/'tables').exists()


def test_q4_source_unchanged():
    assert builder.sha256(builder.ROOT/'studies/regression/sideproject_q4_path_fits.jl') == '2725a2927c9197fe103a4b21d8a9aad0dea111220ace5eaf99bbcd6ac56933e4'


def test_threshold_selection_is_pooled_and_metric_specific(real,tmp_path):
    payload,records = synthetic_records(real,tmp_path/'paths.json')
    bykey={(r['cell_id'],r['candidate_id']):r for r in records}
    _,choices=agg.rows_for_cells(payload['cells'],bykey)
    refs=real[3].copy()
    matching=(refs.method=='weak_sindy') & refs.include_sin_cos.map(agg.boolean) & (refs.polynomial_degree==3)
    # Equal pooled structure rates; deterministic lower threshold wins the tie.
    refs.loc[matching,'sindy_structure_hit_raw'] = (
        (refs.stlsq_threshold==.01) & (refs.subsample_rho==0) |
        (refs.stlsq_threshold==.1) & (refs.subsample_rho==.5))
    # Opposite best threshold for a separate metric.
    refs.loc[matching,'sindy_structure_hit_pruned'] = refs.stlsq_threshold==.1
    rates,_=agg.report_tables(choices,refs)
    rows=[r for r in rates if r['method']=='weak_sindy' and r['configuration']!='all_ten']
    assert all(r['configuration'].endswith('_0.01') for r in rows if r['metric']=='raw_exact')
    assert all(r['configuration'].endswith('_0.1') for r in rows if r['metric']=='pruned_exact')
    assert all(r['rate']==0 for r in rows if r['metric']=='raw_exact' and r['rho']==.5)


def test_manifests_and_shard_lists():
    import yaml
    for mode,count,suffix in [('probe',9,'_probe'),('grid',1632,'')]:
        path=builder.ROOT/f'k8s/sideproject_q5{suffix}_job.yaml'
        job=yaml.safe_load(path.read_text())
        spec=job['spec']; pod=spec['template']['spec']; container=pod['containers'][0]
        assert spec['completionMode']=='Indexed' and spec['completions']==count and spec['parallelism']==8
        assert 'activeDeadlineSeconds' not in spec and 'activeDeadlineSeconds' not in pod
        assert container['resources']['requests']==container['resources']['limits']=={'cpu':'1','memory':'4Gi'}
        assert {e['name']:e['value'] for e in container['env']}=={'JULIA_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
        entries=(builder.BASE/f'q5_{mode}_paths.shards.txt').read_text().splitlines()
        cells=json.loads((builder.BASE/f'q5_{mode}_paths.json').read_text())['cells']
        assert entries==[c['cell_id'] for c in cells] and len(entries)==count
        ranks=[builder.STRATA.index(c['stratum']) for c in cells]
        assert ranks==sorted(ranks)
