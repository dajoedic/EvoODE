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
 for(const attr of ['aria-label','content'])document.querySelectorAll('[data-i18n-'+attr+']').forEach(e=>{const key=e.getAttribute?.('data-i18n-'+attr);if(key)e.setAttribute(attr,tr(key));});
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
window.typesetAll=()=>{if(!window.katex)return;document.querySelectorAll("[data-tex]").forEach(e=>window.katex.render(e.dataset.tex,e,{throwOnError:false,output:'mathml',displayMode:!e.classList.contains('inline')}));};
function math(target,tex){target.dataset.tex=tex;target.textContent=tex;if(window.katex)window.katex.render(tex,target,{throwOnError:false,output:'mathml',displayMode:!target.classList.contains('inline')});}
function equation(support,coefficients){return '\\frac{du}{dt}='+ (support.length?support.map((j,i)=>`${i&&coefficients[i]>=0?'+':''}${fmt(coefficients[i],5)}\\,${texTerms[j]}`).join(' '):'0');}
function options(target,values,label=v=>v){target.replaceChildren(...values.map(v=>{const e=el('option',label(v));e.value=v;return e;}));}
function chart(target,series,{title='',xLabel=tr('j157'),yLabel=tr('j158'),areas=[],highlight=null,point=null,zeroBase=false,integerX=false}={}){
  target.replaceChildren();
  const width=560,height=270,pad={l:76,r:16,t:36,b:42};
  const good=series.flatMap(s=>s.x.map((x,i)=>[x,s.y[i]])).filter(([x,y])=>Number.isFinite(x)&&Number.isFinite(y)&&Math.abs(y)<1e12);
  if(!good.length){target.append(el('p',tr('j159'),'notice'));return;}
  let xmin=Math.min(...good.map(p=>p[0])),xmax=Math.max(...good.map(p=>p[0])),ymin=Math.min(...good.map(p=>p[1])),ymax=Math.max(...good.map(p=>p[1]));
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
  for(const s of series){let d='',drawing=false;for(let i=0;i<s.x.length;i++){
    const v=s.y[i];if(!Number.isFinite(v)||Math.abs(v)>1e12){drawing=false;continue;}d+=`${drawing?'L':'M'}${X(s.x[i]).toFixed(3)},${Y(v).toFixed(3)}`;drawing=true;
  }if(s.x.length===1)svg.append(svgNode('circle',{cx:X(s.x[0]),cy:Y(s.y[0]),r:4,fill:'var(--residual)'}));svg.append(svgNode('path',{d,class:`series-${s.kind||'truth'} ${s.style||''}`}));}
  svg.append(svgNode('text',{x:pad.l,y:17},title));
  svg.append(svgNode('text',{x:width-pad.r,y:height-4,"text-anchor":'end'},xLabel));
  svg.append(svgNode('text',{transform:`translate(14 ${(pad.t+height-pad.b)/2}) rotate(-90)`,"text-anchor":'middle'},yLabel));
  if(point)svg.append(svgNode('circle',{cx:X(point[0]),cy:Y(point[1]),r:5,fill:'var(--model)',stroke:'var(--panel)',"stroke-width":2}));
  target.append(svg);
  const legend=el('div',undefined,'caption');legend.textContent=series.map(s=>`${s.label||s.kind}${s.style?tr('line_style'):''}`).join(' · ');target.append(legend);
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
function hook(rule){const series=[{x:measuredTime,y:measuredNoise(teaching?.sigma||.03),kind:'data',style:'dots',label:teaching?tr('q5_measurements',{v0:teaching.cell_id}):tr('j163')}];if(rule){const initial=[measuredTruth[0]],y=rk4(measuredTime,initial,x=>[rule==='logistic'?demo.constants[0]*x[0]*(1-x[0]/demo.constants[1]):rule==='linear'?.25*x[0]:-.2*x[0]]).map(x=>x[0]);series.push({x:measuredTime,y,kind:'model',label:tr('j164')});}chart($("hook-chart"),series,{title:tr('j166')});}
$('guess').addEventListener('click',e=>{if(!e.target.dataset.guess)return;const guess=e.target.dataset.guess;hook(guess);$("guess-feedback").textContent=guess==='logistic'?tr('j168'):tr('j169');[...$('guess').querySelectorAll('button')].forEach(b=>b.setAttribute("aria-pressed",String(b===e.target)));});hook();
$('rate').value=demo.constants[0];$('capacity').value=demo.constants[1];
function growthRule(){const rate=+$('rate').value,capacity=+$('capacity').value;$("rate-value").value=fmt(rate);$("capacity-value").value=fmt(capacity);chart($("logistic-chart"),[{x:time,y:logistic(rate,capacity),kind:'truth',label:tr('j174')}],{title:tr('j175')});}
['rate','capacity'].forEach(id=>$(id).addEventListener('input',growthRule));growthRule();
math($("predator-equation"),predator.equation.map((s,i)=>`\\frac{d${i?'v':'u'}}{dt}=${s.replaceAll('x_0','u').replaceAll('x_1','v').replaceAll('*','\\,')}`).join('\\qquad '));
function predatorDraw(){const i=+$("predator-time").value,t=predator.t.slice(0,i+1),x=predator.x.slice(0,i+1);$("predator-value").value=fmt(predator.t[i]);chart($("predator-chart"),[{x:t,y:x.map(r=>r[0]),kind:'truth',label:tr('prey')},{x:t,y:x.map(r=>r[1]),kind:'model',style:'dashed',label:tr('predators')}],{title:tr('j180'),yLabel:tr('j181')});chart($("phase-chart"),[{x:predator.x.map(r=>r[0]),y:predator.x.map(r=>r[1]),kind:'truth',label:tr('j183')}],{title:tr('j184'),xLabel:tr('j185'),yLabel:tr('j186'),point:predator.x[i]});}
$("predator-time").max=predator.t.length-1;$("predator-time").value=predator.t.length-1;$("predator-time").addEventListener('input',predatorDraw);predatorDraw();
const coeff=[0,.23,-.005,0,0,0],enabled=[false,true,false,false,false,false];
terms.forEach((name,i)=>{const card=el('div',undefined,"term-card"),label=el('label',name),check=el('input');check.type='checkbox';check.checked=enabled[i];check.setAttribute("aria-label",tr('include_term',{v0:name}));label.append(check);const range=el('input');range.type='range';range.min=i===0?'-10':i===1?'-1':i===2?'-.03':i===3?'-.001':'-2';range.max=i===0?'10':i===1?'1':i===2?'.03':i===3?'.001':'2';range.step=i===3?'.00001':i===2?'.0001':'.01';range.value=coeff[i];range.setAttribute("aria-label",tr('j188',{v0:(name)}));const out=el('output',fmt(coeff[i]));check.addEventListener('change',()=>{enabled[i]=check.checked;play();});range.addEventListener('input',()=>{coeff[i]=+range.value;out.value=fmt(coeff[i]);play();});card.append(label,range,out);$("term-cards").append(card);});
const interactionCard=el('div',undefined,"term-card");interactionCard.append(el('label','u·v'),el('p',tr('j190'),'caption'));$("term-cards").append(interactionCard);
function play(){const limit=2*Math.max(...truth.map(Math.abs)),indices=enabled.map((v,i)=>v?i:-1).filter(i=>i>=0),c=indices.map(i=>coeff[i]);math($("play-equation"),equation(indices,c));const curve=rk4(time,demo.initial,x=>[W.basis(x[0]).reduce((s,v,i)=>s+(enabled[i]?v*coeff[i]:0),0)]).map(x=>x[0]);chart($("play-chart"),[{x:time,y:truth,kind:'data',style:'dots',label:tr('j193')},{x:time,y:curve.map(v=>Number.isFinite(v)?Math.max(-limit,Math.min(limit,v)):NaN),kind:'model',label:tr('j194')}],{title:tr('j195')});const clipped=curve.some(v=>!Number.isFinite(v)||Math.abs(v)>limit);$("play-status").textContent=(curve.every(Number.isFinite)?tr('j197',{v0:(fmt(curve.reduce((s,v,i)=>s+(v-truth[i])**2,0)/curve.length))}):tr('j198'))+(clipped?tr('j199'):'');}
$("play-reset").addEventListener('click',()=>{coeff.splice(0,6,0,demo.constants[0],-demo.constants[0]/demo.constants[1],0,0,0);enabled.splice(0,6,false,true,true,false,false,false);[...$("term-cards").children].slice(0,terms.length).forEach((card,i)=>{card.querySelector('[type=checkbox]').checked=enabled[i];card.querySelector('[type=range]').value=coeff[i];card.querySelector('output').value=fmt(coeff[i]);});play();});play();
options($('dimensions'),LIVE.catalogues.map(c=>c.dim));
function catalogue(){const c=LIVE.catalogues.find(c=>c.dim===+$('dimensions').value);$("combination-count").textContent=tr('j202',{v0:(c.count),v1:(BigInt(c.combinations).toLocaleString(language)),v2:(c.dim),v3:(c.dim===1?'':'s')});$("catalogue-list").textContent=c.terms.join(' · ');}
$('dimensions').addEventListener('change',catalogue);catalogue();
options($("window-length"),LIVE.windows,v=>tr('j205',{v0:(v),v1:(v===1?'':'s')}));$("window-length").value=16;
function finiteDifference(x){const time=measuredTime;return x.map((v,i)=>i===0?(x[1]-v)/(time[1]-time[0]):i===x.length-1?(v-x[i-1])/(time[i]-time[i-1]):(x[i+1]-x[i-1])/(time[i+1]-time[i-1]));}
function redrawNoise(){const time=measuredTime,truth=measuredTruth;sigma=+$("noise-level").value;$("noise-value").value=pct(sigma);noisy=measuredNoise(sigma);$("noise-provenance").textContent=teaching?(sigma===teaching.sigma?tr('j209',{v0:(teaching.cell_id)}):tr('j210',{v0:(teaching.cell_id),v1:(pct(teaching.sigma))})):tr('j211');chart($("noise-chart"),[{x:time,y:truth,kind:'truth',label:tr('j213')},{x:time,y:noisy,kind:'data',style:'dots',label:tr('j214')}],{title:tr('j215')});chart($("derivative-chart"),[{x:time,y:truth.map(v=>demo.constants[0]*v*(1-v/demo.constants[1])),kind:'truth',label:tr('j217')},{x:time,y:finiteDifference(noisy),kind:'data',style:'dots',label:tr('j218')}],{title:tr('j219'),yLabel:tr('j220')});weakDraw();computePath();}
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
options($("path-example"),['illustration',...LIVE.references.map(r=>r.cell_id)],id=>id==='illustration'?tr('j237'):`${id}${LIVE.references.find(r=>r.cell_id===id).available?'':tr('j238')}`);
function computePath(){const choice=$("path-example").value;try{pathError=null;if(choice==='illustration'){currentPath=W.path(measuredTime,noisy,LIVE);$("path-provenance").textContent=tr('j242',{v0:(teaching&&sigma===teaching.sigma?tr('j240')+teaching.cell_id:tr('j241')),v1:(pct(sigma)),v2:(LIVE.cap),v3:(LIVE.sse_stop),v4:(LIVE.backward_fraction)});}else{const r=LIVE.references.find(r=>r.cell_id===choice);if(!r.available){currentPath=null;pathError=tr('j243');$("path-provenance").textContent=pathError;}else{currentPath=W.path(r.t,r.x,LIVE);$("path-provenance").textContent=tr('j244',{v0:(r.cell_id)});}}}catch(err){currentPath=null;pathError=tr('j245',{v0:(err.message)});$("path-provenance").textContent=pathError;}
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
if(MANIFEST.foba_cell){$("recorded-foba").append(el('p',tr('j271',{v0:(MANIFEST.foba_cell)})));MANIFEST.foba_events.forEach(e=>$("recorded-foba").append(el('p',tr('recorded_step',{v0:e.step,v1:e.added.map(i=>terms[i-1]).join(', '),v2:e.removed.map(i=>terms[i-1]).join(', ')}))));MANIFEST.foba_states.forEach(s=>{const e=s.equations[0],box=el('div',undefined,'math');math(box,`\\text{${tr('h083')} }${s.step}: `+equation(e.basis_indices.map(i=>i-1),e.coefficients));$("recorded-foba").append(box);});}else $("recorded-foba").append(el('p',tr('j272')));
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
function conditionCells(stratum){return RESULTS.cells.filter(c=>axesMatch(c.row)&&(!RESULTS.exclude_clean_controls||+c.row.sigma!==0||+c.row.rho!==0)&&c.row.stratum===stratum&&+c.row.sigma===+$("result-sigma").value&&($("result-rho").value==='pooled'||+c.row.rho===+$("result-rho").value));}
function metric(container,row,label,cls=''){const e=el('div',undefined,`metric ${cls}`);e.append(el('b',label));if(!row){e.append(el('small',tr('j283')));container.append(e);return;}e.append(el('div',pct(row.rate)));const meter=el('div',undefined,'meter'),fill=el('span');fill.style.width=`${Math.max(0,Math.min(100,+row.rate*100))}%`;meter.append(fill);e.append(meter);const isSummary=row.configuration==='all_ten';e.append(el('small',isSummary?tr('j284',{v0:(pct(row.min_rate)),v1:(pct(row.max_rate)),v2:(fmt(row.denominator,8))}):tr('cell_count',{v0:fmt(row.numerator,8),v1:fmt(row.denominator,8)})));if(row.method!==RESULTS.primary_method&&!isSummary){const config=el('div',row.configuration,'caption');config.style.overflowWrap='anywhere';e.append(config);}container.append(e);}
function resultsDraw(){const weight=$("result-weight").value;$("metric-key").textContent=tr('j287',{v0:(fmt(RESULTS.score_threshold)),v1:(weightLabel(weight)),v2:(RESULTS.primary_method)});
  $('strata').replaceChildren();for(const stratum of strata){const box=el('article',undefined,'stratum');box.append(el('h3',stratum.replaceAll('_',' ')));const cells=conditionCells(stratum),systems=new Set(cells.map(c=>c.system_id)),units=new Set(cells.map(c=>c.row.unit_id));box.append(el('p',tr('j288',{v0:(systems.size),v1:(units.size),v2:(cells.length)}),'caption'));const button=el('button',tr('inspect',{v0:stratum.replaceAll('_',' ')}));button.type='button';button.setAttribute("aria-pressed",String(stratum===selectedStratum));button.addEventListener('click',()=>{selectedStratum=stratum;resultsDraw();$("system-select").focus();});box.append(button);
    const rows=resultRates.filter(r=>axesMatch(r)&&r.stratum===stratum&&+r.sigma===+$("result-sigma").value&&(r.rho==='pooled'?$("result-rho").value==='pooled':$("result-rho").value!=='pooled'&&+r.rho===+$("result-rho").value)),groups=new Map();rows.forEach(r=>{const key=`${methodLabel(r.method)} / ${(RESULTS.selected_configuration_methods||[]).includes(r.method)&&r.configuration!=='all_ten'?tr('j290'):r.configuration}${axes.map(a=>` / ${a.label}: ${r[a.key]??tr('unspecified')}`).join('')}`;if(!groups.has(key))groups.set(key,{});groups.get(key)[r.metric]=r;});
    if(!groups.size)box.append(el('p',tr('j291'),'caption'));
    for(const [key,metrics] of groups){const group=el('div',undefined,"rate-row");group.append(el('div',key,"rate-name"));if(metrics.raw_exact||metrics.pruned_exact){const structure=el('div',undefined,"metric-pair");metric(structure,metrics.raw_exact,tr('j295'));metric(structure,metrics.pruned_exact,tr('j296'));group.append(structure);}const curves=el('div',undefined,"metric-pair");metric(curves,metrics[`reconstruction_${weight}_hit`],tr('j297'),'curve');metric(curves,metrics[`generalization_${weight}_hit`],tr('j298'),'curve');group.append(curves);box.append(group);}
    $('strata').append(box);
  }systemsDraw();}
function systemsDraw(){const cells=conditionCells(selectedStratum),ids=[...new Set(cells.map(c=>c.system_id))].sort((a,b)=>a-b);options($("system-select"),ids,id=>`${id}`);cellsDraw();}
function cellsDraw(){const cells=conditionCells(selectedStratum).filter(c=>c.system_id===+$("system-select").value);options($("cell-select"),cells.map(c=>c.row.cell_id));cellDraw();}
function storedEquation(c){const active=JSON.parse(c.row.active_idxs),params=JSON.parse(c.row.params);let index=0;return active.map((support,eq)=>`\\frac{du_{${eq+1}}}{dt}=`+(support.length?support.map(i=>{const coef=params[index++],term=c.terms[i-1].replaceAll('*','\\,').replace(/u(\d+)/g,'u_{$1}').replace(/\^(\d+)/g,'^{$1}');return `${coef>=0?'+':''}${fmt(coef,6)}\\,${term}`;}).join(' '):'0'));}
function cellDraw(){const c=RESULTS.cells.find(c=>c.row.cell_id===$("cell-select").value);$("cell-detail").replaceChildren();if(!c){$("cell-detail").append(el('p',tr('j301')));return;}const root=$("cell-detail");root.append(el('p',c.row.cell_id,'caption'),el('h3',c.exact?tr('j302'):tr('j303')));(c.truth||[]).forEach(s=>{const e=el('div',undefined,'math');math(e,s.replaceAll('**','^').replaceAll('x_0','u_{1}').replaceAll('x_1','u_{2}').replaceAll('x_2','u_{3}').replaceAll('x_3','u_{4}').replaceAll('*','\\,'));root.append(e);});root.append(el('h3',tr('j304')));storedEquation(c).forEach(tex=>{const e=el('div',undefined,'math');math(e,tex);root.append(e);});
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
options($("stop-example"),stopFeatures.map(f=>f.cell_id));
function stopDraw(){const feature=stopFeatures.find(f=>f.cell_id===$("stop-example").value);if(!feature)return;
 const r=feature.stop_reference,p=W.significancePath(r.t,r.x,r.threshold),D=p.design,norm=D.b.reduce((s,v)=>s+v*v,0),supports=[[],...p.steps.map(s=>s.support)],steps=supports.map((_,i)=>i);
 chart($("stop-chart"),[{x:steps,y:[1,...p.steps.map(s=>s.remaining)],kind:'residual',label:tr('j265')},{x:steps,y:supports.map(s=>W.noiseFloor(D,s,p.variance)/norm),kind:'data',style:'dashed',label:tr('j317')}],{title:tr('j318'),xLabel:tr('j267'),yLabel:tr('j268'),zeroBase:true});
 $("stop-summary").textContent=tr('j320',{v0:(LIVE.cap),v1:(p.steps.length),v2:(fmt(r.threshold,5))});
}
$("stop-example").addEventListener('change',stopDraw);stopDraw();
options($("fit-example"),featured.map(f=>f.cell_id));
function plotBundle(root,bundle,observed,title){
 if(!bundle){root.append(el('p',tr('j322'),'notice'));if(observed){const plot=el('div');root.append(plot);chart(plot,[{x:observed.t,y:observed.x.map(r=>r[0]),kind:'data',style:'dots',label:tr('j214')}],{title});}return;}
 bundle.truth[0].forEach((_,j)=>{const plot=el('div');root.append(plot);const series=[{x:bundle.t,y:bundle.truth.map(r=>r[j]),kind:'truth',style:'dashed',label:tr('j306')},{x:bundle.t,y:bundle.model.map(r=>r[j]),kind:'model',label:tr('j323')}];if(observed)series.push({x:observed.t,y:observed.x.map(r=>r[j]),kind:'data',style:'dots',label:tr('j214')});chart(plot,series,{title:`${title} · u${j+1}`,yLabel:`u${j+1}`});});
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
 const root=el('article',undefined,'panel'),heading=el('h3',feature.cell_id);root.append(heading);
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

