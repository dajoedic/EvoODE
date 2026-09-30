# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-01, 01:35 (Clusterstatus); sonst 2026-09-29, Abend.** Push und `oc apply` macht der Nutzer. Die einmalige Freigabe vom
28.09. für den WP-T1f-Start ist verbraucht. Freigabe vom 29.09.: C-5-Generalisierung vorziehen,
wenn billig (erledigt).

---

## 1. Was läuft

| Lauf | Wo | Stand 01.10. 01:35 | Anmerkung |
|---|---|---|---|
| C-3 | Orion, `221a3a7` | 176 / 180 | 906 fertig 30.09. 10:15 UTC. Offen: 897 (Level 28), 899 (29), 904 (29), 905 (28), alle Lorenz 55/56 `pretune_on`; letzte Level 22–51 h → 899/904 ~1.–2.10., 897/905 ~2.–5.10.; keine Deadline |
| C-5 Orakel | Orion, `1db1193` | **fertig und eingesammelt** (01.10.) | 180/180, `error = null`, Zeilen-config `925e3957a7a884e2`, lokal `outputs/wp_n3_oracle_refit_phase_c/`. Befund: 52 = Suche scheitert, 61 offen, 63 = Suche scheitert; Instrument nur einseitig beweiskräftig (DIARY 01.10.) |
| WP-T1f | Orion, `1db1193` | 26 / 36 | fertig 0–22, 24, 28, 29 (dim 2, 52, 54 IC1, 55 IC1, 57). Rechnen: 54 IC2, 55 IC2, 56 ×2, 58 ×2 (fertige Zelle = 185 Zeilen). Warten: 59, 61. Ende ~5.–7.10.; Deadline 12.10. |

**Fertig:** C-1/C-2 (756/756, 29.09. 15:10), eingesammelt nach `outputs/phase_c_campaign_221a3a7/`
und als Zwischenstand ausgewertet (DIARY 29.09.). C-5-Generalisierung lokal gerechnet
(`outputs/wp_n5_ic_generalization_phase_c/`, Kontrolle 378/378 exakt). WP-N30 (SINDy-Paarung)
committet als `7173f7b`.

**ODEFormer-Kandidatenraster** (`8e0e699`) eingesammelt, `cdc77ff`: Die Raten liegen höchstens
3 Punkte neben der Referenz, die Schlüsse bleiben gleich.

Status lesen ohne eigenen Pod: `oc exec` in einen laufenden C-3-Pod, NFS unter `/outputs`.
Online-Statusseite „EvoODE auf Orion“: https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx — bei
jedem Statuswechsel neu veröffentlichen.

## 2. Nächster Meilenstein: Statusgespräch

Wenn C-3 und WP-T1f fertig sind (~5./6.10.) und der Cluster leer ist. **Bis dahin nichts Neues auf
dem Cluster starten.** Ausnahme, vom Nutzer freigegeben: der C-5-Orakel-Arm (läuft). Themen:

1. **Rahmung von Paper 1.** Die Daten tragen Effizienz und Suchmechanik (Claim B, sauber und
   bedingt) deutlich besser als Strukturfindung. Die Generalisierung liegt bei 37 % gegen 82 %
   Rekonstruktion, auf dim 2 bei 26 %, gegen SINDy am unteren Rand. „Warum nicht einfach SINDy?“
   ist die offene Flanke.
2. **Kappung:** Für den Orakel-Arm entschieden (mit Kappung, DIARY 29.09.). Offen: Wie wird sie in der
   nächsten Methodenversion entfernt oder begründet? Auch das erreichbare dim 3 (52, 61) trifft die
   Struktur in 0 von 12 Fällen; das Orakel sagt, ob es an der Suche liegt.
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

- Erledigt am 29.09.: die Dreiwege-Klasse (`84be4ce`) und die ODEFormer-Paarung (WP-N31, `1f197dd`).
  Auf den voll repräsentierbaren Systemen generalisiert EvoGrow am besten (DIARY 29.09.).
- Nach dem Ende von C-3: die ganze Kette aus `SCRIPTS.md` („Campaign bridge …“) noch einmal strikt
  und in die versionierten Orte rechnen; `analysis/configs/paper1_phaseC_v1.json` umstellen. Die
  C-1/C-2-Zahlen müssen dabei identisch herauskommen.
- WP-T1f nach dem Ende einsammeln und mit `--aggregate-only` auswerten.

## 4. Offen, klein

- **Codex ist ohne Tokens (Stand 29.09. abends).** Vorerst keine Codex-Pakete übergeben.

- `test_phase_a_evaluation_does_not_overwrite_frozen_artifacts`: Die Ursache ist gefunden, es
  ist ein Umgebungsartefakt. Die lokale Datei `debug_results/generalization_summary.csv` fehlt,
  das Urteil bleibt `OMIT` wie eingefroren. Den Test von der Datei entkoppeln (kleines
  Codex-Paket, nicht dringend).

## 5. Git

Gepusht bis `1db1193`. Lokal, **nicht gepusht**: alle Commits seit `14dc9b5`, darunter WP-N30
(`7173f7b`) und die DIARY-Einträge vom 29.09.
