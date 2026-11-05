"""Chapter-nine polish: real-row DOM checks and cutoff-checker regression cases."""
import json
from pathlib import Path
import subprocess
import sys

from bs4 import BeautifulSoup
import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'explainer/wisp'
sys.path.insert(0, str(ROOT / 'analysis/scripts/explainer'))
from check_wisp_explainer_fit import parse_result


@pytest.mark.parametrize('language', ['de', 'en'])
def test_wisp_chapter_nine_real_dom(language):
    soup = BeautifulSoup((BASE / 'dist/wisp_explainer.html').read_text(encoding='utf8'), 'html.parser')
    data = json.loads(soup.select_one('#wisp-data').string)

    def node(tag):
        return dict(tag=tag.name,
                    attrs={k: ' '.join(v) if isinstance(v, list) else v for k, v in tag.attrs.items()},
                    text=''.join(str(c) for c in tag.children if not getattr(c, 'name', None)) if tag.name not in ('script', 'style') else '',
                    children=[node(c) for c in tag.children if getattr(c, 'name', None)] if tag.name not in ('script', 'style') else [])

    out = ROOT / 'outputs/wp_x20b'
    out.mkdir(exist_ok=True)
    fixture = out / f'dom_{language}.json'
    fixture.write_text(json.dumps(dict(tree=node(soup.html), data=data, language=language, configuration='chapter9')), encoding='utf8')
    run = subprocess.run(['node', str(ROOT / 'analysis/tests/wisp_slides_dom.cjs'), str(BASE), str(fixture)],
                         capture_output=True, text=True, encoding='utf8', timeout=60)
    assert run.returncode == 0, run.stdout + run.stderr
    for i, name in enumerate(('count', 'clean', 'noise', 'original'), 1):
        page = soup.select_one('#p-c9-' + name)
        assert page.select_one(f'.eyebrow[data-i18n="x22_step_{i}"]')
        assert page.select_one('p.c9-lead[data-claim="review"]')
        assert not page.select_one('.c9-content[data-internal-scroll]')
    strings = json.loads((BASE / f'src/i18n/{language}.json').read_text(encoding='utf8'))
    assert 'σ = 0' in strings['x22_lead_clean'] and 'ρ = 0' in strings['x22_lead_clean']
    assert '?' not in strings['x22_lead_clean']


def test_wisp_cutoff_geometry_and_evidence_rejection():
    # Actual viewport/legend dimensions, with an explicit below-viewport mutation.
    script = r"""
const {contentOutside}=require(process.argv[1]),assert=require('assert');
for(const height of [768,657]){
 const bounds={top:0,bottom:height};
 const legend={left:100,right:1200,top:height-60,bottom:height-20,width:1100,height:40};
 assert(!contentOutside(legend,bounds,1366));
 assert(contentOutside({...legend,top:height-10,bottom:height+30},bounds,1366));
 // The same geometry on a page at a later document offset must also fail.
 assert(contentOutside({...legend,top:height*3-10,bottom:height*3+30},{top:height*2,bottom:height*3},1366));
}
"""
    subprocess.run(['node', '-e', script, str(BASE / 'src/pages.js')], check=True, timeout=30)
    sample = dict(selection=['dim1', '0.0'], labelOverlaps=[], clippedContent=[], overflow=[], ok=True)
    record = dict(id='p-c9-noise', variants=[sample], ok=True)

    def parse():
        return parse_result('<pre id="fitcheck-result">' + json.dumps(dict(pages=[record])) + '</pre>')

    assert parse()['ok']
    sample['clippedContent'] = ['c9-noise']
    assert not parse()['ok']
    sample['clippedContent'] = []
    sample['overflow'] = ['SPAN']
    assert not parse()['ok']
    sample['overflow'] = []
    sample['labelOverlaps'] = [['0.04', '0.05']]
    assert not parse()['ok']
    record['variants'] = []
    with pytest.raises(ValueError, match='condition samples'):
        parse()
