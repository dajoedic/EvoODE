/* Presentation adapters: all evidence and result prose bind to exported data. */
"use strict";
const DATA=JSON.parse(document.getElementById("wisp-data").textContent);
// Restore the unchanged results contract from losslessly interned transport arrays.
function hydrateBundle(bundle){if(!bundle)return;for(const key of ['t','truth','model']){const ref=bundle[key];if(ref && !Array.isArray(ref) && '$display' in ref)bundle[key]=DATA.display_arrays[ref.$display];}hydrateBundle(bundle.generalization);}
for(const cell of DATA.results.cells)hydrateBundle(cell.curves);
for(const feature of DATA.live.featured||[])for(const candidate of feature.candidates)hydrateBundle(candidate.curves);
const LIVE=DATA.live, RESULTS=DATA.results, MANIFEST=DATA.manifest, W=WispCompute;
const tables=LIVE.i18n;
function initialLanguage(){
 if(!window.location)return 'en';
 let preferred;try{const url=new URL(window.location.href);preferred=url.searchParams.get('lang')||new URLSearchParams(url.hash.slice(1)).get('lang')||url.hash.slice(1);}catch{}
 if(!['de','en'].includes(preferred)){try{preferred=window.localStorage?.getItem('wisp-language');}catch{}}
 return ['de','en'].includes(preferred)?preferred:((window.navigator?.language||'en').startsWith('de')?'de':'en');
}
let language=initialLanguage();
function tr(key,values={}){const text=tables?.[language]?.[key];if(typeof text!=='string'||!text)throw Error('Missing translation: '+key);return text.replace(/\{(\w+)\}/g,(_,k)=>{if(!(k in values))throw Error('Missing translation argument: '+key);return typeof values[k]==='number'?numberText(values[k],8):values[k];});}
const truthLabel=value=>value==='True'?tr('yes'):value==='False'?tr('no'):tr('j153');
const weightLabel=value=>tr(value==='arithmetic'?'h111':'h110');
function applyLanguage(lang,navigate=false){
 language=lang;document.documentElement?.setAttribute('lang',lang);
 try{window.localStorage?.setItem('wisp-language',lang);}catch{}
 document.querySelectorAll('[data-i18n]').forEach(e=>{if(e.dataset.i18n)e.textContent=tr(e.dataset.i18n);});
 for(const attr of ['aria-label','content','title'])document.querySelectorAll('[data-i18n-'+attr+']').forEach(e=>{const key=e.getAttribute?.('data-i18n-'+attr);if(key)e.setAttribute(attr,tr(key));});
 for(const choice of ['en','de'])document.getElementById('language-'+choice)?.setAttribute('aria-pressed',String(choice===lang));
 if(navigate){const url=new URL(window.location.href);url.searchParams.set('lang',lang);window.location.assign(url.href);}
}
applyLanguage(language);
for(const lang of ['en','de'])document.getElementById('language-'+lang).addEventListener('click',()=>applyLanguage(lang,true));
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const superscript=x=>String(x).replace(/[-+0-9]/g,c=>({'-':'⁻','+':'','0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}[c]));
function numberText(x,d=3){const n=Number(x);if(n!==0&&(Math.abs(n)<1e-4||Math.abs(n)>=1e7)){const [m,e]=n.toExponential(d-1).split('e');return Number(m).toLocaleString(language,{maximumSignificantDigits:d})+' × 10'+superscript(Number(e));}return n.toLocaleString(language,{maximumSignificantDigits:d});}
const fmt=(x,d=3)=>x!==''&&x!==null&&x!==undefined&&Number.isFinite(+x)?numberText(x,d):tr('j153');
const pct=x=>Number.isFinite(+x)&&x!==''?`${fmt(+x*100)}%`:tr('j153');
const terms=['1','u','u²','u³',tr('j154'),tr('j155')];
const texTerms=['1','u','u^{2}','u^{3}','\\sin u','\\cos u'];
const NS='http://www.w3.org/2000/svg';
function svgNode(tag,attrs={},text){const e=document.createElementNS(NS,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,v));if(text!==undefined)e.textContent=text;return e;}
// Illustration only: no scientific data or WISP computation enters this scene.
function initDish(){
 const target=$('dish-illustration'),svg=svgNode('svg',{viewBox:'0 0 1020 260',role:'img','aria-labelledby':'dish-title dish-description'});
 svg.append(svgNode('title',{id:'dish-title'},tr('x7_history')),svgNode('desc',{id:'dish-description'},tr('x7_caption')));
 const dishGroup=svgNode('g',{transform:'scale(1.35)'});svg.append(dishGroup);dishGroup.append(svgNode('circle',{cx:105,cy:88,r:79,class:'dish-rim'}));
 const cells=svgNode('g');dishGroup.append(cells);
 // LCG seed 731; stratified positions fill the disk without overlaps.
 let seed=731;const random=()=>{seed=(Math.imul(1664525,seed)+1013904223)>>>0;return seed/4294967296;};
 const positions=[];for(let y=-68;y<=68;y+=9)for(let x=-68;x<=68;x+=9){const px=x+(random()-.5)*3,py=y+(random()-.5)*3;if(px*px+py*py<72*72)positions.push([105+px,88+py]);}
 for(let i=positions.length-1;i>0;i--){const j=Math.floor(random()*(i+1));[positions[i],positions[j]]=[positions[j],positions[i]];}
 const dots=positions.map(([cx,cy])=>{const dot=svgNode('circle',{cx,cy,r:2.9,class:'dish-cell'});cells.append(dot);return dot;});
 const curveGroup=svgNode('g',{transform:'translate(-140 12) scale(1.5 1.35)'});svg.append(curveGroup);curveGroup.append(svgNode('path',{d:'M280 14V151H752',class:'dish-axis'}),svgNode('text',{x:288,y:17},tr('x7_cells')),svgNode('text',{x:752,y:174,'text-anchor':'end'},tr('x7_time')));
 const curve=svgNode('path',{class:'dish-curve'}),head=svgNode('circle',{r:4,class:'dish-cell'});curveGroup.append(curve,head);target.append(svg);
 // Stack the two scenes in the same accessible illustration on small screens.
 function geometry(){const narrow=innerWidth<760;svg.setAttribute('viewBox',narrow?'0 0 400 480':'0 0 1020 260');dishGroup.setAttribute('transform',narrow?'translate(58 0) scale(1.35)':'scale(1.35)');curveGroup.setAttribute('transform',narrow?'translate(-120 250) scale(.65 1.15)':'translate(-140 12) scale(1.5 1.35)');}
 geometry();window.addEventListener('resize',geometry);
 // K=1 (normalised occupancy), n0=.012, r=10, t in [0,1], 6000 ms.
 const occupancy=t=>1/(1+(1/.012-1)*Math.exp(-10*t));
 function draw(progress){const count=Math.round(occupancy(progress)*dots.length);dots.forEach((dot,i)=>dot.setAttribute('visibility',i<count?'visible':'hidden'));
  const points=Array.from({length:Math.ceil(progress*160)+1},(_,i)=>Math.min(i/160,progress));let d='';
  for(const t of points)d+=(d?'L':'M')+(280+472*t).toFixed(2)+','+(151-130*occupancy(t)).toFixed(2);
  curve.setAttribute('d',d);head.setAttribute('cx',280+472*progress);head.setAttribute('cy',151-130*occupancy(progress));target.dataset.progress=String(progress);
 }
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 let frame=0,visible=typeof IntersectionObserver!=='function',elapsed=0,last=0;
 function tick(now){elapsed=(elapsed+now-last)%7500;last=now;draw(Math.min(1,elapsed/6000));frame=requestAnimationFrame(tick);}
 function update(){cancelAnimationFrame(frame);frame=0;
  if(reduced.matches){draw(1);return;}
  if(visible&&!document.hidden){last=performance.now();frame=requestAnimationFrame(tick);}
 }
 reduced.addEventListener?.('change',()=>{draw(reduced.matches?1:Math.min(1,elapsed/6000));update();});
 document.addEventListener('visibilitychange',update);
 draw(reduced.matches?1:0);
 if(typeof IntersectionObserver==='function'){const observer=new IntersectionObserver(entries=>{visible=entries.some(e=>e.isIntersecting);update();},{threshold:.1});observer.observe(target);}else{const visibility=()=>{const r=target.getBoundingClientRect();visible=r.bottom>0&&r.top<innerHeight;update();};window.addEventListener('scroll',visibility,{passive:true});window.addEventListener('resize',visibility);visibility();}
}
initDish();
window.typesetAll=()=>{if(!window.katex)return;document.querySelectorAll("[data-tex]").forEach(e=>{window.katex.render(e.dataset.tex,e,{throwOnError:false,output:'mathml',displayMode:!e.classList.contains('inline')});});};
function math(target,tex){target.dataset.tex=tex;target.textContent=tex;if(window.katex)window.katex.render(tex,target,{throwOnError:false,output:'mathml',displayMode:!target.classList.contains('inline')});}
function equation(support,coefficients){return '\\frac{du}{dt}='+ (support.length?support.map((j,i)=>`${i&&coefficients[i]>=0?'+':''}${fmt(coefficients[i],4)}\\,${texTerms[j]}`).join(' '):'0');}
// Names and conditions are presentation labels; identifiers remain option values.
function systemName(c){return tables[language]['system_'+c.system_id]||c.description;}
function cellName(id){const c=RESULTS.cells.find(c=>c.row.cell_id===id);if(!c)return tr('j153');const start=String(id).match(/_ic(\d+)/)?.[1],parts=[systemName(c)];if(+c.row.sigma)parts.push(tr('x4_noise',{v0:fmt(+c.row.sigma*100)}));if(+c.row.rho)parts.push(+c.row.rho===.5?tr('x5_half'):tr('x4_missing',{v0:fmt(+c.row.rho*100)}));if(start&&+start>1)parts.push(+start===2?tr('x5_second'):tr('x4_start',{v0:start}));return parts.join(' · ');}
function displayTruth(s){return s.replace(/(?:\d+\.\d+|\d+)(?:[eE][+-]?\d+)?/g,(n,offset,text)=>/[A-Za-z_]/.test(text[offset-1]||'')?n:fmt(+n,4)).replaceAll('**','^').replaceAll('x_0','u_{1}').replaceAll('x_1','u_{2}').replaceAll('x_2','u_{3}').replaceAll('x_3','u_{4}').replaceAll('*','\\,');}
function options(target,values,label=v=>v){target.replaceChildren(...values.map(v=>{const e=el('option',label(v));e.value=v;return e;}));}
function chart(target,series,{title='',xLabel=tr('j157'),yLabel=tr('j158'),areas=[],highlight=null,point=null,zeroBase=false,integerX=false,legend:showLegend=true,truthOnTop=false,xDomain=null,horizontalYLabel=false,dotRadius=2.2}={}){
  target.replaceChildren();
  const width=760,height=310,pad={l:76,r:20,t:36,b:42};
  const good=series.flatMap(s=>s.x.map((x,i)=>[x,s.y[i]])).filter(([x,y])=>Number.isFinite(x)&&Number.isFinite(y)&&Math.abs(y)<1e12);
  if(!good.length){target.append(el('p',tr('j159'),'notice'));return;}
  let xmin=Math.min(...good.map(p=>p[0])),xmax=Math.max(...good.map(p=>p[0])),ymin=Math.min(...good.map(p=>p[1])),ymax=Math.max(...good.map(p=>p[1]));
  if(xDomain)[xmin,xmax]=xDomain;
  if(areas.length||zeroBase){ymin=zeroBase?0:Math.min(ymin,0);ymax=Math.max(ymax,zeroBase?1:0);}
  if(ymax===ymin){ymax+=1;ymin-=1;}if(xmax===xmin)xmax+=1;
  const margin=(ymax-ymin)*.08;ymin=zeroBase?0:ymin-margin;ymax+=margin;
  const X=x=>pad.l+(x-xmin)/(xmax-xmin)*(width-pad.l-pad.r),Y=y=>height-pad.b-(y-ymin)/(ymax-ymin)*(height-pad.t-pad.b);
  const svg=svgNode('svg',{viewBox:`0 0 ${width} ${height}`,class:'chart',role:'img',"aria-label":tr('axis_description',{v0:title,v1:yLabel,v2:xLabel})});
  svg.append(svgNode('title',{},title));
  for(let i=0;i<=4;i++){
    const y=ymin+(ymax-ymin)*i/4,x=xmin+(xmax-xmin)*i/4;
    svg.append(svgNode('line',{x1:pad.l,x2:width-pad.r,y1:Y(y),y2:Y(y),class:'grid'}));
    svg.append(svgNode('text',{x:pad.l-8,y:Y(y)+4,"text-anchor":'end'},fmt(y)));
    if(!integerX)svg.append(svgNode('text',{x:X(x),y:height-23,"text-anchor":'middle'},fmt(x)));
  }
  if(integerX){const stride=Math.max(1,Math.ceil((xmax-xmin)/8));for(let x=Math.ceil(xmin);x<=xmax;x+=stride)svg.append(svgNode('text',{x:X(x),y:height-23,'text-anchor':'middle'},fmt(x)));}
  if(highlight)svg.append(svgNode('rect',{x:X(highlight[0]),y:pad.t,width:Math.max(1,X(highlight[1])-X(highlight[0])),height:height-pad.b-pad.t,fill:'var(--model)',opacity:'.12'}));
  for(const a of areas){const pts=a.x.map((x,i)=>`${X(x)},${Y(a.y[i])}`).join(' ');svg.append(svgNode('polygon',{points:`${X(a.x[0])},${Y(0)} ${pts} ${X(a.x.at(-1))},${Y(0)}`,fill:'var(--data)',opacity:'.18'}));}
  for(const s of series.slice().sort((a,b)=>(truthOnTop&&a.kind==='truth'?3:a.kind==='data'?0:a.kind==='model'?2:1)-(truthOnTop&&b.kind==='truth'?3:b.kind==='data'?0:b.kind==='model'?2:1))){let d='',drawing=false;for(let i=0;i<s.x.length;i++){
    const v=s.y[i];if(!Number.isFinite(v)||Math.abs(v)>1e12){drawing=false;continue;}d+=`${drawing?'L':'M'}${X(s.x[i]).toFixed(3)},${Y(v).toFixed(3)}`;drawing=true;
  }if(s.x.length===1)svg.append(svgNode('circle',{cx:X(s.x[0]),cy:Y(s.y[0]),r:4,fill:'var(--residual)'}));svg.append(svgNode('path',{d,class:`series-${s.kind||'truth'} ${s.style||''}`}));
  if(s.kind==='data'&&s.style!=='dashed')s.x.forEach((x,i)=>{if(Number.isFinite(s.y[i]))svg.append(svgNode('circle',{cx:X(x),cy:Y(s.y[i]),r:dotRadius,class:'measurement-dot'}));});
  }
  svg.append(svgNode('text',{x:pad.l,y:17},title));
  svg.append(svgNode('text',{x:width-pad.r,y:height-4,"text-anchor":'end'},xLabel));
  if(horizontalYLabel)svg.append(svgNode('text',{x:pad.l,y:17},yLabel));
  else svg.append(svgNode('text',{transform:`translate(14 ${(pad.t+height-pad.b)/2}) rotate(-90)`,"text-anchor":'middle'},yLabel));
  if(point)svg.append(svgNode('circle',{cx:X(point[0]),cy:Y(point[1]),r:5,fill:'var(--model)',stroke:'var(--panel)',"stroke-width":2}));
  target.append(svg);
  const legend=el('div',undefined,'caption');legend.textContent=series.map(s=>`${s.label||s.kind} (${tr(s.style==='dashed'||s.kind==='truth'?'x5_dashed':s.kind==='data'?'x5_dots':'x5_solid')})`).join(' · ');if(showLegend)target.append(legend);
  return {svg,X,xmin,xmax,width,pad};
}
function rk4(t,initial,rhs){let x=initial.slice();const out=[x.slice()];for(let i=1;i<t.length;i++){
  const dt=t[i]-t[i-1],n=Math.max(1,Math.ceil(dt/.015)),h=dt/n;
  for(let k=0;k<n;k++){
    const a=rhs(x),b=rhs(x.map((v,j)=>v+h*a[j]/2)),c=rhs(x.map((v,j)=>v+h*b[j]/2)),d=rhs(x.map((v,j)=>v+h*c[j]));
    x=x.map((v,j)=>v+h*(a[j]+2*b[j]+2*c[j]+d[j])/6);
    if(x.some(v=>!Number.isFinite(v)||Math.abs(v)>1e6))return out.concat(t.slice(i).map(()=>initial.map(()=>NaN)));
  }out.push(x.slice());}return out;}
const demo=LIVE.illustrations[0], predator=LIVE.illustrations[1], time=demo.t, truth=demo.x.map(r=>r[0]);
const teaching=LIVE.teaching, measuredTime=teaching?.t||time, measuredTruth=teaching?.truth||truth;
const measuredNoise=s=>teaching?(s===teaching.sigma?teaching.observed:measuredTruth.map((v,i)=>v*(1+s*teaching.noise_draws[i]))):truth.map((v,i)=>v*(1+s*demo.noise_draws[i]));
let sigma=.03,noisy=[],currentPath=null,pathError=null,selectedStratum=RESULTS.rates[0].stratum;
const logistic=(rate,capacity)=>rk4(time,demo.initial,x=>[rate*x[0]*(1-x[0]/capacity)]).map(x=>x[0]);
$('rate').value=demo.constants[0];$('capacity').value=demo.constants[1];
function growthRule(){const rate=+$('rate').value,capacity=+$('capacity').value;$("rate-value").value=fmt(rate);$("capacity-value").value=fmt(capacity);chart($("logistic-chart"),[{x:time,y:logistic(rate,capacity),kind:'truth',label:tr('j174')}],{title:tr('j175')});}
['rate','capacity'].forEach(id=>$(id).addEventListener('input',growthRule));growthRule();
math($("predator-equation"),predator.equation.map((s,i)=>`\\frac{d${i?'v':'u'}}{dt}=${s.replaceAll('x_0','u').replaceAll('x_1','v').replaceAll('*','\\,')}`).join('\\qquad '));
function predatorDraw(){const i=+$("predator-time").value,t=predator.t.slice(0,i+1),x=predator.x.slice(0,i+1);$("predator-value").value=fmt(predator.t[i]);chart($("predator-chart"),[{x:t,y:x.map(r=>r[0]),kind:'truth',label:tr('prey')},{x:t,y:x.map(r=>r[1]),kind:'model',label:tr('predators')}],{title:tr('j180'),yLabel:tr('j181')});chart($("phase-chart"),[{x:predator.x.map(r=>r[0]),y:predator.x.map(r=>r[1]),kind:'truth',label:tr('j183')}],{title:tr('j184'),xLabel:tr('j185'),yLabel:tr('j186'),point:predator.x[i]});}
$("predator-time").max=predator.t.length-1;$("predator-time").value=predator.t.length-1;$("predator-time").addEventListener('input',predatorDraw);predatorDraw();
// Per-term precision makes the data-scale answer reachable without revealing it.
const coefficientLimits=[[-10,10,.01],[-2,2,.001],[-.03,.03,.00001],[-.001,.001,.000001],[-2,2,.01],[-2,2,.01]];
const coefficientButtonSteps=[.1,.1,.001,.0001,.1,.1];
const initialCoefficients=[0,.23,0,0,0,0],coeff=initialCoefficients.slice(),enabled=Array(6).fill(false),termControls=[];
$('challenge-deck-start').textContent=tr('x7_challenge_start',{noise:pct(teaching.sigma)});
let hintCount=0;
terms.forEach((name,i)=>{
 const card=el('div',undefined,'term-card'),label=el('label',name),check=el('input');check.type='checkbox';check.checked=enabled[i];check.setAttribute('aria-label',tr('include_term',{v0:name}));label.append(check);
 const controls=el('div',undefined,'coefficient-controls'),range=el('input'),typed=el('input'),[min,max,step]=coefficientLimits[i];range.type='range';typed.type='number';
 range.min=min;range.max=max;range.step=step;
 for(const input of [range,typed]){input.value=coeff[i];input.setAttribute('aria-label',tr('j188',{v0:name}));}
 typed.step='any';
 const sync=(preserveTyped=false)=>{range.value=coeff[i];if(!preserveTyped)typed.value=coeff[i];controls.dataset.disabled=String(!enabled[i]);for(const input of [range,typed,...controls.querySelectorAll('button')])input.disabled=!enabled[i];};
 const update=(value,preserveTyped=false)=>{if(!Number.isFinite(value))return;coeff[i]=preserveTyped?value:+Math.max(min,Math.min(max,value)).toFixed(8);sync(preserveTyped);play();};
 range.addEventListener('input',()=>update(+range.value));typed.addEventListener('input',()=>{if(typed.value.trim()!=='')update(+typed.value,true);});typed.addEventListener('change',()=>sync());
 const minus=el('button','−'),plus=el('button','+');for(const [button,direction,key] of [[minus,-1,'x6_decrease'],[plus,1,'x6_increase']]){button.type='button';button.setAttribute('aria-label',tr(key,{term:name}));button.addEventListener('click',()=>update(coeff[i]+direction*coefficientButtonSteps[i]));}
 check.addEventListener('change',()=>{enabled[i]=check.checked;sync();play();});controls.append(range,minus,typed,plus);card.append(label,controls);$('term-cards').append(card);termControls.push({check,sync});sync();
});
function observationR2(curve,observations){
 const mean=observations.reduce((s,v)=>s+v,0)/observations.length,total=observations.reduce((s,v)=>s+(v-mean)**2,0);
 return 1-curve.reduce((s,v,i)=>s+(v-observations[i])**2,0)/total;
}
let solutionShown=false;
function toggleSolution(show){
 solutionShown=show;
 const key=show?'x8_hide':'x8_show',button=$('challenge-solution');
 button.setAttribute('aria-label',tr(key));button.setAttribute('title',tr(key));button.setAttribute('aria-pressed',String(show));
 $('challenge-truth').hidden=!show;play();
}
$('challenge-solution').addEventListener('click',()=>toggleSolution(!solutionShown));
// Fit each block with the frozen solver's exact compressed design.
const soloDot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
  function soloCompress(A,b) {
    const p=A[0].length, norms=Array.from({length:p},(_,j)=>Math.sqrt(soloDot(A.map(r=>r[j]),A.map(r=>r[j]))));
    const M=A.map((r,i)=>[...r.map((v,j)=>v/(norms[j]||1)),b[i]]);
    // Householder augmented QR avoids subtracting nearly equal residual norms.
    for(let k=0;k<Math.min(M.length,p+1);k++) {
      const v=M.slice(k).map(r=>r[k]), n=Math.sqrt(soloDot(v,v));
      if(!n) continue;
      v[0]+=(v[0]>=0?1:-1)*n;
      const vv=soloDot(v,v);
      for(let j=k;j<=p;j++) {
        let s=0; for(let i=0;i<v.length;i++) s+=v[i]*M[i+k][j];
        s=2*s/vv; for(let i=0;i<v.length;i++) M[i+k][j]-=s*v[i];
      }
    }
    return {A:M.slice(0,p+1).map(r=>r.slice(0,p)),b:M.slice(0,p+1).map(r=>r[p]),norms};
  }

function soloModel(observations,times,config,feature){
 const result=W.path(times,observations,config),first=result.steps[0],D=result.design;
 if(!first||JSON.stringify(first.support)!==JSON.stringify(feature.path[0].active_idxs[0].map(j=>j-1)))throw Error('Teaching path differs from recorded supports');
 const C=soloCompress(D.A,D.b),norm=soloDot(D.b,D.b),variance=W.noiseVariance(times,observations);
 const rawFloor=W.noiseFloor(D,[],variance)/norm,floor=Number.isFinite(rawFloor)?rawFloor:null;
 const explainable=floor!==null&&1-floor>0?1-floor:1;
 const blocks=first.gains.map(g=>{const fit=W.leastSquares(C.A.map(row=>[row[g.term]]),C.b);return {...g,share:g.gain/explainable,coefficient:fit.coefficients[0]/(C.norms[g.term]||1)};});
 const longest=Math.max(...D.windows.map(([a,b])=>b-a)),rows=D.windows.map((w,i)=>({w,i})).filter(({w})=>w[1]-w[0]===longest&&w[0]%longest===0);
 return {blocks,winner:first.addition,floor,explainable,normalized:floor!==null&&1-floor>0,D,rows,x:rows.map(({w})=>(times[w[0]]+times[w[1]])/2)};
}
function soloNumber(value){return Number(value).toLocaleString(language,{maximumSignificantDigits:3,useGrouping:false}).replaceAll('-','−');}
function soloEquation(block){return 'du/dt = '+soloNumber(block.coefficient)+(block.term?' '+terms[block.term]:'');}
function initSolo(){
 const model=soloModel(teaching.observed,measuredTime,LIVE,LIVE.featured[0]),buttons=[];
 const percent=value=>(value*100).toLocaleString(language,{minimumFractionDigits:1,maximumFractionDigits:1})+' %';
 function select(term){
  const block=model.blocks.find(b=>b.term===term);buttons.forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.term===term)));
  const target=$('solo-chart');
  chart(target,[{x:model.x,y:model.rows.map(({i})=>model.D.b[i]),kind:'data',style:'dots'},
   {x:model.x,y:model.rows.map(({i})=>block.coefficient*model.D.A[i][term]),kind:'model'}],{legend:false,yLabel:tr('x9_change'),horizontalYLabel:true,xDomain:[measuredTime[0],measuredTime.at(-1)],dotRadius:5.5});
  const legend=el('div',undefined,'solo-legend');legend.dataset.claim='review';legend.append(el('span','● '+tr('x9_measured')),el('span','━ '+tr('x9_prediction',{block:terms[term]})));target.append(legend);
  $('solo-equation').textContent=soloEquation(block);$('solo-equation').dataset.term=String(term);
 }
 model.blocks.forEach(block=>{const button=el('button',undefined,'solo-bar'+(block.term===model.winner?' winner':''));button.type='button';button.dataset.term=String(block.term);button.dataset.gain=String(block.gain);button.dataset.share=String(block.share);
  const track=el('span',undefined,'solo-track'),fill=el('span');fill.style.width=(block.share*100)+'%';track.append(fill);
  button.append(el('span',terms[block.term]),track,el('span',percent(block.share)));button.addEventListener('click',()=>select(block.term));buttons.push(button);$('solo-bars').append(button);
 });
 $('solo-caption').textContent=tr(model.normalized?'x9_caption':'x9_total');
 $('solo-result').textContent=tr('x9_result',{winner:terms[model.winner],explain_constant:model.winner===0?tr('x9_constant'):''});
 window.WispSolo={model,select};select(model.winner);
}
function play(){
 const observations=measuredNoise(teaching?.sigma||.03),limit=2*Math.max(...observations.map(Math.abs)),indices=enabled.map((v,i)=>v?i:-1).filter(i=>i>=0),c=indices.map(i=>coeff[i]);
 const tex=equation(indices,c);math($('play-equation'),tex);
 const curve=rk4(measuredTime,[observations[0]],x=>[W.basis(x[0]).reduce((s,v,i)=>s+(enabled[i]?v*coeff[i]:0),0)]).map(x=>x[0]);
 const readerState={t:measuredTime,curve,clipped:curve.map(v=>Number.isFinite(v)&&Math.abs(v)<=limit?v:NaN)};
 const series=[{x:measuredTime,y:observations,kind:'data',style:'dots',label:tr('j214')},{x:measuredTime,y:readerState.clipped,kind:'model',label:tr('x8_true')}];
 if(solutionShown)series.push({x:measuredTime,y:measuredTruth,kind:'truth',style:'dashed'});
 chart($('play-chart'),series,{legend:false});
 const score=observationR2(curve,observations);
 const clipped=curve.some(v=>!Number.isFinite(v)||Math.abs(v)>limit),status=$('play-status');status.dataset.score=Number.isFinite(score)?String(score):'unavailable';
 status.textContent=Number.isFinite(score)?tr('x6_meter',{value:fmt(score,4),grade:tr(score>=.98?'x6_veryclose':score>=.9?'x6_close':score>=.5?'x6_nearer':'x6_far')}):tr('x6_unstable');
 $('challenge-meter').value=Number.isFinite(score)?Math.max(0,Math.min(1,score)):0;
 if(clipped&&Number.isFinite(score))status.textContent+=' '+tr('j199');

}
$('challenge-hint').addEventListener('click',()=>{if(hintCount>=3)return;hintCount++;$('challenge-hints').append(el('li',tr('x6_hint'+hintCount)));$('challenge-hint').disabled=hintCount===3;});
$('play-reset').addEventListener('click',()=>{toggleSolution(false);coeff.splice(0,6,...initialCoefficients);enabled.splice(0,6,...Array(6).fill(false));termControls.forEach(({check,sync},i)=>{check.checked=enabled[i];sync();});play();});play();
options($('dimensions'),LIVE.catalogues.map(c=>c.dim));
function catalogue(){const c=LIVE.catalogues.find(c=>c.dim===+$('dimensions').value);$("combination-count").textContent=tr('j202',{v0:(c.count),v1:(BigInt(c.combinations).toLocaleString(language)),v2:(c.dim),v3:(c.dim===1?'':'s')});$("catalogue-list").textContent=c.terms.join(' · ');}
$('dimensions').addEventListener('change',catalogue);catalogue();
options($("window-length"),LIVE.windows,v=>tr('j205',{v0:(v),v1:(v===1?'':'s')}));$("window-length").value=16;
function finiteDifference(x){const time=measuredTime;return x.map((v,i)=>i===0?(x[1]-v)/(time[1]-time[0]):i===x.length-1?(v-x[i-1])/(time[i]-time[i-1]):(x[i+1]-x[i-1])/(time[i+1]-time[i-1]));}
function redrawNoise(){const time=measuredTime,truth=measuredTruth;sigma=+$("noise-level").value;$("noise-value").value=pct(sigma);noisy=measuredNoise(sigma);$("noise-provenance").textContent=teaching?(sigma===teaching.sigma?tr('j209',{v0:(cellName(teaching.cell_id))}):tr('j210',{v0:(cellName(teaching.cell_id)),v1:(pct(teaching.sigma))})):tr('j211');chart($("noise-chart"),[{x:time,y:truth,kind:'truth',label:tr('j213')},{x:time,y:noisy,kind:'data',style:'dots',label:tr('j214')}],{title:tr('j215')});chart($("derivative-chart"),[{x:time,y:truth.map(v=>demo.constants[0]*v*(1-v/demo.constants[1])),kind:'truth',label:tr('j217')},{x:time,y:finiteDifference(noisy),kind:'data',style:'dots',label:tr('j218')}],{title:tr('j219'),yLabel:tr('j220')});weakDraw();computePath();}
function weakDraw(){const time=measuredTime,truth=measuredTruth;const length=+$("window-length").value;$("window-start").max=time.length-length-1;const start=Math.min(+$("window-start").value,time.length-length-1);$("window-start").value=start;const end=start+length;$("window-start-value").value=start;
  const view=chart($("window-chart"),[{x:time,y:truth,kind:'truth',style:'dashed',label:tr('j213')},{x:time,y:noisy,kind:'data',label:tr('j214')}],{title:tr('j224'),highlight:[time[start],time[end]]});
  if(view){const drag=e=>{const box=view.svg.getBoundingClientRect(),vx=(e.clientX-box.left)/box.width*view.width,tt=view.xmin+(vx-view.pad.l)/(view.width-view.pad.l-view.pad.r)*(view.xmax-view.xmin);let best=0;time.forEach((t,i)=>{if(Math.abs(t-tt)<Math.abs(time[best]-tt))best=i;});$("window-start").value=Math.min(best,time.length-length-1);weakDraw();};view.svg.style.touchAction="pan-y";view.svg.addEventListener('pointerdown',e=>{view.svg.setPointerCapture?.(e.pointerId);drag(e);});view.svg.addEventListener('pointermove',e=>{if(e.buttons===1)drag(e);});}
  const design=W.design(time,noisy),clean=W.design(time,truth),rowIndex=design.windows.findIndex(([a,b])=>a===start&&b===end),row=design.A[rowIndex];
  $("window-summary").textContent=tr('j227',{v0:(fmt(design.b[rowIndex])),v1:(fmt(clean.b[rowIndex]))});
  $("integral-plots").replaceChildren();terms.forEach((name,j)=>{const box=el('div');box.append(el('h4',tr('j229',{v0:(name),v1:(fmt(row[j])),v2:(fmt(clean.A[rowIndex][j]))})));const plot=el('div');box.append(plot);$("integral-plots").append(box);const tx=time.slice(start,end+1),ny=noisy.slice(start,end+1).map(v=>W.basis(v)[j]),cy=truth.slice(start,end+1).map(v=>W.basis(v)[j]);chart(plot,[{x:tx,y:cy,kind:'truth',style:'dashed',label:tr('j230')},{x:tx,y:ny,kind:'data',label:tr('j231')}],{title:tr('j232',{v0:(name)}),yLabel:tr('term_axis',{v0:name}),areas:[{x:tx,y:ny}]});});
  const table=el('table'),head=el('tr');[tr('j233'),...terms,'Δu'].forEach(t=>head.append(el('th',t)));table.append(head);
  const previews=[rowIndex,...design.windows.map((_,i)=>i).filter(i=>i!==rowIndex).slice(0,4)];
  previews.forEach(i=>{const tr=el('tr'),cell=el('td'),button=el('button',design.windows[i].join(' → '));button.type='button';button.addEventListener('click',()=>{const [a,b]=design.windows[i];$("window-start").value=a;$("window-length").value=b-a;weakDraw();});cell.append(button);tr.append(cell);[...design.A[i],design.b[i]].forEach(v=>tr.append(el('td',fmt(v))));table.append(tr);});$('matrix').replaceChildren(table);$("matrix-size").textContent=tr('j235',{v0:(design.A.length.toLocaleString(language)),v1:(design.A[0].length),v2:(LIVE.windows.join(', '))});
}
["window-length","window-start"].forEach(id=>$(id).addEventListener('input',weakDraw));
options($("path-example"),['illustration',...LIVE.references.map(r=>r.cell_id)],id=>id==='illustration'?tr('j237'):`${cellName(id)}${LIVE.references.find(r=>r.cell_id===id).available?'':tr('j238')}`);
function computePath(){const choice=$("path-example").value;try{pathError=null;if(choice==='illustration'){currentPath=W.path(measuredTime,noisy,LIVE);$("path-provenance").textContent=tr('j242',{v0:(teaching&&sigma===teaching.sigma?tr('j240')+cellName(teaching.cell_id):tr('j241')),v1:(pct(sigma)),v2:(LIVE.cap),v3:(LIVE.sse_stop),v4:(LIVE.backward_fraction)});}else{const r=LIVE.references.find(r=>r.cell_id===choice);if(!r.available){currentPath=null;pathError=tr('j243');$("path-provenance").textContent=pathError;}else{currentPath=W.path(r.t,r.x,LIVE);$("path-provenance").textContent=tr('j244',{v0:(cellName(r.cell_id))});}}}catch(err){currentPath=null;pathError=tr('j245',{v0:(err.message)});$("path-provenance").textContent=pathError;}
  $("path-step").max=currentPath?.steps.length||0;$("path-step").value=Math.min(+$("path-step").value,currentPath?.steps.length||0);pathDraw();}
