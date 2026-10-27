# Side project "residual-guided growth" — literature position (2026-10-27)

Novelty check of the Q4 pipeline (weak form + greedy forward-backward path + nonlinear trajectory refit from the weak
start + trajectory-BIC size choice), done by a research agent with web verification on 2026-10-27. Entries marked
*partly* or *unverified* must be read in full before any citation. Not yet read by a human.

## Verdict

No paper found that does the whole combination; every component is published. Closest:

- **Mangan, Kutz, Brunton, Proctor 2017**, Proc. R. Soc. A, 10.1098/rspa.2017.0009 — λ sweep of SINDy gives ~10²
  candidates, least-squares refit in derivative space (no nonlinear refit), each simulated, AIC/AICc on averaged
  absolute trajectory error over **100 validation ICs** (not the training trajectory). Missing vs Q4: weak form, greedy
  path, nonlinear trajectory refit, BIC on the training trajectory.
- **Guo, Guo, Billings, Wei 2016**, Int. J. Systems Science 47(12), 10.1080/00207721.2015.1069906 — modulating-function
  (weak) form + orthogonal forward regression for continuous-time models. No trajectory refit/selection confirmed
  (abstract only).
- **Piroddi & Spinelli 2003**, Int. J. Control 76(17); **Farina & Piroddi 2010**, Int. J. Control 83(7) — simulation-
  error based term selection and pruning for discrete-time polynomial NARX; argue that prediction-error selection picks
  wrong structures.
- **Tang, Liao, Kuske, Kang 2023 (WeakIdent)**, J. Comput. Phys. 483, arXiv 2211.03134 — weak form + subspace pursuit
  per sparsity level + trimming + CV-error choice, all in regression space.
- **Fung, Fasel, Juniper 2024**, arXiv 2402.15357 — weak/FD form + greedy backward elimination by Laplace evidence, no
  simulation.

**Likely accepted as contribution:** nonlinear trajectory refit of every path state seeded by weak least squares; the
measured finding that weak-space size selection overfits while trajectory selection does not (Q4 R9); the benchmark
against Weak-SINDy, SINDy, E-SINDy, ODEFormer with cost. **Likely dismissed as incremental:** the FROLS step and the
FoBa rule alone; BIC instead of AIC. Expected reviewer reading: "Mangan 2017 with a weak form and a different path
generator" — to be answered by an ablation path generator × selection space × refit on/off.

**Must cite:** Mangan 2017, Guo 2016, Piroddi & Spinelli 2003, WeakIdent 2023, Messenger & Bortz 2021 (Weak SINDy,
MMS, arXiv 2005.04339; and J. Comput. Phys. 443, 10.1016/j.jcp.2021.110525), Zhang 2008 FoBa (NeurIPS), Billings,
Chen, Korenberg 1989 (Int. J. Control 49(6), 10.1080/00207178908961377), Fasel et al. 2022 E-SINDy
(10.1098/rspa.2021.0904).

**To check in full:** Bayón-Buján & Merino 2024 (arXiv 2403.06809) — reportedly weak-SINDy selection followed by an
integral-form parameter refit, the closest "weak selection + trajectory refit" found; Chung, Zacharia, Guan 2026 (SLIC,
arXiv 2602.21393); Lejarza & Baldea 2022 (Sci. Rep., 10.1038/s41598-022-13644-w); Goyal & Benner 2022 (RK4-SINDy,
10.1098/rspa.2021.0883); Egan, Li, Carvalho 2024 (ARGOS, Commun. Phys. 7:20). Zhang FoBa IEEE TIT 2011 version and the
SSR attribution to Boninsegna et al. 2018 are unverified.

## Critiques relevant to Q5 (noise)

- Mangan 2017's own caveats: the error term is not a log-likelihood; rankings depend on validation horizon and number
  of series; the method fails at high noise.
- Serially correlated trajectory residuals make N = samples × dimension overstate the effective sample size and mis-
  scale the BIC penalty.
- Under noise the trajectory loss absorbs initial-condition error unless the IC is estimated; chaotic systems make
  trajectory MSE meaningless beyond a Lyapunov time.
- On clean data log(MSE) is dominated by the integrator floor, so trajectory BIC amounts to "the smallest model that
  reaches the floor" — the clean success may not transfer to noise (agent's inference, consistent with Q4).
- Gohain & Jansson 2023, IEEE TSP, 10.1109/TSP.2023.3284365 — AIC/BIC overfit with many candidates relative to samples
  (EBIC-Robust).
