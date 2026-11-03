"""WP-X2 presentation, bilingual DOM and display-import contract checks."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import uuid
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'explainer/wisp'
sys.path.insert(0,str(ROOT/'analysis/scripts/explainer'))
import build_wisp_explainer_x2 as x2

def data(name):return json.loads((BASE/'data'/f'{name}.json').read_text(encoding='utf8'))

def test_selection_rule_from_real_units():
    selected=x2.select_featured(x2.rows('q5_units.csv'))
    assert selected==data('manifest')['featured_selection']['cells']
    assert len(set(selected.values()))==4
    candidates=x2.rows('q5_candidates.csv')
    for feature in data('live')['featured']:
        pool=[r for r in candidates if r['cell_id']==feature['cell_id'] and r['candidate_id'].startswith('path_')]
        assert [r['candidate_id'] for r in pool]==[c['row']['candidate_id'] for c in feature['candidates']]
        usable=[c for c in feature['candidates'] if c['row']['sentinel']=='False' and c['row']['diverged']=='False']
        assert min(usable,key=lambda c:(c['bic'],int(c['row']['step'])))['row']['candidate_id']==feature['chosen']

def test_strict_q7_rule():
    subprocess.run([sys.executable,str(ROOT/'analysis/scripts/explainer/check_wisp_explainer_x2.py')],check=True,capture_output=True,text=True,timeout=120)

def test_i18n_key_parity_and_claim_keys():
    en,de=[json.loads((BASE/'src/i18n'/f'{lang}.json').read_text(encoding='utf8')) for lang in ('en','de')]
    assert en.keys()==de.keys()
    assert all(isinstance(s,str) and s for table in (en,de) for s in table.values())
    marked=['j336','j337','j338','j339']
    assert all(key in en and key in de for key in marked)
    source=(BASE/'src/app.js').read_text(encoding='utf8')
    assert source.count("setAttribute('data-claim'")==1
    assert 'data-claim="review"' in (BASE/'src/index.html').read_text(encoding='utf8')
    print('Result-interpretation claim keys:',','.join(marked))


def dom_harness(language):
    # Reuse the established real-deliverable DOM harness, extending only browser APIs.
    tree=ast.parse((ROOT/'analysis/tests/test_wisp_explainer.py').read_text(encoding='utf8'))
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_app_harness')
    script=next(n.value.value for n in function.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='script' for t in n.targets))
    script=script[:script.index("if(elements.strata.children.length")]
    setup=r'''
const lang=process.argv[2];
global.location={href:'file:///wisp.html?lang='+lang,assign(url){this.href=url;}};
global.localStorage={getItem(){throw Error('storage unavailable');},setItem(){throw Error('storage unavailable');}};
document.documentElement=new Element('html');
Element.prototype.getAttribute=function(k){return this.attrs[k];};
for(const match of source.matchAll(/<([a-z0-9-]+)\b([^>]*data-i18n="([^"]+)"[^>]*)>/g)){
 const e=new Element(match[1]);e.dataset.i18n=match[3];
}
document.querySelectorAll=selector=>selector==='[data-i18n]'?all.filter(e=>e.dataset.i18n):selector==='[data-tex]'?all.filter(e=>e.dataset.tex):[];
'''
    script=script.replace("vm.runInThisContext",setup+"\nvm.runInThisContext",1)
    script+=r'''
if(document.documentElement.attrs.lang!==lang)throw Error('Wrong html lang');
for(const e of all.filter(e=>e.dataset.i18n))if(!e.textContent||e.textContent!==data.live.i18n[lang][e.dataset.i18n])throw Error('Missing static translation');
const keys=new Set(Object.keys(data.live.i18n.en));
for(const e of all)if(keys.has(e.textContent)&&!['WISP','BIC','u','r','K'].includes(e.textContent))throw Error('Raw translation key in DOM: '+e.textContent);
const claims=all.filter(e=>e.attrs['data-claim']);
if(claims.filter(e=>e.attrs['data-claim']!=='review').length!==4||claims.some(e=>e.attrs['data-claim']!=='review'&&!keys.has(e.attrs['data-claim'])))throw Error('Claim marker key mismatch');
for(const feature of data.live.featured){elements['fit-example'].value=feature.cell_id;elements['fit-example'].listeners.change();for(let i=0;i<feature.candidates.length;i++){elements['fit-candidate'].value=i;elements['fit-candidate'].listeners.input();}}
for(const feature of data.live.featured.filter(f=>f.stop_reference)){elements['stop-example'].value=feature.cell_id;elements['stop-example'].listeners.change();}
const other=lang==='de'?'en':'de';elements['language-'+other].listeners.click();
if(document.documentElement.attrs.lang!==other||!location.href.includes('lang='+other))throw Error('Language switch failed');
console.log('PASS DOM '+lang+'; controls, localStorage failure, markers, switch');
'''
    run=subprocess.run(['node','-e',script,str(BASE),language],capture_output=True,text=True,timeout=120)
    assert run.returncode==0,run.stdout+run.stderr
    return run.stdout

@pytest.mark.parametrize('language',['en','de'])
def test_bilingual_dom(language):print(dom_harness(language))

def test_julia_import_real_row_fixture():
    # Derive the CSV inventory and clean targets from real Q5 data. For this import-only
    # fixture, explicitly replace the model by the clean target and all expected R2 by 1.
    # This does not claim that Julia produced that model.
    row=copy.deepcopy(next(r for r in x2.rows('q5_units.csv') if r['size_rule']=='c'))
    payload=json.loads((x2.legacy.INPUTS/'q5_grid_paths.json').read_text(encoding='utf8'))
    cells={c['cell_id']:c for c in payload['cells']};cell=cells[row['cell_id']]
    targets={kind:x2.legacy.read_observations(cells[cid],set()) for kind,cid in (
        ('reconstruction',f"{cell['unit_id']}_s0_r0_n1"),
        ('generalization',f"sys{cell['system_id']:04d}_ic{3-cell['initial_condition_set']}_s0_r0_n1"))}
    record=dict(cell_id=row['cell_id'],candidate_id=row['candidate_id'],passed=True)
    for kind,(t,truth) in targets.items():
        record[kind]=dict(t=t.tolist(),truth=truth.tolist(),model=truth.tolist(),scores=dict(arithmetic=1.,variance_weighted=1.))
        for weight in ('arithmetic','variance_weighted'):row[f'{kind}_r2_{weight}']='1.0'
    parent=ROOT/'outputs/wisp_explainer_tests';parent.mkdir(exist_ok=True)
    path=parent/('julia_fixture_'+uuid.uuid4().hex+'.jsonl')
    try:
        assert x2.read_julia(path)=={}
        path.write_text(json.dumps(record)+'\n',encoding='utf8')
        loaded=x2.read_julia(path)[row['cell_id'],row['candidate_id']]
        bundle,reason=x2.julia_bundle(loaded,row,targets)
        assert reason is None and bundle is not None and len(bundle['t'])<=48
        loaded['reconstruction']['scores']['arithmetic']+=2e-12
        assert x2.julia_bundle(loaded,row,targets)[0] is None
        loaded['reconstruction']['scores']['arithmetic']=1.
        row['generalization_r2_arithmetic']=''
        assert x2.julia_bundle(loaded,row,targets)[0] is None
        row['generalization_r2_arithmetic']='1.0'
        loaded['generalization']['t'][0]+=1
        assert x2.julia_bundle(loaded,row,targets)[0] is None
        path.write_text(json.dumps(record)+'\n'+json.dumps(record)+'\n',encoding='utf8')
        with pytest.raises(ValueError,match='Duplicate'):x2.read_julia(path)
    finally:path.unlink(missing_ok=True)

def test_x2_size_budgets():
    assert (BASE/'dist/wisp_explainer.html').stat().st_size<=14_000_000
    assert sum(p.stat().st_size for p in (BASE/'data').rglob('*') if p.is_file())<=17_000_000


def test_absent_julia_preserves_results_and_present_file_is_consumed():
    import shutil
    parent=ROOT/'outputs/wisp_explainer_tests'
    folder=parent/('import_'+uuid.uuid4().hex);folder.mkdir(parents=True)
    try:
        (folder/'data').mkdir();(folder/'src/i18n').mkdir(parents=True)
        shutil.copyfile(BASE/'src/gates.json',folder/'src/gates.json')
        for lang in ('en','de'):shutil.copyfile(BASE/'src/i18n'/f'{lang}.json',folder/'src/i18n'/f'{lang}.json')
        subset=data('results')
        ids=set(x2.select_featured(x2.rows('q5_units.csv')).values())
        subset['cells']=[c for c in subset['cells'] if c['row']['cell_id'] in ids]
        for name,value in [('live',data('live')),('manifest',data('manifest')),('results',subset)]:
            x2.legacy.write_json(folder/'data'/f'{name}.json',value)
        x2.extend(folder,folder/'absent.jsonl')
        assert json.loads((folder/'data/results.json').read_text(encoding='utf8'))==subset
        # A supplied failed Julia record must supersede any earlier Python curve.
        cell=subset['cells'][0]
        failed=dict(cell_id=cell['row']['cell_id'],candidate_id=cell['row']['candidate_id'],passed=False,reason='Intentional fixture failure')
        x2.legacy.write_json(folder/'failed.jsonl',failed)
        x2.extend(folder,folder/'failed.jsonl')
        current=json.loads((folder/'data/results.json').read_text(encoding='utf8'))
        assert all(c['curves'] is None for c in current['cells'])
        assert next(c for c in current['cells'] if c['row']['cell_id']==failed['cell_id'])['unavailable']=='Intentional fixture failure'
    finally:
        assert folder.resolve().is_relative_to(parent.resolve())
        shutil.rmtree(folder)


def test_transport_roundtrip_on_real_curves():
    from build_wisp_explainer_html_x2 import transport
    source=dict(results=data('results'),live=data('live'),manifest=data('manifest'))
    packed=transport(source)
    def hydrate(bundle):
        if not bundle:return
        for key in ('t','truth','model'):bundle[key]=packed['display_arrays'][bundle[key]['$display']]
        hydrate(bundle.get('generalization'))
    for cell in packed['results']['cells']:hydrate(cell['curves'])
    for feature in packed['live']['featured']:
        for candidate in feature['candidates']:hydrate(candidate['curves'])
    packed.pop('display_arrays')
    assert packed==source
