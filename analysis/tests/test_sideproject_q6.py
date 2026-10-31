"""Q6 mathematical controls and path fixtures derived from actual Q5 cells."""
import copy
import json
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts/aggregate'))
import build_sideproject_q6_paths as q6
from build_sideproject_q4_paths import growth_path
from exploratory.term_relevance.term_relevance import evaluate_basis


@pytest.fixture(scope='module')
def real_cells():
    payload = json.loads(q6.Q5.read_text(encoding='utf8'))
    return q6.select_smoke(payload['cells'])


def test_estimator_cubic_and_actual_time_edges():
    t = np.linspace(0, 1, 51)**1.3
    x = np.column_stack((1+t+t**3, 2-t**2))
    assert np.max(q6.estimate_noise_variance(t, x)) < 1e-25
    with pytest.raises(ValueError):
        q6.estimate_noise_variance(t[:8], x[:8])
    with pytest.raises(ValueError):
        q6.estimate_noise_variance(t[::-1], x[::-1])


def test_estimator_known_heteroscedastic_noise():
    rng = np.random.default_rng(20261031)
    t = np.linspace(0, 1, 101)**1.1
    clean = np.column_stack((1+t+t**3, 2-t**2))
    sd = np.column_stack((.1+.05*t, .2+.1*t))
    estimates = [q6.estimate_noise_variance(t, clean+rng.normal(size=clean.shape)*sd) for _ in range(100)]
    mean = np.mean(estimates, axis=0)
    # Ensemble calibration, not a quality result on the Q5 observations.
    np.testing.assert_allclose(mean.mean(axis=0), (sd**2).mean(axis=0), rtol=.15)
    assert np.all(mean[-21:].mean(axis=0) > mean[:21].mean(axis=0))


@pytest.mark.parametrize('dim', [1, 2, 3, 4])
def test_every_basis_derivative_finite_difference(dim):
    terms = q6.phasec_basis(dim)
    x = np.random.default_rng(dim).normal(size=(9, dim))
    x[0] = 0  # derivative formula must also work at zero
    jac = q6.basis_jacobian(x, terms)
    for j in range(dim):
        step = np.zeros_like(x)
        step[:, j] = 1e-6
        fd = (evaluate_basis(x+step, terms)-evaluate_basis(x-step, terms))/(2e-6)
        np.testing.assert_allclose(jac[:, :, j], fd, atol=1e-8, rtol=1e-7)


@pytest.mark.parametrize('secondary', [False, True])
def test_floor_monte_carlo_and_dense_covariance(secondary):
    rng = np.random.default_rng(20261031)
    t = np.linspace(0, 1, 21)**1.2
    x = np.column_stack((1+t, 2-t**2))
    terms = q6.phasec_basis(2)
    design, target, _ = q6.build_design(t, x, 0, 'weak', terms)
    d, w = q6.weak_noise_operators(t)
    np.testing.assert_allclose(w @ evaluate_basis(x, terms), design, atol=1e-15)
    np.testing.assert_allclose(d @ x[:, 0], target, atol=1e-15)
    variance = np.column_stack((.01+.01*t, .02+.01*t))
    support = [0, 1, 2]
    if secondary:
        jac = q6.basis_jacobian(x, terms)
        coef, _ = q6.weak_coefficients(design, target, support)
        operator = q6.secondary_noise_operator(d, w, variance, jac, coef, support, 0)
        floor = q6.secondary_floor(design, target, support, d, w, variance, jac, 0)
        # Independently form the linearised endpoint-minus-integral operator.
        gradient = np.einsum('nkd,k->nd', jac[:, support], coef)
        direct = np.hstack([(d.toarray() if j == 0 else np.zeros(d.shape)) - w.toarray()*gradient[:, j]
                            for j in range(2)]) * np.sqrt(variance.T.reshape(-1))[None, :]
        np.testing.assert_allclose(operator.toarray(), direct, atol=1e-15)
    else:
        operator = d.multiply(np.sqrt(variance[:, 0])[None, :]).tocsr()
        floor = q6.primary_floor(design, support, d, variance[:, 0])
    a = design[:, support]
    projector = a @ np.linalg.pinv(a)
    covariance = (operator @ operator.T).toarray()
    assert np.count_nonzero(covariance-np.diag(np.diag(covariance))) > 0
    expected = np.trace((np.eye(len(target))-projector) @ covariance)
    assert floor == pytest.approx(expected, rel=1e-12)
    noise = operator @ rng.normal(size=(operator.shape[1], 4000))
    residual = noise-projector @ noise
    assert np.mean(np.sum(residual**2, axis=0)) == pytest.approx(floor, rel=.05)


