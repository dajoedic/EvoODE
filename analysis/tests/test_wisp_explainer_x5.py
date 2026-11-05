"""WP-X5 presentation contracts derived from the frozen exported records."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp'


def test_utf8_output_and_bilingual_strings():
    html = (BASE / 'dist/wisp_explainer.html').read_text(encoding='utf8')
    assert '\ufffd' not in html
    embedded = json.loads(re.search(r'<script id="wisp-data" type="application/json">(.*?)</script>', html, re.S)[1])
    for lang in ('en', 'de'):
        table = json.loads((BASE / f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        for key, value in table.items():
            assert not re.search(r'[^\W\d_]\?[^\W\d_]', value), (lang, key, value)
            assert embedded['live']['i18n'][lang][key] == value


def test_system_translation_coverage_and_frozen_inputs():
    records = json.loads((BASE / 'data/results.json').read_text(encoding='utf8'))['cells']
    for lang in ('en', 'de'):
        table = json.loads((BASE / f'src/i18n/{lang}.json').read_text(encoding='utf8'))
        assert all(table.get('system_' + str(c['system_id'])) for c in records)
    previous = json.loads((ROOT / 'outputs/wisp_x4/input_hashes.json').read_text(encoding='utf8'))
    for file, expected in previous.items():
        if Path(file).name in {"live.json", "manifest.json", "results.json"}:
            continue  # X19 extends Q7 evidence/provenance; their hashes have separate coverage.
        assert hashlib.sha256((ROOT / file).read_bytes()).hexdigest() == expected, file


def test_baseline_banner_matches_the_actual_headline_population():
    data = json.loads((BASE / 'data/results.json').read_text(encoding='utf8'))
    for stratum in ('dim1', 'dim2'):
        for method in ('sindy', 'weak_sindy', 'e_sindy'):
            for metric in ('raw_exact', 'pruned_exact', 'generalization_arithmetic_hit', 'generalization_variance_weighted_hit'):
                rows = [r for r in data['rates'] if r['stratum'] == stratum and r['method'] == method and r['metric'] == metric and float(r['sigma']) == .03 and str(r['rho']) != 'pooled' and float(r['rho']) == 0 and r['configuration'] != 'all_ten']
                assert len(rows) == 1
                assert rows[0]['numerator'] != ''
    en = json.loads((BASE / 'src/i18n/en.json').read_text(encoding='utf8'))
    assert 'one configuration per method' in en['x4_interim']


def test_browser_regression_is_part_of_fit_acceptance():
    source = (ROOT / 'analysis/scripts/explainer/check_wisp_explainer_fit.py').read_text(encoding='utf8')
    assert "channel='msedge'" in source
    assert 'check_interactions(page,evidence)' in source
    assert 'range(1,6)' in source and 'page.mouse.move(683,384)' in source
    assert 'animationName' in source and 'wheel_checks' in source
