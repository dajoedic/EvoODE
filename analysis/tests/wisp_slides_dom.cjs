/* Minimal DOM for executing both shipped presentation scripts against real HTML.
 * It deliberately supplies no layout: Edge is responsible for pixel acceptance. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const base=process.argv[2],fixture=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
class Node {
 constructor(tag,attrs={},text=''){this.tagName=tag.toUpperCase();this.attrs={...attrs};this.children=[];this.parentElement=null;this.style={};this.listeners={};this._text=text;this._value=attrs.value||'';this.dataset={};for(const [k,v] of Object.entries(attrs))if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=v;this.open='open' in attrs;
  this.classList={contains:c=>this.className.split(' ').includes(c),add:c=>{if(!this.classList.contains(c))this.className=(this.className+' '+c).trim();},remove:c=>{this.className=this.className.split(' ').filter(x=>x!==c).join(' ');},toggle:(c,on)=>{if(on===undefined)on=!this.classList.contains(c);this.classList[on?'add':'remove'](c);return on;}};
 }
 get id(){return this.attrs.id||'';}set id(v){this.attrs.id=v;}
 get className(){return this.attrs.class||'';}set className(v){this.attrs.class=v;}
 get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}set textContent(v){this._text=String(v);this.children=[];}
 get value(){if(this.tagName==='SELECT'&&!this._value)return this.children[0]?.value||'';return this._value;}set value(v){this._value=String(v);}
 get href(){return this.attrs.href||'';}set href(v){this.attrs.href=v;}get hash(){return this.href.includes('#')?'#'+this.href.split('#')[1]:'';}
 append(...nodes){for(const n of nodes){n.remove();n.parentElement=this;this.children.push(n);}}
 prepend(...nodes){for(const n of nodes.reverse()){n.remove();n.parentElement=this;this.children.unshift(n);}}
 remove(){if(this.parentElement){const p=this.parentElement;p.children=p.children.filter(c=>c!==this);this.parentElement=null;}}
 before(n){const p=this.parentElement;n.remove();n.parentElement=p;p.children.splice(p.children.indexOf(this),0,n);}
 replaceChildren(...nodes){for(const n of this.children)n.parentElement=null;this.children=[];this._text='';this.append(...nodes);}
 setAttribute(k,v){this.attrs[k]=String(v);}getAttribute(k){return this.attrs[k];}removeAttribute(k){delete this.attrs[k];}
 addEventListener(k,fn){(this.listeners[k]??=[]).push(fn);}emit(k,e={}){for(const fn of this.listeners[k]||[])fn({target:this,type:k,...e});}
 get offsetTop(){return Math.max(0,doc.querySelectorAll('main > .page').indexOf(this))*innerHeight;}
 animate(keyframes,options){this.lastAnimation={keyframes,options};}
 scrollIntoView(){global.lastScrolled=this.id;global.scrollY=this.offsetTop;}focus(){}
 showModal(){this.open=true;this.setAttribute('open','');}close(){this.open=false;this.removeAttribute('open');}
 matches(selector){return selector.split(',').some(raw=>{let s=raw.trim();if(s.includes(':not([open])')){if(this.open)return false;s=s.replace(':not([open])','');}
  for(const match of s.matchAll(/\[([^\]^=]+)(\^=|=)?(?:"([^"]*)"|'([^']*)'|([^\]]*))?\]/g)){
   const attr=match[1],expected=match[3]??match[4]??match[5],value=attr.startsWith('data-')?(this.dataset[attr.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]??this.attrs[attr]):this.attrs[attr];
   if(value===undefined||(match[2]==='='&&String(value)!==expected)||(match[2]==='^='&&!String(value).startsWith(expected)))return false;
  }
  s=s.replace(/\[[^\]]*\]/g,'');const id=s.match(/#([\w-]+)/);if(id&&this.id!==id[1])return false;
  for(const m of s.matchAll(/\.([\w-]+)/g))if(!this.classList.contains(m[1]))return false;
  const tag=s.match(/^[a-z][\w-]*/i);return !tag||this.tagName===tag[0].toUpperCase();
 });}
 closest(selector){for(let e=this;e;e=e.parentElement)if(e.matches(selector))return e;return null;}
 querySelectorAll(selector){if(selector.startsWith(':scope > '))return this.children.filter(e=>e.matches(selector.slice(9)));
  const found=[];const walk=e=>{for(const child of e.children){found.push(child);walk(child);}};walk(this);
  return found.filter(e=>selector.split(',').some(part=>{const tokens=part.trim().split(/\s+(?![^\[]*\])/);if(tokens.length===1)return e.matches(part);
   let current=e;if(!current.matches(tokens.pop()))return false;
   while(tokens.length){const next=tokens.pop();if(next==='>'){current=current.parentElement;if(!current?.matches(tokens.pop()))return false;}else{current=current.parentElement;while(current&&!current.matches(next))current=current.parentElement;if(!current)return false;}}
   return true;
  }));
 }
 querySelector(s){return this.querySelectorAll(s)[0]||null;}
}
function inflate(record){const n=new Node(record.tag,record.attrs,record.text);for(const c of record.children)n.append(inflate(c));return n;}
const html=inflate(fixture.tree),doc=new Node('document');doc.append(html);doc.documentElement=html;doc.body=doc.querySelector('body');doc.fonts={ready:Promise.resolve()};const idIndex=new Map(doc.querySelectorAll('[id]').map(e=>[e.id,e]));doc.getElementById=id=>{if(!idIndex.has(id)){const found=doc.querySelector('#'+id);if(found)idIndex.set(id,found);}return idIndex.get(id)||null;};doc.createElement=t=>new Node(t);doc.createElementNS=(_,t)=>new Node(t);
doc.getElementById('wisp-data').textContent=JSON.stringify(fixture.data);
if(fixture.configuration==='legacy')global.WispVisibleChapters=['intro','later'];
global.document=doc;global.window=global;global.innerWidth=1366;global.innerHeight=657;
global.location={href:'file:///wisp.html?lang='+fixture.language,get hash(){return new URL(this.href).hash;},assign(url){this.href=String(url);}};
global.history={pushState(_,__,url){location.href=String(url);},replaceState(_,__,url){location.href=String(url);}};
global.localStorage={getItem(){return null;},setItem(){}};global.matchMedia=()=>({matches:false,addEventListener(){}});
let now=0,frameId=0;const frames=new Map();global.performance={now:()=>now};global.scrollY=0;global.scrollTo=(_,y)=>{global.scrollY=y;};global.requestAnimationFrame=fn=>{frames.set(++frameId,fn);return frameId;};global.cancelAnimationFrame=id=>frames.delete(id);function advance(ms=800,stride=160){const end=now+ms;while(now<end){now+=Math.min(stride,end-now);const queue=[...frames.values()];frames.clear();queue.forEach(fn=>fn(now));}}
global.WispStoryClock={now:()=>now,request:fn=>requestAnimationFrame(fn),cancel:id=>cancelAnimationFrame(id)};
const events={};global.addEventListener=(k,fn)=>(events[k]??=[]).push(fn);global.WispCompute=require(base+'/src/compute.js');
let dishVisible;global.IntersectionObserver=class{constructor(fn){dishVisible=fn;}observe(){}disconnect(){}};
vm.runInThisContext(fs.readFileSync(base+'/src/app.js','utf8'),{filename:'app.js'});
vm.runInThisContext(fs.readFileSync(base+'/src/pages.js','utf8'),{filename:'pages.js'});
// WP-X12: drive the shipped persistent stage with the injected frame clock.
if(fixture.configuration==='delivered'){
 const story=WispChapterStory,slides=WispSlides,m=WispChapterOne.model,t=fixture.data.live.teaching.t,x=fixture.data.live.teaching.observed,truth=fixture.data.live.teaching.truth;
 const close=(a,b)=>assert(Math.abs(a-b)<=1e-9*Math.max(1,Math.abs(b)),`${a} != ${b}`);
 const ids=['p-hook','p-challenge','p-c1-data','p-c1-slope','p-c1-noise-visible','p-c1-secants','p-c1-changes','p-c1-error-empty','p-c1-fit','p-c1-every','p-c1-noise','p-c1-percent','p-c1-solution'];
 const twoIds=['standing','residual','joint','error','solution'].map(s=>'p-c2-'+s);
 assert.deepEqual(slides.pages.map(p=>p.id),ids.concat(twoIds));
 slides.nav.go(2);assert.equal(doc.getElementById('masthead-title').textContent,tr('x12c_chapter'));assert.equal(doc.getElementById('chapter-progress').getAttribute('aria-valuemax'),'11');
 assert.deepEqual(slides.pages.slice(2,13).map(p=>p.dataset.stage),story.states);
 assert.equal(doc.querySelectorAll('#c1-stage svg').length,1);
 assert(doc.getElementById('p-results').hidden);assert(doc.getElementById('p-solution').hidden);
 for(const id of ['p-results','p-headline','p-solution','p-glossary']){slides.nav.go(0);slides.nav.link('#'+id);assert.equal(slides.nav.index,0);}
 function event(key,target=doc.body){let prevented=false;for(const fn of events.keydown||[])fn({type:'keydown',key,target,preventDefault(){prevented=true;}});advance();return prevented;}
 slides.nav.go(0);advance();assert(!event('ArrowRight'));assert.equal(slides.nav.index,0);assert(!event('ArrowLeft'));assert.equal(slides.nav.index,0);
 assert.strictEqual(story.clock,global.WispStoryClock);
 const svg=story.svg,original=svg;
 for(let i=1;i<ids.length;i++){event(i%3===0?'PageDown':i%3===1?'ArrowDown':' ');assert.equal(slides.nav.index,i);advance(18000,1000);story.finish();if(i>=2){assert.equal(svg.dataset.state,story.states[i-2]);assert.equal(svg.dataset.complete,'true');assert.strictEqual(doc.querySelector('#c1-stage svg'),original);}}
 event('PageDown');assert.equal(slides.nav.index,ids.length);event('ArrowUp');assert.equal(slides.nav.index,ids.length-1);
 assert.equal(doc.querySelectorAll('.page-dots a').filter(a=>!a.hidden).length,11);
 assert.equal(doc.querySelectorAll('.c1-page input').length,1);
 const saved=[];
 for(const [i,state] of story.states.entries()){
  slides.nav.go(i+2);advance(18000,1000);story.finish();assert.equal(svg.dataset.state,state);assert.equal(svg.dataset.complete,'true');
  const dots=doc.querySelectorAll('#c1-stage .measurement-dot'),sticks=doc.querySelectorAll('#c1-stage .story-residual'),rates=doc.querySelectorAll('#c1-stage .story-slope');
  if(state==='data')assert.equal(dots.filter(d=>+d.style.opacity===1).length,t.length);
  if(state==='noise-visible')sticks.forEach((d,j)=>{close(+d.dataset.value,Math.abs(x[j]-truth[j]));assert.equal(+d.style.opacity,1);const lo=Math.min(...x)*.95,hi=Math.max(...x)*1.05;close(+d.getAttribute('y1'),392-(x[j]-lo)/(hi-lo)*350);close(+d.getAttribute('y2'),392-(truth[j]-lo)/(hi-lo)*350);});
  if(state==='secants'){
   assert.equal(rates.filter(d=>+d.style.opacity===1).length,story.rates.filter(r=>Math.abs(r.rate)<=story.rateBound).length);
   rates.forEach((d,j)=>close(+d.dataset.value,(x[j+1]-x[j])/(t[j+1]-t[j])));
   // Verify the actual rendered y coordinates independently of scene metadata.
   const bound=4*Math.max(...story.trueRates.map(Math.abs));
   close(+svg.dataset.slopeBound,bound);
   assert.equal(doc.querySelectorAll('.story-clipped').filter(d=>+d.style.opacity===1).length,story.rates.filter(r=>Math.abs(r.rate)>bound).length);
   rates.forEach(d=>close(+d.getAttribute('cy'),392-(Math.max(-bound,Math.min(bound,+d.dataset.value))+bound)/(2*bound)*122));
  }
  if(state==='windows'){
   story.lengthClouds.forEach(cloud=>{
    // Earlier lengths stay visible, dimmed, once the next length is drawn.
    const visible=cloud.dots.map(id=>svg.children[id]).filter(d=>+d.style.opacity>0);
    assert.equal(visible.length,cloud.rows.length);
    visible.forEach((d,j)=>{close(+d.dataset.value,cloud.rows[j].rate);close(+d.getAttribute('cy'),392-(Math.max(-story.rateBound,Math.min(story.rateBound,cloud.rows[j].rate))+story.rateBound)/(2*story.rateBound)*122);});
   });
   assert.equal(new Set(story.lengthClouds.map(c=>svg.children[c.dots[0]].style.fill)).size,story.longerLengths.length);
  }
  if(state==='error-empty'){close(+doc.querySelector('.story-error').getAttribute('width'),708);close(+svg.dataset.error,1);assert(doc.querySelector('#c1-stage').textContent.includes('100,0 %')||doc.querySelector('#c1-stage').textContent.includes('100.0 %'));}
  if(state==='fit'){
   const block=m.blocks.find(b=>b.term===0);close(+svg.dataset.coefficient,2*block.coefficient);close(+svg.dataset.error,WispChapterOne.error(m,0,2*block.coefficient));assert(!doc.getElementById('c1-play').hidden);
   const slider=doc.getElementById('c1-c');assert(!event('ArrowDown',slider));slider.value=+slider.max;slider.emit('input');assert(+svg.dataset.error>1-block.gain);story.finish();
  }
  if(state==='every'){
   const slots=doc.querySelectorAll('#c1-stage .story-slot');assert.equal(slots.length,6);
   const sorted=slots.slice().sort((a,b)=>+a.getAttribute('y')-+b.getAttribute('y'));
   sorted.forEach((d,j)=>{const b=m.blocks.find(b=>b.term===+d.dataset.term);close(+d.dataset.value,b.share);assert.equal(+d.dataset.rank,j);if(j)assert(+d.dataset.value<=+sorted[j-1].dataset.value);});
   assert.equal(+sorted[0].dataset.term,fixture.data.live.featured[0].path[0].active_idxs[0][0]-1);
   assert.equal(+svg.dataset.term,m.winner);
  }
  if(state==='noise-estimate'){
   assert.deepEqual(story.variance,WispCompute.noiseVariance(t,x));close(story.relative,story.variance.reduce((s,v,j)=>s+Math.sqrt(v)/Math.abs(x[j]),0)/x.length);
   const noise=x.map((v,j)=>v-truth[j]),actual=m.D.windows.reduce((s,[a,b])=>s+(noise[b]-noise[a])**2,0)/m.D.b.reduce((s,v)=>s+v*v,0);close(story.actual,actual);
   for(const reference of fixture.cubic){const local=story.local(reference.center);assert.equal(local.start,reference.start);reference.t.forEach((tt,j)=>close(local.value(tt),reference.y[j]));}
   const bandNumbers=doc.querySelector('.story-band').getAttribute('d').match(/[-+]?(?:[0-9]*[.])?[0-9]+(?:e[-+]?[0-9]+)?/gi).map(Number);assert.equal(bandNumbers.length,4*t.length);
   t.forEach((tt,j)=>{const fitted=story.local(j).value(tt),lo=Math.min(...x)*.95,hi=Math.max(...x)*1.05;close(story.smooth[j],fitted);close(bandNumbers[2*j+1],302-(fitted+Math.sqrt(story.variance[j])-lo)/(hi-lo)*260);close(bandNumbers[2*(2*t.length-1-j)+1],302-(fitted-Math.sqrt(story.variance[j])-lo)/(hi-lo)*260);});
   assert.equal(dots.filter(d=>+d.style.opacity===1).length,512);assert.equal(+doc.querySelector('.story-band').style.opacity,1);assert(+doc.querySelector('.story-part-0').getAttribute('y')>302);
   assert.equal(story.examples.length,5);story.examples.forEach((ex,j)=>{assert.equal(ex.center,Math.round(t.length/3)+j);close(ex.deviation,x[ex.center]-ex.value(t[ex.center]));});
   const pct=v=>(100*v).toLocaleString(fixture.language,{minimumFractionDigits:1,maximumFractionDigits:1})+' %';
   for(const v of [story.relative,fixture.data.live.teaching.sigma,m.floor,actual])assert(doc.getElementById('c1-noise-result').textContent.includes(pct(v)));
   if(fixture.language==='en')console.log(JSON.stringify({estimate:story.relative,added:fixture.data.live.teaching.sigma,floor:m.floor,actual,examples:story.examples.map(e=>({center:e.center,deviation:e.deviation}))}));
  }
  assert.equal(doc.querySelector('.story-caption').style.visibility,i>=4&&i<=7?'visible':'hidden');
  if(state==='percent')close(WispChapterOne.parts(m,m.blocks.find(b=>b.term===m.winner)).reduce((a,b)=>a+b),1);
  if(state==='solution'){assert.equal(+svg.dataset.term,m.winner);assert(doc.querySelector('.story-equation').textContent.includes('du/dt'));}
  // Record full geometry and compare it after a backwards entry and under reduced motion.
  story.enter(state);advance(18000,1000);story.finish();saved[i]=svg.children.map(e=>({...e.attrs,opacity:e.style.opacity}));
 }
 for(let i=story.states.length-1;i>=0;i--){story.enter(story.states[i]);advance(18000,1000);story.finish();svg.children.forEach((e,j)=>assert.deepEqual({...e.attrs,opacity:e.style.opacity},saved[i][j],story.states[i]+' node '+j));}
 global.matchMedia=()=>({matches:true,addEventListener(){}});
 story.states.forEach((state,i)=>{story.enter(state);assert.equal(svg.dataset.complete,'true');svg.children.forEach((e,j)=>assert.deepEqual({...e.attrs,opacity:e.style.opacity},saved[i][j],story.states[i]+' node '+j));});
 global.matchMedia=()=>({matches:false,addEventListener(){}});
 // Time-resolved checks of the actual SVG, driven by the injected clock.
 story.enter('slope');story.finish();story.enter('secants');advance(300);assert.equal(+doc.querySelectorAll('.story-axis')[12].style.opacity,0);assert.equal(+doc.querySelector('.story-clean-slope').style.opacity,0);advance(300);assert.equal(+doc.querySelectorAll('.story-axis')[12].style.opacity,0);advance(500);assert.equal(svg.dataset.phase,'highlight');assert(+doc.querySelector('.story-zoom-box').getAttribute('width')>0);
 advance(300);assert.equal(svg.dataset.phase,'hold');advance(1000);assert.equal(svg.dataset.phase,'zoom-in');
 for(let j=0;j<8;j++){
  story.enter('secants');advance(3900+j*1200);assert.equal(svg.dataset.phase,'zoomed');assert.equal(+svg.dataset.pairStart,t.findIndex(v=>v>=2)+j);
  const leg=doc.querySelector('.story-triangle');assert(+leg.getAttribute('x2')-+leg.getAttribute('x1')>=80);assert.equal(+doc.querySelector('#c1-stage .measurement-dot').getAttribute('r'),8);assert.equal(doc.querySelectorAll('.story-leg-label').filter(e=>+e.style.opacity===1).length,2);
  assert.equal(doc.querySelectorAll('.story-delta').filter(e=>+e.style.opacity===1).length,2);
  assert.equal(doc.querySelector('.story-length').textContent,tr('x12_length',{n:1}));const a=t.findIndex(v=>v>=2)+j;assert.equal(doc.querySelector('.story-construction-readout').textContent,tr('x12c_slope',{value:fmt((x[a+1]-x[a])/(t[a+1]-t[a]))}));
  advance(350);assert.equal(+doc.querySelectorAll('.story-slope')[j].style.opacity+(+doc.querySelectorAll('.story-clipped')[j].style.opacity),1);
 }
 story.enter('noise-visible');advance(800);assert.equal(svg.dataset.phase,'zoom-in');advance(3100);assert.equal(svg.dataset.state,'noise-visible');
 for(const [j,length] of story.longerLengths.entries()){
  story.enter('windows');story.seek(3000+j*2400);assert.equal(+svg.dataset.windowLength,length);
  for(let k=0;k<=j;k++)assert(story.lengthClouds[k].dots.some(id=>+svg.children[id].style.opacity>0));
 }
 const optimum=m.D.A.reduce((sum,row,i)=>sum+row[0]*m.D.b[i],0)/m.D.A.reduce((sum,row)=>sum+row[0]**2,0);close(optimum,m.blocks.find(b=>b.term===0).coefficient);
 story.enter('fit');advance(2899);assert.equal(+doc.querySelector('.story-optimum-dot').style.opacity,0);
 advance(1);close(+svg.dataset.coefficient,optimum);close(+doc.querySelector('.story-optimum-dot').dataset.value,optimum);assert.equal(+doc.querySelector('.story-optimum-dot').style.opacity,1);
 advance(2000);close(+svg.dataset.coefficient,2*optimum);assert.equal(+doc.querySelector('.story-optimum').style.opacity,1);
 const optimumGeometry=doc.querySelector('.story-optimum').getAttribute('d');doc.getElementById('c1-c').value=0;doc.getElementById('c1-c').emit('input');assert.equal(doc.querySelector('.story-optimum').getAttribute('d'),optimumGeometry);
 story.enter('noise-estimate');story.seek(4000);close(+svg.dataset.error,1-m.blocks.find(b=>b.term===m.winner).gain);assert(doc.getElementById('c1-noise-result').hidden);assert.equal(doc.getElementById('c1-story-text-8').style.opacity,'.22');
 story.seek(story.noisePause+1800);assert.equal(+doc.querySelector('.story-cubic').style.opacity,1);assert.equal(doc.getElementById('c1-story-text-8').style.opacity,'1');
 for(const sample of [story.noisePause+2100,story.noisePause+2350,story.noisePause+7100]){
  story.seek(sample);assert(doc.querySelectorAll('.story-deviation').filter(e=>+e.style.opacity>0).length<=1);
 }
 story.seek(story.noisePause+1800);const dotBefore=+doc.querySelectorAll('.story-contribution').at(-1).getAttribute('cy');
 story.seek(story.noisePause+2300);assert(+doc.querySelectorAll('.story-contribution').at(-1).getAttribute('cy')>dotBefore);
 story.seek(story.noisePause+8000);assert(+svg.dataset.noiseSum>0&&+svg.dataset.noiseSum<m.floor);
 story.finish();close(+svg.dataset.noiseSum,m.floor);const sumWidth=+doc.querySelector('.story-part-0').getAttribute('width');
 story.enter('percent');story.finish();close(+doc.querySelector('.story-part-0').getAttribute('width'),sumWidth);
 story.enter('every');advance(2000);assert.equal(+doc.querySelector('.story-optimum-dot').style.opacity,1);advance(14000);assert.equal(svg.dataset.complete,'false');advance(900);assert.equal(svg.dataset.complete,'true');
 story.enter('slope');advance(1200);const before=doc.querySelector('.story-marker').getAttribute('cx');advance(1000);assert.notEqual(doc.querySelector('.story-marker').getAttribute('cx'),before);
 slides.nav.go(1);advance();for(const fn of events.wheel||[])fn({type:'wheel',target:doc.body,deltaY:500,preventDefault(){}});advance();assert.equal(slides.nav.index,2);
 for(const p of slides.pages.slice(2,13)){assert(p.querySelectorAll('p').every(n=>n.dataset.claim==='review'));assert.equal(p.querySelector('.eyebrow').textContent,tr('x10_eye',{i:p.querySelector('.eyebrow').dataset.c1Eye,n:11}));}
 // Chapter two: the same physical SVG continues into five pages.
 const two=WispChapterTwo,wm=two.model,constant=m.blocks.find(b=>b.term===0),joint=wm.blocks.find(b=>b.term===1),win=wm.blocks.find(b=>b.term===wm.winner);
 slides.nav.go(12);story.finish();const end=svg.children.map(e=>({...e.attrs,opacity:e.style.opacity}));
 slides.nav.go(13);assert.equal(doc.getElementById('masthead-title').textContent,tr('x13_chapter'));assert.equal(doc.getElementById('chapter-progress').getAttribute('aria-valuemax'),'5');
 // The first frame has exactly the preceding scene's geometry.
 svg.children.forEach((e,j)=>{for(const k of ['d','x','y','cx','cy','x1','y1','x2','y2','width','height'])if(end[j][k]!==undefined)assert.equal(e.attrs[k],end[j][k]);});
 const twoSaved=[];
 two.states.forEach((state,i)=>{
  slides.nav.go(13+i);story.finish();assert.strictEqual(story.svg,original);assert.equal(svg.dataset.state,state);assert.equal(svg.dataset.complete,'true');
  assert.equal(doc.querySelectorAll('.page-dots a').filter(a=>!a.hidden).length,5);
  assert.equal(slides.pages[13+i].querySelector('.eyebrow').textContent,tr('x10_eye',{i:i+1,n:5}));
  const coords=doc.querySelector('#c1-stage .story-prediction').getAttribute('d').match(/[-+]?(?:[0-9]*[.])?[0-9]+(?:e[-+]?[0-9]+)?/gi).map(Number);
  assert(coords.every(Number.isFinite));
  const shown=doc.querySelectorAll('#c1-stage .measurement-dot').filter(e=>+e.style.opacity===1);assert.equal(shown.length,m.rows.length);
  if(i===1){
   const sticks=doc.querySelectorAll('#c1-stage .story-residual').filter(e=>+e.style.opacity===1);assert.equal(sticks.length,two.slopeRows.length);
   sticks.forEach((e,j)=>close(+e.dataset.value,two.slopeRows[j].rate-constant.coefficient));
   const band=doc.querySelector('#c1-stage .story-band');assert.equal(+band.style.opacity,1);
   const b=band.getAttribute('d').match(/[-+]?(?:[0-9]*[.])?[0-9]+(?:e[-+]?[0-9]+)?/gi).map(Number);
   const r=two.slopeRows[0],w=m.rows[0].w;close(r.sd,Math.sqrt(story.variance[w[0]]+story.variance[w[1]])/(t[w[1]]-t[w[0]]));
   const scale=(+shown[1].getAttribute('cy')- +shown[0].getAttribute('cy'))/(two.slopeRows[1].rate-r.rate);close(b[1],+shown[0].getAttribute('cy')-scale*(r.rate-constant.coefficient-r.sd));
  }
  if(i===2){close(+svg.dataset.error,win.remaining);}
  if(i===2){const bars=doc.querySelectorAll('#c1-stage .c2-slot').filter(e=>+e.style.opacity===1);assert.equal(bars.length,5);bars.forEach((e,j)=>{assert.equal(+e.dataset.term,wm.blocks[j].term);close(+e.dataset.value,wm.blocks[j].share);assert.equal(e.classList.contains('winner'),wm.blocks[j].term===wm.winner);});}
  if(i>=3){close(+svg.dataset.error,win.remaining);close(+doc.querySelector('.story-part-0').getAttribute('width'),708*m.floor);}
  if(i===4){const eq=doc.querySelector('.story-equation').textContent;for(const c of wm.record.equations[0].coefficients)assert(eq.includes(secondNumber(Math.abs(c))));assert(!eq.includes('e-'));}
  twoSaved[i]=svg.children.map(e=>({...e.attrs,opacity:e.style.opacity}));
 });
 // Interrupted animations, catalogue order and both moving coefficients.
 story.enter('c2-joint');story.seek(2400);const midway=JSON.parse(svg.dataset.coefficients);midway.forEach((c,j)=>assert(c!==joint.coefficients[j]));assert(midway[0]!==constant.coefficient);
 story.seek(3900);JSON.parse(svg.dataset.coefficients).forEach((c,j)=>close(c,joint.coefficients[j]));story.seek(7899);assert.equal(+svg.dataset.term,joint.term);assert.equal(doc.getElementById('c2-text-3').style.opacity,'.22');
 story.seek(9500);assert.equal(doc.getElementById('c2-text-3').style.opacity,'1');
 story.remainingBlocks.forEach((b,j)=>{story.seek(story.jointPause+2900+j*2500);assert.equal(+svg.dataset.term,b.term);});
 story.seek(story.jointPause+story.sortAt-1);const catalogue=doc.querySelectorAll('.c2-slot').slice().sort((a,b)=>+a.getAttribute('y')-+b.getAttribute('y'));assert.deepEqual(catalogue.map(b=>+b.dataset.term),wm.blocks.map(b=>b.term));
 story.finish();const ranked=doc.querySelectorAll('.c2-slot').slice().sort((a,b)=>+a.getAttribute('y')-+b.getAttribute('y'));ranked.forEach((b,j)=>{if(j)assert(+b.dataset.value<=+ranked[j-1].dataset.value);});assert(ranked[0].classList.contains('winner'));
 for(let i=4;i>=0;i--){story.enter(two.states[i]);story.finish();svg.children.forEach((e,j)=>assert.deepEqual({...e.attrs,opacity:e.style.opacity},twoSaved[i][j]));}
 global.matchMedia=()=>({matches:true,addEventListener(){}});two.states.forEach((state,i)=>{story.enter(state);assert.equal(svg.dataset.complete,'true');svg.children.forEach((e,j)=>assert.deepEqual({...e.attrs,opacity:e.style.opacity},twoSaved[i][j]));});
 global.matchMedia=()=>({matches:false,addEventListener(){}});
 console.log('PASS X13: five bilingual pages, persistent SVG, joint coefficients, candidate order/shares, slope noise band, recorded equation, replay and reduced motion');
 if(fixture.language==='en')fs.writeFileSync(require('path').join(require('path').dirname(process.argv[3]),'x12c_story_numbers.json'),JSON.stringify({durations:story.durations,n:t.length,neighbourPairs:8,longDots:story.longRows.length,coefficient:optimum,rangeEnd:2*optimum,winnerError:1-m.blocks.find(b=>b.term===m.winner).gain,floor:m.floor,designWindows:m.D.windows.length},null,2));
 console.log('PASS X12: 11 bilingual states, real numeric geometry, keyboard-only walk, vertical wheel/keys, persistent SVG, sequence interruption/replay, reverse and reduced motion');process.exit(0);
}
// Execute the animation lifecycle, including delayed visibility and reduced motion.
const dish=doc.getElementById('dish-illustration');
assert.equal(dish.dataset.progress,'0');advance(1000);assert.equal(dish.dataset.progress,'0');
dishVisible([{isIntersecting:true}]);advance(3000);assert(+dish.dataset.progress>.49&&+dish.dataset.progress<.51);
const dots=()=>dish.querySelectorAll('.dish-cell').filter(n=>n.getAttribute('visibility')==='visible').length;
const middleDots=dots();advance(3100);assert.equal(dish.dataset.progress,'1');assert(dots()>middleDots);
const finalCurve=dish.querySelector('.dish-curve').getAttribute('d');
const positions=()=>dish.querySelectorAll('.dish-cell').map(n=>[n.getAttribute('cx'),n.getAttribute('cy')]);
const finalPositions=positions();advance(1600);assert(+dish.dataset.progress<.06,'loop clears and restarts after hold');
dishVisible([{isIntersecting:false}]);const paused=dish.dataset.progress;advance(10000);assert.equal(dish.dataset.progress,paused);
dishVisible([{isIntersecting:true}]);advance(1000);assert(+dish.dataset.progress>+paused);
doc.hidden=true;doc.emit('visibilitychange');const hiddenProgress=dish.dataset.progress;advance(10000);assert.equal(dish.dataset.progress,hiddenProgress);
doc.hidden=false;doc.emit('visibilitychange');advance(1000);assert(+dish.dataset.progress>+hiddenProgress);
assert(!doc.getElementById('dish-replay'));assert(!doc.querySelector('.hook-bridge'));
const media=global.matchMedia;global.matchMedia=()=>({matches:true,addEventListener(){}});dish.replaceChildren();initDish();
assert.equal(dish.dataset.progress,'1');assert.equal(dish.querySelector('.dish-curve').getAttribute('d'),finalCurve);assert.deepEqual(positions(),finalPositions);global.matchMedia=media;
// Tear down frames from the preceding isolated initializations.
frames.clear();
// Native-scroll fallback also pauses if IntersectionObserver is unavailable.
const savedObserver=global.IntersectionObserver;global.IntersectionObserver=undefined;
let fallbackTop=2000;dish.getBoundingClientRect=()=>({top:fallbackTop,bottom:fallbackTop+260});dish.replaceChildren();initDish();
assert.equal(dish.dataset.progress,'0');advance(1000);assert.equal(dish.dataset.progress,'0');
fallbackTop=0;events.scroll.forEach(fn=>fn());advance(1000);assert(+dish.dataset.progress>0);
fallbackTop=2000;events.scroll.forEach(fn=>fn());const fallbackPaused=dish.dataset.progress;advance(1000);assert.equal(dish.dataset.progress,fallbackPaused);
global.IntersectionObserver=savedObserver;
const table=fixture.data.live.i18n[fixture.language];
assert.equal(doc.getElementById('challenge-deck-start').textContent,table.x7_challenge_start.replace('{noise}',pct(fixture.data.live.teaching.sigma)));
for(const key of ['x7_structure_label','x7_parameter_label'])assert.equal(doc.querySelectorAll('[data-i18n="'+key+'"]').length,1);
for(const [id,key] of [['play-reset','x6_reset'],['challenge-hint','x6_hint']]){const button=doc.getElementById(id);assert.equal(button.getAttribute('aria-label'),table[key]);assert.equal(button.getAttribute('title'),table[key]);assert(button.querySelector('svg'));}
console.log('PASS X7b delayed visibility, six-second growth, hold and restart, page/tab pause, deterministic reduced-motion state, translated icon labels');
const slides=global.WispSlides;
assert.equal(slides.pages.length,19);assert.equal(slides.pages.at(-1).id,'p-glossary');
assert.equal(doc.querySelectorAll('#featured-stories > article').length,fixture.data.live.featured.length);
assert(doc.querySelectorAll('[data-claim]').length>=4);
function emit(type,target,extra={}){const event={type,target,preventDefault(){this.prevented=true;},...extra};for(const fn of events[type]||[])fn(event);return event;}
slides.nav.go(0);advance();emit('keydown',doc.body,{key:'PageDown'});assert.equal(slides.nav.index,1);assert.equal(location.hash,'#'+slides.pages[1].id);assert(location.href.includes('lang='+fixture.language));
advance();const slider=doc.getElementById('rate'),before=slides.nav.index;
emit('keydown',slider,{key:'ArrowDown'});doc.emit('pointerdown',{target:slider});emit('wheel',slider,{deltaY:100});assert.equal(slides.nav.index,before);emit('pointerup',doc.body);
advance();const weak=doc.getElementById('window-chart');doc.emit('pointerdown',{target:weak});emit('keydown',doc.body,{key:'PageDown'});assert.equal(slides.nav.index,before);emit('pointerup',doc.body);advance();
emit('keydown',doc.body,{key:'PageDown'});assert.equal(slides.nav.index,before+1);
for(let i=0;i<slides.pages.length;i++){
 slides.nav.go(i);const chapter=slides.pages[i].dataset.chapter;
 assert.equal(doc.getElementById('masthead-title').hash,'#'+slides.pages.find(p=>p.dataset.chapter===chapter).id);assert(!doc.getElementById('pipeline-bar'));
}
location.href='file:///wisp.html?lang=en#p-weak-intro';emit('popstate',doc.body);assert.equal(slides.pages[slides.nav.index].id,'p-weak-intro');
global.innerWidth=759;emit('resize',doc.body);assert(!html.classList.contains('snapped'));
console.log('PASS full app + slides DOM initialization, 19 pages, featured panels, navigation events, protected slider/window, history, highlights, resize fallback');
if(fixture.language==='en')fs.writeFileSync(require('path').join(require('path').dirname(process.argv[3]),'x3_page_inventory.json'),JSON.stringify(slides.pages.map(p=>({id:p.id,section:p.dataset.section,step:p.dataset.step,title:p.querySelector('h1,h2,h3').textContent,figures:p.querySelectorAll('[id]').map(e=>e.id)})),null,2));

