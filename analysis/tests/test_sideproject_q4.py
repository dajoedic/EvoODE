"""Q4 controls: constructed weak designs and fixtures derived from real reference rows."""
import copy
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis/scripts/aggregate'))
from build_sideproject_q4_paths import growth_path, OUTPUT
from aggregate_sideproject_q4 import select, reference_join, REFERENCE, candidate_row, summarize
from phase1_diagnostic import prune_terms


def test_correlated_decoy_added_then_removed():
    a = np.column_stack(([1.,1.,.3], [1.,0.,0.], [0.,1.,0.]))
    path, log = growth_path([a],[np.array([1.,1.,0.])])
    assert path[0]['support'] == [[0]]
    assert path[-1]['support'] == [[1,2]]
    assert any(check['removed'] and check['removed']['basis_index'] == 1
               for step in log for check in step['backward_checks'])
    assert path[-1]['origin'] == 'removal'


def test_cross_equation_normalisation():
    a = np.eye(2)
    path, log = growth_path([a,a],[np.array([100.,100.]),np.array([0.,1.])])
    assert log[0]['addition']['equation'] == 2
    assert log[0]['addition']['gain'] == pytest.approx(1.)


def test_cap_and_determinism():
    a,b = np.eye(10),np.ones(10)
    first = growth_path([a],[b])
    assert first == growth_path([a],[b])
    assert len(first[0]) == 6
    assert len(first[0][-1]['support'][0]) == 6


def test_size_rules_and_sentinel():
    candidates = [
        dict(candidate_id='small',step=1,k=1,weak_bic=0,mse=.1,n_samples=100,sentinel=False,diverged=False),
        dict(candidate_id='large',step=2,k=2,weak_bic=1,mse=.0995,n_samples=100,sentinel=False,diverged=False),
        dict(candidate_id='sentinel',step=3,k=3,weak_bic=-10,mse=1e-20,n_samples=100,sentinel=True,diverged=False),
        dict(candidate_id='diverged',step=4,k=4,weak_bic=4,mse=1e-30,n_samples=100,sentinel=False,diverged=True)]
    assert select(candidates,'a')['candidate_id'] == 'sentinel'
    assert select(candidates,'b')['candidate_id'] == 'small'
    assert select(candidates,'c')['candidate_id'] == 'small'
    assert select(candidates[2:],'c') is None
    changed = copy.deepcopy(candidates)
    changed[1]['mse'] = .001
    assert select(changed,'c')['candidate_id'] == 'large'


@pytest.fixture
def real_references():
    # Exact real rows, filtered only; no invented reference schema.
    frame = pd.read_csv(REFERENCE)
    return frame[(frame.system_id == 1) & (frame.source_initial_condition_set == 1)].copy()


def test_reference_join_real_rows(real_references):
    units = [dict(system_id=1,initial_condition_set=1)]
    joined = reference_join(real_references,units)
    assert len(joined) == 33
    assert set(joined.target_initial_condition_set) == {2}
    broken = real_references.copy()
    broken.loc[broken.index[0],'direction'] = 'IC2_to_IC1'
    with pytest.raises(ValueError,match='IC/direction'):
        reference_join(broken,units)
    with pytest.raises(ValueError,match='Missing'):
        reference_join(joined.iloc[1:],units)


