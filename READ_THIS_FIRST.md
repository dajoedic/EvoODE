# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-05 nachmittags. Gate 2A v3 ist gescheitert (Anhang A nicht bestanden, Anhang B löst K6 aus). Neue,
eingefrorene Diagnose: Trennt `AMBIGUOUS` nicht identifizierbare von identifizierbaren Fällen? Codex baut das
Skript (WP-DIAG-AMB-a).**

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

1. Codex-Abgabe von WP-DIAG-AMB-a prüfen und committen.
2. **Pilot** (2 Realisierungen je Zelle) starten. Kosten sind unbekannt: eine Realisierung sind 51 Suchen (Haupt
   plus 50 Bootstrap). Clean-Zellen in Stufe K brauchten 40–50 min.
3. Aus den Zählgrößen $N$ und den Laufort festlegen, in `docs/DIAGNOSTIC_AMBIGUITY.md` §6 eintragen und committen,
   **bevor** der Hauptlauf startet.
4. Hauptlauf, `--summarize`, Ergebnis in §7.

## 3. Was noch läuft oder liegt

- Codex arbeitet an WP-DIAG-AMB-a (`codex/STATUS.md`).
- `PRACTICAL_ANNIHILATOR_BENCHMARK.md` ist uncommittet (Entwurf des Nutzers).
- Uncommittet liegen noch Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme
  (`experiments/annihilator_gate2a_v2/results/acceptance/`). v2 ist abgelöst. Ob sie committet oder gelöscht werden,
  entscheidet der Nutzer.
