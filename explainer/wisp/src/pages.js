/* Full-screen presentation only. No numerical search or result contract changes. */
(function(root){
 'use strict';
 // Delivered chapter configuration. Tests may override it before initialization.
 const visibleChapters=['intro','one','two','three','four','five'];
 function visiblePages(pages,configuration=visibleChapters){return pages.filter(p=>configuration.includes(p.dataset.chapter));}
 function chapterTarget(pages,index,direction){const chapters=[...new Set(pages.map(p=>p.dataset.chapter))],current=chapters.indexOf(pages[index].dataset.chapter),next=Math.max(0,Math.min(chapters.length-1,current+direction));return pages.findIndex(p=>p.dataset.chapter===chapters[next]);}
 const steps=['data','weak','frols','foba','stop','fit','bic','test'];
 function fallback(width,height,reduced){return width<760||height<560||reduced;}
 function controller(ids,initial,show){
  let index=Math.max(0,ids.indexOf(initial));
  return {get index(){return index;},go(value,push=true){index=Math.max(0,Math.min(ids.length-1,value));show(index,push);return ids[index];},observe(value){index=Math.max(0,Math.min(ids.length-1,value));show(index,false,false);},next(){return this.go(index+1);},previous(){return this.go(index-1);},link(hash){const i=ids.indexOf(hash.replace(/^#/,''));if(i>=0)this.go(i,false);}};
 }
 function protectedTarget(target){return !!target?.closest?.('input,select,textarea,button,a,[contenteditable],#window-chart,[data-internal-scroll],.matrix,.code-list,details,dialog');}
 function inputAction(event,{active=true,dragging=false}={}){
  if(!active||dragging||protectedTarget(event.target))return 0;
  if(event.type==='keydown')return ['ArrowDown','PageDown',' '].includes(event.key)?(event.shiftKey?-1:1):['ArrowUp','PageUp'].includes(event.key)?-1:0;
  return Math.sign(event.deltaY||0);
 }
 function wheelGate(){let last=-Infinity,locked=0;return (now,delta)=>{const quiet=now-last>220;last=now;if(quiet&&now>=locked&&Math.abs(delta)>2){locked=now+650;return Math.sign(delta);}return 0;};}
 function stepState(pages,index){return steps.map(step=>({step,active:pages[index].dataset.step===step}));}
 const api={visibleChapters,visiblePages,chapterTarget,steps,fallback,controller,protectedTarget,inputAction,wheelGate,stepState};
 if(typeof module!=='undefined')module.exports=api;
 root.WispSlides=api;
 if(typeof document==='undefined')return;
 const main=document.querySelector('main');
 const make=(tag,text,cls)=>{const e=document.createElement(tag);if(text)e.textContent=text;if(cls)e.className=cls;return e;};
 const translate=key=>tr('x3_'+key);
 // One featured story at a time; its secondary evidence shares the existing drawer.
 const stories=document.getElementById('featured-stories'),storyParent=stories.parentElement;
 const storyTabs=make('nav',null,'story-tabs');storyTabs.setAttribute('role','tablist');stories.before(storyTabs);
 const articles=[...stories.children],drawer=storyParent.querySelector('dialog');
 articles.forEach((article,i)=>{const button=make('button',systemName(RESULTS.cells.find(c=>c.row.cell_id===featured[i].cell_id)));button.setAttribute('role','tab');storyTabs.append(button);
  const plot=article.querySelector('.two-plots');
  const componentPlots=panel=>[...panel.children].filter(curve=>curve.querySelector('svg.chart'));
  const components=Math.max(...[...plot.children].map(panel=>componentPlots(panel).length));
  if(components>1){const controls=make('nav',null,'component-tabs');controls.setAttribute('role','tablist');plot.before(controls);
   for(let component=0;component<components;component++){const choice=make('button','u'+(component+1));choice.setAttribute('role','tab');controls.append(choice);const select=()=>{[...plot.children].forEach(panel=>componentPlots(panel).forEach((curve,j)=>curve.hidden=j!==component));[...controls.children].forEach((tab,j)=>tab.setAttribute('aria-selected',String(j===component)));};choice.addEventListener('click',select);}
   [...plot.children].forEach(panel=>componentPlots(panel).forEach((curve,j)=>curve.hidden=j!==0));controls.children[0].setAttribute('aria-selected','true');
  }
  const detail=make('div');[...article.children].filter(e=>e!==plot&&!e.classList.contains('component-tabs')&&e.tagName!=='H3').forEach(e=>detail.append(e));drawer.append(detail);
  const scores=make('p');const cell=RESULTS.cells.find(c=>c.row.cell_id===featured[i].cell_id);scores.textContent=['arithmetic','variance_weighted'].map(w=>weightLabel(w)+': R² '+fmt(cell.row['generalization_r2_'+w],4)).join(' · ');article.append(scores);
  if(['arithmetic','variance_weighted'].some(w=>+cell.row['generalization_r2_'+w]<0)){const explanation=make('p',tr('x5_negative'));explanation.dataset.claim='review';article.append(explanation);}
  const select=()=>{articles.forEach((a,j)=>a.hidden=j!==i);[...storyTabs.children].forEach((b,j)=>b.setAttribute('aria-selected',String(j===i)));};button.addEventListener('click',select);
 });articles.forEach((a,i)=>a.hidden=i!==0);storyTabs.children[0]?.setAttribute('aria-selected','true');
 // Secondary explanations remain available in the single More drawer.
 for(const [id,selector] of [['p-test-intro','[data-i18n="x3_test_sentence"]'],['p-weak-intro','figure > .caption,figure > figcaption'],['p-frols-intro','[data-i18n="x3_frols_sentence"]']]){const page=document.getElementById(id),drawer=page.querySelector('dialog');page.querySelectorAll(selector).forEach(node=>drawer.append(node));}
 const allPages=[...main.querySelectorAll(':scope > .page')];
 const configuration=root.WispVisibleChapters||visibleChapters;
 const pages=visiblePages(allPages,configuration);allPages.forEach(p=>p.hidden=!pages.includes(p));
 document.querySelectorAll('a[href^="#p-"]').forEach(a=>{a.hidden=!pages.some(p=>a.hash==='#'+p.id);});
 pages.forEach(page=>{if(!page.querySelector('h1,h2,h3'))page.querySelector('.page-content').prepend(make('h2',page.dataset.step?translate(page.dataset.step):document.querySelector('#p-'+page.dataset.section+' h2')?.textContent||tr('h006')));});
 const app=document.querySelector('#p-results .page-content');
 const filters=make('div',null,'results-filters'),panels=make('div',null,'results-panels');
 const strata=document.getElementById('strata'),drill=document.querySelector('#p-results .drill');
 [strata,drill].forEach(panel=>{panel.dataset.internalScroll='true';panel.tabIndex=0;panels.append(panel);});
 [...app.children].forEach(child=>filters.append(child));app.append(filters,panels);
 filters.querySelectorAll('details').forEach(detail=>{detail.dataset.internalScroll='true';});
 const tabs=make('nav',null,'result-tabs');tabs.setAttribute('role','tablist');
 const overview=make('div');overview.id='results-overview';overview.dataset.internalScroll='true';overview.append(make('p',tr('x5_range')));const overviewContent=make('div');overview.append(overviewContent);panels.append(overview);
 function overviewDraw(){overviewContent.replaceChildren();overviewContent.className='overview-grid';
  const rows=resultRates.filter(r=>axesMatch(r)&&+r.sigma===+document.getElementById('result-sigma').value&&String(r.rho)===document.getElementById('result-rho').value&&r.configuration!=='all_ten');
  // Extra axes remain separate even when the filter is All.
  const groups=new Map();for(const row of rows){const key=[stratumLabel(row.stratum),...axes.map(a=>a.label+': '+(row[a.key]??tr('unspecified')))].join(' · ');if(!groups.has(key))groups.set(key,[]);groups.get(key).push(row);}
  for(const [key,values] of groups){const card=make('article');card.append(make('h3',key.replaceAll('_',' ')));rateChart(card,values);overviewContent.append(card);}
 }
 ['result-sigma','result-rho','result-weight',...axes.map(a=>'axis-'+a.key)].forEach(id=>document.getElementById(id).addEventListener('change',overviewDraw));overviewDraw();
 const tabPanels=[overview,strata,drill];['x4_overview','x4_condition','x4_system'].forEach((key,i)=>{const button=make('button',tr(key));button.setAttribute('role','tab');button.addEventListener('click',()=>selectTab(i));tabs.append(button);});
 function selectTab(index){tabPanels.forEach((panel,i)=>panel.hidden=i!==index);[...tabs.children].forEach((button,i)=>button.setAttribute('aria-selected',String(i===index)));}
 app.insertBefore?app.insertBefore(tabs,panels):app.append(tabs);selectTab(0);
 // Recap is tied only to the stored running example and the existing live path.
 const example=featured.find(f=>f.roles.includes('running'))||featured[0];
 const candidate=example?.candidates.find(c=>c.row.candidate_id===example.chosen);
 const result=RESULTS.cells.find(c=>c.row.cell_id===example?.cell_id);
 const outcomes={data:cellName(example?.cell_id),weak:document.getElementById('matrix-size').textContent,
  frols:example?.path.map(p=>p.active_idxs.map(eq=>eq.map(i=>result?.terms[i-1]).join(', ')).join(' / ')).join(' → '),
  foba:example?.path.map((p,i)=>{const previous=example.path[i-1];return previous?previous.active_idxs.flatMap((eq,j)=>eq.filter(k=>!p.active_idxs[j].includes(k)).map(k=>result?.terms[k-1])):[];}).flat().join(', ')||tr('j262'),
  stop:example?tr('x3_recorded_end',{v0:example.path.length,v1:LIVE.cap}):tr('j153'),
  fit:example?.candidates.map(c=>c.row.candidate_id).join(', '),bic:candidate?candidate.row.candidate_id+' · BIC '+fmt(candidate.bic,7):tr('j153'),
  test:result?['arithmetic','variance_weighted'].map(w=>tr('curve_scores',{v0:weightLabel(w),v1:fmt(result.row['reconstruction_r2_'+w],7),v2:fmt(result.row['generalization_r2_'+w],7)})).join(' · '):tr('j153')};
 // The long support path has a dedicated bounded detail, not tiny recap text.
 document.querySelectorAll('[data-outcome]').forEach(e=>{e.textContent=outcomes[e.dataset.outcome]||tr('j153');e.tabIndex=0;e.dataset.internalScroll='true';});
 const progress=document.getElementById('chapter-progress'),title=document.getElementById('masthead-title');
 const introTitle=title.textContent;
 const dots=make('nav',null,'page-dots');dots.setAttribute('aria-label',tr('h150'));document.body.append(dots);
 const dotButtons=pages.map((page,i)=>{const a=make('a');a.href='#'+page.id;a.title=(page.dataset.step?translate(page.dataset.step)+' · ':'')+page.querySelector('h1,h2,h3').textContent;a.setAttribute('aria-label',a.title);dots.append(a);return a;});
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 const fitcheck=new URL(location.href).searchParams.has('fitcheck');
 let snapped=false,dragging=false,selectOpen=false,touch=null,scrollTimer;const wheel=wheelGate();
 function updateMode(){snapped=fitcheck||!fallback(innerWidth,innerHeight,reduced.matches);document.documentElement.classList.toggle('snapped',snapped);}
 updateMode();
 let initialized=false,animation=0,animatingUntil=0;
 function smoothTo(target){cancelAnimationFrame(animation);const from=window.scrollY,start=performance.now();animatingUntil=start+720;
  function frame(now){const t=Math.min(1,(now-start)/720),ease=t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;window.scrollTo(0,from+(target-from)*ease);if(t<1)animation=requestAnimationFrame(frame);}
  animation=requestAnimationFrame(frame);
 }
 function show(i,push,scroll=true){const page=pages[i];pages.forEach((p,j)=>p.classList.toggle('active',j===i));dotButtons.forEach((a,j)=>{if(j===i)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  dotButtons.forEach((a,j)=>a.hidden=pages[j].dataset.chapter!==page.dataset.chapter);
  const chapterPages=pages.filter(p=>p.dataset.chapter===page.dataset.chapter),position=chapterPages.indexOf(page)+1;
  title.textContent=page.dataset.chapter==='five'?tr('x19_chapter'):page.dataset.chapter==='four'?tr('x18_chapter'):page.dataset.chapter==='three'?tr('x17_chapter'):page.dataset.chapter==='two'?tr('x13_chapter'):page.dataset.chapter==='one'?tr('x12c_chapter'):introTitle;
  title.href='#'+chapterPages[0].id;title.classList.toggle('chapter-indicator',['one','two','three','four','five'].includes(page.dataset.chapter));
  title.setAttribute('aria-label',title.textContent);
  progress.setAttribute('aria-valuenow',position);progress.setAttribute('aria-valuemax',chapterPages.length);
  progress.setAttribute('aria-label',tr('x10_eye',{i:position,n:chapterPages.length}));
  progress.querySelector('span').style.width=(100*position/chapterPages.length)+'%';
  if(push&&location.hash!=='#'+page.id){const url=new URL(location.href);url.hash=page.id;history.pushState(null,'',url);}
  window.WispChapterStory?.enter(page.dataset.stage);
  if(scroll){if(snapped&&!fitcheck&&initialized&&!reduced.matches)smoothTo(page.offsetTop);else page.scrollIntoView({behavior:'instant',block:'start'});}
 }
 const nav=controller(pages.map(p=>p.id),location.hash.slice(1),show);api.nav=nav;api.pages=pages;
 function link(event){const a=event.target.closest('a[href^="#p-"]');if(!a)return;const i=pages.findIndex(p=>p.id===a.hash.slice(1));event.preventDefault();if(i<0)return;nav.go(i);}
 document.addEventListener('click',link);
 window.addEventListener('popstate',()=>nav.link(location.hash));window.addEventListener('hashchange',()=>nav.link(location.hash));
 window.addEventListener('resize',()=>{updateMode();nav.go(nav.index,false);});reduced.addEventListener('change',updateMode);
 document.addEventListener('pointerdown',e=>{dragging=!!e.target.closest('input[type=range],#window-chart,[data-drag]');if(e.target.closest('select'))selectOpen=!selectOpen;else selectOpen=false;},true);
 document.addEventListener('change',()=>{selectOpen=false;},true);
 document.addEventListener('focusout',()=>{selectOpen=false;},true);
 document.addEventListener('keydown',e=>{if(e.target.closest('select')){if(['Escape','Enter','Tab'].includes(e.key))selectOpen=false;else if(e.key===' '||e.key==='F4'||e.altKey&&e.key==='ArrowDown')selectOpen=true;}},true);
 function scrollRoom(target,delta){for(let node=target;node&&node!==document.body;node=node.parentElement){const overflow=typeof getComputedStyle==='function'?getComputedStyle(node).overflowY:'';if(/auto|scroll/.test(overflow)&&node.scrollHeight>node.clientHeight+1&&((delta>0&&node.scrollTop+node.clientHeight<node.scrollHeight-1)||(delta<0&&node.scrollTop>0)))return true;}return false;}

 window.addEventListener('pointerup',()=>{dragging=false;});window.addEventListener('pointercancel',()=>{dragging=false;});
 window.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]'))return;const direction=inputAction(e,{active:snapped,dragging});if(direction){e.preventDefault();if(performance.now()<animatingUntil)return;if(!e.repeat)nav.go(nav.index+direction);}});
 window.addEventListener('wheel',e=>{if(!snapped)return;if(dragging||selectOpen){e.preventDefault();return;}if(scrollRoom(e.target,e.deltaY))return;e.preventDefault();const direction=wheel(performance.now(),e.deltaY);if(direction&&performance.now()>=animatingUntil)nav.go(nav.index+direction);
 },{passive:false});
 window.addEventListener('touchstart',e=>{touch=snapped&&!document.querySelector('dialog[open]')&&!protectedTarget(e.target)&&!dragging?{y:e.touches[0].clientY,x:e.touches[0].clientX}:null;},{passive:true});
 window.addEventListener('touchmove',e=>{if(document.querySelector('dialog[open]'))return;if(snapped&&(touch||(!e.target.closest('[data-internal-scroll],.matrix,.code-list,details')&&protectedTarget(e.target))))e.preventDefault();},{passive:false});
 window.addEventListener('touchend',e=>{if(touch&&performance.now()>=animatingUntil){const dy=touch.y-e.changedTouches[0].clientY,dx=touch.x-e.changedTouches[0].clientX;if(Math.abs(dy)>60&&Math.abs(dy)>Math.abs(dx))nav.go(nav.index+Math.sign(dy));touch=null;}});
 // Native scrolling in continuous mode updates the visible step and deep link.
 window.addEventListener('scroll',()=>{if(snapped)return;clearTimeout(scrollTimer);scrollTimer=setTimeout(()=>{const nearest=pages.reduce((best,p,i)=>Math.abs(p.getBoundingClientRect().top)<Math.abs(pages[best].getBoundingClientRect().top)?i:best,0);if(nearest!==nav.index){nav.observe(nearest);const url=new URL(location.href);url.hash=pages[nearest].id;history.replaceState(null,'',url);}},120);},{passive:true});
 nav.go(nav.index,false);if(location.hash.startsWith('#p-')&&!pages.some(p=>'#'+p.id===location.hash)){const url=new URL(location.href);url.hash=pages[0].id;history.replaceState(null,'',url);}initialized=true;
 async function measure(){
  document.documentElement.classList.add('fit-measuring');
  await document.fonts.ready;
  // KaTeX is optional; wait for its load/error before measuring either rendering.
  const katexScript=document.querySelector('script[src]');
  if(katexScript&&!window.katex)await Promise.race([new Promise(resolve=>{katexScript.addEventListener('load',resolve,{once:true});katexScript.addEventListener('error',resolve,{once:true});}),new Promise(resolve=>setTimeout(resolve,1800))]);
  window.typesetAll?.();await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  function readPage(page){const content=page.querySelector('.page-content'),rect=content.getBoundingClientRect(),bounds=page.getBoundingClientRect();
   const overflow=[];
   content.querySelectorAll('*').forEach(e=>{if(e.closest('dialog:not([open]),[hidden]')||e.parentElement?.closest('[data-internal-scroll],details:not([open])'))return;const r=e.getBoundingClientRect();if(r.width&&r.height&&(r.bottom>bounds.bottom-12||r.right>innerWidth-24||r.left<0))overflow.push(e.id||e.tagName);});
   let columns=null,solutionStyle=null,soloEquations=null;
   if(page.id==='p-solution'){
    soloEquations=[...page.querySelectorAll('#solo-equation')].map(e=>{
     const rect=e.getBoundingClientRect(),container=e.closest('.solo-prediction').getBoundingClientRect();
     return {text:e.textContent,width:rect.width,containerWidth:container.width,ok:rect.width<=container.width+1&&e.scrollWidth<=container.width+1};
    });
   }
   if(page.id==='p-challenge'){
    const left=page.querySelector('.challenge-parameters').getBoundingClientRect(),right=page.querySelector('.challenge-grid > .panel').getBoundingClientRect();
    const label=getComputedStyle(page.querySelector('#challenge-truth small')),caption=getComputedStyle(page.querySelector('.panel > .caption'));
    const truth=page.querySelector('#play-chart .series-truth');
    solutionStyle={fontEqual:['fontFamily','fontSize','color'].every(k=>label[k]===caption[k]),truthStroke:truth?parseFloat(getComputedStyle(truth).strokeWidth):null};
    solutionStyle.ok=solutionStyle.fontEqual&&(!truth||solutionStyle.truthStroke>=2.5);
    columns={left:{top:left.top,bottom:left.bottom,height:left.height},right:{top:right.top,bottom:right.bottom,height:right.height},ok:Math.abs(left.top-right.top)<=2&&Math.abs(left.bottom-right.bottom)<=2};
   }
   return {id:page.id,section:page.dataset.section,step:page.dataset.step,columns,solutionStyle,soloEquations,contentHeight:Math.ceil(Math.max(content.scrollHeight,rect.height)),availableHeight:Math.floor(innerHeight-112),viewportHeight:innerHeight,overflow,ok:content.scrollHeight<=innerHeight-112&&overflow.length===0&&(!columns||columns.ok)&&(!solutionStyle||solutionStyle.ok)&&(!soloEquations||soloEquations.every(e=>e.ok))};
  }
  const records=pages.map(page=>{
   const variants=[];
   if(page.id==='p-challenge')for(const shown of [false,true]){toggleSolution(shown);variants.push({...readPage(page),solutionShown:shown});}
   if(page.id==='p-solution'){for(const block of window.WispSolo.model.blocks){window.WispSolo.select(block.term);variants.push({...readPage(page),soloTerm:block.term});}window.WispSolo.select(window.WispSolo.model.winner);}
   if(page.dataset.stage){
    function inspectStage(sample){
    const stage=document.getElementById('c1-stage'),r=stage.getBoundingClientRect();
    const stageOk=r.left>=0&&r.top>=0&&r.right<=innerWidth&&r.bottom<=innerHeight-12;
    // Real SVG text bounds: the synthetic DOM intentionally cannot supply layout.
    const labels=[...stage.querySelectorAll('svg text')].filter(e=>+getComputedStyle(e).opacity>.01&&e.textContent.trim()).map(e=>({node:e,text:e.textContent,row:e.dataset.shareRow,rect:e.getBoundingClientRect()}));
    if(page.dataset.stage==='c5-recap')labels.push(...[...page.querySelectorAll('.c5-recap-description')].map(e=>({node:e,text:e.textContent,rect:e.getBoundingClientRect()})));
    const labelOverlaps=[];
    const chipLabelOverlaps=[];
    if(page.dataset.chapter==='four'){
     [...stage.querySelectorAll('.c4-chip')].filter(e=>+getComputedStyle(e).opacity>.01).forEach(chip=>{
      const box=chip.getBoundingClientRect();
      labels.forEach(label=>{const b=label.rect;
       // The chip's own term is intentionally inside its box.
       const inside=label.node===chip.nextElementSibling;
       if(!inside&&Math.min(box.right,b.right)>Math.max(box.left,b.left)&&Math.min(box.bottom,b.bottom)>Math.max(box.top,b.top))chipLabelOverlaps.push(label.text);
      });
     });
    }
    let chapterFourOk=true;
    if(page.dataset.chapter==='four'){
     const svg=stage.querySelector('svg'),state=page.dataset.stage,model=window.WispChapterFour.model;
     chapterFourOk=!labels.some(l=>/\d(?:[.,]\d+)?e[+-]?\d/i.test(l.text));
     if(state==='c4-replay'){
      const round=model.rounds[+svg.dataset.round-1],phase=Math.min(12000,(sample%(window.WispChapterStory.durations[state]+3000))-(+svg.dataset.round-1)*12000);
      if(phase<3000)chapterFourOk&&=svg.dataset.support===JSON.stringify(round.support);
      if(round.passes&&phase>=3000)chapterFourOk&&=[...stage.querySelectorAll('.c4-limit')].filter(e=>+getComputedStyle(e).opacity>.01).length>=(phase<5000?1:2);
     }
     if(['c4-replay','c4-threshold'].includes(state)){
      const limit=[...stage.querySelectorAll('.c4-limit')].find(e=>+e.dataset.value===model.threshold&&+getComputedStyle(e).opacity>.01);
      chapterFourOk&&=!!limit&&labels.some(l=>l.text===tr('x18_limit',{value:thresholdNumber(model.threshold)}));
      const ticks=[...stage.querySelectorAll('.c4-log-tick')].filter(e=>+getComputedStyle(e).opacity>.01),values=ticks.map(e=>+e.dataset.value);
      const expected=[.01,.1,1,10,100,1000,10000],close=(a,b)=>Math.abs(a-b)<1e-8;
      chapterFourOk&&=JSON.stringify(values)===JSON.stringify(expected)&&ticks.every((t,i)=>close(+t.getAttribute('y1'),278-98*i/6));
      chapterFourOk&&=!!limit&&close(+limit.getAttribute('y1'),278-98*(Math.log10(model.threshold)+2)/6);
      chapterFourOk&&=![...stage.querySelectorAll('.c4-zoom')].slice(0,12).some(e=>+getComputedStyle(e).opacity>.01);

     }
    }
    let chapterFiveOk=true;
    if(page.dataset.chapter==='five'){
     const svg=stage.querySelector('svg'),model=window.WispChapterFive.model,state=page.dataset.stage;
     chapterFiveOk=svg.dataset.state===state&&svg.dataset.candidate===model.winner.row.candidate_id&&!labels.some(l=>/\d(?:[.,]\d+)?e[+-]?\d/i.test(l.text));
     if(state==='c5-each'){
      chapterFiveOk&&=[...stage.querySelectorAll('.c5-fit-curve')].filter(e=>+getComputedStyle(e).opacity>.01).length===model.candidates.filter(c=>c.curves).length;
      const readouts=[...stage.querySelectorAll('.c5-readout')].map(e=>e.getBoundingClientRect());
      chapterFiveOk&&=labels.filter(l=>l.text.includes(tr('x19_bound',{terms:''}).trim())).every(l=>readouts.some(b=>l.rect.left>=b.left&&l.rect.right<=b.right&&l.rect.top>=b.top&&l.rect.bottom<=b.bottom));
     }
     if(state==='c5-bic')chapterFiveOk&&=Number.isFinite(+svg.dataset.bicOrigin)&&labels.some(l=>l.text===tr('x19_candidate_axis'))&&labels.some(l=>l.text===tr('x19_bic_axis',{origin:fmt(+svg.dataset.bicOrigin,6)}));
     if(state==='c5-winner'){
      const equations=labels.filter(l=>l.text.startsWith('du/dt = '));
      chapterFiveOk&&=equations.length===3&&equations.every(l=>Math.abs(l.rect.top-equations[0].rect.top)<1);
     }
     if(state==='c5-recap'){
      chapterFiveOk&&=[...stage.querySelectorAll('.c5-recap-box.highlight')].filter(e=>+getComputedStyle(e).opacity>.01).length===1;
      for(const role of ['name','description','result']){
       const texts=[...(role==='description'?page:stage).querySelectorAll('.c5-recap-'+role)];
       chapterFiveOk&&=texts.length===8&&texts.every(e=>e.textContent.trim()&&+getComputedStyle(e).opacity>.01&&parseFloat(getComputedStyle(e).fontSize)*(e.closest('svg')?svg.getScreenCTM().a:1)>=14);
      }
      chapterFiveOk&&=labels.some(l=>l.text==='↻ '+tr('x19_recap_loop'));
      chapterFiveOk&&=labels.every(l=>parseFloat(getComputedStyle(l.node).fontSize)*(l.node.closest('svg')?svg.getScreenCTM().a:1)>=14);
      const boxes=[...stage.querySelectorAll('.c5-recap-box')].map(e=>e.getBoundingClientRect());
      for(const role of ['name','result'])chapterFiveOk&&=[...stage.querySelectorAll('.c5-recap-'+role)].every((e,i)=>{
       const a=e.getBoundingClientRect(),b=boxes[i];return a.left>=b.left&&a.right<=b.right&&a.top>=b.top&&a.bottom<=b.bottom;
      });
      const groups=[...stage.querySelectorAll('.c5-support-group')].filter(e=>+getComputedStyle(e).opacity>.01).map(e=>e.getBoundingClientRect());
      chapterFiveOk&&=groups.length===model.candidates.length&&groups.every((b,i)=>{
       const chips=[...stage.querySelectorAll('.c5-chip')].filter(e=>+getComputedStyle(e).opacity>.01).map(e=>e.getBoundingClientRect());
       return chips.filter(a=>a.left>=b.left&&a.right<=b.right&&a.top>=b.top&&a.bottom<=b.bottom).length===model.candidates[i].support.length;
      });
     }
    }
    if(page.dataset.chapter==='two'||page.dataset.chapter==='three'||page.dataset.chapter==='four'||page.dataset.chapter==='five'||['noise-visible','slope','secants','windows','error-empty','fit','every','noise-why','noise-estimate','percent'].includes(page.dataset.stage)){
     labels.forEach((a,i)=>labels.slice(i+1).forEach(b=>{if(Math.min(a.rect.right,b.rect.right)>Math.max(a.rect.left,b.rect.left)&&Math.min(a.rect.bottom,b.rect.bottom)>Math.max(a.rect.top,b.rect.top))labelOverlaps.push([a.text,b.text]);}));
    }
    const box=stage.querySelector('.story-deviations').getBoundingClientRect(),plot=stage.querySelector('#story-top-clip rect');
    const matrix=stage.querySelector('svg').getScreenCTM(),plotRight=matrix.a*(+plot.getAttribute('x') + +plot.getAttribute('width'))+matrix.e;
    const deviationsOutside=page.dataset.stage!=='noise-estimate'||+getComputedStyle(stage.querySelector('.story-deviations')).opacity<=.01||box.left>plotRight;
    const dataLabels=[];
    const annotationSelector=['two','three','four'].includes(page.dataset.chapter)?'svg text':'.story-construction-readout,.story-long-label,.story-neighbour-label,.story-optimum-label,.story-noise-readout,.story-reference-label,.story-length-key';
    const annotationLabels=[...stage.querySelectorAll(annotationSelector)].filter(e=>+getComputedStyle(e).opacity>.01);
    if(['secants','windows'].includes(page.dataset.stage))annotationLabels.push(...stage.querySelectorAll('.story-delta,.story-length'));
    const dots=[...stage.querySelectorAll('.measurement-dot,.story-slope,.story-long-slope,.story-length-slope')].filter(e=>+getComputedStyle(e).opacity>.01).map(e=>e.getBoundingClientRect());
    annotationLabels.filter(e=>+getComputedStyle(e).opacity>.01).forEach(e=>{const a=e.getBoundingClientRect();if(dots.some(b=>Math.min(a.right,b.right)>Math.max(a.left,b.left)&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top)))dataLabels.push(e.textContent);});
    const intersects=(a,b)=>Math.min(a.right,b.right)>Math.max(a.left,b.left)&&Math.min(a.bottom,b.bottom)>Math.max(a.top,b.top);
    const visible=e=>+getComputedStyle(e).opacity>.99;
    // Clip-path geometry lives in defs; map its SVG coordinates to screen space.
    const plotBox={left:matrix.a*(+plot.getAttribute('x'))+matrix.e,right:plotRight,top:matrix.d*(+plot.getAttribute('y'))+matrix.f,bottom:matrix.d*(+plot.getAttribute('y') + +plot.getAttribute('height'))+matrix.f};
    const visibleData=[...stage.querySelectorAll('.measurement-dot')].filter(e=>visible(e)&&intersects(e.getBoundingClientRect(),plotBox)).length;
    const noiseEndOk=page.dataset.stage!=='noise-estimate'||sample% (story.durations['noise-estimate']+3000)<story.durations['noise-estimate']||(visibleData>=500&&visible(stage.querySelector('.story-band')));
    const shareRows=[...stage.querySelectorAll(page.dataset.chapter==='two'?'.c2-slot':'.story-slot')].map((e,j)=>{const boxes=[e.getBoundingClientRect(),...labels.filter(a=>a.row===String(j)).map(a=>a.rect)];return {left:Math.min(...boxes.map(b=>b.left)),right:Math.max(...boxes.map(b=>b.right)),top:Math.min(...boxes.map(b=>b.top)),bottom:Math.max(...boxes.map(b=>b.bottom))};});
    const shareOverlaps=['percent','c2-joint'].includes(page.dataset.stage)?labels.flatMap(a=>shareRows.filter((b,j)=>a.row!==String(j)&&intersects(a.rect,b)).map(()=>a.text)):[];
    const leg=stage.querySelector('.story-triangle'),neighbourDt=leg.getBoundingClientRect().width;
    const neighbourOk=page.dataset.stage!=='secants'||stage.querySelector('svg').dataset.phase!=='zoomed'||neighbourDt>=60;
    // Audit the shipped chapter-three geometry against the live numerical path.
    let chapterThreeOk=true;
    if(page.dataset.chapter==='three'){
     const state=page.dataset.stage,svg=stage.querySelector('svg'),model=window.WispChapterThree.model;
     const phase=sample%(window.WispChapterStory.durations[state]+3000),close=(a,b)=>Math.abs(a-b)<1e-9;
     const repair=['c3-linear','c3-quadratic'].includes(state),audit=repair||['c3-probe','c3-threshold'].includes(state);
     const round=model.rounds[state==='c3-quadratic'?3:state==='c3-linear'?2:1];
     const expected=audit&&state!=='c3-probe'&&phase>=(repair?1800:0)&&round.threshold<.1*(+svg.dataset.costMaximum);
     chapterThreeOk=(svg.dataset.magnified==='true')===expected&&visible(stage.querySelector('.c3-zoom-title'))===expected;
     if(expected){
      const probe=round.probes[+svg.dataset.probe];
      chapterThreeOk&&=[...stage.querySelectorAll('.c3-zoom-bar')].filter(visible).every(bar=>probe.costs.some(c=>c.term===+bar.dataset.term&&close(c.cost,+bar.dataset.value))&&close(+bar.dataset.limit,2.5*round.threshold)&&+bar.getAttribute('height')<=60+1e-9);
      chapterThreeOk&&=close(+stage.querySelector('.c3-zoom-threshold').dataset.value,round.threshold);
     }
     if(repair){
      const decision=1800+round.probes[0].costs.length*1800;
      if(phase>=decision&&phase<decision+3200)chapterThreeOk&&=svg.dataset.probe==='0'&&[...stage.querySelectorAll('.c3-cost.goes')].some(visible);
     }
     if(state==='c3-next'){
      const gains=model.rounds.map(r=>({term:r.addition,gain:r.gain})).concat([model.next]);
      chapterThreeOk&&=[...stage.querySelectorAll('.c3-round-gain')].every((bar,j)=>close(+bar.dataset.value,gains[j].gain)&&+bar.dataset.term===gains[j].term&&bar.classList.contains('not-taken')===(j===4));
      chapterThreeOk&&=![...stage.querySelectorAll('.c3-threshold')].some(visible);
     }
     if(['c3-compare','c3-next'].includes(state))chapterThreeOk&&=[...stage.querySelectorAll('.c3-candidate')].every(box=>!box.nextElementSibling.textContent.includes('·'));
    }
    variants.push({...readPage(page),sample,stageOk,chapterThreeOk,chapterFourOk,chapterFiveOk,chipLabelOverlaps,labelOverlaps,dataLabels,deviationsOutside,visibleData,noiseEndOk,shareOverlaps,neighbourDt,neighbourOk,ok:readPage(page).ok&&stageOk&&chapterThreeOk&&chapterFourOk&&chapterFiveOk&&chipLabelOverlaps.length===0&&labelOverlaps.length===0&&dataLabels.length===0&&deviationsOutside&&noiseEndOk&&shareOverlaps.length===0&&neighbourOk});
    }
    const story=window.WispChapterStory;story.enter(page.dataset.stage);
    const samples={'c5-weak':[0,300,900,1500,3000,4200,6000,9000,16000],'c5-fit':[0,300,900,1500,3000,4200,6000,9000,16000],'c5-each':[0,300,900,1500,3000,4200,6000,9000,16000],'c5-bic':[0,300,900,1500,3000,4200,6000,9000,16000],'c5-winner':[0,300,900,1500,3000,4200,6000,9000,16000],'c5-recap':[0,1999,2000,3999,4000,5999,6000,7999,8000,9999,10000,11999,12000,13999,14000,16000,19001],'c4-question':[0,600,1200,2400,4200],'c4-noise':[0,600,1200,3000],'c4-threshold':[0,600,1200,3000],'c4-replay':Array.from({length:5},(_,j)=>[0,600,1500,2999,3000,4000,4999,5000,7000,8499,8500,11499,11500,11999].map(t=>j*12000+t)).flat().concat([60000]),'c4-path':[0,700,1400,2100,2800,4200],secants:[0,300,600,899,900,1100,2000,3000,...Array.from({length:8},(_,j)=>3900+j*1200),13200],windows:story.longerLengths.flatMap((_,j)=>[900+j*2400,1600+j*2400,3000+j*2400]).concat([12900]),fit:[2899,2900,4900],every:Array.from({length:6},(_,j)=>[2000+j*2500,3150+j*2500,3399+j*2500]).flat().concat([16900]),'noise-estimate':[0,400,800,1500,2450,2550,4000,6800,7500,8500,9799,9800,10500,12300,13500,story.durations['noise-estimate']], 'c3-standing':[0,600,1200], 'c3-probe':[0,600,1200,1800,2400,3600,5200], 'c3-threshold':[0,1200,2400,3600,5200], 'c3-linear':[0,300,600,899,900,1100,1500,1800,3000,3600,4800,5400,6600,7200,7500,7799,7800,8100,8400,9400,10399,10400,11000,11600,12200,14000,15300,16000,19300], 'c3-quadratic':[0,300,600,899,900,1100,1500,1800,3000,3600,4800,5400,6600,7200,7500,7799,7800,8100,8400,9400,10399,10400,11000,11600,12200,14000,15300,16000,19300], 'c3-compare':[0,1200,2400,3300,4200], 'c3-next':[0,1200,2400,4200], 'c2-standing':[0,300,600,900],'c2-residual':[900,1500,2100,2600,3100], 'c2-joint':[0,900,1650,2400,3900,...Array.from({length:story.remainingBlocks.length},(_,j)=>[story.jointPause+1600+j*2500,story.jointPause+3150+j*2500,story.jointPause+3399+j*2500]).flat(),story.durations['c2-joint']], 'c2-every':[900,1600,3150], 'c2-error':[900,1500,2000,2600,3100], 'c2-solution':[0,450,900]};
    for(const sample of samples[page.dataset.stage]||[]){story.seek(sample);inspectStage(sample);}
    story.finish();inspectStage(story.durations[page.dataset.stage]);
    // Exercise the same deterministic cycle offset used by the live replay.
    story.seek(story.durations[page.dataset.stage]+3000+300);inspectStage(story.durations[page.dataset.stage]+3300);
    story.finish();
   }
   const record=readPage(page);
   return variants.length?{...record,variants,ok:variants.every(v=>v.ok),overflow:[...new Set(variants.flatMap(v=>v.overflow))],contentHeight:Math.max(...variants.map(v=>v.contentHeight))}:record;
  });
  nav.go(nav.index,false);window.WispChapterStory?.finish();
  const pre=make('pre',JSON.stringify({ok:records.every(r=>r.ok),language:document.documentElement.lang,width:innerWidth,height:innerHeight,pages:records}));pre.id='fitcheck-result';document.body.append(pre);
 }
 if(fitcheck)measure();
})(typeof window!=='undefined'?window:globalThis);
