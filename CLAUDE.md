# CLAUDE.md — Annihilator-Spur (Idee #1)

Dieser Ordner (`EvoODE-next`) ist ein Git-Worktree auf dem Branch **`annihilator-discovery`** und ein eigenes
VS-Code-Projekt. Er gehört **ausschließlich** zur Methodenspur „Idee #1 – Annihilator-Guided ODE Discovery“.
**EvoGrow und Paper 1 leben im Ordner `..\EvoODE` auf `main`** und werden hier weder bearbeitet noch zitiert.

Ersetzt auf diesem Branch seit 2026-10-05 die EvoGrow-CLAUDE.md. Die Dateien `PAPER_1.md`, `SCRIPTS.md`,
`CHANGELOG.md`, `src/`, `studies/`, `analysis/`, `k8s/` sind Erbstücke aus der Abzweigung von `main`. Für diese
Spur sind sie **ohne Bedeutung**: nicht lesen, nicht ändern, nicht zitieren.

## Trennung der Spuren (Nutzer, 2026-10-05)

- **Eine Chat-Sitzung pro Spur.** Annihilator-Arbeit nur in einer Sitzung in diesem Ordner, EvoGrow-Arbeit nur in
  `..\EvoODE`.
- Kein Merge dieses Branches nach `main`. Ein eigenes Repository entsteht erst, wenn Gate 2A und Gate 2B
  überzeugend bestanden sind (`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` §10).
- Eigene Übergabe (`READ_THIS_FIRST.md` hier), eigenes `DIARY.md`, eigenes `codex/CURRENT_TASK.md` und
  `codex/STATUS.md`. Auf `main` steht zu dieser Spur höchstens ein Verweis-Satz.
- EvoGrow-Zahlen erscheinen hier nicht als Argument, Annihilator-Zahlen nicht in Paper-1-Dokumenten.

## Dokumente

| Dokument | enthält |
|---|---|
| `READ_THIS_FIRST.md` | flüchtige Übergabe: was läuft, was offen ist; wird überschrieben, nie angehängt |
| `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` | **Leitdokument** der Idee: Motivation, Kernidee, Pipeline, Novelty, Gate-Folge, Regeln |
| `docs/GATE_2A.md` | v1, eingefroren, an der Abnahme gescheitert (nie gelaufen) |
| `docs/GATE_2A_v2.md`, `docs/GATE_2A_v2_RATIONALE.md` | v2 und die Begründung jeder Änderung gegenüber v1; Stufe K gescheitert (FNS-Fehler) |
| `docs/GATE_2A_v3.md` | v3 = v2 mit AML (L-BFGS), $n_{\text{exact}}$ breit, exakter Verifikation |
| `docs/GATE_2A_v3_STAGE_K_RESULT.md` | Anhang A nicht bestanden, Anhang B (Diagnose) löst K6 aus |
| `PRACTICAL_ANNIHILATOR_BENCHMARK.md` | Entwurf (Nutzer): praktischer Benchmark nach Gate 2A, Selective Prediction; noch ohne eingefrorene Kriterien |
| `docs/DIAGNOSTIC_AMBIGUITY.md` | eingefrorene Diagnose: trennt `AMBIGUOUS` N1- von I-Fällen? Entscheidet, ob der praktische Benchmark weiterverfolgt wird |
| `docs/DIAGNOSTIC_AMBIGUITY_RESULT.md` | Ergebnis der Diagnose, Verdikt negativ (B1), Lesart |
| `docs/REALITY_CHECK_DIRECT_REGRESSION.md` | eingefroren: Stufe A, direkte Sparse-Regression auf denselben Samples, Ergebnis in §10 |
| `docs/REALITY_CHECK_DIRECT_REGRESSION_RESULT.md` | Ergebnis und Übergabe, Verdikt `STRONG_NEGATIVE` |
| `docs/ODEBENCH_SMOKE_TEST.md`, `docs/ODEBENCH_SMOKE_TEST_v2.md` | ODEBench-Smoke-Test: v1 (im Pilot am Aufbau gescheitert), v2 eingefroren mit Ergebnis |
| `docs/ODEBENCH_SMOKE_TEST_RESULT.md` | **aktueller Stand:** Ergebnis und Übergabe, Verdikt „beenden“ (Bedingung A); letzte Prüfung vor dem Abschluss von Idee #1 |
| `DIARY.md` | Chronologie (die Einträge ab 2026-10-04 betreffen diese Spur, ältere sind EvoGrow-Erbe) |
| `codex/CODEX_PROTOCOL.md`, `codex/CURRENT_TASK.md`, `codex/STATUS.md`, `codex/reports/` | Codex-Handshake |
| `experiments/annihilator_gate2a/`, `_v2/`, `_v3/` | Code und Ergebnisse je Version, alte Versionen verhaltensgleich eingefroren |

