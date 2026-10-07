import json, numpy as np
from experiments.annihilator_odebench_smoke import end2end as E
from experiments.annihilator_odebench_smoke.fhat import leading_coefficients
from experiments.annihilator_odebench_smoke.catalog import load_systems
from experiments.annihilator_gate2a_v3.weak_operator import WeightContext
from experiments.annihilator_gate2a_v3.operator_search import aml_candidate, normalize_coeffs
from experiments.annihilator_odebench_smoke.config import SEARCH_SETTINGS
ref=json.load(open("experiments/annihilator_odebench_smoke/results/reference.json"))
S=load_systems()
def lead_roots(c,r,d):
    lead=leading_coefficients(c,r,d); return np.roots(lead[::-1])
for sid in (7,19,3):
    s=S[sid]; rc=tuple(ref["systems"][str(sid)]["reference_class"])
    noisy=E.shared_noisy_trajectories(s,0.0,0)
    dom,xg,zg,fg=E.annihilator_grid_from_training(s,noisy,(0,1),fit_only=True,exact_f=True)
    fu=s.numeric_rhs(xg)  # exact on uniform grid
    print(f"system {sid} class {rc} domain [{dom.a:.3f},{dom.b:.3f}]  interp err rel {np.sqrt(np.mean((fg-fu)**2))/np.sqrt(np.mean(fu**2)):.2e}")
    for name,vals in (("interpolated",fg),("exact uniform",fu)):
        kf,kv,af,av=WeightContext(zg,vals,SEARCH_SETTINGS).split(*rc)
        c,it,conv,msg,sv,_=aml_candidate(af,kf)
        print(f"   {name:14s} iters={it} conv={conv} sv_small={np.sort(sv)[:2]} lead roots z={np.round(lead_roots(c,*rc),3)} coeffs={np.round(normalize_coeffs(c),4)}")
