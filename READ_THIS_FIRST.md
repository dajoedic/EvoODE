# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-02, 23:25 — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **Q8-Probe** Orion (`512dd5b`, 75 Shards) | **fertig 75/75**, technisch sauber, 36 h statt geplanter 98–221 h (DIARY) | — |
| **Q7-Fits** Orion (338 Shards, 16 Pods) | 328/338 um 23:25, 0 Fehler; 10 laufen, 4 davon seit 31.10. (Nachzügler bestimmen das Ende) | einsammeln, Q7-Aggregation, **G-Q7** |
| **W-2 = Q8-Gitter** Orion (`512dd5b`, 3.540 Shards) | **gestartet 02.11. 23:35 mit 6 Pods** (frei gewordene Q7-Kerne; Nutzer: Start vor G-Q7, Risiko akzeptiert) | nach Q7 auf 16 hochziehen: `oc patch job evoode-sideproject-q8 -n scch-das -p '{"spec":{"parallelism":16}}'` |
| **C-6 gekappt** Orion (24 Pods) | 1.405/3.366 | weiterlaufen lassen; Blindregel |

Lokal läuft nichts.

## 2. Heute erledigt

- **§5.5 MATLAB** (R2026b, 30-Tage-Testlizenz + Statistics Toolbox): Port nicht identisch (W1 4.359/4.557, W1-interp
  4.395/4.536). Nutzerentscheidung: WSINDy-Zeilen auf gleichmäßigem Gitter **aus dem Original** (`e004aaa`).
- **WP-FA10** (`ad432cd`): MATLAB-Zeilen komplett (4.536 + 4.536), Kontrollen bestanden (keine Schwellenkippung),
  Q7/Q8-Aggregation liest sie per Default. Ursache der Port-Abweichung: Lösungswahl bei rangdefekten Matrizen
  (`gelsy` vs QR), 5 Fälle offen. DIARY 02.11.
- **W-6b** im Plan (`13bb3c0`): vor Einreichung alle MATLAB-Zeilen mit echter Lizenz (JKU) nachrechnen.

## 3. Als Nächstes

1. Q7 fertig → einsammeln, Aggregation (mit `--wsindy-source matlab`), **G-Q7**.
2. W-2 läuft; nach Q7 Parallelität 6 → 16. Hochrechnung aus den ersten Shards. Bei G-Q7 nicht bestanden (unwahrscheinlich):
   exakte Shards neu, Cap-Fallback-Zweig (WP-FA9) erst Codex.

Erledigt 15:30: Q5-W geöffnet (MATLAB-Zeilen ändern keine Q5-Zählung), Q8-Probe geprüft — DIARY 02.11.

> **BLINDREGEL C-6** gilt unverändert: keine C-6-EvoGrow-Ergebnisse ansehen, nur technische Prüfung.

**Feste Regeln:** Claude pusht nie nach GitLab, nach GitHub nur mit ausdrücklicher Erlaubnis. Keine harten Zeit-Cuts.
MATLAB nur MATLAB (kein Octave): `C:\Program Files\MATLAB\R2026b\bin\matlab.exe`. Orion-Login abgelaufen →
`oc login --web https://api.orion.scch.at:6443`. Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (VPN).
Codex: `codex exec -s workspace-write -c 'windows.sandbox="unelevated"' "Lies codex/CODEX_PROTOCOL.md und arbeite den
Auftrag in codex/CURRENT_TASK.md ab." < /dev/null` (Hintergrund).
**Uncommittet, nicht von Claude:** WP-N48b-Dateien (PySR, pausiert nach §9.4d) und `output/`.

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 11 (02.11., 00:09).