def test_real_path_pruning_and_metrics():
    unit = json.loads(OUTPUT.read_text())['units'][0]
    candidate = unit['candidates'][0]
    # New Q4 result fields explicitly derived from a real path's weak coefficients.
    params = candidate['p0']
    kept,offset = [],0
    for eq in candidate['equations']:
        n = len(eq['term_names'])
        names = prune_terms(dict(zip(eq['term_names'],params[offset:offset+n])))
        kept.append([i for i,name in zip(eq['basis_indices'],eq['term_names']) if name in names])
        offset += n
    metric = dict(loss=.001,n_samples=100,sentinel=False,diverged=False,
                  r2_arithmetic=.95,r2_variance_weighted=.96)
    result = dict(params=params,pruned_active_idxs=kept,fit_meta=dict(loss_evals=7),
                  training=metric,generalization=metric)
    truth = [set(eq['term_names']) for eq in candidate['equations']]
    row = candidate_row(unit,candidate,result,truth)
    assert row['raw_exact'] and row['pruned_exact']
    assert row['generalization_variance_weighted_hit']
    broken = copy.deepcopy(result)
    broken['pruned_active_idxs'] = [[]]
    with pytest.raises(ValueError,match='pruning'):
        candidate_row(unit,candidate,broken,truth)


@pytest.fixture
def q4_records():
    from aggregate_sideproject_q4 import sha256
    payload = json.loads(OUTPUT.read_text())
    # Base fields/fit metadata come from an actual Q3 W1 record.
    q3path = ROOT/'outputs/sideproject_q3_weak_start/results.jsonl'
    real = json.loads(q3path.read_text().splitlines()[0])
    provenance = dict(protocol_commit='24ede2d',paths_sha256=sha256(OUTPUT),
        runner_sha256=sha256(ROOT/'studies/regression/sideproject_q4_path_fits.jl'),
        q3_results_sha256=sha256(q3path),
        q3_weak_sha256=sha256(ROOT/'analysis/data/sideproject_residual_growth/q3_weak_starts.json'),
        settings_fingerprint='explicit-test-settings',source_sha256={})
    records = []
    for unit in payload['units']:
        for candidate in unit['candidates']+unit['upper_candidates']:
            params = candidate['p0']
            pruned,offset = [],0
            for eq in candidate['equations']:
                n = len(eq['term_names'])
                kept = prune_terms(dict(zip(eq['term_names'],params[offset:offset+n])))
                pruned.append([i for i,name in zip(eq['basis_indices'],eq['term_names']) if name in kept])
                offset += n
            # Q4-only fields are explicitly added, preserving the real Q3 meta field inventory.
            metric = dict(loss=real['W1']['loss'],r2_arithmetic=real['W1']['r2'],
                r2_variance_weighted=real['W1']['r2'],n_samples=100,sentinel=False,diverged=False)
            records.append(dict(unit_id=unit['unit_id'],candidate_id=candidate['candidate_id'],
                params=params,pruned_active_idxs=pruned,fit_meta=real['W1']['fit_meta'],
                optimizer_loss=real['W1']['optimizer_loss'],
                training=metric,generalization=metric,trajectory_control=real['trajectory_control'],
                provenance=provenance))
    control = copy.deepcopy(records[0])
    control.update(candidate_id='control_true',control_passed=True,expected_loss=real['W1']['loss'])
    records.append(control)
    return records


def test_complete_aggregation_and_missing_candidate(tmp_path, q4_records):
    from aggregate_sideproject_q4 import run
    records = q4_records
    result_path = tmp_path/'fits.jsonl'
    result_path.write_text(''.join(json.dumps(r)+'\n' for r in records))
    target = tmp_path/'complete'
    metadata = run(result_path,OUTPUT,target)
    assert metadata['path_candidates'] == 769
    assert len(pd.read_csv(target/'q4_units.csv')) >= 300
    assert len(pd.read_csv(target/'q4_units.csv').query("size_rule in ['a','b','c']")) == 180
    assert len(pd.read_csv(target/'q4_rules_by_stratum.csv')) == 15
    result_path.write_text(''.join(json.dumps(r)+'\n' for r in records[1:]))
    with pytest.raises(ValueError,match='Missing or unexpected'):
        run(result_path,OUTPUT,tmp_path/'incomplete')
    assert not (tmp_path/'incomplete').exists()


def write_records(path, records):
    path.write_text(''.join(json.dumps(r)+'\n' for r in records))
    return path