function bars(target,gains,winner){
  const plot=el('div',undefined,"gain-bars"),max=Math.max(...gains.map(g=>g.gain),1e-30);
  plot.setAttribute('role','img');plot.setAttribute("aria-label",tr('j248'));
  plot.append(el('div',tr('j249'),"gain-axis"));
  gains.slice().sort((a,b)=>a.term-b.term).forEach(g=>{
    const row=el('div',undefined,"gain-row"),meter=el('div',undefined,"gain-track"),bar=el('span');
    bar.style.width=`${Math.max(0,g.gain/max)*100}%`;bar.style.background=g.term===winner?'var(--model)':'var(--data)';meter.append(bar);
    row.append(el('span',terms[g.term]),meter,el('span',`${g.term===winner?'> ':''}${pct(g.gain)}`,"gain-value"));plot.append(row);
  });target.replaceChildren(plot);
}
function pathDraw(){const n=+$("path-step").value;$("step-value").value=n;$("next-step").disabled=!currentPath||n>=currentPath.steps.length;if(!currentPath){$("gain-chart").replaceChildren();$("path-equation").textContent='';$("residual-chart").replaceChildren();$("path-event").textContent=pathError;$("residual-value").textContent='';return;}const step=currentPath.steps[n-1],next=currentPath.steps[n];bars($("gain-chart"),step?.gains||next?.gains||[],step?.addition);math($("path-equation"),equation(step?.support||[],step?.coefficients||[]));$("path-event").textContent=step?tr('j263',{v0:(terms[step.addition]),v1:(step.removed.length?tr('j261',{v0:(step.removed.map(i=>terms[i]).join(', '))}):tr('j262'))}):tr('j264');
  const residual=[1,...currentPath.steps.slice(0,n).map(s=>s.remaining)];chart($("residual-chart"),[{x:residual.map((_,i)=>i),y:residual,kind:'residual',label:tr('j265')}],{title:tr('j266'),xLabel:tr('j267'),yLabel:tr('j268'),zeroBase:true});$("residual-value").textContent=tr('j269',{v0:(pct(residual.at(-1)))});}
