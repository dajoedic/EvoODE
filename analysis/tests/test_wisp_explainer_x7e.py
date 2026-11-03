"""WP-X7e polynomial, comparison and layout contracts; real DOM tests are bilingual."""
import importlib.util
import json
from pathlib import Path
import subprocess

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp/src'


def test_polynomial_expander_restricts_grammar_and_expands_real_truth():
    app = (BASE/'app.js').read_text(encoding='utf8')
    parser = app[app.index('function expandTruthPolynomial'):app.index('function storedBlockCoefficients')]
    live = json.loads((BASE.parent/'data/live.json').read_text(encoding='utf8'))
    results = json.loads((BASE.parent/'data/results.json').read_text(encoding='utf8'))
    cell = next(c for c in results['cells'] if c['row']['cell_id'] == live['teaching']['cell_id'])
    script = parser + '''
const assert=require('assert');
assert.deepEqual(expandTruthPolynomial('2*(u+1)^3'),[2,6,6,2,0,0]);
assert.deepEqual(expandTruthPolynomial('-u^2+2e-3*u-1'),[-1,.002,-1,0,0,0]);
assert.deepEqual(expandTruthPolynomial('(u-u)*u^4'),[0,0,0,0,0,0]);
assert.deepEqual(expandTruthPolynomial('0'),[0,0,0,0,0,0]);
for(const value of ['sin(u)','u/2','v','u^4','u^-1','u^1.5','u^99','u+','(u','u)','u^2^3','alert(1)','1e999',''])assert.equal(expandTruthPolynomial(value),null,value);
'''
    # Independent expected expansion from the stored expression's numeric factors.
    import re
    rate, inverse_capacity = [float(x) for x in re.findall(r'\d+\.\d+', cell['truth'][0])]
    script += f"const real=expandTruthPolynomial({json.dumps(cell['truth'][0])}); assert(Math.abs(real[1]-{rate})<1e-12); assert(Math.abs(real[2]-({-rate*inverse_capacity}))<1e-12);"
    run = subprocess.run(['node','-e',script],capture_output=True,text=True,timeout=20)
    assert run.returncode == 0, run.stdout+run.stderr


def test_spinner_css_and_stretched_columns_are_measured():
    css = (BASE/'pages.css').read_text(encoding='utf8')
    for fragment in ('appearance:textfield','-moz-appearance:textfield','::-webkit-inner-spin-button','::-webkit-outer-spin-button','-webkit-appearance:none','.challenge-grid{align-items:stretch}', 'grid-template-rows:auto minmax(0,1fr) auto auto auto'):
        assert fragment in css
    js = (BASE/'pages.js').read_text(encoding='utf8')
    assert "page.querySelector('.challenge-parameters').getBoundingClientRect()" in js
    assert 'Math.abs(left.bottom-right.bottom)<=2' in js
    spec = importlib.util.spec_from_file_location('fit',ROOT/'analysis/scripts/explainer/check_wisp_explainer_fit.py')
    fit = importlib.util.module_from_spec(spec);spec.loader.exec_module(fit)
    for delta, expected in ((0,True),(2,True),(2.01,False)):
        record = dict(pages=[dict(id='p-challenge',ok=True,columns=dict(left=dict(top=0,bottom=400),right=dict(top=0,bottom=400+delta)))])
        parsed = fit.parse_result('<pre id="fitcheck-result">'+json.dumps(record)+'</pre>')
        assert parsed['ok'] is expected


def test_comparison_structure_and_responsive_legend():
    soup = BeautifulSoup((BASE/'index.html').read_text(encoding='utf8'),'html.parser')
    visual = soup.select_one('.solution-visual')
    assert visual.select_one('#solution-chart').find_next_sibling()['id'] == 'solution-legend'
    assert [row['data-entry'] for row in soup.select('#solution-legend li')] == ['data','reader','model','truth']
    assert [row['data-entry'] for row in soup.select('#solution-comparison tbody tr')] == ['truth','model','reader']
    assert [th.text for th in soup.select('#solution-comparison thead th')] == ['', '1','u','u²','u³','sin u','cos u','R²']
    assert len(soup.select('#solution-comparison [data-block]')) == 18
    assert soup.select_one('.term-comparison')['data-internal-scroll'] == 'true'
    assert len(soup.select('#solution-equations .math')) == 3
    assert soup.select_one('[data-i18n="x7e_caption"]')['data-claim'] == 'review'
