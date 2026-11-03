"""Evidence-based checks for the single-file explainer (no campaign execution)."""
import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "explainer/wisp"


def exported(name):
    return json.loads((BASE / "data" / f"{name}.json").read_text(encoding="utf8"))


def test_every_rate_field_matches_csv():
    with (ROOT / "analysis/data/sideproject_residual_growth/q5_grid/q5_rates.csv").open(newline="", encoding="utf8") as f:
        source = list(csv.DictReader(f))
    assert exported("results")["rates"] == source
    assert len(source) == 3672


def test_cell_counts_and_scores_match_real_records():
    with (ROOT / "analysis/data/sideproject_residual_growth/q5_grid/q5_units.csv").open(newline="", encoding="utf8") as f:
        source = [r for r in csv.DictReader(f) if r["size_rule"] == "c"]
    data = exported("results")
    assert [c["row"] for c in data["cells"]] == source
    for row in data["rates"]:
        cells = [c for c in source if c["stratum"] == row["stratum"] and float(c["sigma"]) == float(row["sigma"])
                 and (float(c["sigma"]) != 0 or float(c["rho"]) != 0)
                 and (row["rho"] == "pooled" or float(c["rho"]) == float(row["rho"]))]
        assert len(cells) == int(row["n_cells"])
        assert len({c["unit_id"] for c in cells}) == int(row["n_units"])


def test_manifest_inputs_are_whitelisted_and_hash_checked():
    allowed = ("analysis/data/sideproject_residual_growth/q5_grid/", "analysis/data/sideproject_residual_growth/q5_probe/",
               "outputs/phase_c_c6_data_conditions_5dd1df8/", "outputs/sideproject_q5_inputs/", "outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/")
    for path, sha in exported("manifest")["inputs"].items():
        assert path.startswith(allowed) or path == "benchmarks/data/strogatz_extended.json"
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha


def test_no_unverified_trajectory_is_exported():
    manifest = exported("manifest")
    julia = manifest.get("julia_display", {})
    checks = {r["cell_id"]: r for r in (julia["checks"] if julia.get("present") else manifest["resimulation"]["checks"])}
    for cell in exported("results")["cells"]:
        if cell["curves"] is not None:
            check = checks[cell["row"]["cell_id"]]
            assert check["passed"]
            if not julia.get("present"):
                assert check["max_r2_error"] <= 1e-6
        else:
            assert cell["unavailable"]


def test_size_budget_and_presentation_sampling():
    assert (BASE / 'dist/wisp_explainer.html').stat().st_size <= 14_000_000
    assert sum(p.stat().st_size for p in (BASE / 'data').rglob('*') if p.is_file()) <= 17_000_000
    manifest, results, live = exported('manifest'), exported('results'), exported('live')
    assert results['schema_version'] == 2
    references = {r['cell_id']: r for r in live['references']}
    for cell in results['cells']:
        cid = cell['row']['cell_id']
        if cid in references:
            assert cell['observed']['t'] == references[cid]['t']
            assert [r[0] for r in cell['observed']['x']] == references[cid]['x']
        elif cell['observed']:
            assert len(cell['observed']['t']) <= manifest['display']['max_points']
        if cell['curves']:
            for bundle in (cell['curves'], cell['curves']['generalization']):
                assert len(bundle['t']) <= manifest['display']['max_points']
                assert len(bundle['truth']) == len(bundle['model']) == len(bundle['t'])


def test_failure_classification_uses_tightened_scores():
    checks = exported('manifest')['resimulation']
    assert checks['pass_tolerance'] == 1e-6
    assert checks['rtol'] == checks['atol'] == 1e-6
    assert checks['tightened_tolerance'] == 1e-7
    for check in checks['checks']:
        if check['status'] != 'failed':
            continue
        changes = [abs(value-check['tightened_scores'][kind][weight])
                   for kind, scores in check['scores'].items() for weight, value in scores.items()]
        assert check['max_r2_movement'] == max(changes)
        assert check['classification'] == ('integrator sensitivity' if max(changes) > 1e-6 else 'stable disagreement')


