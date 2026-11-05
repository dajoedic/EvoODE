/* Geometry-only scene checks. Actual browser text bounds remain the fit checker's job. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const base=path.resolve(__dirname,'../../../explainer/wisp');
const source=fs.readFileSync(path.join(base,'src/app.js'),'utf8');
const core=fs.readFileSync(path.join(base,'src/compute.js'),'utf8');
const live=JSON.parse(fs.readFileSync(path.join(base,'data/live.json'),'utf8'));
const W=require(path.join(base,'src/compute.js'));
const context={W,console};vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function numberText('),source.indexOf('const fmt='))+source.slice(source.indexOf('function thresholdNumber('),source.indexOf('function secondEquation(')),context);
vm.runInContext(source.slice(source.indexOf('const soloDot='),source.indexOf('function soloNumber('))+source.slice(source.indexOf('function secondModel('),source.indexOf('function secondNumber(')),context);
for(const language of ['de','en']){
 const strings=JSON.parse(fs.readFileSync(path.join(base,`src/i18n/${language}.json`),'utf8'));
 Object.assign(context,{live,language,strings});
 vm.runInContext(`
 var m=soloModel(live.teaching.observed,live.teaching.t,live,live.featured[0]);
 var three=thirdModel(m,live.teaching.t,live.teaching.observed,live,live.featured[0]);
 var four=fourthModel(m,live.teaching.t,live.teaching.observed,live,live.featured[0],three);
 var terms=['1','u','u²','u³','sin u','cos u'],durations={},nodes=[],blank=[];
 var caption={style:{}},svg={dataset:{}},ease=v=>{v=Math.max(0,Math.min(1,v));return v*v*(3-2*v);};
 var tr=(key,args={})=>Object.entries(args).reduce((s,[k,v])=>s.replaceAll('{'+k+'}',String(v)),strings[key]);
 var node=(tag,attrs,geometry,initial)=>{nodes.push({geometry,e:{textContent:'',dataset:{},attrs:{...attrs},classList:{toggle(){}},setAttribute(k,v){this.attrs[k]=v;}}});blank.push(initial);return nodes.length-1;};
 var line=cls=>node('line',{class:cls},'line',[0,0,0,0,0]);
 var label=cls=>node('text',{class:cls},'text',[0,0,0]);
 `,context);
 // Each language gets a fresh lexical scope for the mounted scene nodes.
 vm.runInContext('{'+source.slice(source.indexOf(' // Chapter four uses'),source.indexOf(' // Chapter two shares'))+`
 this.scene=fourthScene;this.plots=c4Plots;this.chips=c4Chips;
 }`,context);
 const scene=(state,time)=>context.scene(state,time);
 for(const [state,duration] of Object.entries(context.durations)){
  const end=JSON.stringify(scene(state,duration));
  scene('c4-noise',1300);scene('c4-replay',35500);
  assert.equal(JSON.stringify(scene(state,duration)),end,'History-dependent geometry');
  for(const time of [0,600,1200,duration]){
   const geometry=scene(state,time);
   assert.equal(geometry.length,context.nodes.length);
   geometry.forEach((g,i)=>{assert(g.every(Number.isFinite),state+' non-finite');if(context.nodes[i].geometry==='rect')assert(g[2]>=0&&g[3]>=0);});
  }
 }
 // Inspect visible model chips, rather than trusting only the support dataset.
 const visibleChips=geometry=>Array.from(context.chips).flatMap(row=>Array.from(row).flatMap((chip,term)=>geometry[chip.box][4]>.01?[term]:[]));
 for(let round=0;round<5;round++){
  for(let time=0;time<3000;time+=137){
   const g=scene('c4-replay',round*12000+time);
   assert.deepEqual(visibleChips(g),Array.from(context.four.rounds[round].support));
   if(round===0)assert(context.nodes.some((n,i)=>n.e.textContent===strings.x18_empty&&g[i].at(-1)>0));
  }
  if(round<4)for(const time of [3000,4999]){
   const g=scene('c4-replay',round*12000+time),right=context.plots[1];
   assert(g[right.axes[1]][4]!==1,'Clean-up probe must wait until the clean-up phase');
  }
  if(round<4)for(const time of [5000,7000,8500,11500]){
   const g=scene('c4-replay',round*12000+time),right=context.plots[1];
   assert(g[right.axes[1]][4]===1,'Clean-up probe must be visible in the clean-up phase');
   assert(Array.from(right.bars).some(b=>g[b.bar][4]===1));
   assert(g[right.limit][4]===1);
  }
  for(const phase of [0,2999,3000,4999,5000,8499,8500,11500,11999]){
   scene('c4-replay',round*12000+phase);
   assert.equal(context.svg.dataset.round,String(round+1));
   assert.equal(context.svg.dataset.phase,round===4?'end':phase<3000?'test':phase<5000?'add':'cleanup');
  }
 }
 let geometry=scene('c4-replay',35500);
 assert.equal(context.svg.dataset.probeSupport,'[1,3]');
 geometry=scene('c4-replay',47500);
 assert.equal(context.svg.dataset.support,'[1,2]');
 scene('c4-replay',60000);
 assert.equal(context.svg.dataset.phase,'end');
 // Mirrored plots have the same axis dimensions; their thresholds differ in meaning.
 geometry=scene('c4-replay',35000);
 const [left,right]=Array.from(context.plots);
 const a=geometry[left.axes[1]],b=geometry[right.axes[1]];
 assert.equal(a[2]-a[0],b[2]-b[0]);assert.equal(a[3],b[3]);
 assert(context.nodes[left.zoom.axis].e.dataset.magnified==='false');
 assert.equal(geometry[left.zoom.axis].at(-1),0);
 const close=(a,b)=>assert(Math.abs(a-b)<1e-9,`${a} != ${b}`);
 for(let round=0;round<5;round++){
  geometry=scene('c4-replay',round*12000+1500);
  assert.equal(context.nodes[left.axes[0]].e.dataset.scale,'log10');
  const ticks=Array.from(left.ticks).filter(t=>geometry[t.text][2]>0);
  assert.deepEqual(ticks.map(t=>+context.nodes[t.line].e.dataset.value),[.01,.1,1,10,100,1000,10000]);
  ticks.forEach((t,i)=>close(geometry[t.line][1],278-98*i/6));
  close(geometry[left.limit][1],278-98*(Math.log10(context.four.threshold)+2)/6);
  assert.equal(context.nodes[left.limitText].e.textContent,strings.x18_limit.replace('{value}',language==='de'?'6,635':'6.635'));
  context.nodes.forEach((n,i)=>{if(geometry[i].at(-1)>.01)assert(!/\d(?:[.,]\d+)?e[+-]?\d/i.test(n.e.textContent));});
 }
 geometry=scene('c4-replay',35000);
 assert(context.nodes[right.zoom.axis].e.dataset.magnified==='true');
 console.log('PASS '+language+' scene topology, finite geometry, deterministic seek, round phases, removals logarithmic ticks/threshold, model order and clean-up probes');
}
