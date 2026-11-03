"""WP-X7c layout contracts; live coefficients and scores run bilingually in the DOM harness."""
import json
from pathlib import Path
from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[2] / 'explainer/wisp'


def test_punchline_is_below_controls_in_left_column():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    left = soup.select_one('.challenge-grid > .challenge-parameters')
    assert left.select_one('.term-cards')
    assert len(left.select('.icon-button')) == 2
    punchline = left.select_one('[data-i18n="x6_punchline"]')
    assert punchline and punchline.find_previous_sibling()['id'] == 'challenge-hint'
    assert len(soup.select('[data-i18n="x6_punchline"]')) == 1


def test_solution_key_names_order_and_swatches():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    entries = soup.select('#solution-equations > li')
    assert [e['data-entry'] for e in entries] == ['data', 'reader', 'model', 'truth']
    assert len(entries[0].select('.measurement-dot')) == 3
    for entry in entries[1:]:
        assert entry.select_one('.curve-swatch .series-' + entry['data-entry'])
        assert entry.select_one('#solution-fit-' + entry['data-entry'])
    for lang, names in [('de', ['Messwerte', 'Deine Gleichung', 'WISP', 'Wahre Gleichung']), ('en', ['Measurements', 'Your equation', 'WISP', 'True equation'])]:
        table = json.loads((BASE / f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert [table[e.select_one('[data-i18n]')['data-i18n']] for e in entries] == names
        assert '{noise}' in table['x7c_noise']


def test_hook_has_full_width_illustration_without_external_media():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    figure = soup.select_one("#p-hook .dish-figure")
    assert [node.name for node in figure.children] == ["div", "figcaption"]
    assert figure.select_one("#dish-illustration")
    assert not soup.select('#p-hook video, #p-hook iframe')


def test_hook_has_no_video_or_placeholder_elements_or_i18n_keys():
    import re
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    hook = soup.select_one('#p-hook')
    forbidden = re.compile(r'video|placeholder|platzhalter|media.slot|x7c_media', re.I)
    assert not forbidden.search(str(hook))
    for lang in ('de', 'en'):
        table = json.loads((BASE / f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert 'x7c_media' not in table
        assert not any(forbidden.search(key) for key in table)
        for node in hook.select('*'):
            for name, key in node.attrs.items():
                if name.startswith('data-i18n'):
                    assert not forbidden.search(key + ' ' + table[key])
