"""Technical-only, bounded acceptance for the Q5-W interpolation addendum."""
import argparse
import json
import time
from pathlib import Path
import pandas as pd
from threadpoolctl import threadpool_limits
from run_sideproject_q5w_wsindy import (
    OUTPUT, EXPORT, KEYS, INTERP_CONFIGS, baseline, run, key,
)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT/'w1_interp_acceptance')
    folder = parser.parse_args().output_dir
    folder.mkdir(parents=True, exist_ok=True)
    index = baseline.read_export_index(EXPORT/'index.csv')
    rows = index[index.subsample_rho == .5]
    rows[KEYS].to_csv(folder/'cells_rho05.csv', index=False)
    # Balance dimensions and include clean/noisy observations, using actual index fields.
    groups = [rows[(rows.dimension == dim) & ((rows.noise_sigma > 0) if noisy else (rows.noise_sigma == 0))]
              for dim in (1, 2, 3) for noisy in (False, True)]
    smoke = pd.concat([g.head(3) for g in groups] + [g.iloc[3:4] for g in groups[:2]])
    if len(smoke) != 20 or smoke[KEYS].duplicated().any():
        raise ValueError('smoke selection must contain 20 unique cells')
    smoke[KEYS].to_csv(folder/'smoke_cells.csv', index=False)
    if not json.loads((OUTPUT/'acceptance/summary.json').read_text())['pre_smoke_passed']:
        raise ValueError('pre-smoke acceptance has not passed')
    # Refuse stale artifacts: both passes must be measured in this invocation.
    for name in ('smoke', 'repeat'):
        if (folder/name/'details.csv').exists():
            raise ValueError('smoke artifacts already exist; preserve them and choose a fresh acceptance folder')
    started = time.perf_counter()
    with threadpool_limits(limits=1):
        paths = [run(smoke, INTERP_CONFIGS, folder/name, technical_only=True)
                 for name in ('smoke', 'repeat')]
    elapsed = time.perf_counter()-started
    frames = [pd.read_csv(p, float_precision='round_trip').fillna('') for p in paths]
    expected = {(key(r), config) for _, r in smoke.iterrows() for config in INTERP_CONFIGS}
    for frame in frames:
        if len(frame) != 40 or {(key(r), r.q5w_configuration) for _, r in frame.iterrows()} != expected:
            raise ValueError('incomplete smoke coverage')
        if not frame.fit_status.eq('success').all():
            raise ValueError('fit error')
    stable = [f.drop(columns=[c for c in f if c.endswith('_elapsed_s_context')]) for f in frames]
    if not stable[0].equals(stable[1]):
        raise ValueError('non-deterministic smoke')
    factor = len(rows)/len(smoke)
    counts = {c: int(frames[0][c].sum()) for c in ('q5w_library_evaluations', 'q5w_least_squares_solves')}
    summary = dict(cells=len(rows), configurations=list(INTERP_CONFIGS), full_fits=len(rows)*2,
                   smoke_cells=len(smoke), rows_per_pass=40, deterministic=True, fit_errors=0,
                   counts_per_pass=counts, projection_factor=factor,
                   projected_counts={c: n*factor for c, n in counts.items()},
                   two_pass_wall_seconds_context=elapsed,
                   projected_fit_seconds_context=float(frames[0].fit_elapsed_s_context.sum()*factor),
                   strata=[dict(dimension=int(dim), noisy=bool(noisy), cells=len(g))
                           for (dim, noisy), g in smoke.groupby(['dimension', smoke.noise_sigma > 0])])
    (folder/'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