// Headline selection is compared to the actual exported rates, including every count.
const expected=fixture.data.results.rates.filter(r=>['dim1','dim2'].includes(r.stratum)&&+r.sigma===.03&&r.rho!=='pooled'&&+r.rho===0&&['raw_exact','pruned_exact','generalization_arithmetic_hit','generalization_variance_weighted_hit'].includes(r.metric)&&((r.method===fixture.data.results.primary_method&&r.configuration==='c')||(['sindy','weak_sindy','e_sindy'].includes(r.method)&&r.configuration!=='all_ten')));
assert.deepEqual(WispPage.headline,expected);
assert.deepEqual(slides.pages.slice(0,4).map(p=>p.id),['p-hook','p-challenge','p-solution','p-headline']);
assert(!doc.getElementById('p-guess'));assert(!doc.querySelector('#p-catalogue #play-chart'));
for(const node of doc.body.querySelectorAll('*')){if(node.closest('script,style,[data-provenance],#provenance,dialog'))continue;assert(!/sys\d{4}_/.test(node._text),'identifier in reader text: '+node.id);}
assert.equal(new Set(slides.pages.map(p=>p.dataset.section)).size,slides.pages.length);
global.innerWidth=1366;emit('resize',doc.body);advance();
const more=doc.querySelector('[data-more]');more.emit('click');const modal=doc.querySelector('dialog[open]');assert(modal);const at=slides.nav.index;doc.emit('pointerdown',{target:slider});emit('wheel',modal,{deltaY:100});emit('pointerup',doc.body);emit('keydown',modal,{key:'PageDown'});assert.equal(slides.nav.index,at);modal.querySelector('[data-close]').emit('click');assert(!modal.open);
slides.nav.go(0);advance();emit('wheel',doc.body,{deltaY:100});assert.equal(slides.nav.index,1);
advance(320);for(let i=0;i<10;i++)emit('wheel',doc.body,{deltaY:40});assert.equal(slides.nav.index,1);advance();assert.equal(scrollY,innerHeight);
emit('keydown',doc.body,{key:'ArrowUp'});advance();assert.equal(scrollY,0);
slides.nav.go(1);advance();const y=scrollY;emit('keydown',doc.body,{key:'ArrowDown'});advance(320);
assert(scrollY>y&&scrollY<slides.pages[2].offsetTop,'intermediate vertical scrolling');advance();assert.equal(scrollY,slides.pages[2].offsetTop);
console.log('PASS X4 headline rows/counts, readable names, closed sections, modal guards, vertical steps, eased scrolling, one-gesture lock');

