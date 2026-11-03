"""WP-X8 source contract; the bilingual DOM harness checks actual interactions."""
import json
from pathlib import Path
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[2] / 'explainer/wisp'


def test_recorded_run_and_bilingual_work_page():
    live = json.loads((BASE/'data/live.json').read_text(encoding='utf8'))
    run = live['featured'][0]
    assert run['cell_id'] == live['teaching']['cell_id']
    assert len(run['path']) == 8
    assert run['chosen'] == 'path_004'
    assert [p['active_idxs'][0] for p in run['path']] == [
        [1], [1, 4], [2, 4], [2, 3], [2, 3, 5],
        [2, 3, 4, 5], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6]]
    assert all(c['curves'] for c in run['candidates'])
    soup = BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'), 'html.parser')
    page = soup.select_one('#p-solution')
    assert not soup.select('#solution-comparison, #solution-legend, #reader-equation')
    assert page.select_one('#work-cards') and page.select_one('#work-chart')
    assert len(page.select('button.icon-button')) == 3
    eye = soup.select_one('#challenge-solution')
    assert eye['data-i18n-aria-label'] == eye['data-i18n-title'] == 'x8_show'
    assert soup.select_one('#challenge-truth').has_attr('hidden')
    for lang in ('en', 'de'):
        table = json.loads((BASE/f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert all(table[node['data-i18n']] for node in page.select('[data-i18n]'))
        assert not any(k.startswith(('x7b_', 'x7c_', 'x7e_')) for k in table)
        assert not {'x4_solution', 'x4_idea', 'x6_yours'} & table.keys()


def test_fit_checks_both_eye_states_and_all_recorded_steps():
    source = (BASE/'src/pages.js').read_text(encoding='utf8')
    assert 'solutionShown:shown' in source and 'workStep:i' in source
    assert 'ok:variants.every(v=>v.ok)' in source
