/* Gate the first single-block step against the actual recorded teaching run. */
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const base=path.resolve(process.argv[2]||'explainer/wisp');
const W=require(path.join(base,'src/compute.js'));
const source=fs.readFileSync(path.join(base,'src/app.js'),'utf8');
const core=fs.readFileSync(path.join(base,'src/compute.js'),'utf8');
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
const report={winner:model.winner,coefficient:model.blocks[0].coefficient,floor:model.floor,normalized:model.normalized,blocks:model.blocks,windows:model.rows.length};
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(report,null,2)+'\n');
console.log('PASS six single-block fits, full-design gains/coefficients, noise floor and recorded first support');
