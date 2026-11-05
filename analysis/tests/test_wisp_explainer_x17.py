"""Stopping presentation; all numerical inputs come from the real teaching record."""
import json
from pathlib import Path
import re
import subprocess

import numpy as np
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'explainer/wisp'
OUT = ROOT/'outputs/wp_x17'


def test_stopping_story_and_counterfactual_both_languages():
    soup = BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'), 'html.parser')
    assert len(soup.select('[data-chapter="two"]')) == 5
    assert not soup.select('#p-c2-all')
    four = soup.select('[data-chapter="four"]')
    assert [p['data-stage'] for p in four] == ['c4-'+n for n in ('question','noise','threshold','replay','path')]
    assert all(n.get('data-claim') == 'review' for p in four for n in p.select('h2,p,.eyebrow'))
    app = (BASE/'src/app.js').read_text(encoding='utf8')
    pages = (BASE/'src/pages.js').read_text(encoding='utf8')
    assert 'c2-all' not in app+pages
    assert "visibleChapters=['intro','one','two','three','four','five']" in pages
    assert "tr('x18_chapter')" in pages
    assert "'c4-replay':Array.from" in pages
    assert not any(not p.has_attr('hidden') for p in soup.select('[data-chapter="later"]'))
    tables = [json.loads((BASE/f'src/i18n/{lang}.json').read_text(encoding='utf8')) for lang in ('de','en')]
    keys = {k for k in tables[0] if k.startswith('x18_')}
    assert keys == {k for k in tables[1] if k.startswith('x18_')}
    for table in tables:
        assert all(table[k] and not re.search(r'\d', table[k]) for k in keys-{'x18_chapter'})
        assert not any(k.startswith('x16_') for k in table)
        assert '·' not in ''.join(table[k] for k in keys-{'x18_chapter'})
        assert 'BIC' not in ''.join(table[k] for k in keys)
    assert tables[0]['x17_forward'] == 'Ohne Aufräumen – so geht WISP nicht vor'
    assert tables[1]['x17_forward'] == 'Without clean-up – not what WISP does'
    # Chapter four goes through the established looping clock, including its end hold.
    assert '...threeStates,...fourStates' in app
    assert 'ms%(durations[current]+3000)' in app
    assert "if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)finish()" in app


def test_stopping_numbers_independently_from_observation_arrays():
    OUT.mkdir(parents=True,exist_ok=True)
    result = subprocess.run(['node',str(ROOT/'analysis/scripts/explainer/check_wisp_work.cjs'),str(BASE),str(OUT/'live_numbers.json')],capture_output=True,text=True,timeout=45)
    assert result.returncode == 0, result.stdout+result.stderr
    data = json.loads((OUT/'live_numbers.json').read_text(encoding='utf8'))['fourth']
    live = json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
    t = np.asarray(live['teaching']['t']); x = np.asarray(live['teaching']['observed'])
    # Independent local cubic projection, leverage correction, and moving average.
    squares=[]
    for i in range(len(t)):
        start=min(max(i-4,0),len(t)-9)
        z=t[start:start+9]-t[i]; z=z/max(abs(z))
        basis=np.array([z**p for p in range(4)]).T
        q=np.linalg.qr(basis)[0]; projection=q@q.T; j=i-start
        squares.append((x[i]-projection[j]@x[start:start+9])**2/(1-projection[j,j]))
    variance=np.array([np.mean(squares[max(0,i-10):min(len(t),i+11)]) for i in range(len(t))])
    np.testing.assert_allclose(data['variance'],variance,atol=1e-11,rtol=1e-10)
    phi=np.array([np.ones_like(x),x,x*x,x*x*x,np.sin(x),np.cos(x)]).T
    a=[]; b=[]; endpoints=[]
    for length in live['windows']:
        for start in range(len(t)-length):
            end=start+length
            a.append(np.sum(np.diff(t[start:end+1])[:,None]*(phi[start:end]+phi[start+1:end+1])/2,axis=0))
            b.append(x[end]-x[start]); endpoints.append((start,end))
    a=np.array(a); b=np.array(b); endpoints=np.array(endpoints)
    def fit(support):
        aa=a[:,support]; residual=b-aa@np.linalg.lstsq(aa,b,rcond=None)[0]
        return residual@residual
    def floor(support):
        total=np.sum(variance[endpoints[:,0]]+variance[endpoints[:,1]])
        if support:
            q=np.linalg.qr(a[:,support])[0]
            for column in q.T:
                projected=np.zeros(len(t))
                np.add.at(projected,endpoints[:,0],-column)
                np.add.at(projected,endpoints[:,1],column)
                total-=np.sum(projected**2*variance)
        return max(0,total)
    # Compute the quantile independently, instead of asserting an editorial constant.
    from statistics import NormalDist
    threshold=NormalDist().inv_cdf(.995)**2
    assert abs(data['threshold']-threshold)<.001
    assert data['threshold'] == live['featured'][0]['stop_reference']['threshold']
    assert data['supports'] == live['featured'][0]['stop_reference']['supports']
    assert len(data['supports']) == live['featured'][0]['stop_reference']['stop_step']
    assert data['supports'][:4] == [r['active_idxs'][0] and [j-1 for j in r['active_idxs'][0]] for r in live['featured'][0]['path'][:4]]
    for i,r in enumerate(data['rounds']):
        support=r['support']
        assert {c['term'] for c in r['blocks']} == set(range(a.shape[1]))-set(support)
        for block in r['blocks']:
            trial=sorted(support+[block['term']])
            gain=fit(support)-fit(trial); noise=floor(support)-floor(trial)
            np.testing.assert_allclose(block['gain'],gain,atol=1e-5,rtol=1e-8)
            np.testing.assert_allclose(block['noise'],noise,atol=1e-6,rtol=1e-8)
            np.testing.assert_allclose(block['ratio'],gain/noise,atol=1e-6,rtol=1e-8)
            assert block['passes'] == (gain/noise>=threshold)
        assert r['passes'] == (i<4)
    assert max(data['rounds'][-1]['blocks'],key=lambda c:c['ratio'])['term'] == 4


def test_scene_geometry_and_deterministic_seek_without_browser():
    run=subprocess.run(['node',str(ROOT/'analysis/scripts/explainer/check_wisp_stop_scene.cjs')],capture_output=True,text=True,timeout=45)
    assert run.returncode == 0,run.stdout+run.stderr
