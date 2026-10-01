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

## 3. Nächste Schritte

1. **WP-N32 abnehmen:** `codex/STATUS.md` und `codex/reports/REPORT_WP_N32.md` lesen, die
   Julia-Tests und die Kontrollzellen fahren (4 Zellen bei (0, 0, 10) bitgleich zu C-1, Orakel bei
   10 bitgleich zu C-5), dann committen.
2. **Vom Nutzer zu bestätigen**, bevor das C-6-Manifest entsteht: drei Rauschrealisierungen je
   Bedingung, Realisierung r gekoppelt an Seed r (§9.4).
3. **WP-N33 schreiben:** Manifeste und k8s-Jobs für den C-6-Piloten, für C-8 Teil A und B und das
   C-6-Raster; dazu die nachträgliche saubere Auswertung.
4. Die Arbeitspakete für die Baselines auf den C-6-Daten (SINDy, Weak-SINDy, ODEFormer) und für
   PySR (§9.5).
5. Nach dem Ende von C-3: die ganze Kette aus `SCRIPTS.md` strikt in die versionierten Orte rechnen,
   `analysis/configs/paper1_phaseC_v1.json` umstellen, die endgültige Auswertung mit der neuen
   Aggregationshierarchie (§9.3). WP-T1f nach dem Ende einsammeln.

## 4. Offen, klein

- `test_phase_a_evaluation_does_not_overwrite_frozen_artifacts`: ein Umgebungsartefakt, den Test
  von der lokalen Datei entkoppeln (kleines Codex-Paket).

## 5. Git

Gepusht bis `1db1193`. Lokal und **nicht gepusht** sind alle Commits seit `14dc9b5`, darunter die
Commits vom 01.10.