def test_html_build_is_deterministic_and_prose_has_no_literal_digits():
    command = [sys.executable, str(ROOT / "analysis/scripts/explainer/build_wisp_explainer_html_x2.py")]
    subprocess.run(command, check=True, capture_output=True)
    first = (BASE / "dist/wisp_explainer.html").read_bytes()
    subprocess.run(command, check=True, capture_output=True)
    assert (BASE / "dist/wisp_explainer.html").read_bytes() == first
    source = first.decode("utf8")
    paragraphs = re.findall(r"<p\b[^>]*>(.*?)</p>", source, flags=re.S)
    assert not [p for p in paragraphs if re.search(r"[0-9]", re.sub(r"<[^>]+>", "", p))]
    resources = re.findall(r'<(?:script|link)\b[^>]*(?:src|href)="([^"]+)"', source)
    assert resources == ["https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"]
    assert "fetch(" not in source


def test_numerical_illustrations_match_python():
    command = [sys.executable, str(ROOT / "analysis/scripts/explainer/check_wisp_explainer_js.py"), "--illustrations-only"]
    subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)


def test_q5_gate_fails_when_reference_bytes_are_missing():
    command = [sys.executable, str(ROOT / "analysis/scripts/explainer/check_wisp_explainer_js.py")]
    run = subprocess.run(command, capture_output=True, text=True, timeout=120)
    missing = exported("manifest")["missing_reference_cells"]
    assert run.returncode == (1 if missing else 0), run.stdout + run.stderr
    if missing:
        assert "BLOCKED" in run.stdout


def run_app_harness(base=BASE, extra=""):
    # A deliberately small DOM harness tests JS execution only, not browser layout.
    # Page IDs, defaults and all scientific inputs come from the actual deliverable.
    script = r'''
const fs=require('fs'),vm=require('vm'),base=process.argv[1];
const source=fs.readFileSync(base+'/dist/wisp_explainer.html','utf8'), data=JSON.parse(source.match(/<script id="wisp-data" type="application\/json">(.*?)<\/script>/s)[1]);
let all=[];
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.style={};this.listeners={};this.attrs={};this._value='';this.textContent='';this.classList={toggle:(name,on)=>{const classes=(this.className||'').split(' ').filter(c=>c&&c!==name);if(on)classes.push(name);this.className=classes.join(' ');}};all.push(this);}
 append(...children){this.children.push(...children);if(this.tag==='select'&&this._value===''&&this.children.length)this._value=this.children[0].value;}
 replaceChildren(...children){this.children=[];this._value='';this.append(...children);}
 setAttribute(k,v){this.attrs[k]=String(v);}
 getAttribute(k){return this.attrs[k];}
 get value(){return this._value;}
 set value(v){this._value=String(v);}
 addEventListener(event,fn){this.listeners[event]=fn;}
 querySelector(selector){if(selector.startsWith('.'))return this.querySelectorAll('*').find(c=>(c.className||'').split(' ').includes(selector.slice(1)));if(selector==='output')return this.children.find(c=>c.tag==='output');if(selector==='svg')return this.querySelectorAll('svg')[0];if(selector==='path')return this.querySelectorAll('path')[0];const type=selector.includes('checkbox')?'checkbox':'range';return this.children.flatMap(c=>[c,...c.children]).find(c=>c.type===type);}
 querySelectorAll(selector){return this.children.flatMap(c=>[c,...c.querySelectorAll('*')]).filter(c=>selector==='*'||c.tag===selector);}
 focus(){}
}
const elements={};for(const match of source.matchAll(/<([a-z0-9-]+)\b([^>]*\bid="([^"]+)"[^>]*)>/g)){
 const e=new Element(match[1]);elements[match[3]]=e;
 const v=match[2].match(/\bvalue="([^"]*)"/);if(v)e.value=v[1];
 if(match[1]==='select'){const body=source.slice(match.index).split('</select>')[0],opt=body.match(/<option value="([^"]+)"/);if(opt)e.value=opt[1];}
}
elements['wisp-data'].textContent=JSON.stringify(data);
global.document={getElementById:id=>{if(!elements[id])throw Error('Missing page ID '+id);return elements[id];},createElement:t=>new Element(t),createElementNS:(ns,t)=>new Element(t),querySelectorAll:()=>all.filter(e=>e.dataset.tex)};
global.innerWidth=1366;global.innerHeight=768;global.addEventListener=()=>{};document.addEventListener=()=>{};global.IntersectionObserver=class{observe(){}};
global.window=global;global.location={href:'file:///wisp.html?lang=en'};global.WispCompute=require(base+'/src/compute.js');
global.matchMedia=()=>({matches:true,addEventListener(){}});global.cancelAnimationFrame=()=>{};
vm.runInThisContext(fs.readFileSync(base+'/src/app.js','utf8'),{filename:'app.js'});
if(elements.strata.children.length!==new Set(data.results.rates.map(r=>r.stratum)).size)throw Error('Missing strata');
for(const sigma of [0,.01,.03,.05]){elements['noise-level'].value=sigma;elements['noise-level'].listeners.input();if(!elements['path-provenance'].textContent.startsWith(data.live.teaching&&sigma===data.live.teaching.sigma?'Real Q5':'Illustration'))throw Error('Teaching provenance label absent: '+elements['path-provenance'].textContent);elements['next-step'].listeners.click();}
for(const r of data.live.references){elements['path-example'].value=r.cell_id;elements['path-example'].listeners.change();}
for(const rho of ['pooled','0.0','0.5']){elements['result-rho'].value=rho;elements['result-rho'].listeners.change();}
elements['result-weight'].value='arithmetic';elements['result-weight'].listeners.change();
elements['play-reset'].listeners.click();elements['dimensions'].value='4';elements['dimensions'].listeners.change();
if(!elements['combination-count'].textContent.includes('27 terms'))throw Error('Wrong catalogue size');
const missingScore=data.results.cells.find(c=>c.row.reconstruction_r2_arithmetic==='');
if(missingScore){elements['cell-select'].value=missingScore.row.cell_id;elements['cell-select'].listeners.change();const detail=elements['cell-detail'].children.flatMap(c=>[c,...c.children]).map(c=>c.textContent).join(' ');if(!detail.includes('reconstruction: unavailable'))throw Error('Missing R2 shown as a number');}
console.log('Application initialized; noise, path, step, result filters, reset and catalogue controls executed.');
'''
    run = subprocess.run(["node", "-e", script + extra, str(base)], capture_output=True, text=True, timeout=120)
    assert run.returncode == 0, run.stdout + run.stderr