$("path-example").addEventListener('change',computePath);$("path-step").addEventListener('input',pathDraw);$("next-step").addEventListener('click',()=>{$("path-step").value=Math.min(+$("path-step").value+1,+$("path-step").max);pathDraw();});
if(MANIFEST.foba_cell){$("recorded-foba").append(el('p',tr('j271',{v0:(cellName(MANIFEST.foba_cell))})));MANIFEST.foba_events.forEach(e=>$("recorded-foba").append(el('p',tr('recorded_step',{v0:e.step,v1:e.added.map(i=>terms[i-1]).join(', '),v2:e.removed.map(i=>terms[i-1]).join(', ')}))));MANIFEST.foba_states.forEach(s=>{const e=s.equations[0],box=el('div',undefined,'math');math(box,`\\text{${tr('h083')} }${s.step}: `+equation(e.basis_indices.map(i=>i-1),e.coefficients));$("recorded-foba").append(box);});}else $("recorded-foba").append(el('p',tr('j272')));
$("noise-level").addEventListener('input',redrawNoise);redrawNoise();
// Results schema is protocol-independent: swapping results.json replaces provenance and evidence.
const prov=RESULTS.provenance;
$("provenance-banner").textContent=prov.status==='interim'?tr('j274',{v0:(prov.protocol)}):tr('result_status',{v0:prov.status,v1:prov.protocol});
Object.entries(prov).filter(([k])=>['protocol','protocol_commit','git_hash','campaign','status','baseline_reference_sha256','baseline_source'].includes(k)).forEach(([k,v])=>{$('provenance').append(el('dt',tr('provenance_'+k)),el('dd',k==='status'?tr('status_'+v):v));});
const comparison=RESULTS.comparison||{status:"pending",rates:[]};
$("comparison-status").textContent=comparison.status==='available'?tr('j277'):tr('j278');
const resultRates=[...RESULTS.rates,...(comparison.status==='available'?comparison.rates.map(r=>({...r,configuration:r.configuration||r.comparison,n_cells:r.n_cells||r.denominator})):[])];
const methodLabel=m=>RESULTS.method_labels?.[m]||(/^W1(?:-interp)?:/.test(m)?`WSINDy ${m}`:m);
const axes=RESULTS.axes||[];
for(const axis of axes){const label=el('label',axis.label),select=el('select');select.id=`axis-${axis.key}`;options(select,['all',...axis.values],v=>v==='all'?tr('all'):v);select.addEventListener('change',resultsDraw);label.append(select);$("result-axes").append(label);axis.control=select;}
const axesMatch=row=>axes.every(a=>a.control.value==='all'||String(row[a.key])===a.control.value);
const strata=[...new Set(resultRates.map(r=>r.stratum))];
options($("result-sigma"),[...new Set(resultRates.map(r=>String(r.sigma)))].sort((a,b)=>+a-+b),v=>pct(v));
options($("result-rho"),[...new Set(resultRates.map(r=>String(r.rho)))],v=>v==='pooled'?tr('j282'):fmt(v));
function stratumLabel(stratum){return ({dim1:'1D',dim2:'2D',dim3_feasible:tr('x6_dim3'),dim4:'4D'})[stratum]||stratum.replaceAll('_',' ');}
function conditionCells(stratum){return RESULTS.cells.filter(c=>axesMatch(c.row)&&(!RESULTS.exclude_clean_controls||+c.row.sigma!==0||+c.row.rho!==0)&&c.row.stratum===stratum&&+c.row.sigma===+$("result-sigma").value&&($("result-rho").value==='pooled'||+c.row.rho===+$("result-rho").value));}
function metric(container,row,label,cls=''){const e=el('div',undefined,`metric ${cls}`);e.append(el('b',label));if(!row){e.append(el('small',tr('j283')));container.append(e);return;}e.append(el('div',pct(row.rate)));const meter=el('div',undefined,'meter'),fill=el('span');fill.style.width=`${Math.max(0,Math.min(100,+row.rate*100))}%`;meter.append(fill);e.append(meter);const isSummary=row.configuration==='all_ten';e.append(el('small',isSummary?tr('j284',{v0:(pct(row.min_rate)),v1:(pct(row.max_rate)),v2:(fmt(row.denominator,8))}):tr('cell_count',{v0:fmt(row.numerator,8),v1:fmt(row.denominator,8)})));if(row.method!==RESULTS.primary_method&&!isSummary){const config=el('div',row.configuration,'caption');config.style.overflowWrap='anywhere';e.append(config);}container.append(e);}
function resultsDraw(){const weight=$("result-weight").value;$("metric-key").textContent=tr('j287',{v0:(fmt(RESULTS.score_threshold)),v1:(weightLabel(weight)),v2:(RESULTS.primary_method)});
  $('strata').replaceChildren();for(const stratum of strata){const box=el('article',undefined,'stratum');box.append(el('h3',stratumLabel(stratum)));const cells=conditionCells(stratum),systems=new Set(cells.map(c=>c.system_id)),units=new Set(cells.map(c=>c.row.unit_id));box.append(el('p',tr('j288',{v0:(systems.size),v1:(units.size),v2:(cells.length)}),'caption'));const button=el('button',tr('inspect',{v0:stratumLabel(stratum)}));button.type='button';button.setAttribute("aria-pressed",String(stratum===selectedStratum));button.addEventListener('click',()=>{selectedStratum=stratum;resultsDraw();$("system-select").focus();});box.append(button);
    const rows=resultRates.filter(r=>axesMatch(r)&&r.stratum===stratum&&+r.sigma===+$("result-sigma").value&&(r.rho==='pooled'?$("result-rho").value==='pooled':$("result-rho").value!=='pooled'&&+r.rho===+$("result-rho").value)),groups=new Map();rows.forEach(r=>{const key=`${methodLabel(r.method)} / ${(RESULTS.selected_configuration_methods||[]).includes(r.method)&&r.configuration!=='all_ten'?tr('j290'):r.configuration}${axes.map(a=>` / ${a.label}: ${r[a.key]??tr('unspecified')}`).join('')}`;if(!groups.has(key))groups.set(key,{});groups.get(key)[r.metric]=r;});
    if(!groups.size)box.append(el('p',tr('j291'),'caption'));
    for(const [key,metrics] of groups){const group=el('div',undefined,"rate-row");group.append(el('div',key,"rate-name"));if(metrics.raw_exact||metrics.pruned_exact){const structure=el('div',undefined,"metric-pair");metric(structure,metrics.raw_exact,tr('j295'));metric(structure,metrics.pruned_exact,tr('j296'));group.append(structure);}const curves=el('div',undefined,"metric-pair");metric(curves,metrics[`reconstruction_${weight}_hit`],tr('j297'),'curve');metric(curves,metrics[`generalization_${weight}_hit`],tr('j298'),'curve');group.append(curves);box.append(group);}
    $('strata').append(box);
  }systemsDraw();}
function systemsDraw(){const cells=conditionCells(selectedStratum),ids=[...new Set(cells.map(c=>c.system_id))].sort((a,b)=>a-b);options($("system-select"),ids,id=>systemName(cells.find(c=>c.system_id===id)));cellsDraw();}
function cellsDraw(){const cells=conditionCells(selectedStratum).filter(c=>c.system_id===+$("system-select").value);options($("cell-select"),cells.map(c=>c.row.cell_id),cellName);cellDraw();}
function storedEquation(c){const active=JSON.parse(c.row.active_idxs),params=JSON.parse(c.row.params);let index=0;return active.map((support,eq)=>`\\frac{du_{${eq+1}}}{dt}=`+(support.length?support.map(i=>{const coef=params[index++],term=c.terms[i-1].replaceAll('*','\\,').replace(/u(\d+)/g,'u_{$1}').replace(/\^(\d+)/g,'^{$1}');return `${coef>=0?'+':''}${fmt(coef,4)}\\,${term}`;}).join(' '):'0'));}
function cellDraw(){const c=RESULTS.cells.find(c=>c.row.cell_id===$("cell-select").value);$("cell-detail").replaceChildren();if(!c){$("cell-detail").append(el('p',tr('j301')));return;}const root=$("cell-detail");const provenance=el('details');provenance.dataset.provenance='true';provenance.append(el('summary',tr('h105')),el('p',c.row.cell_id,'caption'));root.append(provenance,el('h3',c.exact?tr('j302'):tr('j303')));(c.truth||[]).forEach(s=>{const e=el('div',undefined,'math');math(e,displayTruth(s));root.append(e);});root.append(el('h3',tr('j304')));storedEquation(c).forEach(tex=>{const e=el('div',undefined,'math');math(e,tex);root.append(e);});
  const score=el('div',undefined,"cell-score"),structure=el('p',tr('structure_scores',{v0:truthLabel(c.row.raw_exact),v1:truthLabel(c.row.pruned_exact)})),curves=el('p',tr('curve_scores',{v0:weightLabel($('result-weight').value),v1:fmt(c.row['reconstruction_r2_'+$('result-weight').value],7),v2:fmt(c.row['generalization_r2_'+$('result-weight').value],7)}));if(c.exact)score.append(structure);score.append(curves);root.append(score);
  if(c.unavailable)root.append(el('p',tr('j309'),'notice'));
  if(c.curves){c.curves.truth[0].forEach((_,j)=>{const plot=el('div');root.append(plot);const series=[{x:c.curves.t,y:c.curves.truth.map(r=>r[j]),kind:'truth',style:'dashed',label:tr('j306')},{x:c.curves.t,y:c.curves.model.map(r=>r[j]),kind:'model',label:tr(MANIFEST.julia_display?.present?'j323':'j307')}];if(c.observed)series.push({x:c.observed.t,y:c.observed.x.map(r=>r[j]),kind:'data',style:'dots',label:tr('j214')});chart(plot,series,{title:tr('j308',{v0:(j+1)})});});}
  else root.append(el('p',tr('j309'),'caption'));
}
["result-sigma","result-rho","result-weight"].forEach(id=>$(id).addEventListener('change',resultsDraw));$("system-select").addEventListener('change',cellsDraw);$("cell-select").addEventListener('change',cellDraw);resultsDraw();window.typesetAll();
window.WispPage={data:DATA,redrawNoise,resultsDraw,computePath,applyLanguage,get language(){return language;}};

// Featured narratives are separate from the replaceable results explorer contract.
const featured=LIVE.featured||[];
function gateText(key,pending){const value=LIVE.gate_status?.[key]||"pending";return value==="pending"?pending:tr('gate_'+({initial_state:'initial',coefficient_bound:'bound'}[key]||key)+'_'+value);}
$("stop-gate").textContent=gateText('stop',tr('j311'));
$("fit-gate").textContent=gateText('initial_state',tr('j313'))+' '+gateText('coefficient_bound',tr('j314'));
const stopFeatures=featured.filter(f=>f.stop_reference);
options($("stop-example"),stopFeatures.map(f=>f.cell_id),cellName);
function stopDraw(){const feature=stopFeatures.find(f=>f.cell_id===$("stop-example").value);if(!feature)return;
 const r=feature.stop_reference,p=W.significancePath(r.t,r.x,r.threshold),D=p.design,norm=D.b.reduce((s,v)=>s+v*v,0),supports=[[],...p.steps.map(s=>s.support)],steps=supports.map((_,i)=>i);
 chart($("stop-chart"),[{x:steps,y:[1,...p.steps.map(s=>s.remaining)],kind:'residual',label:tr('j265')},{x:steps,y:supports.map(s=>W.noiseFloor(D,s,p.variance)/norm),kind:'data',style:'dashed',label:tr('j317')}],{title:tr('j318'),xLabel:tr('j267'),yLabel:tr('j268'),zeroBase:true});
 $("stop-summary").textContent=tr('j320',{v0:(LIVE.cap),v1:(p.steps.length),v2:(fmt(r.threshold,5))});
}
$("stop-example").addEventListener('change',stopDraw);stopDraw();
options($("fit-example"),featured.map(f=>f.cell_id),cellName);
function plotBundle(root,bundle,observed,title){
 if(!bundle){root.append(el('p',tr('j322'),'notice'));if(observed){const plot=el('div');root.append(plot);chart(plot,[{x:observed.t,y:observed.x.map(r=>r[0]),kind:'data',style:'dots',label:tr('j214')}],{title});}return;}
 bundle.truth[0].forEach((_,j)=>{const plot=el('div');root.append(plot);const series=[{x:bundle.t,y:bundle.truth.map(r=>r[j]),kind:'truth',style:'dashed',label:tr('x8_true')},{x:bundle.t,y:bundle.model.map(r=>r[j]),kind:'model',label:tr('j323')}];if(observed)series.push({x:observed.t,y:observed.x.map(r=>r[j]),kind:'data',style:'dots',label:tr('j214')});chart(plot,series,{title:`${title} · u${j+1}`,yLabel:`u${j+1}`});});
}
function fitDraw(reset=false){const feature=featured.find(f=>f.cell_id===$("fit-example").value);if(!feature||!RESULTS.cells.some(c=>c.row.cell_id===feature.cell_id))return;
 $("fit-candidate").max=feature.candidates.length-1;if(reset)$("fit-candidate").value=0;const index=Math.min(+$("fit-candidate").value,feature.candidates.length-1),candidate=feature.candidates[index],row=candidate.row;
 $("fit-index").value=`${index+1} / ${feature.candidates.length}`;math($("fit-equation"),storedEquation({...feature,row,terms:RESULTS.cells.find(c=>c.row.cell_id===feature.cell_id).terms}).join('\\qquad '));
 $("fit-summary").textContent=tr('j330',{v0:(row.candidate_id),v1:(fmt(row.mse,7)),v2:(fmt(candidate.bic,7)),v3:(fmt(candidate.penalty,7)),v4:(row.candidate_id===feature.chosen?tr('j328'):tr('j329'))});
 const valid=feature.candidates.filter(c=>Number.isFinite(c.bic)),chosen=feature.candidates.find(c=>c.row.candidate_id===feature.chosen);
 chart($("bic-chart"),[{x:valid.map(c=>+c.row.k),y:valid.map(c=>c.bic),kind:'model',label:tr('j332')}],{title:tr('j333'),xLabel:tr('j334'),yLabel:'BIC',integerX:true,point:chosen?[+chosen.row.k,chosen.bic]:null});
 $("fit-curves").replaceChildren();plotBundle($("fit-curves"),candidate.curves,RESULTS.cells.find(c=>c.row.cell_id===feature.cell_id)?.observed,tr('j297'));
}
$("fit-example").addEventListener('change',()=>fitDraw(true));$("fit-candidate").addEventListener('input',()=>fitDraw());fitDraw();
for(const feature of featured){const cell=RESULTS.cells.find(c=>c.row.cell_id===feature.cell_id);if(!cell)continue;
 const root=el('article',undefined,'panel'),heading=el('h3',cellName(feature.cell_id));root.append(heading);
 const role=feature.roles.includes('missing_truth')?tr('j336'):feature.roles.includes('generalization_failure')?tr('j337'):feature.roles.includes('exact_dim2')?tr('j338'):tr('j339');
 const interpretation=el('p',role);interpretation.setAttribute('data-claim',feature.roles.includes('missing_truth')?'j336':feature.roles.includes('generalization_failure')?'j337':feature.roles.includes('exact_dim2')?'j338':'j339');root.append(interpretation);
 root.append(el('p',tr('j342',{v0:(truthLabel(cell.row.raw_exact)),v1:(truthLabel(cell.row.pruned_exact)),v2:(truthLabel(cell.row.truth_on_path))})));
 for(const weight of ['arithmetic','variance_weighted'])root.append(el('p',tr('curve_scores',{v0:weightLabel(weight),v1:fmt(cell.row['reconstruction_r2_'+weight],7),v2:fmt(cell.row['generalization_r2_'+weight],7)})));
 if(feature.roles.includes('missing_truth')){
 root.append(el('h4',tr('j343')));root.append(el('p',feature.truth_support.map(eq=>eq.map(i=>cell.terms[i-1]).join(', ')).join(' / ')));
 root.append(el('h4',tr('j344')));feature.path.forEach(p=>root.append(el('p',`${p.step}: ${p.active_idxs.map(eq=>eq.map(i=>cell.terms[i-1]).join(', ')).join(' / ')}`)));}
 const pair=el('div',undefined,"two-plots"),reconstruction=el('div'),generalization=el('div');pair.append(reconstruction,generalization);root.append(pair);
 const candidate=feature.candidates.find(c=>c.row.candidate_id===feature.chosen),curves=candidate?.curves;
 plotBundle(reconstruction,curves,cell.observed,tr('j297'));plotBundle(generalization,curves?.generalization,null,tr('j298'));$("featured-stories").append(root);
}

