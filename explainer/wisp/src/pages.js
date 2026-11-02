/* Full-screen presentation only. No numerical search or result contract changes. */
(function(root){
 'use strict';
 const steps=['data','weak','frols','foba','stop','fit','bic','test'];
 function fallback(width,height,reduced){return width<760||height<560||reduced;}
 function controller(ids,initial,show){
  let index=Math.max(0,ids.indexOf(initial));
  return {get index(){return index;},go(value,push=true){index=Math.max(0,Math.min(ids.length-1,value));show(index,push);return ids[index];},observe(value){index=Math.max(0,Math.min(ids.length-1,value));show(index,false,false);},next(){return this.go(index+1);},previous(){return this.go(index-1);},link(hash){const i=ids.indexOf(hash.replace(/^#/,''));if(i>=0)this.go(i,false);}};
 }
 function protectedTarget(target){return !!target?.closest?.('input,select,textarea,button,a,[contenteditable],#window-chart,[data-internal-scroll],.matrix,.code-list,details');}
 function inputAction(event,{active=true,dragging=false}={}){
  if(!active||dragging||protectedTarget(event.target))return 0;
  if(event.type==='keydown')return ['ArrowDown','PageDown',' '].includes(event.key)?(event.shiftKey?-1:1):['ArrowUp','PageUp'].includes(event.key)?-1:0;
  return Math.sign(event.deltaY||0);
 }
 function wheelGate(){let last=-Infinity,locked=0;return (now,delta)=>{const quiet=now-last>220;last=now;if(quiet&&now>=locked&&Math.abs(delta)>2){locked=now+650;return Math.sign(delta);}return 0;};}
 function stepState(pages,index){return steps.map(step=>({step,active:pages[index].dataset.step===step}));}
 const api={steps,fallback,controller,protectedTarget,inputAction,wheelGate,stepState};
 if(typeof module!=='undefined')module.exports=api;
 root.WispSlides=api;
 if(typeof document==='undefined')return;
 const main=document.querySelector('main');
 const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e;};
 const translate=key=>tr('x3_'+key);
 // Each featured cell gets its own large pair of curve panels. Long path evidence
 // is retained in an explicitly bounded, internally scrolling disclosure.
 const holder=document.getElementById('p-featured');
 const articles=[...document.querySelectorAll('#featured-stories > article')];
 articles.forEach((article,i)=>{
  const page=make('section',null,'page featured-page');page.id='p-featured-'+i;page.dataset.step='test';page.dataset.section='generalization';
  const content=make('div',null,'page-content'),text=make('div',null,'featured-text');
  const pair=article.querySelector('.two-plots');
  const children=[...article.children];let evidence=null;
  children.forEach(child=>{if(child===pair)return;if(child.tagName==='H4'&&!evidence){evidence=make('details');evidence.append(make('summary',child.textContent));text.append(evidence);}if(evidence)evidence.append(child);else text.append(child);});
  content.append(text,pair);page.append(content);holder.before(page);
 });
 holder.remove();
 // The data entry card is placed before the catalogue, after the motivation.
 const dataPage=make('section',null,'page');dataPage.id='p-data-intro';dataPage.dataset.step='data';dataPage.dataset.section='catalogue';
 const dataContent=make('div',null,'page-content');dataContent.append(make('h2',translate('data')),make('p',translate('data_io')),make('p',translate('data_sentence')));dataPage.append(dataContent);
 document.getElementById('p-catalogue').before(dataPage);
 document.getElementById('p-play').before(document.getElementById('p-term-controls'));
 // Do not hide recorded FoBa evidence behind a collapsed disclosure by default.
 document.querySelector('#p-backward-record details').open=true;
 const pages=[...main.querySelectorAll(':scope > .page')];
 pages.forEach(page=>{if(!page.querySelector('h1,h2,h3'))page.querySelector('.page-content').prepend(make('h2',page.dataset.step?translate(page.dataset.step):document.querySelector('#p-'+page.dataset.section+' h2')?.textContent||tr('h006')));});
 const app=document.querySelector('#p-results .page-content');
 const filters=make('div',null,'results-filters'),panels=make('div',null,'results-panels');
 const strata=document.getElementById('strata'),drill=document.querySelector('#p-results .drill');
 [strata,drill].forEach(panel=>{panel.dataset.internalScroll='true';panel.tabIndex=0;panels.append(panel);});
 [...app.children].forEach(child=>filters.append(child));app.append(filters,panels);
 filters.querySelectorAll('details').forEach(detail=>{detail.dataset.internalScroll='true';});
 // Recap is tied only to the stored running example and the existing live path.
 const example=featured.find(f=>f.roles.includes('running'))||featured[0];
 const candidate=example?.candidates.find(c=>c.row.candidate_id===example.chosen);
 const result=RESULTS.cells.find(c=>c.row.cell_id===example?.cell_id);
 const outcomes={data:example?.cell_id,weak:document.getElementById('matrix-size').textContent,
  frols:example?.path.map(p=>p.active_idxs.map(eq=>eq.map(i=>result?.terms[i-1]).join(', ')).join(' / ')).join(' → '),
  foba:example?.path.map((p,i)=>{const previous=example.path[i-1];return previous?previous.active_idxs.flatMap((eq,j)=>eq.filter(k=>!p.active_idxs[j].includes(k)).map(k=>result?.terms[k-1])):[];}).flat().join(', ')||tr('j262'),
  stop:example?tr('x3_recorded_end',{v0:example.path.length,v1:LIVE.cap}):tr('j153'),
  fit:example?.candidates.map(c=>c.row.candidate_id).join(', '),bic:candidate?candidate.row.candidate_id+' · BIC '+fmt(candidate.bic,7):tr('j153'),
  test:result?['arithmetic','variance_weighted'].map(w=>tr('curve_scores',{v0:weightLabel(w),v1:fmt(result.row['reconstruction_r2_'+w],7),v2:fmt(result.row['generalization_r2_'+w],7)})).join(' · '):tr('j153')};
 // The long support path has a dedicated bounded detail, not tiny recap text.
 document.querySelectorAll('[data-outcome]').forEach(e=>{e.textContent=outcomes[e.dataset.outcome]||tr('j153');e.tabIndex=0;e.dataset.internalScroll='true';});
 const bar=document.getElementById('pipeline-bar');bar.setAttribute('aria-label','WISP');
 steps.forEach(step=>{const a=make('a',translate(step));a.href='#p-'+step+'-intro';a.dataset.step=step;bar.append(a);});
 const dots=make('nav',null,'page-dots');dots.setAttribute('aria-label',tr('h150'));document.body.append(dots);
 const dotButtons=pages.map((page,i)=>{const a=make('a');a.href='#'+page.id;a.title=(page.dataset.step?translate(page.dataset.step)+' · ':'')+page.querySelector('h1,h2,h3').textContent;a.setAttribute('aria-label',a.title);dots.append(a);return a;});
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 const fitcheck=new URL(location.href).searchParams.has('fitcheck');
 let snapped=false,dragging=false,touch=null,scrollTimer;const wheel=wheelGate();
 function updateMode(){snapped=fitcheck||!fallback(innerWidth,innerHeight,reduced.matches);document.documentElement.classList.toggle('snapped',snapped);}
 updateMode();
 function show(i,push,scroll=true){const page=pages[i];pages.forEach((p,j)=>p.classList.toggle('active',j===i));dotButtons.forEach((a,j)=>{if(j===i)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  bar.hidden=!page.dataset.step;const state=stepState(pages,i);bar.querySelectorAll('a').forEach(a=>{const active=state.find(s=>s.step===a.dataset.step).active;a.classList.toggle('current',active);if(active)a.setAttribute('aria-current','step');else a.removeAttribute('aria-current');});
  if(push&&location.hash!=='#'+page.id){const url=new URL(location.href);url.hash=page.id;history.pushState(null,'',url);}
  if(scroll)page.scrollIntoView({behavior:'instant',block:'start'});
 }
 const nav=controller(pages.map(p=>p.id),location.hash.slice(1),show);api.nav=nav;api.pages=pages;
 function link(event){const a=event.target.closest('a[href^="#p-"]');if(!a)return;const i=pages.findIndex(p=>p.id===a.hash.slice(1));if(i<0)return;event.preventDefault();nav.go(i);}
 document.addEventListener('click',link);
 window.addEventListener('popstate',()=>nav.link(location.hash));window.addEventListener('hashchange',()=>nav.link(location.hash));
 window.addEventListener('resize',()=>{updateMode();nav.go(nav.index,false);});reduced.addEventListener('change',updateMode);
 document.addEventListener('pointerdown',e=>{dragging=protectedTarget(e.target);},true);
 window.addEventListener('pointerup',()=>{dragging=false;});window.addEventListener('pointercancel',()=>{dragging=false;});
 window.addEventListener('keydown',e=>{const direction=inputAction(e,{active:snapped,dragging});if(direction){e.preventDefault();if(!e.repeat)nav.go(nav.index+direction);}});
 window.addEventListener('wheel',e=>{if(!snapped)return;if(protectedTarget(e.target)||dragging){if(!e.target.closest('[data-internal-scroll],.matrix,.code-list,details'))e.preventDefault();return;}e.preventDefault();const direction=wheel(performance.now(),e.deltaY);if(direction)nav.go(nav.index+direction);
 },{passive:false});
 window.addEventListener('touchstart',e=>{touch=snapped&&!protectedTarget(e.target)&&!dragging?{y:e.touches[0].clientY,x:e.touches[0].clientX}:null;},{passive:true});
 window.addEventListener('touchmove',e=>{if(snapped&&(touch||(!e.target.closest('[data-internal-scroll],.matrix,.code-list,details')&&protectedTarget(e.target))))e.preventDefault();},{passive:false});
 window.addEventListener('touchend',e=>{if(touch){const dy=touch.y-e.changedTouches[0].clientY,dx=touch.x-e.changedTouches[0].clientX;if(Math.abs(dy)>60&&Math.abs(dy)>Math.abs(dx))nav.go(nav.index+Math.sign(dy));touch=null;}});
 // Native scrolling in continuous mode updates the visible step and deep link.
 window.addEventListener('scroll',()=>{if(snapped)return;clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>{const nearest=pages.reduce((best,p,i)=>Math.abs(p.getBoundingClientRect().top)<Math.abs(pages[best].getBoundingClientRect().top)?i:best,0);if(nearest!==nav.index){nav.observe(nearest);const url=new URL(location.href);url.hash=pages[nearest].id;history.replaceState(null,'',url);}},120);},{passive:true});
 nav.go(nav.index,false);
 async function measure(){
  document.documentElement.classList.add('fit-measuring');
  await document.fonts.ready;
  // KaTeX is optional; wait for its load/error before measuring either rendering.
  const katexScript=document.querySelector('script[src]');
  if(katexScript&&!window.katex)await Promise.race([new Promise(resolve=>{katexScript.addEventListener('load',resolve,{once:true});katexScript.addEventListener('error',resolve,{once:true});}),new Promise(resolve=>setTimeout(resolve,1800))]);
  window.typesetAll?.();await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  const records=pages.map(page=>{const content=page.querySelector('.page-content'),rect=content.getBoundingClientRect(),bounds=page.getBoundingClientRect();
   const overflow=[];
   content.querySelectorAll('*').forEach(e=>{if(e.parentElement?.closest('[data-internal-scroll],details:not([open])'))return;const r=e.getBoundingClientRect();if(r.width&&r.height&&(r.bottom>bounds.bottom-12||r.right>innerWidth-24||r.left<0))overflow.push(e.id||e.tagName);});
   return {id:page.id,section:page.dataset.section,step:page.dataset.step,contentHeight:Math.ceil(Math.max(content.scrollHeight,rect.height)),availableHeight:Math.floor(innerHeight-112),viewportHeight:innerHeight,overflow,ok:content.scrollHeight<=innerHeight-112&&overflow.length===0};
  });
  const pre=make('pre',JSON.stringify({ok:records.every(r=>r.ok),language:document.documentElement.lang,width:innerWidth,height:innerHeight,pages:records}));pre.id='fitcheck-result';document.body.append(pre);
 }
 if(fitcheck)measure();
})(typeof window!=='undefined'?window:globalThis);
