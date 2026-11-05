"""WP-X3 presentation and real-page navigation contracts; no pixel claims."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'explainer/wisp'
sys.path.insert(0,str(ROOT/'analysis/scripts/explainer'))
from check_wisp_explainer_fit import parse_result

def test_navigation_dom_harness():
    # Page inventory and step membership are derived from the actual page, not
    # invented method pages. A small DOM target implements closest(), as used by
    # the actual event guard. Browser event routing/pixels remain Edge checks.
    soup=BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'),'html.parser')
    pages=[{'id':p['id'],'dataset':{'step':p.get('data-step','')}} for p in soup.select('main > .page')]
    script=r'''
const assert=require('assert'),W=require(process.argv[1]),pages=JSON.parse(process.argv[2]);
const ids=pages.map(p=>p.id),observed=[];
const nav=W.controller(ids,ids[3],(index,push,scroll)=>observed.push({index,push,scroll}));
assert.equal(nav.index,3);assert.equal(nav.next(),ids[4]);assert.equal(nav.previous(),ids[3]);
nav.go(-100);assert.equal(nav.index,0);nav.go(10000);assert.equal(nav.index,ids.length-1);
nav.link('#'+ids[5]);assert.equal(nav.index,5);assert.equal(observed.at(-1).push,false);
nav.link('#missing');assert.equal(nav.index,5);
nav.observe(6);assert.equal(observed.at(-1).scroll,false);
class Target{constructor(kind){this.kind=kind;}closest(selector){return selector.includes(this.kind)?this:null;}}
const plain=new Target('not-a-control');
assert.equal(W.inputAction({type:'keydown',key:'ArrowDown',target:plain}),1);
assert.equal(W.inputAction({type:'keydown',key:'PageUp',target:plain}),-1);
assert.equal(W.inputAction({type:'keydown',key:' ',shiftKey:true,target:plain}),-1);
for(const kind of ['input','select','#window-chart','[data-internal-scroll]','button']){
 const target=new Target(kind),before=nav.index;
 for(const event of [{type:'keydown',key:'ArrowDown',target},{type:'wheel',deltaY:100,target}]){
  const action=W.inputAction(event);if(action)nav.go(nav.index+action);
 }
 assert.equal(nav.index,before,'control changed page: '+kind);
}
assert.equal(W.inputAction({type:'wheel',deltaY:100,target:plain},{dragging:true}),0);
assert.equal(W.inputAction({type:'keydown',key:'ArrowDown',target:plain},{active:false}),0);
const wheel=W.wheelGate();assert.equal(wheel(0,100),1);
for(let t=20;t<=2000;t+=20)assert.equal(wheel(t,10),0,'inertial swipe skipped a page');
assert.equal(wheel(2400,-100),-1);
for(const [width,height,reduced,expected] of [[1366,657,false,false],[759,768,false,true],[1366,559,false,true],[1366,768,true,true],[760,560,false,false]])assert.equal(W.fallback(width,height,reduced),expected);
for(let i=0;i<pages.length;i++){
 const active=W.stepState(pages,i).filter(s=>s.active);
 assert.deepEqual(active.map(s=>s.step),pages[i].dataset.step?[pages[i].dataset.step]:[]);
}
for(const step of W.steps.filter(s=>s!=='data'))assert(ids.includes('p-'+step+'-intro'));
console.log('PASS actual-page navigation, controls, drag, inertia, every method highlight and fallback');
'''
    run=subprocess.run(['node','-e',script,str(BASE/'src/pages.js'),json.dumps(pages)],capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stdout+run.stderr

@pytest.mark.parametrize('configuration',['legacy','delivered'])
@pytest.mark.parametrize('language',['en','de'])
def test_full_presentation_dom(language,configuration):
    soup=BeautifulSoup((BASE/'dist/wisp_explainer.html').read_text(encoding='utf8'),'html.parser')
    data=json.loads(soup.select_one('#wisp-data').string)
    # Independent cubic reference from the real teaching record, including edges.
    import numpy as np
    teaching = data['live']['teaching']
    t, x = np.asarray(teaching['t']), np.asarray(teaching['observed'])
    cubic = []
    for center in (0, *range(round(len(t)/3),round(len(t)/3)+5), len(t)-1):
        start = min(max(center-4, 0), len(t)-9)
        ts = t[start:start+9]
        scale = max(abs(ts-t[center]))
        coefficients = np.linalg.lstsq(np.vander((ts-t[center])/scale, 4, increasing=True), x[start:start+9], rcond=None)[0]
        probe = np.linspace(ts[0], ts[-1], 17)
        cubic.append(dict(center=center, start=start, t=probe.tolist(), y=(np.vander((probe-t[center])/scale, 4, increasing=True) @ coefficients).tolist()))
    def node(tag):
        return {'tag':tag.name,'attrs':{k:' '.join(v) if isinstance(v,list) else v for k,v in tag.attrs.items()},
                'text':''.join(str(c) for c in tag.children if not getattr(c,'name',None)) if tag.name not in ('script','style') else '',
                'children':[node(c) for c in tag.children if getattr(c,'name',None)] if tag.name not in ('script','style') else []}
    fixture=ROOT/'outputs/wisp_explainer_checks/x3_dom_fixture.json'
    fixture.parent.mkdir(parents=True,exist_ok=True)
    fixture.write_text(json.dumps({'tree':node(soup.html),'data':data,'language':language,'configuration':configuration,'cubic':cubic}),encoding='utf8')
    run=subprocess.run(['node',str(ROOT/'analysis/tests/wisp_slides_dom.cjs'),str(BASE),str(fixture)],capture_output=True,text=True,timeout=60)
    assert run.returncode==0,run.stdout+run.stderr

def test_page_structure_and_bilingual_source():
    soup=BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'),'html.parser')
    pages=soup.select('main > .page')
    assert len(pages)==43
    assert [p['id'] for p in pages[:13]] == [
        'p-hook', 'p-challenge', 'p-c1-data', 'p-c1-slope', 'p-c1-noise-visible', 'p-c1-secants', 'p-c1-changes',
        'p-c1-error-empty', 'p-c1-fit', 'p-c1-every', 'p-c1-noise',
        'p-c1-percent', 'p-c1-solution',
    ]
    assert pages[-1]['id']=='p-glossary'
    assert len({p['id'] for p in pages})==len(pages)
    assert len(soup.select('#p-overview .pipeline-map > a'))==8
    assert len(soup.select('#p-recap [data-outcome]'))==8
    en,de=[json.loads((BASE/'src/i18n'/f'{lang}.json').read_text(encoding='utf8')) for lang in ('en','de')]
    assert en.keys()==de.keys()
    assert all(node['data-i18n'] in en for node in soup.select('[data-i18n]'))
    assert en['j323']=='Model' and de['j323']=='Modell'
    assert en['j263'].startswith('FROLS:') and de['j261'].startswith('FoBa:')

def test_fit_parser_and_failure_contract():
    report={'ok':False,'pages':[{'id':'p-window','ok':False,'contentHeight':700,'viewportHeight':657}]}
    dom='<pre id="fitcheck-result">'+json.dumps(report)+'</pre>'
    assert parse_result(dom)==report
    import pytest
    with pytest.raises(ValueError,match='initialization'):parse_result('<html></html>')
    with pytest.raises(ValueError,match='no pages'):parse_result('<pre id="fitcheck-result">{"pages":[]}</pre>')
