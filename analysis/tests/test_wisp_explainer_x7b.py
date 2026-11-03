"""WP-X7b contracts; animation, controls and scores also run in the bilingual DOM harness."""
import json
from pathlib import Path
import subprocess

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[2] / 'explainer/wisp'


def test_hook_and_removed_keys():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    assert not soup.select('#dish-replay, .hook-bridge, #challenge-reveal')
    for lang in ('de', 'en'):
        table = json.loads((BASE / f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert not {'x7_replay', 'x7_bridge', 'x6_reveal'} & table.keys()
        assert table['x7b_fit']


def test_navigation_keeps_only_nonsequential_links_and_pipeline_map():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    pages = soup.select('main > .page')
    for index, page in enumerate(pages[:-1]):
        assert not [a for a in page.select('a[href]') if a['href'] == '#' + pages[index + 1]['id'] and not a.find_parent(class_='pipeline-map')]
    assert soup.select_one('#p-headline a[href="#p-results"]')
    assert soup.select_one('#p-catalogue a[href="#p-challenge"]')
    assert len(soup.select('.pipeline-map a')) == 16


def test_icon_labels_and_single_grid_legend():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    for key in ('x7_structure_label', 'x7_parameter_label'):
        assert len(soup.select(f'[data-i18n="{key}"]')) == 1
    for id, key in (('play-reset', 'x6_reset'), ('challenge-hint', 'x6_hint')):
        button = soup.select_one('#' + id)
        assert not button.has_attr('data-i18n')
        assert button['data-i18n-aria-label'] == button['data-i18n-title'] == key
        assert button.select_one('svg[aria-hidden="true"] path')


def test_fit_rejects_uncomparable_grids_and_preserves_meter_definition():
    app = (BASE / 'src/app.js').read_text(encoding='utf8')
    functions = app[app.index('function observationR2('):app.index('let readerState=')]
    script = functions + r'''
const assert = require('assert');
assert.equal(observationR2([1,2,3],[1,2,3]),1);
assert.equal(observationR2([2,2,2],[1,2,3]),0);
assert.equal(observationR2([3,2,1],[1,2,3]),-3);
assert(Number.isNaN(observationR2([1,NaN,3],[1,2,3])));
assert.deepEqual(interpolateCurve([0,2,4],[1,5,9],[0,1,2,4]),[1,3,5,9]);
for(const t of [[0,0,4],[0,4,2],[0,NaN,4]])assert.equal(interpolateCurve(t,[1,5,9],[1]),null);
assert.equal(interpolateCurve([0,2],[1],[1]),null);
assert.equal(interpolateCurve([0,2],[1,5],[3]),null);
assert.equal(interpolateCurve([0,2],[1,5],[NaN]),null);
assert(Number.isNaN(interpolateCurve([0,2],[null,5],[1])[0]));
'''
    run = subprocess.run(['node', '-e', script], capture_output=True, text=True, timeout=20)
    assert run.returncode == 0, run.stdout + run.stderr
