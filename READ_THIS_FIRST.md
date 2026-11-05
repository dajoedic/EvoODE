# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-05, ~10:00 (Q7 eingesammelt, G-Q7 bestanden) — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft (Orion, Stand 05.11. ~08:00)

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **Q7-Fits** (338 Shards, `3541063`) | **fertig 338/338** (05.11. 06:58), eingesammelt, aggregiert (`q7_grid/`); **G-Q7 bestanden** | — |
| **W-2 = Q8-Gitter** (`512dd5b`, 3.540 Shards) | **338/3.540** (05.11. ~08:00), 0 Fehler, **40 Pods** (seit 05.11. 07:56) | Hochrechnung, sobald die langen Shards durch sind; linear grob ~22 Tage — gegen Plan W-2 bis ~13.11. beobachten |
| **C-6 gekappt** | 1.435/3.366, **Parallelität 0 seit 04.11. 10:26** (leergezogen, kein Pod getötet) | nach W-4 zurück auf 24 |

Kerne: Q8 40, Q7 0, C-6 0 = 40, voll belegt. C-6-Job pausiert, nicht gefährdet (TTL greift erst nach Abschluss, keine Deadline, Datensätze auf NFS). Q8-Probe (75/75) fertig. Statusseite „EvoODE auf Orion“ Version 13 (05.11. ~10:00).
oc-Token war 05.11. ~01:07 abgelaufen, Nutzer hat sich neu eingeloggt; in der Lücke hat `shift_pods.sh` nur Lesefehler
geloggt und nichts verändert.

**`shift_pods.sh` hat sich 05.11. 07:56 beendet** („all 40 cores on Q8: done“); frühere Beschreibung: lokal lief `shift_pods.sh` (Scratchpad der Sitzung `9f46954f…`, detached, Log `shift_pods.log`, neue Version mit
Schutzregel): pro fertiger C-6-Zelle C-6-Parallelität −1; Q8 = 40 − C-6 − aktive Q7-Pods (nur steigend); stoppt, wenn
C-6 `failed` sich ändert. Zuletzt: 04.11. 10:26 C-6 1 → 0, 17:40 Q8 38 → 39. Braucht Laptop an + VPN + gültigen oc-Login (VPN-Ausfall
03.11. 16:58–21:04: nichts verschoben, nichts gelöscht). **C-6 NICHT „reparieren“.** Neu starten (nur diese Version), Git Bash:
`/c/Users/joedicke/AppData/Local/Temp/claude/c--Users-joedicke-Documents-Repositories-EvoODE/9f46954f-0bf8-4401-ad3b-884a094e8a73/scratchpad/shift_pods.sh >> /c/Users/joedicke/AppData/Local/Temp/claude/c--Users-joedicke-Documents-Repositories-EvoODE/9f46954f-0bf8-4401-ad3b-884a094e8a73/scratchpad/shift_pods.log 2>&1 &`
**Rückweg nach W-4:** `oc patch job evoode-phase-c-c6-grid-capped -n scch-das -p '{"spec":{"parallelism":24}}'`;
automatischer Rückweg als Cluster-Pod noch zu bauen.

## 2. WISP-Explorable (W-X)

- Preview https://claude.ai/artifact/XsxgvgYGZdqPkpnzVd2YMQ **Version 21** (05.11., `46ffca5`): Einführung +
  Kap. 1 (11 Schritte) + Kap. 2 (6) + **Kap. 3 „Aufräumen“ (FoBa, 7 Schritte)**: Kostenbalken mit Messlatte ½ Gewinn,
  Lupe, wahre Gleichung erstmals gezeigt, Gewinn je Runde. `gates.json` stop = significance (G-Q7).
- **Nutzerauftrag 05.11.: „alles fertig“, in der echten WISP-Reihenfolge** (Runde = Test Q7 → Hinzufügen → Aufräumen;
  Fit + BIC erst am Ende). Reihe: **X17 läuft** (Kap. 2 Schritt 6 raus – zeigte einen Pfad, den WISP nie geht; Kap. 4
  Aufhören/Q7 mit Rundenübersicht) → X18 Kap. 5 Fitten + Wählen → X19 Kap. 1 Schritt 11, Zwei-Gleichungs-Beispiel,
  Fehlschlag, Generalisierung → X20 Ergebnis-Explorer. Danach: Nutzer-Idee zur Visualisierung der Spiegelung
  Hinzufügen/Aufräumen (bis dahin schlicht gebaut). Kap. 5 hängt an G2 (Variante C, Grenze 1000), Ergebnisse an Q9.
- **Tests:** im Iterieren nur die schnellen Darstellungstests (`test_wisp_explainer_x*.py` ohne `_x2`, ~2 min) +
  `check_wisp_explainer_js.py`; Browser-Check `check_wisp_explainer_fit.py` startet Claude (Codex-Sandbox kann es nicht).
  Zwischenzeit-Screenshots: Playwright-Skript mit Wartezeit nach `WispSlides.nav.link`.

## 3. Als Nächstes

1. ~~Q7 einsammeln, G-Q7~~ erledigt 05.11.: Q7 ersetzt die 6-Term-Grenze in WISP (`DIARY.md`).
2. W-2 läuft; Hochrechnung aus den ersten langen Shards.
3. Explorable: Nutzer-Feedback zu Version 20, dann Kapitel 3 (Aufräumen/FoBa); Schritt 11 später.

> **BLINDREGEL C-6** gilt unverändert: keine C-6-EvoGrow-Ergebnisse ansehen, nur technische Prüfung.

**Feste Regeln:** Claude pusht nie nach GitLab, nach GitHub nur mit ausdrücklicher Erlaubnis. Keine harten Zeit-Cuts.
MATLAB nur MATLAB (kein Octave): `C:\Program Files\MATLAB\R2026b\bin\matlab.exe`. Orion-Login abgelaufen →
`oc login --web https://api.orion.scch.at:6443`. Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (VPN).
Codex: `codex exec -s workspace-write -c 'windows.sandbox="unelevated"' "Lies codex/CODEX_PROTOCOL.md und arbeite den
Auftrag in codex/CURRENT_TASK.md ab." < /dev/null` (Hintergrund); ein per TaskStop angehaltener Lauf kann als
verwaister Prozess weiterlaufen — prüfen und dessen halbe Änderungen zurücksetzen. Nutzer erlaubt Claude auch, selbst zu
implementieren (03.11.).
**Uncommittet, nicht von Claude:** WP-N48b-Dateien (PySR, pausiert nach §9.4d) und `output/`.

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 13 (05.11., ~10:00).
