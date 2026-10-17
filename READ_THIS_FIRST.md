# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-17, 23:15. Side-Projekt „Residual-Wachstum“: Q1–Q3 abgeschlossen und positiv (σ = 0); Q4
(Modellgröße ohne Orakel) läuft — dim 1/2 auf dem Laptop fertig, dim 3/4 seit 22:56 als Orion-Job. Nutzer hat
Feierabend gemacht; Auswertung von Q4 gemeinsam und in Ruhe.**

> **BLINDREGEL C-6 (Nutzer, 05.10., „Weg 2“):** Bis die Entscheidungsregel für Story-Linie (b) mit dem Nutzer
> festgelegt und als Plan §9.4d eingefroren ist, sieht sich Claude **keine C-6-EvoGrow-Ergebnisse** an — weder
> R², noch Struktur, noch Vergleiche mit SINDy. Erlaubt ist nur Einsammeln und **technische** Prüfung (Zellenzahl,
> `error`/`failure_reason`, Fingerprint, Daten-Hashes). Die Story-Diskussion folgt, wenn **alles** vom Cluster
> durchgelaufen ist; zuerst die Regel festlegen, dann die Zahlen öffnen.

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts — auch keine Tool-Zeitlimits** (Nutzer 05.10.: lange Läufe abgekoppelt starten, Abbruch nur
gemeinsam). Gilt auch für Skripte, die Codex schreibt (WP-FA3 hatte einen 15-min-Timer eingebaut). Orion-Ergebnisse
unter `S:\BigDataOrion\data-science\joedicke\` (nur mit VPN). Orion-Login abgelaufen → `oc login --web
https://api.orion.scch.at:6443`.
**Codex startet Claude selbst:** `codex exec -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag
in codex/CURRENT_TASK.md ab." < /dev/null` (`run_in_background`). Modell seit 17.10. **`gpt-6.1-sol`** in
`~/.codex/config.toml` (`gpt-5.5` ist ausgelaufen). Codex kann kein Julia ausführen: Julia-Teile parst und startet
Claude (`Meta.parseall` zuerst). **Vor jedem Docker-Build `df -h /c` (< 30 GB → erst aufräumen).** Diese Datei bei
jedem Statuswechsel aktualisieren.

---

## 1. Was läuft — Orion, **40 / 40 Kerne** (24 + 8 C-6, 8 Side-Projekt Q4)

| Lauf | Stand | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **Side-Projekt Q4, dim 3/4** — Job `evoode-sideproject-q4`, Image `e70eeea`, 19 indizierte Pods, 8 parallel, 4 Gi, kein Deadline | Start 17.10. 22:56; nach 1 min 33 Datensätze, technisch sauber | ~5–8 h → 18.10. früh (~19 Kern-h, Unsicherheit bis ×2; längste Einheiten sys 61, 55) | 429 Datensätze in `sideproject_q4_e70eeeaa…/out/index_*.jsonl` → nach `outputs/sideproject_q4_e70eeea/out/` kopieren; Plattformkontrolle `sys0024_ic1` (3 Fits, muss bit-identisch zum Laptop sein); dann Aggregation (Befehl unten) |
| **C-6-Raster gekappt** (3.366, 24 Pods) | 855 (Zählung 17.10. 00:15) | ~8.–15. Nov. + Nachlauf | einsammeln, technische Prüfung (Blindregel) |
| **C-6-Raster ungekappt, Seed 42** (461, 8 Pods) | 211 (Zählung 17.10. 00:15) | ~27. Okt. bis Anfang Nov. | Nutzer entscheidet Seed 123/7; dann 16 Kerne frei |

Q4-Aggregation nach dem Einsammeln (Laptop-Datei + Orion-Dateien, erwartet `duplicates_compared = 3`):
`python analysis/scripts/aggregate/aggregate_sideproject_q4.py --input outputs/sideproject_q4_path_fits/results.jsonl "outputs/sideproject_q4_e70eeea/out/index_*.jsonl"`
— prüfen, wie das Skript den Ausgabeort wählt und dass es keine vorhandenen Tabellen überschreibt.

