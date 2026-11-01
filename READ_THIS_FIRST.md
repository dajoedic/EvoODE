# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-02, kurz nach Mitternacht — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **Q7-Fits** Orion (`evoode-sideproject-q7`, 338 Shards, **16 Pods**) | 27/338 am 01.11. 23:05, 0 Fehler | einsammeln (`out/` auf NFS, robocopy), offizielle Q7-Aggregation, **G-Q7** nach Q7 §5 |
| **C-6 gekappt** Orion (24 Pods) | 1.370/3.366, ~24 Zellen/Tag → Ende ~Ende Januar | weiterlaufen lassen (Nutzer); nicht verkleinern (tötet Pods) |
| **Codex WP-FA9** (Q8-Umsetzung), lokal, gestartet 02.11. 00:07 | läuft | Julia parsen + Smoke (Befehle im Report), prüfen, committen; Nutzer pusht → Image; Probe |

Orion: 40/40 Kerne. Q5 fertig und vom Cluster entfernt (TTL).

## 2. Seit gestern erledigt

- **Q5 offiziell aggregiert** (`7f1a142`): Tabellen `analysis/data/sideproject_residual_growth/q5_grid/`, DIARY 01.11.
  Zwei technische Nachträge über einen Wrapper im Scratchpad (Protokoll-Hash bei `f454a32`; Referenzfilter für
  (0, 0,5)); Skriptkorrektur ist Scope 7 von WP-FA9.
- **Q7-Zwischenblick** (Nutzerwunsch, DIARY 01.11., `1d28d9a`/`da2bb8c`): dim 1 endgültig, Q7 klar besser als Q5 und
  WSINDy; WSINDy nur auf dim 3 / ρ = 0 bei der Struktur vorn. Vorläufig.
- **Q8-Protokoll eingefroren** (`d2abf7f`, Tor G1 bestanden): A/C × Schranke 10/1000, dim 1/2 alle 51 Systeme,
  dim-3-Stichprobe 52, 61, 54–59, Ablationen auf C1000; Regeln R2 → R1 → R3 nur auf dim 1/2.

## 3. Als Nächstes

1. WP-FA9 prüfen, Julia-Smoke, committen; Nutzer pusht nach GitLab (Image), dann Q8-Probe auf Orion.
2. Q7 fertig → aggregieren, G-Q7 berichten (Q8 hängt am Pfadende).
3. MATLAB-Lizenz (IT) → §5.5-Abgleich Q5-W (Befehle im DIARY 31.10. / altem Stand).

> **BLINDREGEL C-6** gilt unverändert: keine C-6-EvoGrow-Ergebnisse ansehen, nur technische Prüfung.

**Feste Regeln:** Claude pusht nie nach GitLab, nach GitHub nur mit ausdrücklicher Erlaubnis. Keine harten Zeit-Cuts.
Orion-Login abgelaufen → `oc login --web https://api.orion.scch.at:6443`. Orion-Ergebnisse unter
`S:\BigDataOrion\data-science\joedicke\` (VPN). Codex: `codex exec -s workspace-write -c 'windows.sandbox="unelevated"'
"Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null` (Hintergrund).
**Uncommittet, nicht von Claude:** WP-N48b-Dateien (PySR, pausiert nach §9.4d) und `output/`.

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 11 (02.11., 00:09).
Lokale Quelle im Sitzungs-Scratchpad (`orion_status.html`); bei jeder Änderung per Artifact `read` holen und darauf
aufbauen.