def test_app_initialization_and_controls_without_a_browser():
    if not (ROOT / 'analysis/data/sideproject_residual_growth/q7_q5w_comparison.csv').is_file():
        assert exported('results')['comparison']['status'] == 'pending'
    run_app_harness(extra=r"""
function texts(e){return [e.textContent,...e.children.flatMap(texts)];}
const labels=texts(elements.strata);
if(data.results.comparison.status==='pending'&&labels.some(t=>t.includes('WSINDy')))throw Error('Premature WSINDy result label');
if(!labels.some(t=>t.includes('Weak-SINDy (pysindy, fixed threshold)')))throw Error('Missing corrected baseline label');
const removal=data.live.references.find(r=>r.cell_id===data.manifest.foba_cell);
if(!removal?.available)throw Error('Real removal input unavailable');
elements['path-example'].value=removal.cell_id;elements['path-example'].listeners.change();
elements['path-step'].value=removal.path.length;elements['path-step'].listeners.input();
if(!elements['path-event'].textContent.includes('FoBa'))throw Error('Live FoBa failed');
if(!data.live.teaching||data.live.teaching.cell_id!==data.live.references[0].cell_id)throw Error('Missing real teaching cell');
// Visible titles accompany every Cartesian SVG chart, including dynamically created plots.
for(const svg of all.filter(e=>e.tag==='svg'&&e.attrs.class==='chart')){
 const horizontalSolo=svg.children.some(e=>e.tag==='text'&&[tr('x9_change'),tr('x10_rate')].includes(e.textContent)&&e.attrs.y==='17'&&!e.attrs.transform);
 if(!horizontalSolo&&!svg.children.some(e=>e.tag==='text'&&e.attrs.transform?.includes('rotate(-90)')))throw Error('Missing visible y axis title');
 if(!svg.children.some(e=>e.tag==='text'&&['306','267'].includes(e.attrs.y)))throw Error('Missing visible x axis title');
}
coeff[1]=1;enabled.splice(0,6,false,true,false,false,false,false);play();
if(!elements['play-status'].textContent.includes('clipped at twice'))throw Error('Missing clipping notice');
bars(elements['gain-chart'],[{term:1,gain:.1},{term:2,gain:.002}],1);
if(elements['gain-chart'].children[0].className!=='gain-bars')throw Error('Missing responsive HTML bars');
elements['noise-level'].value=data.live.teaching.sigma;elements['noise-level'].listeners.input();
if(!elements['noise-provenance'].textContent.startsWith('Real Q5'))throw Error('Real noise label missing');
""")


