# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-05 nachmittags. Gate 2A v3 ist gescheitert (Anhang A nicht bestanden, Anhang B löst K6 aus). Neue,
eingefrorene Diagnose: Trennt `AMBIGUOUS` nicht identifizierbare von identifizierbaren Fällen? Skript fertig
(WP-DIAG-AMB-a/b), Pilot ausgewertet, Hauptlauf mit N = 100 läuft auf Orion seit 05.10. 15:15, Ende etwa 06.10. Mitternacht.**

## 1. Wo wir stehen

- **Gate 2A v3:** `docs/GATE_2A_v3_STAGE_K_RESULT.md`. Ordnung 1–2 kalibriert, K6 (Ordnung 3) nicht; Clean K7
  schmal `WRONG`, K7 und K8 breit `AMBIGUOUS`. Anhang B: F4, F5, F8, F9 und F10 bei 1 % breit N1, K6 würde
  auslösen. Das Ergebnis bleibt so stehen, **keine v4**.
- **Neue Frage** (Nutzer, `PRACTICAL_ANNIHILATOR_BENCHMARK.md`, Entwurf): Taugt die Methode als Selective Prediction,
  also mit Abstention bei unzureichender Evidenz?
- **Vorher die Diagnose** `docs/DIAGNOSTIC_AMBIGUITY.md` (eingefroren): N1 = F4, F5, F8 und I = F1, F2, F6, breit,
  1 %, v3 unverändert. Interessant nur, wenn B1–B4 alle erfüllt sind, sonst ist die Abstention-Story negativ.
  Ab diesem Lauf sind F1–F10 Entwicklungsset.
- **Pilot (6 pro Gruppe, nicht belastbar, Details im DIARY):** N1 5 `AMBIGUOUS` und 1 `WRONG`, I 3 `CORRECT` und
  3 `AMBIGUOUS`. Vorläufig sind B1 und B3 nicht erfüllt, B2 und B4 erfüllt. Zwei Warnsignale: In N1 trägt A1 die
  Abstention, der Bootstrap (A2) erkennt die stabil falsche Wahl (3,0) nicht. In I verwirft der Test die
  Referenzklasse in 3 von 6 Fällen (nominal 1 %). Bestätigt sich das, ist B3 kaum erreichbar. Wird beobachtet,
  nicht repariert.

## 2. Nächste Schritte

1. Überwachen mit `experiments/annihilator_gate2a_v3/orion/RUNBOOK.md` §5. Das Fortschrittsprotokoll enthält keine
   Zustände. Bei Neustarts von Pods: Die Teile setzen fort, doppelte Records verhindert `--merge`.
2. Nach `DONE` in allen 11 Teilen: einsammeln (RUNBOOK §6), `--merge --reps 100`, `--summarize`, Ergebnis in
   `docs/DIAGNOSTIC_AMBIGUITY.md` §7. Verdikt nach B1–B4, keine Schwellenänderung. Danach den Hilfs-Pod löschen.
3. Folge des Verdikts (§5): **interessant** heißt `docs/PRACTICAL_BENCHMARK_v1.md` mit eingefrorenen numerischen
   Kriterien, Baselines und Hold-out-Set ausarbeiten. **Negativ** heißt kein Hold-out-Set und kein größerer
   Benchmark. Dann mit dem Nutzer entscheiden, ob die Spur endet.

## 3. Was noch läuft oder liegt

- **Der Hauptlauf läuft auf Orion** (Job `annihilator-diag-amb`), gestartet vom Nutzer am 05.10. um 15:15.
  11 Pods à 1 Kern, Code aus `c71841f`, NFS `/bigdata/data-science/joedicke/annihilator_diag_amb/`. 588 offene
  Realisierungen, 53–54 pro Teil. **Ende erwartet am 06.10. gegen Mitternacht** (rund 32 h, Streuung einige
  Stunden). Der Hilfs-Pod `annihilator-diag-amb-helper` läuft mit, für Überwachung und Einsammeln. Kein aktiver
  Codex-Auftrag.
- `.codex_tmp/` im Wurzelverzeichnis: leerer Temp-Ordner aus der Codex-Sandbox, gesperrt durch Rechte. Nicht
  committen, später löschen.
- `PRACTICAL_ANNIHILATOR_BENCHMARK.md` ist uncommittet (Entwurf des Nutzers).
- `experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/records_merged.jsonl` ist uncommittet:
  Codex' Probe-Merge der 12 Pilot-Records. Er wird vom echten Merge ersetzt.
- Uncommittet liegen noch Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme
  (`experiments/annihilator_gate2a_v2/results/acceptance/`). v2 ist abgelöst. Ob sie committet oder gelöscht werden,
  entscheidet der Nutzer.
