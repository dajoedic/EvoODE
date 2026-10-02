# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-02, ~16:00.** Arbeitsreihenfolge: Backlog in `CLAUDE.md` („Backlog Paper 1“).

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts.** Orion-Ergebnisse liegen lokal unter `S:\BigDataOrion\data-science\joedicke\`
(Git Bash `/s/BigDataOrion/...`); Einsammeln ohne `oc exec`, Jobstatus braucht `oc login`.
**Codex startet Claude immer selbst** (nur bei Problemen melden):
`codex exec -C "C:/Users/joedicke/Documents/reps/EvoODE" -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null`
als `run_in_background`, nie `nohup &`, nie `--full-auto` (gibt es nicht). Ohne `-C` landet Codex im
falschen Arbeitsordner.

---

## 1. Was läuft

| Lauf | Wo | Image | Stand | Anmerkung |
|---|---|---|---|---|
| **ODEFormer auf den Stufenzellen** (WP-N38, R-09) | Laptop, Docker | `evoode/odeformer-reference:wp-n27c` (= Dockerfile-Stand `55e9c75`) | gestartet ~15:55, erwartet ~1,5 h | 20 Datenzellen × 4 Konfig. × 3 Wdh. Ausgabe `outputs/wp_n38_noise_odeformer/stages/`, Log `$TEMP/claude/odeformer_stages.log`. **Keine andere lokale Last daneben** (1-s-Zeitwächter) |
| Stufe 3 (System 41, gekappt) | Orion | `5dd1df8` | 0/2, seit ~14:20 | Smoke bitgleich. Erwartet ~8–17 h je Zelle |
| B-03 (Orakel dim 3/4, 3 Grenzen) | Orion | `5dd1df8` | 16 + 12 + 9 von 18 Shards nach 45 min | Schranke ≤ 76,6 h je Grenze |
| C-3 | Orion | `221a3a7` | 178/180 | 2 Lorenz-Nachzügler |
| WP-T1f | Orion | `1db1193` | 28/36 | 58 IC1 langsam |

## 2. Unterbrochen

- **WP-N39 (PySR, R-10):** Codex hat das Nutzungslimit erreicht, wieder verfügbar **ab 18:58**. Die
  Spezifikation steht in `codex/CURRENT_TASK.md` (committet `b2ab762`). Uncommittet im Tree liegt eine
  Teiländerung an `baselines/harness.py`, und `codex/STATUS.md` steht noch auf `working`. Nach 18:58
  neu starten. Codex macht dann an derselben Stelle weiter (Hinweis „weiterarbeiten“ ist in der Spec nicht
  nötig, der Tree ist die Wahrheit).

## 3. Nächste Schritte (Claude)

1. ODEFormer-Lauf prüfen: alle `hash_verified`, Zeilen = 20 × 4 × 3. Vergleichstabelle der Stufenzellen
   (EvoGrow / SINDy / Weak-SINDy / ODEFormer, beide Metriken). DIARY.
2. B-03 einsammeln, `aggregate_c8_oracle_bounds.py` über B-02 + B-03 (n = 144) → Bericht Tor B3.
3. Nach 18:58: Codex auf WP-N39, dann den PySR-Smoke (Image bauen lassen bzw. lokal).
4. Stufe 3 einsammeln, wenn fertig → Bericht Tor S3.
5. Wenn C-3 fertig ist: P-02. Statusseite nach jedem Statuswechsel.

## 4. Wartet auf den Nutzer

- Tor S3 (nach Stufe 3), Tor B3 (nach B-03).

## 5. Befunde heute (alle im DIARY 02.10.)

- Unter Rauschen ist die Stufenkappe auf allen fünf Stufen-Systemen (1, 17, 18, 24, 41) `nothing`.
  Ein ungekappter Arm ist dort identisch und wurde gestrichen.
- B-02 (dim 1/2, vorläufig): Bei ∞ reißt das Aufwandskriterium (×1,61 > 1,5), 1000 hält es (×1,47).
- Das alte ODEFormer-Vergleichsskript (`compare_odeformer_equivalence.py`) verdichtet volle Raster auf
  eine Konfiguration je Zelle. Für die zitierten Ergebnisse folgenlos (REPORT_WP_N38), das Skript
  bleibt unverändert.

## 6. Git

GitHub und GitLab stehen auf `5dd1df8`. Lokal liegen darüber Doku, Spezifikationen, WP-N37 und WP-N38
(Manifeste und Python, kein Skript im Image geändert). Ein neuer Image-Build ist nicht nötig.