// WP-X4 presentation only: fixed headline selection, opening and bounded details.
function headlineRows(rows){return rows.filter(r=>['dim1','dim2'].includes(r.stratum)&&+r.sigma===.03&&String(r.rho)!=='pooled'&&+r.rho===0&&['raw_exact','pruned_exact','generalization_arithmetic_hit','generalization_variance_weighted_hit'].includes(r.metric)&&((r.method===RESULTS.primary_method&&r.configuration==='c')||(['sindy','weak_sindy','e_sindy'].includes(r.method)&&r.configuration!=='all_ten')));}
const headline=headlineRows(RESULTS.rates);
window.WispPage.headlineRows=headlineRows;window.WispPage.headline=headline;
// Configuration endpoints always retain their original source row and counts.
function rateEndpoints(rows){const ordered=rows.filter(r=>r.configuration!=='all_ten').slice().sort((a,b)=>+a.rate-+b.rate);return ordered.length?[ordered[0],ordered.at(-1)]:[];}
function metricLabel(key){return ({raw_exact:tr('j295'),pruned_exact:tr('j296')})[key]||tr(key.startsWith('generalization')?'j298':'j297')+' R² > '+fmt(RESULTS.score_threshold)+' ('+weightLabel(key.includes('variance_weighted')?'variance_weighted':'arithmetic')+')';}
function rateChart(target,rows){
 const methods=[...new Set(rows.filter(r=>r.configuration!=='all_ten').map(r=>r.method))],metrics=['pruned_exact','generalization_variance_weighted_hit','generalization_arithmetic_hit'].filter(metric=>rows.some(r=>r.metric===metric));
 const palette=['var(--accent)','#71869a','#9a8980','#8a879e','#83958a','#a49572'];
 const alternatives=el('details');alternatives.dataset.internalScroll='true';alternatives.append(el('summary',tr('x5_table')));const table=el('table');alternatives.append(table);
 if(rows.some(r=>r.metric==='pruned_exact'))target.append(el('p',tr('x5_marks'),'caption'));const plots=el('div',undefined,'rate-plots');target.append(plots);
 const count=r=>pct(r.rate)+' ('+fmt(r.numerator,8)+'/'+fmt(r.denominator,8)+') · '+r.configuration;
 for(const metric of metrics){const group=el('div',undefined,'rate-plot'),height=40+methods.length*28,svg=svgNode('svg',{viewBox:`0 0 540 ${height}`,role:'img',class:'rate-chart','aria-label':metricLabel(metric)});group.append(el('h4',metricLabel(metric)),svg);plots.append(group);
  for(const [i,m] of methods.entries()){const endpoints=rateEndpoints(rows.filter(r=>r.method===m&&r.metric===metric));if(!endpoints.length)continue;const [lo,hi]=endpoints,y=24+i*28,color=palette[(m===RESULTS.primary_method?0:1+Math.max(0,[...new Set(resultRates.map(r=>r.method))].filter(v=>v!==RESULTS.primary_method).indexOf(m)))%palette.length],X=r=>150+360*+r.rate;
   svg.append(svgNode('text',{x:0,y:y+4},({sindy:'SINDy',weak_sindy:'Weak-SINDy',e_sindy:'E-SINDy'})[m]||methodLabel(m)));svg.append(svgNode('line',{x1:150,x2:510,y1:y,y2:y,stroke:'var(--line)'}));
   const mark=svgNode('g',{tabindex:0,'aria-label':methodLabel(m)+' · '+metricLabel(metric)+': '+count(lo)+' – '+count(hi)});const rawText=metric==='pruned_exact'?' · '+metricLabel('raw_exact')+': '+rateEndpoints(rows.filter(r=>r.method===m&&r.metric==='raw_exact')).map(count).join(' – '):'';mark.setAttribute('aria-label',methodLabel(m)+' ? '+metricLabel(metric)+': '+count(lo)+' ? '+count(hi)+rawText);mark.append(svgNode('title',{},methodLabel(m)+': '+count(lo)+' – '+count(hi)+rawText));
   if(m===RESULTS.primary_method)mark.append(svgNode('rect',{x:150,y:y-6,width:Math.max(1,X(hi)-150),height:12,fill:color}));
   else mark.append(svgNode('line',{x1:X(lo),x2:X(hi),y1:y,y2:y,stroke:color,'stroke-width':8}));
   for(const r of endpoints)mark.append(svgNode('line',{x1:X(r),x2:X(r),y1:y-8,y2:y+8,stroke:color,'stroke-width':2}));
   if(metric==='pruned_exact'){const raw=rateEndpoints(rows.filter(r=>r.method===m&&r.metric==='raw_exact'));for(const r of raw)mark.append(svgNode('circle',{cx:X(r),cy:y,r:3,fill:'var(--bg)',stroke:color}));}
   svg.append(mark);const row=el('tr');[methodLabel(m),metricLabel(metric),count(lo)+' – '+count(hi)].forEach(t=>row.append(el('td',t)));table.append(row);
   if(metric==='pruned_exact')for(const r of rateEndpoints(rows.filter(r=>r.method===m&&r.metric==='raw_exact'))){const raw=el('tr');[methodLabel(m),metricLabel('raw_exact'),count(r)].forEach(t=>raw.append(el('td',t)));table.append(raw);}
  }
  for(const [x,label] of [[150,'0%'],[330,'50%'],[510,'100%']])svg.append(svgNode('text',{x,y:height-2,'text-anchor':'middle'},label));
 }
 target.append(alternatives);
}
function headlineDraw(){const panel=$('headline-panel');panel.replaceChildren();for(const stratum of ['dim1','dim2']){const box=el('div',undefined,'headline-stratum');box.append(el('h3',stratum==='dim1'?'1D':'2D'));rateChart(box,headline.filter(r=>r.stratum===stratum));panel.append(box);}}
headlineDraw();
const runningFeature=featured.find(f=>f.roles.includes('running')),runningCell=RESULTS.cells.find(c=>c.row.cell_id===runningFeature?.cell_id);
if(runningCell)math($('challenge-truth-equation'),'\\frac{du}{dt}='+runningCell.truth.map(displayTruth).join('\\qquad ').replaceAll('u_{1}','u'));
initSolo();
$('data-summary').textContent=$('combination-count').textContent;
// One native modal per section: focus is trapped by the browser and scrolling stays inside.
document.querySelectorAll('[data-more]').forEach(button=>button.addEventListener('click',()=>button.parentElement.querySelector('dialog').showModal()));
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
// Chapter one uses the same full design and frozen first-step fit as the retained page.
function chapterError(model,term,c){return model.D.b.reduce((sum,b,i)=>sum+(b-c*model.D.A[i][term])**2,0)/soloDot(model.D.b,model.D.b);}
function chapterParts(model,block){const floor=model.normalized?model.floor:0;return [floor,block.gain,1-floor-block.gain];}
function chapterWindows(length){const t=measuredTime,x=teaching.observed,out=[];for(let a=0;a+length<t.length;a+=length){const b=a+length;out.push({time:(t[a]+t[b])/2,rate:(x[b]-x[a])/(t[b]-t[a]),clean:(teaching.truth[b]-teaching.truth[a])/(t[b]-t[a])});}return out;}
// One persistent SVG. Scene arrays have a fixed topology so axes, points, lines and
// labels interpolate through every transition, including interrupted/reverse ones.
function secondModel(model,t,x,config,feature){
 const live=W.path(t,x,config),step=live.steps[1],record=feature.path[1];
 if(!step||JSON.stringify(step.support)!==JSON.stringify(record.active_idxs[0].map(j=>j-1)))throw Error('Teaching step-2 path differs from recorded supports');
 const first=live.steps[0],C=soloCompress(model.D.A,model.D.b);
 const blocks=step.gains.slice().sort((a,b)=>a.term-b.term).map(g=>{
  const support=[...first.support,g.term].sort((a,b)=>a-b),fit=W.leastSquares(C.A.map(row=>support.map(j=>row[j])),C.b);
  return {...g,support,coefficients:fit.coefficients.map((v,i)=>v/(C.norms[support[i]]||1)),share:(1-first.remaining+g.gain)/model.explainable,remaining:fit.sse/soloDot(model.D.b,model.D.b)};
 });
 return {blocks,winner:step.addition,record,step,constant:model.blocks.find(b=>b.term===first.addition)};
}
// Presentation audit of every removal pass; the numerical search remains W.path.
function thirdModel(model,t,x,config,feature){
 const live=W.path(t,x,config),C=soloCompress(model.D.A,model.D.b),norm=soloDot(model.D.b,model.D.b);
 const fit=support=>{const f=W.leastSquares(C.A.map(row=>support.map(j=>row[j])),C.b);return {support:support.slice(),coefficients:f.coefficients.map((v,i)=>v/(C.norms[support[i]]||1)),sse:f.sse,remaining:f.sse/norm,share:(1-f.sse/norm)/model.explainable};};
 const rounds=live.steps.slice(0,4).map((step,i)=>{
  const record=feature.path[i];
  if(!record||JSON.stringify(step.support)!==JSON.stringify(record.active_idxs[0].map(j=>j-1)))throw Error('Teaching FoBa path differs from recorded supports');
  const before=fit(i?live.steps[i-1].support:[]),added=fit([...before.support,step.addition].sort((a,b)=>a-b));
  const gain=step.gains.find(g=>g.term===step.addition).gain/model.explainable,threshold=config.backward_fraction*gain,probes=[];
  let current=added;
  for(const removed of [...step.removed,null]){
   const costs=current.support.map(term=>({term,fit:fit(current.support.filter(j=>j!==term))})).map(c=>({...c,cost:(c.fit.sse-current.sse)/norm/model.explainable}));
   const eligible=costs.filter(c=>c.cost<threshold).sort((a,b)=>a.cost-b.cost||a.term-b.term);
   if((eligible[0]?.term??null)!==removed)throw Error('Teaching removal audit differs from live path');
   probes.push({model:current,costs,removed});if(removed!==null)current=costs.find(c=>c.term===removed).fit;
  }
  return {before,added,after:fit(step.support),addition:step.addition,removed:step.removed,gain,threshold,probes};
 });
 const truth=feature.truth_support[0].map(j=>j-1);
 if(JSON.stringify(rounds.at(-1).after.support)!==JSON.stringify(truth))throw Error('Teaching FoBa truth differs from recorded support');
 const last=rounds.at(-1).after;
 const next=Array.from({length:model.D.A[0].length},(_,term)=>term).filter(j=>!last.support.includes(j)).map(term=>({term,gain:(last.sse-fit([...last.support,term].sort((a,b)=>a-b)).sse)/norm/model.explainable})).sort((a,b)=>b.gain-a.gain||a.term-b.term)[0];
 return {rounds,truth,next,fit};
}
function secondNumber(value){return Number(value).toLocaleString(language,{maximumSignificantDigits:3,maximumFractionDigits:12,useGrouping:false}).replaceAll('-','−');}
function secondEquation(support,coefficients){return 'du/dt = '+coefficients.map((c,i)=>(i?(c<0?' − ':' + '):c<0?'−':'')+secondNumber(Math.abs(c))+(support[i]?'·'+terms[support[i]]:'')).join('');}
function initChapterOne(){
 if(!$('p-c1-data'))return;
 const m=window.WispSolo.model,t=measuredTime,x=teaching.observed,clean=teaching.truth,n=t.length;
 const legacyStates=['data','noise-visible','slope','secants','windows','error-empty','fit','every','noise-why','noise-estimate','percent','solution'];
 const states=['data','slope','noise-visible','secants','windows','error-empty','fit','every','noise-estimate','percent','solution'];
 const constant=m.blocks.find(b=>b.term===0),winner=m.blocks.find(b=>b.term===m.winner),norm=soloDot(m.D.b,m.D.b);
 const two=secondModel(m,t,x,LIVE,LIVE.featured[0]),twoStates=['c2-standing','c2-residual','c2-joint','c2-error','c2-solution','c2-all'];
 const three=thirdModel(m,t,x,LIVE,LIVE.featured[0]),threeStates=['c3-standing','c3-probe','c3-threshold','c3-linear','c3-quadratic','c3-compare','c3-next'];
 const twoWinner=two.blocks.find(b=>b.term===two.winner),joint=two.blocks.find(b=>b.term===1);
 const remainingBlocks=two.blocks.filter(b=>b.term!==joint.term),sortAt=remainingBlocks.length*2500;
 // Last step of chapter two: the same round (try every open block, refit jointly, keep the best)
 // repeated until every block is in. Additions only; the cleanup step is chapter three's subject.
 const twoC=soloCompress(m.D.A,m.D.b),fitSupport=support=>{const f=W.leastSquares(twoC.A.map(row=>support.map(j=>row[j])),twoC.b);return {support,coefficients:f.coefficients.map((v,i)=>v/(twoC.norms[support[i]]||1)),remaining:f.sse/norm};};
 const rounds=[];
 for(let base={support:twoWinner.support,coefficients:twoWinner.coefficients,remaining:twoWinner.remaining,term:two.winner,share:twoWinner.share};base.support.length<terms.length;){
  const candidates=terms.map((_,j)=>j).filter(j=>!base.support.includes(j)).map(j=>{const f=fitSupport([...base.support,j].sort((a,b)=>a-b));return {...f,term:j,share:(1-f.remaining)/m.explainable};});
  const best=candidates.reduce((a,b)=>b.remaining<a.remaining?b:a);rounds.push({base,candidates,winner:best});base=best;
 }
 const trialMs=750,tailMs=1300,roundStart=[0];rounds.forEach(R=>roundStart.push(roundStart.at(-1)+R.candidates.length*trialMs+tailMs));
 function allFrame(seq){
  const r=rounds.findIndex((_,k)=>seq<roundStart[k+1]);
  if(r<0){const R=rounds.at(-1);return {r:rounds.length-1,R,done:true,j:R.candidates.length,tl:tailMs,tail:true,from:R.winner,to:R.winner,morph:1,join:1,fade:0};}
  const R=rounds[r],local=seq-roundStart[r],k=R.candidates.length,fade=clamp(local/300);
  if(local<k*trialMs){const j=Math.floor(local/trialMs),tl=local%trialMs;return {r,R,j,tl,tail:false,from:j?R.candidates[j-1]:R.base,to:R.candidates[j],morph:ease(tl/300),join:0,fade};}
  const tl=local-k*trialMs;return {r,R,j:k,tl,tail:true,from:R.candidates[k-1],to:R.winner,morph:ease(tl/400),join:ease((tl-500)/800),fade};
 }
 const pct=v=>(100*v).toLocaleString(language,{minimumFractionDigits:1,maximumFractionDigits:1})+' %';
 const variance=W.noiseVariance(t,x),relative=variance.reduce((s,v,i)=>s+Math.sqrt(v)/Math.abs(x[i]),0)/n;
 const noise=x.map((v,i)=>v-clean[i]),actual=m.D.windows.reduce((s,[a,b])=>s+(noise[b]-noise[a])**2,0)/norm;
 // The same scaled cubic basis as noiseVariance; only its fitted values are
 // needed for the illustration (variance still comes from the frozen function).
 function local(i){const start=Math.min(Math.max(i-4,0),n-9),ts=t.slice(start,start+9),xs=x.slice(start,start+9),scale=Math.max(...ts.map(v=>Math.abs(v-t[i])));
  const coefficients=W.leastSquares(ts.map(v=>[0,1,2,3].map(p=>((v-t[i])/scale)**p)),xs).coefficients;
  const value=v=>coefficients.reduce((s,c,p)=>s+c*((v-t[i])/scale)**p,0);
  return {center:i,start,ts,xs,value,deviation:x[i]-value(t[i])};}
 const examples=Array.from({length:5},(_,j)=>local(Math.round(n/3)+j));
 // At most four uniformly spaced catalogue indices, including shortest and longest.
 // Selection depends only on the live window list, never authored lengths.
 const allLengths=[...new Set(LIVE.windows)].sort((a,b)=>a-b);
 const longerLengths=Array.from({length:Math.min(4,allLengths.length)},(_,i)=>allLengths[Math.round(i*(allLengths.length-1)/Math.max(1,Math.min(4,allLengths.length)-1))]);
 const args={n,t0:fmt(t[0]),t1:fmt(t.at(-1)),noise:pct(teaching.sigma),lengths:longerLengths.join(', '),floor:pct(m.floor),explainable:pct(m.explainable),winner:terms[m.winner],meaning:tr(m.winner===0?'x10_constant':'x10_other')};
 const textKeys=['x12_text_0','x12_text_1','x12_text_2','x12_text_3','x12_text_4','x10_text_2','x10_text_3','x10_text_4','x12_text_8','x10_text_5','x10_text_6'];
 textKeys.forEach((key,i)=>{$('c1-story-text-'+i).textContent=tr(key,args);});
 $('c1-story-text-6').textContent+=' '+tr('x10_direct');
 $('c1-noise-why-text').textContent=tr('x12c_noise_text');
 const result=$('c1-noise-result');result.textContent=tr('x12_noise_result',{est:pct(relative),true:pct(teaching.sigma),floor:pct(m.floor)})+' '+tr('x12_actual',{actual:pct(actual)});
 $('c1-story-text-9').textContent+=' '+tr(m.normalized?'x10_r2':'x10_fallback');
 $('c1-story-text-10').textContent+=' '+tr('x10_next');
 document.querySelectorAll('[data-c1-eye]').forEach(e=>e.textContent=tr('x10_eye',{i:e.dataset.c1Eye,n:states.length}));
 const twoArgs={before:pct(constant.share),after:pct(twoWinner.share),maximum:Math.max(...x.map(v=>W.basis(v)[two.winner])).toLocaleString(language,{maximumSignificantDigits:2}),term:terms[two.winner],c:soloNumber(constant.coefficient)};
 Array.from({length:6},(_,i)=>i).forEach(i=>{
  $('c2-text-'+i).textContent=tr('x13_text_'+i,twoArgs);
 });
 document.querySelectorAll('[data-c2-eye]').forEach(e=>e.textContent=tr('x10_eye',{i:e.dataset.c2Eye,n:twoStates.length}));
 $('c2-closing').textContent=tr('x13_closing');
 const allArgs={count:terms.length,second:pct(twoWinner.share),third:pct(rounds[0].winner.share),last:pct(rounds.at(-1).winner.share)};
 [0,1].forEach(i=>{$('c2-all-text-'+i).textContent=tr('x16_text_'+i,allArgs);});
 document.querySelectorAll('[data-c3-eye]').forEach(e=>e.textContent=tr('x10_eye',{i:e.dataset.c3Eye,n:threeStates.length}));
 const threeArgs={share:pct(three.rounds[1].after.share),linear:terms[three.rounds[2].addition],quadratic:terms[three.rounds[3].addition],constant:terms[three.rounds[2].removed[0]],cubic:terms[three.rounds[3].removed[0]],roundLinear:three.rounds.indexOf(three.rounds[2])+1,roundQuadratic:three.rounds.indexOf(three.rounds[3])+1,fraction:secondNumber(LIVE.backward_fraction),next:terms[three.next.term],gain:secondNumber(100*three.next.gain)+' %'};
 threeStates.forEach((_,i)=>{ $('c3-title-'+i).textContent=tr('x17_title_'+i,threeArgs);$('c3-text-'+i).textContent=tr('x17_text_'+i,threeArgs);});
 const teachingCell=RESULTS.cells.find(c=>c.row.cell_id===teaching.cell_id),truthDemo=LIVE.illustrations.find(d=>d.system_id===teachingCell.system_id);
 // The teaching system's stored logistic constants, not fitted result-row params.
 const truthCoefficients=[truthDemo.constants[0],-truthDemo.constants[0]/truthDemo.constants[1]];
 const host=$('c1-stage'),svg=svgNode('svg',{viewBox:'0 0 800 480',role:'img',class:'story-svg'});host.append(svg);const caption=el('figcaption',tr('x10_caption'),'story-caption');caption.dataset.claim='review';host.append(caption);
 const clock=window.WispStoryClock||{now:()=>performance.now(),request:fn=>requestAnimationFrame(fn),cancel:id=>cancelAnimationFrame(id)};
 const clamp=v=>Math.max(0,Math.min(1,v)),ease=v=>{v=clamp(v);return v*v*(3-2*v);},mix=(a,b,s)=>a+(b-a)*s;
 // Scene record: [x,y,...,opacity]; all paths retain the same number of vertices.
 const nodes=[],blank=[];
 function node(tag,attrs,geometry,initial){const e=svgNode(tag,attrs);svg.append(e);nodes.push({e,geometry});blank.push(initial);return nodes.length-1;}
 const points=(count)=>Array.from({length:count},()=>[64,400]).flat();
 const path=(cls,count=n)=>node('path',{class:cls},'path',[...points(count),0]);
 const line=cls=>node('line',{class:cls},'line',[64,400,64,400,0]);
 const dot=(cls,r=2.5)=>node('circle',{class:cls,r},'dot',[64,400,0]);
 const label=(cls='')=>node('text',{class:cls,'data-claim':'review'},'text',[64,20,0]);
 const axisLines=Array.from({length:12},()=>line('story-grid'));
 const axisLabels=Array.from({length:18},()=>label('story-axis'));
 const data=t.map(()=>dot('measurement-dot')),slopeDots=Array.from({length:n-1},()=>dot('story-slope',2.8));
 const truthPath=path('story-truth'),predictionPath=path('story-prediction'),bandTop=path('story-band',2*n),bandBottom=path('story-band-unused');
 const sticks=t.map(()=>line('story-residual')),triangle=Array.from({length:3},()=>line('story-triangle'));
 const lengthColours=['#3369c7','#ab4d9a','#b86a12','#008b91'];
 const lengthClouds=longerLengths.map((length,j)=>({length,rows:chapterWindows(length),dots:Array.from({length:n-1},()=>{const id=dot('story-length-slope',3);nodes[id].e.style.fill=lengthColours[j];return id;}),label:label('story-length-key'),bar:node('rect',{class:'story-length-rms'},'rect',[0,0,0,0,0]),value:label('story-length-key')}));
 const lengthTitle=[label('story-length-key'),label('story-length-key'),label('story-length-key')];
 const lengthRms=lengthClouds.map(c=>Math.sqrt(c.rows.reduce((sum,r)=>sum+(r.rate-r.clean)**2,0)/c.rows.length)),rmsMax=Math.max(...lengthRms);
 const historyTriangles=Array.from({length:8},()=>Array.from({length:3},()=>line('story-triangle story-history')));
 const zoomBox=node('rect',{class:'story-zoom-box'},'rect',[64,42,0,0,0]);
 const legend=[label('story-neighbour-label'),label('story-long-label')];
 const optimumPath=path('story-optimum'),optimumMarker=dot('story-optimum-dot',5),optimumLabel=label('story-optimum-label');
 const sumLabels=[label('story-noise-readout'),label('story-noise-readout'),label('story-noise-readout')];
 const legLabels=[label('story-leg-label'),label('story-leg-label')];
 const curveAxes=[line('story-grid story-curve-axis'),line('story-grid story-curve-axis')],curveTicks=Array.from({length:7},()=>label('story-axis story-curve-label'));
 const triangleLabels=[label('story-delta'),label('story-delta'),label('story-length')];
 const clipped=Array.from({length:n-1},()=>path('story-clipped',3)),clippedLabel=label();
 const marker=dot('story-marker',6),ring=dot('story-ring',10),tangent=line('story-tangent'),localPath=path('story-cubic',61);
 const windowBox=node('rect',{class:'story-window'},'rect',[64,40,0,0,0]);
 const readout=label(),truthLabel=label(),equation=label('story-equation'),errorLabel=label(),noiseLabel=label();
 const errorBar=node('rect',{class:'story-error'},'rect',[64,426,0,14,0]);
 const curvePath=path('story-prediction',81),curveMarker=dot('story-marker',5),curveLabel=label();
 const slots=m.blocks.map(()=>({bar:node('rect',{class:'story-slot'},'rect',[64,70,0,15,0]),text:label(),value:label()}));
 const twoSlots=two.blocks.map(()=>({bar:node('rect',{class:'c2-slot'},'rect',[64,70,0,15,0]),text:label(),value:label()}));
 const pathTitle=label('story-arithmetic'),pathLabels=terms.map(()=>[label('story-arithmetic'),label('story-arithmetic')]);
 const deviationBox=node('rect',{class:'story-deviations'},'rect',[590,42,195,180,0]);
 const deviationLabels=[label('story-deviation')],deviationDot=node('rect',{class:'story-contribution'},'rect',[0,0,10,10,0]);
 const squareBars=t.map(()=>node('rect',{class:'story-square'},'rect',[0,0,0,0,0]));
 const arithmeticLabels=Array.from({length:6},()=>label('story-arithmetic'));
 const smooth=t.map((v,i)=>local(i).value(v)),deviations=x.map((v,i)=>v-smooth[i]);
 const squarePrefix=[0];deviations.forEach(v=>squarePrefix.push(squarePrefix.at(-1)+v*v));
 const defs=svgNode('defs',{}),clip=svgNode('clipPath',{id:'story-top-clip'}),clipRect=svgNode('rect',{});clip.append(clipRect);defs.append(clip);svg.append(defs);
 // Lines of the lower panel span the full series; keep them inside the plot's horizontal extent when zoomed.
 const xClip=svgNode('clipPath',{id:'story-x-clip'}),xClipRect=svgNode('rect',{});xClip.append(xClipRect);defs.append(xClip);nodes[predictionPath].e.setAttribute('clip-path','url(#story-x-clip)');
 for(const id of [...data,...sticks,truthPath,bandTop,localPath,windowBox,ring,tangent,marker,...triangle,...historyTriangles.flat(),zoomBox])nodes[id].e.setAttribute('clip-path','url(#story-top-clip)');
 const stack=[0,1,2].map(i=>({bar:node('rect',{class:'story-part-'+i},'rect',[64,70,0,42,0]),text:label()}));
 const longest=Math.max(...LIVE.windows),longRows=chapterWindows(longest);
 const rates=chapterWindows(1),trueRates=t.map((v,i)=>{const a=Math.max(0,i-1),b=Math.min(n-1,i+1);return (clean[b]-clean[a])/(t[b]-t[a]);});
 const uRange=[Math.min(...x)*.95,Math.max(...x)*1.05],rateBound=4*Math.max(...trueRates.map(Math.abs));
 const changeBound=Math.max(...m.rows.map(({i})=>Math.abs(m.D.b[i])))*1.15||1;
 const fitMin=0,fitMax=2*constant.coefficient;
 const blockCurves=new Map(m.blocks.map(block=>{const values=Array.from({length:81},(_,i)=>2*block.coefficient*i/80),errs=values.map(v=>chapterError(m,block.term,v));return [block.term,{values,errs,maximum:Math.max(...errs)}];}));
 const curveValues=Array.from({length:81},(_,i)=>fitMin+(fitMax-fitMin)*i/80),curveErrors=curveValues.map(v=>chapterError(m,0,v)),curveMaximum=Math.max(...curveErrors);
 const noisePause=0,jointPause=4000;
 // Noise sweep: zoom in, six points slowly, then an accelerating sweep over all points.
 const noiseIn=800,noiseSlow=6,noiseSlowEnd=noiseIn+noiseSlow*1000,noiseFastEnd=noiseSlowEnd+3000;
 const noiseCount=seq=>seq<noiseIn?0:seq<noiseSlowEnd?(seq-noiseIn)/1000:noiseSlow+(n-noiseSlow)*clamp((seq-noiseSlowEnd)/3000)**2;
 const durations={data:900,'noise-visible':2300,slope:3800,secants:16100,windows:12900,'error-empty':2900,fit:4900,every:16900,'noise-why':900,'noise-estimate':noiseFastEnd+4700,percent:900,solution:900};
 Object.assign(durations,{'c2-standing':900,'c2-residual':3900,'c2-joint':jointPause+sortAt+1900,'c2-every':sortAt+1900,'c2-error':3900,'c2-solution':900,'c2-all':900+roundStart.at(-1)+1200});
 Object.assign(durations,{'c3-standing':1200,'c3-probe':3600,'c3-threshold':3600,'c3-linear':16000,'c3-quadratic':16000,'c3-compare':4200,'c3-next':4200});
 const c3Chips=terms.map(()=>({box:node('rect',{class:'c3-chip',rx:6},'rect',[0,0,0,0,0]),text:label('c3-chip-label')}));
 const c3Bars=terms.map(()=>({bar:node('rect',{class:'c3-cost'},'rect',[0,0,0,0,0]),name:label(),value:label(),status:label()}));
 const c3GainBar=node('rect',{class:'c3-new-gain'},'rect',[0,0,0,0,0]),c3GainName=label(),c3GainValue=label();
 const c3Line=line('c3-threshold'),c3Threshold=label('c3-threshold-label'),c3Status=label(),c3Share=label(),c3Gain=label(),c3Axis=label(),c3Zero=label(),c3Max=label();
 const c3Paths=Array.from({length:8},()=>({box:node('rect',{class:'c3-candidate',rx:6},'rect',[0,0,0,0,0]),text:label()}));
 const c3Headers=[label(),label()],c3Truth=label(),c3Weak=label(),c3Coefficients=three.truth.map(()=>label());
 const c3Zoom={title:label('c3-zoom-title'),y:label(),value:label(),max:label(),zero:label(),axis:line('story-grid'),base:line('story-grid'),threshold:line('c3-threshold c3-zoom-threshold'),x:label(),bars:terms.map(()=>({bar:node('rect',{class:'c3-zoom-bar'},'rect',[0,0,0,0,0]),cut:line('c3-cut'),name:label()}))};
 const c3RoundBars=Array.from({length:5},(_,j)=>({bar:node('rect',{class:'c3-round-gain'+(j===4?' not-taken':'')},'rect',[0,0,0,0,0]),name:label(),value:label(),round:label()}));
 const c3CostX=label();
 const c3RoundAxes=[line('story-grid'),line('story-grid')],c3RoundX=label(),c3RoundY=label(),c3NotTaken=label();

 nodes[c3NotTaken].e.setAttribute('text-anchor','end');
 // Chapter two shares the persistent topology, renderer, axes, windows and clock.
 // Divide weak changes and design rows by each displayed window's duration to
 // show slopes; fitting still uses ALL original windows in unscaled weak units.
 const slopeRows=m.rows.map(({w,i})=>({i,time:(t[w[0]]+t[w[1]])/2,dt:t[w[1]]-t[w[0]],rate:m.D.b[i]/(t[w[1]]-t[w[0]]),sd:Math.sqrt(variance[w[0]]+variance[w[1]])/(t[w[1]]-t[w[0]])}));
 const predict=(block,row)=>block.support.reduce((sum,j,k)=>sum+block.coefficients[k]*m.D.A[row.i][j]/row.dt,0);
 const slopeExtent=Math.max(...slopeRows.flatMap(r=>[Math.abs(r.rate),...two.blocks.map(b=>Math.abs(predict(b,r))),Math.abs(constant.coefficient)+r.sd]))*1.15;
 function ranking(ordered,completed,phase,initial=[]){
  const count=Math.min(ordered.length,Math.max(0,Math.floor(completed))),before=initial.concat(ordered.slice(0,count)),after=initial.concat(ordered.slice(0,Math.min(ordered.length,count+1)));
  const order=known=>known.slice().sort((a,b)=>b.share-a.share).concat(ordered.filter(b=>!known.includes(b)));
  const from=order(before),to=order(after),blend=ease((phase-2000)/500);
  const moves=from.some((b,i)=>to[i]!==b);
  return {position:b=>mix(from.indexOf(b),to.indexOf(b),blend),sorting:moves&&blend>0&&blend<1};
 }
 function secondScene(state,ms){
  const s=blank.map(a=>a.slice()),put=(id,a)=>{s[id]=a;},text=(id,value,xx,yy,opacity=1)=>{nodes[id].e.textContent=value;put(id,[xx,yy,opacity]);};
  const seq=Math.max(0,ms-900),list=state==='c2-every',all=state==='c2-all',tour=all?allFrame(seq):null,left=list||all?284:64,right=772,top=140,bottom=392;
  nodes[predictionPath].e.classList.remove('story-clean-slope');
  nodes[readout].e.classList.remove('story-construction-readout');nodes[readout].e.classList.remove('story-long-label');
  nodes[axisLabels[0]].e.classList.remove('story-stack-legend');nodes[equation].e.classList.toggle('story-equation-long',all);
  twoSlots.forEach((slot,j)=>{nodes[slot.bar].e.classList.remove('winner');nodes[slot.bar].e.dataset.term=String(two.blocks[j].term);nodes[slot.bar].e.dataset.value=String(two.blocks[j].share);});
  const X=v=>left+(v-t[0])/(t.at(-1)-t[0])*(right-left),Y=v=>bottom-(v+slopeExtent)/(2*slopeExtent)*(bottom-top);
  const at=seq<sortAt?Math.min(remainingBlocks.length-1,Math.floor(seq/2500)):remainingBlocks.findIndex(b=>b.term===two.winner);
  const block=state==='c2-joint'?joint:list?(remainingBlocks[at]||twoWinner):twoWinner;
  let blend=['c2-standing','c2-residual'].includes(state)?0:state==='c2-joint'?ease(seq/3000):1;
  let coefficients=block.support.map((j,k)=>mix(j===0?constant.coefficient:0,block.coefficients[k],blend));
  // Candidate-to-candidate interpolation keeps every prediction vertex in place.
  let previous=null,flight=1;
  if(list){previous=seq>=sortAt?remainingBlocks.at(-1):at>0?remainingBlocks[at-1]:joint;flight=ease((seq>=sortAt?seq-sortAt:seq%2500)/700);}
  const prediction=slopeRows.map(r=>tour?mix(predict(tour.from,r),predict(tour.to,r),tour.morph):list?mix(previous?predict(previous,r):constant.coefficient,predict(block,r),flight):predict({...block,coefficients},r));
  const residualOn=state==='c2-residual'?ease(seq/1200):0;
  const bandOn=state==='c2-residual'?ease((seq-1200)/1000):0;
  caption.style.visibility='visible';caption.textContent=tr('x13_caption');
  nodes[predictionPath].e.setAttribute('clip-path','url(#story-top-clip)');
  for(const [key,v] of Object.entries({x:left,y:top,width:right-left,height:bottom-top}))clipRect.setAttribute(key,v);
  for(let j=0;j<5;j++){
   const v=mix(-slopeExtent,slopeExtent,j/4),tt=mix(t[0],t.at(-1),j/4);
   put(axisLines[j],[left,Y(v),right,Y(v),1]);text(axisLabels[j],fmt(v),left-10,Y(v)+4,j===0?0:1);nodes[axisLabels[j]].e.setAttribute('text-anchor','end');
   text(axisLabels[j+5],fmt(tt),X(tt),416);
  }
  put(axisLines[5],[left,bottom,right,bottom,1]);text(axisLabels[10],tr('x12_axis_slope'),left,120);text(axisLabels[11],tr('j157'),right-90,440);
  data.forEach((id,j)=>{const r=slopeRows[j];put(id,[r?X(r.time):left,r?Y(r.rate):bottom,r?1:0]);nodes[id].e.setAttribute('r',2.5);});
  sticks.forEach((id,j)=>{const r=slopeRows[j];put(id,[r?X(r.time):left,r?Y(prediction[j]):bottom,r?X(r.time):left,r?Y(r.rate):bottom,r?residualOn:0]);if(r)nodes[id].e.dataset.value=String(r.rate-prediction[j]);});
  const expanded=Array.from({length:n},(_,j)=>Math.min(slopeRows.length-1,Math.floor(j*slopeRows.length/n)));
  put(predictionPath,[...expanded.flatMap(i=>[X(slopeRows[i].time),Y(prediction[i])]),1]);
  put(bandTop,[...expanded.flatMap(i=>[X(slopeRows[i].time),Y(constant.coefficient+slopeRows[i].sd)]),...expanded.slice().reverse().flatMap(i=>[X(slopeRows[i].time),Y(constant.coefficient-slopeRows[i].sd)]),bandOn]);
  let gain=constant.gain;
  if(state==='c2-joint')gain=1-m.D.b.reduce((sum,b,i)=>sum+(b-block.support.reduce((v,j,k)=>v+coefficients[k]*m.D.A[i][j],0))**2,0)/norm;
  if(list)gain=mix(previous?1-previous.remaining:constant.gain,1-block.remaining,flight);
  if(state==='c2-error')gain=mix(constant.gain,1-twoWinner.remaining,ease(seq/2200));
  if(state==='c2-solution')gain=1-twoWinner.remaining;
  if(all)gain=mix(1-tour.R.base.remaining,1-tour.R.winner.remaining,tour.join);
  // Three segments retain chapter one's labels and its frozen noise fraction.
  let xx=left;
  chapterParts(m,{gain}).forEach((v,i)=>{put(stack[i].bar,[xx,20,(right-left)*v,16,1]);xx+=(right-left)*v;});
  // One legend line with all three values, as in chapter one's percent step.
  const parts=chapterParts(m,{gain});
  text(stack[0].text,tr('x13_legend',{floor:pct(parts[0]),explained:pct(parts[1]),remaining:pct(parts[2])}),left,56,list||all?0:1);
  [1,2].forEach(i=>text(stack[i].text,'',left,56,0));
  text(readout,tr('x13_share',{p:pct(gain/m.explainable)}),left,80);
  if(state==='c2-error')text(noiseLabel,tr('x13_before_after',{before:pct(constant.share),after:pct(twoWinner.share)}),left,120);
  if(state==='c2-error')s[axisLabels[10]][2]=0;
  if(state==='c2-joint'){
   text(equation,secondEquation(block.support,coefficients),left,470);
  }else if(state==='c2-solution')text(equation,secondEquation(two.record.active_idxs[0].map(j=>j-1),two.record.equations[0].coefficients),left,470);
  else if(all){const e=tour.join<.5?tour.R.base:tour.R.winner;text(equation,secondEquation(e.support,e.coefficients),12,470,tour.join>0&&tour.join<1?Math.abs(1-2*tour.join):1);svg.dataset.support=JSON.stringify(e.support);svg.dataset.round=String(tour.r);}
  else if(!list)text(equation,blend===0?soloEquation(constant):secondEquation(block.support,coefficients),left,470);
  if(list)two.blocks.forEach((b,j)=>{
   const ordering=ranking(remainingBlocks,Math.floor(seq/2500),seq%2500,[joint]);
   const yy=150+ordering.position(b)*52,progress=b.term===joint.term?1:ease((seq-remainingBlocks.indexOf(b)*2500-1800)/200),slot=twoSlots[j];
   put(slot.bar,[12,yy+10,204*clamp(b.share)*progress,12,1]);const labels=ordering.sorting?0:1;
   text(slot.text,terms[b.term],12,yy,labels);text(slot.value,pct(b.share),135,yy,progress*labels);
   nodes[slot.bar].e.dataset.term=String(b.term);nodes[slot.bar].e.dataset.value=String(b.share);nodes[slot.bar].e.classList.toggle('winner',seq>=sortAt+1000&&b.term===two.winner);
   nodes[slot.text].e.dataset.shareRow=String(j);nodes[slot.value].e.dataset.shareRow=String(j);
  });
  if(all){
   const {R,j,tl,tail,join,fade,done}=tour,k=R.candidates.length,ordering=ranking(R.candidates,j,tail?2500:2000+(tl-450)*2);
   two.blocks.forEach((b,s)=>{
    const slot=twoSlots[s],c=R.candidates.find(c=>c.term===b.term),ci=R.candidates.indexOf(c);
    if(!c||done){put(slot.bar,[12,150,0,12,0]);text(slot.text,'',12,150,0);text(slot.value,'',135,150,0);return;}
    const yy=150+ordering.position(c)*52,progress=tail||ci<j?1:ci===j?ease((tl-300)/150):0,shown=fade*(1-join),labels=ordering.sorting?0:shown;
    put(slot.bar,[12,yy+10,204*clamp(c.share)*progress,12,shown]);
    text(slot.text,terms[c.term],12,yy,labels);text(slot.value,pct(c.share),135,yy,progress>0?labels:0);
    nodes[slot.bar].e.dataset.term=String(c.term);nodes[slot.bar].e.dataset.value=String(c.share);nodes[slot.bar].e.classList.toggle('winner',tail&&c===R.winner);
    nodes[slot.text].e.dataset.shareRow=String(s);nodes[slot.value].e.dataset.shareRow=String(s);
   });
   text(errorLabel,done?tr('x16_done'):tr('x16_round',{round:tour.r+3,open:k}),12,128,done?1:fade);
   // The path so far: steps one and two from before, then one line per finished round.
   text(pathTitle,tr('x16_path'),12,350);
   [{term:0,share:constant.share},{term:two.winner,share:twoWinner.share},...rounds.map(Q=>Q.winner)].forEach((e,q)=>{
    const on=q<2||q-2<tour.r?1:q-2===tour.r?clamp(2*join-1):0;
    const col=Math.floor(q/3),yy=374+(q%3)*22;text(pathLabels[q][0],(q?'+ ':'')+terms[e.term],12+col*124,yy,on);text(pathLabels[q][1],pct(e.share),66+col*124,yy,on);
   });
  }
  svg.dataset.state=state;svg.dataset.term=String(block.term);svg.dataset.error=String(1-gain);svg.dataset.coefficients=JSON.stringify(coefficients);svg.dataset.complete=String(ms>=durations[state]);
  return s;
 }
 // All chapter-three nodes are mounted once; removal/refit only changes geometry.
 function thirdScene(state,ms){
  const costPct=value=>secondNumber(100*value)+' %';
  const s=blank.map(a=>a.slice()),put=(id,a)=>{s[id]=a;},text=(id,value,x,y,opacity=1)=>{nodes[id].e.textContent=value;put(id,[x,y,opacity]);};
  svg.dataset.magnified='false';
  nodes[equation].e.classList.remove('story-equation-long');
  twoSlots.forEach(slot=>nodes[slot.bar].e.classList.remove('winner'));
  c3Bars.forEach((slot,j)=>{nodes[slot.bar].e.dataset.term=String(j);nodes[slot.bar].e.dataset.value='';nodes[slot.bar].e.classList.remove('goes');});nodes[c3Line].e.dataset.value='';nodes[c3GainBar].e.dataset.value='';
  const compare=state==='c3-compare',next=state==='c3-next',audit=['c3-probe','c3-threshold','c3-linear','c3-quadratic'].includes(state),repair=['c3-linear','c3-quadratic'].includes(state);
  const R=three.rounds[state==='c3-quadratic'?3:state==='c3-linear'?2:1];
  const start=repair?1800:0,firstEnd=start+R.probes[0].costs.length*1800,removeEnd=firstEnd+3200,compactEnd=firstEnd+1200;
  const pass=repair&&ms>=removeEnd?1:0,probe=R.probes[pass]||R.probes[0],local=ms-(pass?removeEnd:start);
  const index=Math.min(probe.costs.length-1,Math.max(0,Math.floor(local/1800))),trial=probe.costs[index];
  const testing=audit&&ms>=start&&local<probe.costs.length*1800;
  const phase=testing?ease((local%1800)/1200):0;
  let from=R.after,to=R.after,blend=1;
  if(repair&&ms<start){from=R.before;to=R.added;blend=ease(ms/start);}
  else if(testing){from=probe.model;to=trial.fit;blend=phase<.5?phase*2:(1-phase)*2;}
  else if(repair&&ms<removeEnd){from=R.added;to=R.after;blend=ease((ms-firstEnd)/1200);}
  const current=repair&&ms<start?R.added:repair&&ms>=compactEnd?R.after:probe.model;
  const support=compare||next?three.rounds.at(-1).after.support:current.support;
  svg.dataset.support=JSON.stringify(support);svg.dataset.probeSupport=JSON.stringify(probe.model.support);svg.dataset.probe=String(pass);svg.dataset.testedTerm=testing?String(trial.term):'';
  caption.style.visibility='visible';caption.textContent=tr('x17_caption');
  if(compare||next){
   const fade=ease(ms/1200);
   const forward=[three.rounds[0].after,three.rounds[1].after,rounds[0].winner,rounds[1].winner];
   text(c3Headers[0],tr(compare?'x17_forward':'x17_candidates'),48,30);
   if(compare)text(c3Headers[1],tr('x17_foba'),432,30);
   c3Paths.forEach((slot,j)=>{
    const col=Math.floor(j/4),row=j%4,entry=compare?(col?three.rounds[row].after:forward[row]):col?null:three.rounds[row].after;
    if(!entry)return;
    const xx=48+col*384,yy=54+row*64;
    put(slot.box,[xx,yy,316,44,fade]);text(slot.text,entry.support.map(j=>terms[j]).join(',  '),xx+16,yy+28,fade);
   });
   if(compare){
    const reveal=ease((ms-1800)/1500);
    text(c3Truth,tr('x17_truth')+'  '+secondEquation(three.truth,truthCoefficients),48,354,reveal);
    text(c3Weak,tr('x17_weak')+'  '+secondEquation(three.rounds.at(-1).after.support,three.rounds.at(-1).after.coefficients),48,390,reveal);
    three.truth.forEach((term,j)=>text(c3Coefficients[j],tr('x17_coefficient',{term:terms[term],fit:secondNumber(three.rounds.at(-1).after.coefficients[j]),truth:secondNumber(truthCoefficients[j])}),48,430+j*28,reveal));
   }else{
    const gains=three.rounds.map(r=>({term:r.addition,gain:r.gain})).concat([three.next]);
    const maximum=Math.max(...gains.map(g=>g.gain)),top=152,bottom=340,left=448,right=776;
    const Y=v=>bottom-(bottom-top)*v/maximum;
    text(c3Axis,tr('x17_round_gain'),432,80);text(c3RoundY,tr('x17_explained_scale'),432,110);
    text(c3Max,costPct(maximum),400,140);text(c3Zero,pct(0),400,346);
    put(c3RoundAxes[0],[432,top,432,bottom,1]);put(c3RoundAxes[1],[432,bottom,right,bottom,1]);
    text(c3RoundX,tr('x17_round_axis'),690,470);
    gains.forEach((g,j)=>{
     const slot=c3RoundBars[j],xx=left+j*64,h=(bottom-Y(g.gain))*fade;
     nodes[slot.bar].e.dataset.term=String(g.term);nodes[slot.bar].e.dataset.value=String(g.gain);
     put(slot.bar,[xx,bottom-h,32,h,1]);text(slot.value,costPct(g.gain),xx-8,370,fade);
     text(slot.name,terms[g.term],xx,394);text(slot.round,String(j+1),xx,418);
    });
    nodes[c3NotTaken].e.setAttribute('text-anchor','end');text(c3NotTaken,tr('x17_not_taken'),772,444);
    text(c3Status,tr('x17_question'),48,458,ease((ms-2200)/1200));
   }
   return s;
  }
  // Model chips always keep catalogue order; an omitted block fades during its probe.
  support.forEach((term,j)=>{let xx=48+j*112;const grey=testing&&trial.term===term;
   if(repair&&ms<start&&!R.before.support.includes(term))xx=48+j*112;
   else if(repair&&ms<start)xx=mix(48+R.before.support.indexOf(term)*112,xx,ease(ms/(start/2)));
   else if(repair&&ms>=firstEnd&&ms<removeEnd&&!R.removed.includes(term))xx=mix(xx,48+R.after.support.indexOf(term)*112,ease((ms-firstEnd-600)/600));
   const leaving=repair&&ms>=firstEnd&&ms<removeEnd&&R.removed.includes(term);
   const opacity=leaving?1-ease((ms-firstEnd)/600):repair&&ms<start&&term===R.addition?ease((ms-start/2)/(start/2)):grey?.25:1,chip=c3Chips[term];
   const yy=leaving?14-12*ease((ms-firstEnd)/600):14;
   put(chip.box,[xx,yy,96,36,opacity]);text(chip.text,terms[term],xx+14,yy+24,opacity);
  });
  const visibleShare=(1-mix(from.remaining,to.remaining,blend))/m.explainable;
  text(c3Share,tr('x17_share',{share:pct(visibleShare)}),48,80);
  if(repair)text(c3Gain,tr('x17_gain',{term:terms[R.addition],gain:costPct(R.gain)}),48,110);
  if(audit){
   // One fixed axis for both passes of this round, including the newcomer's gain.
   const maximum=Math.max(R.gain,R.threshold,...R.probes.flatMap(p=>p.costs.map(c=>c.cost)))*1.18;
   const top=196,bottom=368,Y=v=>bottom-(bottom-top)*v/maximum;
   text(c3Axis,tr('x17_cost_axis'),48,172);text(c3CostX,tr('x17_block_axis'),350,462);text(c3Max,pct(maximum),4,190);text(c3Zero,pct(0),4,380);
   put(c3Line,[48,Y(R.threshold),444,Y(R.threshold),state==='c3-probe'?0:1]);
   text(c3Threshold,tr('x17_threshold',{value:costPct(R.threshold)}),48,142,state==='c3-probe'?0:1);
   nodes[c3Line].e.dataset.value=String(R.threshold);
   if(repair){const h=(bottom-Y(R.gain))*ease(ms/start);put(c3GainBar,[394,bottom-h,44,h,1]);text(c3GainName,'+'+terms[R.addition],394,395);text(c3GainValue,costPct(R.gain),394,418);nodes[c3GainBar].e.dataset.value=String(R.gain);}

   probe.costs.forEach((c,j)=>{
    const slot=c3Bars[c.term],xx=60+j*108,done=local>=j*1800,progress=clamp((local-j*1800)/1200),h=(bottom-Y(c.cost))*ease(progress);
    const goes=state!=='c3-probe'&&c.cost<R.threshold;
    nodes[slot.bar].e.classList.toggle('goes',goes);nodes[slot.bar].e.dataset.term=String(c.term);nodes[slot.bar].e.dataset.value=String(c.cost);
    put(slot.bar,[xx,bottom-h,58,h,done?1:0]);
    text(slot.name,terms[c.term],xx,395);
    // Numeric annotations stay in separate rows, clear of bars and the threshold.
    text(slot.value,costPct(c.cost),xx,418,done?1:0);
    text(slot.status,tr(goes?'x17_goes':'x17_stays'),xx,440,done&&state!=='c3-probe'&&(!goes||!repair||ms>=firstEnd)?1:0);
   });
   text(c3Status,tr(testing?'x17_omit':repair&&pass?'x17_repeat':repair&&ms>=firstEnd?'x17_removed':'x17_all_stay',{term:testing?terms[trial.term]:''}),48,472);
   // Keep the common full-scale axis fixed across both probes; magnify the
   // decisive low costs without a discontinuous rescale or hiding large bars.
   const magnified=state!=='c3-probe'&&ms>=start&&R.threshold<.1*maximum;
   svg.dataset.magnified=String(magnified);svg.dataset.costMaximum=String(maximum);
   nodes[c3Zoom.threshold].e.dataset.value=String(R.threshold);
   if(magnified){
    const limit=2.5*R.threshold,top=64,bottom=124,Y=v=>bottom-(bottom-top)*Math.min(v,limit)/limit;
    const closest=probe.costs.reduce((a,b)=>Math.abs(a.cost-R.threshold)<Math.abs(b.cost-R.threshold)?a:b);
    text(c3Zoom.title,tr('x17_magnified'),480,20);text(c3Zoom.y,tr('x17_cost_axis'),590,20);
    text(c3Zoom.value,terms[closest.term]+': '+costPct(closest.cost),480,42);
    text(c3Zoom.max,costPct(limit),480,62);text(c3Zoom.zero,pct(0),480,128);text(c3Zoom.x,tr('x17_block_axis'),480,150);
    put(c3Zoom.axis,[538,top,538,bottom,1]);put(c3Zoom.base,[538,bottom,772,bottom,1]);
    put(c3Zoom.threshold,[538,Y(R.threshold),772,Y(R.threshold),1]);
    probe.costs.forEach((c,j)=>{
     const slot=c3Zoom.bars[c.term],xx=550+j*72,done=local>=j*1800,progress=ease(clamp((local-j*1800)/1200));
     const h=bottom-Y(c.cost*progress);
     put(slot.bar,[xx,bottom-h,40,h,done?1:0]);
     nodes[slot.bar].e.dataset.value=String(c.cost);nodes[slot.bar].e.dataset.term=String(c.term);
     nodes[slot.bar].e.dataset.limit=String(limit);
     put(slot.cut,[xx-2,top+5,xx+42,top-5,done&&c.cost*progress>limit?1:0]);
     text(slot.name,terms[c.term],xx,150);
    });
   }

  }
  // Reuse chapter two's weak-rate rows and fixed prediction vertices for every refit.
  const left=480,right=772,top=210,bottom=368,X=v=>left+(v-t[0])/(t.at(-1)-t[0])*(right-left),Y=v=>bottom-(v+slopeExtent)/(2*slopeExtent)*(bottom-top);
  text(c3Headers[0],tr('x17_live_fit'),480,172);
  text(axisLabels[10],tr('x12_axis_slope'),480,194);text(axisLabels[11],tr('j157'),680,395);
  for(const [key,v] of Object.entries({x:left,y:top,width:right-left,height:bottom-top}))clipRect.setAttribute(key,v);
  nodes[predictionPath].e.setAttribute('clip-path','url(#story-top-clip)');nodes[predictionPath].e.classList.remove('story-clean-slope');
  put(axisLines[0],[left,bottom,right,bottom,1]);
  data.forEach((id,j)=>{const r=slopeRows[j];put(id,[r?X(r.time):left,r?Y(r.rate):bottom,r?1:0]);});
  const expanded=Array.from({length:n},(_,j)=>Math.min(slopeRows.length-1,Math.floor(j*slopeRows.length/n)));
  put(predictionPath,[...expanded.flatMap(i=>{const r=slopeRows[i];return [X(r.time),Y(mix(predict(from,r),predict(to,r),blend))];}),1]);
  text(c3Weak,secondEquation(current.support,current.coefficients),480,418);
  return s;
 }
 let current=null,frame=0,last=blank.map(a=>a.slice()),elapsed=0,reverseZoom=false;
 function scene(state,ms){
  if(state?.startsWith('c3-')){const s=thirdScene(state,ms);svg.dataset.state=state;svg.dataset.complete=String(ms>=durations[state]);result.hidden=true;return s;}
  const requested=state,elapsedMs=ms;
  $('c1-story-text-8').style.opacity='1';
  $('c2-text-3').style.opacity='1';
  if(state==='c2-joint'){
   state=ms>=jointPause?'c2-every':'c2-joint';ms=state==='c2-every'?ms-jointPause:Math.min(ms,4900);
  }
  const geometry=baseScene(state,ms);
  // The phase change interpolates the same mounted vertices in either direction.
  const boundary=requested==='c2-joint'?jointPause:0;
  if(boundary&&elapsedMs>=boundary&&elapsedMs<boundary+900){
   const previous=baseScene('c2-joint',4900),blend=ease((elapsedMs-boundary)/900);
   baseScene(state,ms); // Restore label/style side effects from the active phase.
   // Axis tick labels would fly across the candidate bars; they fade in at their new place instead.
   const fadeOnly=requested==='c2-joint'?new Set(axisLabels):new Set();
   geometry.forEach((a,i)=>{
    if(fadeOnly.has(i)){a[a.length-1]*=Math.max(0,(blend-0.8)/0.2);return;}
    const before=previous[i],wasVisible=before.at(-1)>0,isVisible=a.at(-1)>0;
    a.forEach((v,j)=>{if(j===a.length-1||wasVisible&&isVisible)a[j]=mix(before[j],v,blend);else if(wasVisible)a[j]=before[j];});
   });
  }
  svg.dataset.state=requested;svg.dataset.phase=boundary?(elapsedMs<boundary?'explanation':'sequence'):svg.dataset.phase;
  svg.dataset.complete=String(elapsedMs>=durations[requested]);
  result.hidden=requested!=='noise-estimate'||elapsedMs<durations[requested];
  result.style.opacity=result.hidden?'0':'1';
  return geometry;
 }
 function baseScene(state,ms){
  if(state.startsWith('c2-'))return secondScene(state,ms);
  nodes[equation].e.classList.remove('story-equation-long');
  twoSlots.forEach(slot=>nodes[slot.bar].e.classList.remove('winner'));
  caption.textContent=tr('x10_caption');
  nodes[axisLabels[0]].e.classList.remove('story-stack-legend');nodes[axisLabels[0]].e.setAttribute('text-anchor','end');
  nodes[readout].e.classList.remove('story-construction-readout');nodes[readout].e.classList.remove('story-long-label');
  triangle.forEach(id=>nodes[id].e.classList.toggle('story-long-triangle',state==='windows'));
  triangleLabels.forEach(id=>nodes[id].e.classList.toggle('story-long-label',state==='windows'));
  const s=blank.map(a=>a.slice()),step=legacyStates.indexOf(state),seq=Math.max(0,ms-(state==='noise-estimate'?0:900)),final=ms>=durations[state];
  caption.style.visibility=step>=4&&step<=7?'visible':'hidden';
  result.hidden=state!=='noise-estimate'||!final;result.style.opacity=result.hidden?'0':'1';
  const put=(id,a)=>{s[id]=a;},text=(id,value,xx,yy,opacity=1)=>{nodes[id].e.textContent=value;put(id,[xx,yy,opacity]);};
  const split=step===3||step===4,changes=step>=5&&step<=8||state==='solution';
  let domain=[t[0],t.at(-1)],top=42,bottom=392,range=uRange;
  if(split)bottom=state==='secants'?mix(392,210,ease(ms/450)):210;
  if(state==='noise-estimate'){
   bottom=302;
   // A 9-point window is ~9 px wide on the full series: zoom onto it, follow the sweep, then zoom out.
   const z=seq<noiseIn?ease(seq/noiseIn):seq<noiseSlowEnd?1:1-ease((seq-noiseSlowEnd)/2000),half=8;
   const centre=mix((n-1)/2,Math.max(half,Math.min(n-1-half,noiseCount(seq))),z),width=mix((n-1)/2,half,z);
   const a=Math.max(0,centre-width),b=Math.min(n-1,a+2*width),tAt=k=>t[0]+(t.at(-1)-t[0])*k/(n-1);
   const visible=x.slice(Math.floor(a),Math.ceil(b)+1),lo=Math.min(...visible),hi=Math.max(...visible),margin=(hi-lo)*.25||1;
   domain=[tAt(a),tAt(b)];range=[mix(uRange[0],lo-margin,z),mix(uRange[1],hi+margin,z)];
   svg.dataset.noiseZoom=String(z);
  }
  // S4: draw the target, hold, zoom, then eight complete pair constructions.
  let zoom=0,windowLength=1;
  const start=t.findIndex(v=>v>=2),constructionLengths=longerLengths;
  const pairBegin=2200,pairEnd=11800,pairOut=12600;
  const windowEnd=longerLengths.length*2400;
  if(state==='secants'||state==='windows'){
   zoom=state==='secants'?(seq<600?0:seq<2200?ease((seq-600)/1600):seq<pairEnd?1:1-ease((seq-pairEnd)/800)):(seq<windowEnd?1:1-ease((seq-windowEnd)/800));
   const pan=Math.min(7,Math.max(0,Math.floor((seq-pairBegin)/1200)))+ (seq<pairEnd-1200?ease(((seq-pairBegin)%1200-1000)/200):0);
   const begin=state==='secants'?start+pan-2:start,end=state==='secants'?begin+6:start+18;
   // The pair phase zooms in height as well, so a neighbour triangle has a visible rise.
   const visible=state==='secants'?x.slice(Math.max(0,Math.floor(begin)),Math.min(n,Math.ceil(end)+1)):x.slice(start-2,start+19);
   const vlo=Math.min(...visible),vhi=Math.max(...visible),margin=(vhi-vlo)*(state==='secants'?.25:.1)||1,lo=vlo-margin,hi=vhi+margin;
   const at=i=>t[Math.floor(i)]+(i%1)*(t[Math.floor(i)+1]-t[Math.floor(i)]);
   domain=[mix(t[0],at(begin),zoom),mix(t.at(-1),at(end),zoom)];
   range=[mix(uRange[0],lo,zoom),mix(uRange[1],hi,zoom)];
   windowLength=state==='windows'?constructionLengths[Math.min(constructionLengths.length-1,Math.floor(seq/2400))]:1;
  }
  if(changes){range=[-changeBound,changeBound];top=state==='fit'?240:140;}
  nodes[predictionPath].e.setAttribute('clip-path',changes?'url(#story-top-clip)':'url(#story-x-clip)');nodes[optimumPath].e.setAttribute('clip-path','url(#story-top-clip)');
  const list=state==='every'||state==='percent',left=state==='every'?284:64,right=state==='noise-estimate'?570:split?mix(772,570,state==='secants'?ease(ms/450):1):772;
  const lowerReveal=state==='secants'?ease((ms-450)/450):1;
  const X=v=>left+(v-domain[0])/(domain[1]-domain[0])*(right-left),Y=v=>bottom-(v-range[0])/(range[1]-range[0])*(bottom-top);
  const inside=v=>v>=domain[0]&&v<=domain[1];
  const lowerTop=270,lowerBottom=392;
  const lowerBound=rateBound;
  svg.dataset.slopeBound=String(lowerBound);svg.dataset.phase=state==='secants'?(seq<400?'highlight':seq<600?'hold':seq<2200?'zoom-in':seq<11800?'zoomed':seq<12600?'zoom-out':'sweep'):'';
  for(const [key,v] of Object.entries({x:left,y:top,width:right-left,height:bottom-top}))clipRect.setAttribute(key,v);
  for(const [key,v] of Object.entries({x:left,y:0,width:right-left,height:2000}))xClipRect.setAttribute(key,v);
  const R=v=>lowerBottom-(v+lowerBound)/(2*lowerBound)*(lowerBottom-lowerTop);
  for(let j=0;j<5;j++){
   const v=mix(range[0],range[1],j/4),tt=mix(domain[0],domain[1],j/4);
   put(axisLines[j],[left,Y(v),right,Y(v),1]);text(axisLabels[j],fmt(v),left-10,Y(v)+4,j===0?0:1);nodes[axisLabels[j]].e.setAttribute('text-anchor','end');
   text(axisLabels[j+5],fmt(tt),X(tt),split?bottom+25:state==='noise-estimate'?326:416);
  }
  put(axisLines[5],[left,bottom,right,bottom,1]);text(axisLabels[10],changes?tr('x9_change'):'u',left,state==='every'?120:24);text(axisLabels[11],tr('j157'),right-90,split?bottom+42:state==='noise-estimate'?350:440);
  if(split){put(axisLines[6],[left,R(0),right,R(0),1]);text(axisLabels[12],tr('x12_axis_slope'),left,lowerTop-15);text(axisLabels[13],tr('j157'),right-90,440);
   [-lowerBound,0,lowerBound].forEach((v,j)=>{text(axisLabels[14+j],fmt(v),left-10,R(v)+4);nodes[axisLabels[14+j]].e.setAttribute('text-anchor','end');});
   put(axisLines[7],[left,lowerTop,left,lowerBottom,1]);}
  if(split&&ms<900){for(const id of [axisLines[6],axisLines[7],...axisLabels.slice(12)])s[id][s[id].length-1]=0;}
  if(state==='percent')for(const id of [...axisLines,...axisLabels])s[id][s[id].length-1]=0;
  const plotU=!changes&&state!=='percent';
  data.forEach((id,i)=>put(id,[X(t[i]),Y(x[i]),plotU&&inside(t[i])?1:0]));
  const curveOpacity=state==='noise-visible'||state==='slope'||split?1:0;
  const reveal=state==='noise-visible'?clamp(seq/900):1;
  put(truthPath,[...t.flatMap((v,i)=>[X(v),Y(clean[i])]),curveOpacity]);
  nodes[truthPath].e.style.strokeDasharray=state==='noise-visible'?'1 1':'';
  nodes[truthPath].e.setAttribute('pathLength','1');nodes[truthPath].e.style.strokeDashoffset=String(1-reveal);
  text(truthLabel,split?tr('x14_true_slope'):tr('x12_truth'),split?590:left+10,split?(state==='windows'?190:260):top+20,curveOpacity);nodes[truthLabel].e.classList.toggle('story-reference-label',split);
  // All scientific values are attached unscaled for the numerical DOM assertions.
  if(state==='noise-visible')sticks.forEach((id,i)=>{put(id,[X(t[i]),Y(x[i]),X(t[i]),Y(clean[i]),inside(t[i])?clamp((seq-900)/500):0]);nodes[id].e.dataset.value=String(Math.abs(x[i]-clean[i]));});
  if(state==='slope'){
   const i=Math.min(n-2,Math.floor(clamp(seq/2900)*(n-2))),slope=trueRates[i],dt=(t.at(-1)-t[0])*.25,ta=Math.max(t[0],Math.min(t.at(-1)-dt,t[i]-dt/2)),tb=ta+dt;
   put(marker,[X(t[i]),Y(clean[i]),1]);put(tangent,[X(ta),Y(clean[i]+(ta-t[i])*slope),X(tb),Y(clean[i]+(tb-t[i])*slope),1]);text(readout,tr('x12_slope',{value:fmt(slope)}),Math.max(left+15,Math.min(right-230,X(t[i])+15)),Math.max(top+45,Y(clean[i])-35));
   const xx=X(t[i]),yy=Y(clean[i]),dx=(right-left)*.08*(X(t[i])>right-100?-1:1),dy=Y(clean[i]+slope*(domain[1]-domain[0])*.08*(dx<0?-1:1));
   put(triangle[0],[xx,yy,xx+dx,yy,1]);put(triangle[1],[xx+dx,yy,xx+dx,dy,1]);
   text(triangleLabels[0],tr('x12_dt'),xx+dx/2,yy+20);text(triangleLabels[1],tr('x12_du'),xx+dx+8,yy-8);
  }
  if(split){
   const neighbour=state==='secants',intro=neighbour&&seq<pairOut;
   const sweep=clamp((seq-pairOut)/2600),pair=Math.min(7,Math.max(0,Math.floor((seq-pairBegin)/1200)));
   const active=neighbour?seq>=pairBegin&&seq<pairEnd:seq<windowEnd;
   const localTime=neighbour?seq-pairBegin-pair*1200:seq%2400;
   const a=neighbour?start+pair:start,b=a+windowLength;
   const draw=ease(localTime/350),labels=clamp((localTime-350)/150),written=clamp((localTime-500)/150),drop=ease((localTime-750)/400);
   if(neighbour&&seq<pairBegin){
    const xx=X(t[start]);
    const lo=Math.min(...x.slice(start,start+19))*.98,hi=Math.max(...x.slice(start,start+19))*1.02;
    const w=X(t[start+18])-xx,h=Y(lo)-Y(hi),bw=Math.max(48,w),bh=Math.max(48,h);put(zoomBox,[xx+w/2-bw/2,Y(hi)+h/2-bh/2,bw,bh,1]);
    nodes[zoomBox].e.setAttribute('pathLength','1');nodes[zoomBox].e.style.strokeDasharray='1 1';nodes[zoomBox].e.style.strokeDashoffset=String(1-clamp(seq/400));
   }
   put(predictionPath,[...t.flatMap((v,i)=>[X(v),R(trueRates[i])]),lowerReveal]);
   // The neighbour cloud belongs only to the neighbour construction.
   slopeDots.forEach((id,i)=>{
    const j=intro?start+i:i,row=rates[j],v=row?.rate??0,outside=Math.abs(v)>lowerBound;
    const completed=intro?seq>=pairBegin+i*1200+750&&i<8:!neighbour&&seq<windowEnd?i>=start&&i<start+8:i<Math.floor((neighbour?sweep:1)*rates.length);
    const flight=intro&&i===pair?drop:1,xx=X(row?.time??t[0]),yy=mix(Y(x[j]??x[0]),R(Math.max(-lowerBound,Math.min(lowerBound,v))),flight);
    const opacity=completed&&inside(row?.time)?(neighbour?flight:0):0,dir=v>0?1:-1;
    put(id,[xx,yy,outside?0:opacity]);nodes[id].e.dataset.value=String(v);
    put(clipped[i],[xx,yy,xx-3,yy+dir*6,xx+3,yy+dir*6,outside?opacity:0]);
   });
   historyTriangles.forEach((ids,j)=>{
    const aa=start+j,bb=aa+1,visible=0;
    put(ids[0],[X(t[aa]),Y(x[aa]),X(t[bb]),Y(x[aa]),visible]);
    put(ids[1],[X(t[bb]),Y(x[aa]),X(t[bb]),Y(x[bb]),visible]);
    put(ids[2],[X(t[aa]),Y(x[aa]),X(t[bb]),Y(x[bb]),visible]);
   });
   if(!neighbour)lengthClouds.forEach((cloud,j)=>{
    const progress=clamp((seq-j*2400)/1400);
    cloud.dots.forEach((id,i)=>{const row=cloud.rows[i],v=row?.rate??0;
     put(id,[X(row?.time??t[0]),R(Math.max(-lowerBound,Math.min(lowerBound,v))),row&&inside(row.time)&&i<Math.floor(progress*cloud.rows.length)?(j===Math.min(lengthClouds.length-1,Math.floor(seq/2400))?1:0):0]);
     nodes[id].e.dataset.value=String(v);nodes[id].e.dataset.length=String(cloud.length);
    });
    text(cloud.label,tr('x14_length',{k:cloud.length}),590,298+j*34);nodes[cloud.label].e.style.fill=lengthColours[j];
    const barProgress=clamp((seq-j*2400-1400)/600);
    put(cloud.bar,[590,306+j*34,135*lengthRms[j]/rmsMax*barProgress,8,1]);nodes[cloud.bar].e.style.fill=lengthColours[j];nodes[cloud.bar].e.dataset.value=String(lengthRms[j]*barProgress);
    text(cloud.value,fmt(lengthRms[j]*barProgress),745,314+j*34,barProgress>0?1:0);
    text(lengthTitle[0],tr('x15_rms_title'),600,226);text(lengthTitle[1],tr('x15_rms_subtitle'),600,244);text(lengthTitle[2],tr('x15_true_used'),600,265);
   });
   const opacity=active?1:0,xx=X(t[a]),yy=Y(x[a]),xb=X(t[b]),yb=Y(x[b]);
   put(triangle[0],[xx,yy,mix(xx,xb,draw),yy,opacity]);put(triangle[1],[xb,yy,xb,mix(yy,yb,draw),opacity]);put(triangle[2],[xx,yy,mix(xx,xb,draw),mix(yy,yb,draw),opacity]);
   triangle.forEach(id=>nodes[id].e.classList.toggle('story-long-triangle',!neighbour));
   text(triangleLabels[0],tr('x12_dt')+' = '+fmt(t[b]-t[a]),590,90,opacity*labels);
   text(triangleLabels[1],tr('x12_du')+' = '+fmt(x[b]-x[a]),590,116,opacity*labels);
   if(neighbour){text(legLabels[0],tr('x12_dt'),(xx+xb)/2-8,yy+22,opacity*labels);text(legLabels[1],tr('x12_du'),xb+12,(yy+yb)/2,opacity*labels);}
   text(triangleLabels[2],tr('x12_length',{n:b-a}),590,64,opacity);
   text(readout,tr('x12c_slope',{value:fmt((x[b]-x[a])/(t[b]-t[a]))}),590,150,opacity*written);
   nodes[readout].e.classList.add('story-construction-readout');nodes[readout].e.classList.toggle('story-long-label',!neighbour);
   // Length colours are identified directly by the RMS bars.
   text(clippedLabel,tr('x12_clipped',{n:rates.filter(r=>Math.abs(r.rate)>lowerBound).length}),590,300,neighbour&&!intro?1:0);
   svg.dataset.pairStart=String(a);
   data.forEach(id=>nodes[id].e.setAttribute('r',zoom>.9?(neighbour?8:5):2.5));
  }
  let block=constant,c=0,error=1;
  if(changes){
   if(state==='fit')c=2*constant.coefficient*clamp(seq/4000);
   if(state==='every'){
    const index=Math.min(m.blocks.length-1,Math.floor(seq/2500));block=m.blocks.slice().sort((a,b)=>a.term-b.term)[index];
    const phase=seq-index*2500;c=phase>=1800?block.coefficient:block.coefficient*clamp((phase-400)/1400);
    if(seq>=15000){block=winner;c=winner.coefficient;}
   }
   if(state==='solution'||state==='noise-why'){block=winner;c=winner.coefficient;}
   let previous=null,transition=1;
   if(state==='every'){
    const ordered=m.blocks.slice().sort((a,b)=>a.term-b.term),index=Math.min(ordered.length-1,Math.floor(seq/2500));
    if(seq<15000&&index>0){previous=ordered[index-1];transition=ease((seq-index*2500)/160);}
    if(seq>=15000){previous=ordered.at(-1);transition=ease((seq-15000)/1000);}
   }
   const predict=i=>c*m.D.A[i][block.term]*transition+(previous?previous.coefficient*m.D.A[i][previous.term]*(1-transition):0);
   error=previous?m.D.b.reduce((sum,b,i)=>sum+(b-predict(i))**2,0)/norm:chapterError(m,block.term,c);
   const predictions=m.rows.map(({i})=>predict(i));
   // Keep n vertices while drawing the sparse displayed design windows.
   put(predictionPath,[...t.map((_,j)=>Math.min(m.rows.length-1,Math.floor(j*m.rows.length/n))).flatMap(i=>[X(m.x[i]),Y(predictions[i])]),state==='error-empty'?0:state==='every'&&seq<15000?clamp((seq%2500)/400):1]);
   data.forEach((id,j)=>{const row=m.rows[j];put(id,[X(m.x[j]??t[0]),Y(row?m.D.b[row.i]:0),row?1:0]);});
   sticks.forEach((id,j)=>{const row=m.rows[j],v=row?m.D.b[row.i]:0,p=predictions[j]??0,progress=state==='error-empty'?clamp(seq/2000*m.rows.length-j):1;
    put(id,[X(m.x[j]??t[0]),Y(v),X(m.x[j]??t[0]),Y(mix(v,p,progress)),row?progress:0]);nodes[id].e.dataset.value=String(v-p);});
   put(axisLines[6],[left,Y(0),right,Y(0),1]);
   const progress=state==='error-empty'?clamp(seq/2000):1;
   if(state==='noise-why')text(noiseLabel,'? '+tr('x12c_question'),left+20,64);
   put(errorBar,[left,447,(right-left)*clamp(error)*progress,14,1]);text(errorLabel,tr('x10_error',{p:pct(error*progress)}),left,477);
   text(equation,state==='error-empty'?tr('x10_none'):state==='every'?'du/dt = '+soloNumber(c)+' · '+terms[block.term]:soloEquation({...block,coefficient:c}),left,24,['every','solution'].includes(state)?1:0);
   if(state==='fit'){
    const lo=fitMin,hi=fitMax,values=curveValues,maxError=curveMaximum;
    const CX=v=>470+280*(v-lo)/(hi-lo),CY=v=>180-140*v/maxError;
    put(curveAxes[0],[470,180,750,180,1]);put(curveAxes[1],[470,40,470,180,1]);
    text(curveTicks[0],tr('x12d_error_axis'),470,24);text(curveTicks[1],'c',766,184);
    ['0','c*','2\u00b7c*'].forEach((v,j)=>text(curveTicks[j+2],v,470+j*140,201));
    [0,maxError].forEach((v,j)=>{text(curveTicks[j+5],String(Math.round(v*100)),460,CY(v)+4);nodes[curveTicks[j+5]].e.setAttribute('text-anchor','end');});
    put(curvePath,[...values.flatMap((v,i)=>[CX(v),CY(curveErrors[i])]),1]);nodes[curvePath].e.setAttribute('pathLength','1');nodes[curvePath].e.style.strokeDasharray='1 1';nodes[curvePath].e.style.strokeDashoffset=String(1-clamp(seq/4000));put(curveMarker,[CX(c),CY(error),1]);text(curveLabel,'c = '+soloNumber(c),left,64);
    const passed=seq>=2000;
    nodes[optimumMarker].e.dataset.value=String(constant.coefficient);
    put(optimumMarker,[CX(constant.coefficient),CY(chapterError(m,0,constant.coefficient)),passed?1:0]);
    text(optimumLabel,tr('x12c_best',{c:soloNumber(constant.coefficient)}),left,104,passed?1:0);
   }
   const blockTime=seq%2500,passed=state==='fit'?seq>=2000:state==='every'&&(seq>=15000||blockTime>=1100);
   put(optimumPath,[...t.map((_,j)=>Math.min(m.rows.length-1,Math.floor(j*m.rows.length/n))).flatMap(i=>[X(m.x[i]),Y(block.coefficient*m.D.A[m.rows[i].i][block.term])]),passed?1:0]);
   if(state==='every'){
    nodes[optimumMarker].e.dataset.value=String(block.coefficient);
    const {values,errs,maximum}=blockCurves.get(block.term);
    const CX=v=>right-180+180*v/(2*block.coefficient),CY=v=>100-45*v/maximum;
    put(curvePath,[...values.flatMap((v,i)=>[CX(v),CY(errs[i])]),0]);
    nodes[curvePath].e.setAttribute('pathLength','1');nodes[curvePath].e.style.strokeDasharray='1 1';nodes[curvePath].e.style.strokeDashoffset=String(1-clamp((blockTime-400)/1400));
    put(curveMarker,[CX(c),CY(error),0]);put(optimumMarker,[CX(block.coefficient),CY(chapterError(m,block.term,block.coefficient)),0]);
    text(optimumLabel,tr('x12c_best',{c:soloNumber(block.coefficient)}),right-185,128,passed?1:0);
   }

  }
  if(list){
   const ordered=m.blocks.slice().sort((a,b)=>a.term-b.term),ranked=ordered.slice().sort((a,b)=>b.share-a.share),ordering=ranking(ordered,Math.floor(seq/2500),seq%2500);
   slots.forEach((slot,j)=>{const b=ordered[j],rank=ranked.indexOf(b),yy=(state==='percent'?155:62)+(state==='percent'?j:ordering.position(b))*48;
    const visible=state==='percent'?1:clamp((seq-j*2500-1800)/200),value=b.share;
    // New values travel from the prediction plot into their catalogue slot.
    const flight=state==='percent'?1:ease((seq-j*2500-1800)/200),xx=mix(left+30,12,clamp(flight/.6)),flightY=mix(110,yy,clamp((flight-.6)/.4));
    put(slot.bar,[xx,flightY+8,204*clamp(value),12,visible]);const labels=state==='every'&&ordering.sorting?0:visible;
    text(slot.text,terms[b.term],xx,flightY,labels);text(slot.value,pct(value),xx+140,flightY,labels);
    nodes[slot.text].e.dataset.shareRow=String(j);nodes[slot.value].e.dataset.shareRow=String(j);
    nodes[slot.bar].e.dataset.term=String(b.term);nodes[slot.bar].e.dataset.value=String(value);nodes[slot.bar].e.dataset.rank=String(rank);nodes[slot.bar].e.classList.toggle('winner',b.term===m.winner&&(state==='percent'||seq>=16000));
   });
  }
  if(state==='percent'){
   const parts=chapterParts(m,winner);let xx=left;
   parts.forEach((v,i)=>{put(stack[i].bar,[xx,42,(right-left)*v,32,1]);xx+=(right-left)*v;});
   text(axisLabels[0],parts.map((v,i)=>tr(['x10_floor','x10_reduced','x10_remaining'][i])+': '+pct(v)).join(' \u00b7 '),left,102);
   nodes[axisLabels[0]].e.setAttribute('text-anchor','start');nodes[axisLabels[0]].e.classList.add('story-stack-legend');
   if(!m.normalized)text(errorLabel,tr('x10_fallback'),left,350);
  }
  if(state==='noise-estimate'){
   const aEnd=noiseFastEnd,bStart=aEnd,cStart=noiseFastEnd+2500;
   const continuous=noiseCount(seq),count=Math.min(n,Math.floor(continuous)),i=Math.min(n-1,count),cycle=continuous-count,drop=ease((cycle-.55)/.4),example=local(i);
   const total=squarePrefix[count],square=deviations[i]**2,all=squarePrefix[n],stackHeight=110,stackBottom=340;
   const phaseA=seq<aEnd,phaseB=seq>=bStart,phaseC=seq>=cStart;
   const draw=phaseA?1:0,dd=deviations[i];
   put(deviationBox,[590,42,195,145,draw]);
   text(noiseLabel,tr('x12_deviations'),605,66,draw);
   text(deviationLabels[0],cycle<.35?'d = '+fmt(dd):'d² = '+fmt(square),605,112,draw*(1-drop));
   const fine=Array.from({length:61},(_,j)=>mix(example.ts[0],example.ts.at(-1),j/60));
   put(localPath,[...fine.flatMap(v=>[X(v),Y(example.value(v))]),draw]);
   put(windowBox,[X(example.ts[0]),top,X(example.ts.at(-1))-X(example.ts[0]),bottom-top,draw*(.25-.15*(+svg.dataset.noiseZoom||0))]);
   put(ring,[X(t[i]),Y(x[i]),draw]);put(sticks[i],[X(t[i]),Y(x[i]),X(t[i]),Y(example.value(t[i])),draw]);
   squareBars.forEach((id,j)=>{const h=stackHeight*(squarePrefix[j+1]-squarePrefix[j])/all;put(id,[590,stackBottom-stackHeight*squarePrefix[j+1]/all,30,h,j<count?1:0]);nodes[id].e.dataset.value=String(deviations[j]**2);});
   put(deviationDot,[mix(620,590,drop),mix(125,stackBottom-stackHeight*(total+square)/all,drop),mix(10,30,drop),mix(10,stackHeight*square/all,drop),draw&&cycle>=.35?1:0]);
   text(sumLabels[0],tr('x15_sum_title'),590,208);text(sumLabels[1],tr('x15_sum_subtitle'),590,226);
   text(arithmeticLabels[0],'Σ d² = '+fmt(total),635,270);text(arithmeticLabels[1],tr('x15_points',{k:count,n}),635,292);
   text(arithmeticLabels[2],tr('x15_mean',{sum:fmt(all),n,mean:fmt(all/n)}),64,378,phaseB?1:0);
   text(arithmeticLabels[3],tr('x15_root',{mean:fmt(all/n),root:fmt(Math.sqrt(all/n))}),64,400,phaseB?1:0);
   text(arithmeticLabels[4],tr('x15_corrected')+' '+tr('x15_noise',{noise:pct(relative)}),64,422,phaseB?1:0);
   const band=phaseB?ease((seq-bStart)/900):0;
   put(bandTop,[...t.flatMap((v,j)=>[X(v),Y(smooth[j]+Math.sqrt(variance[j]))]),...t.slice().reverse().flatMap((v,k)=>{const j=n-1-k;return [X(v),Y(smooth[j]-Math.sqrt(variance[j]))];}),band]);
   text(arithmeticLabels[5],tr('x15_endpoints')+' '+tr('x12c_floor',{floor:pct(m.floor)}),64,444,phaseC?1:0);
   const floor=m.floor*ease((seq-cStart)/1500);
   put(stack[0].bar,[64,460,708*floor,12,phaseC?1:0]);
   svg.dataset.pointCount=String(count);svg.dataset.squaredSum=String(total);svg.dataset.noiseSum=String(floor);svg.dataset.noisePhase=phaseC?'C':phaseB?'B':'A';
   data.forEach(id=>nodes[id].e.setAttribute('r',2.5));
  }else if(state!=='secants')data.forEach(id=>nodes[id].e.setAttribute('r',2.5));
  nodes[predictionPath].e.classList.toggle('story-clean-slope',split);
  svg.dataset.windowLength=String(windowLength);svg.dataset.state=state;svg.dataset.coefficient=String(c);svg.dataset.error=String(error);svg.dataset.term=String(block.term);svg.dataset.complete=String(final);
  return s;
 }
 function render(s){
  s.forEach((a,i)=>{const {e,geometry}=nodes[i],opacity=a.at(-1);e.style.opacity=String(opacity);
   if(geometry==='path')e.setAttribute('d',a.slice(0,-1).reduce((out,v,j)=>out+(j%2?',':j?' L':'M')+v,'')+(e.classList.contains('story-band')||e.classList.contains('story-clipped')?' Z':''));
   if(geometry==='line')for(const [j,key] of ['x1','y1','x2','y2'].entries())e.setAttribute(key,a[j]);
   if(geometry==='dot'||geometry==='text'){e.setAttribute(geometry==='dot'?'cx':'x',a[0]);e.setAttribute(geometry==='dot'?'cy':'y',a[1]);}
   if(geometry==='rect')for(const [j,key] of ['x','y','width','height'].entries())e.setAttribute(key,a[j]);
  });last=s;
 }
 function seek(ms){if(current){clock.cancel(frame);elapsed=Math.max(0,Math.min(durations[current],ms%(durations[current]+3000)));render(scene(current,elapsed));}}
 function finish(){if(current){clock.cancel(frame);elapsed=durations[current];render(scene(current,elapsed));}}
 function enter(state,restart=false){
  reverseZoom=current==='secants'&&state==='noise-visible';
  finish();host.hidden=![...states,...twoStates,...threeStates].includes(state);
  if(host.hidden){current=null;return;}
  const from=last.map(a=>a.slice());current=state;elapsed=0;
  svg.setAttribute('aria-label',document.querySelector('[data-stage="'+state+'"] h2')?.textContent||state);
  const start=clock.now();
  function tick(now){
   elapsed=Math.min(durations[state],now-start);
   const target=reverseZoom&&elapsed<2200?scene('secants',900+2200-elapsed):scene(state,elapsed),blend=restart||reverseZoom||state==='secants'?1:ease(elapsed/900);
   render(blend===1?target:target.map((a,i)=>a.map((v,j)=>nodes[i].e.classList.contains('story-slope')&&j<2?v:mix(from[i][j],v,blend))));
   if(elapsed<durations[state])frame=clock.request(tick);
   else if(!document.hidden&&!new URL(location.href).searchParams.has('fitcheck')){
    // Leave the complete comparison readable before replaying the sequence.
    frame=clock.request(function hold(now){
     if(now-start<durations[state]+3000)frame=clock.request(hold);
     else if(!document.hidden)enter(state,true);
    });
   }
  }
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches)finish();else {tick(start);}
 }
 window.WispChapterOne={model:m,error:chapterError,parts:chapterParts};
 window.WispChapterThree={model:three,states:threeStates,truthCoefficients};
 window.WispChapterTwo={model:two,states:twoStates,slopeRows,predict};
 window.WispChapterStory={states,durations,rounds,roundStart,trialMs,tailMs,enter,finish,seek,local,examples,variance,relative,actual,longRows,lengthClouds,longerLengths,remainingBlocks,sortAt,noisePause,jointPause,squarePrefix,deviations,lengthRms,rates,trueRates,smooth,rateBound,clock,svg,current:()=>current,elapsed:()=>elapsed};
}
initChapterOne();
