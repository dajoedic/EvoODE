"""Validate Q8 technical artifacts without scientific metrics or simulations."""
import argparse
import csv
import hashlib
import json
import tarfile
from pathlib import Path
import build_sideproject_q8_paths as b


def validate(first, second, report):
    first,second=Path(first),Path(second)
    files={p.name for p in first.iterdir() if p.is_file()}
    if files!={p.name for p in second.iterdir() if p.is_file()}:raise ValueError('Artifact sets differ')
    comparisons={}
    for name in sorted(files):
        raw=(first/name).read_bytes()
        equal=raw==(second/name).read_bytes()
        if not equal:raise ValueError('Non-deterministic artifact: '+name)
        comparisons[name]=dict(equal=True,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    payload=json.loads((first/'q8_paths.json').read_bytes());cells=payload['cells']
    summary=json.loads((first/'technical.json').read_bytes())
    source={c['cell_id']:c for c in b.source_cells()}
    if len(cells)!=3770 or len(source)!=590:raise ValueError('Q8 scope differs')
    for name,digest in payload['input_sha256'].items():
        if b.q6.sha256(b.ROOT/name)!=digest:raise ValueError('Q8 input changed: '+name)
    originals={c['cell_id']:c for c in json.loads(b.Q7_PATHS.read_bytes())['cells']}
    reused=0
    for c in cells:
        for field in source[c['cell_id']]:
            if c[field]!=source[c['cell_id']][field]:raise ValueError('Cell identity differs')
        if c['representability']=='surrogate':
            if c['upper_candidates'] or any('truth' in key or key.startswith('true_') for key in c):
                raise ValueError('Surrogate truth dependency')
        if c['reuse_q7']:
            b.reuse_control(c,originals[c['cell_id']]);reused+=1
        for k in c['candidates']:
            active=[e['basis_indices'] for e in k['equations']]
            if active!=k['active_idxs'] or len(k['p0'])!=k['k'] or k['k']!=sum(map(len,active)):
                raise ValueError('Candidate parameter/basis schema')
            if b.q6.canonical(k['p0'])!=b.q6.canonical([v for e in k['equations'] for v in e['coefficients']]):
                raise ValueError('Parameter order differs')
    if reused!=230:raise ValueError('A10 reuse count')
    fits=json.loads((first/'q8_fit_paths.json').read_bytes())['cells']
    if b.q6.canonical(fits)!=b.q6.canonical([c for c in cells if not c['reuse_q7']]):raise ValueError('Fit scope differs')
    order=(first/'q8_grid.shards_cost_desc.txt').read_text().splitlines()
    expected=[c['shard_id'] for c in sorted(fits,key=lambda c:(-c['planned_seconds_high'],c['shard_id']))]
    if order!=expected or len(set(order))!=3540:raise ValueError('Shard order/coverage differs')
    for arm in b.ARMS:
        items=json.loads((first/f'q8_{arm}_paths.json').read_bytes())['cells']
        if b.q6.canonical(items)!=b.q6.canonical([c for c in cells if c['arm']==arm]):raise ValueError('Arm scope differs')
    probes={}
    for block in summary['blocks']:
        group=[c for c in cells if c['block']==block]
        costs={uid:sum(c['planned_seconds_high'] for c in group if c['unit_id']==uid) for uid in {c['unit_id'] for c in group}}
        units=sorted(costs,key=lambda uid:(costs[uid],uid))
        probes[block]=units[len(units)//2]
    if probes!=summary['probe_units']:raise ValueError('Probe order statistic differs')
    expected_probe=[c['shard_id'] for c in sorted(fits,key=lambda c:(-c['planned_seconds_high'],c['shard_id'])) if c['unit_id']==probes[c['block']]]
    if (first/'q8_probe.shards_cost_desc.txt').read_text().splitlines()!=expected_probe:raise ValueError('Probe coverage differs')
    rows=list(csv.DictReader((first/'staging.csv').open(newline='',encoding='utf8')))
    additions={}
    for r in rows:
        if b.q6.sha256(b.ROOT/r['local_path'])!=r['sha256']:raise ValueError('Staging source hash differs')
        if r['already_staged']=='False':additions[r['nfs_path'].split('export_additions/',1)[1]]=r['sha256']
    with tarfile.open(first/'q8_export_additions.tar') as tar:
        if set(tar.getnames())!=set(additions):raise ValueError('Tar inventory differs')
        for member in tar:
            if hashlib.sha256(tar.extractfile(member).read()).hexdigest()!=additions[member.name]:raise ValueError('Tar member hash differs')
    result=dict(passed=True,artifacts=comparisons,source_cells=590,cell_arms=3770,reused_cell_arms=reused,
        states=summary['states'],new_states=summary['new_states'],shards=3540,probe_shards=len(expected_probe),
        surrogate_truth_fields=False,staging_new_files=len(additions),blocks=summary['blocks'])
    report=Path(report);report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--first',type=Path,default=b.OUTPUT/'grid')
    p.add_argument('--second',type=Path,default=b.OUTPUT/'repeat')
    p.add_argument('--report',type=Path,default=b.OUTPUT/'validation.json')
    a=p.parse_args();r=validate(a.first,a.second,a.report)
    print(json.dumps({k:v for k,v in r.items() if k!='artifacts'},sort_keys=True))
