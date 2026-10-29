"""Acceptance and deterministic authorized smoke for WP-FA6."""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp
from threadpoolctl import threadpool_limits
from run_sideproject_q5w_wsindy import (
    ROOT, OUTPUT, EXPORT, CFG, KEYS, CONFIGS, library, context, reference_rows,
    smoke_rows, run, evaluate, StoredModel, baseline, key, phasec_basis,
)
from scripts.aggregate.wsindy_reference import fit


def lorenz(output):
    t = np.linspace(0, 10, 10001)
    def rhs(_, u):
        return [10*(u[1]-u[0]), u[0]*(28-u[2])-u[1], u[0]*u[1]-8/3*u[2]]
    solution = solve_ivp(rhs, (0, 10), [-8, 7, 27], t_eval=t, method='RK45', rtol=1e-12, atol=1e-12)
    if not solution.success:
        raise ValueError(solution.message)
    x = solution.y.T
    columns = library(3, degree=5, trig=False)
    names = [c.name.replace(' ', '*') for c in columns]
    truth = np.zeros((3, len(names)))
    for eq, terms in enumerate([{'x0': -10, 'x1': 10}, {'x0': 28, 'x1': -1, 'x0*x2': -1}, {'x2': -8/3, 'x0*x1': 1}]):
        for name, value in terms.items():
            truth[eq, names.index(name)] = value
    rows = []
    for seed in [-1, *range(20)]:
        started = time.perf_counter()
        observed = x if seed == -1 else x + np.random.default_rng(seed).normal(0, .1*np.sqrt(np.mean(x*x)), x.shape)
        coefficient, metadata = fit(t, observed, columns)
        delta = coefficient-truth
        row = dict(seed=seed, exact_support=bool(np.array_equal(coefficient != 0, truth != 0)),
                   E_inf=float(np.max(np.abs(delta))/np.max(np.abs(truth))),
                   E2=float(np.linalg.norm(delta)/np.linalg.norm(truth)),
                   lambda_hat=[m['lambda_hat'] for m in metadata], equations=metadata,
                   coefficients=coefficient.tolist(), elapsed_s_context=time.perf_counter()-started)
        rows.append(row)
        with (output/'lorenz.jsonl').open('a', encoding='utf8') as handle:
            handle.write(json.dumps(row, sort_keys=True)+'\n')
        print({k: row[k] for k in ('seed', 'exact_support', 'E_inf', 'E2', 'lambda_hat', 'elapsed_s_context')}, flush=True)
    return dict(clean_passed=rows[0]['exact_support'] and rows[0]['E_inf'] <= 1e-4,
                clean_E_inf=rows[0]['E_inf'], clean_exact_support=rows[0]['exact_support'],
                noisy_support_hits=sum(r['exact_support'] for r in rows[1:]), noisy_trials=20)


def mapping():
    results = []
    for dim in range(1, 5):
        c6 = library(dim)
        q5 = library(dim, 'L-Q5')
        existing = baseline.build_library(CFG).fit(np.ones((2, dim)))
        expected = existing.get_feature_names([f'x{i}' for i in range(dim)])
        names_match = expected == [c.name for c in c6]
        # Reversible naming map, independently applied to the canonical names.
        import re
        inverse = []
        for c in q5:
            name = re.sub(r'(sin|cos)\(1 (x\d+)\)', r'\1(\2)', c.name)
            name = name.replace(' ', '*')
            inverse.append(re.sub(r'x(\d+)', lambda m: f'u{int(m[1])+1}', name))
        canonical_match = inverse == [c.name for c in phasec_basis(dim)]
        state = np.arange(1, 1+5*dim, dtype=float).reshape(5, dim)/7
        q5_values = np.column_stack([c.function(state) for c in q5])
        c6_values = np.asarray(existing.transform(state))
        numerical_match = np.allclose(q5_values, c6_values[:, [expected.index(c.name) for c in q5]], rtol=1e-14, atol=1e-14)
        results.append(dict(dim=dim, L_C6_count=len(c6), L_Q5_count=len(q5), c6_names=expected,
                            q5_names=[c.name for c in q5], canonical_names=inverse,
                            passed=names_match and canonical_match and numerical_match))
    return results


