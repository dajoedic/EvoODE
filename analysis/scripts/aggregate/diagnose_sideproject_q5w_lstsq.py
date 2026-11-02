"""Offline solver experiment; never edits or fits through the production port.

Reconstructed designs are labelled explicitly: preserved MATLAB JSONs contain
coefficients and tags, not G/b. No claim of bit identity with MATLAB G is made.
"""
from __future__ import annotations
import argparse
import json
import time
from pathlib import Path
import hashlib
from unittest.mock import patch
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.linalg import qr, solve_triangular, svdvals
from scipy.signal import convolve
from threadpoolctl import threadpool_limits
import run_sideproject_q5w_wsindy as runner
from scripts.aggregate import wsindy_reference as reference
from compare_sideproject_q5w_matlab import compare_equations


def qr_basic(a, b, **kwargs):
    """Pivoted-QR basic solution; candidate tolerance, not a MATLAB emulator.

    tol=max(m,n)*eps*abs(R11), fixed before inspecting outcomes. LAPACK
    pivoting/roundoff and MATLAB's internal rank test can still differ.
    """
    q, r, piv = qr(a, mode='economic', pivoting=True)
    tol = max(a.shape)*np.finfo(float).eps*abs(r[0, 0])
    rank = int(np.count_nonzero(np.abs(np.diag(r)) > tol))
    result = np.zeros(a.shape[1])
    if rank:
        result[piv[:rank]] = solve_triangular(r[:rank, :rank], (q.T@b)[:rank])
    return result, None, rank, None


def matrix_facts(g):
    if not g.shape[1]:
        return dict(rows=g.shape[0], columns=0, condition_number=None, svd_rank=0, qr_rank=0)
    singular = svdvals(g)
    _, r, _ = qr(g, mode='economic', pivoting=True)
    tolerance = max(g.shape)*np.finfo(float).eps*abs(r[0,0])
    return dict(rows=g.shape[0], columns=g.shape[1],
                condition_number=float(singular[0]/singular[-1]) if singular[-1] else 'inf',
                svd_rank=int(np.count_nonzero(singular > max(g.shape)*np.finfo(float).eps*singular[0])),
                qr_rank=int(np.count_nonzero(abs(np.diag(r)) > tolerance)), qr_tolerance=float(tolerance),
                singular_min=float(singular[-1]), singular_max=float(singular[0]))


def reconstructed_original(t, x, columns, original):
    """Independently assemble documented original-order scaled G and b.

    Reuse parameter/smoothing helpers; use the original's factorized test
    polynomial and normalize states before powers (unlike port arithmetic).
    """
    parameters = [reference.corner_parameters(y) for y in x.T]
    filtered = np.column_stack([reference.smooth(t,y)[0] for y in x.T])
    tags = np.asarray(original['tags_real'], float).reshape(-1, x.shape[1])
    imag = np.asarray(original['tags_imag'], float).reshape(tags.shape)
    powers = tags.max(axis=0)
    state_scale = np.linalg.norm(x**powers, axis=0)**(1/powers)
    theta = []
    for real, imaginary in zip(tags,imag):
        if np.any(imaginary):
            j = np.flatnonzero(imaginary)[0]
            theta.append(np.sin(filtered[:,j]) if imaginary[j]<0 else np.cos(filtered[:,j]))
        else:
            theta.append(np.prod((filtered/state_scale)**real,axis=1))
    theta = np.column_stack(theta)
    scaling = 1/np.prod(state_scale**tags,axis=1)
    designs,targets = [],[]
    dt = np.mean(np.diff(t))
    for eq, info in enumerate(parameters):
        m,p = info['half_support_samples'],info['degree']
        positive = np.arange(m+1)/m
        left,right = (1+positive)**p,(1-positive)**p
        phi = left*right
        derivative = p*(1+positive)**(p-1)*right - p*left*(1-positive)**(p-1)
        phi = np.r_[phi[::-1],phi[1:]]
        derivative = np.r_[-derivative[::-1],derivative[1:]]
        designs.append(np.column_stack([convolve(theta[:,j],phi*dt,mode='valid',method='direct') for j in range(theta.shape[1])]))
        targets.append(convolve(filtered[:,eq],derivative/m,mode='valid',method='direct'))
    return designs,targets,scaling


def experiment(g, b, scaling, permutation, solver=None):
    # Patch only this standalone process's imported callable, never its source.
    with patch.object(reference, 'lstsq', solver or reference.lstsq):
        coefficient, info = reference.select_model(g,b,scaling)
    info['coefficients_original_scale'] = coefficient[permutation].tolist()
    return info


