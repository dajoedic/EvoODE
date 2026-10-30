"""Focused checks using the preserved real Lorenz record as schema foundation."""
import copy
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'analysis/scripts/aggregate'))
from compare_sideproject_q5w_matlab import compare_equations, lorenz_equations
from export_sideproject_q5w_matlab import write_cell, expressibility
from run_sideproject_q5w_wsindy import OUTPUT, library
from scripts.aggregate.wsindy_reference import select_model
from accept_sideproject_q5w_wsindy import pre_smoke_gate


def test_revised_gate_is_independent_of_noisy_lorenz_and_matlab():
    summary = dict(lorenz=dict(clean_passed=True, noisy_support_hits=0),
                   mapping=[dict(passed=True)], identity=dict(passed=True),
                   matlab_identity_passed=False)
    assert pre_smoke_gate(summary)
    for field in ('lorenz', 'mapping', 'identity'):
        damaged = copy.deepcopy(summary)
        if field == 'mapping':
            damaged[field][0]['passed'] = False
        else:
            damaged[field]['clean_passed' if field == 'lorenz' else 'passed'] = False
        assert not pre_smoke_gate(damaged)


def real_equations():
    record = json.loads((OUTPUT/'acceptance/lorenz.jsonl').read_text().splitlines()[0])
    return lorenz_equations(record)


def test_identical_real_record():
    equations = real_equations()
    assert compare_equations(equations, copy.deepcopy(equations))['passed']


@pytest.mark.parametrize('change,reason', [('coefficient','coefficients'), ('support','support'), ('index','lambda_grid_index')])
def test_deliberate_perturbations(change, reason):
    a = real_equations()
    b = copy.deepcopy(a)
    active = np.flatnonzero(b[1]['coefficients_original_scale'])[0]
    if change == 'coefficient':
        b[1]['coefficients_original_scale'][active] *= 1.01
    elif change == 'support':
        b[1]['coefficients_original_scale'][active] = 0
    else:
        b[1]['lambda_grid_index'] += 1
    verdict = compare_equations(a, b)
    assert verdict['reason'] == reason and verdict['first_differing_equation'] == 1


def test_tolerance_and_zero_equation():
    a = real_equations()
    b = copy.deepcopy(a)
    active = np.flatnonzero(b[0]['coefficients_original_scale'])[0]
    b[0]['coefficients_original_scale'][active] *= 1+1e-8
    assert compare_equations(a, b)['passed']
    empty = [dict(coefficients_original_scale=[0.,0.], lambda_grid_index=0)]
    assert compare_equations(empty, empty)['passed']


def test_output_metadata_is_original_scale():
    coef, info = select_model(np.eye(2), np.array([2., -3.]), np.ones(2))
    assert info['lambda_grid_index'] == 0
    assert info['support_indices'] == [0, 1]
    assert info['coefficients_original_scale'] == coef.tolist()


def test_binary_export_roundtrip():
    # Exact real export arrays, not a plan-derived synthetic schema.
    from run_sideproject_q5w_wsindy import baseline, EXPORT, smoke_rows, key, KEYS
    row = smoke_rows().iloc[0]
    t, x = baseline.read_index_cell(EXPORT, row)
    manifest = write_cell(OUTPUT/'test_matlab_export', 'fixture', dict(zip(KEYS,key(row))), t,x,'L-C6',library(x.shape[1]))
    assert manifest['time_sha256'] == row.time_sha256
    assert manifest['state_sha256'] == row.state_sha256


def test_comparison_cli_identity_and_failure(monkeypatch, capsys):
    import compare_sideproject_q5w_matlab as comparison
    folder = OUTPUT/'test_matlab_comparison'
    for sub in ('matlab_inputs', 'acceptance', 'matlab_outputs'):
        (folder/sub).mkdir(parents=True, exist_ok=True)
    record = json.loads((OUTPUT/'acceptance/lorenz.jsonl').read_text().splitlines()[0])
    cell = dict(cell_id='lorenz_-1', cell_key=dict(seed=-1), library='Lorenz-poly5',
                time_sha256='fixture_time', state_sha256='fixture_state',
                column_names=[c.name for c in library(3,degree=5,trig=False)])
    (folder/'matlab_inputs/manifest.json').write_text(json.dumps(dict(cells=[cell])))
    (folder/'acceptance/lorenz.jsonl').write_text(json.dumps(record)+'\n')
    (folder/'acceptance/summary.json').write_text(json.dumps(dict(matlab_identity_passed=None)))
    original = dict(cell, equations=lorenz_equations(record))
    target = folder/'matlab_outputs/lorenz_-1.json'
    target.write_text(json.dumps(original))
    monkeypatch.setattr(comparison, 'OUTPUT', folder)
    monkeypatch.setattr(sys, 'argv', ['compare'])
    comparison.main()
    assert json.loads(capsys.readouterr().out)['passed'] == 1
    original['equations'][0]['lambda_grid_index'] += 1
    target.write_text(json.dumps(original))
    comparison.main()
    summary = json.loads(capsys.readouterr().out)
    assert summary['passed'] == 0
    assert summary['failing_cells'][0]['first_differing_equation'] == 0
    assert not json.loads((folder/'acceptance/summary.json').read_text())['matlab_identity_passed']


@pytest.mark.parametrize('dim', range(1,5))
def test_explicit_tags_express_both_libraries(dim):
    x = np.random.default_rng(112).normal(size=(31,dim))
    for lib in ('L-C6','L-Q5'):
        assert expressibility(library(dim,lib),x)['expressible']