@pytest.mark.parametrize('use_glob', [False, True])
def test_multifile_two_runner_hashes_and_platform_duplicates(tmp_path, q4_records, use_glob):
    from aggregate_sideproject_q4 import run, Q4_RUNNER_HASHES
    records = copy.deepcopy(q4_records)
    for record in records:
        record['provenance']['runner_sha256'] = Q4_RUNNER_HASHES[0]
    # Orion re-fits the three candidates of the real sys0024_ic1 path.
    platform = copy.deepcopy([r for r in records if r['unit_id'] == 'sys0024_ic1'])
    assert len(platform) == 3
    for record in platform:
        record['provenance']['runner_sha256'] = Q4_RUNNER_HASHES[1]
        record['provenance']['input_paths'] = {'--paths': '/outputs/input/q4_paths.json'}
    files = [write_records(tmp_path/'laptop.jsonl', records[:400]),
             write_records(tmp_path/'remaining.jsonl', records[400:]),
             write_records(tmp_path/'orion.jsonl', platform)]
    metadata = run(str(tmp_path/'*.jsonl') if use_glob else files, OUTPUT, tmp_path/'tables')
    assert metadata['duplicates_compared'] == 3
    assert metadata['runner_sha256_accepted'] == list(Q4_RUNNER_HASHES)
    assert metadata['runner_sha256_observed'] == sorted(Q4_RUNNER_HASHES)
    assert metadata['settings_fingerprint'] == 'explicit-test-settings'
    assert len(metadata['result_files']) == 3
    assert len(pd.read_csv(tmp_path/'tables/q4_candidates.csv')) == 829


@pytest.mark.parametrize('field', ['training', 'generalization', 'optimizer_loss'])
def test_duplicate_loss_must_be_bit_identical(tmp_path, q4_records, field):
    from aggregate_sideproject_q4 import run
    records = copy.deepcopy(q4_records)
    if field == 'optimizer_loss':
        records[0][field] = 0.0
    else:
        records[0][field]['loss'] = 0.0
    duplicate = copy.deepcopy(records[0])
    if field == 'optimizer_loss':
        duplicate[field] = -0.0
    else:
        duplicate[field]['loss'] = -0.0
    source = write_records(tmp_path/'records.jsonl', records)
    other = write_records(tmp_path/'duplicate.jsonl', [duplicate])
    with pytest.raises(ValueError, match='not bit-identical'):
        run([source, other], OUTPUT, tmp_path/'tables')
    assert not (tmp_path/'tables').exists()


@pytest.mark.parametrize('invalid', ['runner', 'settings', 'duplicate_settings', 'duplicate_source'])
def test_multifile_provenance_remains_strict(tmp_path, q4_records, invalid):
    from aggregate_sideproject_q4 import run
    records = copy.deepcopy(q4_records)
    changed = copy.deepcopy(records[0])
    if invalid == 'runner':
        changed['provenance']['runner_sha256'] = '0'*64
    elif invalid in ('settings', 'duplicate_settings'):
        changed['provenance']['settings_fingerprint'] = 'different-settings'
    else:
        changed['provenance']['source_sha256'] = {'Project.toml': '0'*64}
    base = records if invalid.startswith('duplicate') else records[1:]
    a = write_records(tmp_path/'base.jsonl', base)
    b = write_records(tmp_path/'changed.jsonl', [changed])
    with pytest.raises(ValueError, match='provenance|settings|source changed'):
        run([a,b], OUTPUT, tmp_path/'tables')
    assert not (tmp_path/'tables').exists()


def test_result_file_expansion_and_pinned_runner(tmp_path):
    from aggregate_sideproject_q4 import result_files, sha256, Q4_RUNNER_POST_FA4B_SHA256
    with pytest.raises(FileNotFoundError):
        result_files(str(tmp_path/'missing*.jsonl'))
    with pytest.raises(ValueError, match='No result files'):
        result_files([])
    assert sha256(ROOT/'studies/regression/sideproject_q4_path_fits.jl') == Q4_RUNNER_POST_FA4B_SHA256