def run(output, passing_sample=28, limit=None, original_design_dir=None):
    output.mkdir(parents=True,exist_ok=True)
    started = time.monotonic()
    results=[]
    for interp in (False,True):
        suffix='/w1_interp' if interp else ''
        base=runner.OUTPUT
        manifest=json.loads((base/('matlab_inputs'+suffix)/'manifest.json').read_text())
        verdicts={v['cell']:v for v in json.loads((base/('matlab_identity'+suffix)/'verdicts.json').read_text())}
        cells=[c for c in manifest['cells'] if 'seed' not in c['cell_key']]
        failures=[c for c in cells if not verdicts[c['cell_id']]['passed']]
        # Deterministic samples spread over systems/libraries, rather than first N.
        passing=[c for c in cells if verdicts[c['cell_id']]['passed']]
        positions=np.linspace(0,len(passing)-1,min(passing_sample,len(passing)),dtype=int)
        selected=failures+[passing[i] for i in positions]
        if limit: selected=selected[:limit]
        for cell in selected:
            if time.monotonic()-started>840:
                raise TimeoutError('15-minute protocol boundary')
            original=json.loads((base/('matlab_outputs'+suffix)/(cell['cell_id']+'.json')).read_text())
            data=loadmat(base/('matlab_inputs'+suffix)/cell['input_file'])
            t,x=data['tobs'].ravel(),data['xobs']
            for array,field in ((t,'time_sha256'),(x,'state_sha256')):
                if hashlib.sha256(np.asarray(array,dtype='<f8').tobytes(order='C')).hexdigest()!=cell[field]:
                    raise ValueError('diagnosis input hash mismatch')
            columns=runner.library(x.shape[1],cell['library'])
            gs,bs,scale,_=reference.weak_design(t,x,columns)
            ogs,obs,oscale=reconstructed_original(t,x,columns,original)
            permutation=np.asarray(original['port_to_original_column_index_base1'])-1
            scenarios={'port_gelsy':[], 'port_qr_basic':[], 'original_order_gelsy':[], 'original_order_qr_basic':[]}
            exported=None
            if original_design_dir is not None:
                exported=loadmat(original_design_dir/(cell['cell_id']+'.mat'))
                if any(str(exported[field].ravel()[0])!=cell[field] for field in ('time_sha256','state_sha256')):
                    raise ValueError('exported design input hash differs')
                if not np.array_equal(exported['permutation'].ravel().astype(int)-1,permutation):
                    raise ValueError('exported design column mapping differs')
                check=[dict(coefficients_original_scale=exported['coef'][permutation,eq].tolist(),
                            lambda_grid_index=int(exported['lambda_indices'].ravel()[eq])) for eq in range(x.shape[1])]
                if not compare_equations(check,original['equations'])['passed']:
                    raise ValueError('exported design run differs from preserved MATLAB output')
                scenarios.update(exported_matlab_gelsy=[],exported_matlab_qr_basic=[])
            equations=[]
            for eq,(g,b,og,ob) in enumerate(zip(gs,bs,ogs,obs)):
                identity=np.arange(g.shape[1])
                for name,design,target,scaling,perm,solver in (
                    ('port_gelsy',g,b,scale,identity,None),
                    ('port_qr_basic',g,b,scale,identity,qr_basic),
                    ('original_order_gelsy',og,ob,oscale,permutation,None),
                    ('original_order_qr_basic',og,ob,oscale,permutation,qr_basic)):
                    scenarios[name].append(experiment(design,target,scaling,perm,solver))
                active=np.flatnonzero(np.asarray(original['equations'][eq]['coefficients_original_scale']))
                original_active=permutation[active]
                equations.append(dict(equation=eq,selected_lambda_index=original['equations'][eq]['lambda_grid_index'],
                    port_full=matrix_facts(g),reconstructed_original_full=matrix_facts(og),
                    reconstructed_original_selected_support=matrix_facts(og[:,original_active]),
                    design_max_abs_delta=float(np.max(abs(g-og[:,permutation]))),
                    target_max_abs_delta=float(np.max(abs(b-ob)))))
                if exported is not None:
                    eg,eb=exported[f'G_{eq}'],exported[f'b_{eq}'].ravel()
                    es=exported['scaling'].ravel()
                    for name,solver in (('exported_matlab_gelsy',None),('exported_matlab_qr_basic',qr_basic)):
                        scenarios[name].append(experiment(eg,eb,es,permutation,solver))
                    equations[-1].update(exported_matlab_full=matrix_facts(eg),
                        exported_matlab_selected_support=matrix_facts(eg[:,original_active]),
                        reconstruction_max_absolute_delta=float(np.max(abs(og-eg))))
            results.append(dict(cell=cell['cell_id'],arm='W1-interp' if interp else 'W1',
                system_id=cell['cell_key']['system_id'],identity_passed=verdicts[cell['cell_id']]['passed'],
                equations=equations,scenarios={name:compare_equations(info,original['equations']) for name,info in scenarios.items()},
                experiment_equations={name:[{field:eq[field] for field in ('coefficients_original_scale','lambda_grid_index','lambda_hat')} for eq in info] for name,info in scenarios.items()}))
            if len(results)%25==0: print(json.dumps(dict(diagnosed_tasks=len(results))),flush=True)
    payload=dict(matrix_source='Exported MATLAB G/b plus Python reconstruction' if original_design_dir else 'Python reconstruction, not exported MATLAB G/b',
                 exact_original_matrices_available=original_design_dir is not None,
                 qr_tolerance='max(m,n)*eps*abs(R[0,0]); candidate, MATLAB internal test unverified',
                 passing_sample_per_arm=passing_sample,tasks=results)
    (output/'diagnosis.json').write_text(json.dumps(payload,indent=2),encoding='utf8')
    summary=[]
    for arm in ('W1','W1-interp'):
        for passed in (False,True):
            group=[r for r in results if r['arm']==arm and r['identity_passed']==passed]
            summary.append(dict(arm=arm,identity_passed=passed,tasks=len(group),
                scenario_identity_counts={name:sum(r['scenarios'][name]['passed'] for r in group) for name in scenarios},
                tasks_with_rank_deficient_design=sum(any(e['reconstructed_original_full']['svd_rank']<e['reconstructed_original_full']['columns'] for e in r['equations']) for r in group)))
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(json.dumps(summary),flush=True)
    return payload


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-dir',type=Path,default=runner.OUTPUT/'solver_diagnosis')
    p.add_argument('--original-design-dir',type=Path)
    p.add_argument('--limit',type=int)
    a=p.parse_args()
    if a.limit is not None and a.limit<1:p.error('--limit must be positive')
    with threadpool_limits(limits=1): run(a.output_dir,limit=a.limit,original_design_dir=a.original_design_dir)
