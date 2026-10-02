# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-03, vormittags.** Arbeitsreihenfolge: Backlog in `CLAUDE.md` („Backlog Paper 1“).

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts.** Orion-Ergebnisse liegen lokal unter `S:\BigDataOrion\data-science\joedicke\`
(Git Bash `/s/BigDataOrion/...`, nur mit VPN). **Codex startet Claude immer selbst:**
`codex exec -C "C:/Users/joedicke/Documents/reps/EvoODE" -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null`
als `run_in_background`. **Diese Datei bei jedem Statuswechsel aktualisieren.**

---

## 1. Was läuft

| Lauf | Wo | Image | Stand | Anmerkung |
|---|---|---|---|---|
| WP-N39 Fortsetzung 3 (PySR 0.19.x **und** 1.5.9) | Codex, lokal | — | `working` | Danach baut Claude beide Images und fährt den Smoke auf beiden (Nutzer: „beides testen und reporten“) |
| B-03 (Orakel dim 3/4) | Orion | `5dd1df8` | 10 und 1000 komplett, ∞ 17/18 | Danach einsammeln und Tor-B3-Bericht |
| C-3 | Orion | `221a3a7` | 179/180 | 1 Lorenz-Nachzügler |
| WP-T1f | Orion | `1db1193` | 30/36 | |

**Fertig seit gestern:** Stufe 3 (System 41) eingesammelt und ausgewertet (DIARY 03.10.).
ODEFormer auf allen Stufenzellen (WP-N38, `outputs/wp_n38_noise_odeformer/stages/`).

## 2. Wartet auf den Nutzer

- **Tor S3:** Stufe 3 ist fertig. Danach kommt Tor G (Rasterentscheidung C-6) mit den Kostenfaktoren aller Stufen.
- **Tor B3**, sobald B-03 komplett ist.
- Die Entscheidung zur PySR-Version fällt nach dem Smoke beider Varianten.

## 3. Nächste Schritte (Claude)

1. B-03 einsammeln (NFS), `aggregate_c8_oracle_bounds.py` über B-02 + B-03 (n = 144) → Bericht Tor B3.
2. WP-N39 abnehmen, beide PySR-Images bauen, Smoke System 1 (σ 0,01; ρ 0) auf beiden, Bericht.
3. Gemeinsame Tabelle der Stufenzellen: EvoGrow / SINDy / Weak-SINDy / ODEFormer (/ PySR), beide Metriken.
4. ODEFormer-Strukturtreffer im Referenz- und Kandidatenraster nachrechnen (WP-N38-Modus), dann WP-N31 neu aggregieren.
5. Wenn C-3 fertig ist: P-02. Statusseite und diese Datei nach jedem Statuswechsel.

## 4. Befunde (DIARY 02./03.10.)

- Unter Rauschen ist die Stufenkappe auf allen fünf Stufen-Systemen `nothing`. Der ungekappte Arm entfällt.
- Rauschkosten folgen der C-1-Levelzahl: ×0,7–1,15, wo C-1 viele Level lief, ×13,7 bei System 24.
- System 41 divergiert unter Rauschen von der sauberen IC aus, ODEFormer scheitert dort auch.
- ODEFormer-Strukturtreffer waren nie berechnet (WP-N31-Strukturraten ungültig, R² nicht betroffen).
- B-02 vorläufig: ∞ reißt das Aufwandskriterium (×1,61), 1000 hält es (×1,47).

## 5. Git

GitHub und GitLab stehen auf `5dd1df8`. Lokal liegen darüber Doku, Spezifikationen und WP-N37–N39
(Manifeste, Python, Dockerfiles; kein Skript im Kampagnen-Image geändert).
