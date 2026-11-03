"""WP-X7 opening content contracts; animation behavior runs in the real-page harness."""
import json
from pathlib import Path
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[2] / 'explainer/wisp'


def test_hook_bilingual_history_and_illustration_only():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    hook = soup.select_one('#p-hook')
    assert len(soup.select('main > .page')) == 26
    assert len(hook.select('.history-timeline > li')) == 5
    assert [n.text for n in hook.select('.history-timeline small')[:4]] == ['1609–1687', '1838', '1925–26', '1952']
    assert not hook.select('[data-tex], .math, #problem-chart')
    assert hook.select_one('#dish-illustration')
    assert not hook.select_one('a[href="#p-challenge"]')
    for lang in ('de', 'en'):
        table = json.loads((BASE / f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert not {'x4_problem', 'x4_why'} & table.keys()
        assert all(table[node['data-i18n']] for node in hook.select('[data-i18n]'))
        assert all(hook.select_one(f'[data-i18n="x7_station{i}"]') for i in range(1, 6))
        assert 'Illustration' in table['x7_caption']


def test_challenge_framing_has_emphasis_and_dynamic_noise():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    deck = soup.select_one('#p-challenge .challenge-deck')
    assert [n['data-i18n'] for n in deck.select('strong')] == ['x7_structure', 'x7_parameters']
    app = (BASE / 'src/app.js').read_text(encoding='utf8')
    assert "tr('x7_challenge_start',{noise:pct(teaching.sigma)})" in app
    for key in ('x7_structure_label', 'x7_parameter_label'):
        assert soup.select_one(f'[data-i18n="{key}"]')