// Wheel hovering controls is navigation; only an active drag blocks it.
slides.nav.go(0);advance();emit('wheel',slider,{deltaY:100});assert.equal(slides.nav.index,1);
for(const node of doc.body.querySelectorAll('*')){if(node.closest('script,style,[data-provenance],#provenance'))continue;assert(!/raw_exact|pruned_exact|generalization_(?:arithmetic|variance_weighted)_hit|reconstruction_(?:arithmetic|variance_weighted)_hit/.test(node._text),'internal metric in reader text');assert(!/\uFFFD|[a-zA-ZäöüÄÖÜ]\?[a-zA-ZäöüÄÖÜ]/.test(node._text),'broken encoding in reader text: '+node._text);}
assert(doc.querySelectorAll('#headline-panel .rate-chart').length>=2);
assert.equal(doc.querySelectorAll('#p-test-intro [data-more]').length,1);
assert.equal(doc.querySelectorAll('#featured-stories > article').filter(a=>!a.hidden).length,1);
for(const metric of ['raw_exact','pruned_exact','generalization_arithmetic_hit','generalization_variance_weighted_hit']){
 const rows=fixture.data.results.rates.filter(r=>r.stratum==='dim1'&&r.metric===metric&&r.configuration!=='all_ten');const endpoints=rateEndpoints(rows);if(rows.length){assert.equal(+endpoints[0].rate,Math.min(...rows.map(r=>+r.rate)));assert.equal(+endpoints[1].rate,Math.max(...rows.map(r=>+r.rate)));assert(rows.includes(endpoints[0])&&rows.includes(endpoints[1]));}
}
console.log('PASS X5 chart endpoints/counts, reader metric labels, encoding, hover wheel and story switcher');

