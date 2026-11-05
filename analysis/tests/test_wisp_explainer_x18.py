"""Trajectory-fit presentation contracts, derived from the shipped teaching record."""
import json
import math
from pathlib import Path
import re
import subprocess

from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'explainer/wisp'


def test_fit_story_source_and_both_languages():
    soup=BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'),'html.parser')
    pages=soup.select('[data-chapter="five"]')
    assert [p['data-stage'] for p in pages]==['c5-'+n for n in ('weak','fit','each','bic','winner','recap')]
    assert all(n.get('data-claim')=='review' for p in pages for n in p.select('h2,p,.eyebrow'))
    assert all(pages[i].select_one('dialog') for i in (1,3,4))
    tables=[json.loads((BASE/f'src/i18n/{lang}.json').read_text(encoding='utf8')) for lang in ('de','en')]
    keys={k for k in tables[0] if k.startswith('x19_')}
    assert keys=={k for k in tables[1] if k.startswith('x19_')}
    for table in tables:
        assert all(table[k] and not re.search(r'\d',table[k]) for k in keys-{'x19_chapter'})
        assert not re.search(r'\d(?:[.,]\d+)?e[+-]?\d',' '.join(table[k] for k in keys),re.I)
    app=(BASE/'src/app.js').read_text(encoding='utf8')
    assert '...fourStates,...fiveStates' in app
    samples=(BASE/'src/pages.js').read_text(encoding='utf8')
    assert all("'"+p['data-stage']+"':[" in samples for p in pages)


def test_bic_identities_from_actual_records():
    live=json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
    feature=live['featured'][0]
    supports=feature['stop_reference']['supports']
    candidates=[c for c in feature['candidates'] if sorted(j-1 for j in json.loads(c['row']['active_idxs'])[0]) in supports]
    assert len(candidates)==len(supports)
    for candidate in candidates:
        row=candidate['row'];n=int(row['n_samples']);k=int(row['k'])
        assert n==len(live['teaching']['t'])*len(json.loads(row['active_idxs']))
        assert math.isclose(candidate['bic'],n*math.log(float(row['mse']))+k*math.log(n),rel_tol=1e-9)
        assert math.isclose(candidate['penalty'],k*math.log(n),rel_tol=1e-9)


def test_real_record_adapter_guards_supports_simulation_and_gates():
    script=r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path'),base=process.argv[1];
const source=fs.readFileSync(path.join(base,'src/app.js'),'utf8');
const live=JSON.parse(fs.readFileSync(path.join(base,'data/live.json'),'utf8'));
const protocol=JSON.parse(fs.readFileSync(path.join(base,'src/fit_protocol.json'),'utf8'));
const W=require(path.join(base,'src/compute.js'));
const ctx={W};vm.createContext(ctx);
vm.runInContext(source.slice(source.indexOf('function rk4('),source.indexOf('const demo='))+
 source.slice(source.indexOf('function fifthModel('),source.indexOf('function fifthSettings(')),ctx);
const actual=ctx.fifthModel(live,protocol),copy=()=>JSON.parse(JSON.stringify(live));
assert.equal(actual.weakCurve[0],live.teaching.observed[0]);
assert.deepEqual(actual.weak.p0,live.featured[0].path.find(p=>p.candidate_id===actual.weak.row.candidate_id).p0);
const shuffled=copy();shuffled.featured[0].candidates.reverse();shuffled.featured[0].path.reverse();
assert.deepEqual(ctx.fifthModel(shuffled,protocol).candidates.map(c=>c.row.candidate_id),actual.candidates.map(c=>c.row.candidate_id));
assert.equal(actual.winner.bic,Math.min(...actual.candidates.map(c=>c.bic)));
for(const c of actual.candidates){assert.strictEqual(c.curves,live.featured[0].candidates.find(p=>p.row.candidate_id===c.row.candidate_id).curves);assert.deepEqual(c.atBound,c.params.map(p=>Math.abs(p)===actual.bound));}
const changed=copy();changed.featured[0].candidates[0].bic=actual.winner.bic-actual.winner.penalty;
assert.equal(ctx.fifthModel(changed,protocol).winner.row.candidate_id,changed.featured[0].candidates[0].row.candidate_id);
const fitChange=copy();fitChange.featured[0].candidates.forEach(c=>c.row.params=JSON.stringify(JSON.parse(c.row.params).map(p=>p/2)));
assert.deepEqual(ctx.fifthModel(fitChange,protocol).weakCurve,actual.weakCurve);
const startChange=copy();startChange.featured[0].path.find(p=>p.candidate_id===actual.weak.row.candidate_id).p0[0]*=.99;
assert.notDeepEqual(ctx.fifthModel(startChange,protocol).weakCurve,actual.weakCurve);
const mismatch=copy();mismatch.teaching.cell_id='mismatched';assert.throws(()=>ctx.fifthModel(mismatch,protocol),/cell mismatch/);
const gates=copy();gates.gate_status={...gates.gate_status,coefficient_bound:'1000',initial_state:'estimated'};
const decided=ctx.fifthModel(gates,protocol);assert.equal(actual.provisional,true);assert.equal(decided.provisional,false);assert.equal(decided.bound,1000);assert.equal(decided.initial,'estimated');assert(decided.candidates.every(c=>c.atBound.every(b=>!b)));
const absent=copy();absent.featured[0].candidates[0].curves=null;absent.featured[0].candidates[0].unavailable='stored withheld reason';
assert.equal(ctx.fifthModel(absent,protocol).candidates[0].curves,null);
const mid=actual.weak.curves.t[1];assert.equal(ctx.fifthAt(actual.weak.curves,mid),actual.weak.curves.model[1][0]);
console.log('PASS support order, cell guard, weak p0/first observation, stored curves, computed winner/bounds and gate swap');
'''
    run=subprocess.run(['node','-e',script,str(BASE)],capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stdout+run.stderr
