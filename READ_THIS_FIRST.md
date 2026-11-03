# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-04, 00:45 — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft (Orion, Stand 04.11. 00:44)

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **Q7-Fits** (338 Shards) | **335/338**, 0 Fehler; 3 Nachzügler laufen (einer seit 31.10.) | einsammeln, Q7-Aggregation (`--wsindy-source matlab`), **G-Q7** |
| **W-2 = Q8-Gitter** (`512dd5b`, 3.540 Shards) | 91/3.540, 0 Fehler, **36 Pods** | Hochrechnung, sobald die langen Shards durch sind (frühestens 04.11.) |
| **C-6 gekappt** | 1.434/3.366, Parallelität 1 (Zelle 1361, seit 31.10.); **wird leergezogen** (W-Reihe hat Vorrang) | nach W-4 zurück auf 24 |

Kerne: 1 + 3 + 36 = 40, voll belegt. Q8-Probe (75/75) fertig.

**Lokal läuft `shift_pods.sh`** (Scratchpad der Sitzung `9f46954f…`, detached, Log `shift_pods.log`, neue Version mit
Schutzregel): pro fertiger C-6-Zelle C-6-Parallelität −1; Q8 = 40 − C-6 − aktive Q7-Pods (nur steigend); stoppt, wenn
C-6 `failed` sich ändert. Zuletzt: 03.11. 21:51 Q8 35 → 36. Braucht Laptop an + VPN + gültigen oc-Login (VPN-Ausfall
03.11. 16:58–21:04: nichts verschoben, nichts gelöscht). **C-6 NICHT „reparieren“.** Neu starten (nur diese Version), Git Bash:
`/c/Users/joedicke/AppData/Local/Temp/claude/c--Users-joedicke-Documents-Repositories-EvoODE/9f46954f-0bf8-4401-ad3b-884a094e8a73/scratchpad/shift_pods.sh >> /c/Users/joedicke/AppData/Local/Temp/claude/c--Users-joedicke-Documents-Repositories-EvoODE/9f46954f-0bf8-4401-ad3b-884a094e8a73/scratchpad/shift_pods.log 2>&1 &`
**Rückweg nach W-4:** `oc patch job evoode-phase-c-c6-grid-capped -n scch-das -p '{"spec":{"parallelism":24}}'`;
automatischer Rückweg als Cluster-Pod noch zu bauen.

## 2. WISP-Explorable (W-X)

- Preview https://claude.ai/artifact/XsxgvgYGZdqPkpnzVd2YMQ **Version 16** (`344c52f`): Einführung (2 Seiten) +
  **Kapitel 1 „Ein Baustein allein“ als Scroll-Geschichte in 12 Schritten** — eine persistente, animierte Grafik, nur
  Scrollen (Messwerte → Rauschen → Steigung → Steigung aus zwei Punkten → längere Abschnitte → Fehler ohne Baustein →
  Fit mit Sweep → alle Bausteine → warum Rauschen → Rauschschätzung mit Summe → Prozent → erste Lösung).
- Alle späteren Seiten sind **ausgeblendet** (eine Liste im Quelltext, `pages.js`), nicht gelöscht.
- **Offen:** Nutzer will die Aufteilung „Rauschen / vom Baustein erklärt / noch erklärbar“ (Schritt 11) genauer
  besprechen. Danach Kapitel 2 („noch einer dazu“), erst nach seiner Freigabe von Kapitel 1.
- Arbeitsweise: Nutzer geht Kapitel für Kapitel durch; Claude prüft jeden Schritt per Edge-Headless-Frames zu mehreren
  Zeitpunkten und behebt eigene Funde vor dem Veröffentlichen. Build: `build_wisp_explainer_html_x2.py`; Tests
  `python -m pytest analysis/tests/ -q -p no:cacheprovider -k wisp` (51); Fit `check_wisp_explainer_fit.py`.
- Codex-Pakete WP-X7 … WP-X12d committet; `codex/CURRENT_TASK.md` = WP-X12d (erledigt).

## 3. Als Nächstes

1. Q7 fertig → einsammeln, Aggregation, **G-Q7** (automatisch nach §5-Regel, Claude berichtet).
2. W-2 läuft; Hochrechnung aus den ersten langen Shards.
3. Explorable: Schritt 11 mit dem Nutzer besprechen, dann Kapitel 2.

> **BLINDREGEL C-6** gilt unverändert: keine C-6-EvoGrow-Ergebnisse ansehen, nur technische Prüfung.

**Feste Regeln:** Claude pusht nie nach GitLab, nach GitHub nur mit ausdrücklicher Erlaubnis. Keine harten Zeit-Cuts.
MATLAB nur MATLAB (kein Octave): `C:\Program Files\MATLAB\R2026b\bin\matlab.exe`. Orion-Login abgelaufen →
`oc login --web https://api.orion.scch.at:6443`. Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (VPN).
Codex: `codex exec -s workspace-write -c 'windows.sandbox="unelevated"' "Lies codex/CODEX_PROTOCOL.md und arbeite den
Auftrag in codex/CURRENT_TASK.md ab." < /dev/null` (Hintergrund); ein per TaskStop angehaltener Lauf kann als
verwaister Prozess weiterlaufen — prüfen und dessen halbe Änderungen zurücksetzen. Nutzer erlaubt Claude auch, selbst zu
implementieren (03.11.).
**Uncommittet, nicht von Claude:** WP-N48b-Dateien (PySR, pausiert nach §9.4d) und `output/`.

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 11 (02.11., 00:09).
