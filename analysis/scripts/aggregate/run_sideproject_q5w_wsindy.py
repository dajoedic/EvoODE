"""Q5-W runner; evaluation is delegated unchanged to the WP-N47 path."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from unittest.mock import patch
from threadpoolctl import threadpool_limits
import numpy as np
import pandas as pd
import pysindy as ps

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'analysis'))
import scripts.aggregate.run_phasec_noise_sindy_baselines as baseline
from scripts.aggregate.run_wp_n6_sindy_baseline import LibraryConfig, term_name_from_monomial
from exploratory.term_relevance.term_relevance import phasec_basis, evaluate_basis
from scripts.aggregate.wsindy_reference import Column, fit, scales, select_model

EXPORT = ROOT/'outputs/phase_c_c6_data_conditions_5dd1df8'
REFERENCE = ROOT/'outputs/c6_sindy_baselines_dop853_e935c37/merged/details.csv'
OUTPUT = ROOT/'outputs/sideproject_q5w_wsindy'
CONFIGS = tuple(f'{arm}:{lib}' for arm in ('W1', 'W1-cap', 'W2') for lib in ('L-C6', 'L-Q5'))
INTERP_CONFIGS = ('W1-interp:L-C6', 'W1-interp:L-Q5')
KEYS = ['system_id', 'initial_condition_set', 'noise_sigma', 'subsample_rho', 'noise_realization']
CFG = LibraryConfig('poly_deg3_sin_cos_stlsq_0.1', 3, True, .1)


def library(dim, library_id='L-C6', degree=3, trig=True):
    """Derive columns and ordering from the existing canonical constructors."""
    if library_id == 'L-Q5':
        terms = phasec_basis(dim)
        columns = []
        for term in terms:
            name = term.name
            name = re.sub(r'u(\d+)', lambda m: f'x{int(m[1])-1}', name)
            name = re.sub(r'(sin|cos)\((x\d+)\)', r'\1(1 \2)', name)
            if term.kind == 'monomial':
                name = name.replace('*', ' ')
            powers = term.powers if term.powers else (0,)*dim
            columns.append(Column(name, lambda x, term=term: evaluate_basis(x, [term])[:, 0], powers))
        return columns
    cfg = LibraryConfig('acceptance' if degree != 3 or not trig else CFG.library_id, degree, trig, .1)
    existing = baseline.build_library(cfg)
    existing.fit(np.ones((2, dim)))
    names = existing.get_feature_names([f'x{i}' for i in range(dim)])
    poly = ps.PolynomialLibrary(degree=degree, include_bias=True).fit(np.ones((2, dim)))
    powers = list(poly.powers_) + [(0,)*dim]*(len(names)-len(poly.powers_))
    cached_input, cached_matrix = None, None
    def column(x, i):
        nonlocal cached_input, cached_matrix
        if x is not cached_input:
            cached_input, cached_matrix = x, np.asarray(existing.transform(x))
        return cached_matrix[:, i]
    # Each callable uses the established library's numerical evaluation.
    return [Column(name, lambda x, i=i: column(x, i), tuple(power))
            for i, (name, power) in enumerate(zip(names, powers))]


class StoredModel:
    def __init__(self, coefficients, names):
        self.coef, self.names = coefficients, names

    def coefficients(self):
        return self.coef

    def get_feature_names(self):
        return self.names


def evaluate(model, system, support, row, t, x, clean_t, clean):
    # Reuse all simulation, truth, pruning, serialization and row construction.
    with patch.object(baseline, 'fit_weak_sindy', return_value=model):
        return baseline.run_one_model('weak_sindy', CFG, system, support, row, t, x, clean_t, clean, integrator='dop853')


def interpolate_uniform(t, x):
    """Linear interpolation per state; preserve already-uniform inputs exactly."""
    t, x = np.asarray(t, dtype=float), np.asarray(x, dtype=float)
    if (t.ndim != 1 or len(t) < 2 or x.ndim != 2 or len(x) != len(t)
            or not np.all(np.isfinite(t)) or not np.all(np.isfinite(x))
            or not np.all(np.diff(t) > 0)):
        raise ValueError('interpolation requires finite states and increasing times')
    dt = float(np.mean(np.diff(t)))
    if not np.allclose(np.diff(t), dt, rtol=1e-10, atol=1e-14):
        uniform = np.linspace(t[0], t[-1], len(t))
        x = np.column_stack([np.interp(uniform, t, state) for state in x.T])
        t = uniform
    return t, x


def interpolation_facts(t, x):
    """Hash little-endian float64 C-order time bytes followed by state bytes."""
    digest = hashlib.sha256()
    for array in (t, x):
        digest.update(np.asarray(array, dtype='<f8').tobytes(order='C'))
    return dict(q5w_interpolation_points=len(t),
                q5w_interpolation_dt=float((t[-1]-t[0])/(len(t)-1)),
                q5w_interpolated_sha256=digest.hexdigest())


def fit_arm(t, x, columns, arm, row):
    if arm == 'W1-interp':
        t, x = interpolate_uniform(t, x)
    if arm != 'W2':
        return fit(t, x, columns, cap=6 if arm == 'W1-cap' else None)
    seed = baseline.weak_sindy_seed(row, CFG.library_id)
    # The constructor settings and seed are exactly those of fit_weak_sindy.
    np.random.seed(seed)
    weak = ps.WeakPDELibrary(function_library=baseline.build_library(CFG), derivative_order=0,
                             spatiotemporal_grid=np.asarray(t).reshape(-1, 1), include_bias=False)
    weak.fit(x)
    full_names = weak.get_feature_names([f'x{i}' for i in range(x.shape[1])])
    indices = [full_names.index(c.name) for c in columns]
    g = np.asarray(weak.transform(x))[:, indices]
    b = weak.convert_u_dot_integral(x)
    scaling = scales(x, columns)
    coefficients, metadata = [], []
    for eq in range(x.shape[1]):
        coef, info = select_model(g*scaling, b[:, eq], scaling)
        info.update(half_support_samples=None, half_support_time=float((t[-1]-t[0])/20),
                    degree=4, smoothing_window=1, n_test_functions=100, weak_seed=seed)
        coefficients.append(coef)
        metadata.append(info)
    return np.asarray(coefficients), metadata


def context():
    path = ROOT/'analysis/configs/paper1_phaseC_sindy_baseline.json'
    config = baseline.load_config(path)
    systems = {int(s['id']): s for s in baseline.load_benchmark(baseline.resolve_path(config['benchmark_path'], path))}
    support = baseline.load_phase_c_support(baseline.resolve_path(config['phase_c_support_path'], path)).set_index('system_id')
    return systems, support


def key(row):
    values = []
    for field in KEYS:
        if field == 'initial_condition_set' and field not in row:
            field = 'source_initial_condition_set'
        value = row[field]
        values.append(value.item() if hasattr(value, 'item') else value)
    return tuple(values)


def smoke_rows():
    index = baseline.read_export_index(EXPORT/'index.csv')
    _, support = context()
    surrogate = set(support.index[support.phasec_representability != 'exact'])
    return index[(index.system_id.isin(surrogate)) & (index.noise_sigma == 0) & (index.subsample_rho == 0)].head(20)


def reference_rows():
    # Read only one method; no comparative statistics are calculated.
    chunks = pd.read_csv(REFERENCE, chunksize=10000, low_memory=False, float_precision='round_trip')
    return pd.concat([f[f.method_config_id == 'weak_sindy_poly_deg3_sin_cos_stlsq_0.1'] for f in chunks], ignore_index=True)


def run(rows, configurations=CONFIGS, output=OUTPUT/'smoke', technical_only=False):
    output.mkdir(parents=True, exist_ok=True)
    result_path = output/'details.csv'
    reference = reference_rows().rename(columns={'source_initial_condition_set': 'initial_condition_set'}).set_index(KEYS)
    systems, support = context()
    clean_t = np.linspace(0, 10, 512)
    completed = set()
    if result_path.exists():
        previous = pd.read_csv(result_path)
        for _, r in previous.iterrows():
            completed.add((key(r), r.q5w_configuration))
    for _, row in rows.iterrows():
        t, x = baseline.read_index_cell(EXPORT, row)
        expected = reference.loc[key(row)]
        if baseline.data_sha(row) != expected.observed_data_sha256:
            raise ValueError(f'WP-N47 data hash mismatch: {key(row)}')
        sid = int(row.system_id)
        clean = None if technical_only else {ic: baseline.integrate_truth(systems[sid], ic-1, clean_t)[0] for ic in (1, 2)}
        for configuration in configurations:
            if (key(row), configuration) in completed:
                continue
            arm, lib = configuration.split(':')
            columns = library(x.shape[1], lib)
            started = time.perf_counter()
            coef, metadata = fit_arm(t, x, columns, arm, row)
            fit_elapsed = time.perf_counter()-started
            result = dict(zip(KEYS, key(row)), fit_status='success', observed_data_sha256=baseline.data_sha(row)) if technical_only else evaluate(StoredModel(coef, [c.name for c in columns]), systems[sid], support.loc[sid].to_dict(), row, t, x, clean_t, clean)
            result.update(method=arm, library_id=lib, method_config_id=configuration, stlsq_threshold='',
                          source_shard='q5w_laptop',
                          weak_sindy_source_note=baseline.weak_source_note() if arm == 'W2' else 'Q5-W independent published WSINDy implementation; reference commit 72d8d6e',
                          weak_seed=baseline.weak_sindy_seed(row, CFG.library_id) if arm == 'W2' else '',
                          q5w_configuration=configuration, q5w_equations=json.dumps(metadata, sort_keys=True),
                          q5w_library_evaluations=len(t)*(len(library(x.shape[1])) if arm == 'W2' else len(columns)),
                          q5w_least_squares_solves=sum(m['least_squares_solves'] for m in metadata),
                          fit_elapsed_s_context=fit_elapsed, q5w_elapsed_s_context=time.perf_counter()-started)
            if arm == 'W1-interp':
                result.update(interpolation_facts(*interpolate_uniform(t, x)))
            if not technical_only and not all(info['selected'] for info in metadata):
                result['sindy_structure_hit_raw'] = False
                result['sindy_structure_hit_pruned'] = False
            baseline.append_csv_rows(result_path, [result])
            print(f'completed {key(row)} {configuration}', flush=True)
    return result_path


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--cells', help='CSV with the five export cell keys')
    parser.add_argument('--all-cells', action='store_true', help='Full run for Claude after accepted smoke and user review')
    parser.add_argument('--configurations', default=','.join(CONFIGS))
    parser.add_argument('--output-dir', type=Path, default=OUTPUT/'smoke')
    args = parser.parse_args()
    configs = tuple(args.configurations.split(','))
    if not configs or set(configs)-set(CONFIGS + INTERP_CONFIGS):
        parser.error('unknown configuration')
    rows = baseline.read_export_index(EXPORT/'index.csv') if args.all_cells or args.cells else smoke_rows()
    if args.cells:
        requested = pd.read_csv(args.cells)
        rows = rows.merge(requested[KEYS], on=KEYS, validate='one_to_one')
        if len(rows) != len(requested):
            parser.error('requested cells are outside the selected export subset')
    if args.limit is not None:
        if args.limit < 1:
            parser.error('--limit must be positive')
        rows = rows.head(args.limit)
    acceptance = OUTPUT/'acceptance/summary.json'
    if not acceptance.exists() or not json.loads(acceptance.read_text())['pre_smoke_passed']:
        parser.error('pre-smoke acceptance has not passed')
    if args.all_cells:
        summary = json.loads(acceptance.read_text())
        if not summary.get('smoke', {}).get('passed', False):
            parser.error('full run requires accepted deterministic smoke')
        if args.output_dir == OUTPUT/'smoke':
            parser.error('full run requires a separate --output-dir')
    with threadpool_limits(limits=1):
        run(rows, configs, args.output_dir)


if __name__ == '__main__':
    main()