## Arbeitsweise (übernommen aus den Nutzerregeln; das Gedächtnis aus `..\EvoODE` gilt hier nicht automatisch)

- **Kommunikation mit dem Nutzer auf Deutsch.** Code, Kommentare, Docstrings und Commit-Messages auf Englisch.
- **Commits ohne `Co-Authored-By` oder sonstige KI-Attribution** (akademischer Kontext).
- **Claude committet, der Nutzer pusht.** Nie nach GitLab pushen, nach GitHub nur mit ausdrücklicher Erlaubnis. Nie
  `git add -A`, weil Codex parallel im Working Tree arbeitet. Nur gezielte Pfade stagen.
- **Code schreibt Codex, nicht Claude.** Claude schreibt den Auftrag nach `codex/CURRENT_TASK.md` (immer
  überschreiben, zweite Zeile `**Language: Python**`, kein Code im Auftrag, nur Spezifikation) und startet Codex
  **selbst** aus diesem Ordner, im Hintergrund:
  `codex exec -C "C:/Users/joedicke/Documents/reps/EvoODE-next" -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null`
  Nie `--full-auto`, nie `nohup … &`. Nach einem Abbruch prüfen, ob der Kindprozess weiterläuft
  (Geistersitzungen), und ihn gezielt beenden. `done` heißt: Dateien uncommittet im Working Tree, Claude prüft und
  committet. Claude-Diagnosen in Wegwerf-Skripten im Scratchpad sind erlaubt.
- **Laufort nach erwarteter Laufzeit:** unter 1 h startet Claude auf dem Laptop, unter 24 h Orion (startet der
  Nutzer), sonst Gespräch. **Keine harten Zeit-Cuts.** Erwartete Laufzeit vorher nennen, eine deutliche
  Überschreitung melden. Läufe über 2 h losgelöst starten (eigener Prozess, Logs, `DONE`-Datei), weil
  Hintergrundbefehle der Werkzeugumgebung nach 2 h beendet werden.
- **Wall-Clock ist nie Evidenz.** Kosten- und Effizienzaussagen nur aus Zählgrößen.
- **Veraltete Aussagen in Projektdokumenten sofort korrigieren**, nicht erst fragen. Nach jedem Commit den Hash als
  HTML-Kommentar in den aktuellen DIARY-Eintrag. READ_THIS_FIRST bei jedem Statuswechsel überschreiben und
  committen.
- **Befehle für den Nutzer** direkt im Chat, mit Zweck, Dauer und Pass-Kriterium, erst wenn sie fällig sind.
- **Token abgelaufen** (Orion): „TOKEN ABGELAUFEN“ melden, `oc login --web https://api.orion.scch.at:6443`
  ausgeben, warten.

## Regeln dieser Spur

- Erst billig versuchen, die Idee zu zerstören. Entwicklungszeit oder Compute bekommt sie erst nach mehreren
  harten Gates.
- **Jede Entscheidungsregel wird vor dem ersten Lauf eingefroren.** Eine Änderung danach braucht eine neue Version,
  alte Versionen und Ergebnisse bleiben stehen. Nichts wird am Gate-Set kalibriert, Kalibrierung nur auf einem
  disjunkten Set.
- Von einfach zu komplex. **Kein GP.** Nichts aufbauen auf Arbeiten mit Gabriel Kronberger (Operon,
  shape-constrained SR, E-Graph-SR mit de França u. a.). Autorenschaft prüfen, bevor eine Methode übernommen wird.
- Kein HPC, solange ein Gate auf dem Laptop machbar ist.
- Systeme für spätere Gates: Entwicklung 7 / 40 / 56 / 63, verschlossenes Prüfset 4 / 49 / 59 / 62. Das Prüfset
  wird nie angesehen, bevor ein Gate es verlangt.
