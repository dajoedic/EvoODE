# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-31, Nachmittag — Q5-W vorläufig ausgewertet; W1-interp fertig und Primärzeile auf ρ = 0,5 (§4a,
`9ffea6b`); Methode heißt WISP; **Q6 Stufe 1 gerechnet: Noise-Floor-Regel verworfen (T = 591/2.788), Schätzer
unverzerrt; Stufe 2 entfällt (DIARY 31.10., `683429b`)**. Pfadende = Paper-2-Kandidat (CLAUDE.md `cad8482`).
**Nächster Schritt, wenn der Nutzer so weit ist:** ein Protokoll für (1) dim 2 ohne Grenze (Pfad bis volle Basis,
~500 Kernstunden), (2) dim 3/4 Stichprobe mit Grenze 8 oder 10 als Sensitivität (6 dort als Rechenbudget erklärt;
ohne Grenze wären es ~17–55 k Kernstunden), (3) Variante C auf derselben Teilmenge. Noch nicht entschieden;
Q5: 1.630/1.632, 2 Pods laufen; MATLAB ausstehend.** WISP als Paper 1 statt EvoGrow: offen, hängt an §9.4d.
- **Portlauf:** 27.216 / 27.216 Zeilen (4.536 Zellen × 6 Konfigurationen W1/W1-cap/W2 × L-C6/L-Q5), Schlüssel
  (Zelle, Konfiguration) eindeutig, `fit_status = success` überall, 0 `fit_error`. Zusammengeführt aus 12 Shards
  (`outputs/sideproject_q5w_wsindy/full_shards/shard_*/details.csv`) nach `outputs/sideproject_q5w_wsindy/full/details.csv`.
  Letzte Zeile Sa 03:18.
- **Vorläufig geöffnet (Nutzer, 31.10. morgens, Abweichung von §7):** Auswertung gegen Q5 (1.626/1.632 Zellen) im
  DIARY 31.10.; gilt erst mit bestandenem §5.5. Fair lesbar nur ρ = 0 (W1 auf ρ = 0,5 = unsere Rasteranbindung).
- **Sobald MATLAB installiert ist (IT-Helpdesk, Lizenz ~14 Tage):** Claude startet (< 1 h-Regel)
  `matlab -batch "addpath('analysis/matlab'); run_wsindy_original_q5w(pwd, 2)"` (Probe), dann ohne Limit, dann
  `python analysis/scripts/aggregate/compare_sideproject_q5w_matlab.py --port-rows outputs/sideproject_q5w_wsindy/full/details.csv`
  → bei Bestehen entsiegeln, Q5-W-Tabellen bauen, Q5 gegen W1 vergleichen.
- **W1-interp fertig (31.10. 09:39, 4.536/4.536, 0 Fehler, `w1_interp_full/details.csv`; Ergebnis DIARY 31.10.):** Protokoll §4a (Sensitivitätsarm, W1 bleibt Primärzeile auf
  ρ = 0,5; Literatur DIARY 31.10.), WP-FA6c `9439a05`. Shards `outputs/sideproject_q5w_wsindy/w1_interp_shards/cells_{0..11}.csv`
  → `shard_{i}/`, Logs daneben, 4.536 Zeilen erwartet. Neustart eines Teils: `python analysis/scripts/aggregate/run_sideproject_q5w_wsindy.py
  --all-cells --cells …/cells_$i.csv --configurations W1-interp:L-C6,W1-interp:L-Q5 --output-dir …/shard_$i` (setzt fort).
- **Q5-Raster auf Orion** (16 Pods): Ende ~31.10. abends erwartet; Zwischenblick 1.144 / 1.632 im DIARY 30.10.
- **Kochbuch-PDFs** (Stand 27.10., ohne Q5) liegen nur im Sitzungs-Scratchpad; Nutzer kopiert sie.

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

## 1. Was läuft — Orion, **40 / 40 Kerne** (24 C-6 gekappt + 16 Q5-Raster), Stand 29.10.

