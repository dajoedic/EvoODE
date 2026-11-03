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


