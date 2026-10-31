"""Interpolation checks derived from real C-6 index rows and recorded Q5-W rows."""
import copy
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scipy.io import loadmat
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'analysis/scripts/aggregate'))
import run_sideproject_q5w_wsindy as runner
import compare_sideproject_q5w_matlab as comparison
from export_sideproject_q5w_matlab import write_cell, array_hash


def real_row(rho):
    index = runner.baseline.read_export_index(runner.EXPORT/'index.csv')
    return index[(index.subsample_rho == rho) & (index.dimension == 2)].iloc[0]


def test_linear_interpolation_and_export():
    row = real_row(.5)
    t, x = runner.baseline.read_index_cell(runner.EXPORT, row)
    u, y = runner.interpolate_uniform(t, x)
    assert len(u) == len(t) and u[0] == t[0] and u[-1] == t[-1]
    assert np.allclose(np.diff(u), (t[-1]-t[0])/(len(t)-1), rtol=1e-10, atol=1e-14)
    for j in range(x.shape[1]):
        np.testing.assert_array_equal(y[:, j], np.interp(u, t, x[:, j]))
    assert not np.shares_memory(y, x)
    facts = runner.interpolation_facts(u, y)
    changed = y.copy()
    changed[1, 0] += 1
    assert facts != runner.interpolation_facts(u, changed)
    folder = runner.OUTPUT/'test_interp_export'
    entry = write_cell(folder, 'fixture', dict(zip(runner.KEYS, runner.key(row))), u, y,
                       'L-Q5', runner.library(x.shape[1], 'L-Q5'))
    assert entry['time_sha256'] == array_hash(u)
    assert entry['state_sha256'] == array_hash(y)
    saved = loadmat(folder/'fixture.mat')
    np.testing.assert_array_equal(saved['xobs'], y)


def test_uniform_identity_bit_exact():
    row = real_row(0)
    t, x = runner.baseline.read_index_cell(runner.EXPORT, row)
    u, y = runner.interpolate_uniform(t, x)
    assert u is t and y is x
    with threadpool_limits(limits=1):
        for lib in ('L-C6', 'L-Q5'):
            a, ma = runner.fit_arm(t, x, runner.library(x.shape[1], lib), 'W1', row)
            b, mb = runner.fit_arm(t, x, runner.library(x.shape[1], lib), 'W1-interp', row)
            assert a.tobytes() == b.tobytes()
            assert ma == mb


@pytest.mark.parametrize('times,states', [([0, 0], [[1], [2]]), ([1, 0], [[1], [2]]),
                                         ([0, 1], [[1], [np.nan]]), ([0, 1], [[1]]),
                                         ([0], [[1]])])
def test_invalid_interpolation_inputs(times, states):
    with pytest.raises(ValueError, match='interpolation requires'):
        runner.interpolate_uniform(times, states)


def test_default_six_rows_match_preserved_smoke():
    assert runner.CONFIGS == tuple(f'{a}:{l}' for a in ('W1', 'W1-cap', 'W2') for l in ('L-C6', 'L-Q5'))
    preserved = pd.read_csv(runner.OUTPUT/'smoke/details.csv', float_precision='round_trip').fillna('')
    first = preserved.iloc[0]
    index = runner.baseline.read_export_index(runner.EXPORT/'index.csv')
    row = index[[runner.key(r) == runner.key(first) for _, r in index.iterrows()]]
    folder = runner.OUTPUT/'test_interp_default_identity'
    path = folder/'details.csv'
    if path.exists():
        path.unlink()
    with threadpool_limits(limits=1):
        runner.run(row, output=folder, technical_only=True)
    actual = pd.read_csv(path, float_precision='round_trip').fillna('')
    old = preserved[[runner.key(r) == runner.key(first) for _, r in preserved.iterrows()]].reset_index(drop=True)
    timing = [c for c in old if c.endswith('_elapsed_s_context')]
    pd.testing.assert_frame_equal(actual.drop(columns=timing), old.drop(columns=timing), check_exact=True)


