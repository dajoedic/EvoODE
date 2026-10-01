# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-01, Abend.** Push und `oc apply` macht der Nutzer.

---

## 1. Was läuft

| Lauf | Wo | Stand 01.10. 15:40 | Anmerkung |
|---|---|---|---|
| C-3 | Orion, `221a3a7` | 177 / 180 | 904 fertig 01.10. 07:50 UTC. Offen: 897 (Level 28), 899 (29), 905 (28), Lorenz `pretune_on`; Ende ~2.–5.10.; keine Deadline |
| WP-T1f | Orion, `1db1193` | 27 / 36 | rechnen: 54 IC2 (182/185), 55 IC2 (163), 56 IC2 (164), 58 IC1 (29), 58 IC2 (80), 59 IC1 (87); warten: 59 IC2, 61 ×2. **Risiko:** 58 IC1 schaffte 7 Zeilen in 11,5 h — bei dem Tempo reicht die Deadline 12.10. nicht. Morgen nachsehen |
| WP-N32 | Codex, lokal | übergeben | Datenbedingung und `clamp_val` im Kampagnenpfad. Julia-Abnahme macht Claude (Kommandos im Report) |

Statusseite „EvoODE auf Orion“: https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx (Version 20) — bei
jedem Statuswechsel neu veröffentlichen.

## 2. Was heute entschieden wurde

Scope-Erweiterung vom 01.10.: Paper 1 ist ein Fundament-Paper und genau das Phase-C-EvoGrow **mit**
[−10, 10]. Neu eingefroren sind C-6 (Robustheit), C-7 (PySR) und C-8 (Grenzen-Diagnose). Verbindlich
sind `PAPER_1.md` („Scope Extension“) und `docs/paper1_phaseC_benchmark_plan.md` §9; die
Zusammenfassung steht im DIARY vom 01.10. (oberster Eintrag).

## 3. Nächste Schritte — die Reihenfolge steht im Backlog in `CLAUDE.md`

**Gestuft, mit Toren** (§9.4a). Laufort: unter 1 h auf dem Laptop, unter 24 h auf Orion, darüber
nur auf ausdrückliche Entscheidung.

1. **R-02:** WP-N32 abnehmen. `codex/STATUS.md` und den Report lesen, die Julia-Tests fahren, dann
   **Stufe 0** (System 1 bei (0, 0) bitgleich zu C-1) und B-01 (Orakel System 1, Grenze 10 bitgleich
   zu C-5), dann committen.
2. **R-03:** WP-N33a an Codex: die nachträgliche saubere Auswertung.
3. **R-04, Stufe 1:** System 1 mit beiden Bedingungen auf dem Laptop, 1 h Timeout. Danach **Tor S1**:
   alle Zahlen an den Nutzer. Er entscheidet über Stufe 2.

Parallel, unabhängig vom Rauschen: P-01 bis P-03 (C-3 und WP-T1f einsammeln, endgültige
Phase-C-Auswertung).

## 4. Offen, klein

- `test_phase_a_evaluation_does_not_overwrite_frozen_artifacts`: ein Umgebungsartefakt, den Test
  von der lokalen Datei entkoppeln (kleines Codex-Paket).

## 5. Git

Gepusht bis `1db1193`. Lokal und **nicht gepusht** sind alle Commits seit `14dc9b5`, darunter die
Commits vom 01.10.
