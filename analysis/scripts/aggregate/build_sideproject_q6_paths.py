"""Q6 stage 1: data-derived weak-space path ends (no fits or simulations).

Smoke mode deliberately does not evaluate truth or estimator quality. Scientific
tables are generated only by the full runner, for the subsequent authorized run.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from contextlib import ExitStack
import csv
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
from scipy import sparse

from build_sideproject_q5_paths import (
    ROOT, BASE, EXPORT, STRATA, WeakFit, phasec_basis, build_design,
    weak_coefficients, candidate, sha256, read_index_cell, data_sha,
)

Q5 = BASE / 'q5_grid_paths.json'
PROTOCOL = ROOT / 'docs/sideproject_residual_growth_protocol_q6.md'
OUTPUT = ROOT / 'outputs/sideproject_q6_paths'
RULES = ('primary', 'secondary', 'reference')
Q5_PROTOCOL = 'docs/sideproject_residual_growth_protocol_q5.md'
Q5_PROTOCOL_REVISION = 'f454a32'


def q5_input_digest(name):
    """Check the frozen Q5 protocol blob; all other inputs use their files."""
    if name == Q5_PROTOCOL:
        blob = subprocess.run(
            ['git', 'show', f'{Q5_PROTOCOL_REVISION}:{name}'], cwd=ROOT,
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout
        return hashlib.sha256(blob).hexdigest()
    return sha256(ROOT/name)


def estimate_noise_variance(time, state):
    """Nine-point local cubic residuals, leverage correction, 21-point mean.

    Centering/scaling times changes only polynomial coordinates, not the fit.
    The residual variance is estimated separately for every observed component.
    """
    time, state = np.asarray(time), np.asarray(state)
    n = len(time)
    if n < 9 or state.ndim != 2 or len(state) != n:
        raise ValueError('Need at least nine aligned observed points')
    if not np.isfinite(time).all() or not np.isfinite(state).all() or np.any(np.diff(time) <= 0):
        raise ValueError('Expected finite data and strictly increasing actual times')
    squared = np.empty_like(state, dtype=float)
    for i in range(n):
        start = min(max(i - 4, 0), n - 9)
        z = time[start:start+9] - time[i]
        z = z / np.max(np.abs(z))
        a = np.vander(z, 4, increasing=True)
        u, _, _ = np.linalg.svd(a, full_matrices=False)
        if np.linalg.matrix_rank(a) != 4:
            raise ValueError('Rank-deficient local cubic')
        residual = state[i] - (u @ (u.T @ state[start:start+9]))[i-start]
        leverage = float(u[i-start] @ u[i-start])
        squared[i] = residual**2 / (1 - leverage)
    prefix = np.vstack((np.zeros((1, state.shape[1])), np.cumsum(squared, axis=0)))
    lo, hi = np.maximum(np.arange(n)-10, 0), np.minimum(np.arange(n)+11, n)
    return (prefix[hi] - prefix[lo]) / (hi-lo)[:, None]


def weak_noise_operators(time):
    """Endpoint incidence D and trapezoid W in build_design's exact row order."""
    n = len(time)
    rows, starts, stops, wr, wc, wv = [], [], [], [], [], []
    for length in (1, 2, 4, 8, 16):
        for start in range(n-length):
            stop, row = start+length, len(rows)
            rows.append(row)
            starts.append(start)
            stops.append(stop)
            dt = np.diff(time[start:stop+1]) / 2
            weights = np.r_[dt, 0.] + np.r_[0., dt]
            wr.extend([row]*(length+1))
            wc.extend(range(start, stop+1))
            wv.extend(weights)
    d = sparse.csr_matrix((np.r_[-np.ones(len(rows)), np.ones(len(rows))],
                           (rows+rows, starts+stops)), shape=(len(rows), n))
    w = sparse.csr_matrix((wv, (wr, wc)), shape=(len(rows), n))
    return d, w


