"""Lossless inputs and explicit library tags for the sealed MATLAB identity check."""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from scipy.io import savemat, loadmat
from run_sideproject_q5w_wsindy import OUTPUT, EXPORT, KEYS, baseline, key, library


def tags_for(columns):
    tags = np.asarray([c.powers for c in columns], dtype=complex)
    for i, column in enumerate(columns):
        match = re.fullmatch(r'(sin|cos)\(1 x(\d+)\)', column.name)
        if match:
            tags[i, int(match[2])] = -1j if match[1] == 'sin' else 1j
    return tags


def tag_values(x, tags):
    values = []
    for tag in tags:
        if np.any(tag.imag):
            j = np.flatnonzero(tag.imag)[0]
            values.append(np.sin(x[:, j]) if tag[j].imag < 0 else np.cos(x[:, j]))
        else:
            values.append(np.prod(x**tag.real, axis=1))
    return np.column_stack(values)


def expressibility(columns, state):
    tags = tags_for(columns)
    expected = np.column_stack([c.function(state) for c in columns])
    delta = float(np.max(np.abs(tag_values(state, tags)-expected)))
    return dict(expressible=bool(np.allclose(tag_values(state, tags), expected, rtol=1e-14, atol=1e-14)),
                max_absolute_delta=delta, columns=len(columns),
                binding='polys=[], trigs=[], custom_tags=all explicit tags; custom_fcns={}; permute returned tags')


def array_hash(a):
    return hashlib.sha256(np.asarray(a, dtype='<f8').tobytes(order='C')).hexdigest()


def write_cell(folder, cell_id, cell_key, t, x, lib, columns):
    folder.mkdir(parents=True, exist_ok=True)
    payload = dict(cell_id=cell_id, cell_key=cell_key, library=lib,
                   time_sha256=array_hash(t), state_sha256=array_hash(x),
                   column_names=[c.name for c in columns], input_file=f'{cell_id}.mat')
    savemat(folder/payload['input_file'], dict(tobs=t[:, None], xobs=x,
            requested_tags=tags_for(columns)), do_compression=False)
    check = loadmat(folder/payload['input_file'])
    if not np.array_equal(check['tobs'][:, 0], t) or not np.array_equal(check['xobs'], x):
        raise ValueError('binary export failed round-trip identity')
    (folder/f'{cell_id}.json').write_text(json.dumps(payload, indent=2), encoding='utf8')
    return payload


def main():
    folder = OUTPUT/'matlab_inputs'
    entries = []
    t = np.linspace(0, 10, 10001)
    def rhs(_, u):
        return [10*(u[1]-u[0]), u[0]*(28-u[2])-u[1], u[0]*u[1]-8/3*u[2]]
    solution = solve_ivp(rhs, (0, 10), [-8, 7, 27], t_eval=t, method='RK45', rtol=1e-12, atol=1e-12)
    if not solution.success:
        raise ValueError(solution.message)
    x = solution.y.T
    for seed in [-1, *range(20)]:
        observed = x if seed == -1 else x + np.random.default_rng(seed).normal(0, .1*np.sqrt(np.mean(x*x)), x.shape)
        entries.append(write_cell(folder, f'lorenz_{seed}', dict(seed=seed), t, observed,
                                  'Lorenz-poly5', library(3, degree=5, trig=False)))
    index = baseline.read_export_index(EXPORT/'index.csv')
    uniform = index[index.subsample_rho == 0]
    for _, row in uniform.iterrows():
        t, x = baseline.read_index_cell(EXPORT, row)
        cell_key = dict(zip(KEYS, key(row)))
        slug = '_'.join(format(v, 'g') for v in key(row))
        for lib in ('L-C6', 'L-Q5'):
            entries.append(write_cell(folder, f'c6_{slug}_{lib}', cell_key, t, x, lib, library(x.shape[1], lib)))
    manifest = dict(lorenz_cells=21, c6_uniform_cells=len(uniform), tasks=len(entries), cells=entries)
    (folder/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'cells'}))


if __name__ == '__main__':
    main()
