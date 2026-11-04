"""Chapter-two contracts; live numeric checks use the actual teaching record."""
import json
from pathlib import Path
import re
import subprocess

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp'


def test_wisp_two_pages_and_bilingual_claims():
    soup = BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'), 'html.parser')
    pages = soup.select('main > .page')
    two = soup.select('[data-chapter="two"]')
    names = ['standing', 'residual', 'joint', 'error', 'solution']
    assert [p['id'] for p in two] == ['p-c2-'+s for s in names]
    start = next(i for i, p in enumerate(pages) if p['id'] == 'p-c1-solution')+1
    assert pages[start:start+5] == two
    assert [p['data-stage'] for p in two] == ['c2-'+s for s in names]
    assert "visibleChapters=['intro','one','two']" in (BASE/'src/pages.js').read_text(encoding='utf8')
    for page in two:
        assert all(n.get('data-claim') == 'review' for n in page.select('h2,p,footer,.eyebrow'))
    tables = [json.loads((BASE/f'src/i18n/{lang}.json').read_text(encoding='utf8')) for lang in ['de', 'en']]
    keys = {k for k in tables[0] if k.startswith('x13_')}
    assert keys == {k for k in tables[1] if k.startswith('x13_')}
    for table in tables:
        assert all(table[k] for k in keys)
        assert all(n['data-i18n'] in keys for page in two for n in page.select('[data-i18n]'))
        for key in keys-{'x13_closing'}:
            assert not re.search(r'falsch|richtig|\bwrong\b|\bcorrect\b|\bright\b|swap|austausch', table[key], re.I)
        # Scientific values are live substitutions; prose includes no numeric literal.
        assert not any(re.search(r'\d', table[k]) for k in keys-{'x13_chapter'})
    assert tables[0]['x13_closing'] == 'Ob das schon die richtige Gleichung ist — und was WISP als Nächstes tut — zeigt das nächste Kapitel.'
    assert 'together' in tables[1]['x13_text_2']


def test_wisp_two_real_record_and_guard():
    live = json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
    assert live['featured'][0]['cell_id'] == live['teaching']['cell_id']
    record = live['featured'][0]['path'][1]
    assert record['active_idxs'][0] == record['equations'][0]['basis_indices']
    source = (BASE/'src/app.js').read_text(encoding='utf8')
    model = source[source.index('function secondModel('):source.index('function secondNumber(')]
    assert 'W.path(t,x,config)' in model
    assert 'record.active_idxs' in model
    assert "throw Error('Teaching step-2 path differs from recorded supports')" in model
    scene = source[source.index('function secondScene('):source.index('let current=null,frame=0')]
    assert 'two.record.equations[0].coefficients' in scene
    for coefficient in record['equations'][0]['coefficients']:
        assert str(coefficient) not in model+scene
    run = subprocess.run(['node', str(ROOT/'analysis/scripts/explainer/check_wisp_work.cjs'), str(BASE)],
                         capture_output=True, text=True, timeout=45)
    assert run.returncode == 0, run.stdout+run.stderr
    assert 'five joint refits' in run.stdout


def test_wisp_two_fit_sampling():
    source = (BASE/'src/pages.js').read_text(encoding='utf8')
    for name in ['standing', 'residual', 'joint', 'error', 'solution']:
        assert "'c2-"+name+"':" in source
    assert "page.dataset.chapter==='two'||" in source
    assert "['percent','c2-joint'].includes(page.dataset.stage)" in source
