"""Q8 technical paths, measured planning, deterministic staging; no fits or truth scoring.

--path-end declares G-Q7's externally adopted exact-system end. Surrogates
always use Q7 significance. Existing Q5/Q6/Q7 source files are never modified.
"""
from __future__ import annotations
import argparse
import ast
import copy
import csv
import hashlib
import inspect
import json
import tarfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
import build_sideproject_q7_paths as q7
from build_sideproject_q5_paths import cell_id, read_export_index

q6 = q7.q6
ROOT, EXPORT = q7.ROOT, q6.EXPORT
OUTPUT = ROOT/'outputs/sideproject_q8_inputs'
Q7_PATHS = ROOT/'outputs/sideproject_q7_inputs/validated/q7_paths.json'
Q5_RECORDS = ROOT/'outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/out'
Q5_NFS = '/outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/input/export/'
Q8_NFS = '/outputs/sideproject_q8_<COMMIT_SHA>/input/'
ARMS = {
    'A10': ('first_sample',10,'weak',True), 'C10': ('estimated',10,'weak',True),
    'A1000': ('first_sample',1000,'weak',True), 'C1000': ('estimated',1000,'weak',True),
    'no_foba': ('estimated',1000,'weak',True),
    'random_start': ('estimated',1000,'random',True),
    'no_refit': ('estimated',1000,'weak',False),
}
PROTOCOL = ROOT/'docs/sideproject_residual_growth_protocol_q8.md'


def forward_only_path():
    """Disable the existing backward loop, without copying path arithmetic.

    The frozen function has no public FoBa switch. Identify its one loop with
    backward_checks and replace only its test by False; all other AST nodes
    (including forward choices, stops and candidate emission) are untouched.
    """
    tree = ast.parse(inspect.getsource(q6.growth_path_with_end))
    loops = [n for n in ast.walk(tree) if isinstance(n, ast.While) and
             any(isinstance(k, ast.Subscript) and isinstance(k.slice, ast.Constant) and
                 k.slice.value == 'backward_checks' for k in ast.walk(n))]
    # The outer forward loop also contains the backward loop; choose innermost.
    inner = [n for n in loops if not any(k in loops for k in ast.walk(n) if k is not n)]
    if len(inner) != 1:
        raise ValueError('Frozen FoBa loop layout changed')
    inner[0].test = ast.Constant(False)
    ns = dict(q6.__dict__)
    exec(compile(ast.fix_missing_locations(tree), '<Q8 forward-only Q6>', 'exec'), ns)
    return ns['growth_path_with_end']


FORWARD = forward_only_path()


def dump(path, value):
    path.write_bytes(q6.canonical(value)+b'\n')


def block(cell, ablation=False):
    if ablation: return 'ablations'
    if cell['dim'] < 3: return 'dim12_'+cell['representability']
    return 'dim3_52_61' if cell['system_id'] in (52,61) else 'dim3_54_59'


def source_cells():
    # Only classification/dimension metadata are read; no truth supports.
    support = json.loads((ROOT/'studies/regression/phase_c_support.json').read_bytes())
    systems = {s['system_id']:{k:s[k] for k in ('dim','representability')} for s in support['systems']
               if s['dim'] <= 2 or s['system_id'] in (52,61,54,55,56,57,58,59)}
    index = read_export_index(EXPORT/'index.csv')
    cells = []
    for row in index.to_dict('records'):
        sid = int(row['system_id'])
        if sid not in systems or row['noise_realization'] != 1: continue
        sigma, rho = float(row['noise_sigma']), float(row['subsample_rho'])
        if (sigma,rho) not in ((0,0),(.01,0),(.01,.5),(.05,0),(.05,.5)): continue
        dim = systems[sid]['dim']
        uid = f"sys{sid:04d}_ic{int(row['initial_condition_set'])}"
        cells.append(dict(unit_id=uid,cell_id=cell_id(uid,sigma,rho,1),system_id=sid,
            initial_condition_set=int(row['initial_condition_set']),dim=dim,
            representability=systems[sid]['representability'],stratum=f'dim{dim}_'+systems[sid]['representability'],
            sigma=sigma,rho=rho,realization=1,observed_data_sha256=q6.data_sha(pd.Series(row)),
            export=row,n_observed_points=int(row['n_observed_points'])))
    cells.sort(key=lambda c:c['cell_id'])
    if len(cells) != 590 or len({c['cell_id'] for c in cells}) != 590:
        raise ValueError('Expected exactly 590 Q8 source cells')
    return cells


