# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-29, Abend.** Push und `oc apply` macht der Nutzer. Die einmalige Freigabe vom
28.09. für den WP-T1f-Start ist verbraucht. Freigabe vom 29.09.: C-5-Generalisierung vorziehen,
wenn billig (erledigt).

---

## 1. Was läuft

| Lauf | Wo | Stand 29.09. 18:15 | Anmerkung |
|---|---|---|---|
| C-3 | Orion, `221a3a7` | 175 / 180 | 5 × Lorenz 55/56 `pretune_on` (Zellen 897, 899, 904, 905, 906), Level 27–29/30, 15–48 h/Level → Ende ~1.–4.10.; keine Deadline |
| WP-T1f | Orion, `1db1193` | 22 / 36 | dim 2 und System 52 fertig; 54/55/56 rechnen, 57/58/59/61 warten. Ende eher ~5./6.10.; Deadline 12.10. |

**Fertig:** C-1/C-2 (756/756, 29.09. 15:10), eingesammelt nach `outputs/phase_c_campaign_221a3a7/`
und als Zwischenstand ausgewertet (DIARY 29.09.). C-5-Generalisierung lokal gerechnet
(`outputs/wp_n5_ic_generalization_phase_c/`, Kontrolle 378/378 exakt). WP-N30 (SINDy-Paarung)
committet als `7173f7b`.

Fertig, noch nicht eingesammelt: **ODEFormer-Kandidatenraster** (`8e0e699`, 126/126).

Status lesen ohne eigenen Pod: `oc exec` in einen laufenden C-3-Pod, NFS unter `/outputs`.
Online-Statusseite „EvoODE auf Orion“: https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx — bei
jedem Statuswechsel neu veröffentlichen.

## 2. Nächster Meilenstein: Statusgespräch

Wenn C-3 und WP-T1f fertig sind (~5./6.10.) und der Cluster leer ist. **Bis dahin nichts Neues auf
dem Cluster starten, insbesondere nicht den C-5-Orakel-Arm.** Themen:

1. **Rahmung von Paper 1.** Die Daten tragen Effizienz und Suchmechanik (Claim B, sauber und
   bedingt) deutlich besser als Strukturfindung. Die Generalisierung liegt bei 37 % gegen 82 %
   Rekonstruktion, auf dim 2 bei 26 %, gegen SINDy am unteren Rand. „Warum nicht einfach SINDy?“
   ist die offene Flanke.
2. **Kappung:** Den Vorschlag bestätigen oder ändern, dass der Orakel-Arm mit Kappung läuft und die
   Systeme 54–59 vorab als unerreichbar markiert sind. Zulässige Begründungen: DIARY 29.09.
   Befund: Auch das erreichbare dim 3 (52, 61) trifft die Struktur in 0 von 12 Fällen.
3. WP-T1f-Tor.
4. ODEFormer-Kandidat und **ODEFormer-Paarung gegen C-1**. Zeigt ODEFormer dieselbe Lücke
   zwischen Rekonstruktion und Generalisierung, ist das ein Befund über das Feld, kein Makel von
   EvoGrow allein.
5. **Richtung, vom Nutzer am 29.09. gesetzt: das Overfitting an die Trajektorie angehen.** Die
   Rekonstruktion liegt bei 92 %, die Generalisierung bei 26 %, der rohe Strukturtreffer auf dim 2
   bei 3 von 60. Die Suche belohnt nur die Passung der einen Kurve. Kandidaten: Validierung auf der
   zweiten IC als Auswahlkriterium, ein stärkerer Komplexitätsterm, Sparsamkeit wie bei SINDy.
   Einordnen in `docs/phd_thesis_arc.md` (Paper 2/3, nicht Paper 1) und klären, wie das zur
   Leitlinie von Paper 2 (WP-T1f-Tor) passt.
6. Reihenfolge: C-5-Orakel und Restart-Kurve, WP-T2a.
7. `CLAUDE.md` eindampfen, zusammen mit dem Claim-Tracing-Audit.

## 3. Vorbereitung bis dahin (ohne Rechenlast)

- **Nächstes Codex-Paket: die Dreiwege-Repräsentierbarkeit für Phase C.** Die Supporttabelle nennt
  nur die erste nicht repräsentierbare Gleichung; nötig ist ein Status je Gleichung unter der
  Konstanten-Basis (Julia, von Claude auszuführen), dazu `aggregate_representability_threeway.py`
  ohne die Phase-B-Datei `representational_adequacy.csv`. Noch nicht geschrieben.
- Die ODEFormer-Paarung gegen C-1 bauen (gleich gegen gleich wie WP-N30).
- Den ODEFormer-Kandidaten einsammeln.
- Nach dem Ende von C-3: die ganze Kette aus `SCRIPTS.md` („Campaign bridge …“) noch einmal strikt
  und in die versionierten Orte rechnen; `analysis/configs/paper1_phaseC_v1.json` umstellen. Die
  C-1/C-2-Zahlen müssen dabei identisch herauskommen.
- WP-T1f nach dem Ende einsammeln und mit `--aggregate-only` auswerten.

## 4. Offen, klein

- `test_phase_a_evaluation_does_not_overwrite_frozen_artifacts` schlägt fehl, unabhängig von
  WP-N30, noch nicht untersucht.

## 5. Git

Gepusht bis `1db1193`. Lokal, **nicht gepusht**: alle Commits seit `14dc9b5`, darunter WP-N30
(`7173f7b`) und die DIARY-Einträge vom 29.09.