Lokal läuft nichts. **Ungepusht:** `e72d3bb` und dieser Commit (pusht der Nutzer; GitHub reicht, kein neues Image
nötig). Ungetrackt im Repo-Wurzelverzeichnis: zwei Literatur-PDFs und die Skizze
`sideprojekt_residualgesteuertes_strukturwachstum.md` des Nutzers, bewusst nicht committet.

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 2 (17.10. 22:56) mit Q4.
Quelle im Scratchpad dieser Sitzung; sonst per Artifact `read` holen und darauf aufbauen. Nach dem Q4-Ende neu
veröffentlichen (Q4 fertig, 8 Kerne frei).

## 2. Side-Projekt „Residual-Wachstum“ — Stand (Details DIARY 17.10.)

Protokolle (eingefroren vor jeder Rechnung): `docs/sideproject_residual_growth_protocol.md` (Q1/Q2, `e61f48f`),
`_q3.md` (`c81e7c6`), `_q4.md` (`24ede2d`, vom Nutzer freigegeben). Daten: `analysis/data/sideproject_residual_growth/`.

- **WP-FA1** C-1-Strukturinventur: reines Hinzufügen würde 22 von 354 Gleichungen reparieren; meist fehlt etwas
  **und** ist etwas Falsches da. Zwischenstrukturen speichert C-1 nicht.
- **Q1/Q2 (WP-FA2), R1–R4 bestehen** in dim 1, 2, 3 fittbar: Wahrheit im schwachen Raum auf einer Trajektorie
  identifizierbar; von C-1-Endstrukturen aus mit Hinzufügen + Refit + Entfernen erreichbar (Orakelgrößen).
- **Q3 (WP-FA3), R5/R6 bestehen:** ein Fit vom schwachen Start schlägt zehn Zufallsstarts auf der wahren Struktur
  (dim 2: 20/20 gegen 39/60); System 61 unter Schranke 10 lösbar (in CLAUDE.md nachgetragen).
- **Q4 (WP-FA4/4b/4c) läuft:** Wachstumspfad + Trajektorien-BIC (primär); R7 gegen C-1, **R8 gegen Weak-SINDy-Median
  entscheidet**, R9 = bringt die Simulation etwas. dim 1/2: `outputs/sideproject_q4_path_fits/results.jsonl` (404
  Datensätze, nicht ausgewertet).
- **Neuheit (Nutzer):** nicht das Residual-Ranking (FROLS), sondern falls es gelingt die Kombination aus inkrementellem
  Wachstum, schwacher Regression und simulativer Prüfung. Reihenfolge: Q3 → Q4 → Rauschen.

**Nicht vergessen:** 20 Dateien unter `src/`, `studies/`, `benchmarks/` haben im Working Tree CRLF/gemischte
Zeilenenden (Index LF). Erst **nach** der Q4-Auswertung normalisieren, sonst sind die Laptop-Hashes nicht mehr prüfbar.

## 3. Als Nächstes — wartet auf den Nutzer

1. **Q4 gemeinsam auswerten** (R7–R9, dann Entscheidung über Rauschen).
2. **Fehleranatomie** (Diskussionspapier `docs/diskussion_warum_scheitert_die_suche.md`): Ergebnis der externen
   Diskussion steht aus; Q3 hat Klasse B auf der Wahrheit bereits beantwortet.
3. **Tor T2a-1:** Stopp der Führungsspur oder S2 (S1: p = 0,25 nach eingefrorener Regel).
4. **Entscheidungsregel (b) als §9.4d**, erst dann C-6-EvoGrow öffnen. **Paper 1 ist nicht fix (Nutzer 14.10.).**

## 4. Annihilator-Spur: getrennt (Nutzer, 05.10.)

Die Methodenspur „Idee #1“ lebt **nur** im Ordner `..\EvoODE-next` (Branch `annihilator-discovery`), als eigenes
VS-Code-Projekt mit eigener `CLAUDE.md`, eigenem `READ_THIS_FIRST.md` und eigenem `DIARY.md`. Sie wird in Sitzungen
dieses Ordners nicht bearbeitet. Stand dort: Gate 2A v3, K6 würde auslösen, die Grundsatzentscheidung des Nutzers
ist offen.