def test_rank_deficient_projector():
    from scipy import sparse
    design = np.column_stack((np.ones(9), np.ones(9), np.zeros(9)))
    assert q6.projected_noise_floor(design, [0, 1, 2], sparse.eye(9, format='csr')) == pytest.approx(8.)
    assert q6.projected_noise_floor(design, [2], sparse.eye(9, format='csr')) == pytest.approx(9.)


def test_reference_cap_bit_identity_real_q5(real_cells):
    # Real records preserve candidate fields, weak coefficients and signed zeros.
    for cell in real_cells:
        t, x = q6.read_index_cell(q6.EXPORT, q6.pd.Series(cell['export']))
        terms = q6.phasec_basis(cell['dim'])
        designs, targets = zip(*(q6.build_design(t, x, eq, 'weak', terms)[:2] for eq in range(cell['dim'])))
        expected, expected_log = growth_path(designs, targets)
        path, log, _ = q6.growth_path_with_end(designs, targets, cap=6)
        assert q6.canonical(path) == q6.canonical(expected)
        assert q6.canonical(log) == q6.canonical(expected_log)
        candidates = [q6.candidate(designs, targets, terms, p['support'], f"path_{p['step']:03d}",
                                  step=p['step'], origin=p['origin']) for p in path]
        assert q6.canonical(candidates) == q6.canonical(cell['candidates'])


def test_pluggable_floor_full_basis_and_zero():
    a, b = np.eye(9), np.ones(9)
    reference, _, ends = q6.growth_path_with_end([a], [b])
    assert len(reference[-1]['support'][0]) == 9
    stopped, _, ends = q6.growth_path_with_end([a], [b], lambda eq, fit, support: 9.)
    assert stopped == [] and ends[0]['end_reason'] == 'floor'
    stopped, _, ends = q6.growth_path_with_end([a], [b*0])
    assert stopped == [] and ends[0]['end_reason'] == 'sse'


def test_cycle_keeps_previous_state(monkeypatch):
    # A deliberately nonstationary fit emulates floating-point FoBa repetition.
    class CyclingFit:
        def __init__(self, a, b):
            self.p, self.b_norm2, self.expanded = 2, 1., False

        def sse(self, support):
            key = tuple(sorted(support))
            if key == (0, 1):
                self.expanded = True
                return .4
            return {():1., (0,):.41 if self.expanded else .5, (1,):.9}[key]

    monkeypatch.setattr(q6, 'WeakFit', CyclingFit)
    path, log, ends = q6.growth_path_with_end([np.eye(2)], [np.ones(2)])
    assert len(path) == len(log) == 1
    assert path[-1]['support'] == [[0]]
    assert ends[0]['end_reason'] == 'cycle'


@pytest.mark.parametrize('rule', q6.RULES)
def test_no_gain_ends_all_eligible_equations_and_preserves_stops(rule):
    # After the first column is selected, the zero column cannot reduce SSE.
    a, b = np.diag([1., 0.]), np.ones(2)
    floor = None if rule == 'reference' else lambda eq, fit, support: 2. if eq == 3 else 0.
    designs, targets = [a]*4, [b, b, b*0, b]
    path, log, ends = q6.growth_path_with_end(designs, targets, floor)
    assert len(path) == len(log) == (3 if rule == 'reference' else 2)
    assert path[-1]['support'] == ([[0], [0], [], [0]] if rule == 'reference' else [[0], [0], [], []])
    assert [end['end_reason'] for end in ends] == [
        'no_gain', 'no_gain', 'sse', 'no_gain' if rule == 'reference' else 'floor',
    ]
    assert all(end['path_length'] == len(path) for end in ends)
    with pytest.raises(ValueError, match='No positive gain before protocol stop'):
        q6.growth_path_with_end(designs, targets, floor, cap=6)
    with pytest.raises(ValueError):
        growth_path(designs, targets)


def test_smoke_selection(real_cells):
    assert len(real_cells) == len({c['cell_id'] for c in real_cells}) == 20
    for stratum in q6.STRATA:
        cells = [c for c in real_cells if c['stratum'] == stratum]
        assert len(cells) == 5
        assert {c['sigma'] > 0 for c in cells} == {False, True}
        assert {c['rho'] > 0 for c in cells} == {False, True}


def test_hash_failure_is_loud(monkeypatch):
    original = q6.sha256
    monkeypatch.setattr(q6, 'sha256', lambda p: 'corrupt' if Path(p).name == 'index.csv' else original(p))
    with pytest.raises(ValueError, match='Q5 input hash mismatch'):
        q6.run(q6.OUTPUT/'must_not_be_created', smoke=True)
    assert not (q6.OUTPUT/'must_not_be_created').exists()


