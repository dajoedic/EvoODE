# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-03, nachmittags.** Arbeitsreihenfolge: Backlog in `CLAUDE.md` („Backlog Paper 1“).

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts.** Orion-Ergebnisse liegen lokal unter `S:\BigDataOrion\data-science\joedicke\`
(Git Bash `/s/BigDataOrion/...`, nur mit VPN). **Codex startet Claude immer selbst:**
`codex exec -C "C:/Users/joedicke/Documents/reps/EvoODE" -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null`
als `run_in_background`. **Diese Datei bei jedem Statuswechsel aktualisieren.**

---

## 1. Was läuft

| Lauf | Wo | Image | Stand | Anmerkung |
|---|---|---|---|---|
| B-03 (Orakel dim 3/4) | Orion | `5dd1df8` | 10: 54/54, 1000: 54/54, ∞: 52/54 | Letzter Shard seit 11 h, Schranke ~15 h |
| C-3 | Orion | `221a3a7` | 179/180 | |
| WP-T1f | Orion | `1db1193` | 30/36 | |

**PySR-Smoke fertig (03.10.):** beide Versionen dasselbe Modell (`-0,2993·x_0`, Konstante fehlt), 1.5.9 doppelt so teuer. Ausgabe `outputs/wp_n39_pysr_smoke/`. **Wartet auf den Nutzer: welche PySR-Version für C-7** (DIARY 03.10.).

**Plattenvorfall 03.10.:** C: lief auf 0 Byte voll (Docker-vhdx 57 GB, davon 37 GB Build-Cache). Behoben:
Cache geleert, alte Images gelöscht (`evoode-regression:h2/h5`, `odeformer-*:wp-n21`, Nutzer-OK), die
vhdx hat der Nutzer als Admin kompaktiert (57 → 13 GB). **Jetzt 57 GB frei.** Regel: vor jedem Build
`df -h /c` (unter 30 GB erst aufräumen), danach `docker builder prune -af`.

Committet (`a30382b`): `baselines/requirements-pysr-legacy.txt` (`juliacall` 0.9.24 → 0.9.23, Pflicht für PySR
0.19.4). `docs/WP-N39.md` nennt an zwei Stellen noch 0.9.24 für Legacy und muss nachgezogen werden.

## 2. Wartet auf den Nutzer

- **Tor S3:** Stufe 3 ist fertig. Danach kommt Tor G (Rasterentscheidung C-6) mit den Kostenfaktoren aller Stufen.
- **Tor B3**, sobald B-03 komplett ist.
- **PySR-Version für C-7:** 0.19.4 (wie ODEFormer, halb so teuer) oder 1.5.9. Der Smoke zeigt dasselbe Modell.

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
