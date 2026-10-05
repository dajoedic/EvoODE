# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-05 nachmittags. Gate 2A v3 ist gescheitert (Anhang A nicht bestanden, Anhang B löst K6 aus). Neue,
eingefrorene Diagnose: Trennt `AMBIGUOUS` nicht identifizierbare von identifizierbaren Fällen? Das Skript
ist fertig (WP-DIAG-AMB-a), Pilot fertig, Hauptlauf mit N = 100 auf Orion (11 Pods) in Vorbereitung.**

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

1. ~~Codex-Abgabe von WP-DIAG-AMB-a prüfen und committen.~~ Erledigt (`ba83120`). Codex meldete `blocked`, weil der
   eine echte Aufruf (F2, Seed 50000) nach 13 min nicht fertig war (vorgesehener Fall). Die Prüfung der
   Koeffizientenreihenfolge ist bestanden (alle 6 Funktionen, Skalarprodukt 1,0). Tests: 2 grün, 4 übersprungen
   (warten auf einen echten Record).
2. **Pilot** (2 Realisierungen je Zelle, 12 Aufgaben) starten, Befehl:
   `python -m experiments.annihilator_gate2a_v3.diagnostics.ambiguity_diagnostic --pilot --workers 6`.
   Eine Realisierung sind 51 Suchen (Haupt plus 50 Bootstrap), F2 allein brauchte über 13 min.
3. **Vor dem Hauptlauf an Codex (WP-DIAG-AMB-b):**
   - Der Nullraum-Cache wird bei mehreren Workern von jedem Prozess ganz neu geschrieben (Wettlauf, möglicher
     Abbruch, fortsetzbar).
   - Die 4 übersprungenen Tests mit einem echten Pilot-Record füllen.
   - `run.log` darf den Zustand nicht mehr enthalten, nur Funktion, Seed und Zählgrößen. Grund: Der Zustand von
     F2/50000 war in `run.log` sichtbar, bevor $N$ festgelegt war. Das ist offenzulegen, ändert aber nichts, weil $N$
     und der Laufort nur nach Kosten festgelegt werden. Ab dann blendet die Überwachung den Zustand aus.
4. **Erst nach dem Ende des Pilots** (Nutzer: nicht schon bei einer Realisierung pro Funktion) aus den Zählgrößen
   $N$ und den Laufort festlegen, in `docs/DIAGNOSTIC_AMBIGUITY.md` §6 eintragen und committen, **bevor** der
   Hauptlauf startet. Erste Schätzung: Bei $N = 100$ sind es 600 Realisierungen zu je 40 min oder mehr, auf
   6 Workern also über 60 h. Das ist nichts für den Laptop.
5. Hauptlauf, `--summarize`, Ergebnis in §7.

## 3. Was noch läuft oder liegt

- **Der Pilot ist fertig und ausgewertet** (12 Records, uncommittet in `results/diagnostic_ambiguity/`). Festgelegt
  in `docs/DIAGNOSTIC_AMBIGUITY.md` §6, **vor** Ansicht der Zustände: $N = 100$, Orion mit 11 Pods à 1 Kern, rund 32 h
  (Nutzer erlaubt die Laufzeit). Pilot-Zustände in `DIARY.md` (6 pro Gruppe, nicht belastbar). Kein aktiver
  Codex-Auftrag.
- `PRACTICAL_ANNIHILATOR_BENCHMARK.md` ist uncommittet (Entwurf des Nutzers).
- Uncommittet liegen noch Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme
  (`experiments/annihilator_gate2a_v2/results/acceptance/`). v2 ist abgelöst. Ob sie committet oder gelöscht werden,
  entscheidet der Nutzer.
