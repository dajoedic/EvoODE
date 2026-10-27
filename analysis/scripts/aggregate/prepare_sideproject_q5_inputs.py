"""Create Q5 staging inventory and audit clean export targets against baseline integration."""
import csv
import json
from pathlib import Path
import numpy as np
from build_sideproject_q5_paths import BASE, ROOT, EXPORT, Q4, STRATA, sha256
from run_phasec_noise_sindy_baselines import read_export_index, read_index_cell
from run_wp_n6_sindy_baseline import load_benchmark, integrate_truth


def prepare():
    grid_path = BASE/'q5_grid_paths.json'
    grid = json.loads(grid_path.read_text())
    index = read_export_index(EXPORT/'index.csv')
    benchmark = {int(s['id']):s for s in load_benchmark(ROOT/'benchmarks/data/strogatz_extended.json')}
    audit = []
    for c in grid['cells']:
        if c['sigma'] or c['rho']:
            continue
        row = index[(index.system_id==c['system_id']) & (index.initial_condition_set==c['initial_condition_set']) &
            (index.noise_sigma==0) & (index.subsample_rho==0) & (index.noise_realization==1)].iloc[0]
        t,x = read_index_cell(EXPORT,row)
        integrated,status = integrate_truth(benchmark[c['system_id']],c['initial_condition_set']-1,t)
        if status != 'success' or not np.isfinite(integrated).all():
            raise ValueError('Baseline truth integration failed')
        audit.append(dict(unit_id=c['unit_id'],max_abs_difference=float(np.max(np.abs(x-integrated))),
            max_scaled_difference=float(np.max(np.abs(x-integrated)/np.maximum(1.,np.abs(integrated)))),
            bit_identical=bool(np.array_equal(x,integrated))))
    (BASE/'clean_target_agreement.json').write_text(json.dumps(audit,indent=2)+'\n')
    # Preserve the full original index, including its SHA; stage only binaries needed by Q5.
    mappings = {EXPORT/'index.csv':'export/index.csv',grid_path:'q5_grid_paths.json',
                BASE/'q5_probe_paths.json':'q5_probe_paths.json',
                BASE/'q5_grid_paths.shards.txt':'q5_grid_paths.shards.txt',
                BASE/'q5_probe_paths.shards.txt':'q5_probe_paths.shards.txt'}
    for c in grid['cells']:
        row = c['export']
        for field in ('time_path','state_path'):
            rel = Path(str(row['cell_dir']).replace('\\','/'))/Path(str(row[field]).replace('\\','/'))
            mappings[EXPORT/rel] = 'export/'+rel.as_posix()
    with (BASE/'staging.csv').open('x',newline='',encoding='utf8') as f:
        writer = csv.DictWriter(f,fieldnames=['local_path','nfs_path','sha256','bytes'])
        writer.writeheader()
        for path,relative in sorted(mappings.items(),key=lambda x:str(x[0])):
            writer.writerow(dict(local_path=path.relative_to(ROOT).as_posix(),
                nfs_path='/outputs/sideproject_q5_<COMMIT_SHA>/input/'+relative,
                sha256=sha256(path),bytes=path.stat().st_size))
    return audit


if __name__ == '__main__':
    print(json.dumps(prepare(),indent=2))
