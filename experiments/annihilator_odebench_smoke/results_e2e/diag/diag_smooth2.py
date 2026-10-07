import numpy as np
from scipy.interpolate import make_smoothing_spline
from experiments.annihilator_odebench_smoke import end2end as E
from experiments.annihilator_odebench_smoke.catalog import load_systems
S=load_systems(); rel=lambda a,b: np.sqrt(np.mean((a-b)**2))/np.sqrt(np.mean(b**2))
def binned_smooth(X,F,points=2000,nb=200):
    edges=np.linspace(X.min(),X.max(),nb+1); k=np.clip(np.digitize(X,edges)-1,0,nb-1)
    cnt=np.bincount(k,minlength=nb); m=cnt>0
    xb=np.bincount(k,X,nb)[m]/cnt[m]; fb=np.bincount(k,F,nb)[m]/cnt[m]
    g=np.linspace(X.min(),X.max(),points)
    return g, make_smoothing_spline(xb,fb,w=cnt[m].astype(float))(g)
for sid in (3,7,19,21):
    s=S[sid]
    for eta in (0.0,0.01):
      for prot,idx in (("P1_AB1",(0,)),("P1_AB2",(1,)),("P2",(0,1))):
        res=[]
        for seed in ((0,) if eta==0 else (70000,70001,70002)):
            noisy=E.shared_noisy_trajectories(s,eta,seed); fm,_=E.split_mask(s.t)
            X=[];F=[]
            for i in idx:
                x=noisy.noisy[i][fm]; X.append(x)
                F.append(s.numeric_rhs(x) if eta==0 else E.estimate_derivatives(s.t[fm],[x])[0])
            X=np.concatenate(X);F=np.concatenate(F)
            try:
                g,v=binned_smooth(X,F); res.append(rel(v,s.numeric_rhs(g)))
            except Exception as e: res.append(np.nan); print("   fail",sid,prot,type(e).__name__)
        print(f"sys {sid:2d} eta {eta} {prot}: binned+GCV err {np.nanmedian(res):.2e}")