def build_path(cell, path_end, no_foba=False):
    t,x = q6.read_index_cell(EXPORT,pd.Series(cell['export']))
    if q6.data_sha(pd.Series(cell['export'])) != cell['observed_data_sha256']:
        raise ValueError('Observation hash mismatch')
    terms = q6.phasec_basis(cell['dim'])
    designs, targets = zip(*(q6.build_design(t,x,e,'weak',terms)[:2] for e in range(cell['dim'])))
    use_q7 = path_end == 'q7' or cell['representability'] == 'surrogate'
    end = None
    if use_q7:
        variance = q6.estimate_noise_variance(t,x)
        incidence,_ = q6.weak_noise_operators(t)
        operators = [incidence.multiply(np.sqrt(variance[:,e])[None,:]).tocsr() for e in range(cell['dim'])]
        end = q7.significance_end(designs,operators,q7.THRESHOLDS['chi2_0.01'])
    function = FORWARD if no_foba else q6.growth_path_with_end
    path,_,ends = function(designs,targets,end_condition=end,cap=None if use_q7 else 6)
    candidates = [q6.candidate(designs,targets,terms,p['support'],f"q7_{p['step']:03d}",step=p['step'],origin=p['origin']) for p in path]
    return dict(cell,candidates=candidates,upper_candidates=[],path_end=[e['end_reason'] for e in ends],
                equation_paths=ends,ended_at_cap=not use_q7,end_condition='q7' if use_q7 else 'cap6')


def reuse_control(cell, original):
    a,b = cell['candidates'],original['candidates']
    if len(a)!=len(b): raise ValueError('A10 Q7 candidate count differs')
    for candidate,old in zip(a,b):
        for field in ('candidate_id','active_idxs','p0'):
            if q6.canonical(candidate[field]) != q6.canonical(old[field]):
                raise ValueError('A10 Q7 support/p0 differs')
        candidate.update(new=False,reuse_q7_candidate_id=old['candidate_id'])
    cell['reuse_q7'] = True
    return cell


def measured_costs():
    """Actual Q5 solve seconds per candidate, by dimension stratum.

    Surrogates and 54--59 have no Q5 timings; use their dimension's exact
    stratum explicitly as a proxy, with an extra unmeasured x1--2 on 54--59.
    """
    totals,counts = {},{}
    files = sorted(Q5_RECORDS.glob('index_*.jsonl'))
    if len(files)!=1632: raise ValueError('Complete Q5 grid timing inventory required')
    cells = {c['cell_id']:c for c in json.loads(q6.Q5.read_bytes())['cells']}
    for p in files:
        for line in p.read_text().splitlines():
            r=json.loads(line); dim=cells[r['cell_id']]['dim']
            seconds=float(r['fit_meta']['solve_time_s'])
            if not np.isfinite(seconds) or seconds<0: raise ValueError('Invalid solve time')
            totals[dim]=totals.get(dim,0.)+seconds; counts[dim]=counts.get(dim,0)+1
    return {d:totals[d]/counts[d] for d in totals}, dict(files=len(files),candidate_counts=counts,solve_seconds=totals)


def staging(cells, output):
    staged = json.loads(q6.Q5.read_bytes())['cells']
    existing = { (Path(c['export']['cell_dir'].replace('\\','/'))/c['export'][f].replace('\\','/')).as_posix()
                for c in staged for f in ('time_path','state_path')}
    required = {}
    for c in cells:
        for field in ('time_path','state_path'):
            rel=(Path(c['export']['cell_dir'].replace('\\','/'))/c['export'][field].replace('\\','/')).as_posix()
            required[rel]=c['export'][field.replace('_path','_sha256')]
    rows=[]
    with tarfile.open(output/'q8_export_additions.tar','w',format=tarfile.USTAR_FORMAT) as tar:
        # The full unchanged index is required in the overlay directory.
        for rel,digest in sorted({'index.csv':q6.sha256(EXPORT/'index.csv'),**required}.items()):
            p=EXPORT/rel
            if q6.sha256(p)!=digest: raise ValueError('Staging binary hash mismatch')
            old=rel in existing
            rows.append(dict(local_path=p.relative_to(ROOT).as_posix(),nfs_path=(Q5_NFS if old else Q8_NFS+'export_additions/')+rel,
                             sha256=digest,bytes=p.stat().st_size,already_staged=old))
            if not old:
                info=tar.gettarinfo(str(p),arcname=rel)
                info.mtime=info.uid=info.gid=0; info.uname=info.gname=''; info.mode=0o644
                with p.open('rb') as f: tar.addfile(info,f)
    with (output/'staging.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return dict(required_files=len(rows),new_files=sum(not r['already_staged'] for r in rows),
                tar_sha256=q6.sha256(output/'q8_export_additions.tar'))


