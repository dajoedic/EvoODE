# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

> ## WISP-Explorable, Stand 03.11. 23:45
> Preview https://claude.ai/artifact/XsxgvgYGZdqPkpnzVd2YMQ Version 15 (`281d67b`): Einführung (2 Seiten) + Kapitel 1 als
> Scroll-Geschichte (11 Schritte, eine animierte Grafik, nur Scrollen). Später Kapitel ausgeblendet (eine Liste im
> Quelltext). Offen: Nutzer will die Aufteilung „Rauschen / vom Baustein erklärt / noch erklärbar“ (S10) noch genauer
> besprechen; Kapitel 2 („noch einer dazu“) erst nach seiner Freigabe. Build: `build_wisp_explainer_html_x2.py`.

> ## ⚠️ ACHTUNG: C-6 WIRD LEERGEZOGEN — PODS WANDERN AUTOMATISCH ZUR W-REIHE
> **Seit 02.11. 23:58 (Nutzer: W-Reihe hat absolute Priorität).** Das Skript `shift_pods.sh` (Scratchpad dieser Sitzung,
> detached, Log `shift_pods.log`) senkt bei **jeder fertigen C-6-Zelle** die C-6-Parallelität um 1 und hebt W-2 (Q8)
> auf 40 − C-6 − aktive Q7-Pods. **Ziel: C-6 auf 0, alle 40 Kerne für W-2, danach W-4.** Kein laufender Pod wird getötet.
> - **C-6 NICHT „reparieren“**, auch wenn seine Parallelität < 24 ist — das ist gewollt.
> - Erste Verschiebung geprüft 03.11. 00:07: C-6 24 → 23, Q8 6 → 7, C-6 `failed` = 0, kein Pod beendet.
> - **Vorfall 03.11. 11:48:** nach Token-Ausfall (06:37–11:48) holte das alte Skript 8 verpasste Fertigmeldungen auf
>   einmal nach (C-6 9 → 1); der Controller hatte nachgefüllt, also wurden **8 laufende Pods gelöscht**, 6 davon 55–73 h alt
>   (~390 Kern-h). DIARY 03.11. **Neue Version mit Schutzregel** (nie unter die Zahl der > 10 min laufenden Pods).
>   Stand danach: C-6 1 (Zelle 1361, seit 31.10.), Q7 7, Q8 32.
> - Braucht Laptop an + VPN + gültigen oc-Login; läuft es nicht, wird nur nichts verschoben. Neu starten
>   (nur die neue Version!) in Git Bash: `/c/Users/joedicke/AppData/Local/Temp/claude/c--Users-joedicke-Documents-Repositories-EvoODE/9f46954f-0bf8-4401-ad3b-884a094e8a73/scratchpad/shift_pods.sh >> /c/Users/joedicke/AppData/Local/Temp/claude/c--Users-joedicke-Documents-Repositories-EvoODE/9f46954f-0bf8-4401-ad3b-884a094e8a73/scratchpad/shift_pods.log 2>&1 &`
> - **Rückweg nach W-4:** C-6 wieder auf 24 (`oc patch job evoode-phase-c-c6-grid-capped -n scch-das -p '{"spec":{"parallelism":24}}'`);
>   automatischer Rückweg als Cluster-Pod (Codex) noch zu bauen.

**Stand: 2026-11-03, 00:15 — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **Q8-Probe** Orion (`512dd5b`, 75 Shards) | **fertig 75/75**, technisch sauber, 36 h statt geplanter 98–221 h (DIARY) | — |
| **Q7-Fits** Orion (338 Shards, 16 Pods) | 328/338 um 23:25, 0 Fehler; 10 laufen, 4 davon seit 31.10. (Nachzügler bestimmen das Ende) | einsammeln, Q7-Aggregation, **G-Q7** |
| **W-2 = Q8-Gitter** Orion (`512dd5b`, 3.540 Shards) | **gestartet 02.11. 23:35 mit 6 Pods** (frei gewordene Q7-Kerne; Nutzer: Start vor G-Q7, Risiko akzeptiert) | nach Q7 auf 16 hochziehen: `oc patch job evoode-sideproject-q8 -n scch-das -p '{"spec":{"parallelism":16}}'` |
| **C-6 gekappt** Orion | 1.411/3.366; **wird seit 02.11. 23:58 leergezogen** (Nutzer: W-Reihe hat Vorrang) | nach W-4 Parallelität zurück auf 24 |

**Lokal läuft:** `shift_pods.sh` (Scratchpad, detached, Log `shift_pods.log`): pro fertiger C-6-Zelle C-6-Parallelität −1,
Q8-Parallelität = 40 − C-6 − aktive Q7-Pods (nur steigend); stoppt, wenn C-6 `failed` sich ändert. Braucht Laptop an,
VPN, gültigen oc-Login; fällt es aus, wird nichts verschoben; die alte Version hat beim Wiederanlauf laufende Pods gelöscht (Vorfall 03.11.), die neue nicht mehr. Rückweg nach W-4
noch zu bauen (Cluster-Pod, Codex).

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
