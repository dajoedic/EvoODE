"""X19b provenance and mounted presentation contracts, based on real Q5/Q7 artifacts."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'explainer/wisp'
sys.path.insert(0,str(ROOT/'analysis/scripts/explainer'))
import build_wisp_explainer_data as exporter


def test_campaign_identity_comes_from_real_run_metadata():
    metadata=json.loads((exporter.GRID/'q5_run_metadata.json').read_text(encoding='utf8'))
    expected='354106398d5e67ffa72c237e2ba83e3feeb25b31'
    assert exporter.source_identity(metadata)==expected
    assert 'evoode:'+expected in (ROOT/'k8s/sideproject_q5_job.yaml').read_text(encoding='utf8')
    # The real metadata has no git_hash field: the canonical source paths carry it.
    assert 'git_hash' not in metadata
    source=Path(exporter.__file__).read_text(encoding='utf8')
    assert 'identity = source_identity(metadata)' in source
    assert 'head_hash()' not in source
    broken=copy.deepcopy(metadata)
    broken['result_files'][0]=broken['result_files'][0].replace(expected,'0'*40)
    with pytest.raises(ValueError,match='conflicting'):exporter.source_identity(broken)
    broken['result_files']=[]
    with pytest.raises(ValueError,match='conflicting'):exporter.source_identity(broken)


def test_frozen_results_restored_and_source_manifest_separate():
    results=json.loads((BASE/'data/results.json').read_text(encoding='utf8'))
    assert results['primary_method']=='Q7' and results['provenance']['protocol']=='Q7'
    manifest=json.loads((BASE/'data/manifest.json').read_text(encoding='utf8'))
    metadata=json.loads((exporter.GRID/'q5_run_metadata.json').read_text(encoding='utf8'))
    assert manifest['git_hash']==exporter.source_identity(metadata)


def test_new_stages_and_fit_samples_are_mounted():
    from bs4 import BeautifulSoup
    soup=BeautifulSoup((BASE/'src/index.html').read_text(encoding='utf8'),'html.parser')
    pages=soup.select('.x21-page')
    assert len(pages)==15
    assert all(p.select_one('.eyebrow[data-example-eye]') for p in pages)
    assert all(p.select_one('.x21-panel') for p in pages)
    assert soup.select_one('#x21-stage')
    markup=(BASE/'src/index.html').read_text(encoding='utf8')
    assert markup.index('id="x21-stage"')<markup.index('<!--APP-->')
    script=(BASE/'src/pages.js').read_text(encoding='utf8')
    for assertion in ['stageFits','rawNames','labelOverlaps','2999,3000,3800,5999,6000,7500,8999']:
        assert assertion in script
    app=(BASE/'src/app.js').read_text(encoding='utf8')
    assert 'x21_truth_after_stop' in app
    assert 'xTicks:[0,20,40,60,80]' in app
    assert "name(e,j)" in app
