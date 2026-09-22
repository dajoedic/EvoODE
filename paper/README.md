# paper/ — Paper 1 manuscript sections

One file per section of the structure fixed in `PAPER_1.md` ("Planned Paper Structure").
Written in English. Numbers come from the documents, never from memory; each factual claim should be
traceable to `DIARY.md`, a work-package report, or a committed artefact.

| File | Section | Status |
|---|---|---|
| `03_method.md` | 3 Method | draft, written 2026-08-22 |
| `04_failure_analysis.md` | 4 Failure analysis | draft, written 2026-08-22 |
| `05_experimental_protocol.md` | 5 Experimental protocol | draft, written 2026-08-22 |

Sections 1, 2, 8 and 9 are not started. Section 2 (Related Work) waits on the protocol audit, since
what may be said about published results depends on what that audit finds.

> **These drafts describe a method the project no longer runs. Do not reuse a sentence from them
> without checking it against `PAPER_1.md` and `docs/paper1_phaseC_benchmark_plan.md`.** They were
> written on 2026-08-22, before the campaign finished (2026-09-04), before its analysis (WP-A5 to
> A9), and before the four findings of the September reset: the missing constant term, coefficient
> persistence, the first held-out evaluation, and the first baseline.
>
> **Three things have since changed that the drafts cannot absorb by editing a number.**
> The canonical basis is `staged_polynomial_basis_with_constant` (P3, 2026-09-13), so the model
> class is different and **30 of 63 systems are exactly representable, not 20** — which moves the
> exact/surrogate stratification, the support-recovery tables and every count derived from them.
> `05_experimental_protocol.md` still states that no external baseline is computed in-house; that
> non-goal was **lifted** on 2026-09-09 and Claim D now requires exactly it. And Phase B is demoted
> to diagnostics, so the main tables come from Phase C alone.
>
> **The scope is no longer open.** Decided 2026-09-09: Paper 1 is a **method paper** with four
> claims (A structure discovery, B stage capping, C generalization, D against SINDy). The three
> candidate framings of 2026-09-07 are rejected, and the old Claim A/B/C labels are retired —
> `PAPER_1.md` keeps them under "Superseded Claim Labels". The drafts use the old labels.
>
> Nothing here is deleted, because the drafts are the record of what was arguable at the time.
> Sections 3 and 5 are rewritten from the Phase C state once the campaign has been evaluated;
> rewriting them earlier means writing them twice.

**Where a report lives.** `codex/reports/REPORT_WP_<id>.md` is the finishing report of a work package —
provenance, written once. `docs/WP-<id>.md` is a report promoted because a decision rests on it; it
is linked from `CLAUDE.md` or `PAPER_1.md` and kept correct. Cite the promoted form where one
exists. Older `docs/wp_<id>_<description>.md` files predate the rule and keep their names.

**Rules while drafting.**

- Results stay placeholders until campaign records exist. A sentence that anticipates a result is a
  sentence that will have to be unwritten.
- Claims about the cap hold for the exactly representable systems — **30 of 63 under the canonical
  basis**, 20 under the old one, so state which basis a number comes from. On the surrogates the
  controller is unauditable by construction, and no sentence may blur that.
- **The cap saves search effort only where it caps every equation** (`_effective_max_stage` takes
  the maximum over the caps). Claim B is conditional, and the condition's frequency belongs beside
  it: fully capped are dim 1 32/46, dim 2 15/56, dim 3 3/20, dim 4 0/4.
- Cost statements rest on counters, never on wall-clock (Design Principle 7). Timing appears only as
  capacity context, labelled as such.
- Exact and surrogate systems are never mixed into one structure-correctness metric.
- **Both metrics, always** (Design Principle 9): structure recovery *and* the R² > 0.9 rate. Never
  one alone — they disagree, and the R² rate is what makes any external comparison possible at all.
- Any recovery number that comes from EvoODE carries its **compute cost** beside it. For a method
  whose thesis is efficiency, a recovery rate without a fit count is half a sentence.