def basis_jacobian(state, terms):
    """Analytic derivatives, including monomials at zero (no division by x)."""
    n, dim = state.shape
    out = np.zeros((n, len(terms), dim))
    for col, term in enumerate(terms):
        if term.kind == 'constant':
            continue
        if term.kind in ('sin', 'cos'):
            x = state[:, term.var]
            out[:, col, term.var] = np.cos(x) if term.kind == 'sin' else -np.sin(x)
        elif term.kind == 'monomial':
            for axis, power in enumerate(term.powers):
                if not power:
                    continue
                value = np.full(n, float(power))
                for j, exponent in enumerate(term.powers):
                    value *= state[:, j] ** (exponent - (axis == j))
                out[:, col, axis] = value
        else:
            raise ValueError(f'Unknown basis kind: {term.kind}')
    return out


def projected_noise_floor(design, support, operator):
    """trace((I-P) LL') without a dense row-by-row covariance matrix.

    L already includes per-point standard deviations. SVD uses unit-norm
    design columns and the same lstsq rank convention as the weak solver.
    """
    total = float(operator.multiply(operator).sum())
    indices = sorted(support)
    if not indices:
        return total
    a = design[:, indices]
    norms = np.linalg.norm(a, axis=0)
    a = a / np.where(norms > 0, norms, 1.)
    u, s, _ = np.linalg.svd(a, full_matrices=False)
    rank = np.count_nonzero(s > np.finfo(float).eps * max(a.shape) * s[0]) if len(s) else 0
    projected = operator.T @ u[:, :rank]
    return max(0., total - float(np.sum(projected**2)))


def primary_floor(design, support, incidence, variance):
    return projected_noise_floor(design, support, incidence.multiply(np.sqrt(variance)[None, :]).tocsr())


def secondary_noise_operator(incidence, weights, variance, jacobian, coefficients, support, equation):
    indices = sorted(support)
    gradient = np.einsum('nkd,k->nd', jacobian[:, indices, :], coefficients)
    blocks = []
    for j in range(variance.shape[1]):
        block = -weights.multiply(gradient[:, j][None, :])
        if j == equation:
            block = block + incidence
        blocks.append(block.multiply(np.sqrt(variance[:, j])[None, :]))
    return sparse.hstack(blocks, format='csr')


def secondary_floor(design, target, support, incidence, weights, variance, jacobian, equation):
    coefficients, _ = weak_coefficients(design, target, sorted(support))
    operator = secondary_noise_operator(incidence, weights, variance, jacobian, coefficients, support, equation)
    return projected_noise_floor(design, support, operator)


def growth_path_with_end(designs, targets, end_condition=None, cap=None):
    """Frozen growth_path arithmetic and tie rules, with replaceable stops.

    end_condition(eq, fit, support) returns a floor or None (reference).
    cap=6 supplies the Q5 identity control; scientific paths use the full basis.
    Stops are reevaluated after cross-equation backward removals, as in Q4.
    A repeated FoBa state is discarded and the preceding state retained.
    Nonpositive best gain ends scientific paths; capped controls still raise.
    """
    fits = [WeakFit(a, b) for a, b in zip(designs, targets)]
    active = [set() for _ in fits]
    candidates, log, seen = [], [], set()
    step = 0

    def reason(eq):
        fit, support = fits[eq], active[eq]
        if cap is not None and len(support) >= cap:
            return 'cap'
        if fit.b_norm2 == 0 or fit.sse(support) / fit.b_norm2 < 1e-14:
            return 'sse'
        if len(support) == fit.p:
            return 'full'
        floor = end_condition(eq, fit, support) if end_condition else None
        return 'floor' if floor is not None and fit.sse(support) <= floor else None

    cycle = no_gain = False
    while True:
        gains = []
        for eq, fit in enumerate(fits):
            if reason(eq) is not None:
                continue
            for term in sorted(set(range(fit.p)) - active[eq]):
                gain = (fit.sse(active[eq]) - fit.sse(active[eq] | {term})) / fit.b_norm2
                gains.append((gain, eq, term))
        if not gains:
            break
        gain, eq, term = min(gains, key=lambda x: (-x[0], x[1], x[2]))
        if gain <= 0:
            if cap is not None:
                raise ValueError('No positive gain before protocol stop')
            no_gain = True
            break
        previous = [s.copy() for s in active]
        step += 1
        active[eq].add(term)
        entry = dict(step=step, addition=dict(equation=eq+1, basis_index=term+1, gain=gain),
                     gains=[dict(equation=e+1, basis_index=t+1, gain=g) for g,e,t in gains],
                     backward_checks=[])
        removed = False
        while True:
            checks = []
            for e, fit in enumerate(fits):
                for t in sorted(active[e]):
                    cost = (fit.sse(active[e] - {t}) - fit.sse(active[e])) / fit.b_norm2 if fit.b_norm2 else 0.
                    checks.append((cost, e, t))
            eligible = [x for x in checks if x[0] < .5 * gain]
            chosen = min(eligible) if eligible else None
            entry['backward_checks'].append(dict(
                checks=[dict(cost=c, equation=e+1, basis_index=t+1, qualifies=c < .5*gain) for c,e,t in checks],
                removed=None if chosen is None else dict(cost=chosen[0], equation=chosen[1]+1, basis_index=chosen[2]+1)))
            if chosen is None:
                break
            active[chosen[1]].remove(chosen[2])
            removed = True
        key = tuple(tuple(sorted(eq)) for eq in active)
        if key in seen:
            active, cycle = previous, True
            break
        seen.add(key)
        candidates.append(dict(step=step, origin='removal' if removed else 'addition', support=[list(eq) for eq in key]))
        log.append(entry)
    ends = []
    for eq in range(len(fits)):
        history = [tuple(c['support'][eq]) for c in candidates]
        # Length counts all joint states, including unchanged equation supports.
        ends.append(dict(equation_index=eq+1,
                         end_reason=reason(eq) or ('no_gain' if no_gain else 'cycle' if cycle else None),
                         path_length=len(history), states_beyond_6=sum(len(s) > 6 for s in history)))
    return candidates, log, ends


