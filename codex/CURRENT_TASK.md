# WP-N7b — Abnahme korrigiert: roher gegen ausgedünnter Support

**Language: Python**

## Warum dieses Paket existiert

WP-N7 hat korrekt `blocked` gemeldet. **Der Fehler lag im Abnahmekriterium, nicht im Code.** Die
Begründung im Report ist allerdings unvollständig, und die richtige Erklärung ist ein eigener Befund.

Nachgeprüft an den Rohdaten:

- `run_registry.exact_support_match` ist für Phase B **identisch mit `pruned_match`** aus
  `history.jsonl` — 756 von 756 Zellen, keine Abweichung. Die Spalte ist also der **ausgedünnte**
  Support-Match.
- `support_terms` ist dagegen die **rohe**, nicht ausgedünnte aktive Termmenge
  (`active_term_names`, `studies/regression/run_regression.jl:870`).

Die 40 Abweichungen sind daher keine Fehler, sondern genau die Zellen, in denen die Ausdünnungsregel
überzählige Terme entfernt und den Treffer damit erst herstellt. Ein Vergleich von roh gegen
ausgedünnt **kann** nicht übereinstimmen, und aus den Phase-B-Records ist der ausgedünnte Zustand
nicht rekonstruierbar, weil dort keine Koeffizienten gespeichert sind.

Die WP-N7-Dateien bleiben liegen und werden hier erweitert, nicht ersetzt.

## Was zu tun ist

### Teil 1 — Die erreichbare Abnahme als Test festschreiben

Es gibt eine exakte, gerichtete Beziehung, und sie ist nachgeprüft:

> `pruned_match == True` impliziert `n_missing_true_terms == 0`.

Auf den 240 exakten Phase-B-Zellen gilt sie in **110 von 110** Fällen ohne eine einzige Verletzung.
Die Umkehrung gilt nicht: 119 Zellen haben `missing == 0`, aber nur 110 davon sind ausgedünnte
Treffer.

Das ist die richtige Validierung der neuen Recall-Berechnung, und sie gehört als **Test** nach
`analysis/tests/`, nicht nur als Zahl in einen Report. Der Test muss fallen, wenn die
Normalisierung oder die Recall-Berechnung kaputtgeht.

### Teil 2 — Roh gegen ausgedünnt als eigene Ableitung

Eine Tabelle nach `analysis/data/paper1_phaseB_v1/`, die je Zellklasse gegenüberstellt:

- Anzahl exakter Zellen
- roher exakter Struktur-Match (aus `support_terms`, ohne Ausdünnung)
- ausgedünnter Match (`exact_support_match` aus dem Registry)
- die Differenz, also die Zellen, die den Treffer **allein der Ausdünnungsregel verdanken**
- dieselben Zahlen aufgeschlüsselt nach Dimension, Bedingung und IC-Satz

Die Gesamtzahlen sind bereits geprüft und dienen dir als Kontrolle: 240 exakte Zellen, 110
ausgedünnte Treffer, 70 rohe Treffer, 40 durch Ausdünnung gerettet. **Weichen deine Zahlen davon ab,
ist das ein Fehler in der Ableitung und gehört im Report benannt — nicht stillschweigend korrigiert.**

### Teil 3 — Die Doppeldeutigkeit der Spalte dokumentieren

Die beiden Runner belegen denselben Spaltennamen verschieden:

- `experiments/run_experiment.jl:405` setzt `"exact_support_match" => exact_support_match_raw` und
  führt roh und ausgedünnt zusätzlich getrennt. Das ist der **Phase-A**-Pfad.
- `studies/regression/run_regression.jl` schreibt ausschließlich `pruned_match`, das in der Registry
  als `exact_support_match` landet. Das ist der **Phase-B**-Pfad.

Ein Join von Phase A und Phase B über diese Spalte vergleicht damit **verschiedene Größen**. Baue
eine Prüffunktion, die aus Registry-Metadaten bestimmt, welche Definition eine Datei trägt, und die
**laut fehlschlägt**, wenn Daten mit unterschiedlicher Definition in einer Auswertung
zusammenkommen. Stillschweigendes Zusammenführen darf nicht möglich sein.

Phase A wird dabei **nicht angefasst und nicht neu ausgewertet** — die Prüffunktion ist ein Wächter,
keine Migration.

## Abnahme

1. Der Test aus Teil 1 existiert, läuft grün und fällt nachweislich, wenn man die Recall-Berechnung
   absichtlich kaputtmacht. Den Gegenprobe-Nachweis im Report beschreiben.
2. Die Tabelle aus Teil 2 existiert und reproduziert 240 / 110 / 70 / 40 exakt.
3. Die Prüffunktion aus Teil 3 existiert, hat einen Test für den Gutfall und einen für den
   Konfliktfall.
4. Alle Tests unter `analysis/tests/` laufen grün; das Kommando steht im Report.
5. Die WP-N7-Ergebnisse bleiben gültig und reproduzierbar; nichts davon wird zurückgebaut.

## Verboten

- **Keine Kampagne, keine Cluster-Jobs, keine Julia-Läufe, nichts über 15 Minuten.**
- **Keine Änderung an der Ausdünnungsregel** `max(1e-6, 1e-3 * max_abs)`. Sie ist eingefroren; WP-V1
  und WP-N2 dokumentieren genau das als Fehler.
- **Keine Phase-A-Daten neu auswerten oder verändern.**
- Bestehende T1–T5-Tabellen und die WP-N7-Dateien nicht überschreiben.
- Keine Bewertung der Ergebnisse. Zahlen nennen, Einschätzungen weglassen.
- Nicht committen, nicht stagen, keine Git-Operationen.

## Report

`codex/reports/REPORT_WP_N7b.md`. Enthält die Tabelle aus Teil 2, den Gegenprobe-Nachweis aus
Abnahmepunkt 1, das Verhalten der Prüffunktion in beiden Fällen und die Kommandos.
