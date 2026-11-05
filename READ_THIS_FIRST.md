# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-11-05, 01:15 (Explorable und Cluster) — WISP-Plan bis 31.12. (CLAUDE.md, „WISP paper — the fixed plan“).**

## 1. Was läuft (Orion, Stand 05.11. 01:15)

| Lauf | Stand | Wenn fertig |
|---|---|---|
| **Q7-Fits** (338 Shards, `3541063`) | **337/338**, 0 Fehler; 1 Nachzügler läuft | einsammeln, Q7-Aggregation (`--wsindy-source matlab`), **G-Q7** |
| **W-2 = Q8-Gitter** (`512dd5b`, 3.540 Shards) | **265/3.540**, 0 Fehler, **39 Pods** (seit 02.11. 23:41) | Hochrechnung, sobald die langen Shards durch sind |
| **C-6 gekappt** | 1.435/3.366, **Parallelität 0 seit 04.11. 10:26** (leergezogen, kein Pod getötet) | nach W-4 zurück auf 24 |

Kerne: 39 + 1 + 0 = 40, voll belegt. Q8-Probe (75/75) fertig. Statusseite „EvoODE auf Orion“ Version 12 (05.11. 01:15).
oc-Token war 05.11. ~01:07 abgelaufen, Nutzer hat sich neu eingeloggt; in der Lücke hat `shift_pods.sh` nur Lesefehler
geloggt und nichts verändert.

**Lokal läuft `shift_pods.sh`** (Scratchpad der Sitzung `9f46954f…`, detached, Log `shift_pods.log`, neue Version mit
Schutzregel): pro fertiger C-6-Zelle C-6-Parallelität −1; Q8 = 40 − C-6 − aktive Q7-Pods (nur steigend); stoppt, wenn
C-6 `failed` sich ändert. Zuletzt: 04.11. 10:26 C-6 1 → 0, 17:40 Q8 38 → 39. Braucht Laptop an + VPN + gültigen oc-Login (VPN-Ausfall
03.11. 16:58–21:04: nichts verschoben, nichts gelöscht). **C-6 NICHT „reparieren“.** Neu starten (nur diese Version), Git Bash:
`/c/Users/joedicke/AppData/Local/Temp/claude/c--Users-joedicke-Documents-Repositories-EvoODE/9f46954f-0bf8-4401-ad3b-884a094e8a73/scratchpad/shift_pods.sh >> /c/Users/joedicke/AppData/Local/Temp/claude/c--Users-joedicke-Documents-Repositories-EvoODE/9f46954f-0bf8-4401-ad3b-884a094e8a73/scratchpad/shift_pods.log 2>&1 &`
**Rückweg nach W-4:** `oc patch job evoode-phase-c-c6-grid-capped -n scch-das -p '{"spec":{"parallelism":24}}'`;
automatischer Rückweg als Cluster-Pod noch zu bauen.

## 2. WISP-Explorable (W-X)

- Preview https://claude.ai/artifact/XsxgvgYGZdqPkpnzVd2YMQ **Version 20** (05.11., `411573c`): Einführung +
  Kapitel 1 „Ein Baustein allein“ (11 Schritte) + Kapitel 2 „Noch ein Baustein dazu“ (6 Schritte). Alle Animationen
  laufen in Dauerschleife (3 s Pause); kein Regler.
- **Stand Kapitel 1:** Nutzer findet es „erstmal verständlich“. Schritt 9 (Rauschen) zoomt seit Version 20 auf das
  9-Punkte-Fenster, folgt dem Durchlauf, zoomt heraus, dann die Rechnung Σd² → /n → √ → korrigiert ≈ 2,9 % → 71,6 % Boden.
- **Stand Kapitel 2:** neutral, kein Urteil, keine wahre Gleichung. Schritt 6 (neu, 05.11.) „Und so weiter, bis alle
  Bausteine drin sind“: Runde für Runde jeder offene Baustein, nur Hinzunahmen (geprüft gegen `W.path` mit
  abgeschaltetem Rückschritt), Weg 1 → +u³ → +u → +u² → +sin u → +cos u, erklärter Anteil 52,9 → 74,2 → 80,6 → 81,1 →
  81,4 → 81,5 %. Annahme: „für alle offenen Bausteine“ = Runden nach dem zweiten Baustein — Nutzer hat das noch nicht
  bestätigt.
- **Nutzerentscheidung 04.11.:** den Fehlgriff (u³ statt u², Konstante überflüssig) löst **Kapitel 3** auf (Aufräumen/FoBa:
  1 → 1,u³ → u,u³ → u,u² = Wahrheit, BIC wählt `path_004`).
- **Offen:** Nutzer prüft Version 20; Schritt 11 von Kap. 1 (Aufteilung Rauschen/erklärt/noch erklärbar) „später“.
- **Tests:** im Iterieren nur die schnellen Darstellungstests (`test_wisp_explainer_x*.py` ohne `_x2`, ~2 min) +
  `check_wisp_explainer_js.py` + `check_wisp_explainer_fit.py` (Edge, Claude startet; In-Page-Timeout seit 05.11. 60 s);
  die volle `-k wisp`-Sammlung (~30 min) nur bei Daten-/Exportänderungen, spätestens beim Q9-Tausch. So auch in Codex-Aufträge.

## 3. Als Nächstes

1. Q7 fertig → einsammeln, Aggregation, **G-Q7** (automatisch nach §5-Regel, Claude berichtet).
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

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 12 (05.11., 01:15).