def canonical(value):
    """JSON bytes distinguish signed zeros as well as every float digit."""
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def select_smoke(cells):
    """Five cells per stratum: clean, then crossed noisy/zero sigma and both rho."""
    selected = []
    for stratum in STRATA:
        pool = [c for c in cells if c['stratum'] == stratum]
        unit = pool[0]['unit_id']
        pool = [c for c in pool if c['unit_id'] == unit]
        selected.append(next(c for c in pool if c['sigma'] == c['rho'] == 0))
        for noisy, irregular in ((False, True), (True, False), (True, True)):
            selected.append(next(c for c in pool if (c['sigma'] > 0) == noisy and (c['rho'] > 0) == irregular))
        selected.append(next(c for c in pool if c['sigma'] > 0 and c['rho'] > 0 and c['realization'] == 2))
    return selected


def build_cell_job(job):
    cell, export, scientific, truth = job
    row = pd.Series(cell['export'])
    time, state = read_index_cell(export, row)  # verifies raw-byte hashes
    if data_sha(row) != cell['observed_data_sha256']:
        raise ValueError(f"Q5 observed hash mismatch: {cell['cell_id']}")
    terms = phasec_basis(cell['dim'])
    designs, targets = zip(*(build_design(time, state, eq, 'weak', terms)[:2] for eq in range(cell['dim'])))
    control_path, _, _ = growth_path_with_end(designs, targets, cap=6)
    control_candidates = [candidate(designs, targets, terms, p['support'], f"path_{p['step']:03d}",
                                    step=p['step'], origin=p['origin']) for p in control_path]
    q5 = cell['candidates']
    if canonical(control_candidates) != canonical(q5):
        raise ValueError(f"Q5 identity control failed: {cell['cell_id']}")
    variance = estimate_noise_variance(time, state)
    incidence, weights = weak_noise_operators(time)
    jacobian = basis_jacobian(state, terms)
    paths, ends = {}, {}
    for rule in RULES:
        cache = {}

        def floor(eq, fit, support):
            key = (eq, tuple(sorted(support)))
            if key not in cache:
                cache[key] = (primary_floor(designs[eq], support, incidence, variance[:, eq]) if rule == 'primary'
                    else secondary_floor(designs[eq], targets[eq], support, incidence, weights, variance, jacobian, eq))
            return cache[key]

        try:
            path, _, ends[rule] = growth_path_with_end(designs, targets, None if rule == 'reference' else floor)
        except ValueError as error:
            raise ValueError(f"{cell['cell_id']} ({rule}): {error}") from error
        paths[rule] = [candidate(designs, targets, terms, p['support'], f"path_{p['step']:03d}",
                                step=p['step'], origin=p['origin']) for p in path]
    clean_control = None
    if cell['sigma'] == cell['rho'] == 0:
        clean_control = canonical(paths['primary']) == canonical(q5)
    table = []
    for rule in RULES:
        for eq, end in enumerate(ends[rule]):
            record = dict(cell_id=cell['cell_id'], unit_id=cell['unit_id'], system_id=cell['system_id'],
                          sigma=cell['sigma'], rho=cell['rho'], realization=cell['realization'],
                          stratum=cell['stratum'], rule=rule, **end)
            if scientific:
                true = set(truth[eq])
                history = [set(c['active_idxs'][eq]) for c in paths[rule]]
                reference = [set(c['active_idxs'][eq]) for c in paths['reference']]
                reached = next((i for i, s in enumerate(history) if true <= s), None)
                final = history[-1] if history else set()
                record.update(classification='R' if reached is not None else 'T' if any(true <= s for s in reference) else 'P',
                              extra_terms_at_end=len(final-true) if reached is not None else None,
                              extra_terms_first_truth=len(history[reached]-true) if reached is not None else None,
                              first_truth_step=reached+1 if reached is not None else None,
                              true_term_recall_at_end=len(final & true)/len(true))
            table.append(record)
    estimator = []
    if scientific:
        # Clean, full-observation export is selected from the actual index by the runner.
        clean_time, clean_state = read_index_cell(export, pd.Series(cell['_clean_export']))
        indices = np.searchsorted(clean_time, time)
        if np.any(indices >= len(clean_time)) or not np.array_equal(clean_time[indices], time):
            raise ValueError('Observed times are not an exact clean-export subset')
        true_sd = cell['sigma'] * np.abs(clean_state[indices])
        for i in range(len(time)):
            for eq in range(cell['dim']):
                estimator.append(dict(cell_id=cell['cell_id'], stratum=cell['stratum'], sigma=cell['sigma'],
                    rho=cell['rho'], realization=cell['realization'], point_index=i, equation_index=eq+1,
                    time=float(time[i]), estimated_sigma=float(np.sqrt(variance[i, eq])), true_sigma=float(true_sd[i, eq])))
    output_cells = {}
    for rule in RULES:
        result = {k:v for k,v in cell.items() if k != '_clean_export'}
        result.update(candidates=paths[rule], upper_candidates=[], path_end=[e['end_reason'] for e in ends[rule]],
                      ended_at_cap=False, end_condition=rule, equation_paths=ends[rule])
        output_cells[rule] = result
    return output_cells, table, estimator, dict(cell_id=cell['cell_id'], hash_control=True,
        q5_identity_control=True, primary_clean_identity=clean_control)


