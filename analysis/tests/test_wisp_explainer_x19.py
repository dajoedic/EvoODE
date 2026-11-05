"""Named Q7 examples checked against real records and the shipped browser code."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import copy
import pytest

import numpy as np
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'explainer/wisp'
sys.path.insert(0,str(ROOT/'analysis/scripts/explainer'))


def test_named_examples_fields_hashes_and_winners():
    live=json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
    manifest=json.loads((BASE/'data/manifest.json').read_text(encoding='utf8'))
    with (ROOT/'analysis/data/sideproject_residual_growth/q7_grid/q7_candidates.csv').open(newline='') as f:
        rows=list(csv.DictReader(f))
    assert [e['cell_id'] for e in live['examples']]==['sys0027_ic1_s0.03_r0_n1','sys0003_ic2_s0.03_r0_n1']
    for name,sha in manifest['x19_inputs'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha
    for e in live['examples']:
        assert [p['support'] for p in e['path']]==[c['active_idxs'] for c in e['candidates']]
        x=np.array(e['observed']['x'])
        assert e['seen_range']==[x.min(),x.max()]
        for c in e['candidates']:
            source=next(r for r in rows if r['cell_id']==e['cell_id'] and r['candidate_id']==c['row']['candidate_id'])
            assert c['row']==source
            assert c['params']==json.loads(source['params'])
            assert c['bic']==c['N']*np.log(c['mse'])+c['k']*np.log(c['N'])
            if not manifest['x19_display']['present']:
                assert c['curves'] is None and c['true_initial'] is None and 'pending' in c['unavailable']
        assert min(e['candidates'],key=lambda c:c['bic'])['row']['candidate_id']==e['chosen']
        assert all(s['stopped'] for s in e['stop']['equations'])
        assert all(not block['passes'] and block['ratio']<e['stop']['threshold'] for s in e['stop']['equations'] for block in s['blocks'])
    lv,failure=live['examples']
    assert len(lv['path'])==4 and len(failure['path'])==3
    assert all(check['removed'] is None for e in live['examples'] for p in e['path'] for check in p['backward_checks'])
    assert lv['candidates'][-1]['row']['raw_exact']=='True'
    assert failure['candidates'][-1]['row']['raw_exact']=='False'
    assert all(float(failure['candidates'][-1]['row'][kind+'_r2_variance_weighted'])>.9 for kind in ('reconstruction','generalization'))


def test_live_failure_path_and_lv_record_guards():
    source=(BASE/'src/app.js').read_text(encoding='utf8')
    function=source[source.index('function exampleModel('):source.index('function initExamples(')]
    script=r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert'),base=process.argv[1];
const live=JSON.parse(fs.readFileSync(base+'/data/live.json','utf8'));
const ctx={W:require(base+'/src/compute.js'),soloDot:(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0)};vm.createContext(ctx);
vm.runInContext(process.argv[2]+';this.model=exampleModel;',ctx);
const [lv,failure]=live.examples.map(ctx.model);
assert.equal(failure.rounds.length,3);assert(failure.rounds.every(r=>r.backward_checks.every(b=>b.removed===null)));
for(const [i,round] of failure.rounds.entries()){
 assert.deepEqual(JSON.parse(JSON.stringify(round.support)),failure.example.path[i].support);
 for(const block of round.tests[0].blocks){const stored=failure.example.path[i].tests[0].blocks.find(b=>b.term===block.term);
  assert(Math.abs(block.gain-stored.gain)<1e-9);assert(Math.abs(block.ratio-stored.ratio)<1e-3);}
}
assert(failure.stopTests[0].blocks.every(b=>!b.passes));
const broken=JSON.parse(JSON.stringify(failure.example));broken.path[0].support=[[2]];
assert.throws(()=>ctx.model(broken),/Live failure path/);
const brokenLv=JSON.parse(JSON.stringify(lv.example));brokenLv.path[0].support=[[2],[]];
assert.throws(()=>ctx.model(brokenLv),/LV rounds/);
const winner=JSON.parse(JSON.stringify(lv.example));winner.chosen='q7_001';assert.throws(()=>ctx.model(winner),/argmin BIC/);
console.log('PASS live failure supports/gains/ratios, final stop, LV supports and argmin guards');
'''
    result=subprocess.run(['node','-e',script,str(BASE),function],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr


def test_example_pages_translations_and_pending_gate():
    soup=BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'),'html.parser')
    assert len(soup.select('[data-chapter="six"]'))==6
    assert len(soup.select('[data-chapter="seven"]'))==5
    assert len(soup.select('[data-chapter="eight"]'))==4
    assert soup.select_one('#p-c4-remains')['data-chapter']=='four'
    for lang in ('de','en'):
        table=json.loads((BASE/f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        for key,value in table.items():
            if key.startswith('x20_'):
                assert not re.search(r'[^\W\d_]\?[^\W\d_]',value)
                assert not re.search(r'\d',re.sub(r'\{\w+\}|G2|R²','',value)) or key in {'x20_chapter6','x20_chapter7','x20_chapter8'}
    app=(BASE/'src/app.js').read_text(encoding='utf8')
    assert "LIVE.gate_status.initial_state==='pending'" in app
    assert "highlight:e.seen_range" in app
    assert "curve($('c8-generalization'),teachingWinner.curves?.generalization)" in app
    julia=(ROOT/'studies/explainer/export_wisp_display_trajectories.jl').read_text(encoding='utf8')
    assert '--q7-examples' in julia and 'record["training"]' in julia
    assert not re.search(r'\b(?:fit_parameters|q5_fit|q5_main)\s*\(',julia)


def test_display_import_full_arrays_and_withholding_from_real_record():
    import build_wisp_explainer_x2 as x2
    from wisp_examples_x19 import display_candidate,GRID
    live=json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
    e=live['examples'][0]
    row=copy.deepcopy(e['candidates'][-1]['row'])
    # Start with the real Julia record inventory. Explicit identity-array replacements
    # below test import validation only; these arrays are not ODE predictions.
    record=copy.deepcopy(next(iter(x2.read_julia(ROOT/'outputs/wisp_explainer_julia/trajectories.jsonl').values())))
    record.update(passed=True,source_units_sha256=x2.legacy.digest(GRID/'q7_units.csv'),
                  source_candidates_sha256=x2.legacy.digest(GRID/'q7_candidates.csv'))
    targets={kind:(np.array(raw['t']),np.array(raw['x'])) for kind,raw in e['clean'].items()}
    t,x=np.array(e['observed']['t']),np.array(e['observed']['x'])
    for kind,(ct,cx) in targets.items():
        record[kind]=dict(t=ct.tolist(),truth=cx.tolist(),model=cx.tolist(),scores=dict(arithmetic=1.,variance_weighted=1.))
        for weight in ('arithmetic','variance_weighted'):
            row[f'{kind}_r2_{weight}']='1'
    record['training']=dict(t=t.tolist(),truth=x.tolist(),model=x.tolist())
    record['true_initial']=copy.deepcopy(record['reconstruction'])
    row['observed_start_mse']='0'
    row['clean_start_mse']=str(float(np.mean((targets['reconstruction'][1]-x)**2)))
    call=lambda r:display_candidate(r,row,targets,t,x,x2.julia_bundle)
    curves,true,errors,reason=call(record)
    assert reason is None and len(curves['t'])==len(t) and true is not None
    assert errors['noisy_initial_training_mse']==0
    assert call(None)[0] is None
    for change in ('hash','target','prediction','score','training_missing','training_start','true_initial','error'):
        broken=copy.deepcopy(record)
        if change=='hash':broken['source_units_sha256']='changed'
        if change=='target':broken['generalization']['t'][0]+=1
        if change=='prediction':broken['reconstruction']['model'][1][0]+=1
        if change=='score':broken['reconstruction']['scores']['arithmetic']+=1e-6
        if change=='training_missing':del broken['training']
        if change=='training_start':broken['training']['model'][0][0]+=1
        if change=='true_initial':broken['true_initial']['model'][1][0]+=1
        if change=='error':broken['training']['model'][1][0]+=1
        assert call(broken)[0] is None,change


@pytest.mark.parametrize('language',['en','de'])
def test_shipped_example_dom_and_replays(language):
    soup=BeautifulSoup((BASE/'dist/wisp_explainer.html').read_text(encoding='utf8'),'html.parser')
    data=json.loads(soup.select_one('#wisp-data').string)
    def node(tag):
        return dict(tag=tag.name,attrs={k:' '.join(v) if isinstance(v,list) else v for k,v in tag.attrs.items()},
                    text=''.join(str(c) for c in tag.children if not getattr(c,'name',None)) if tag.name not in ('script','style') else '',
                    children=[node(c) for c in tag.children if getattr(c,'name',None)] if tag.name not in ('script','style') else [])
    out=ROOT/'outputs/wp_x19';out.mkdir(exist_ok=True)
    fixture=out/f'dom_{language}.json'
    fixture.write_text(json.dumps(dict(tree=node(soup.html),data=data,language=language,configuration='examples')),encoding='utf8')
    result=subprocess.run(['node',str(ROOT/'analysis/tests/wisp_slides_dom.cjs'),str(BASE),str(fixture)],
                          capture_output=True,text=True,encoding="utf8",timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
