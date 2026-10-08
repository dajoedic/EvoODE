# CLAUDE.md — Annihilator-Spur (Idee #1), Akte

> **Spur abgeschlossen am 2026-10-08: Idee #1 ist gescheitert** (Entscheidung des Nutzers). Dieser Branch ist
> die Akte. Dokumente, Code und Records bleiben unverändert stehen.
>
> - Keine neuen Läufe, kein Codex-Auftrag, keine inhaltlichen Änderungen.
> - Erlaubt sind nur Korrekturen sachlich falscher Aussagen, und die mit DIARY-Eintrag.
> - Eine Wiederaufnahme wäre eine neue Idee mit eigener Gate-Folge (`docs/IDEA_01_RETROSPECTIVE.md` §8).

Dieser Ordner (`EvoODE-next`) ist ein Git-Worktree auf dem Branch **`annihilator-discovery`** des
EvoODE-Repositorys.

- **Inhalt:** ausschließlich die Methodenspur „Idee #1 – Annihilator-Guided ODE Discovery“. Der EvoGrow-Bestand
  aus der Abzweigung von `main` wurde am 08.10. entfernt.
- **EvoGrow und Paper 1** leben im Ordner `..\EvoODE` auf `main`. Sie werden hier weder bearbeitet noch zitiert.
- **Kein Merge** dieses Branches nach `main`.
- **Tags:**
  - `idea01-annihilator-closed`: Stand bei der Abschlussentscheidung;
  - `idea01-annihilator-archive`: die aufgeräumte Akte.

## Einstieg

1. `README.md`: Idee, Prüfungen, Gründe des Scheiterns, Wegweiser (Englisch).
2. `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` §12: Abschluss mit Belegtabelle.
3. `docs/IDEA_01_RETROSPECTIVE.md`: ausführlicher Rückblick mit Lehren.

## Dokumente

| Dokument | enthält |
|---|---|
| `READ_THIS_FIRST.md` | Endstand der Übergabe |
| `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` | **Leitdokument:** Motivation, Kernidee, Pipeline, Novelty, Gate-Folge, Regeln; §12 Abschluss mit Belegtabelle |
| `docs/IDEA_01_RETROSPECTIVE.md` | **Rückblick, endgültig:** Motivation, Idee, Entwicklung, Gründe des Scheiterns, Lehren, Abschluss (§10) |
| `docs/idea_structural_diagnostics.md` | Ursprungsnotiz der Idee (überholt, Denkstand der Entstehung) |
| `docs/GATE_2A.md` | v1, eingefroren, an der Abnahme gescheitert (nie gelaufen) |
| `docs/GATE_2A_v2.md`, `docs/GATE_2A_v2_RATIONALE.md` | v2 und die Begründung jeder Änderung gegenüber v1; Stufe K gescheitert (FNS-Fehler) |
| `docs/GATE_2A_v3.md` | v3 = v2 mit AML (L-BFGS), $n_{\text{exact}}$ breit, exakter Verifikation |
| `docs/GATE_2A_v3_STAGE_K_RESULT.md` | Anhang A nicht bestanden, Anhang B (Diagnose) löst K6 aus |
| `docs/DIAGNOSTIC_AMBIGUITY.md`, `…_RESULT.md` | Diagnose `AMBIGUOUS` gegen `WRONG`, Verdikt negativ |
| `docs/PRACTICAL_ANNIHILATOR_BENCHMARK.md` | Entwurf des Nutzers (Selective Prediction), nach der Diagnose gegenstandslos |
| `docs/REALITY_CHECK_DIRECT_REGRESSION.md`, `…_RESULT.md` | direkte Sparse-Regression auf denselben Samples, `STRONG_NEGATIVE` |
| `docs/ODEBENCH_SMOKE_TEST.md`, `…_v2.md`, `…_RESULT.md` | ODEBench-Smoke-Test mit Oracle-$f$, Verdikt „beenden“ (A) |
| `docs/ODEBENCH_END2END.md`, `…_v2.md`, `…_RESULT.md` | End-to-End-Vergleich aus denselben Trajektorien, deskriptiv; Grundlage der Abschlussentscheidung |
| `DIARY.md` | Chronologie 04.–08.10. |
| `codex/` | Codex-Handshake: Protokoll (enthält noch Julia-Abschnitte aus der EvoGrow-Zeit), letzter Status, Berichte der Annihilator-Arbeitspakete |

## Code und Daten

| Ordner | Inhalt |
|---|---|
| `experiments/annihilator_gate2a/`, `_v2/`, `_v3/` | Gate 2A je Version, alte Versionen verhaltensgleich eingefroren; Diagnose und Reality-Check unter `_v3/diagnostics/`, Orion-Runbook unter `_v3/orion/` |
| `experiments/annihilator_odebench_smoke/` | Smoke-Test (`run.py`) und End-to-End (`end2end.py`), baut auf `_v3` auf; Records kompakt |
| `benchmarks/data/strogatz_extended.json` | ODEBench-Systemdefinitionen, einzige Datei aus dem EvoGrow-Bestand, die der Code braucht |
| `requirements.txt` | Python-Umgebung aller Läufe (Python 3.12.10) |

- **Rohdaten End-to-End** (2 × 910 MB): nicht in Git. Archiviert auf dem Orion-NFS unter
  `/bigdata/data-science/joedicke/annihilator_e2e_raw/`, Prüfsummen in
  `experiments/annihilator_odebench_smoke/RAW_RECORDS_SHA256.txt`, Kopie dort am 08.10. geprüft.
- **Originaldaten der Diagnose:** `/bigdata/data-science/joedicke/annihilator_diag_amb/`, lokale Kopie committet.
- **Tests:** je Ordner aufrufen, weil gleichnamige Testdateien in mehreren Versionen liegen. Stand bei der
  Archivierung 8 + 16 + 54 + 34 bestanden.

## Arbeitsweise (falls hier doch noch etwas korrigiert wird)

- **Kommunikation mit dem Nutzer auf Deutsch.** Code, Kommentare, Docstrings und Commit-Messages auf Englisch.
- **Commits ohne `Co-Authored-By`** oder sonstige KI-Attribution (akademischer Kontext).
- **Claude committet, der Nutzer pusht.**
  - Nie nach GitLab pushen, nach GitHub nur mit ausdrücklicher Erlaubnis.
  - Nur gezielte Pfade stagen, nie `git add -A`.
- **Veraltete Aussagen** in Projektdokumenten sofort korrigieren. Nach jedem Commit den Hash als HTML-Kommentar in
  den DIARY-Eintrag.

## Regeln, die für die Spur galten

- Erst billig versuchen, die Idee zu zerstören. Entwicklungszeit oder Compute bekommt sie erst nach mehreren
  harten Gates.
- **Jede Entscheidungsregel wird vor dem ersten Lauf eingefroren.**
  - Eine Änderung danach braucht eine neue Version; alte Versionen und Ergebnisse bleiben stehen.
  - Nichts wird am Gate-Set kalibriert, Kalibrierung nur auf einem disjunkten Set.
- Von einfach zu komplex. **Kein GP.** Nichts aufbauen auf Arbeiten mit Gabriel Kronberger.
- Kein HPC, solange ein Gate auf dem Laptop machbar ist.
- **Wall-Clock ist nie Evidenz.** Kosten- und Effizienzaussagen nur aus Zählgrößen.
- **Prüfset:** ODEBench 4/49/59/62 wurde nie angesehen und bleibt für künftige Ideen verschlossen.
