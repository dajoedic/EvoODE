import numpy as np
from experiments.annihilator_gate2a_v3.operator_search import evaluate_class
from experiments.annihilator_gate2a_v3.weak_operator import WeightContext
from experiments.annihilator_gate2a_v3.functions import sigma_eff
from experiments.annihilator_odebench_smoke.config import SEARCH_SETTINGS as ST
from experiments.annihilator_odebench_smoke.catalog import load_systems, training_domain
S=load_systems()
for sid,cls in [(3,(3,0)),(7,(3,1))]:
    s=S[sid]; dom=training_domain(s)
    xt=np.sort(np.concatenate(s.x_train))
    grids={"trajectory(1024)":xt,"trajectory dedup":np.unique(np.round(xt,12)),
           "equispaced 1024":np.linspace(dom.a,dom.b,1024),"equispaced 2000":np.linspace(dom.a,dom.b,2000)}
    for name,x in grids.items():
        z=(x-dom.mu)/dom.scale; f=s.numeric_rhs(x)
        sig=sigma_eff(f,0.0,ST.sigma_floor_factor)
        kf,kv,af,av=WeightContext(z,f,ST).split(*cls)
        ev=evaluate_class(af,kf,av,kv,sig,ST)
        t=ev.test
        print(sid,cls,f"{name:18s} n={len(x):4d} min dz={np.min(np.diff(z)):.1e} T={t.statistic:.3g} crit={t.critical:.3g} passed={t.passed}")
