"""Check every full-screen page in Edge and save EN/DE page screenshots.

Exit 0: all four viewport/language combinations fit and screenshots exist.
Exit 1: overflow, initialization failure or an incomplete screenshot set.
Exit 2: Edge cannot be launched in this environment. All evidence is retained.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/wisp_explainer_checks'
EDGE=Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')

class FitResult(HTMLParser):
    def __init__(self):
        super().__init__();self.inside=False;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='pre' and dict(attrs).get('id')=='fitcheck-result':self.inside=True
    def handle_data(self,data):
        if self.inside:self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=='pre':self.inside=False

def parse_result(dom):
    parser=FitResult();parser.feed(dom)
    if not parser.parts:raise ValueError('No fitcheck-result: page initialization did not finish')
    result=json.loads(''.join(parser.parts))
    if not result.get('pages'):raise ValueError('Fit check returned no pages')
    if any(not p['id'].startswith('p-') for p in result['pages']):raise ValueError('Invalid page identifier')
    return result

def run(edge=EDGE):
    OUT.mkdir(parents=True,exist_ok=True);shots=OUT/'pages';shots.mkdir(exist_ok=True)
    deadline=time.monotonic()+840
    evidence={'checks':[],'screenshots':[],'errors':[]}
    def invoke(width,height,lang,extra,hash_value=''):
        if time.monotonic()>deadline:raise TimeoutError('Fit checker exceeded its 14-minute budget')
        url=(ROOT/'explainer/wisp/dist/wisp_explainer.html').as_uri()+f'?fitcheck=1&lang={lang}'+hash_value
        command=[str(edge),'--headless=new','--no-first-run','--no-default-browser-check',
                 '--disable-extensions','--disable-background-networking','--disable-sync',
                 '--force-device-scale-factor=1','--hide-scrollbars',f'--window-size={width},{height}',
                 '--user-data-dir='+str(OUT/'edge_fit_profile'),'--virtual-time-budget=7000',*extra,url]
        completed=subprocess.run(command,capture_output=True,encoding='utf8',errors='replace',timeout=min(35,max(1,deadline-time.monotonic())),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if completed.returncode:
            evidence['errors'].append({'command':command,'exit':completed.returncode,'stderr':completed.stderr[-6000:]})
            raise OSError(f'Edge headless exited {completed.returncode}: {completed.stderr[-600:]}')
        return completed.stdout
    code=0
    try:
        for lang in ('en','de'):
            for width,height in ((1366,768),(1366,657)):
                dom=invoke(width,height,lang,['--dump-dom'])
                (OUT/f'fit_{lang}_{height}.html').write_text(dom,encoding='utf8')
                result=parse_result(dom)
                if (result['width'],result['height'])!=(width,height):
                    raise ValueError(f"Viewport differs from requested CSS size: {result['width']}×{result['height']} vs {width}×{height}")
                if result['language']!=lang:raise ValueError('Wrong fit-check language')
                evidence['checks'].append(result)
        page_ids=[p['id'] for p in evidence['checks'][0]['pages']]
        if any([p['id'] for p in r['pages']]!=page_ids for r in evidence['checks']):raise ValueError('Page inventories differ')
        for lang in ('en','de'):
            for page_id in page_ids:
                path=shots/f'{lang}_{page_id}.png'
                # An old image must not make an unsuccessful capture look successful.
                path.unlink(missing_ok=True)
                invoke(1366,768,lang,['--screenshot='+str(path)],'#'+page_id)
                if not path.is_file() or path.stat().st_size<100:raise ValueError(f'Missing screenshot: {path}')
                evidence['screenshots'].append(str(path.relative_to(ROOT)))
        code=0 if all(r['ok'] for r in evidence['checks']) else 1
    except (OSError,subprocess.TimeoutExpired) as exc:
        evidence['errors'].append(str(exc));code=2
    except (ValueError,TimeoutError) as exc:
        evidence['errors'].append(str(exc));code=1
    evidence['exit']=code
    (OUT/'wp_x3_fit.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(evidence if evidence['errors'] else {'exit':code,'checks':len(evidence['checks']),'screenshots':len(evidence['screenshots']),'overflow':[p for r in evidence['checks'] for p in r['pages'] if not p['ok']]},ensure_ascii=False))
    return code

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--edge',type=Path,default=EDGE)
    raise SystemExit(run(parser.parse_args().edge))