@pytest.fixture
def crlf_source(tmp_path):
    # Derive the source fixture from the actual Q3 source recorded by the Q4 runner.
    source = tmp_path/'source.txt'
    data = (ROOT/'studies/regression/sideproject_q3_weak_start.jl').read_bytes()
    source.write_bytes(data.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
    return source


def test_source_line_endings_and_metadata(tmp_path, q4_records, crlf_source):
    import hashlib
    from aggregate_sideproject_q4 import run, sha256
    records = copy.deepcopy(q4_records)
    raw = sha256(crlf_source)
    lf = hashlib.sha256(crlf_source.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
    assert raw != lf
    for index, record in enumerate(records):
        record['provenance'] = copy.deepcopy(record['provenance'])
        record['provenance']['source_sha256'] = {str(crlf_source): raw if index == 0 else lf}
    # Duplicates must also be validated and included in the variant match counts.
    records.append(copy.deepcopy(records[0]))
    target = tmp_path/'tables'
    metadata = run(write_records(tmp_path/'records.jsonl', records), OUTPUT, target)
    expected = dict(raw_sha256=raw, lf_sha256=lf, raw_matches=2, lf_matches=len(records)-2)
    assert metadata['source_sha256'][str(crlf_source)] == expected
    assert json.loads((target/'q4_run_metadata.json').read_text())['source_sha256'][str(crlf_source)] == expected
    assert metadata['duplicates_compared'] == 1


def test_different_source_content_rejected(tmp_path, q4_records, crlf_source):
    import hashlib
    from aggregate_sideproject_q4 import run
    records = copy.deepcopy(q4_records)
    records[0]['provenance']['source_sha256'] = {
        str(crlf_source): hashlib.sha256(crlf_source.read_bytes()+b'# changed').hexdigest()}
    with pytest.raises(ValueError, match='Julia source changed'):
        run(write_records(tmp_path/'records.jsonl', records), OUTPUT, tmp_path/'tables')
    assert not (tmp_path/'tables').exists()


def test_identical_source_variants_count_both(tmp_path):
    from aggregate_sideproject_q4 import check_source_hash, sha256
    source = tmp_path/'source.txt'
    source.write_bytes(b'line\nstandalone\rcarriage return\n')
    metadata = {}
    check_source_hash(str(source), sha256(source), metadata)
    entry = metadata[str(source)]
    assert entry['raw_sha256'] == entry['lf_sha256']
    assert entry['raw_matches'] == entry['lf_matches'] == 1


@pytest.mark.parametrize('field', ['paths_sha256', 'q3_results_sha256', 'q3_weak_sha256'])
def test_data_hashes_remain_byte_exact(tmp_path, q4_records, field):
    import hashlib
    from aggregate_sideproject_q4 import run, sha256
    records = copy.deepcopy(q4_records)
    # A CRLF data file and its LF digest differ; source normalization must not apply here.
    source = tmp_path/'data.json'
    source.write_bytes(b'{\r\n}\r\n')
    records[0]['provenance'][field] = hashlib.sha256(b'{\n}\n').hexdigest()
    import aggregate_sideproject_q4 as aggregation
    original_sha256 = aggregation.sha256
    data_path = {'paths_sha256': OUTPUT,
                 'q3_results_sha256': ROOT/'outputs/sideproject_q3_weak_start/results.jsonl',
                 'q3_weak_sha256': ROOT/'analysis/data/sideproject_residual_growth/q3_weak_starts.json'}[field]
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(aggregation, 'sha256', lambda path: sha256(source) if path == data_path else original_sha256(path))
        with pytest.raises(ValueError, match='provenance|source changed'):
            run(write_records(tmp_path/'records.jsonl', records), OUTPUT, tmp_path/'tables')
    assert not (tmp_path/'tables').exists()
