# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-30, 23:45 — Q5-W-Portlauf umverteilt, 12 Prozesse.** 19.913 / 27.216 Zeilen, 0 Fehler. Teuer ist ρ = 0,5
(dim-2-Systeme 37–39 je ~10 CPU-h), nicht dim 3 (~16 s/Zeile). Shards 0–2 (ρ = 0) laufen unverändert (dim 3). Shards 3–5
(ρ = 0,5) gestoppt (CSV-Integrität geprüft, 67 Spalten in allen Zeilen) und ihr Rest auf 9 Prozesse verteilt:
`cells_{k}_{j}.csv` für k = 3–5, j = 0–2; j = 0 schreibt weiter nach `shard_{k}/` (Log `shard_{k}_r0.log`), j = 1, 2 nach
`shard_{k}_{j}/`. **Merge = alle `shard_*/details.csv`, Schlüssel (Zelle, Konfiguration) eindeutig prüfen.** Neustart
eines Teils: gleiche `--cells`/`--output-dir`-Kombination. Laptop muss wach bleiben. Orion-Token abgelaufen (23:36).

**Stand: 2026-10-30, 12:50 — Sitzung beendet, voller Q5-W-Portlauf rechnet weiter auf dem Laptop.**
- **Prozesse:** 6 × `python …/run_sideproject_q5w_wsindy.py`, gestartet 10:04 (PIDs 9956, 11728, 28768, 29452, 32168,
  48584), **15.997 / 27.216** Zeilen, 0 Fehler; dim 1 fertig, dim 2 bei Systemen 35–42, dim 3/4 (52–63, 5.184 Zeilen)
  kommt noch. Hochrechnung: dim 2 Rest ~3 h, dim 3/4 grob 11–20+ h (Simulationsbudget-Ausreißer, 2–6 min/Zeile) →
  fertig zwischen Freitagnacht und Wochenende (Nutzerwette: reicht nicht).
- **Zuklappen** = Ruhezustand, Prozesse frieren ein und laufen weiter. **Falls sie tot sind** (Neustart/Update), aus dem
  Repo-Root für i = 0…5 neu starten — setzt an den fertigen Zeilen fort:
  `python analysis/scripts/aggregate/run_sideproject_q5w_wsindy.py --all-cells --cells outputs/sideproject_q5w_wsindy/full_shards/cells_$i.csv --output-dir outputs/sideproject_q5w_wsindy/full_shards/shard_$i`
  (Fortschritt: `grep -c '^completed' outputs/sideproject_q5w_wsindy/full_shards/shard_*.log`).
- **Offen beim Nutzer:** ob auf 11 Prozesse umgeshardet wird (halbiert dim 3/4); MATLAB-Lizenz (IT-Helpdesk, ~14 Tage).
- **Danach, in dieser Reihenfolge:** Shards zu `outputs/sideproject_q5w_wsindy/full/details.csv` zusammenführen
  (technische Prüfung: 27.216 Zeilen, 0 Fehler, Hashes) → MATLAB-Lauf (`matlab -batch "addpath('analysis/matlab');
  run_wsindy_original_q5w(pwd, 2)"`, dann ohne Limit; < 1 h-Regel) → `compare_sideproject_q5w_matlab.py --port-rows
  outputs/sideproject_q5w_wsindy/full/details.csv` → **erst bei bestandenem §5.5 entsiegeln** und Q5-W-Tabellen bauen.
  **Bis dahin keine Rate, keine Struktur, kein Vergleich aus dem Portlauf ansehen.** Q5-Raster läuft auf Orion, Ende
  ~31.10. abends.

