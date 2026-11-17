# Paper 2 note — an exchange step for WISP's growth path ("FoBaEx", working name)

Written 2026-11-17 at the user's request. A note, not a plan: no compute before 31.12. (CLAUDE.md, WISP plan), and
WISP 1 stays unchanged (simplicity guardrail). Placement: `docs/phd_thesis_arc.md` §12, item 4.

## 1. The failure it addresses (Q9, measured)

Noisy dim-1/2 exact data sets, rule (c), `analysis/data/sideproject_residual_growth/q9_failure_anatomy/`:

- WISP misses the exact structure in 724 of 1,260 data sets. **55 are selection failures, 669 path failures.**
  When the truth is on the path, the trajectory BIC chooses it in 559 of 590 data sets: selection works.
- In **601 of the 669** path failures a true term enters no candidate at all; 38 are supersets that are never pruned
  back; 30 have all true terms enter, never together (19 on system 17).
- The path is rarely too short: its largest model has at least the true size in **499 of 601**. A correlated wrong
  term enters first, absorbs the true term's signal, the true term's remaining gain falls below the χ² floor and the
  path stops. Every path in this group ends at the noise-referenced stop, none at a size limit.
- Missing terms are low-order: u1 (312), u1² (235), u2 (132), the constant (110).

This is the textbook failure of greedy forward selection under correlated columns: Tropp's exact-recovery condition
(OMP picks only true atoms) is violated. FoBa's backward step does not repair it, because it removes a term only when
the removal costs little, and a term that has taken the true term's place does not.

## 2. The idea

After the forward/backward loop (or after every forward step), try replacing each active term by each inactive term
in the weak space and accept the exchange that lowers the weak residual most, as long as one does; then continue the
path. Cost: one least-squares solve per (active, inactive) pair, no ODE solve. The decision between path states stays
on the trajectory (refit + trajectory BIC), unchanged.

Variants worth comparing: (a) exchange once at the end of the path; (b) exchange after every forward step;
(c) a small beam over the first steps instead of exchange, letting the trajectory BIC choose (selection is reliable,
so widening the candidate set should pay directly).

## 3. Prior work — the exchange step is not new

Verified by web search 2026-11-17 (subagent report; full texts opened only where marked):

- **Sequential replacement:** Miller, *Subset Selection in Regression*, 2nd ed., Chapman & Hall/CRC 2002
  (doi:10.1201/9781420035933); Miller, JRSS A 147(3):389–425, 1984 (doi:10.2307/2981576). Swap one variable at a time
  while the RSS falls — this is the proposed step. Background: Efroymson 1960 (stepwise), Hocking, Biometrics 1976.
- **Greedy sparse approximation with replacement:** Vats & Baraniuk, "When in Doubt, SWAP: High-Dimensional Sparse
  Recovery from Correlated Measurements", NIPS 26, 2013 (arXiv:1312.1706) — swaps repair greedy/Lasso errors under
  correlated columns, with recovery guarantees. **The main prior art.** Also Jain, Tewari & Dhillon, "Orthogonal
  Matching Pursuit with Replacement", NIPS 24, 2011; Soussen et al., Single Best Replacement, IEEE TSP 59(10), 2011
  (doi:10.1109/TSP.2011.2160633); CoSaMP (Needell & Tropp 2009) and Subspace Pursuit (Dai & Milenkovic 2009) replace
  several atoms per step; Tropp, "Greed is good", IEEE TIT 2004 (doi:10.1109/TIT.2004.834793) for when greedy fails;
  Zhang, FoBa, IEEE TIT 2011 (doi:10.1109/TIT.2011.2146690).
- **System identification:** Li, Peng & Bai, "A two-stage algorithm for identification of nonlinear dynamic systems",
  Automatica 42(7), 2006 (doi:10.1016/j.automatica.2006.03.004) — forward OLS selection, then each selected term is
  reviewed and replaced by a better candidate at the same size: **an exchange step on FROLS-type NARX identification.**
  Guo, Guo, Billings & Wei, "An iterative orthogonal forward regression algorithm", IJSS 46(5), 2015
  (doi:10.1080/00207721.2014.981237; full text checked) — reruns OFR with each first-model term forced first.
  Piroddi & Spinelli, IJC 76(17), 2003 — selection by simulation error plus pruning (already cited in the WISP paper).
  Correction: "Piroddi & Lovera 2008" (IFAC) is about error filtering, not about revising the selected set.
- **Sparse ODE identification:** WeakIdent (Tang et al., JCP 483, 2023, doi:10.1016/j.jcp.2023.112069) already uses
  Subspace Pursuit in the weak space, i.e. implicit multi-term replacement. MIOSR (Bertsimas & Gurnee, Nonlinear Dyn
  111, 2023, doi:10.1007/s11071-022-08178-9) solves the best subset per size exactly by mixed-integer optimization;
  for moderate libraries it makes exchange in the linear space unnecessary. SINDy/SR3/E-SINDy/WSINDy/PDE-FIND do not
  exchange.
- **Name:** "FoBaEx" / "forward-backward-exchange" not found in use (nearest: FoBa-obj/FoBa-gdt, Liu et al. ICML 2014).

## 4. What could still be a contribution

Not the exchange itself. The defensible claim is about the interface: **exchange changes which states the path offers
to a trajectory-level selector.** WISP's own data say selection is solved and the generator is the bottleneck, so the
question is whether a better linear-space generator (exchange, beam, or exact best subset per size) raises structure
recovery once its states are judged on the trajectory. A fair study therefore compares, on the frozen Q9 data:
FoBa (WISP 1) / FoBa + exchange / beam / **MIOSR best subset per size** as generators, all followed by the same
trajectory refit and BIC. MIOSR is the reference a reviewer will ask for; if exact best subset in the weak space is
no better than FoBa + exchange, the cheap step is enough; if it is better, the paper is about generators, not swaps.

## 5. First step when there is time (minutes, no fits)

On the 601 never-entered data sets: from the largest path candidate, does one best weak-space exchange reach the true
support? And how often does the best-subset solution of the true size equal the truth in the weak space? Both are
upper bounds on what any generator change can buy, computed from the stored designs without a single ODE solve.
Guard: the exchange must not create false hits on the 536 data sets WISP already gets right (WP-T1f evidence that
same-size swaps do not leave the true support: 0 of 2,479).
