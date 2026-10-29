"""Focused Q5-W checks, with schema fixtures read from actual exported rows."""
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'analysis/scripts/aggregate'))
from run_sideproject_q5w_wsindy import (
    EXPORT, baseline, library, key, CFG, evaluate, StoredModel, fit_arm,
)
from accept_sideproject_q5w_wsindy import mapping
from scripts.aggregate.wsindy_reference import Column, scales, select_model, weak_design, smooth


def test_mapping_from_existing_libraries():
    assert all(r['passed'] for r in mapping())


def test_original_scale_and_loss_coordinates():
    # Known algebraic system, independent of the trajectory pipeline.
    original = np.array([[1., 0.], [0., 1.], [1., 2.], [3., 1.]])
    scaling = np.array([.01, .001])
    truth = np.array([2., -3.])
    actual, info = select_model(original*scaling, original@truth, scaling, lambdas=np.array([1e-4, 1e-3]))
    np.testing.assert_allclose(actual, truth, rtol=1e-12)
    assert info['lambda_hat'] == 1e-4
    np.testing.assert_allclose(info['loss_curve'], [.4, .4], atol=1e-12)


def test_cap_unselected_and_inclusive_bounds():
    coefficient, info = select_model(np.eye(2), np.ones(2), np.ones(2), cap=1, lambdas=np.array([1e-4]))
    assert not info['selected'] and info['lambda_hat'] is None
    assert np.array_equal(coefficient, [0., 0.])
    # Bounds are inclusive: coefficients equal to 1 survive lambda=1.
    coefficient, info = select_model(np.eye(1), np.ones(1), np.ones(1), lambdas=np.array([1.]))
    assert np.array_equal(coefficient, [1.])


def test_upper_bound_removes_large_term():
    coefficient, _ = select_model(np.eye(2), np.array([100., .001]), np.ones(2), lambdas=np.array([.1]))
    assert np.array_equal(coefficient, [0., 0.])


def test_zero_signal_and_zero_column_are_finite():
    coefficient, info = select_model(np.zeros((5, 2)), np.zeros(5), np.ones(2))
    assert np.array_equal(coefficient, [0., 0.])
    assert all(np.isfinite(info['loss_curve']))


def test_irregular_quadrature_and_sign():
    t = np.linspace(0, 5, 501)
    t[1:-1] += .001*np.sin(t[1:-1])
    x = (2+t)[:, None]
    columns = [Column('1', lambda x: np.ones(len(x)), (0,))]
    g, b, scaling, metadata = weak_design(t, x, columns)
    np.testing.assert_allclose(b[0], g[0][:, 0], rtol=.003, atol=1e-5)
    assert metadata[0]['n_test_functions'] == len(b[0])
    assert metadata[0]['smoothing_window'] >= 1
    assert metadata[0]['smoothing_window'] % 2 == 1
    # On a uniform linear signal the automatic decision needs no smoothing.
    uniform = np.linspace(0, 5, 501)
    _, window = smooth(uniform, 2+uniform)
    assert window == 1


def test_real_export_fixture_hash_and_seed():
    index = baseline.read_export_index(EXPORT/'index.csv')
    # A real authorized smoke row, unchanged field inventory.
    row = index[(index.system_id == 4) & (index.initial_condition_set == 1)
                & (index.noise_sigma == 0) & (index.subsample_rho == 0)].iloc[0].copy()
    t, x = baseline.read_index_cell(EXPORT, row)
    assert x.shape == (len(t), int(row.dimension))
    assert set(json.loads(baseline.data_sha(row))) == {'time_sha256', 'state_sha256'}
    assert baseline.weak_sindy_seed(row, CFG.library_id) == baseline.weak_sindy_seed(row.copy(), CFG.library_id)
    # Details rows use the existing WP-N47 source-IC alias, including on resume.
    details_row = row.rename({'initial_condition_set': 'source_initial_condition_set'})
    assert key(details_row) == key(row)
    damaged = row.copy()
    damaged['state_sha256'] = '0'*64  # The only fixture alteration.
    with pytest.raises(ValueError, match='hash'):
        baseline.read_index_cell(EXPORT, damaged)


def test_evaluation_uses_existing_path_without_refit(monkeypatch):
    calls = []
    def existing(*args, **kwargs):
        calls.append((args, kwargs))
        return {'sentinel': 17}
    monkeypatch.setattr(baseline, 'run_one_model', existing)
    result = evaluate(StoredModel(np.array([[1.]]), ['1']), {}, {}, {}, None, None, None, None)
    assert result == {'sentinel': 17}
    assert calls[0][1]['integrator'] == 'dop853'


def test_w2_seeded_design_matches_existing_helper_on_synthetic_signal(monkeypatch):
    index = baseline.read_export_index(EXPORT/'index.csv')
    row = index[(index.system_id == 4) & (index.noise_sigma == 0) & (index.subsample_rho == 0)].iloc[0]
    t = np.linspace(0, 10, 512)
    # Deliberately synthetic signal, not a C-6 configuration run.
    x = np.column_stack([np.sin(t), np.cos(2*t)])
    expected_model = baseline.fit_weak_sindy(x, t, ['x0', 'x1'], CFG, baseline.weak_sindy_seed(row, CFG.library_id))
    expected_g = np.asarray(expected_model.feature_library.transform(x))
    expected_b = expected_model.feature_library.convert_u_dot_integral(x)
    import scripts.aggregate.run_sideproject_q5w_wsindy as runner
    calls = []
    def capture(g, b, scaling):
        calls.append((g/scaling, b))
        return np.zeros(g.shape[1]), {'least_squares_solves': 0}
    monkeypatch.setattr(runner, 'select_model', capture)
    for library_id in ('L-C6', 'L-Q5'):
        calls.clear()
        columns = library(2, library_id)
        runner.fit_arm(t, x, columns, 'W2', row)
        indices = [expected_model.get_feature_names().index(c.name) for c in columns]
        for eq, (g, b) in enumerate(calls):
            np.testing.assert_allclose(g, expected_g[:, indices], rtol=1e-15, atol=1e-15)
            assert np.array_equal(b, expected_b[:, eq])
