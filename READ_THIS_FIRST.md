# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-16, früh. C-6-Baselines DOP853 eingesammelt und ausgewertet (`hierarchy_n47_e935c37`); WP-T2a S1 fertig, nicht eingesammelt.**

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

| Lauf | Stand (15.10. 22:35) | Erwartetes Ende | Wenn fertig |
|---|---|---|---|
| **C-6-Raster gekappt** (3.366, 24 Pods) | 771; Reihenfolge = erst dim 2 (Sys. 24–51), dann dim 1, **nicht nach Kosten**; die teuersten (37, 40, 43, 44) kommen noch | ~8.–15. Nov. + Nachlauf (Rest ~13.400 Kern-h, DIARY 16.10.) | einsammeln (NFS `phase_c_c6_grid_<SHA>/tasks`), technische Prüfung (Blindregel) |
| **C-6-Raster ungekappt, Seed 42** (461, 8 Pods) | 207 | ~27. Okt. bis Anfang Nov. (Rest ~2.100 Kern-h) | Nutzer entscheidet Seed 123/7; dann 16 Kerne frei |
| ~~WP-T2a S1~~ | **fertig 15.10. abends** (20/20) | — | **noch einsammeln** `paper2_t2a_s1_e483f83…/tasks`; Tor T2a-1 auf den 39 fittbaren dim-2-Zellen |

Lokal läuft nichts. **Ungepusht:** `744b4d3`, `e06f640`, `58b3a7b`, `fee92a9`, `094d7a3` und dieser Commit (pusht der Nutzer).
Ungetrackt im Repo-Wurzelverzeichnis: zwei Literatur-PDFs, bewusst nicht committet.

## 2. Erledigt (DIARY 16.10.)

- **C-6-Baselines DOP853 eingesammelt** (`outputs/c6_sindy_baselines_dop853_e935c37/`, 240/240, 1 `LinAlgError` E-SINDy
  Sys. 57). Abnahme **nicht bit-identisch**: 120/11.340 saubere Zeilen kippen Terme — OpenBLAS-Kernel, lokal mit
  `OPENBLAS_CORETYPE` reproduziert. **Nutzer: Option (a)** — Orion ist kanonische Quelle für sauber und verrauscht.
- **Neue Tabelle `analysis/data/paper1_phaseC_v1/hierarchy_n47_e935c37/` ersetzt `hierarchy_n46`** (Verschiebungen ≤ 3/378 Zellen).

## 3. Als Nächstes

1. **Statusseite „EvoODE auf Orion“ neu anlegen** (Nutzer: Neuanlage freigegeben).
2. **WP-T2a S1 einsammeln**, Tor T2a-1.
3. **Mit dem Nutzer genauer anschauen:** (i) Umgang mit dem gekappten Raster (Ende ~Mitte Nov., 8 freie Kerne);
   (ii) Entscheidungsregel (b) als §9.4d — Messlatte: Rauschtabelle der SINDy-Familie in DIARY 16.10.
4. Erst dann C-6-EvoGrow öffnen. **Paper 1 ist nicht fix (Nutzer 14.10.).**
5. Später: PySR und ODEFormer auf C-6, wenn Kerne frei sind.

## 4. Annihilator-Spur: getrennt (Nutzer, 05.10.)

Die Methodenspur „Idee #1“ lebt **nur** im Ordner `..\EvoODE-next` (Branch `annihilator-discovery`), als eigenes
VS-Code-Projekt mit eigener `CLAUDE.md`, eigenem `READ_THIS_FIRST.md` und eigenem `DIARY.md`. Sie wird in Sitzungen
dieses Ordners nicht bearbeitet. Stand dort: Gate 2A v3, K6 würde auslösen, die Grundsatzentscheidung des Nutzers
ist offen.
