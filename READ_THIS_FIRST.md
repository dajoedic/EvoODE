# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-02, 13:40 — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **Q8-Probe** Orion (`512dd5b`, 75 Shards) | 73/75; Shards 1 und 7 (System 58 IC 2, σ 0,05, ρ 0,5; C1000 / A1000) seit 00:05, schreiten voran | technische Prüfung, Probe-Auswertung, dann W-2 |
| **Q7-Fits** Orion (338 Shards, 16 Pods) | 102/338 um 13:40, 0 Fehler | einsammeln, Q7-Aggregation, **G-Q7** |
| **C-6 gekappt** Orion (24 Pods) | 1.387/3.366 | weiterlaufen lassen; Blindregel |

Lokal läuft nichts.

## 2. Heute erledigt

- **§5.5 MATLAB** (R2026b, 30-Tage-Testlizenz + Statistics Toolbox): Port nicht identisch (W1 4.359/4.557, W1-interp
  4.395/4.536). Nutzerentscheidung: WSINDy-Zeilen auf gleichmäßigem Gitter **aus dem Original** (`e004aaa`).
- **WP-FA10** (`ad432cd`): MATLAB-Zeilen komplett (4.536 + 4.536), Kontrollen bestanden (keine Schwellenkippung),
  Q7/Q8-Aggregation liest sie per Default. Ursache der Port-Abweichung: Lösungswahl bei rangdefekten Matrizen
  (`gelsy` vs QR), 5 Fälle offen. DIARY 02.11.
- **W-6b** im Plan (`13bb3c0`): vor Einreichung alle MATLAB-Zeilen mit echter Lizenz (JKU) nachrechnen.

## 3. Als Nächstes

1. **WSINDy-Zahlen öffnen?** Sie sind seit Q5-W versiegelt bis §5.5; mit den Original-Zeilen entfällt der Grund —
   Öffnen ist eine Nutzerentscheidung.
2. Q8-Probe fertig → technische Prüfung, Auswertung; W-2 starten (Nutzer `oc apply`).
3. Q7 fertig → Aggregation (mit `--wsindy-source matlab`), G-Q7.

> **BLINDREGEL C-6** gilt unverändert: keine C-6-EvoGrow-Ergebnisse ansehen, nur technische Prüfung.

**Feste Regeln:** Claude pusht nie nach GitLab, nach GitHub nur mit ausdrücklicher Erlaubnis. Keine harten Zeit-Cuts.
MATLAB nur MATLAB (kein Octave): `C:\Program Files\MATLAB\R2026b\bin\matlab.exe`. Orion-Login abgelaufen →
`oc login --web https://api.orion.scch.at:6443`. Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (VPN).
Codex: `codex exec -s workspace-write -c 'windows.sandbox="unelevated"' "Lies codex/CODEX_PROTOCOL.md und arbeite den
Auftrag in codex/CURRENT_TASK.md ab." < /dev/null` (Hintergrund).
**Uncommittet, nicht von Claude:** WP-N48b-Dateien (PySR, pausiert nach §9.4d) und `output/`.

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 11 (02.11., 00:09).