def identity(output):
    reference = reference_rows()
    # Evaluation of stored coefficients only; this does not fit any C-6 cell.
    # Noisy trajectories are never loaded or used here.
    reference = reference[(reference.noise_sigma == 0) & (reference.subsample_rho == 0)].head(100)
    if len(reference) < 100:
        raise ValueError('fewer than 100 clean stored coefficient rows')
    index = baseline.read_export_index(EXPORT/'index.csv').set_index(KEYS)
    systems, support = context()
    clean_t = np.linspace(0, 10, 512)
    clean_cache, results = {}, []
    for _, stored in reference.iterrows():
        payload = json.loads(stored.sindy_coefficients_full)
        names = [term['term'].replace('*', ' ') for term in payload[0]]
        # Full serializer normalizes multiplication; trig also needs its space.
        coefficients = np.array([[term['coefficient'] for term in equation] for equation in payload])
        sid = int(stored.system_id)
        if sid not in clean_cache:
            clean_cache[sid] = {ic: baseline.integrate_truth(systems[sid], ic-1, clean_t)[0] for ic in (1, 2)}
        row_key = (sid, int(stored.source_initial_condition_set), 0., 0., int(stored.noise_realization))
        row = index.loc[row_key].copy()
        for field, value in zip(KEYS, row_key):
            row[field] = value
        # Evaluate at the same WP-N47 field names returned by build_library.
        names = baseline.build_library(CFG).fit(np.ones((2, int(stored.dimension)))).get_feature_names([f'x{i}' for i in range(int(stored.dimension))])
        actual = evaluate(StoredModel(coefficients, names), systems[sid], support.loc[sid].to_dict(), row,
                          clean_t, clean_cache[sid][int(row.initial_condition_set)], clean_t, clean_cache[sid])
        fields = [k for k in stored.index if k.startswith(('reconstruction_', 'generalization_', 'sindy_structure_', 'active_terms_'))]
        differences = []
        for field in fields:
            a, b = actual[field], stored[field]
            if isinstance(a, (float, np.floating)):
                equal = (np.isnan(a) and pd.isna(b)) or float(a) == float(b)
            else:
                equal = str(a) == str(b) or (a == '' and pd.isna(b))
            if not equal:
                differences.append(dict(field=field, actual=str(a), stored=str(b)))
        results.append(dict(cell=list(row_key), differences=differences, passed=not differences))
        if len(results) % 10 == 0:
            print(f'evaluation identity: {len(results)}/100', flush=True)
    (output/'evaluation_identity.json').write_text(json.dumps(results, indent=2), encoding='utf8')
    return dict(cells=len(results), bit_identical_cells=sum(r['passed'] for r in results),
                differing_fields=sum(len(r['differences']) for r in results))


def smoke(output):
    rows = smoke_rows()
    rows[KEYS].to_csv(output/'smoke_cells.csv', index=False)
    started = time.perf_counter()
    a = run(rows, output=OUTPUT/'smoke')
    b = run(rows, output=OUTPUT/'determinism_repeat')
    first, second = pd.read_csv(a), pd.read_csv(b)
    ignore = [c for c in first if 'elapsed' in c]
    deterministic = first.drop(columns=ignore).equals(second.drop(columns=ignore))
    totals = {field: int(first[field].sum()) for field in ('q5w_library_evaluations', 'q5w_least_squares_solves')}
    return dict(cells=len(rows), configurations=6, rows=len(first), deterministic=deterministic,
                fit_errors=int((first.fit_status != 'success').sum()), elapsed_two_runs_s_context=time.perf_counter()-started,
                smoke_counts=totals, projection_factor=4536/20,
                projected_full_counts={k: v*4536/20 for k, v in totals.items()},
                projected_full_s_context=float(first.q5w_elapsed_s_context.sum()*4536/20))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--stage', choices=['pre', 'complete-pre', 'smoke'], default='pre')
    args = parser.parse_args()
    output = OUTPUT/'acceptance'
    output.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=1):
        if args.stage in ('pre', 'complete-pre'):
            if args.stage == 'pre' and (output/'lorenz.jsonl').exists():
                raise FileExistsError('preserve the existing acceptance run')
            if args.stage == 'pre':
                published = lorenz(output)
            else:
                records = [json.loads(line) for line in (output/'lorenz.jsonl').read_text().splitlines()]
                if [r['seed'] for r in records] != [-1, *range(20)]:
                    raise ValueError('incomplete preserved Lorenz acceptance')
                published = dict(clean_passed=records[0]['exact_support'] and records[0]['E_inf'] <= 1e-4,
                                 clean_E_inf=records[0]['E_inf'], clean_exact_support=records[0]['exact_support'],
                                 noisy_support_hits=sum(r['exact_support'] for r in records[1:]), noisy_trials=20)
            summary = dict(lorenz=published, mapping=mapping(), identity=identity(output))
            summary['pre_smoke_passed'] = (summary['lorenz']['clean_passed'] and summary['lorenz']['noisy_support_hits'] >= 15
                                           and all(m['passed'] for m in summary['mapping'])
                                           and summary['identity']['bit_identical_cells'] == 100)
        else:
            summary = json.loads((output/'summary.json').read_text())
            if not summary['pre_smoke_passed']:
                raise ValueError('pre-smoke acceptance failed; no C-6 fits authorized')
            summary['smoke'] = smoke(output)
        (output/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
        print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
