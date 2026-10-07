import json, numpy as np
from scipy.interpolate import CubicSpline
from experiments.annihilator_odebench_smoke import end2end as E
from experiments.annihilator_odebench_smoke.catalog import load_systems, Domain
S=load_systems()
ref=json.load(open("experiments/annihilator_odebench_smoke/results/reference.json"))
orig=E.resample_state_derivative
def spline_resample(x_values,f_values,points=2000):
    x=np.asarray(x_values,float).ravel(); f=np.asarray(f_values,float).ravel()
    o=np.argsort(x); xs,fs=x[o],f[o]
    u,st=np.unique(xs,return_index=True); mf=np.add.reduceat(fs,st)/np.diff(np.append(st,fs.size))
    g=np.linspace(u[0],u[-1],points); v=CubicSpline(u,mf)(g)
    z=(g-0.5*(g[0]+g[-1]))/(0.5*(g[-1]-g[0])); return g,z,v
E.resample_state_derivative=spline_resample
for sid in (7,19,3,21):
    s=S[sid]; rc=tuple(ref["systems"][str(sid)]["reference_class"])
    noisy=E.shared_noisy_trajectories(s,0.0,0)
    dom,xg,zg,fg=E.annihilator_grid_from_training(s,noisy,(0,1),fit_only=True,exact_f=True)
    err=np.sqrt(np.mean((fg-s.numeric_rhs(xg))**2))/np.sqrt(np.mean(s.numeric_rhs(xg)**2))
    fhat,info,fail=E.fit_annihilator_candidate(dom,xg,zg,fg,rc)
    val,vf=E.validation_error(s,fhat,noisy,(0,1)) if fhat is not None else (np.inf,fail)
    print(sid,rc,f"spline interp err {err:.1e}  fail={fail} validation NRMSE={val:.2e}",flush=True)
