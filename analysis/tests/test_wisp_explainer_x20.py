"""Q7 result provenance and chapter-nine contracts, using actual aggregation rows."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp'
sys.path.insert(0, str(ROOT / 'analysis/scripts/explainer'))
import wisp_results_x20 as exporter


def data(name):
    return json.loads((BASE / 'data' / f'{name}.json').read_text(encoding='utf8'))


def test_q7_rows_and_provenance_are_copied():
    result, manifest = data('results'), data('manifest')
    assert result['schema_version'] == 2 and result['primary_method'] == 'Q7'
    assert result['rates'] == exporter.csv_rows(exporter.GRID / 'q7_rates.csv')
    assert [c['row'] for c in result['cells']] == [r for r in exporter.csv_rows(exporter.GRID / 'q7_units.csv') if r['size_rule'] == 'c']
    meta = json.loads((exporter.GRID / 'q7_run_metadata.json').read_text())
    assert result['provenance']['git_hash'] == meta['image'].rsplit(':', 1)[1]
    assert result['provenance']['status'] == 'interim'
    assert 'Q9' in result['provenance']['note']
    for path, sha in manifest['x20_inputs'].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == sha
    comparison = result['comparison']
    if exporter.legacy.COMPARISON.is_file():
        assert comparison['rates'] == exporter.csv_rows(exporter.legacy.COMPARISON)
    else:
        assert comparison['status'] == 'pending' and comparison['rates'] == []


def test_q7_curves_require_julia_and_reuse_identity():
    manifest = data('manifest')
    checks = {c['cell_id']: c for c in manifest['x20_display']['checks']}
    for cell in data('results')['cells']:
        if cell['curves']:
            assert manifest['x20_display']['present'] and checks[cell['row']['cell_id']]['passed']
        else:
            assert cell['unavailable']
    missing = [c for c in data('results')['cells'] if not c['row']['candidate_id']]
    assert len(missing) == manifest['x20_display']['no_model']
    for cell in missing:
        assert exporter.model_identity(cell['row']) is None
        assert cell['curves'] is None and 'no candidate' in cell['unavailable']
    # This fixture starts with a real chosen record; mutations are explicit.
    row = next(r for r in exporter.csv_rows(exporter.GRID / 'q7_units.csv') if r['size_rule'] == 'c')
    other = dict(row, candidate_id='renamed')
    assert exporter.model_identity(row) == exporter.model_identity(other)
    params = json.loads(row['params']); params[0] += .001
    other['params'] = json.dumps(params)
    assert exporter.model_identity(row) != exporter.model_identity(other)


def test_chapter_nine_mount_and_filter_no_pooling():
    soup = BeautifulSoup((BASE / 'src/index.html').read_text(encoding='utf8'), 'html.parser')
    pages = soup.select('[data-chapter="nine"]')
    assert [p['id'] for p in pages] == ['p-c9-count', 'p-c9-clean', 'p-c9-noise', 'p-c9-original', 'p-results', 'p-glossary']
    source = (BASE / 'src/app.js').read_text(encoding='utf8')
    function = source[source.index('function chapterNineRows('):source.index('function initResultsChapter(')]
    script = "const fs=require('fs'),assert=require('assert'),RESULTS=JSON.parse(fs.readFileSync(0,'utf8'));" + function + """
const rows=chapterNineRows(RESULTS.rates);
assert(rows.every(r=>r.rho!=='pooled'&&r.configuration!=='all_ten'));
const clean=chapterNineRows(RESULTS.rates,{sigma:0});
assert(clean.length>0);assert(clean.every(r=>+r.rho!==0));
for(const row of rows)assert(RESULTS.rates.includes(row));
for(const s of new Set(rows.map(r=>r.stratum)))for(const m of new Set(rows.map(r=>r.method)))
 for(const metric of ['raw_exact','reconstruction_variance_weighted_hit','generalization_variance_weighted_hit'])
 assert(rows.some(r=>r.stratum===s&&r.method===m&&r.metric===metric));
"""
    subprocess.run(['node', '-e', script], input=json.dumps(data('results')), text=True, check=True, timeout=30)
    julia = (ROOT / 'studies/explainer/export_wisp_display_trajectories.jl').read_text()
    assert '--q7-results' in julia and 'q7_results ? [chosen]' in julia
    assert 'reused_from' in julia and 'old_candidates_hash' in julia
