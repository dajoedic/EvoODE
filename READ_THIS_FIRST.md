# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-05 nachmittags. Gate 2A v3 ist gescheitert (Anhang A nicht bestanden, Anhang B löst K6 aus). Neue,
eingefrorene Diagnose: Trennt `AMBIGUOUS` nicht identifizierbare von identifizierbaren Fällen? Das Skript
ist fertig (WP-DIAG-AMB-a), Pilot fertig, Hauptlauf mit N = 100 auf Orion (11 Pods) startbereit.**

## 1. Wo wir stehen

- **Gate 2A v3:** `docs/GATE_2A_v3_STAGE_K_RESULT.md`. Ordnung 1–2 kalibriert, K6 (Ordnung 3) nicht; Clean K7
  schmal `WRONG`, K7 und K8 breit `AMBIGUOUS`. Anhang B: F4, F5, F8, F9 und F10 bei 1 % breit N1, K6 würde
  auslösen. Das Ergebnis bleibt so stehen, **keine v4**.
- **Neue Frage** (Nutzer, `PRACTICAL_ANNIHILATOR_BENCHMARK.md`, Entwurf): Taugt die Methode als Selective Prediction,
  also mit Abstention bei unzureichender Evidenz?
- **Vorher die Diagnose** `docs/DIAGNOSTIC_AMBIGUITY.md` (eingefroren): N1 = F4, F5, F8 und I = F1, F2, F6, breit,
  1 %, v3 unverändert. Interessant nur, wenn B1–B4 alle erfüllt sind, sonst ist die Abstention-Story negativ.
  Ab diesem Lauf sind F1–F10 Entwicklungsset.

## 2. Nächste Schritte

1. **Hauptlauf auf Orion starten (Nutzer).** Anleitung: `experiments/annihilator_gate2a_v3/orion/RUNBOOK.md`
   (Bereitstellen über den Hilfs-Pod, Probelauf, `job.yaml`). Das Archiv `stage.tar` (Code aus `c71841f`, Wheels,
   Pilot-Records) liegt im Scratchpad der Sitzung vom 05.10. unter `orion/` und lässt sich aus dem Repository neu
   bauen (RUNBOOK §1). 11 Pods à 1 Kern, 588 offene Realisierungen, 53–54 pro Teil, rund 32 h.
2. Überwachen mit RUNBOOK §5. Das Fortschrittsprotokoll enthält keine Zustände mehr.
3. Danach einsammeln, `--merge --reps 100`, `--summarize`, Ergebnis in `docs/DIAGNOSTIC_AMBIGUITY.md` §7.
   Verdikt nach B1–B4, keine Schwellenänderung.

## 3. Was noch läuft oder liegt

- **Pilot fertig und ausgewertet** (`c71841f`, Zustände im DIARY). Festgelegt in `docs/DIAGNOSTIC_AMBIGUITY.md`
  §6, **vor** Ansicht der Zustände: $N = 100$, Orion mit 11 Pods. WP-DIAG-AMB-b ist abgenommen (Teile, Merge,
  atomarer Cache, Log ohne Zustand, 10 Tests grün). Manifeste per Dry-Run gegen Orion geprüft. **Der Hauptlauf ist
  noch nicht gestartet.** Kein aktiver Codex-Auftrag.
- `.codex_tmp/` im Wurzelverzeichnis: leerer Temp-Ordner aus der Codex-Sandbox, gesperrt durch Rechte. Nicht
  committen, später löschen.
- `PRACTICAL_ANNIHILATOR_BENCHMARK.md` ist uncommittet (Entwurf des Nutzers).
- Uncommittet liegen noch Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme
  (`experiments/annihilator_gate2a_v2/results/acceptance/`). v2 ist abgelöst. Ob sie committet oder gelöscht werden,
  entscheidet der Nutzer.
