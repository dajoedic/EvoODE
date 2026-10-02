# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-02, ~14:30.** Arbeitsreihenfolge: Backlog in `CLAUDE.md` („Backlog Paper 1“).

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis,
beides macht der Nutzer. **Keine harten Zeit-Cuts.** `codex exec` immer mit `< /dev/null`.
Orion-Ergebnisse liegen lokal lesbar unter `S:\BigDataOrion\data-science\joedicke\` (Git Bash:
`/s/BigDataOrion/...`). Einsammeln geht ohne `oc exec`, der Jobstatus braucht `oc login`.

---

## 1. Was läuft

| Lauf | Wo | Image | Stand | Anmerkung |
|---|---|---|---|---|
| C-3 | Orion | `221a3a7` | 178/180 | 2 Lorenz-Nachzügler (Index 14, 22) |
| WP-T1f | Orion | `1db1193` | 28/36 | 58 IC1 langsam |
| Stufe 3 (System 41, gekappt) | Orion | `5dd1df8` | 0/2, seit ~14:20 | Smoke bitgleich. Erwartet ~8–17 h je Zelle. Kappe unter Rauschen `nothing`, deshalb kein ungekappter Arm |
| B-03 (Orakel dim 3/4, 3 Grenzen) | Orion | `5dd1df8` | läuft | 3 × 18 Shards, Schranke ≤ 76,6 h je Grenze |

Die Pods starten kurz mit `Error` (Index-Datei fehlt), solange der Bootstrap läuft. Das ist harmlos,
der Backoff fängt es auf.

## 2. Wartet auf den Nutzer

- Tor S3, sobald Stufe 3 fertig ist. Tor B3, sobald B-03 fertig ist.

## 3. Nächste Schritte (Claude)

1. Stufe 3 einsammeln (NFS), Clean-Auswertung je Bedingung (`by_condition/`), Stufenbericht → Tor S3.
2. B-03 einsammeln, `aggregate_c8_oracle_bounds.py` über B-02 und B-03 (n = 144) → Tor B3.
3. Arbeitspakete ODEFormer auf Rausch-Daten (R-09) und PySR (R-10).
4. Wenn C-3 fertig ist: P-02.
5. Statusseite nach jedem Statuswechsel.

## 4. Git

GitHub und GitLab stehen auf `5dd1df8`. Lokal liegen darüber Doku, Spezifikationen und WP-N37
(Manifeste und Python, kein Skript im Image geändert). Ein neuer Image-Build ist nicht nötig.
