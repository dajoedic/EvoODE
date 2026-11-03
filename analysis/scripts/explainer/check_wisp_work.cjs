/* Recorded teaching trace gate, usable by the assembler without a browser. */
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const base=path.resolve(process.argv[2]||'explainer/wisp');
const W=require(path.join(base,'src/compute.js'));
const source=fs.readFileSync(path.join(base,'src/app.js'),'utf8');
const core=fs.readFileSync(path.join(base,'src/compute.js'),'utf8');
const live=JSON.parse(fs.readFileSync(path.join(base,'data/live.json'),'utf8'));
const compression=core.slice(core.indexOf('  function compress('),core.indexOf('  function leastSquares(')).replace('function compress(','function workCompress(').replaceAll('dot(','workDot(');
assert(source.includes(compression),'Adapter compression must equal frozen compute.js');
const context={W,observationR2:(curve,y)=>{const mean=y.reduce((a,b)=>a+b)/y.length;return 1-curve.reduce((s,v,i)=>s+(v-y[i])**2,0)/y.reduce((s,v)=>s+(v-mean)**2,0);},teaching:live.teaching,measuredTime:live.teaching.t};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('const workDot='),source.indexOf('function initWork(){'))+'\nthis.trace=workTrace;this.score=workCurveR2;',context);
const records=context.trace(live.featured[0],live.teaching.observed,live.teaching.t,live);
const scores=records.map(r=>context.score(r.candidate.curves));
// Recompute gains/costs independently on the full, normalized design.
const D=W.design(live.teaching.t,live.teaching.observed,live.windows),norm=D.b.reduce((s,v)=>s+v*v,0);
const scales=D.A[0].map((_,j)=>Math.sqrt(D.A.reduce((s,row)=>s+row[j]**2,0)));
const sse=s=>W.leastSquares(D.A.map(row=>s.map(j=>row[j]/scales[j])),D.b).sse;
const close=(a,b)=>assert(Math.abs(a-b)<1e-10,`${a} != ${b}`);
for(const r of records){
 assert(r.candidate,'Each recorded stage needs its exported fitted candidate');
 assert.deepEqual(JSON.parse(r.candidate.row.active_idxs)[0].map(j=>j-1),Array.from(r.step.support));
 close(r.remainingBefore,sse(r.previous)/norm);
 const variance=W.noiseVariance(live.teaching.t,live.teaching.observed);
 close(r.floorBefore,W.noiseFloor(D,Array.from(r.previous),variance)/norm);
 close(r.floorAdded,W.noiseFloor(D,Array.from(r.added),variance)/norm);
 close(r.floorAfter,W.noiseFloor(D,Array.from(r.step.support),variance)/norm);
 for(const g of r.step.gains)close(g.gain,(sse(r.previous)-sse([...r.previous,g.term].sort((a,b)=>a-b)))/norm);
 for(const check of r.checks){
  for(const c of check.costs)close(c.cost,(sse(check.support.filter(j=>j!==c.term))-sse(check.support))/norm);
  const out=check.costs.filter(c=>c.cost<r.threshold).sort((a,b)=>a.cost-b.cost||a.term-b.term)[0];assert.equal(check.out,out?.term??null);
 }
}
const report={steps:records.map((r,i)=>({stage:i+1,remaining_before:r.remainingBefore,remaining_after:r.step.remaining,floor_before:r.floorBefore,floor_added:r.floorAdded,floor_after:r.floorAfter,gains:r.step.gains,threshold:r.threshold,checks:r.checks,support:r.step.support,score:scores[i]})),chosen:live.featured[0].chosen};
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(report,null,2)+'\n');
console.log('PASS recorded supports, 8 stages, compressed/full-design gains and removal costs, repeated removal decisions');