def run(output=OUTPUT, smoke=False, workers=1, limit=None):
    output = Path(output).resolve()
    if not output.is_relative_to(OUTPUT.resolve()):
        raise ValueError('Q6 outputs must stay under outputs/sideproject_q6_paths/')
    if output.exists():
        raise FileExistsError(output)
    payload = json.loads(Q5.read_text(encoding='utf8'))
    for name, expected in payload['input_sha256'].items():
        if q5_input_digest(name) != expected:
            raise ValueError(f'Q5 input hash mismatch: {name}')
    if len(payload['cells']) != 1632:
        raise ValueError('Expected 1,632 Q5 cells')
    export = next((ROOT/name).parent for name in payload['input_sha256'] if name.endswith('/index.csv'))
    cells = select_smoke(payload['cells']) if smoke else payload['cells']
    if limit is not None:
        if limit < 1 or not smoke:
            raise ValueError('--limit is only available for technical smoke checks')
        cells = cells[:limit]
    scientific = not smoke
    truth = {}
    if scientific:
        support = json.loads((ROOT/'studies/regression/phase_c_support.json').read_text(encoding='utf8'))
        truth = {s['system_id']:s['support_idxs'] for s in support['systems'] if s.get('representability') == 'exact'}
        clean = {(c['system_id'], c['initial_condition_set']):c['export'] for c in payload['cells'] if c['sigma'] == c['rho'] == 0}
        cells = [dict(c, _clean_export=clean[c['system_id'], c['initial_condition_set']]) for c in cells]
    jobs = [(c, export, scientific, truth.get(c['system_id'])) for c in cells]
    if workers < 1:
        raise ValueError('workers must be positive')
    inputs = dict(payload['input_sha256'])
    for path in (Q5, PROTOCOL, Path(__file__), ROOT/'studies/regression/phase_c_support.json',
                 ROOT/'analysis/exploratory/term_relevance/term_relevance.py',
                 ROOT/'analysis/scripts/aggregate/run_sideproject_residual_growth.py',
                 ROOT/'analysis/scripts/aggregate/build_sideproject_q3_weak_starts.py',
                 ROOT/'analysis/scripts/aggregate/build_sideproject_q4_paths.py'):
        inputs[path.relative_to(ROOT).as_posix()] = sha256(path)
    output.mkdir(parents=True)
    equation_rows = candidate_states = 0
    with ExitStack() as stack:
        handles = {}
        for rule in RULES:
            header = dict(protocol='Q6', mode='smoke' if smoke else 'grid', end_condition=rule, input_sha256=inputs)
            handle = stack.enter_context((output/f'q6_{rule}_paths.json').open('xb'))
            handle.write(canonical(header)[:-1] + b',"cells":[')
            handles[rule] = handle
        csv_handles = {name:stack.enter_context((output/f'{name}.csv').open('x', newline='', encoding='utf8'))
                       for name in ('equations', 'controls') + (('estimator_points',) if scientific else ())}
        writers = {}

        def append_rows(name, rows):
            if rows and name not in writers:
                writers[name] = csv.DictWriter(csv_handles[name], fieldnames=list(rows[0]))
                writers[name].writeheader()
            if rows:
                writers[name].writerows(rows)

        def serial_results():
            for job in jobs:
                yield build_cell_job(job)

        def parallel_results(pool):
            # Bound outstanding results to one batch, preserving input order.
            for start in range(0, len(jobs), workers):
                yield from pool.map(build_cell_job, jobs[start:start+workers])

        results = serial_results() if workers == 1 else parallel_results(
            stack.enter_context(ProcessPoolExecutor(max_workers=workers)))
        for index, result in enumerate(results):
            paths, equations, estimator, control = result
            for rule in RULES:
                if index:
                    handles[rule].write(b',')
                handles[rule].write(canonical(paths[rule]))
            append_rows('equations', equations)
            append_rows('controls', [control])
            if scientific:
                append_rows('estimator_points', estimator)
            equation_rows += len(equations)
            candidate_states += sum(len(paths[rule]['candidates']) for rule in RULES)
        for handle in handles.values():
            handle.write(b']}\n')
    if scientific:
        frame = pd.read_csv(output/'estimator_points.csv',
                            usecols=['stratum','sigma','rho','estimated_sigma','true_sigma'])
        frame['error'] = frame.estimated_sigma - frame.true_sigma
        frame['ratio'] = frame.estimated_sigma / frame.true_sigma.replace(0, np.nan)
        # No reporting probabilities are specified in Q6. Emit the complete
        # empirical quantile function at every order statistic, choosing none.
        with (output/'estimator_quantiles.csv').open('x', newline='', encoding='utf8') as handle:
            writer = csv.DictWriter(handle, fieldnames=['stratum','sigma','rho','metric','quantile','value','n_points'])
            writer.writeheader()
            for condition, group in frame.groupby(['stratum','sigma','rho'], sort=True):
                for metric in ('estimated_sigma','true_sigma','error','ratio'):
                    values = np.sort(group[metric].dropna().to_numpy())
                    base = dict(zip(('stratum','sigma','rho'), condition), metric=metric, n_points=len(values))
                    if not len(values):
                        writer.writerow(dict(base, quantile=None, value=None))
                    for index, value in enumerate(values, start=1):
                        writer.writerow(dict(base, quantile=index/len(values), value=float(value)))
    summary = dict(cells=len(cells), paths=len(cells)*len(RULES), equation_rows=equation_rows,
                   control_paths=len(cells), candidate_states=candidate_states,
                   hash_control=True, scientific_tables=scientific)
    (output/'technical.json').write_bytes(canonical(summary)+b'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT/'grid')
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--workers', type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.smoke, args.workers, args.limit), sort_keys=True))
