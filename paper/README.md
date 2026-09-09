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

> **These drafts predate the campaign and the reset. Read them against `PAPER_1.md` before
> reusing a sentence.** They were written on 2026-08-22, before the campaign finished (2026-09-04),
> before its analysis (WP-A5 to A9), and before the four findings of the September reset: the
> missing constant term, coefficient persistence, the first held-out evaluation, and the first
> baseline. `PAPER_1.md` also no longer treats Claim B as one claim — it has two halves resting on
> different evidence, and the drafts do not make that distinction.
>
> Nothing here is deleted, because the drafts are the record of what was arguable at the time. But
> **the paper's scope is reopened**: `PAPER_1.md` lists three candidate framings that have to be
> chosen between before sections 6 and 7 can be written.

**Where a report lives.** `codex/REPORT_WP_<id>.md` is the finishing report of a work package —
provenance, written once. `docs/WP-<id>.md` is a report promoted because a decision rests on it; it
is linked from `CLAUDE.md` or `PAPER_1.md` and kept correct. Cite the promoted form where one
exists. Older `docs/wp_<id>_<description>.md` files predate the rule and keep their names.

**Rules while drafting.**

- Results stay placeholders until campaign records exist. A sentence that anticipates a result is a
  sentence that will have to be unwritten.
- Claims about the cap hold for the 20 exactly representable systems. On the 43 surrogates the
  controller is unauditable by construction, and no sentence may blur that.
- Cost statements rest on counters, never on wall-clock (Design Principle 7). Timing appears only as
  capacity context, labelled as such.
- Exact and surrogate systems are never mixed into one structure-correctness metric.
- **Both metrics, always** (Design Principle 9): structure recovery *and* the R² > 0.9 rate. Never
  one alone — they disagree, and the R² rate is what makes any external comparison possible at all.
- Any recovery number that comes from EvoODE carries its **compute cost** beside it. For a method
  whose thesis is efficiency, a recovery rate without a fit count is half a sentence.
