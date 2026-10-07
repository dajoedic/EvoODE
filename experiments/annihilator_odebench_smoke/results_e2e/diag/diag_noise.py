import numpy as np, json
from experiments.annihilator_odebench_smoke import end2end as E
from experiments.annihilator_odebench_smoke.catalog import load_systems
S=load_systems()
rel=lambda a,b: np.sqrt(np.mean((a-b)**2))/np.sqrt(np.mean(b**2))
for sid in (3,7):
    s=S[sid]
    for prot,idx in (("P1_AB1",(0,)),("P2",(0,1))):
        errs_d=[];errs_s=[];errs_l=[];osc=[]
        for seed in (70000,70001,70002):
            noisy=E.shared_noisy_trajectories(s,0.01,seed)
            # derivative error at sample points
            fm,_=E.split_mask(s.t)
            xs=[];fs=[]
            for i in idx:
                x=noisy.noisy[i][fm]; d=E.estimate_derivatives(s.t[fm],[x])[0]
                errs_d.append(rel(d,s.numeric_rhs(s.x_train[i][fm]))); xs.append(x); fs.append(d)
            X=np.concatenate(xs);F=np.concatenate(fs)
            g,z,v=E.resample_state_derivative(X,F)          # spline (current)
            o=np.argsort(X); vl=np.interp(g,X[o],F[o])        # linear for comparison
            tru=s.numeric_rhs(g)
            errs_s.append(rel(v,tru)); errs_l.append(rel(vl,tru)); osc.append(np.max(np.abs(v))/np.max(np.abs(tru)))
        print(f"sys {sid} {prot}: deriv err {np.median(errs_d):.3f} | spline-grid err {np.median(errs_s):.3g} (max/true {np.median(osc):.3g}) | linear-grid err {np.median(errs_l):.3f}")
