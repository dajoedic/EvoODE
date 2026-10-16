# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-17. WP-T2a S1 eingesammelt, Tor T2a-1 nach eingefrorener Regel nicht bestanden. Vorschlag Fokuswechsel „ob → warum“ (Diskussionspapier), Nutzer diskutiert ihn extern; bis zur Rückkehr wird nichts Neues gestartet.**

> **BLINDREGEL C-6 (Nutzer, 05.10., „Weg 2“):** Bis die Entscheidungsregel für Story-Linie (b) mit dem Nutzer
> festgelegt und als Plan §9.4d eingefroren ist, sieht sich Claude **keine C-6-EvoGrow-Ergebnisse** an — weder
> R², noch Struktur, noch Vergleiche mit SINDy. Erlaubt ist nur Einsammeln und **technische** Prüfung (Zellenzahl,
> `error`/`failure_reason`, Fingerprint, Daten-Hashes). Die Story-Diskussion folgt, wenn **alles** vom Cluster
> durchgelaufen ist; zuerst die Regel festlegen, dann die Zahlen öffnen.

**Feste Regeln:** Claude pusht **nie** nach GitLab und nach GitHub nur mit ausdrücklicher Erlaubnis.
**Keine harten Zeit-Cuts — auch keine Tool-Zeitlimits** (Nutzer 05.10.: lange Läufe abgekoppelt starten, Abbruch nur gemeinsam). Orion-Ergebnisse unter `S:\BigDataOrion\data-science\joedicke\` (nur mit VPN).
**Codex startet Claude selbst:** `codex exec -C "C:/Users/joedicke/Documents/Repositories/EvoODE" -s workspace-write "Lies codex/CODEX_PROTOCOL.md und arbeite den Auftrag in codex/CURRENT_TASK.md ab." < /dev/null`
(`run_in_background`). **Vor jedem Docker-Build `df -h /c` (< 30 GB → erst aufräumen).** Diese Datei bei
jedem Statuswechsel aktualisieren.

---

## 1. Was läuft — Orion, **32 Kerne (24 + 8), Limit 40 → 8 frei**

| Lauf | Stand (17.10. 00:15) | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **C-6-Raster gekappt** (3.366, 24 Pods) | 855; Reihenfolge = erst dim 2 (Sys. 24–51), dann dim 1, **nicht nach Kosten**; die teuersten (37, 40, 43, 44) kommen noch | ~8.–15. Nov. + Nachlauf (Rest ~13.400 Kern-h, DIARY 16.10.) | einsammeln (NFS `phase_c_c6_grid_<SHA>/tasks`), technische Prüfung (Blindregel) |
| **C-6-Raster ungekappt, Seed 42** (461, 8 Pods) | 211 | ~27. Okt. bis Anfang Nov. (Rest ~2.100 Kern-h) | Nutzer entscheidet Seed 123/7; dann 16 Kerne frei |

Lokal läuft nichts. **Ungepusht:** `744b4d3`, `e06f640`, `58b3a7b`, `fee92a9`, `094d7a3`, `90bd849`, `4a5f87b`, `727db7f`, `13b0457`, `bca37c7`, `7addd72`, `5cc3d8a`, `ba046d5` und
dieser Commit (pusht der Nutzer). Ungetrackt im Repo-Wurzelverzeichnis: zwei Literatur-PDFs, bewusst nicht committet.

**Statusseite „EvoODE auf Orion“ neu:** https://claude.ai/artifact/9zzJsoGCBahPsuNkaaf3DN (die alte ist weg). Quelle lokal
im Scratchpad dieser Sitzung; sonst per Artifact `read` holen und darauf aufbauen.

## 2. Erledigt (DIARY 16.10. und 17.10.)

- **C-6-Baselines DOP853** eingesammelt, Option (a), `hierarchy_n47_e935c37` ersetzt `hierarchy_n46`.
- **WP-T2a S1 eingesammelt** (`outputs/paper2_t2a_s1_e483f83/`, 20/20, technisch sauber). Fittbare dim-2-Zellen
  (13/20, 8 Systeme): geprunt 3 → 5 (+15,4 pp), roh 0 → 2, R² > 0,9 13 → 13, Aufwand ×0,997. **Cluster-p = 0,25 →
  Tor T2a-1 nach eingefrorener Regel nicht bestanden.** Vorläufig, inline gerechnet; Generalisierung und Konfounder fehlen.
- **Diskussionspapier** `docs/diskussion_warum_scheitert_die_suche.md` (`5cc3d8a`): Fokuswechsel von „ob“ zu „warum“,
  fünf Fehlerklassen A–E (nicht erreicht / schlecht gefittet / Obermenge / nicht identifizierbar / absolutes λ = 1e-3),
  Schritt 1 ohne Rechenzeit. Der Nutzer hat es mitgenommen und diskutiert extern.
- **Idee des Nutzers behalten:** Terme schrittweise auf den Restfehler (FROLS-Familie). Tragfähig nur im Ableitungsraum
  oder in der schwachen Form, gemeinsam nachfitten. Steht in `CLAUDE.md` „Open, not scheduled“ und DIARY 17.10.

## 3. Als Nächstes — wartet auf den Nutzer

1. **Ergebnis der externen Diskussion** zum Fokuswechsel. Bei Zustimmung: Schritt 1 der Fehleranatomie (C-1-Objective
   gegen das Objective der Wahrheit aus P-04 bei k = 3 und k = 10), vorher die zwei Code-Annahmen prüfen (gemeldet wird
   das globale Objective-Minimum; λ wirkt pro Koeffizient).
2. **Tor T2a-1:** Stopp der Führungsspur oder S2. Beobachtung (keine Umdeutung): p < 0,05 war auf S1 nur mit ≥ 5
   gewinnenden Systemen ohne Verlierer erreichbar.
3. **Mit dem Nutzer genauer anschauen:** (i) 8 freie Kerne (PySR/ODEFormer auf C-6?); (ii) Entscheidungsregel (b) als
   §9.4d — Messlatte: Rauschtabelle der SINDy-Familie in DIARY 16.10.
4. Erst dann C-6-EvoGrow öffnen. **Paper 1 ist nicht fix (Nutzer 14.10.).**

## 4. Annihilator-Spur: getrennt (Nutzer, 05.10.)

Die Methodenspur „Idee #1“ lebt **nur** im Ordner `..\EvoODE-next` (Branch `annihilator-discovery`), als eigenes
VS-Code-Projekt mit eigener `CLAUDE.md`, eigenem `READ_THIS_FIRST.md` und eigenem `DIARY.md`. Sie wird in Sitzungen
dieses Ordners nicht bearbeitet. Stand dort: Gate 2A v3, K6 würde auslösen, die Grundsatzentscheidung des Nutzers
ist offen.
