"""Page-three display contracts; numerical and SVG checks use the real-record harness."""
import json
from pathlib import Path

from bs4 import BeautifulSoup

BASE = Path(__file__).resolve().parents[2] / 'explainer/wisp'


def test_chart_caption_and_axis_label_in_both_languages():
    soup = BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'), 'html.parser')
    page = soup.select_one('#p-solution')
    assert page.select_one('.solo-prediction [data-i18n="x9_windows"]')
    assert page.select_one('.page-content').contents[0]['data-i18n'] == 'x9_eyebrow'
    expected = {
        'de': ('Änderung von u', 'Gezeigt: Zeitabschnitte, die sich nicht überlappen. WISP rechnet mit allen Abschnitten, auch überlappenden und kürzeren.'),
        'en': ('change of u', 'Shown: windows that do not overlap. WISP computes with all windows, including overlapping and shorter ones.'),
    }
    for lang, (label, caption) in expected.items():
        table = json.loads((BASE/f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert table['x9_change'] == label
        assert table['x9_windows'] == caption
    css = (BASE/'src/pages.css').read_text(encoding='utf8')
    assert '.snapped #p-solution .page-content>.eyebrow{display:block}' in css
