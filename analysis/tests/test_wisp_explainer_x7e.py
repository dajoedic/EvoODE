"""WP-X7e polynomial, comparison and layout contracts; real DOM tests are bilingual."""
import importlib.util
import json
from pathlib import Path
import subprocess

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp/src'


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


