/* Numerical core shared verbatim by Node checks and the browser. */
(function (root) {
  'use strict';
  const dot = (a,b) => a.reduce((s,v,i)=>s+v*b[i],0);
  const basis = x => [1,x,x*x,x*x*x,Math.sin(x),Math.cos(x)];
  function design(t,x,lengths=[1,2,4,8,16]) {
    const phi=x.map(basis), A=[], b=[], windows=[];
    for (const length of lengths) for(let start=0;start<t.length-length;start++) {
      const end=start+length, row=Array(6).fill(0);
      for(let k=start;k<end;k++) for(let j=0;j<6;j++)
        row[j]+=(t[k+1]-t[k])*(phi[k][j]+phi[k+1][j])/2;
      A.push(row); b.push(x[end]-x[start]); windows.push([start,end]);
    }
    return {A,b,phi,windows};
  }
  function compress(A,b) {
    const p=A[0].length, norms=Array.from({length:p},(_,j)=>Math.sqrt(dot(A.map(r=>r[j]),A.map(r=>r[j]))));
    const M=A.map((r,i)=>[...r.map((v,j)=>v/(norms[j]||1)),b[i]]);
    // Householder augmented QR avoids subtracting nearly equal residual norms.
    for(let k=0;k<Math.min(M.length,p+1);k++) {
      const v=M.slice(k).map(r=>r[k]), n=Math.sqrt(dot(v,v));
      if(!n) continue;
      v[0]+=(v[0]>=0?1:-1)*n;
      const vv=dot(v,v);
      for(let j=k;j<=p;j++) {
        let s=0; for(let i=0;i<v.length;i++) s+=v[i]*M[i+k][j];
        s=2*s/vv; for(let i=0;i<v.length;i++) M[i+k][j]-=s*v[i];
      }
    }
    return {A:M.slice(0,p+1).map(r=>r.slice(0,p)),b:M.slice(0,p+1).map(r=>r[p]),norms};
  }
  function leastSquares(A,b) {
    const n=A[0]?.length||0;
    if(!n) return {coefficients:[],sse:dot(b,b)};
    const cols=Array.from({length:n},(_,j)=>A.map(r=>r[j]));
    const V=Array.from({length:n},(_,j)=>Array.from({length:n},(_,i)=>+(i===j)));
    // One-sided Jacobi SVD; never form the normal equations.
    for(let sweep=0;sweep<100;sweep++) {
      let changed=false;
      for(let j=0;j<n;j++) for(let k=j+1;k<n;k++) {
        const a=dot(cols[j],cols[j]), d=dot(cols[k],cols[k]), c=dot(cols[j],cols[k]);
        if(!a||!d||Math.abs(c)<=Number.EPSILON*Math.sqrt(a*d)*2) continue;
        changed=true;
        const z=(d-a)/(2*c), tan=(z>=0?1:-1)/(Math.abs(z)+Math.sqrt(1+z*z));
        const cs=1/Math.sqrt(1+tan*tan), sn=cs*tan;
        for(const arr of [cols,V]) {
          const u=arr[j].slice(), v=arr[k].slice();
          arr[j]=u.map((x,i)=>cs*x-sn*v[i]); arr[k]=u.map((x,i)=>sn*x+cs*v[i]);
        }
      }
      if(!changed) break;
    }
    const norms=cols.map(c=>Math.sqrt(dot(c,c))), cutoff=Math.max(...norms)*Number.EPSILON*Math.max(A.length,n);
    const coefficients=Array(n).fill(0);
    cols.forEach((c,j)=>{if(norms[j]>cutoff) {const f=dot(c,b)/(norms[j]*norms[j]); V[j].forEach((v,i)=>coefficients[i]+=v*f);}});
    const residual=b.map((v,i)=>v-dot(A[i],coefficients));
    return {coefficients,sse:dot(residual,residual)};
  }
  function path(t,x,config={}) {
    const D=design(t,x,config.windows), C=compress(D.A,D.b), norm=dot(D.b,D.b), cache=new Map();
    const fit=s=>{const key=s.join(','); if(!cache.has(key)) {
      const f=leastSquares(C.A.map(r=>s.map(j=>r[j])),C.b);
      cache.set(key,{sse:f.sse,coefficients:f.coefficients.map((v,i)=>v/(C.norms[s[i]]||1))});
    } return cache.get(key);};
    let active=[]; const steps=[],seen=new Set();
    while(active.length<(config.cap||6) && norm && fit(active).sse/norm>=(config.sse_stop||1e-14)) {
      const gains=Array.from({length:6},(_,i)=>i).filter(i=>!active.includes(i)).map(i=>({term:i,gain:(fit(active).sse-fit([...active,i].sort((a,b)=>a-b)).sse)/norm}));
      gains.sort((a,b)=>b.gain-a.gain||a.term-b.term);
      if(!gains.length) break;
      if(config.significance){
        const base=noiseFloor(D,active,config.variance);
        const significant=gains.some(g=>{const noise=base-noiseFloor(D,[...active,g.term].sort((a,b)=>a-b),config.variance);return noise<=0||g.gain*norm/noise>=config.threshold;});
        if(!significant)break;
      }
      const winner=gains[0]; if(winner.gain<=0){if(config.significance)break;throw Error('No positive gain before protocol stop');}
      active=[...active,winner.term].sort((a,b)=>a-b);
      const removed=[];
      while(true) {
        const costs=active.map(i=>({term:i,cost:(fit(active.filter(j=>j!==i)).sse-fit(active).sse)/norm})).filter(a=>a.cost<(config.backward_fraction||0.5)*winner.gain).sort((a,b)=>a.cost-b.cost||a.term-b.term);
        if(!costs.length) break;
        removed.push(costs[0].term); active=active.filter(i=>i!==costs[0].term);
      }
      const key=active.join(','); if(seen.has(key)){if(config.significance)break;throw Error('Repeated FoBa model');} seen.add(key);
      steps.push({support:active.slice(),addition:winner.term,removed,gains,coefficients:fit(active).coefficients,sse:fit(active).sse,remaining:fit(active).sse/norm});
    }
    return {steps,design:D};
  }
  function orthogonal(columns){
    const Q=[];
    for(const col of columns){let v=col.slice(),norm=Math.sqrt(dot(v,v));if(!norm)continue;v=v.map(x=>x/norm);
      for(let pass=0;pass<2;pass++)for(const q of Q){const d=dot(q,v);v=v.map((x,i)=>x-d*q[i]);}
      const length=Math.sqrt(dot(v,v));if(length>Number.EPSILON*col.length*4)Q.push(v.map(x=>x/length));
    }return Q;
  }
  function noiseVariance(t,x){
    const squares=t.map((_,i)=>{
      const start=Math.min(Math.max(i-4,0),t.length-9),z=t.slice(start,start+9).map(v=>v-t[i]),scale=Math.max(...z.map(Math.abs));
      const Q=orthogonal([0,1,2,3].map(p=>z.map(v=>(v/scale)**p))),local=x.slice(start,start+9),j=i-start;
      const prediction=Q.reduce((sum,q)=>sum+q[j]*dot(q,local),0),h=Q.reduce((sum,q)=>sum+q[j]**2,0);
      return (x[i]-prediction)**2/(1-h);
    });
    const prefix=[0];squares.forEach(v=>prefix.push(prefix.at(-1)+v));
    return t.map((_,i)=>{const lo=Math.max(i-10,0),hi=Math.min(i+11,t.length);return (prefix[hi]-prefix[lo])/(hi-lo);});
  }
  function noiseFloor(D,support,variance){
    let total=D.windows.reduce((sum,[a,b])=>sum+variance[a]+variance[b],0);
    const Q=orthogonal(support.map(j=>D.A.map(row=>row[j])));
    for(const q of Q){const projected=variance.map(()=>0);D.windows.forEach(([a,b],i)=>{projected[a]-=q[i];projected[b]+=q[i];});total-=projected.reduce((sum,v,i)=>sum+v*v*variance[i],0);}
    return Math.max(0,total);
  }
  function significancePath(t,x,threshold=6.635){const variance=noiseVariance(t,x);return {...path(t,x,{significance:true,variance,threshold}),variance};}
  root.WispCompute={basis,design,path,leastSquares,noiseVariance,noiseFloor,significancePath};
  if(typeof module!=='undefined') module.exports=root.WispCompute;
})(typeof globalThis==='undefined'?window:globalThis);