for(const article of doc.querySelectorAll('#featured-stories > article')){const pair=article.querySelector('.two-plots'),curves=panel=>panel.children.filter(curve=>curve.querySelector('svg.chart'));for(const panel of pair.children)assert.equal(curves(panel).filter(curve=>!curve.hidden).length,Math.min(1,curves(panel).length));const controls=article.querySelector('.component-tabs');if(controls){controls.children.at(-1).emit('click');for(const panel of pair.children){assert.equal(curves(panel).filter(curve=>!curve.hidden).length,Math.min(1,curves(panel).length));if(curves(panel).length)assert(!curves(panel).at(-1).hidden);}}}
console.log('PASS X5 one readable component per available featured reconstruction/generalization plot');

// WP-X6: execute the real challenge in each language against its exported measurements.
const challenge=doc.getElementById('p-challenge'),cards=doc.getElementById('term-cards').children;
assert.equal(cards.length,6);
const layout=()=>cards.map(c=>[c.className,c.children.map(n=>n.className),c.querySelectorAll('input').length]);
const originalLayout=layout();
assert(cards.every(c=>!c.querySelector('input').checked));
assert.equal(doc.getElementById('play-equation').dataset.tex,'\\frac{du}{dt}=0');

for(const card of cards){const check=card.querySelector('input');check.checked=!check.checked;check.emit('change');assert.deepEqual(layout(),originalLayout);const controls=card.querySelector('.coefficient-controls');assert(!controls.hidden);assert(controls.querySelectorAll('input,button').every(n=>n.disabled===!check.checked));check.checked=!check.checked;check.emit('change');}
const snapshot=()=>({equation:doc.getElementById('play-equation').dataset.tex,curve:doc.getElementById('play-chart').querySelector('path.series-model').getAttribute('d'),score:doc.getElementById('play-status').dataset.score});
const control=(index,type)=>cards[index].querySelectorAll('input').find(n=>n.type===type);
// WP-X7c: each coarse button uses its term scale; typed values retain fine precision.
for(const [i,step] of [0.1,0.1,0.001,0.0001,0.1,0.1].entries()){
 const check=control(i,'checkbox');check.checked=true;check.emit('change');
 const field=control(i,'number');field.value='0';field.emit('input');
 const buttons=cards[i].querySelectorAll('button');
 buttons.at(-1).emit('click');assert.equal(+field.value,step);assert.equal(String(field.value),String(step));
 buttons[0].emit('click');assert.equal(+field.value,0);
 for(let n=0;n<3;n++)buttons.at(-1).emit('click');assert.equal(String(field.value),String(+(3*step).toFixed(8)));
}
control(0,'number').value='0.300000123456';control(0,'number').emit('input');
assert.equal(coeff[0],0.300000123456);
control(0,'number').value='12.345678901';control(0,'number').emit('input');assert.equal(coeff[0],12.345678901);
doc.getElementById('play-reset').emit('click');
let previous=snapshot();control(2,'checkbox').checked=true;control(2,'checkbox').emit('change');
assert.notEqual(snapshot().equation,previous.equation);
const coefficient=control(2,'number');coefficient.value='-.01';coefficient.emit('input');
assert.notEqual(snapshot().curve,previous.curve);assert.notEqual(snapshot().score,previous.score);
assert.equal(+control(2,'range').value,-.01);
control(1,'checkbox').checked=true;control(1,'checkbox').emit('change');
previous=snapshot();const linear=control(1,'range');linear.value='.6';linear.emit('input');
assert.notEqual(snapshot().equation,previous.equation);assert.notEqual(snapshot().curve,previous.curve);assert.notEqual(snapshot().score,previous.score);
previous=snapshot();cards[1].querySelectorAll('button').at(-1).emit('click');assert.notEqual(snapshot().equation,previous.equation);
// Values are derived from the real exported illustration of this same logistic system.
const [growth,capacity]=fixture.data.live.illustrations[0].constants;
for(const [i,value] of [[1,growth],[2,-growth/capacity]]){const number=control(i,'number');assert.equal(number.step,'any');number.value=String(value);number.emit('input');}
assert(+snapshot().score>.98,'data-scale logistic answer is reachable');
previous=snapshot();control(2,'checkbox').checked=false;control(2,'checkbox').emit('change');
assert.notEqual(snapshot().equation,previous.equation);assert.notEqual(snapshot().curve,previous.curve);assert.notEqual(snapshot().score,previous.score);
control(2,'checkbox').checked=true;control(2,'checkbox').emit('change');
assert(Math.abs(+doc.getElementById('challenge-meter').value-Math.max(0,+snapshot().score))<1e-12);
const measurements=fixture.data.live.teaching;
assert.equal(doc.getElementById('play-chart').querySelectorAll('.measurement-dot').length,measurements.t.length);
const expectedCurve=rk4(measurements.t,[measurements.observed[0]],x=>[WispCompute.basis(x[0]).reduce((s,v,i)=>s+(enabled[i]?v*coeff[i]:0),0)]).map(x=>x[0]);
const mean=measurements.observed.reduce((a,b)=>a+b,0)/measurements.observed.length;
const expectedScore=1-expectedCurve.reduce((s,v,i)=>s+(v-measurements.observed[i])**2,0)/measurements.observed.reduce((s,v)=>s+(v-mean)**2,0);
assert(Math.abs(+snapshot().score-expectedScore)<1e-12);
for(let n=1;n<=4;n++){doc.getElementById('challenge-hint').emit('click');assert.equal(doc.getElementById('challenge-hints').children.length,Math.min(n,3));}
assert.deepEqual(doc.getElementById('challenge-hints').children.map(n=>n.textContent),[1,2,3].map(n=>fixture.data.live.i18n[fixture.language]['x6_hint'+n]));
const last=snapshot().equation;assert(!doc.getElementById('challenge-reveal'));slides.nav.go(1);advance();emit('wheel',doc.body,{deltaY:500});advance();
assert.equal(slides.pages[slides.nav.index].id,'p-solution');
doc.getElementById('play-reset').emit('click');assert.notEqual(snapshot().equation,last);
assert(cards.every(c=>!c.querySelector('input').checked));assert.equal(doc.getElementById('play-equation').dataset.tex,'\\frac{du}{dt}=0');
control(1,'checkbox').checked=true;control(1,'checkbox').emit('change');control(1,'number').value='2';control(1,'number').emit('input');assert(+snapshot().score<0||snapshot().score==='unavailable');
assert(doc.getElementById('play-status').textContent.length>0);
console.log('PASS X6 bilingual challenge, toggles, slider, typed and fine coefficients, measurement R2, reachable answer, ordered hints and divergence');

