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
    for page in result['pages']:
        if page['id']=='p-challenge':
            columns=page.get('columns')
            if not columns:raise ValueError('Missing challenge column bounding rects')
            aligned=all(abs(columns['left'][edge]-columns['right'][edge])<=2 for edge in ('top','bottom'))
            columns['ok']=aligned
            page['ok']=page['ok'] and aligned
    result['ok']=all(page['ok'] for page in result['pages'])
    return result

def edge_run(edge=EDGE):
    OUT.mkdir(parents=True,exist_ok=True);shots=OUT/'pages';shots.mkdir(exist_ok=True)
    deadline=time.monotonic()+840
    evidence={'checks':[],'screenshots':[],'errors':[]}
    offset=[0,0]
    def invoke(width,height,lang,extra,hash_value='',probe=False):
        if time.monotonic()>deadline:raise TimeoutError('Fit checker exceeded its 14-minute budget')
        url=(ROOT/'explainer/wisp/dist/wisp_explainer.html').as_uri()+f'?fitcheck=1&lang={lang}'+hash_value
        if probe:url=(OUT/'viewport_probe.html').as_uri()
        command=[str(edge),'--headless=new','--no-first-run','--no-default-browser-check',
                 '--disable-extensions','--disable-background-networking','--disable-sync',
                 '--force-device-scale-factor=1','--hide-scrollbars',f'--window-size={width+offset[0]},{height+offset[1]}',
                 '--user-data-dir='+str(OUT/'edge_fit_profile'),'--virtual-time-budget=20000',*extra,url]
        completed=subprocess.run(command,capture_output=True,encoding='utf8',errors='replace',timeout=min(35,max(1,deadline-time.monotonic())),creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        if completed.returncode:
            evidence['errors'].append({'command':command,'exit':completed.returncode,'stderr':completed.stderr[-6000:]})
            raise OSError(f'Edge headless exited {completed.returncode}: {completed.stderr[-600:]}')
        return completed.stdout
    code=0
    try:
        (OUT/'viewport_probe.html').write_text('<pre id="probe"></pre><script>document.getElementById("probe").textContent=innerWidth+","+innerHeight</script>',encoding='utf8')
        import re
        probe=invoke(1366,768,'en',['--dump-dom'],probe=True)
        measured=re.search(r'<pre id="probe">(\d+),(\d+)</pre>',probe)
        if not measured:raise ValueError('Viewport probe did not complete')
        offset[:]=[1366-int(measured[1]),768-int(measured[2])]
        evidence['browser_offset']=offset[:]
        for lang in ('en','de'):
            for width,height in ((1366,768),(1366,657)):
                for attempt in range(3):
                    dom=invoke(width,height,lang,['--dump-dom'])
                    try:result=parse_result(dom);break
                    except ValueError:
                        if attempt==2:raise
                (OUT/f'fit_{lang}_{height}.html').write_text(dom,encoding='utf8')
                result=parse_result(dom)
                if (result['width'],result['height'])!=(width,height):
                    raise ValueError(f"Viewport differs from requested CSS size: {result['width']}×{result['height']} vs {width}×{height}")
                if result['language']!=lang:raise ValueError('Wrong fit-check language')
                evidence['checks'].append(result)
        page_ids=[p['id'] for p in evidence['checks'][0]['pages']]
        if any([p['id'] for p in r['pages']]!=page_ids for r in evidence['checks']):raise ValueError('Page inventories differ')
        evidence['errors'].append('Edge fallback measures fit only; per-page screenshots require Playwright (Edge --screenshot deep links are unreliable).')
        code=1  # Playwright screenshots remain mandatory for full acceptance.
    except (OSError,subprocess.TimeoutExpired) as exc:
        evidence['errors'].append(str(exc));code=2
    except (ValueError,TimeoutError) as exc:
        evidence['errors'].append(str(exc));code=1
    evidence['exit']=code
    (OUT/'wp_x6_edge_fit.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(evidence if evidence['errors'] else {'exit':code,'checks':len(evidence['checks']),'screenshots':len(evidence['screenshots']),'overflow':[p for r in evidence['checks'] for p in r['pages'] if not p['ok']]},ensure_ascii=True))
    return code

def check_interactions(page, evidence):
    """Actual centre-pointer wheel routing, arrival visibility and reader labels."""
    import re
    page.add_init_script("window.WispVisibleChapters=['intro','later']")
    for lang in ('en','de'):
        url=(ROOT/'explainer/wisp/dist/wisp_explainer.html').as_uri()+f'?lang={lang}'
        page.set_viewport_size({'width':1366,'height':768})
        page.goto(url,wait_until='load')
        page.wait_for_function('window.WispSlides && WispSlides.nav')
        page.mouse.move(683,384)
        for n in range(1,6):
            page.evaluate('WispSlides.nav.go(0)')
            page.wait_for_timeout(850)
            for _ in range(n):
                page.mouse.wheel(0,500)
                page.wait_for_timeout(850)
            actual=page.evaluate('WispSlides.nav.index')
            if actual!=n:raise AssertionError(f'{lang}: {n} centre wheel gestures reached index {actual}')
            evidence.setdefault('wheel_checks',[]).append({'language':lang,'gestures':n,'page':actual+1})
        page.evaluate('WispSlides.nav.link("#p-headline")')
        # Inspect before another animation frame: no entrance animation may gate content.
        visible=page.locator('#headline-panel').evaluate("e=>getComputedStyle(e).opacity==='1' && e.querySelectorAll('.rate-chart').length>0 && [...e.querySelectorAll('*')].every(n=>getComputedStyle(n).animationName==='none')")
        if not visible:raise AssertionError('Headline gated by an entrance animation')
        texts=page.locator('body').evaluate("e=>{const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);const out=[];while(w.nextNode()){const p=w.currentNode.parentElement;if(!p.closest('script,style,[data-provenance],#provenance'))out.push(w.currentNode.textContent);}return out.join(' ');}")
        if re.search(r'raw_exact|pruned_exact|(?:generalization|reconstruction)_(?:arithmetic|variance_weighted)_hit',texts):raise AssertionError('Internal metric name in reader DOM')
        if '\ufffd' in texts or re.search(r'[^\W\d_]\?[^\W\d_]',texts):raise AssertionError('Broken reader encoding')


        page.evaluate('WispSlides.nav.link("#p-solution")')
        page.wait_for_timeout(850)
        bars=page.locator('#solo-bars button')
        if bars.count()!=6:raise AssertionError('Expected six single-block buttons')
        equations,lines=set(),set()
        for i in range(6):
            bars.nth(i).click()
            if bars.nth(i).get_attribute('aria-pressed')!='true':raise AssertionError('Selected block is not pressed')
            if page.locator('#solo-bars button[aria-pressed=true]').count()!=1:raise AssertionError('Selection is not unique')
            equations.add(page.locator('#solo-equation').inner_text())
            lines.add(page.locator('#solo-chart .series-model').get_attribute('d'))
        if len(equations)!=6 or len(lines)!=6:raise AssertionError('Block selection did not switch every equation and line')
        page.locator('#solo-bars button[data-term="0"]').click()
        constant=page.locator('#solo-equation').inner_text()
        if not re.fullmatch(r'du/dt = [\u2212-]?[0-9]+(?:[.,][0-9]+)?',constant):raise AssertionError('Constant equation has a trailing block')
        page.set_viewport_size({'width':390,'height':844})
        page.wait_for_timeout(300)
        fits=page.locator('#p-solution').evaluate("e=>document.documentElement.scrollWidth<=innerWidth && [...e.querySelectorAll('*')].filter(n=>!n.closest('[hidden]')).every(n=>{const r=n.getBoundingClientRect();return !r.width || (r.left>=0 && r.right<=innerWidth+1);})")
        if not fits:raise AssertionError('Phone page 3 has horizontal overflow')
        evidence.setdefault('single_block_checks',[]).append({'language':lang,'bars':6,'equations':len(equations),'lines':len(lines),'phone_width':390,'phone_ok':fits})


def check_chapter_interactions(page,evidence):
    """Delivered configuration: hidden pages, chapter keys, all block choices and sliders."""
    for lang in ('en','de'):
        page.set_viewport_size({'width':1366,'height':657})
        page.goto((ROOT/'explainer/wisp/dist/wisp_explainer.html').as_uri()+f'?lang={lang}',wait_until='load')
        page.wait_for_function('window.WispChapterOne && window.WispSlides?.nav')
        ids=page.evaluate('WispSlides.pages.map(p=>p.id)')
        expected=['p-hook','p-challenge','p-c1-data','p-c1-changes','p-c1-error-empty','p-c1-fit','p-c1-every','p-c1-noise','p-c1-percent','p-c1-solution']
        if ids!=expected:raise AssertionError(f'Incorrect delivered inventory: {ids}')
        for id in ('p-solution','p-headline','p-results','p-glossary'):
            page.evaluate('(id)=>WispSlides.nav.link("#"+id)',id)
            if page.evaluate('WispSlides.nav.index')!=0:raise AssertionError('Hidden link reachable')
        page.keyboard.press('ArrowRight');page.wait_for_timeout(850)
        if page.evaluate('WispSlides.nav.index')!=1:raise AssertionError('Right must advance one page')
        page.keyboard.press('ArrowRight');page.wait_for_timeout(850)
        if page.evaluate('WispSlides.nav.index')!=2:raise AssertionError('Right must cross into chapter one')
        if page.locator('.page-dots a:visible').count()!=8:raise AssertionError('Wrong sub-step dots')
        page.keyboard.press('ArrowRight');page.wait_for_timeout(850)
        page.locator('#c1-window').focus();page.keyboard.press('ArrowLeft')
        if page.evaluate('WispSlides.nav.index')!=3:raise AssertionError('Slider lost its arrow key')
        for id in expected[2:]:
            page.evaluate('(id)=>WispSlides.nav.link("#"+id)',id);page.wait_for_timeout(850)
            page.locator('body').click(position={'x':5,'y':5})
            page.keyboard.press('ArrowUp');page.wait_for_timeout(850)
            if page.evaluate('WispSlides.nav.index')!=0:raise AssertionError('Up must reach the intro chapter')
        page.keyboard.press('ArrowDown');page.wait_for_timeout(850)
        if page.evaluate('WispSlides.nav.index')!=2:raise AssertionError('Down must reach chapter one')
        for id in ('p-c1-every','p-c1-noise','p-c1-percent'):
            page.evaluate('(id)=>WispSlides.nav.link("#"+id)',id);page.wait_for_timeout(850)
            selector='#c1-visual-4 button' if id=='p-c1-every' else '.c1-chips button'
            for button in page.locator(selector).all():
                button.click()
                if button.get_attribute('aria-pressed')!='true':raise AssertionError('Block selection failed')
                if id=='p-c1-percent':
                    parts=page.locator('.c1-stack').evaluate('e=>JSON.parse(e.dataset.parts)')
                    if abs(sum(parts)-1)>1e-12:raise AssertionError('Stack does not sum to 100%')
        evidence.setdefault('chapter_checks',[]).append({'language':lang,'pages':ids,'block_choices':12})


def run(edge=EDGE):
    """Playwright supplies exact CSS viewports and reliable deep-link captures."""
    OUT.mkdir(parents=True,exist_ok=True)
    evidence={'checks':[],'screenshots':[],'errors':[]}
    deadline=time.monotonic()+840
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser=pw.chromium.launch(channel='msedge',headless=True)
            page=browser.new_page()
            check_interactions(page,evidence)
            page.close()
            page=browser.new_page()
            check_chapter_interactions(page,evidence)
            for lang in ('en','de'):
                for width,height in ((1366,768),(1366,657)):
                    if time.monotonic()>deadline:raise TimeoutError('14-minute budget exceeded')
                    page.set_viewport_size({'width':width,'height':height})
                    url=(ROOT/'explainer/wisp/dist/wisp_explainer.html').as_uri()+f'?fitcheck=1&lang={lang}'
                    for attempt in range(3):
                        page.goto(url,wait_until='load')
                        try:page.wait_for_selector('#fitcheck-result',state='attached',timeout=25000);break
                        except Exception:
                            if attempt==2:raise
                    result=parse_result(page.content())
                    if (result['width'],result['height'])!=(width,height):raise ValueError('Incorrect CSS viewport')
                    if result['language']!=lang:raise ValueError('Incorrect language')
                    evidence['checks'].append(result)
                    shots=OUT/'pages';shots.mkdir(exist_ok=True)
                    for record in result['pages']:
                        if time.monotonic()>deadline:raise TimeoutError('14-minute budget exceeded')
                        page.evaluate('(id)=>WispSlides.nav.link("#"+id)',record['id'])
                        path=shots/f"{lang}_{height}_{record['id']}.png"
                        page.screenshot(path=str(path))
                        evidence['screenshots'].append(str(path.relative_to(ROOT)))
            browser.close()
        code=0 if all(r['ok'] for r in evidence['checks']) else 1
    except (ImportError,OSError) as exc:
        evidence['errors'].append(str(exc));code=2
    except Exception as exc:
        evidence['errors'].append(str(exc));code=2 if not evidence['checks'] else 1
    if code==2:
        evidence['fallback_exit']=edge_run(edge)
    evidence['exit']=code
    (OUT/'wp_x6_fit.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'exit':code,'checks':len(evidence['checks']),'screenshots':len(evidence['screenshots']),'errors':evidence['errors'],'overflow':[p for r in evidence['checks'] for p in r['pages'] if not p['ok']]},ensure_ascii=True))
    return code

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--edge',type=Path,default=EDGE)
    raise SystemExit(run(parser.parse_args().edge))
