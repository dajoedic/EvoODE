# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-10-01, nachts (nach dem Orakel).** Push und `oc apply` macht der Nutzer. Die einmalige Freigabe vom
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

## 2a. Morgen (02.10.): Rauschen und Abtastrate — vom Nutzer entschieden

Plan, Kosten und Optionen: DIARY 01.10., „Plan: Rauschen und Abtastrate …“.

1. **Claude** schreibt die vorab festgelegte Protokoll-Spezifikation: ODEFormer-Protokoll,
   dim 1 und dim 2, Gegner SINDy, Weak-SINDy und ODEFormer auf dem vollständigen Raster, primäre
   Metriken, geseedete Rauschziehung, Pilot mit Go-Kriterium. **Alles wird berichtet.**
2. **Codex** baut Rauschen und Ausdünnung in den Kampagnenpfad ein (`codex/CURRENT_TASK.md`, mit
   `codex exec` starten).
3. **Pilot** auf Orion: Läuft jede Zelle unter Rauschen alle 30 Level durch? Danach entscheidet der
   Nutzer über das EvoGrow-Raster: vollständig mit 3 Seeds ~39.000 h, vollständig mit 1 Seed
   ~13.000 h, oder 3 Bedingungen ~5.900 h. Das ist jeweils eine Untergrenze. Ein Teilraster nur mit
   vorab geschriebener Begründung.

## 2. Nächster Meilenstein: Statusgespräch — der Scheideweg

Wenn C-3 und WP-T1f fertig sind (~5.–7.10.) und der Cluster leer ist. **Bis dahin nichts Neues auf
dem Cluster starten.** Hintergrund und alle Zahlen: DIARY 01.10., beide Einträge.

**Die Leitfrage des Nutzers:** ein Fundament statt zwanzig Versuche. Paper 1 als publizierbares
EvoGrow („gut unterwegs, teilweise besser, vor allem da und da stark“), dann Warmstart, Multiple
Shooting und Ranking als eigene Papers obendrauf, so wie SINDy die Basis seiner Erweiterungen war.

**Zu entscheiden, in dieser Reihenfolge:**

1. **Rahmung von Paper 1 als Fundament-Paper.** Stärken: Rekonstruktion auf jeder Dimension besser
   als SINDy; Generalisierung auf dim 1 vorn und auf den 30 voll repräsentierbaren Systemen die
   beste der drei Methoden; Claim B gilt mit Bedingung. Schwächen: Strukturfindung auf gekoppelten
   Systemen, dim-2-Generalisierung, etwa hundertmal mehr Rechenaufwand. Die Orakel-Diagnose
   („Auswahl nach Fittbarkeit“) wird zum Befund, und die Limitations werden zur Roadmap der
   Folgepapers.
2. **Kommt genau eine Stärke-Messung noch in Paper 1?** Kandidat: Rauschen und/oder Abtastrate nach
   dem ODEFormer-Protokoll, gegen SINDy **und** Weak-SINDy, vorab festgelegt, jedes Ergebnis wird
   berichtet. Erst eine Kostenschätzung, dann die Entscheidung. Alles andere kommt nicht in
   Paper 1.
3. **Definition eines guten Ergebnisses für alle neuen Methodenversionen:** primär roher
   Strukturtreffer und Generalisierungs-R², sekundär Rekonstruktions-R². Festlegen vor dem ersten
   neuen Lauf.
4. **Reihenfolge der Folgepapers** (gehört nach `docs/phd_thesis_arc.md`): (a) Ranking bzw.
   Screening im Ableitungsraum, Spur vom Juli, ungeprüft statt widerlegt; (b) Warmstart bzw.
   Pretuning als Startpunkt; (c) Multiple Shooting gegen die Fittbarkeit. Dazu klären, wie das zur
   Paper-2-Leitlinie und zum WP-T1f-Tor passt.
5. Kleinere Punkte: Kappung in der nächsten Methodenversion; System 61 (Restart-Kurve oder WP-T1f);
   `CLAUDE.md` eindampfen samt Claim-Tracing-Audit.

**Billigster nächster Schritt, lokal und ohne Cluster, erst nach Freigabe:** Wie hoch rankt der
Ableitungs-Score die wahre Struktur unter ihren Nachbarn, auf den 30 exakten Systemen? Er
entscheidet, ob Punkt 4a eine Grundlage hat.

## 3. Vorbereitung bis dahin (ohne Rechenlast)

- Erledigt am 29.09.: die Dreiwege-Klasse (`84be4ce`) und die ODEFormer-Paarung (WP-N31, `1f197dd`).
  Auf den voll repräsentierbaren Systemen generalisiert EvoGrow am besten (DIARY 29.09.).
- Nach dem Ende von C-3: die ganze Kette aus `SCRIPTS.md` („Campaign bridge …“) noch einmal strikt
  und in die versionierten Orte rechnen; `analysis/configs/paper1_phaseC_v1.json` umstellen. Die
  C-1/C-2-Zahlen müssen dabei identisch herauskommen.
- WP-T1f nach dem Ende einsammeln und mit `--aggregate-only` auswerten.

## 4. Offen, klein

- **Codex ist wieder verfügbar (Stand 01.10.).**

- `test_phase_a_evaluation_does_not_overwrite_frozen_artifacts`: Die Ursache ist gefunden, es
  ist ein Umgebungsartefakt. Die lokale Datei `debug_results/generalization_summary.csv` fehlt,
  das Urteil bleibt `OMIT` wie eingefroren. Den Test von der Datei entkoppeln (kleines
  Codex-Paket, nicht dringend).

## 5. Git

Gepusht bis `1db1193`. Lokal, **nicht gepusht**: alle Commits seit `14dc9b5`, darunter WP-N30
(`7173f7b`) und die DIARY-Einträge vom 29.09.
