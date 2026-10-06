# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-06 abends. Die Diagnose `AMBIGUOUS` ist abgeschlossen, Verdikt negativ (B1 verfehlt). Vor dem
Abschluss läuft ein letzter Reality-Check (Stufe A, `docs/REALITY_CHECK_DIRECT_REGRESSION.md`, eingefroren): Codex
baut WP-RC-A, danach rechnet Claude Pilot und Hauptlauf auf dem Laptop (Minuten).**

## 1. Wo wir stehen

- **Ausführlich:** `docs/DIAGNOSTIC_AMBIGUITY_RESULT.md` (Ergebnis, Lesart, Optionen, Datenablage).
- **Kurz:** 600 Realisierungen (N = 100 je Funktion, breit, 1 %).
  - B1 = 1,000: alle 118 eindeutigen N1-Ausgaben sind `WRONG`. Schwelle < 0,20, **nicht erfüllt**.
  - B2 = 0,607, B3 = 0,990, B4 = 0,597: erfüllt.
- **Mechanismus:** Die Suche bleibt in N1 an einer früheren falschen Klasse mit konstanten Koeffizienten hängen,
  F4/F5 an (3,0), F8 an (2,0) oder (3,0). Das passt fast exakt zur Teststärke aus Anhang B. Ob daraus `AMBIGUOUS`
  oder `WRONG` wird, hängt an der Nullraumdimension dieser Klasse (A1), nicht an der Identifizierbarkeit. Der
  Bootstrap (A2) erkennt stabile Fehlwahlen nicht. F4 ist zu 99 % stabil falsch.
- **Folgen nach der eingefrorenen Regel (§5):** kein `PRACTICAL_BENCHMARK_v1.md`, kein Hold-out-Set, kein größerer
  Benchmark, keine Nachjustierung von A1–A3 oder Schwellen. F1–F10 sind Entwicklungsset. Das Prüfset
  4 / 49 / 59 / 62 bleibt verschlossen.
- **Gesamtbild der Spur:** v1 nie gelaufen, v2 Stufe K gescheitert, v3 Anhang A nicht bestanden, Anhang B löst K6
  aus, Diagnose negativ.

## 2. Nächste Schritte

0. **WP-RC-A abnehmen** (Codex, `codex/STATUS.md`), dann Pilot (Seeds 50000–50001) und Hauptlauf (50000–50019)
   auf dem Laptop, `--summarize`, Ergebnis in §10 der Spezifikation. `STRONG_NEGATIVE` heißt Spur beenden, `OPEN`
   heißt Stufe B (W-SINDy) erst spezifizieren und mit dem Nutzer besprechen.
1. **Entscheidung des Nutzers** (nach Stufe A):
   - **A, Spur beenden (Empfehlung):** Abschluss in `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` festhalten.
   - **B, grundsätzliche Neubewertung:** Messdesign oder eingebaute Identifizierbarkeitsprüfung. Das wäre eine neue
     Idee mit eigener, vorab eingefrorener Spezifikation und neuen Testfunktionen, keine Fortsetzung von Gate 2A.
2. Danach aufräumen (§3).

## 3. Was noch liegt

- Codex-Auftrag WP-RC-A aktiv (gestartet 06.10.). Kein Job, kein Pod auf Orion aktiv. Der Hilfs-Pod `annihilator-diag-amb-helper` ist gelöscht. Die
  Originaldaten bleiben auf dem NFS unter `/bigdata/data-science/joedicke/annihilator_diag_amb/`. Eine lokale Kopie
  ist committet unter `experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/orion/`.
- Die abgeschlossenen Job-Pods (`annihilator-diag-amb-*`, `Completed`) und der Job selbst stehen noch auf Orion. Sie
  belegen keine Ressourcen. Löschen bei Bedarf mit `oc delete job annihilator-diag-amb`.
- `.codex_tmp/` im Wurzelverzeichnis: leerer Temp-Ordner aus der Codex-Sandbox, gesperrt durch Rechte. Nicht
  committen, später löschen.
- `PRACTICAL_ANNIHILATOR_BENCHMARK.md` ist uncommittet (Entwurf des Nutzers). Nach dem negativen Verdikt entscheidet
  der Nutzer, ob er als Dokument der Spur committet oder verworfen wird.
- Uncommittet liegen noch Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme
  (`experiments/annihilator_gate2a_v2/results/acceptance/`). v2 ist abgelöst. Ob sie committet oder gelöscht werden,
  entscheidet der Nutzer.