// WP-X8: the eye changes only the overlay; reset hides it.
doc.getElementById('play-reset').emit('click');
const beforeEye=snapshot(),beforeValues=coeff.slice(),beforeEnabled=enabled.slice();
const eye=doc.getElementById('challenge-solution');eye.emit('click');
assert.equal(eye.getAttribute('aria-label'),table.x8_hide);
assert(!doc.getElementById('challenge-truth').hidden);
assert(doc.querySelector('#play-chart .series-truth'));
assert(doc.getElementById('challenge-truth-equation').dataset.tex.includes(displayTruth(runningCell.truth[0]).replaceAll('u_{1}','u')));
assert.deepEqual(snapshot(),beforeEye);assert.deepEqual(coeff,beforeValues);assert.deepEqual(enabled,beforeEnabled);
assert.equal(doc.querySelectorAll('#play-chart path').at(-1).getAttribute('class').split(' ')[0],'series-model');
eye.emit('click');assert(!doc.querySelector('#play-chart .series-truth'));assert(doc.getElementById('challenge-truth').hidden);
eye.emit('click');doc.getElementById('play-reset').emit('click');assert(!doc.querySelector('#play-chart .series-truth'));assert.equal(eye.getAttribute('aria-label'),table.x8_show);


const solo=global.WispSolo,model=solo.model;
const close=(a,b)=>assert(Math.abs(a-b)<1e-10,`${a} != ${b}`);
const rows=doc.querySelectorAll('#solo-bars button');assert.equal(rows.length,6);
assert.deepEqual(model.blocks.map(b=>b.term),[0,1,2,3,5,4]);
assert.equal(model.winner,fixture.data.live.featured[0].path[0].active_idxs[0][0]-1);
assert.equal(rows.filter(b=>b.getAttribute('aria-pressed')==='true').length,1);
assert.equal(+rows.find(b=>b.getAttribute('aria-pressed')==='true').dataset.term,model.winner);
const savedChart=chart;let captured,capturedOptions;
chart=function(target,series,options){if(target.id==='solo-chart'){captured=series;capturedOptions=options;}return savedChart(target,series,options);};
const longest=Math.max(...model.D.windows.map(([a,b])=>b-a));
assert.equal(model.rows.length,Math.floor((measuredTime.length-1)/longest));
model.rows.forEach(({w},k)=>assert.deepEqual(w,[k*longest,(k+1)*longest]));
const savedChallenge=snapshot(),lines=new Set(),equations=new Set();
for(const [index,row] of rows.entries()){
 const block=model.blocks[index];close(+row.dataset.gain,block.gain);close(+row.dataset.share,block.share);
 assert.equal(row.children[2].textContent,(block.share*100).toLocaleString(language,{minimumFractionDigits:1,maximumFractionDigits:1})+' %');
 assert.equal(row.classList.contains('winner'),block.term===model.winner);
 close(parseFloat(row.querySelector('.solo-track').children[0].style.width),block.share*100);
 row.emit('click');assert.equal(row.getAttribute('aria-pressed'),'true');assert.equal(rows.filter(b=>b.getAttribute('aria-pressed')==='true').length,1);
 assert.equal(doc.getElementById('solo-equation').textContent,soloEquation(block));
 if(block.term===0)assert.equal(soloEquation(block),'du/dt = '+soloNumber(block.coefficient));
 assert(!/[eE][+-]\d|×/.test(soloEquation(block)));
 assert.deepEqual(captured[0].x,model.x);assert.deepEqual(captured[1].x,model.x);
 assert.equal(doc.querySelectorAll('#solo-chart .measurement-dot').length,model.rows.length);
 model.rows.forEach(({w,i},k)=>{close(model.x[k],(measuredTime[w[0]]+measuredTime[w[1]])/2);close(captured[0].y[k],model.D.b[i]);close(captured[1].y[k],block.coefficient*model.D.A[i][block.term]);});
 assert.deepEqual(capturedOptions.xDomain,[0,10]);assert.equal(capturedOptions.horizontalYLabel,true);
 const svg=doc.querySelector('#solo-chart svg'),labels=svg.querySelectorAll('text');
 assert.deepEqual(labels.filter(n=>n.getAttribute('y')==='287').map(n=>n.textContent),[0,2.5,5,7.5,10].map(v=>fmt(v)));
 const ylabel=labels.find(n=>n.textContent===tr('x9_change'));assert(ylabel);assert(!ylabel.getAttribute('transform'));assert.equal(ylabel.getAttribute('y'),'17');
 doc.querySelectorAll('#solo-chart .measurement-dot').forEach(n=>assert.equal(+n.getAttribute('r'),5.5));
 assert(doc.querySelector('.solo-legend').textContent.includes(tr('x9_prediction',{block:terms[block.term]})));
 lines.add(doc.querySelector('#solo-chart .series-model').getAttribute('d'));equations.add(soloEquation(block));
 assert.deepEqual(snapshot(),savedChallenge);
}
assert.equal(lines.size,6);assert.equal(equations.size,6);
const equationBefore=doc.getElementById('solo-equation').textContent;
global.katex={render(tex,target){assert.notEqual(target.id,'solo-equation');}};window.typesetAll();delete global.katex;
assert.equal(doc.getElementById('solo-equation').textContent,equationBefore);
const text=doc.getElementById('p-solution').textContent;
assert(!/\b(?:FoBa|FROLS|BIC|SSE|residual|Residual|Koeffizient|coefficient|least.squares|compressed|R\u00b2|support|threshold)\b/i.test(text));
const changed=JSON.parse(JSON.stringify(fixture.data.live.featured[0]));changed.path[0].active_idxs=[[2]];
assert.throws(()=>soloModel(teaching.observed,measuredTime,LIVE,changed),/differs from recorded/);
console.log('PASS X9a bilingual six bars, shares/order, all chart/equation switches, centres, constant, no jargon and frozen first support');
