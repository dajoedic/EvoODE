"""Q7 presentation evidence for named cells; no fitting or campaign discovery."""
import csv
import json
import math
from pathlib import Path
import numpy as np
import build_wisp_explainer_data as legacy
import build_sideproject_q6_paths as q6
from build_sideproject_q7_paths import significance_end, THRESHOLDS
from aggregate_phaseb_structure_metrics import true_coefficients_for_phasec_terms

IDS = ('sys0027_ic1_s0.03_r0_n1', 'sys0003_ic2_s0.03_r0_n1')
GRID = legacy.ROOT/'analysis/data/sideproject_residual_growth/q7_grid'
DISPLAY = legacy.ROOT/'outputs/wisp_explainer_julia/q7_examples.jsonl'
THRESHOLD = THRESHOLDS['chi2_0.01']


def display_candidate(record, row, targets, t, x, julia_bundle):
    """Validate complete arrays before exposing any fitted display trajectory."""
    if record is None:
        return None, None, None, 'Julia Q7 display export pending'
    try:
        if any(record.get('source_'+name+'_sha256') != legacy.digest(GRID/f'q7_{name}.csv')
               for name in ('units','candidates')):
            raise ValueError('Julia Q7 source hash mismatch')
        bundle,reason=julia_bundle(record,row,targets)
        if bundle is None:
            return None,None,None,reason
        for kind,(_,truth) in targets.items():
            prediction=np.asarray(record[kind]['model'],dtype=float)
            for weight,value in zip(('arithmetic','variance_weighted'),legacy.r2_scores(truth,prediction)[:2]):
                if not math.isfinite(value) or abs(value-float(row[f'{kind}_r2_{weight}']))>1e-12:
                    raise ValueError('Recomputed Julia score mismatch')
        def checked(kind,grid,truth):
            raw=record.get(kind,{})
            model=np.asarray(raw.get('model',[]),dtype=float)
            if raw.get('t')!=grid.tolist() or raw.get('truth')!=truth.tolist():
                raise ValueError('Julia '+kind+' target/grid mismatch')
            if model.shape!=truth.shape or not np.isfinite(model).all() or not np.array_equal(model[0],truth[0]):
                raise ValueError('Invalid Julia '+kind+' prediction')
            return {key:raw[key] for key in ('t','truth','model')},model
        training,observed=checked('training',t,x)
        ct,cx=targets['reconstruction']
        true_curve,model=checked('true_initial',ct,cx)
        if record['true_initial']['model']!=record['reconstruction']['model']:
            raise ValueError('True-initial curve differs from clean-start reconstruction')
        errors=dict(noisy_initial_clean_mse=float(np.mean((observed-cx)**2)),
                    true_initial_clean_mse=float(np.mean((model-cx)**2)),
                    noisy_initial_training_mse=float(np.mean((observed-x)**2)),
                    true_initial_training_mse=float(np.mean((model-x)**2)))
        # Both stored start-loss diagnostics must agree with these full-grid arrays.
        for field,key in (('observed_start_mse','noisy_initial_training_mse'),('clean_start_mse','true_initial_training_mse')):
            if abs(errors[key]-float(row[field]))>1e-12*max(1,abs(float(row[field]))):
                raise ValueError('Julia training error mismatch: '+field)
        curves={key:record['reconstruction'][key] for key in ('t','truth','model')}
        curves.update(generalization={key:record['generalization'][key] for key in ('t','truth','model')},training=training)
        return curves,true_curve,errors,None
    except (ValueError,TypeError,KeyError,IndexError,OverflowError) as exc:
        return None,None,None,'Malformed or withheld Julia Q7 record: '+str(exc)


