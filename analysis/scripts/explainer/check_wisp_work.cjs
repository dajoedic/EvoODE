/* Gate the first single-block step against the actual recorded teaching run. */
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const base=path.resolve(process.argv[2]||'explainer/wisp');
const W=require(path.join(base,'src/compute.js'));
const source=fs.readFileSync(path.join(base,'src/app.js'),'utf8').replaceAll('\r\n','\n');
const core=fs.readFileSync(path.join(base,'src/compute.js'),'utf8').replaceAll('\r\n','\n');
const live=JSON.parse(fs.readFileSync(path.join(base,'data/live.json'),'utf8'));
const compression=core.slice(core.indexOf('  function compress('),core.indexOf('  function leastSquares(')).replace('function compress(','function soloCompress(').replaceAll('dot(','soloDot(');
assert(source.includes(compression),'Adapter compression must equal frozen compute.js');
const context={W};vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('const soloDot='),source.indexOf('function soloNumber('))+'\nthis.model=soloModel;',context);
const model=context.model(live.teaching.observed,live.teaching.t,live,live.featured[0]);
const close=(a,b)=>assert(Math.abs(a-b)<1e-10,`${a} != ${b}`);
const D=model.D,norm=D.b.reduce((s,v)=>s+v*v,0);
assert.equal(model.blocks.length,6);assert.equal(model.winner,live.featured[0].path[0].active_idxs[0][0]-1);
for(const block of model.blocks){
 const fit=W.leastSquares(D.A.map(row=>[row[block.term]]),D.b);
 close(block.gain,(norm-fit.sse)/norm);close(block.coefficient,fit.coefficients[0]);
 close(block.share,block.gain/model.explainable);
}
close(model.floor,W.noiseFloor(D,[],W.noiseVariance(live.teaching.t,live.teaching.observed))/norm);
vm.runInContext(source.slice(source.indexOf('function secondModel('),source.indexOf('function secondNumber('))+'\nthis.second=secondModel;',context);
const second=context.second(model,live.teaching.t,live.teaching.observed,live,live.featured[0]);
assert.equal(second.blocks.length,5);
for(const block of second.blocks){
 const fit=W.leastSquares(D.A.map(row=>block.support.map(j=>row[j])),D.b);
 block.coefficients.forEach((v,j)=>close(v,fit.coefficients[j]));
 close(block.remaining,fit.sse/norm);close(block.gain,1-model.blocks.find(b=>b.term===0).gain-fit.sse/norm);
 close(block.share,(1-fit.sse/norm)/model.explainable);
}
const changed=JSON.parse(JSON.stringify(live.featured[0]));changed.path[1].active_idxs[0]=[1,2];
assert.throws(()=>context.second(model,live.teaching.t,live.teaching.observed,live,changed),/step-2/);
const report={winner:model.winner,coefficient:model.blocks[0].coefficient,floor:model.floor,normalized:model.normalized,blocks:model.blocks,windows:model.rows.length,second};
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(report,null,2)+'\n');
console.log('PASS six single-block fits, full-design gains/coefficients, noise floor and recorded first support');
console.log('PASS five joint refits, full-design gains/shares/coefficients and step-2 support guard');

vm.runInContext(source.slice(source.indexOf('function thirdModel('),source.indexOf('function secondNumber('))+'\nthis.third=thirdModel;',context);
const third=context.third(model,live.teaching.t,live.teaching.observed,live,live.featured[0]);
assert.deepEqual(Array.from(third.truth),live.featured[0].truth_support[0].map(j=>j-1));
const broken=JSON.parse(JSON.stringify(live.featured[0]));broken.path[2].active_idxs[0]=[1,2];
assert.throws(()=>context.third(model,live.teaching.t,live.teaching.observed,live,broken),/FoBa path/);
const wrongTruth=JSON.parse(JSON.stringify(live.featured[0]));wrongTruth.truth_support=[[1]];
assert.throws(()=>context.third(model,live.teaching.t,live.teaching.observed,live,wrongTruth),/FoBa truth/);
console.log('PASS four live FoBa supports, repeated removal probes and truth guard');
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify({...report,third},null,2)+'\n');

vm.runInContext(source.slice(source.indexOf('function fourthModel('),source.indexOf('function secondNumber('))+'\nthis.fourth=fourthModel;',context);
const fourth=context.fourth(model,live.teaching.t,live.teaching.observed,live,live.featured[0],third);
assert.deepEqual(JSON.parse(JSON.stringify(fourth.supports)),live.featured[0].stop_reference.supports);
assert.deepEqual(Array.from(fourth.rounds,r=>r.passes),[true,true,true,true,false]);
const wrongStop=JSON.parse(JSON.stringify(live.featured[0]));wrongStop.stop_reference.stop_step++;
assert.throws(()=>context.fourth(model,live.teaching.t,live.teaching.observed,live,wrongStop,third),/stop reference/);
console.log('PASS live significance supports, stop count, first four FoBa supports and fifth-round failure');
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify({...report,third,fourth},null,2)+'\n');