def run(output, path_end, workers=1, limit=None):
    output=Path(output).resolve()
    if not output.is_relative_to(OUTPUT.resolve()): raise ValueError('Output outside Q8 workspace')
    if output.exists(): raise FileExistsError(output)
    if workers<1 or (limit is not None and limit<1): raise ValueError('Invalid workers/limit')
    cells=source_cells()
    if limit is not None: cells=cells[:limit]
    old={c['cell_id']:c for c in json.loads(Q7_PATHS.read_bytes())['cells']}
    costs,timing=measured_costs()
    def job(cell):
        normal=build_path(cell,path_end)
        if cell['representability']=='exact' and cell['cell_id'] in old and path_end=='q7':
            reuse_control(copy.deepcopy(normal),old[cell['cell_id']])
        forward=build_path(cell,path_end,True) if cell['dim']<3 else None
        return normal,forward
    with threadpool_limits(limits=1):
        if workers==1: results=list(map(job,cells))
        else:
            with ThreadPoolExecutor(max_workers=workers) as pool: results=list(pool.map(job,cells))
    arms={a:[] for a in ARMS}
    for normal,forward in results:
        for arm,(ic,bound,start,refit) in ARMS.items():
            if normal['dim']==3 and (arm in ('no_foba','random_start','no_refit') or
                (normal['system_id'] not in (52,61) and bound==10)): continue
            c=copy.deepcopy(forward if arm=='no_foba' else normal)
            c.update(arm=arm,ic_mode=ic,coefficient_bound=bound,start=start,refit=refit,
                     shard_id=c['cell_id']+'__'+arm,reuse_q7=False,block=block(c,arm in ('no_foba','random_start','no_refit')))
            if arm=='A10' and c['representability']=='exact':
                if path_end!='q7': raise ValueError('A10 reuse under cap6 requires externally supplied matching capped Q7 manifest')
                reuse_control(c,old[c['cell_id']])
            else:
                for k in c['candidates']: k['new']=True
            factor=(2 if ic=='estimated' and refit else 1)*(2 if c['system_id'] in range(54,60) else 1)
            seconds=0 if c['reuse_q7'] or not refit else costs[c['dim']]*len(c['candidates'])
            c.update(planned_seconds_low=seconds,planned_seconds_high=seconds*factor,
                     timing_proxy=f"Q5 dim{c['dim']} exact mean solve seconds/candidate",
                     unmeasured_factor=factor)
            arms[arm].append(c)
    header=dict(protocol='Q8',mode='grid' if limit is None else 'technical_limit',path_end=path_end,
                q8_protocol_sha256=q6.sha256(PROTOCOL),q7_paths_sha256=q6.sha256(Q7_PATHS),
                input_sha256={p.relative_to(ROOT).as_posix():q6.sha256(p) for p in
                    (EXPORT/'index.csv',PROTOCOL,Q7_PATHS,Path(__file__),Path(q7.__file__),Path(q6.__file__))})
    allcells=[c for a in arms.values() for c in a]
    fits=[c for c in allcells if not c['reuse_q7']]
    ordered=sorted(fits,key=lambda c:(-c['planned_seconds_high'],c['shard_id']))
    probes={}
    for name in sorted({c['block'] for c in allcells}):
        group=[c for c in allcells if c['block']==name]
        unit_cost={uid:sum(c['planned_seconds_high'] for c in group if c['unit_id']==uid) for uid in {c['unit_id'] for c in group}}
        units=sorted(unit_cost,key=lambda uid:(unit_cost[uid],uid))
        probes[name]=units[len(units)//2]
    probe=[c for c in ordered if c['unit_id']==probes[c['block']]]
    output.mkdir(parents=True)
    for arm,items in arms.items(): dump(output/f'q8_{arm}_paths.json',dict(header,cells=items))
    dump(output/'q8_paths.json',dict(header,cells=allcells))
    dump(output/'q8_fit_paths.json',dict(header,cells=fits))
    dump(output/'q8_probe_paths.json',dict(header,cells=probe))
    for name,items in (('grid',ordered),('probe',probe)):
        (output/f'q8_{name}.shards_cost_desc.txt').write_text(''.join(c['shard_id']+'\n' for c in items),encoding='utf8')
    summary=dict(source_cells=len(cells),cell_arms=len(allcells),shards=len(fits),probe_shards=len(probe),probe_units=probes,
        states=sum(len(c['candidates']) for c in allcells),new_states=sum(len(c['candidates']) for c in fits),timing=timing,
        blocks={b:dict(cell_arms=sum(c['block']==b for c in allcells),
            states=sum(len(c['candidates']) for c in allcells if c['block']==b),
            shards=sum(c['block']==b for c in fits),
            core_h_low=sum(c['planned_seconds_low'] for c in allcells if c['block']==b)/3600,
            core_h_high=sum(c['planned_seconds_high'] for c in allcells if c['block']==b)/3600)
            for b in sorted({c['block'] for c in allcells})},staging=staging(cells,output),
        no_refit_consequences='First observed IC; weak coefficients clamped to arm bound; zero optimizer calls. Simulation cost unmeasured.',
        path_end_authority='Externally declared; no G-Q7 verdict computed by this builder')
    dump(output/'technical.json',summary)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=OUTPUT/'grid')
    p.add_argument('--path-end',choices=['q7','cap6'],required=True)
    p.add_argument('--workers',type=int,default=1)
    p.add_argument('--limit',type=int)
    a=p.parse_args();print(json.dumps(run(a.output,a.path_end,a.workers,a.limit),sort_keys=True))
