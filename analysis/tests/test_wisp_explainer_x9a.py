"""First-step contracts, using the real teaching record and actual-page DOM harness."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp'


def test_first_step_numerical_gate_and_corrupt_record_rejection():
    command = ['node', str(ROOT/'analysis/scripts/explainer/check_wisp_work.cjs'), str(BASE)]
    run = subprocess.run(command, capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr
    parent = ROOT/'outputs/wisp_x9a'
    parent.mkdir(parents=True, exist_ok=True)
    temporary = parent/('bad_support_'+uuid.uuid4().hex)
    temporary.mkdir()
    try:
        (temporary/'src').mkdir()
        (temporary/'data').mkdir()
        for name in ('compute.js', 'app.js'):
            (temporary/'src'/name).write_bytes((BASE/'src'/name).read_bytes())
        live = json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
        live['featured'][0]['path'][0]['active_idxs'] = [[2]]
        (temporary/'data/live.json').write_text(json.dumps(live), encoding='utf8')
        run = subprocess.run([sys.executable, str(ROOT/'analysis/scripts/explainer/build_wisp_explainer_html_x2.py'),
                              '--base', str(temporary)], capture_output=True, text=True, timeout=30)
        assert run.returncode != 0
        assert 'Teaching path differs from recorded supports' in run.stderr
        assert not (temporary/'dist/wisp_explainer.html').exists()
    finally:
        shutil.rmtree(temporary)


def test_old_page_removed_and_new_page_translated():
    soup = BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'), 'html.parser')
    page = soup.select_one('#p-solution')
    assert page.select_one('#solo-bars') and page.select_one('#solo-chart')
    assert not page.select('[id^="work-"]')
    for lang in ('de', 'en'):
        table = json.loads((BASE/f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert all(table[n['data-i18n']] for n in page.select('[data-i18n]'))
        assert {k for k in table if k.startswith('x8')} == {'x8_show', 'x8_hide', 'x8_true'}
    for name in ('app.js', 'pages.css', 'pages.js'):
        text = (BASE/'src'/name).read_text(encoding='utf8')
        assert not any(token in text for token in ('WispWork', 'work-', 'workTrace', 'x8c_', 'x8d_'))
    assert all(n.get('data-claim') == 'review' for n in page.select('p'))
    eye = soup.select_one('#challenge-solution')
    assert eye['data-i18n-aria-label'] == eye['data-i18n-title'] == 'x8_show'
    assert soup.select_one('#challenge-truth').has_attr('hidden')


def test_fallback_shares_and_decimal_equations():
    script = r"""
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const base=process.argv[1],W=require(path.resolve(base,'src/compute.js'));
const source=fs.readFileSync(base+'/src/app.js','utf8'),live=JSON.parse(fs.readFileSync(base+'/data/live.json','utf8'));
for(const language of ['de','en']){
 const c={W,language,terms:['1','u','u²','u³','sin u','cos u']};vm.createContext(c);
 vm.runInContext(source.slice(source.indexOf('const soloDot='),source.indexOf('function initSolo(')),c);
 assert.equal(c.soloEquation({term:0,coefficient:10}),'du/dt = 10');
 assert.equal(c.soloEquation({term:0,coefficient:-10}),'du/dt = −10');
 for(const v of [-.0000275123,1.234567e-12,123456789,0]){
  const formatted=c.soloNumber(v);assert(!/[eE×]/.test(formatted));
  assert.equal(Number(formatted.replace('−','-').replace(',','.')),Number(v.toPrecision(3)));
 }
 for(const floor of [NaN,1,1.2]){
  const D=W.design(live.teaching.t,live.teaching.observed,live.windows),norm=D.b.reduce((s,v)=>s+v*v,0);
  c.W={...W,noiseFloor:()=>floor*norm};const m=c.soloModel(live.teaching.observed,live.teaching.t,live,live.featured[0]);
  assert(!m.normalized);m.blocks.forEach(b=>assert.equal(b.share,b.gain));
 }
}
"""
    run = subprocess.run(['node', '-e', script, str(BASE)], capture_output=True, text=True, timeout=30)
    assert run.returncode == 0, run.stdout + run.stderr


def test_fit_covers_all_six_blocks_and_retains_page_two_gates():
    source = (BASE/'src/pages.js').read_text(encoding='utf8')
    assert 'soloTerm:block.term' in source
    assert 'ok:variants.every(v=>v.ok)' in source
    assert 'rect.width<=container.width+1&&e.scrollWidth<=container.width+1' in source
    assert 'solutionShown:shown' in source
    assert "['fontFamily','fontSize','color'].every(k=>label[k]===caption[k])" in source
    assert 'solutionStyle.truthStroke>=2.5' in source
