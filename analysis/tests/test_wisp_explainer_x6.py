"""Opening challenge contracts; live behavior runs in the bilingual DOM harness."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp'


def test_challenge_is_second_in_both_languages_and_catalogue_refers_back():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    pages = soup.select('main > .page')
    assert len(pages) == 53
    assert pages[1]['id'] == 'p-challenge'
    assert pages[2]['id'] == 'p-c1-data'
    for lang in ('en', 'de'):
        table = json.loads((BASE / f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert table[pages[1].select_one('h2')['data-i18n']]
        assert all(table[f'x6_hint{n}'] for n in range(1, 4))
        assert table['x6_catalogue']
    assert not soup.select_one('#challenge-reveal')
    assert not soup.select_one('#reader-equation')
    assert soup.select_one('#p-catalogue a[href="#p-challenge"]')
    assert not soup.select('#p-guess, [data-guess], #p-catalogue #term-cards, #p-catalogue #play-chart')


def test_challenge_uses_the_running_measurements_and_keeps_numerical_inputs_frozen():
    live = json.loads((BASE / 'data/live.json').read_text(encoding='utf8'))
    results = json.loads((BASE / 'data/results.json').read_text(encoding='utf8'))
    cell = next(c for c in results['cells'] if c['row']['cell_id'] == live['teaching']['cell_id'])
    assert live['teaching']['t'] == cell['observed']['t']
    assert live['teaching']['observed'] == [row[0] for row in cell['observed']['x']]
    assert live['teaching']['sigma'] == .03
    import hashlib
    expected = json.loads((ROOT / 'outputs/wisp_x4/input_hashes.json').read_text(encoding='utf8'))
    assert all(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha for path, sha in expected.items())
