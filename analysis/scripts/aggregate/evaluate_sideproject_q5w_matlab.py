"""Evaluate preserved MATLAB coefficients through the unchanged port evaluator.

Only technical controls are printed. Scientific rows remain in details.csv.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
import uuid
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.io import loadmat
from threadpoolctl import threadpool_limits
import run_sideproject_q5w_wsindy as runner
from compare_sideproject_q5w_matlab import compare_equations

SOURCE = 'matlab_original_72d8d6e'
IDENTITY_FIELDS = ('cell_id', 'cell_key', 'library', 'time_sha256', 'state_sha256', 'column_names', 'input_file')
COST_FIELDS = ('q5w_library_evaluations', 'q5w_least_squares_solves', 'fit_elapsed_s_context')
_WORKER = None


def initialize_worker():
    global _WORKER
    systems, support = runner.context()
    _WORKER = (systems, support, np.linspace(0,10,512), {}, threadpool_limits(limits=1))


def evaluate_task(payload):
    original, row_dict, columns = payload
    systems, supports, clean_t, cache, _ = _WORKER
    row = pd.Series(row_dict)
    t,x = runner.baseline.read_index_cell(runner.EXPORT,row)
    actual_t,actual_x = runner.interpolate_uniform(t,x) if original.get('arm')=='W1-interp' else (t,x)
    if digest(actual_t)!=original['time_sha256'] or digest(actual_x)!=original['state_sha256']:
        raise ValueError('export/manifest hash mismatch')
    sid = int(row.system_id)
    if sid not in cache:
        cache[sid] = {ic:runner.baseline.integrate_truth(systems[sid],ic-1,clean_t)[0] for ic in (1,2)}
    return make_row(original,row,systems[sid],supports.loc[sid].to_dict(),t,x,clean_t,cache[sid],columns)


def json_default(value):
    return value.item() if hasattr(value,'item') else str(value)


def worker_file(path):
    """File-based IPC works in the Windows sandbox where named pipes do not."""
    initialize_worker()
    with path.with_suffix('.jsonl').open('w',encoding='utf8') as stream:
        for task,payload in json.loads(path.read_text(encoding='utf8')):
            result = evaluate_task(payload)
            stream.write(json.dumps(dict(task=task,row=result),default=json_default)+'\n')
            stream.flush()


def file_workers(pending, output, workers, deadline):
    folder=output/'evaluation_workers'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    processes=[]
    readers=[]
    try:
        for index in range(min(workers,len(pending))):
            path=folder/f'worker_{index}.json'
            path.write_text(json.dumps(pending[index::workers],default=json_default),encoding='utf8')
            log=path.with_suffix('.log').open('w',encoding='utf8')
            process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker-input',str(path)],
                stdout=log,stderr=log,stdin=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            processes.append((process,log,path))
            readers.append(None)
        remaining=len(pending)
        while remaining:
            if time.monotonic()>deadline:
                raise TimeoutError('15-minute protocol boundary')
            for i,(process,_,path) in enumerate(processes):
                if readers[i] is None and path.with_suffix('.jsonl').exists():
                    readers[i]=path.with_suffix('.jsonl').open(encoding='utf8')
                if readers[i] is not None:
                    reader=readers[i]
                    while True:
                        position=reader.tell()
                        line=reader.readline()
                        if not line.endswith('\n'):
                            reader.seek(position)
                            break
                        record=json.loads(line)
                        task=tuple(record['task'][0]),record['task'][1]
                        remaining-=1
                        yield task,record['row']
                if process.poll() not in (None,0):
                    raise RuntimeError('Evaluation worker failed; see '+str(path.with_suffix('.log')))
            if all(p.poll() is not None for p,_,_ in processes) and remaining:
                # Drain a final flush once before declaring truncation.
                if all(reader is not None and reader.tell()==path.with_suffix('.jsonl').stat().st_size for reader,(_,_,path) in zip(readers,processes)):
                    raise RuntimeError('Evaluation worker output is incomplete')
            time.sleep(.05)
    finally:
        for process,log,_ in processes:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=10)
            log.close()
        for reader in readers:
            if reader is not None:reader.close()


def digest(array):
    return hashlib.sha256(np.asarray(array, dtype='<f8').tobytes(order='C')).hexdigest()


def validate_outputs(manifest, matlab_dir, input_dir):
    """Require a bijection, manifest metadata, binary input hashes and valid equations."""
    cells = manifest['cells']
    ids = [c['cell_id'] for c in cells]
    if len(ids) != len(set(ids)) or {p.stem for p in matlab_dir.glob('*.json')} != set(ids):
        raise ValueError('MATLAB outputs are not a bijection with manifest tasks')
    def validate_cell(cell):
        original = json.loads((matlab_dir/(cell['cell_id']+'.json')).read_text())
        if any(original.get(k) != cell[k] for k in IDENTITY_FIELDS):
            raise ValueError('MATLAB manifest identity mismatch: '+cell['cell_id'])
        for field in ('arm', 'q5w_interpolated_sha256', 'q5w_interpolation_points', 'q5w_interpolation_dt'):
            if field in cell and original.get(field) != cell[field]:
                raise ValueError('MATLAB interpolation identity mismatch: '+cell['cell_id'])
        data = loadmat(input_dir/cell['input_file'])
        if digest(data['tobs'].ravel()) != cell['time_sha256'] or digest(data['xobs']) != cell['state_sha256']:
            raise ValueError('binary input hash mismatch: '+cell['cell_id'])
        equations = original['equations']
        if len(equations) != data['xobs'].shape[1]:
            raise ValueError('equation count mismatch')
        for eq in equations:
            coef = np.asarray(eq['coefficients_original_scale'], float)
            if coef.shape != (len(cell['column_names']),) or not np.all(np.isfinite(coef)):
                raise ValueError('invalid MATLAB coefficient vector')
            index = eq['lambda_grid_index']
            if (eq['lambda_grid_index_base'] != 0 or not isinstance(index, int) or not 0 <= index < 100
                    or not np.isclose(eq['lambda_hat'], np.logspace(-4, 0, 100)[index], rtol=1e-14, atol=0)
                    or eq['support_indices'] != np.flatnonzero(coef).tolist()):
                raise ValueError('invalid MATLAB equation metadata')
        return cell['cell_id'], original
    # Files are independent; overlap filesystem latency without fitting in parallel.
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(pool.map(validate_cell, cells))


def evaluation_fields(columns):
    return [c for c in columns if c.startswith(('reconstruction_', 'generalization_', 'active_terms_', 'sindy_structure_'))
            or c in ('fit_status', 'fit_error', 'true_terms', 'n_library_terms', 'n_target_regressions')]


def differences(actual, expected, fields):
    """Name every unequal evaluation field, including JSON per-dimension R2."""
    result = []
    for field in fields:
        a, b = actual[field], expected[field]
        # pandas reads an empty CSV field as NaN; this is serialization identity.
        empty_a = a is None or a == '' or (isinstance(a,(float,np.floating)) and math.isnan(a))
        empty_b = b is None or b == '' or (isinstance(b,(float,np.floating)) and math.isnan(b))
        if empty_a and empty_b:
            continue
        if field.endswith('_r2_by_dim'):
            a, b = json.loads(a), json.loads(b)
            same = len(a) == len(b) and all(x == y or (math.isnan(x) and math.isnan(y)) for x, y in zip(a, b))
            delta = max((abs(x-y) for x, y in zip(a, b) if math.isfinite(x) and math.isfinite(y)), default=0.)
        else:
            same = a == b or (isinstance(a, (float, np.floating)) and isinstance(b, (float, np.floating)) and math.isnan(a) and math.isnan(b))
            delta = abs(float(a)-float(b)) if isinstance(a, (float, np.floating)) and isinstance(b, (float, np.floating)) and math.isfinite(a) and math.isfinite(b) else None
        if not same:
            result.append(dict(field=field, actual=a, port=b, absolute_delta=delta))
    return result


def make_row(original, export_row, system, support, t, x, clean_t, clean, template_columns):
    coef = np.asarray([e['coefficients_original_scale'] for e in original['equations']])
    result = runner.evaluate(runner.StoredModel(coef, original['column_names']), system, support,
                             export_row, t, x, clean_t, clean)
    arm = original.get('arm', 'W1')
    config = arm+':'+original['library']
    result.update(method=arm, library_id=original['library'], method_config_id=config, stlsq_threshold='',
                  source_shard='q5w_matlab_original', weak_seed='',
                  weak_sindy_source_note='Original MATLAB WSINDy; reference commit 72d8d6e',
                  q5w_configuration=config, q5w_equations=json.dumps(original['equations'], sort_keys=True),
                  q5w_coefficient_source=SOURCE,
                  q5w_input_time_sha256=original['time_sha256'], q5w_input_state_sha256=original['state_sha256'],
                  q5w_matlab_cell_id=original['cell_id'],
                  q5w_cost_note='MATLAB cost counts and fit timing unavailable; left empty',
                  q5w_elapsed_s_context='', **{field: '' for field in COST_FIELDS})
    for field in ('q5w_interpolation_points', 'q5w_interpolation_dt', 'q5w_interpolated_sha256'):
        if field in original:
            result[field] = original[field]
    return {field: result.get(field, '') for field in dict.fromkeys([*template_columns, *result])}


def run(interpolated=False, limit=None, output=None, max_seconds=840, workers=4, controls_only=False):
    started = time.monotonic()
    base = runner.OUTPUT
    suffix = '/w1_interp' if interpolated else ''
    arm = 'W1-interp' if interpolated else 'W1'
    input_dir, matlab_dir = base/('matlab_inputs'+suffix), base/('matlab_outputs'+suffix)
    output = output or base/('w1_interp_full_matlab' if interpolated else 'full_matlab')
    output.mkdir(parents=True, exist_ok=True)
    (output/'controls.json').write_text(json.dumps(dict(complete=False,state='checking')),encoding='utf8')
    manifest = json.loads((input_dir/'manifest.json').read_text())
    originals = validate_outputs(manifest, matlab_dir, input_dir)
    print(json.dumps(dict(validated_manifest_tasks=len(originals))), flush=True)
    port_path = base/('w1_interp_full/details.csv' if interpolated else 'full/details.csv')
    port = pd.read_csv(port_path, float_precision='round_trip', low_memory=False)
    port = port[port.q5w_configuration.str.startswith(arm+':') & (port.subsample_rho == (.5 if interpolated else 0))]
    ports = {(runner.key(r), r.library_id): r for _, r in port.iterrows()}
    if len(ports) != len(port):
        raise ValueError('duplicate port task')
    verdicts = {v['cell']: v for v in json.loads((base/('matlab_identity'+suffix)/'verdicts.json').read_text())}
    cells = [c for c in manifest['cells'] if 'seed' not in c['cell_key']]
    if len(cells)!=len(ports) or {(runner.key(c['cell_key']), c['library']) for c in cells} != set(ports):
        raise ValueError('port task coverage differs')
    index = runner.baseline.read_export_index(runner.EXPORT/'index.csv').set_index(runner.KEYS, drop=False)
    references = runner.reference_rows().rename(columns={'source_initial_condition_set':'initial_condition_set'}).set_index(runner.KEYS)
    path = output/'details.csv'
    done = {}
    if path.exists():
        previous = pd.read_csv(path, float_precision='round_trip', low_memory=False)
        done = {(runner.key(r), r.library_id): r for _, r in previous.iterrows()}
        if len(done) != len(previous) or not set(done) <= set(ports) or set(previous.q5w_coefficient_source) != {SOURCE}:
            raise ValueError('invalid resumed rows')
    selected = cells[:limit] if limit else cells
    if controls_only:
        selected=[c for c in selected if (runner.key(c['cell_key']),c['library']) in done]
    pending = []
    for cell in selected:
        task = runner.key(cell['cell_key']), cell['library']
        row = index.loc[task[0]]
        if runner.baseline.data_sha(row) != references.loc[task[0]].observed_data_sha256 or runner.baseline.data_sha(row) != ports[task].observed_data_sha256:
            raise ValueError('WP-N47/port observed hash mismatch')
        if task in done:
            old = done[task]
            if (json.loads(old['q5w_equations']) != originals[cell['cell_id']]['equations']
                    or old['q5w_input_time_sha256'] != cell['time_sha256']
                    or old['q5w_input_state_sha256'] != cell['state_sha256']
                    or old['observed_data_sha256'] != runner.baseline.data_sha(row)):
                raise ValueError('resumed row coefficient/input provenance differs')
            continue
        if time.monotonic()-started > max_seconds:
            raise TimeoutError('15-minute protocol boundary: resume with the same command')
        pending.append((task, (originals[cell['cell_id']], row.to_dict(), list(port.columns))))
    if pending:
        for task,result in file_workers(pending,output,workers,started+max_seconds):
            runner.baseline.append_csv_rows(path,[result])
            done[task] = result
            if len(done)%100 == 0:
                print(json.dumps(dict(completed_tasks=len(done),expected_tasks=len(selected))),flush=True)
            if time.monotonic()-started > max_seconds:
                raise TimeoutError('15-minute protocol boundary')
    exceptions, passed, max_delta = [], 0, 0.
    for cell in selected:
        task = runner.key(cell['cell_key']), cell['library']
        recomputed = compare_equations(json.loads(ports[task].q5w_equations), originals[cell['cell_id']]['equations'])
        if recomputed['passed'] != verdicts[cell['cell_id']]['passed']:
            raise ValueError('saved identity verdict differs')
        if not recomputed['passed']:
            continue
        passed += 1
        diffs = differences(done[task], ports[task], evaluation_fields(port.columns))
        if diffs:
            exact_coef = json.loads(ports[task].q5w_equations)
            coef_delta = max(np.max(np.abs(np.asarray(a['coefficients_original_scale'])-np.asarray(b['coefficients_original_scale'])))
                             for a,b in zip(exact_coef, originals[cell['cell_id']]['equations']))
            for diff in diffs:
                if diff['field'].startswith('sindy_structure_') and done[task]['active_terms_pruned']==ports[task].active_terms_pruned:
                    diff['reason']='Identical support sets; floating-point metric representation/arithmetic discrepancy'
                elif '_r2_' in diff['field']:
                    diff['reason']=('Nonidentical coefficients within the identity tolerance; integration may amplify the perturbation'
                                    if coef_delta else 'Identical coefficients; floating-point execution/serialization discrepancy remains unlocalized')
            exceptions.append(dict(cell=cell['cell_id'], coefficient_max_absolute_delta=float(coef_delta),
                                   reason='coefficients agree within identity tolerance, not bit-identically' if coef_delta else 'identical coefficients; evaluation environment/numerical execution difference', differences=diffs))
            max_delta = max(max_delta, *(d['absolute_delta'] or 0. for d in diffs if '_r2_' in d['field']), 0.)
    controls = dict(manifest_tasks=len(manifest['cells']), manifest_bijection_and_hashes=True,
                    expected_c6_rows=len(cells), completed_c6_rows=len(done), complete=len(done)==len(cells) and len(selected)==len(cells),
                    passing_identity_tasks_checked=passed, evaluation_exception_tasks=len(exceptions),
                    maximum_r2_absolute_delta=max_delta, exceptions=exceptions,
                    unavailable_cost_fields=list(COST_FIELDS), coefficient_source=SOURCE)
    (output/'controls.json').write_text(json.dumps(controls, indent=2, default=lambda v: v.item() if hasattr(v,'item') else str(v)), encoding='utf8')
    print(json.dumps({k:v for k,v in controls.items() if k!='exceptions'}), flush=True)
    return controls


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--interpolated', action='store_true')
    p.add_argument('--limit', type=int)
    p.add_argument('--output-dir', type=Path)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--controls-only',action='store_true',help='Validate persisted rows without evaluating missing tasks')
    p.add_argument('--worker-input',type=Path,help=argparse.SUPPRESS)
    a = p.parse_args()
    if a.workers < 1 or (a.limit is not None and a.limit < 1):
        p.error('--limit and --workers must be positive')
    with threadpool_limits(limits=1):
        if a.worker_input:
            worker_file(a.worker_input)
        else:
            run(a.interpolated, a.limit, a.output_dir,workers=a.workers,controls_only=a.controls_only)
