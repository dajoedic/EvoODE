# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-15, 15:10. C-6-Baselines DOP853 auf Orion fertig, noch nicht eingesammelt; gekapptes C-6-Raster verlangsamt.**

> **BLINDREGEL C-6 (Nutzer, 05.10., „Weg 2“):** Bis die Entscheidungsregel für Story-Linie (b) mit dem Nutzer
> festgelegt und als Plan §9.4d eingefroren ist, sieht sich Claude **keine C-6-EvoGrow-Ergebnisse** an — weder
> R², noch Struktur, noch Vergleiche mit SINDy. Erlaubt ist nur Einsammeln und **technische** Prüfung (Zellenzahl,
> `error`/`failure_reason`, Fingerprint, Daten-Hashes). Die Story-Diskussion folgt, wenn **alles** vom Cluster
> durchgelaufen ist; zuerst die Regel festlegen, dann die Zahlen öffnen.

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts — auch keine Tool-Zeitlimits** (Nutzer 05.10.: lange Läufe abgekoppelt starten, Abbruch nur gemeinsam). Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (nur mit VPN).
**Codex startet Claude selbst:** `codex exec -C "C:/Users/joedicke/Documents/reps/EvoODE" -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null`
(`run_in_background`). **Vor jedem Docker-Build `df -h /c` (< 30 GB → erst aufräumen).** Diese Datei bei
jedem Statuswechsel aktualisieren.

---

## 1. Was läuft — Orion, **33 Kerne (24 + 8 + 1), Limit 40**

| Lauf | Stand (15.10. 15:10) | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **C-6-Raster gekappt** (3.366, 24 Pods) | 752 (+29 seit 13.10. abends, ~16/Tag; viele Pods 1–3 Tage alt) | bei diesem Tempo deutlich nach Jan. — mit Nutzer besprechen | einsammeln (NFS `phase_c_c6_grid_<SHA>/tasks`), technische Prüfung (Blindregel) |
| **C-6-Raster ungekappt, Seed 42** (461, 8 Pods) | 207 | ~Anfang Nov. | Nutzer entscheidet Seed 123/7; 8 Kerne frei |
| **WP-T2a S1** (Orakel-Prior, dim 2, 20 Zellen) | 19/20, letzter Pod (Index 15) läuft seit 43 h | offen | einsammeln `paper2_t2a_s1_e483f83…/tasks`; Tor T2a-1 auf den 39 fittbaren dim-2-Zellen |
| ~~C-6-Baselines DOP853~~ (WP-N47, `sindy-baselines:e935c37`) | **fertig** (Job per TTL entfernt): 240/240 Shards, 136.080 Zeilen, 136.079 `success`, 1 `LinAlgError` (SVD) | — | **noch nicht eingesammelt/abgenommen**: saubere Zeilen identisch zu `outputs/c6_n46_clean_dop853`; Hierarchie ohne `--clean-only` |

Lokal läuft nichts. Platte: 109 GB frei. **Ungepusht:** `744b4d3`, `e06f640`, `58b3a7b` und dieser Commit (pusht der Nutzer). Ungetrackt im Repo-Wurzelverzeichnis: zwei Literatur-PDFs (FROLS, Piroddi & Lovera 2008), bewusst nicht committet.

## 2. Heute erledigt (DIARY 13.10.)

- **Zwei Bewertungsfehler zu Ungunsten der SINDy-Familie behoben:** explizites Euler statt genauem Löser (R² seit WP-N6),
  und leere Wahrheit für sin-Gleichungen (Systeme 23, 28, 43). WP-N46 (`da83040`) + WP-N46b; sauberer Neulauf lokal,
  C-4c neu mit DOP853, Kontrollen 652/652. **Neue Tabelle `analysis/data/paper1_phaseC_v1/hierarchy_n46/` ersetzt
  `hierarchy_n45`.**
- Ergebnis: Weak-SINDy deg3 0,01 liegt **auf allen drei Achsen** vor EvoGrow (Rek. 89,4 vs 88,6 %, Gen. 61,9 vs
  41,4 %, Struktur 65,0 vs 29,4 %). EvoGrow vorn nur bei dim-1-Generalisierung (70,3 vs 62,3 %) und Rekonstruktion dim 2.

## 2a. Offen aus der Sitzung vom 15.10. (Fenster geschlossen, nichts angefangen)

- **Nächster Schritt:** C-6-Baselines DOP853 von NFS `c6_sindy_baselines_dop853_e935c37…/shard_*` einsammeln,
  Abnahme (saubere Zeilen identisch zu `outputs/c6_n46_clean_dop853`), die eine `LinAlgError`-Zeile benennen,
  dann Hierarchie ohne `--clean-only`.
- **Nutzerentscheidung:** gekapptes C-6-Raster nur noch ~16 Zellen/Tag (752/3.366) → Rest ~160 Tage statt ~Jan.
  Weiterlaufen lassen oder umplanen? 7 Kerne bis zum 40er-Limit frei.
- **Statusseite „EvoODE auf Orion“** (`claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx`) ist nicht mehr lesbar
  („artifact not found“) und deshalb nicht nachgezogen. Nutzer: neuen Link nennen oder Neuanlage freigeben.

## 3. Als Nächstes

1. **Entscheidungsregel (b) mit dem Nutzer festlegen und als §9.4d einfrieren** — gegen `hierarchy_n46`, „jede Baseline“
   = SINDy, Weak-SINDy, E-SINDy, ODEFormer (später PySR). Alter Entwurf (B1 ≥ 10 pp vor der besten Konfiguration
   jeder Baseline auf dim 1/2 Generalisierung, Cluster-p < 0,05; B2 flacherer Abfall σ 0 → 0,05) ist auf sauberen
   Daten bereits verfehlt (dim 2: 29,8 vs 61,3 %); die Regel betrifft das Rauschverhalten.
2. **Verrauschte C-6-Baselines** laufen auf Orion (oben); danach einsammeln, Kontrolle, Hierarchie.
3. Erst dann C-6-EvoGrow öffnen. Story-Diskussion nach C-6. **Paper 1 ist nicht fix (Nutzer 14.10.)** — Rahmen und Hebel in DIARY 14.10.; Nutzer liest Piroddi & Spinelli 2003.
4. Später: PySR und ODEFormer auf C-6, wenn Kerne frei sind.

## 4. Annihilator-Spur: getrennt (Nutzer, 05.10.)

Die Methodenspur „Idee #1“ lebt **nur** im Ordner `..\EvoODE-next` (Branch `annihilator-discovery`), als eigenes
VS-Code-Projekt mit eigener `CLAUDE.md`, eigenem `READ_THIS_FIRST.md` und eigenem `DIARY.md`. Sie wird in Sitzungen
dieses Ordners nicht bearbeitet. Stand dort: Gate 2A v3, K6 würde auslösen, die Grundsatzentscheidung des Nutzers
ist offen.
