"""Audit Q5 inputs without fitting or reading any EvoGrow C-6 result."""
import heapq
import json
import csv
from collections import Counter
import pandas as pd
from build_sideproject_q5_paths import BASE, ROOT, STRATA, Q4, sha256
from aggregate_sideproject_q5 import REFERENCE


def audit():
    grid = json.loads((BASE/'q5_grid_paths.json').read_text())
    probe = json.loads((BASE/'q5_probe_paths.json').read_text())
    controls = json.loads((BASE/'q5_controls_paths.json').read_text())
    for payload in (grid,probe,controls):
        for name,digest in payload['input_sha256'].items():
            if sha256(ROOT/name)!=digest:
                raise ValueError('Stale input: '+name)
    refs = pd.read_csv(REFERENCE,usecols=['system_id','source_initial_condition_set','noise_sigma','subsample_rho','noise_realization','observed_data_sha256'])
    hashes = refs.groupby(['system_id','source_initial_condition_set','noise_sigma','subsample_rho','noise_realization']).observed_data_sha256.agg(set).to_dict()
    for c in grid['cells']:
        key=c['system_id'],c['initial_condition_set'],c['sigma'],c['rho'],c['realization']
        if hashes.get(key)!={c['observed_data_sha256']}:
            raise ValueError('Baseline hash control failed')
    with (BASE/'staging.csv').open(newline='',encoding='utf8') as f:
        staged=list(csv.DictReader(f))
    for row in staged:
        if sha256(ROOT/row['local_path'])!=row['sha256']:
            raise ValueError('Staging hash changed')
    q4={u['unit_id']:u for u in json.loads(Q4.read_text())['units']}
    for c in controls['cells']:
        if c['candidates']!=q4[c['unit_id']]['candidates'] or c['upper_candidates']!=q4[c['unit_id']]['upper_candidates']:
            raise ValueError('Clean Q4 path control failed')
    def scheduling(payload):
        estimates=[payload['q4_seconds_per_candidate'][c['unit_id']]*(len(c['candidates'])+len(c['upper_candidates'])) for c in payload['cells']]
        pods=[0.]*8
        for cost in estimates:
            heapq.heapreplace(pods,pods[0]+cost)
        return dict(core_hours=sum(estimates)/3600,ordered_wall_hours=max(pods)/3600,
            maximum_shard_hours=max(estimates)/3600,shards_over_3h=sum(e>10800 for e in estimates),
            by_stratum={s:sum(e for c,e in zip(payload['cells'],estimates) if c['stratum']==s)/3600 for s in STRATA})
    summary=dict(grid=scheduling(grid),probe=scheduling(probe),
        grid_build_seconds=grid['build_seconds'],probe_build_seconds=probe['build_seconds'],
        probe_units=probe['probe_units'],cells=len(grid['cells']),baseline_hashes_matched=len(grid['cells']),
        candidates=sum(len(c['candidates']) for c in grid['cells']),upper_candidates=len(grid['cells']),
        cap_paths=sum(c['ended_at_cap'] for c in grid['cells']),
        caps_by_stratum={s:dict(Counter(c['ended_at_cap'] for c in grid['cells'] if c['stratum']==s)) for s in STRATA},
        staging_files=len(staged),staging_bytes=sum(int(r['bytes']) for r in staged),
        probe_cells=[dict(cell_id=c['cell_id'],candidates=len(c['candidates']),q4_candidates=len(q4[c['unit_id']]['candidates']),
                          path_end=c['path_end']) for c in probe['cells']])
    (BASE/'input_audit.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__=='__main__':
    print(json.dumps(audit(),indent=2))