**Stand: 2026-10-30, ~11:00 — voller Q5-W-Portlauf rechnet auf dem Laptop** (6 Prozesse, Zell-Shards unter
`outputs/sideproject_q5w_wsindy/full_shards/shard_{0..5}/`, Logs daneben; resumable — Neustart mit derselben
`--cells`/`--output-dir`-Kombination setzt fort). Dim 1 fertig, dim 2 läuft; einzelne Auswertungen schöpfen das
eingefrorene Simulationsbudget (1,2 Mio. RHS-Evals) aus → 2–6 min pro Zeile, Hochrechnung ≥ 10–18 h. **Nutzer: tagsüber
laufen lassen, am Abend entscheiden** (Option: auf 11 Prozesse umshardeln, Q5-Zellen zuerst). Ergebnisse versiegelt bis
MATLAB-Abgleich (§5.5); MATLAB-Lizenz beim IT-Helpdesk angefragt. WP-FA6b committet (`8aa6eec`).

**Stand: 2026-10-30, Vormittag — Q5-W läuft weiter.** Nutzer hat entschieden: Protokoll **eingefroren** (`83139f0`),
Abnahme 1(ii) nur berichtet; neuer Punkt 5 = **Identität mit dem Originalcode in MATLAB** (SCCH hat Lizenzen, Installation
über IT-Helpdesk beantragt; Octave entfällt) auf allen ρ = 0-Zellen. **WP-FA6b bei Codex** (Abnahme umstellen, Smoke,
MATLAB-Export/-Treiber/-Vergleich). Danach startet Claude den vollen Lauf; **Ergebnisse versiegelt bis Punkt 5
bestanden**. Sobald MATLAB da ist: Claude startet den Original-Lauf (< 1 h-Regel).

**Stand: 2026-10-30, ~01:30 — wartet auf den Nutzer.** Code-Audit fertig: **Nachbau = Original** auf gleichmäßigem
Raster (DIARY 30.10., `9b49329`); 6/20 ist WSINDys eigenes Verhalten, die 15/20-Schwelle war falsch angesetzt.
WP-FA6-Code committet. **Morgens zu entscheiden:** (1) Abnahme 1(ii) ersetzen — Treue per Audit genügt, oder zusätzlich
Octave-Gegenlauf freigeben (Rechteregel für `docker run` mit fremdem Code); (2) Protokoll einfrieren; (3) dann
Determinismus + Smoke (Minuten) und voller Lauf 6 × 4.536 auf dem Laptop (Hochrechnung aus dem Smoke). Q5-Raster
(49/1.632) läuft weiter, der Q5-Vergleich braucht sein Ende (~31.10. abends).

**Stand: 2026-10-30, ~01:00. WP-FA6 `blocked`, Abnahme Lorenz 1(ii) 6/20 statt ≥ 15/20.** Muster: in allen 14
Fehlschlägen sind **alle wahren Terme da** (Koeffizientenfehler 1–3 %), dazu 1–3 kleine Störterme (|c| ≈ 0,01–0,05).
Die 15/20 waren von Claude gesetzt, ohne veröffentlichte Vergleichszahl — **nicht nachträglich gesenkt**. Klärung, ob
Nachbau-Fehler oder echtes Verhalten des Originals: (1) Octave-Gegenlauf des Originalcodes auf denselben Daten ist
vorbereitet (`gnuoctave/octave:9.2.0` gezogen, Daten + Treiber im Scratchpad), aber **vom Rechteprüfer blockiert
(„Code from External“) → Nutzerentscheidung**; (2) unabhängige Code-Prüfung Nachbau vs. Original läuft (Agent).
Abnahme 3 (Auswertung): 36/100 bit-identisch, Rest nur R²-Gleitkomma (Laptop vs. Orion), alle Strukturfelder und
R²>0,9-Entscheidungen gleich → benannte Ausnahme. Kein C-6-Lauf, keine Vergleichszahl. WP-FA6-Dateien uncommittet.

