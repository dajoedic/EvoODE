# WP-N20 — Varianzgewichtetes R² in der Analysepipeline
**Language: Python**

## Ziel

Die Analysepipeline soll aus vorhandenen Records **beide** R²-Aggregationen berechnen — die
arithmetische, die wir speichern, und die varianzgewichtete, die ODEBench verwendet — und die
Schwellenraten `R² > 0.9` je Aggregation ausweisen.

Die Entscheidung dahinter steht in `docs/paper1_phaseC_benchmark_plan.md` §6b und ist **nicht Teil
dieses Auftrags**: beide werden berichtet, die varianzgewichtete traegt das Etikett
„Literaturvergleich", weil sie ODEBench' Definition ist. Hier wird gerechnet, nicht entschieden.

**Kein Neulauf der Kampagne.** Alles Noetige ist gespeichert.

## Woraus sich das rekonstruieren laesst

`r2_by_dim` steht in jedem Record und enthaelt das R² je Dimension. Die Gewichte sind die Varianzen
der **Referenztrajektorie** je Dimension — eine Eigenschaft der Trajektorie allein, nicht des Fits.
Sie kommen aus dem gehashten Export unter
`outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/`: `trajectory_manifest.csv` mit
126 Zeilen, dazu Rohdaten als float64, deren Achsen- und Formangaben im Manifest stehen und
**gelesen, nicht angenommen** werden.

Die Zuordnung Record → Trajektorie laeuft ueber System-Kennung und IC-Set.

## Die Kontrolle, die den Auftrag traegt

Die Rekonstruktion ist **exakt, nicht naeherungsweise**, und das ist pruefbar: das arithmetische
Mittel ueber `r2_by_dim` muss das gespeicherte Feld `r2` reproduzieren. Am 2026-09-18 galt das auf
52 von 52 Phase-C-Records mit einer Abweichung unter `1e-12`.

**Diese Kontrolle laeuft mit, bei jedem Lauf, ueber jeden Record** — nicht einmalig als Test.
Schlaegt sie an, ist entweder die Zuordnung falsch oder der Recordbestand nicht der erwartete; beides
muss auffallen, statt eine plausibel aussehende Zahl zu erzeugen. Wie die Pipeline darauf reagiert
— Abbruch oder markierte Zeile mit Zaehler im Ergebnis — ist zu entscheiden und im Report zu
begruenden; stillschweigend weiterrechnen ist keine Option.

Zweite Kontrolle, gratis: auf eindimensionalen Systemen **muessen** beide Aggregationen identisch
sein. Sind sie es nicht, ist die Gewichtung falsch angewandt.

## Was zu liefern ist

Eine Auswertung ueber einen Kampagnen-Recordbestand, die je Zelle beide Aggregationen und beide
Schwellenflags fuehrt, und darueber aggregiert:

- die Rate `R² > 0.9` je Aggregation, aufgeschluesselt nach Dimension, Arm und IC-Set — die
  Nicht-Aggregation ueber IC-Sets ist seit WP-A4b Regel
- die **Kipprate**: Zellen, bei denen die beiden Aggregationen auf verschiedenen Seiten der Schwelle
  liegen, mit Richtung. Sie ist eine berichtete Groesse, keine Zwischenrechnung
- die Verteilung der Differenz als **Quantile**, nie als Mittelwert oder Median allein — die Regel
  aus WP-A6/A7 gilt auch hier

Der Kampagnen-Bezeichner ist ein **Parameter**, kein fest verdrahteter Wert. `CLAUDE.md` fuehrt unter
„Known Gaps" bereits, dass die Strukturmetriken aus WP-N7 auf `paper1_phaseB_v1` festverdrahtet sind
und genau das nachgezogen werden muss — diesen Fehler nicht wiederholen.

Ablage analog zu den bestehenden Auswertungen unter `analysis/`; die dortigen Konventionen
(`analysis/CONVENTIONS.md`) gelten.

## Wogegen zu pruefen ist

Der vorhandene Phase-C-Bestand auf der Freigabe ist **unvollstaendig und waechst** — am 2026-09-18
waren es 52 Records von 936. Das ist kein Fehler, sondern der laufende Betrieb. Die Auswertung muss
mit einem Teilbestand umgehen und die Anzahl ausgewiesener Zellen **im Ergebnis nennen**, damit eine
Zahl nie ohne ihren Nenner zitiert wird.

Nicht verfuegbar ist die Freigabe aus Codex' Umgebung. Fuer Entwicklung und Test ist der
versionierte, echte Recordbestand zu verwenden, der im Repository liegt — insbesondere
`analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke/records.jsonl` sowie die
Registry unter `experiments/paper1_phaseB_v1/`. **Fixtures werden daraus abgeleitet, nie erfunden**
(`codex/CODEX_PROTOCOL.md`).

Ein Hinweis, der Zeit spart: die Phase-B-Registry traegt `r2_by_dim` als Spalte, sie wird aber laut
`CLAUDE.md` nicht aggregiert. Ob ihr Format dem der Phase-C-Records entspricht, ist zu **pruefen und
im Report zu benennen**, nicht anzunehmen.

## Was ausdruecklich nicht gemacht wird

Keine Aenderung an `studies/regression/` oder am Kampagnenpfad — die Rekonstruktion gehoert in die
Analyse, nie in den Lauf. Keine Entscheidung darueber, welche Aggregation die Hauptzahl ist. Kein
GitLab-Push.

## Abnahmekriterium

1. Die Kontrolle „arithmetisches Mittel reproduziert `r2`" laeuft ueber jeden Record und ist im
   Ergebnis als Zahl sichtbar, nicht nur als bestandener Test.
2. Auf eindimensionalen Zellen sind beide Aggregationen identisch.
3. Auf mindestens einer mehrdimensionalen Zelle aus echten Daten sind sie verschieden, und die
   Kipprate ist ausgewiesen.
4. Der Kampagnen-Bezeichner ist ein Parameter; ein zweiter Bestand laesst sich ohne Codeaenderung
   auswerten.
5. Jede berichtete Rate nennt ihren Nenner.

## Bericht

`codex/reports/REPORT_WP_N20.md`. Aufzunehmen: die Herkunft jedes Feldes (bestehendes Recordfeld,
neues Feld, oder Analyseschicht), das Ergebnis der beiden Kontrollen mit Zahlen aus dem Lauf, die
Entscheidung zum Verhalten bei Kontrollverletzung mit Begruendung, und das Ergebnis der Pruefung, ob
die Phase-B-Registry dasselbe `r2_by_dim`-Format traegt.
