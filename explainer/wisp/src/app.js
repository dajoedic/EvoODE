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
function initChapterOne(){
 if(!$('p-c1-data'))return;
 const m=window.WispSolo.model,constant=m.blocks.find(b=>b.term===0),winner=m.blocks.find(b=>b.term===m.winner),norm=soloDot(m.D.b,m.D.b);
 const percent=x=>(100*x).toLocaleString(language,{minimumFractionDigits:1,maximumFractionDigits:1})+' %';
 const args={n:measuredTime.length,t0:fmt(measuredTime[0]),t1:fmt(measuredTime.at(-1)),noise:percent(teaching.sigma),floor:percent(m.floor),explainable:percent(m.explainable),winner:terms[m.winner],meaning:tr(m.winner===0?'x10_constant':'x10_other')};
 for(let i=0;i<7;i++)$('c1-text-'+i).textContent=tr('x10_text_'+i,args);
 if(!m.normalized){$('c1-text-5').textContent=tr('x10_fallback');document.querySelector('[data-i18n="x10_r2"]').textContent=tr('x10_fallback');}
 document.querySelectorAll('[data-c1-eye]').forEach(e=>e.textContent=tr('x10_eye',{i:e.dataset.c1Eye}));
 chart($('c1-visual-0'),[{x:measuredTime,y:teaching.observed,kind:'data',label:tr('x9_measured')}],{legend:false,yLabel:'u'});
 // The 1b axis follows the noise-free rate, so long windows stay readable; noisier rates are clipped to its edge.
 const rateMax=4*Math.max(...LIVE.windows.flatMap(chapterWindows).map(w=>Math.abs(w.clean)));
 // Shared SVG plot supplies a fixed rate axis for 1b and explicit residual sticks elsewhere.
 function plot(target,x,observed,predicted,{rate=false,clean=false,label=''}={}){
  target.replaceChildren();const width=760,height=270,pad={l:76,r:20,t:30,b:42};
  const bound=rate?rateMax:Math.max(1,...observed.map(Math.abs),...predicted.map(Math.abs))*1.08;
  const clipped=observed.filter(v=>Math.abs(v)>bound).length;observed=observed.map(v=>Math.max(-bound,Math.min(bound,v)));
  const X=v=>pad.l+(v-measuredTime[0])/(measuredTime.at(-1)-measuredTime[0])*(width-pad.l-pad.r),Y=v=>height-pad.b-(v+bound)/(2*bound)*(height-pad.t-pad.b);
  const svg=svgNode('svg',{viewBox:`0 0 ${width} ${height}`,class:'chart',role:'img','aria-label':tr(rate?'x10_rate':'x9_change')});target.append(svg);
  for(let i=0;i<=4;i++){const v=bound*(i/2-1);svg.append(svgNode('line',{x1:pad.l,x2:width-pad.r,y1:Y(v),y2:Y(v),class:'grid'}),svgNode('text',{x:pad.l-8,y:Y(v)+4,'text-anchor':'end'},fmt(v)));const t=measuredTime[0]+(measuredTime.at(-1)-measuredTime[0])*i/4;svg.append(svgNode('text',{x:X(t),y:height-22,'text-anchor':'middle'},fmt(t)));}
  svg.append(svgNode('text',{x:pad.l,y:17},tr(rate?'x10_rate':'x9_change')),svgNode('text',{x:width-pad.r,y:height-3,'text-anchor':'end'},tr('j157')));
  if(!clean)x.forEach((v,i)=>svg.append(svgNode('line',{x1:X(v),x2:X(v),y1:Y(observed[i]),y2:Y(predicted[i]),class:'c1-residual'})));
  svg.append(svgNode('path',{d:x.map((v,i)=>(i?'L':'M')+X(v)+','+Y(predicted[i])).join(''),class:clean?'series-truth':'series-model'}));
  x.forEach((v,i)=>svg.append(svgNode('circle',{cx:X(v),cy:Y(observed[i]),r:4,class:'measurement-dot'})));
  const legend=el('figcaption',tr('x9_measured')+' · '+(clean?tr('x10_clean'):label)+(clipped?' · '+tr('x10_clipped',{n:clipped}):''),'caption');legend.dataset.claim='review';target.append(legend);
 }
 const windowSlider=$('c1-window');windowSlider.max=LIVE.windows.length-1;windowSlider.value=0;
 function changes(){const length=LIVE.windows[+windowSlider.value],rows=chapterWindows(length);$('c1-window-value').textContent=tr('x10_length',{samples:length,duration:fmt(measuredTime[length]-measuredTime[0])});plot($('c1-visual-1'),rows.map(w=>w.time),rows.map(w=>w.rate),rows.map(w=>w.clean),{rate:true,clean:true});}
 windowSlider.addEventListener('input',changes);changes();
 const y=m.rows.map(({i})=>m.D.b[i]),prediction=block=>m.rows.map(({i})=>block.coefficient*m.D.A[i][block.term]);
 const emptyPlot=el('div'),emptyBar=el('div');$('c1-visual-2').append(emptyPlot,emptyBar);plot(emptyPlot,m.x,y,y.map(()=>0),{label:tr('x10_none')});
 emptyBar.className='c1-empty-bar';emptyBar.textContent=tr('x10_error',{p:percent(norm/norm)});
 const fitPlot=el('div'),curve=el('div');$('c1-visual-3').append(fitPlot,curve);
 const cSlider=$('c1-c'),span=Math.max(Math.abs(constant.coefficient),1);cSlider.min=constant.coefficient-span;cSlider.max=constant.coefficient+span;cSlider.value=constant.coefficient;
 function fit(){const c=+cSlider.value;$('c1-c-value').textContent=soloNumber(c);plot(fitPlot,m.x,y,m.rows.map(({i})=>c*m.D.A[i][0]),{label:tr('x9_prediction',{block:terms[0]})});
  const cs=Array.from({length:81},(_,i)=>+cSlider.min+(+cSlider.max-cSlider.min)*i/80);cs.push(constant.coefficient);cs.sort((a,b)=>a-b);
  chart(curve,[{x:cs,y:cs.map(v=>100*chapterError(m,0,v)),kind:'model'},{x:[constant.coefficient],y:[100*chapterError(m,0,constant.coefficient)],kind:'truth'}],{legend:false,xLabel:'c',yLabel:tr('x10_error_axis'),point:[c,100*chapterError(m,0,c)]});
  const caption=el('figcaption',tr('x10_minimum',{c:soloNumber(constant.coefficient)}),'caption');caption.dataset.claim='review';curve.append(caption);
  const svg=curve.querySelectorAll('svg')[0];svg.append(svgNode('text',{x:380,y:30,'text-anchor':'middle'},'◆ c* = '+soloNumber(constant.coefficient)));
 }
 cSlider.addEventListener('input',fit);fit();
 const everyBars=el('div'),everyPrediction=el('div'),everyChart=el('div'),everyEquation=el('div',undefined,'solo-equation');everyPrediction.append(everyChart,everyEquation);$('c1-visual-4').append(everyBars,everyPrediction);
 function chooseEvery(term){const block=m.blocks.find(b=>b.term===term);everyBars.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.term===term)));plot(everyChart,m.x,y,prediction(block),{label:tr('x9_prediction',{block:terms[term]})});everyEquation.textContent=soloEquation(block);}
 m.blocks.slice().sort((a,b)=>chapterError(m,a.term,a.coefficient)-chapterError(m,b.term,b.coefficient)).forEach(block=>{const error=chapterError(m,block.term,block.coefficient),button=el('button',undefined,'solo-bar'+(block.term===m.winner?' winner':'')),track=el('span',undefined,'solo-track'),fill=el('span');button.dataset.term=block.term;button.dataset.error=error;fill.style.width=100*error+'%';track.append(fill);button.append(el('span',terms[block.term]),track,el('span',percent(error)));button.addEventListener('click',()=>chooseEvery(block.term));everyBars.append(button);});chooseEvery(m.winner);
 const chips=el('nav',undefined,'c1-chips'),stack=el('div',undefined,'c1-stack'),shares=el('div'),stackLegend=el('figcaption',undefined,'caption');stackLegend.dataset.claim='review';$('c1-visual-5').append(chips,stack,stackLegend,shares);
 function choosePercent(term){const block=m.blocks.find(b=>b.term===term),parts=chapterParts(m,block);stack.replaceChildren();parts.forEach((part,i)=>{const node=el('span',percent(part),'c1-part-'+i);node.style.width=100*part+'%';stack.append(node);});stack.dataset.parts=JSON.stringify(parts);stackLegend.textContent=['floor','reduced','remaining'].map((key,i)=>tr('x10_'+key)+': '+percent(parts[i])).join(' · ');if(!m.normalized)stackLegend.textContent=tr('x10_fallback');chips.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(+b.dataset.term===term)));}
 m.blocks.forEach(block=>{const chip=el('button',terms[block.term]);chip.dataset.term=block.term;chip.addEventListener('click',()=>choosePercent(block.term));chips.append(chip);const row=el('div',undefined,'solo-bar'),track=el('span',undefined,'solo-track'),fill=el('span');fill.style.width=100*block.share+'%';track.append(fill);row.append(el('span',terms[block.term]),track,el('span',percent(block.share)));shares.append(row);});choosePercent(m.winner);
 const solutionEquation=el('div',soloEquation(winner),'solo-equation');$('c1-visual-6').append(solutionEquation);const solutionChart=el('div');$('c1-visual-6').append(solutionChart);plot(solutionChart,m.x,y,prediction(winner),{label:tr('x9_prediction',{block:terms[m.winner]})});
 window.WispChapterOne={model:m,chooseEvery,choosePercent,error:chapterError,parts:chapterParts};
}
initChapterOne();