**Stand: 2026-10-30, 00:15. Q5-W läuft (Nacht, Nutzer schläft, will morgen ein Ergebnis).** Anlass: Zwischenblick
29.10. auf System 61 — Q5 (c) 16/44 Struktur gepruned gegen Weak-SINDy 0/44 (DIARY 29.10., `6aeb014`); Weak-SINDy verliert
dort nur an der festen Schwelle. Daher fairer Gegner: **WSINDy wie veröffentlicht** (offizieller Code MathBioCU/WSINDy_ODE
`72d8d6e`, lokal gitignored unter `outputs/reference_wsindy_ode_72d8d6e/`, „All Rights Reserved“ → nur nachbauen).
Protokoll-**Entwurf** `docs/sideproject_residual_growth_protocol_q5w.md` (`374e553`; A, B und Grenzen-Arm vom Nutzer
gebilligt, Einfrieren der Details steht aus). **Codex WP-FA6 gestartet 30.10. 00:04** (Implementierung, Abnahme gegen
das Lorenz-Beispiel des Originalcodes, Smoke nur auf sauberen Surrogat-Zellen). Danach: Claude prüft, voller Lauf auf dem
Laptop nur bei Hochrechnung < 1 h. Neuer offener Punkt in CLAUDE.md: datengetriebenes Pfadende statt 6-Term-Grenze.
Chaos-Befund System 61: schon 1 % Koeffizientenfehler → R² ≈ 0,06 beim wahren Modell (Chen-Lee, chaotisch).

**Stand: 2026-10-28, 17:15. Q5-Raster läuft** seit 16:19 auf Orion (`evoode-sideproject-q5`, 16 Pods, teuerste Zellen zuerst, Nachtrag `ecc8bac`; erwartet ~63 h + Nachzügler, ~1.000–1.100 Kern-h); **Belegung 40/40**. Wenn fertig: `out/index_*.jsonl` einsammeln, `aggregate_sideproject_q5.py --paths outputs/sideproject_q5_inputs/q5_grid_paths.json` (REPORT_WP_FA5). **C-6-Zwischenblick auf Nutzerwunsch** (Kriterium `4001c21`, Ergebnis `04e07eb`): kein Abbruchsignal, EvoGrow auf 18 dim-2-Systemen unter Rauschen vor der SINDy-Familie; **C-6 läuft weiter** (Nutzer). Blindheit für C-6 ist damit aufgehoben und im Paper offenzulegen. **Stand: 2026-10-28, 16:10. Q5-Probe fertig: 9/9** (Pod 7 letzter Schreibzugriff 14:48, Job per TTL entfernt), eingesammelt nach `outputs/sideproject_q5_354106398d5e67ffa72c237e2ba83e3feeb25b31/out/` (SHA-256 gleich NFS), aggregiert nach `analysis/data/sideproject_residual_growth/q5_probe/`, alle Kontrollen bestanden. **D1–D5 nicht ausgewertet** (gemeinsam). **Kostenfaktor ×3,16 gesamt** (Plan 8,9 → 28,3 Kern-h), verrauscht dim 1 ×0,74, dim 2 ×8,0, dim 3 ×4,2; Einzelzellen 0,18–19 (Tabelle DIARY 28.10.). Raster hochgerechnet ~1.100 Kern-h (~1.650 €) statt 244. **Nutzer entscheidet über das Q5-Raster.** Belegung jetzt **24/40 Kerne** (nur C-6 gekappt, 1.271/3.366 um 16:01). C-6 ungekappt (Seed 42) fertig 461/461, technisch geprüft, noch nicht lokal eingesammelt. §9.4d eingefroren (`f012fd0`). Q5 eingefroren (`f737939` + `f454a32`). Codex nur mit `-c 'windows.sandbox="unelevated"'`. WP-N48b (PySR) liegt pausiert und ungeprüft im Working Tree. Älter: Side-Projekt „Residual-Wachstum“: Q1–Q3 abgeschlossen und positiv (σ = 0); Q4
(Modellgröße ohne Orakel) vollständig gerechnet und aggregiert — alle Kontrollen bestanden, Plattformkontrolle
bit-identisch. R7–R9 noch nicht angesehen; Auswertung gemeinsam und in Ruhe.**

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

Lokal läuft nichts. Alles bis `a9e94ed` ist gepusht; der Commit vom 21.10. ist ungepusht (pusht der Nutzer).
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
