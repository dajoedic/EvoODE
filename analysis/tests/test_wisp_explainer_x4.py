"""WP-X4 source and headline contract against the unchanged Q5 CSV."""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'explainer/wisp'

def test_headline_selected_rows_match_original_csv():
    source=(BASE/'src/app.js').read_text(encoding='utf8')
    function=source[source.index('function headlineRows('):source.index('const headline=headlineRows')]
    results=json.loads((BASE/'data/results.json').read_text(encoding='utf8'))
    script="const fs=require('fs'),RESULTS=JSON.parse(fs.readFileSync(0,'utf8'));"+function+"process.stdout.write(JSON.stringify(headlineRows(RESULTS.rates)));"
    run=subprocess.run(['node','-e',script],input=json.dumps(results),capture_output=True,text=True,check=True,timeout=30)
    with (ROOT/'analysis/data/sideproject_residual_growth/q5_grid/q5_rates.csv').open(encoding='utf8',newline='') as file:
        expected=[r for r in csv.DictReader(file) if r['stratum'] in ('dim1','dim2') and float(r['sigma'])==.03 and r['rho']!='pooled' and float(r['rho'])==0 and r['metric'] in ('raw_exact','pruned_exact','generalization_arithmetic_hit','generalization_variance_weighted_hit') and ((r['method']=='Q5' and r['configuration']=='c') or (r['method'] in ('sindy','weak_sindy','e_sindy') and r['configuration']!='all_ten'))]
    assert json.loads(run.stdout)==expected
    assert {r['stratum'] for r in expected}=={'dim1','dim2'}

def test_sections_and_reader_strings():
    soup=BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'),'html.parser')
    pages=soup.select('main > .page')
    assert len(pages)==35
    assert len({p['data-section'] for p in pages})==len(pages)
    assert [p['id'] for p in pages[:4]]==['p-hook','p-challenge','p-c1-data','p-c1-slope']
    assert all(len(p.select(':scope > .page-content'))==1 for p in pages)
    import re
    for lang in ('en','de'):
        table=json.loads((BASE/'src/i18n'/f'{lang}.json').read_text(encoding='utf8'))
        assert not any(re.search(r'sys\d{4}_',s) for s in table.values())
    assert not soup.select('#p-guess, [data-guess]')
    assert soup.select('#p-challenge #term-cards')
    assert soup.select('dialog[data-internal-scroll]')

def test_assembly_rebuild_is_byte_identical():
    command=[sys.executable,str(ROOT/'analysis/scripts/explainer/build_wisp_explainer_html_x2.py')]
    hashes=[]
    for _ in range(2):
        subprocess.run(command,capture_output=True,text=True,check=True,timeout=45)
        hashes.append(hashlib.sha256((BASE/'dist/wisp_explainer.html').read_bytes()).hexdigest())
    assert hashes[0]==hashes[1]
    out=ROOT/'outputs/wisp_x4/rebuild.json';out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({'byte_identical':True,'sha256':hashes[0],'html_bytes':(BASE/'dist/wisp_explainer.html').stat().st_size},indent=2),encoding='utf8')
