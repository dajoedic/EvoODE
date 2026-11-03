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
global.document=doc;global.window=global;global.innerWidth=1366;global.innerHeight=657;
global.location={href:'file:///wisp.html?lang='+fixture.language,get hash(){return new URL(this.href).hash;},assign(url){this.href=String(url);}};
global.history={pushState(_,__,url){location.href=String(url);},replaceState(_,__,url){location.href=String(url);}};
global.localStorage={getItem(){return null;},setItem(){}};global.matchMedia=()=>({matches:false,addEventListener(){}});
let now=0,frameId=0;const frames=new Map();global.performance={now:()=>now};global.scrollY=0;global.scrollTo=(_,y)=>{global.scrollY=y;};global.requestAnimationFrame=fn=>{frames.set(++frameId,fn);return frameId;};global.cancelAnimationFrame=id=>frames.delete(id);function advance(ms=800){const end=now+ms;while(now<end){now+=16;const queue=[...frames.values()];frames.clear();queue.forEach(fn=>fn(now));}}
const events={};global.addEventListener=(k,fn)=>(events[k]??=[]).push(fn);global.WispCompute=require(base+'/src/compute.js');
let dishVisible;global.IntersectionObserver=class{constructor(fn){dishVisible=fn;}observe(){}disconnect(){}};
vm.runInThisContext(fs.readFileSync(base+'/src/app.js','utf8'),{filename:'app.js'});
vm.runInThisContext(fs.readFileSync(base+'/src/pages.js','utf8'),{filename:'pages.js'});
// Execute the animation lifecycle, including delayed visibility and reduced motion.
const dish=doc.getElementById('dish-illustration');
assert.equal(dish.dataset.progress,'0');advance(1000);assert.equal(dish.dataset.progress,'0');
dishVisible([{isIntersecting:true}]);advance(3000);assert(+dish.dataset.progress>.49&&+dish.dataset.progress<.51);
const dots=()=>dish.querySelectorAll('.dish-cell').filter(n=>n.getAttribute('visibility')==='visible').length;
const middleDots=dots();advance(3100);assert.equal(dish.dataset.progress,'1');assert(dots()>middleDots);
const finalCurve=dish.querySelector('.dish-curve').getAttribute('d');
const positions=()=>dish.querySelectorAll('.dish-cell').map(n=>[n.getAttribute('cx'),n.getAttribute('cy')]);
const finalPositions=positions();doc.getElementById('dish-replay').emit('click');advance(6100);
assert.equal(dish.querySelector('.dish-curve').getAttribute('d'),finalCurve);assert.deepEqual(positions(),finalPositions);
const media=global.matchMedia;global.matchMedia=()=>({matches:true,addEventListener(){}});dish.replaceChildren();initDish();
assert.equal(dish.dataset.progress,'1');assert.equal(dish.querySelector('.dish-curve').getAttribute('d'),finalCurve);assert.deepEqual(positions(),finalPositions);global.matchMedia=media;
const table=fixture.data.live.i18n[fixture.language];
assert.equal(doc.getElementById('challenge-deck-start').textContent,table.x7_challenge_start.replace('{noise}',pct(fixture.data.live.teaching.sigma)));
for(const card of doc.getElementById('term-cards').children){assert.equal(card.querySelector('.part-label').textContent,table.x7_structure_label);assert.equal(card.querySelector('.coefficient-controls .part-label').textContent,table.x7_parameter_label);}
console.log('PASS X7 delayed visibility, six-second animation, replay determinism, reduced-motion final state, data-derived noise and labels');
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
 slides.nav.go(i);const active=doc.querySelectorAll('#pipeline-bar .current');const step=slides.pages[i].dataset.step;
 assert.deepEqual(active.map(a=>a.dataset.step),step?[step]:[]);
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
slides.nav.go(0);advance();const y=scrollY;emit('wheel',doc.body,{deltaY:100});assert.equal(slides.nav.index,1);advance(320);assert(scrollY>y&&scrollY<innerHeight,'intermediate eased scrolling');for(let i=0;i<10;i++)emit('wheel',doc.body,{deltaY:40});assert.equal(slides.nav.index,1);advance();assert.equal(scrollY,innerHeight);
console.log('PASS X4 headline rows/counts, readable names, closed sections, modal guards, eased one-gesture scrolling');

// Wheel hovering controls is navigation; only an active drag blocks it.
slides.nav.go(0);advance();emit('wheel',slider,{deltaY:100});assert.equal(slides.nav.index,1);
for(const node of doc.body.querySelectorAll('*')){if(node.closest('script,style,[data-provenance],#provenance'))continue;assert(!/raw_exact|pruned_exact|generalization_(?:arithmetic|variance_weighted)_hit|reconstruction_(?:arithmetic|variance_weighted)_hit/.test(node._text),'internal metric in reader text');assert(!/\uFFFD|[a-zA-ZäöüÄÖÜ]\?[a-zA-ZäöüÄÖÜ]/.test(node._text),'broken encoding in reader text');}
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
const snapshot=()=>({equation:doc.getElementById('play-equation').dataset.tex,curve:doc.getElementById('play-chart').querySelector('path.series-model').getAttribute('d'),score:doc.getElementById('play-status').dataset.score});
const control=(index,type)=>cards[index].querySelectorAll('input').find(n=>n.type===type);
let previous=snapshot();control(2,'checkbox').checked=true;control(2,'checkbox').emit('change');
assert.notEqual(snapshot().equation,previous.equation);
const coefficient=control(2,'number');coefficient.value='-.01';coefficient.emit('input');
assert.notEqual(snapshot().curve,previous.curve);assert.notEqual(snapshot().score,previous.score);
assert.equal(+control(2,'range').value,-.01);
previous=snapshot();const linear=control(1,'range');linear.value='.6';linear.emit('input');
assert.notEqual(snapshot().equation,previous.equation);assert.notEqual(snapshot().curve,previous.curve);assert.notEqual(snapshot().score,previous.score);
previous=snapshot();cards[1].querySelectorAll('button').at(-1).emit('click');assert.notEqual(snapshot().equation,previous.equation);
// Values are derived from the real exported illustration of this same logistic system.
const [growth,capacity]=fixture.data.live.illustrations[0].constants;
for(const [i,value] of [[1,growth],[2,-growth/capacity]]){const number=control(i,'number');assert(+number.min<=value&&+number.max>=value);number.value=String(value);number.emit('input');}
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
const last=snapshot().equation,link=doc.getElementById('challenge-reveal');doc.emit('click',{target:link,preventDefault(){}});advance();
assert.equal(slides.pages[slides.nav.index].id,'p-solution');assert.equal(doc.getElementById('reader-equation').dataset.tex,last);
doc.getElementById('play-reset').emit('click');assert.notEqual(snapshot().equation,last);
control(1,'number').value='2';control(1,'number').emit('input');assert(+snapshot().score<0||snapshot().score==='unavailable');
assert(doc.getElementById('play-status').textContent.length>0);
console.log('PASS X6 bilingual challenge, toggles, slider, typed and fine coefficients, measurement R2, reachable answer, ordered hints, reveal equation and divergence');
