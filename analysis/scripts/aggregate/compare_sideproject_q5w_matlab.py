"""Equation-wise identity verdicts only; no scientific performance aggregation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from run_sideproject_q5w_wsindy import OUTPUT, key


def compare_equations(port, original):
    if len(port) != len(original):
        return dict(passed=False, first_differing_equation=0, reason='equation_count')
    for eq, (a, b) in enumerate(zip(port, original)):
        ca = np.asarray(a['coefficients_original_scale'], float)
        cb = np.asarray(b['coefficients_original_scale'], float)
        reason = None
        if ca.shape != cb.shape or ca.ndim != 1 or not np.all(np.isfinite(ca)) or not np.all(np.isfinite(cb)):
            reason = 'coefficient_shape_or_finiteness'
        elif not np.array_equal(ca != 0, cb != 0):
            reason = 'support'
        elif a['lambda_grid_index'] != b['lambda_grid_index']:
            reason = 'lambda_grid_index'
        elif np.max(np.abs(ca-cb), initial=0) > 1e-6*np.max(np.abs(cb), initial=0):
            reason = 'coefficients'
        if reason:
            return dict(passed=False, first_differing_equation=eq, reason=reason)
    return dict(passed=True, first_differing_equation=None, reason=None)


def lorenz_equations(record):
    # Add metadata in memory only; never rewrite the preserved acceptance run.
    equations = []
    for coef, info in zip(record['coefficients'], record['equations']):
        indices = np.flatnonzero(np.asarray(info['lambda_grid']) == info['lambda_hat'])
        if len(indices) != 1:
            raise ValueError('preserved selected lambda is not unique on its grid')
        equations.append(dict(coefficients_original_scale=coef, lambda_grid_index=int(indices[0])))
    return equations


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--port-rows', type=Path, default=OUTPUT/'full/details.csv')
    parser.add_argument('--matlab-dir', type=Path, default=OUTPUT/'matlab_outputs')
    parser.add_argument('--output-dir', type=Path, default=OUTPUT/'matlab_identity')
    parser.add_argument('--interpolated', action='store_true', help='Check the W1-interp manifest and rows')
    args = parser.parse_args()
    if args.interpolated:
        if args.matlab_dir == OUTPUT/'matlab_outputs':
            args.matlab_dir = OUTPUT/'matlab_outputs/w1_interp'
        if args.output_dir == OUTPUT/'matlab_identity':
            args.output_dir = OUTPUT/'matlab_identity/w1_interp'
    manifest_path = OUTPUT/('matlab_inputs/w1_interp/manifest.json' if args.interpolated else 'matlab_inputs/manifest.json')
    manifest = json.loads(manifest_path.read_text())
    arm = 'W1-interp' if args.interpolated else 'W1'
    lorenz = {} if args.interpolated else {r['seed']: r for r in map(json.loads, (OUTPUT/'acceptance/lorenz.jsonl').read_text().splitlines())}
    rows = {}
    if args.port_rows.exists():
        for _, row in pd.read_csv(args.port_rows, float_precision='round_trip').iterrows():
            if row.q5w_configuration.startswith(arm + ':'):
                row_key = (key(row), row.q5w_configuration.split(':')[1])
                if row_key in rows:
                    raise ValueError('duplicate port cell')
                rows[row_key] = row
    verdicts = []
    for cell in manifest['cells']:
        path = args.matlab_dir/f"{cell['cell_id']}.json"
        row = rows.get((key(cell['cell_key']), cell['library'])) if 'seed' not in cell['cell_key'] else None
        port = lorenz_equations(lorenz[cell['cell_key']['seed']]) if 'seed' in cell['cell_key'] else (json.loads(row.q5w_equations) if row is not None else None)
        if not path.exists() or port is None:
            verdict = dict(passed=False, first_differing_equation=None, reason='missing_matlab' if not path.exists() else 'missing_port')
        else:
            original = json.loads(path.read_text())
            if args.interpolated and row.q5w_interpolated_sha256 != cell['q5w_interpolated_sha256']:
                verdict = dict(passed=False, first_differing_equation=None, reason='port_input_identity')
            elif any(original.get(k) != cell[k] for k in ('cell_id', 'library', 'time_sha256', 'state_sha256', 'column_names')):
                verdict = dict(passed=False, first_differing_equation=None, reason='manifest_identity')
            else:
                verdict = compare_equations(port, original['equations'])
        verdicts.append(dict(cell=cell['cell_id'], **verdict))
    summary = dict(cells=len(verdicts), passed=sum(v['passed'] for v in verdicts),
                   failing_cells=[v for v in verdicts if not v['passed']])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'verdicts.json').write_text(json.dumps(verdicts, indent=2), encoding='utf8')
    (args.output_dir/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    acceptance_path = OUTPUT/'acceptance/summary.json'
    acceptance = json.loads(acceptance_path.read_text())
    acceptance['matlab_interp_identity_passed' if args.interpolated else 'matlab_identity_passed'] = None if not any(args.matlab_dir.glob('*.json')) else all(v['passed'] for v in verdicts)
    acceptance_path.write_text(json.dumps(acceptance, indent=2), encoding='utf8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