| Lauf | Stand (Job-Zähler) | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **C-6-Raster gekappt** (3.366, 24 Pods) | 1.302 (29.10. 23:15) / 1.293 (29.10.); 24 Pods laufen, 0 Fehler, 0 Neustarts; ~33 Zellen/Tag seit 21.10. (davor ~42) | beim aktuellen Tempo ~Ende Dez. (Nov. nicht mehr haltbar) | einsammeln, technische Prüfung; dann Abgleich mit dem ungekappten Arm (§9.4b) |
| **Q5-Raster** (1.632, 16 Pods) | 46 (29.10. 23:15, alle System 61) / 33 (29.10.), teuerste zuerst; laut Kostenschätzung ~42 % der Last erledigt, 0 Fehler, 0 Neustarts | ~31.10. abends + Nachzügler | einsammeln, aggregieren (REPORT_WP_FA5) |
| C-6-Raster ungekappt, Seed 42 (461) | **fertig und eingesammelt 29.10.** nach `outputs/phase_c_c6_grid_uncapped_5dd1df8…/`, SHA-256 gleich NFS, technisch geprüft (DIARY 29.10.) | — | Abgleich erst nach dem gekappten Raster: heute 259 Paare, nur dim 2 |

**WP-N48b (PySR auf C-6, für die 8 freien Kerne):** Codex meldet `blocked` — Umsetzung fertig, 48 gezielte Tests
grün, aber Testlaufzeit > 15-min-Protokollgrenze. Änderungen liegen uncommittet im Working Tree; noch nicht geprüft.

**Q4 ist fertig und eingesammelt:** 429/429 Datensätze unter `outputs/sideproject_q4_e70eeea/out/`, Job vom Cluster
entfernt. Aggregiert nach `analysis/data/sideproject_residual_growth/q4_*.csv` + `q4_run_metadata.json`; alle
Kontrollen bestanden, `duplicates_compared = 3` bit-identisch (DIARY 21.10.). Das Skript weigert sich, vorhandene
Tabellen zu überschreiben — ein erneuter Lauf braucht `--output-dir`.

Lokal läuft nichts.
**Offen für den Nutzer:** sieben schreibgeschützte pytest-Ordner unter `tmp/` (Codex-Sandbox, nur mit Admin-Rechten
löschbar) und die Annihilator-Dateien `output/pdf/` und `tmp/pdfs/` → gehören nach `..\EvoODE-next`.

**Statusseite „EvoODE auf Orion“:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN — Version 8 (28.10. 16:05): Q5-Probe fertig, Kostenfaktor, 16 Kerne frei. Bei jeder Änderung per Artifact `read` holen und darauf aufbauen.

## 2. Side-Projekt „Residual-Wachstum“ — Stand (Details DIARY 17.10.)

Protokolle (eingefroren vor jeder Rechnung): `docs/sideproject_residual_growth_protocol.md` (Q1/Q2, `e61f48f`),
`_q3.md` (`c81e7c6`), `_q4.md` (`24ede2d`, vom Nutzer freigegeben). Daten: `analysis/data/sideproject_residual_growth/`.

- **WP-FA1** C-1-Strukturinventur: reines Hinzufügen würde 22 von 354 Gleichungen reparieren; meist fehlt etwas
  **und** ist etwas Falsches da. Zwischenstrukturen speichert C-1 nicht.
- **Q1/Q2 (WP-FA2), R1–R4 bestehen** in dim 1, 2, 3 fittbar: Wahrheit im schwachen Raum auf einer Trajektorie
  identifizierbar; von C-1-Endstrukturen aus mit Hinzufügen + Refit + Entfernen erreichbar (Orakelgrößen).
- **Q3 (WP-FA3), R5/R6 bestehen:** ein Fit vom schwachen Start schlägt zehn Zufallsstarts auf der wahren Struktur
  (dim 2: 20/20 gegen 39/60); System 61 unter Schranke 10 lösbar (in CLAUDE.md nachgetragen).
- **Q4 (WP-FA4/4b/4c) gerechnet und aggregiert, nicht ausgewertet:** Wachstumspfad + Trajektorien-BIC (primär); R7 gegen C-1, **R8 gegen Weak-SINDy-Median
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
3. ~~Tor T2a-1~~ **geparkt bis nach Q5-W (Nutzer, 31.10.)**: weder Stopp noch S2; Entscheidung, wenn der WSINDy-Vergleich steht.
4. **Entscheidungsregel (b) als §9.4d**, erst dann C-6-EvoGrow öffnen. **Paper 1 ist nicht fix (Nutzer 14.10.).**

## 4. Annihilator-Spur: getrennt (Nutzer, 05.10.)

Die Methodenspur „Idee #1“ lebt **nur** im Ordner `..\EvoODE-next` (Branch `annihilator-discovery`), als eigenes
VS-Code-Projekt mit eigener `CLAUDE.md`, eigenem `READ_THIS_FIRST.md` und eigenem `DIARY.md`. Sie wird in Sitzungen
dieses Ordners nicht bearbeitet. Stand dort: Gate 2A v3, K6 würde auslösen, die Grundsatzentscheidung des Nutzers
ist offen.