def export_examples(live, manifest, byid, read_julia, julia_bundle):
    used = {GRID/n for n in ('q7_units.csv', 'q7_candidates.csv')}
    def rows(name):
        with (GRID/name).open(encoding='utf8', newline='') as f:
            return list(csv.DictReader(f))
    units, candidates = rows('q7_units.csv'), rows('q7_candidates.csv')
    benchmark = legacy.ROOT/'benchmarks/data/strogatz_extended.json'
    support_file = legacy.ROOT/'studies/regression/phase_c_support.json'
    used.update((benchmark, support_file, legacy.INPUTS/'q5_grid_paths.json'))
    systems = {s['id']: s for s in json.loads(benchmark.read_text(encoding='utf8'))}
    truths = {s['system_id']:s['support_idxs'] for s in json.loads(support_file.read_text())['systems']
              if s.get('representability') == 'exact'}
    records = read_julia(DISPLAY)
    examples = []
    for cid in IDS:
        cell = byid[cid]
        sid, ic, dim = cell['system_id'], cell['initial_condition_set'], cell['dim']
        t, x = legacy.read_observations(cell, used)
        targets = {kind:legacy.read_observations(byid[target_id], used) for kind,target_id in (
            ('reconstruction',f"{cell['unit_id']}_s0_r0_n1"),
            ('generalization',f"sys{sid:04d}_ic{3-ic}_s0_r0_n1"))}
        terms = q6.phasec_basis(dim)
        designs, targets_weak = zip(*(q6.build_design(t,x,e,'weak',terms)[:2] for e in range(dim)))
        variance = q6.estimate_noise_variance(t,x)
        incidence, _ = q6.weak_noise_operators(t)
        operators = [incidence.multiply(np.sqrt(variance[:,e])[None,:]).tocsr() for e in range(dim)]
        path, log, ends = q6.growth_path_with_end(designs,targets_weak,significance_end(designs,operators,THRESHOLD))
        pool = sorted((r for r in candidates if r['cell_id']==cid and r['candidate_id'].startswith('q7_')),
                      key=lambda r:int(r['step']))
        expected = [json.loads(r['active_idxs']) for r in pool]
        actual = [[[j+1 for j in eq] for eq in p['support']] for p in path]
        if actual != expected:
            raise ValueError('Q7 path support mismatch: '+cid)
        fits = [q6.WeakFit(a,b) for a,b in zip(designs,targets_weak)]
        def tests(support):
            result=[]
            for e,(a,fit,op) in enumerate(zip(designs,fits,operators)):
                active=set(support[e]); floor=q6.projected_noise_floor(a,active,op)
                blocks=[]
                for j in sorted(set(range(fit.p))-active):
                    noise=floor-q6.projected_noise_floor(a,active|{j},op)
                    gain=fit.sse(active)-fit.sse(active|{j})
                    blocks.append(dict(term=j+1,gain=gain/fit.b_norm2,noise=noise/fit.b_norm2,
                                       ratio=gain/noise if noise>0 else None,passes=noise<=0 or gain/noise>=THRESHOLD))
                result.append(dict(equation=e+1,blocks=blocks,stopped=not any(b['passes'] for b in blocks)))
            return result
        before=[[] for _ in range(dim)]
        rounds=[]
        for state,event in zip(path,log,strict=True):
            rounds.append(dict(**event,before=[[j+1 for j in eq] for eq in before],
                               support=[[j+1 for j in eq] for eq in state['support']],tests=tests(before)))
            before=state['support']
        exported=[]
        for row in pool:
            n,k,mse=int(row['n_samples']),int(row['k']),float(row['mse'])
            record=records.get((cid,row['candidate_id']))
            bundle,true_curve,errors,reason=display_candidate(record,row,targets,t,x,julia_bundle)
            exported.append(dict(row=row,active_idxs=json.loads(row['active_idxs']),params=json.loads(row['params']),
                                 N=n,k=k,mse=mse,bic=n*math.log(mse)+k*math.log(n),penalty=k*math.log(n),
                                 curves=bundle,unavailable=reason,true_initial=true_curve,curve_errors=errors))
        winner=min(exported,key=lambda c:c['bic'])
        chosen=next(r for r in units if r['cell_id']==cid and r['size_rule']=='c')
        if winner['row']['candidate_id']!=chosen['candidate_id']:
            raise ValueError('Q7 BIC winner mismatch: '+cid)
        system=systems[sid]
        labels=live['catalogues'][dim-1]['terms']
        coefficients=[true_coefficients_for_phasec_terms(equation,dim,[labels[j-1] for j in support])
                      for equation,support in zip(system['substituted'][0],truths[sid],strict=True)]
        examples.append(dict(cell_id=cid,system_id=sid,dim=dim,sigma=cell['sigma'],terms=live['catalogues'][dim-1]['terms'],
                             observed=dict(t=t.tolist(),x=x.tolist()),
                             clean={kind:dict(t=ct.tolist(),x=cx.tolist()) for kind,(ct,cx) in targets.items()},
                             truth=dict(equations=system['substituted'][0],constants=system['consts'][0],
                                        initial=system['init'][ic-1],other_initial=system['init'][2-ic],support=truths[sid],coefficients=coefficients),
                             path=rounds,stop=dict(threshold=THRESHOLD,equations=tests(before),ends=ends),
                             candidates=exported,chosen=winner['row']['candidate_id'],
                             seen_range=[float(x.min()),float(x.max())]))
    live['examples']=examples
    manifest['x19_inputs']={p.relative_to(legacy.ROOT).as_posix():legacy.digest(p) for p in sorted(used)}
    manifest['x19_display']=dict(path=DISPLAY.relative_to(legacy.ROOT).as_posix(),present=DISPLAY.is_file(),
                                  sha256=legacy.digest(DISPLAY) if DISPLAY.is_file() else None)
    manifest['x19_sources']={p.relative_to(legacy.ROOT).as_posix():legacy.digest(p) for p in (
        Path(__file__),legacy.ROOT/'studies/explainer/export_wisp_display_trajectories.jl',
        legacy.ROOT/'analysis/scripts/aggregate/aggregate_phaseb_structure_metrics.py')}