def test_observed_hash_failure_real_record(real_cells):
    cell = copy.deepcopy(real_cells[0])
    cell['observed_data_sha256'] = 'corrupt'
    with pytest.raises(ValueError, match='Q5 observed hash mismatch'):
        q6.build_cell_job((cell, q6.EXPORT, False, None))


def test_cell_determinism_without_scientific_evaluation(real_cells):
    cell = next(c for c in real_cells if c['dim'] == 1 and c['sigma'] > 0)
    job = (cell, q6.EXPORT, False, None)
    first = q6.build_cell_job(job)
    second = q6.build_cell_job(job)
    assert q6.canonical(first) == q6.canonical(second)
    assert first[2] == []
    assert all('classification' not in row for row in first[1])
    assert first[3]['hash_control'] and first[3]['q5_identity_control']


def test_uncapped_reference_may_differ_from_q5(real_cells):
    # A capped joint path need not be a prefix of its uncapped version:
    # one equation can exceed six terms while another is still below six.
    cell = next(c for c in real_cells if c['cell_id'] == 'sys0024_ic1_s0.01_r0_n1')
    paths, equations, estimator, control = q6.build_cell_job((cell, q6.EXPORT, False, None))
    assert control['q5_identity_control']
    assert q6.canonical(paths['reference']['candidates'][:len(cell['candidates'])]) != q6.canonical(cell['candidates'])
    assert set(paths) == set(q6.RULES)
    assert all('classification' not in row for row in equations)
    assert estimator == []


def test_q5_identity_failure_real_record(real_cells):
    cell = copy.deepcopy(real_cells[0])
    cell['candidates'][0]['equations'][0]['coefficients'][0] += 1.
    with pytest.raises(ValueError, match='Q5 identity control failed'):
        q6.build_cell_job((cell, q6.EXPORT, False, None))


def test_historical_protocol_digest_is_exact(monkeypatch):
    payload = json.loads(q6.Q5.read_text(encoding='utf8'))
    expected = payload['input_sha256'][q6.Q5_PROTOCOL]
    assert q6.q5_input_digest(q6.Q5_PROTOCOL) == expected
    assert q6.sha256(q6.ROOT/q6.Q5_PROTOCOL) != expected
    original = q6.q5_input_digest
    monkeypatch.setattr(q6, 'q5_input_digest', lambda name: 'corrupt' if name == q6.Q5_PROTOCOL else original(name))
    with pytest.raises(ValueError, match='Q5 input hash mismatch'):
        q6.run(q6.OUTPUT/'must_not_be_created', smoke=True)
    assert not (q6.OUTPUT/'must_not_be_created').exists()


@pytest.mark.parametrize('workers', [1, 2])
def test_streamed_writer_determinism_derived_fixture(monkeypatch, real_cells, workers):
    directory = q6.OUTPUT/'tests'/uuid.uuid4().hex
    directory.mkdir(parents=True)
    # Use the unchanged real manifest, selecting two actual cells only.
    cells = [c for c in real_cells if c['dim'] == 1 and c['sigma'] > 0][:2]
    monkeypatch.setattr(q6, 'select_smoke', lambda original: cells)
    first = q6.run(directory/'serial', smoke=True, workers=1)
    try:
        second = q6.run(directory/'repeat', smoke=True, workers=workers)
    except PermissionError as error:
        if workers == 2 and getattr(error, 'winerror', None) == 5:
            pytest.skip('Managed Windows sandbox denies multiprocessing Pipe creation')
        raise
    assert first == second
    for file in (directory/'serial').iterdir():
        assert file.read_bytes() == (directory/'repeat'/file.name).read_bytes()
    for rule in q6.RULES:
        result = json.loads((directory/'repeat'/f'q6_{rule}_paths.json').read_bytes())
        assert len(result['cells']) == 2
        assert q6.canonical(result['cells'][0]['candidates']) == q6.canonical(
            q6.build_cell_job((cells[0], q6.EXPORT, False, None))[0][rule]['candidates'])
    assert not (directory/'repeat'/'estimator_points.csv').exists()
    assert {p.name for p in (directory/'repeat').iterdir()} == {
        *(f'q6_{rule}_paths.json' for rule in q6.RULES),
        'equations.csv', 'controls.csv', 'technical.json',
    }
    controls = q6.pd.read_csv(directory/'repeat'/'controls.csv')
    assert controls['q5_identity_control'].all()