def test_results_swap_richer_schema():
    # Python 3.12's Windows mode-0700 temporary directories deny the sandbox
    # token access. Use inherited workspace permissions for this temporary tree.
    import shutil
    import uuid
    parent = ROOT / 'outputs/wisp_explainer_tests'
    parent.mkdir(parents=True, exist_ok=True)
    temporary = parent / ('swap_' + uuid.uuid4().hex)
    temporary.mkdir()
    try:
        check_results_swap(temporary)
    finally:
        assert temporary.resolve().is_relative_to(parent.resolve())
        shutil.rmtree(temporary)


def check_results_swap(tmp_path):
    # Deliberately fake rates. Real cell field inventory is retained as the basis.
    import copy
    import shutil
    base = tmp_path / 'synthetic-explainer'
    shutil.copytree(BASE / 'src', base / 'src')
    (base / 'data').mkdir()
    for name in ('live', 'manifest'):
        shutil.copyfile(BASE / 'data' / f'{name}.json', base / 'data' / f'{name}.json')
    source = exported('results')
    templates = {stratum: copy.deepcopy(next(c for c in source['cells'] if c['row']['stratum'] == stratum))
                 for stratum in ('dim1','dim2','dim3_feasible','dim4')}
    data = {k: copy.deepcopy(v) for k, v in source.items() if k not in ('cells', 'rates')}
    del source
    data.update(cells=[], rates=[], method_labels={'Q5':'WISP','sindy':'SINDy','weak_sindy':'Weak-SINDy (pysindy, fixed threshold)','e_sindy':'E-SINDy'}, provenance={'protocol': 'SYNTHETIC', 'status': 'synthetic'},
                axes=[{'key':'realization','label':'Realization','values':['1','2']},
                      {'key':'variant','label':'Initial-state estimation','values':['on','off']}],
                comparison={'status':'pending','rates':[]})
    strata = ['dim1', 'dim2', 'dim3_feasible', 'dim4', 'surrogate']
    methods = ['Q5', 'sindy', 'weak_sindy', 'e_sindy', 'WSINDy W1', 'WSINDy W1-interp']
    metrics = ['raw_exact','pruned_exact','reconstruction_arithmetic_hit',
               'reconstruction_variance_weighted_hit','generalization_arithmetic_hit',
               'generalization_variance_weighted_hit']
    for stratum in strata:
        for condition in range(11):
            for realization in ('1','2'):
                for variant in ('on','off'):
                    cell = copy.deepcopy(templates.get(stratum, templates['dim3_feasible']))
                    cell.update(exact=stratum!='surrogate', observed=None, curves=None,
                                unavailable='SYNTHETIC fixture; no trajectory')
                    cell['row'].update(stratum=stratum, sigma=str(condition/100), rho=str(condition%2/2),
                                       realization=realization, variant=variant,
                                       cell_id=f'SYNTHETIC_{stratum}_{condition}_{realization}_{variant}')
                    for kind in ('reconstruction','generalization'):
                        for weight in ('arithmetic','variance_weighted'):
                            cell['row'][f'{kind}_r2_{weight}'] = '-123456'
                    if not cell['exact']:
                        cell['row'].pop('raw_exact',None);cell['row'].pop('pruned_exact',None)
                        cell['truth']=[]
                    data['cells'].append(cell)
                    for method in methods:
                        for metric in metrics:
                            if stratum=='surrogate' and metric in ('raw_exact','pruned_exact'):
                                continue
                            data['rates'].append(dict(stratum=stratum,sigma=str(condition/100),rho=str(condition%2/2),
                                realization=realization,variant=variant,method=method,configuration='SYNTHETIC',
                                metric=metric,numerator='123456',denominator='1000000',rate='0.123456',n_units='1',n_cells='1'))
    data['selected_configuration_methods'] = []
    data['rates'] = [{**row, 'configuration': config} for row in data['rates'] for config in ('SYNTHETIC_A','SYNTHETIC_B')]
    (base/'data/results.json').write_text(json.dumps(data),encoding='utf8')
    subprocess.run([sys.executable,str(ROOT/'analysis/scripts/explainer/build_wisp_explainer_html_x2.py'),
                    '--base',str(base)],check=True,capture_output=True,text=True)
    run_app_harness(base, extra=r"""
function texts(e){return [e.textContent,...e.children.flatMap(texts)];}
if(elements['result-sigma'].children.length!==11)throw Error('Missing conditions');
if(elements['result-axes'].children.length!==2)throw Error('Missing axes');
elements['result-sigma'].value='0.01';elements['result-rho'].value='0.5';elements['result-sigma'].listeners.change();
for(const axis of data.results.axes){
 const control=all.find(e=>e.id==='axis-'+axis.key);
 for(const value of axis.values){control.value=value;control.listeners.change();if(!texts(elements.strata).some(t=>t.includes(axis.label+': '+value)))throw Error('Axis value not rendered');}
}
for(let condition=0;condition<11;condition++){
 elements['result-sigma'].value=String(condition/100);elements['result-rho'].value=String(condition%2/2);
 elements['result-sigma'].listeners.change();
 for(const box of elements.strata.children){
  const labels=texts(box);
  for(const method of ['WISP','SINDy','Weak-SINDy (pysindy, fixed threshold)','E-SINDy','WSINDy W1','WSINDy W1-interp']){
   if(!labels.some(t=>t.startsWith(method+' / ')))throw Error('Missing method '+method);
  }
  if(labels[0]==='surrogate'&&labels.includes('Raw structure'))throw Error('Surrogate structure metric');
  if(!labels.some(t=>t.includes('Initial-state estimation: off')))throw Error('Variant missing');
  for(const config of ['SYNTHETIC_A','SYNTHETIC_B'])if(!labels.some(t=>t.includes(' / '+config)))throw Error('Configuration missing');
 }
}
for(const box of elements.strata.children){const button=box.children.find(e=>e.tag==='button');button.listeners.click();}
""")


