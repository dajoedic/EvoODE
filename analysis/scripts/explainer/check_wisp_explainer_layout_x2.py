"""Isolated headless Chrome layout checks for the locally assembled page."""
import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request
import websocket
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/wisp_explainer_checks/x2_layout'
OUT.mkdir(parents=True,exist_ok=True)
profile=OUT/'chrome_profile'
process=subprocess.Popen([r'C:\Program Files\Google\Chrome\Application\chrome.exe','--headless=new','--remote-debugging-port=0','--remote-allow-origins=*','--no-first-run','--no-default-browser-check','--disable-extensions','--disable-background-networking','--disable-sync','--user-data-dir='+str(profile),'about:blank'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
ws=None
try:
    deadline=time.monotonic()+30
    while not (profile/'DevToolsActivePort').exists():
        if time.monotonic()>deadline:raise RuntimeError('Headless Chrome did not start')
        time.sleep(.1)
    port=(profile/'DevToolsActivePort').read_text().splitlines()[0]
    tabs=json.load(urllib.request.urlopen('http://127.0.0.1:'+port+'/json'))
    ws=websocket.create_connection(tabs[0]['webSocketDebuggerUrl'],timeout=20)
    count=0
    def call(method,params=None):
        global count
        count+=1;ws.send(json.dumps(dict(id=count,method=method,params=params or {})))
        while True:
            response=json.loads(ws.recv())
            if response.get('id')==count:
                if 'error' in response:raise RuntimeError(response['error'])
                return response.get('result',{})
    def evaluate(code):
        result=call('Runtime.evaluate',dict(expression=code,returnByValue=True))
        if 'exceptionDetails' in result:raise RuntimeError(result['exceptionDetails'])
        return result['result'].get('value')
    call('Page.enable');call('Runtime.enable')
    reports=[]
    for lang in ('en','de'):
        for width in (360,1280):
            call('Emulation.setDeviceMetricsOverride',dict(width=width,height=900,deviceScaleFactor=1,mobile=False))
            call('Page.navigate',dict(url=(ROOT/'explainer/wisp/dist/wisp_explainer.html').as_uri()+'?lang='+lang))
            deadline=time.monotonic()+40
            while not evaluate("!!window.WispPage && document.documentElement.lang === '"+lang+"'"):
                if time.monotonic()>deadline:raise RuntimeError('Page initialization timed out')
                time.sleep(.1)
            result=evaluate(r'''(()=>({lang:document.documentElement.lang,width:innerWidth,scrollWidth:document.documentElement.scrollWidth,
              figures:[...document.querySelectorAll('figure,.panel,.chart')].map(e=>{const r=e.getBoundingClientRect();return {id:e.id||e.tagName,left:r.left,right:r.right,width:r.width};}),
              overflow:[...document.querySelectorAll('body *')].filter(e=>!['SCRIPT','STYLE','PATH','g','path'].includes(e.tagName)).filter(e=>{const r=e.getBoundingClientRect();return r.width&& (r.left<-.5||r.right>innerWidth+.5);}).map(e=>({tag:e.tagName,id:e.id,text:e.textContent.slice(0,100)})),
              emptyTranslations:[...document.querySelectorAll('[data-i18n]')].filter(e=>!e.textContent.trim()).map(e=>e.dataset.i18n)
            }))()''')
            reports.append(result)
            # Capture every narrative figure for visual review, at both sizes/languages.
            for section in ('hook','growth','stopping','selection','generalization','results'):
                evaluate("document.getElementById('"+section+"').scrollIntoView()")
                shot=call('Page.captureScreenshot',dict(format='png',captureBeyondViewport=False))
                (OUT/f'{lang}_{width}_{section}.png').write_bytes(base64.b64decode(shot['data']))
    (OUT/'layout.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps([dict(lang=r['lang'],width=r['width'],scrollWidth=r['scrollWidth'],overflow=len(r['overflow']),empty=len(r['emptyTranslations'])) for r in reports]))
    assert all(r['scrollWidth']<=r['width'] and not r['overflow'] and not r['emptyTranslations'] for r in reports)
finally:
    if ws:ws.close()
    process.terminate()
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:process.kill()
