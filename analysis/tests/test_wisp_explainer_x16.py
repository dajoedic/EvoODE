"""Chapter-three presentation contracts derived from the actual teaching export."""
import json
from pathlib import Path
import re
import subprocess

import numpy as np
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp'


def test_chapter_three_bilingual_story_and_gates():
    soup = BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'), 'html.parser')
    pages = soup.select('[data-chapter="three"]')
    names = ['standing', 'probe', 'threshold', 'linear', 'quadratic', 'compare', 'next']
    assert [p['data-stage'] for p in pages] == ['c3-'+s for s in names]
    assert all(n.get('data-claim') == 'review' for p in pages for n in p.select('h2,h3,p,.eyebrow'))
    assert pages[2].select_one('[data-more]') and pages[2].select_one('dialog')
    assert not any(p.get('data-chapter') == 'later' and not p.has_attr('hidden') for p in soup.select('.page'))
    tables = [json.loads((BASE/f'src/i18n/{lang}.json').read_text(encoding='utf8')) for lang in ('de', 'en')]
    keys = {k for k in tables[0] if k.startswith('x17_')}
    assert keys == {k for k in tables[1] if k.startswith('x17_')}
    for table in tables:
        assert all(table[k] for k in keys)
        assert not any(re.search(r'\d|½', table[k]) for k in keys-{'x17_chapter'})
        assert not re.search(r'\bBIC\b|Q7|trajectory', ' '.join(table[k] for k in keys), re.I)
    assert json.loads((BASE/'src/gates.json').read_text()) == dict(stop='significance', initial_state='pending', coefficient_bound='pending')
    samples = (BASE/'src/pages.js').read_text(encoding='utf8')
    for name in names:
        assert "'c3-"+name+"':[" in samples
    assert "page.dataset.chapter==='three'||" in samples


def test_live_removal_costs_and_recorded_supports_independently():
    output = ROOT/'outputs/wp_x16/unit_numbers.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(['node', str(ROOT/'analysis/scripts/explainer/check_wisp_work.cjs'), str(BASE), str(output)], capture_output=True, text=True, timeout=45)
    assert run.returncode == 0, run.stdout+run.stderr
    report = json.loads(output.read_text(encoding='utf8'))
    live = json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
    featured = live['featured'][0]
    assert featured['cell_id'] == live['teaching']['cell_id']
    records = featured['path'][:4]
    assert [r['candidate_id'] for r in records] == [f'path_{i:03}' for i in range(1,5)]
    assert [r['origin'] for r in records] == ['addition', 'addition', 'removal', 'removal']
    # Independently integrate the real observation arrays, then solve the full design
    # with NumPy SVD (the page uses its compressed JS design).
    t = np.array(live['teaching']['t']); x = np.array(live['teaching']['observed'])
    phi = np.array([np.ones_like(x), x, x*x, x*x*x, np.sin(x), np.cos(x)]).T
    a, b = [], []
    for length in live['windows']:
        for start in range(len(t)-length):
            end = start+length
            a.append(np.sum(np.diff(t[start:end+1])[:,None]*(phi[start:end]+phi[start+1:end+1])/2, axis=0))
            b.append(x[end]-x[start])
    a, b = np.array(a), np.array(b)
    norm = b@b; explainable = 1-report['floor']
    def fit(support):
        aa = a[:,support]
        coefficients = np.linalg.lstsq(aa, b, rcond=None)[0]
        residual = b-aa@coefficients
        return residual@residual
    for i, r in enumerate(report['third']['rounds']):
        assert r['after']['support'] == [j-1 for j in records[i]['active_idxs'][0]]
        gain = (fit(r['before']['support'])-fit(r['added']['support']))/norm/explainable
        np.testing.assert_allclose(r['gain'], gain, atol=1e-10, rtol=1e-9)
        np.testing.assert_allclose(r['threshold'], live['backward_fraction']*gain, atol=1e-10)
        assert len(r['probes']) == len(r['removed'])+1
        for probe in r['probes']:
            support = probe['model']['support']
            for c in probe['costs']:
                cost = (fit([j for j in support if j != c['term']])-fit(support))/norm/explainable
                np.testing.assert_allclose(c['cost'], cost, atol=1e-10, rtol=1e-8)
            assert all(c['cost'] >= r['threshold'] for c in probe['costs']) if probe['removed'] is None else min(probe['costs'], key=lambda c: c['cost'])['term'] == probe['removed']
    assert report['third']['truth'] == [j-1 for j in featured['truth_support'][0]]
    assert report['third']['next']['term'] == 4
    final = report['third']['rounds'][-1]['after']['support']
    next_gain = (fit(final)-fit(sorted(final+[4])))/norm/explainable
    np.testing.assert_allclose(report['third']['next']['gain'], next_gain, atol=1e-10)