def test_observation_hash_and_path_gates_use_real_record():
    import copy
    import importlib.util
    import pytest
    spec = importlib.util.spec_from_file_location('wisp_data_export', ROOT / 'analysis/scripts/explainer/build_wisp_explainer_data.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    payload = json.loads((ROOT / 'outputs/sideproject_q5_inputs/q5_grid_paths.json').read_text(encoding='utf8'))
    cell = copy.deepcopy(payload['cells'][0])
    t, x = module.read_observations(cell, set())
    assert t.shape == tuple(json.loads(cell['export']['time_shape']))
    assert x.shape == tuple(json.loads(cell['export']['state_shape']))
    import numpy as np
    display = module.display_arrays(t, x=x)
    assert display['t'][0] == float(format(t[0], '.5g'))
    assert display['t'][-1] == float(format(t[-1], '.5g'))
    indices = np.unique(np.linspace(0, len(t)-1, min(module.DISPLAY_POINTS, len(t))).round().astype(int))
    np.testing.assert_allclose(display['x'], x[indices], rtol=5e-5, atol=0)
    cell['export']['time_sha256'] = '0' * 64  # Only the recorded hash is corrupted.
    with pytest.raises(ValueError, match='SHA-256 mismatch'):
        module.read_observations(cell, set())
    cell['export']['cell_dir'] = '../forbidden'
    with pytest.raises(ValueError, match='escapes'):
        module.read_observations(cell, set())