def test_interp_comparison_cli(monkeypatch, capsys):
    # Equation schema comes from an existing real W1 row; only arm/input facts are adapted.
    source = pd.read_csv(runner.OUTPUT/'smoke/details.csv', float_precision='round_trip').iloc[0]
    row = source.to_dict()
    row['q5w_configuration'] = 'W1-interp:L-C6'
    row['q5w_interpolated_sha256'] = 'fixture_hash'
    folder = runner.OUTPUT/'test_interp_comparison'
    for sub in ('matlab_inputs/w1_interp', 'matlab_outputs/w1_interp', 'acceptance'):
        (folder/sub).mkdir(parents=True, exist_ok=True)
    cell = dict(cell_id='interp_fixture', cell_key=dict(zip(runner.KEYS, runner.key(row))),
                library='L-C6', arm='W1-interp', time_sha256='fixture_time', state_sha256='fixture_state',
                column_names=[c.name for c in runner.library(1)], q5w_interpolated_sha256='fixture_hash')
    (folder/'matlab_inputs/w1_interp/manifest.json').write_text(json.dumps(dict(cells=[cell])))
    (folder/'acceptance/summary.json').write_text(json.dumps(dict(matlab_identity_passed=None)))
    pd.DataFrame([row]).to_csv(folder/'port.csv', index=False)
    original = dict(cell, equations=json.loads(row['q5w_equations']))
    target = folder/'matlab_outputs/w1_interp/interp_fixture.json'
    target.write_text(json.dumps(original))
    monkeypatch.setattr(comparison, 'OUTPUT', folder)
    monkeypatch.setattr(sys, 'argv', ['compare', '--interpolated', '--port-rows', str(folder/'port.csv')])
    comparison.main()
    assert json.loads(capsys.readouterr().out)['passed'] == 1
    original['equations'][0]['lambda_grid_index'] += 1
    target.write_text(json.dumps(original))
    comparison.main()
    assert json.loads(capsys.readouterr().out)['failing_cells'][0]['reason'] == 'lambda_grid_index'
    row['q5w_interpolated_sha256'] = 'wrong_hash'
    pd.DataFrame([row]).to_csv(folder/'port.csv', index=False)
    comparison.main()
    assert json.loads(capsys.readouterr().out)['failing_cells'][0]['reason'] == 'port_input_identity'
    acceptance = json.loads((folder/'acceptance/summary.json').read_text())
    assert acceptance['matlab_identity_passed'] is None
    assert acceptance['matlab_interp_identity_passed'] is False


def test_runner_evaluation_receives_original_observations(monkeypatch):
    row = real_row(.5)
    t, x = runner.baseline.read_index_cell(runner.EXPORT, row)
    reference = pd.DataFrame([dict(zip(runner.KEYS, runner.key(row)),
                                  observed_data_sha256=runner.baseline.data_sha(row))])
    monkeypatch.setattr(runner, 'reference_rows', lambda: reference)
    monkeypatch.setattr(runner, 'context', lambda: ({int(row.system_id): {}},
                        pd.DataFrame([{}], index=[int(row.system_id)])))
    monkeypatch.setattr(runner.baseline, 'read_index_cell', lambda *a: (t, x))
    monkeypatch.setattr(runner.baseline, 'integrate_truth', lambda *a: (np.ones((512, x.shape[1])), None))
    monkeypatch.setattr(runner, 'fit_arm', lambda *a: (np.zeros((x.shape[1], len(a[2]))),
                        [dict(selected=True, least_squares_solves=0)]))
    seen = []
    def evaluator(model, system, support, observed_row, observed_t, observed_x, clean_t, clean):
        assert observed_t is t and observed_x is x
        seen.append(True)
        return dict(fit_status='success')
    monkeypatch.setattr(runner, 'evaluate', evaluator)
    monkeypatch.setattr(runner.baseline, 'append_csv_rows', lambda *a: None)
    runner.run(pd.DataFrame([row]), runner.INTERP_CONFIGS, runner.OUTPUT/'test_interp_evaluation')
    assert len(seen) == 2


def test_cells_cli_selects_irregular_rows(monkeypatch):
    row = real_row(.5)
    folder = runner.OUTPUT/'test_interp_cli'
    folder.mkdir(parents=True, exist_ok=True)
    cells = folder/'cells.csv'
    pd.DataFrame([row])[runner.KEYS].to_csv(cells, index=False)
    calls = []
    monkeypatch.setattr(runner, 'run', lambda rows, configs, output: calls.append((rows, configs)))
    monkeypatch.setattr(sys, 'argv', ['run', '--cells', str(cells), '--configurations', ','.join(runner.INTERP_CONFIGS)])
    runner.main()
    assert len(calls[0][0]) == 1 and runner.key(calls[0][0].iloc[0]) == runner.key(row)
    assert calls[0][1] == runner.INTERP_CONFIGS


def test_interpolated_export_manifest(monkeypatch, capsys):
    import export_sideproject_q5w_matlab as exporter
    row = real_row(.5)
    folder = runner.OUTPUT/'test_interp_manifest'
    monkeypatch.setattr(exporter, 'OUTPUT', folder)
    monkeypatch.setattr(exporter.baseline, 'read_export_index', lambda *a: pd.DataFrame([row]))
    exporter.export_interpolated()
    assert json.loads(capsys.readouterr().out)['tasks'] == 2
    manifest = json.loads((folder/'matlab_inputs/w1_interp/manifest.json').read_text())
    assert manifest['arm'] == 'W1-interp' and manifest['c6_interpolated_cells'] == 1
    t, x = runner.interpolate_uniform(*runner.baseline.read_index_cell(runner.EXPORT, row))
    for entry in manifest['cells']:
        assert entry['arm'] == 'W1-interp'
        assert entry['q5w_interpolated_sha256'] == runner.interpolation_facts(t, x)['q5w_interpolated_sha256']
        saved = loadmat(folder/'matlab_inputs/w1_interp'/entry['input_file'])
        np.testing.assert_array_equal(saved['tobs'][:, 0], t)
        np.testing.assert_array_equal(saved['xobs'], x)
