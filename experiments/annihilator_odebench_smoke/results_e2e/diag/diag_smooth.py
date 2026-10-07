import numpy as np
from scipy.interpolate import make_smoothing_spline
from experiments.annihilator_odebench_smoke import end2end as E
from experiments.annihilator_odebench_smoke.catalog import load_systems
S=load_systems(); rel=lambda a,b: np.sqrt(np.mean((a-b)**2))/np.sqrt(np.mean(b**2))
for sid in (3,7,19,21):
    s=S[sid]
    for prot,idx in (("P1_AB1",(0,)),("P2",(0,1))):
        res={"lin":[],"smooth":[]}
        for seed in (70000,70001,70002):
            noisy=E.shared_noisy_trajectories(s,0.01,seed); fm,_=E.split_mask(s.t)
            X=[];F=[]
            for i in idx:
                x=noisy.noisy[i][fm]; X.append(x); F.append(E.estimate_derivatives(s.t[fm],[x])[0])
            X=np.concatenate(X);F=np.concatenate(F); o=np.argsort(X); X,F=X[o],F[o]
            u,st=np.unique(X,return_index=True); mf=np.add.reduceat(F,st)/np.diff(np.append(st,F.size))
            g=np.linspace(u[0],u[-1],2000); tru=s.numeric_rhs(g)
            res["lin"].append(rel(np.interp(g,u,mf),tru))
            res["smooth"].append(rel(make_smoothing_spline(u,mf)(g),tru))
        print(f"sys {sid:2d} {prot}: linear {np.median(res['lin']):.3f}  GCV smoothing {np.median(res['smooth']):.3f}")
