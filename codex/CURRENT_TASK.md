> **Claude-Status:** `waiting for codex` — WP-A2 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-A2 — Die Auswertung kennt die Kampagnenvarianten nicht und schweigt darüber
**Language: Python**

## Der Befund

WP-A1 (2026-08-13) hat eine Brücke von den Kampagnen-Records in die Python-Auswertung gebaut. Dabei
fiel auf, dass `analysis/scripts/plot/table_main_results.py` danach **fehlerfrei durchläuft und
Unsinn liefert**:

```text
agg_variants   = evogrow_v2_2_stage_capped, evogrow_v3, …   (Kampagne)
VARIANT_ORDER  = evogrow_v1, evogrow_v2_1, gp_baseline, …   (eingefrorene Phase-A-Liste)
table_rows=30   table_nonempty_mean_loss=5
```

`reindex_table_data` indiziert auf `VARIANT_ORDER` (Zeile 29) um und lässt alles fallen, was dort
nicht steht. **25 von 30 Zeilen bleiben leer, ohne eine einzige Meldung.** Zum Vergleich:
`evaluate_hypotheses.py` scheitert bei derselben Datenlage sauber mit `Missing expected variants`.

Das ist die gefährlichste Fehlerklasse in der Auswertung, weil das Ergebnis wie ein Ergebnis
aussieht. Nach 756 Kampagnenzellen wäre eine fast leere Tabelle das Erste, was jemand ins Paper
übernimmt.

## Umfang

### Teil 1 — Kein stilles Fallenlassen mehr

Die Skripte unter `analysis/scripts/` dürfen Varianten, die in den Daten vorkommen, nicht
unbemerkt verwerfen. Zwei Dinge sind zu trennen:

- **Reihenfolge und Beschriftung** — dafür ist eine feste Liste legitim, denn Tabellen brauchen eine
  stabile Ordnung.
- **Auswahl, welche Zeilen erscheinen** — dafür ist eine feste Liste falsch, sobald die Daten andere
  Varianten enthalten.

Wähle den Entwurf selbst. Anforderung: Enthalten die Daten eine Variante, die die Ordnungsliste
nicht kennt, muss das **sichtbar** werden — entweder erscheint sie in der Ausgabe, oder der Lauf
bricht mit einer klaren Meldung ab. Stilles Weglassen ist in keinem Fall zulässig. Begründe im
Report, welchen der beiden Wege du je Skript gewählt hast und warum.

Betroffen ist mindestens `table_main_results.py`. Prüfe die übrigen Skripte unter
`analysis/scripts/aggregate/` und `analysis/scripts/plot/` auf dasselbe Muster und behandle sie
mit.

### Teil 2 — Der Phase-A-Pfad bleibt unangetastet

`paper1_phaseA_v1` ist eingefroren und muss reproduzierbar bleiben. Weise nach, dass die
Phase-A-Auswertung nach deiner Änderung **identische** Ausgaben erzeugt — Tabelle und
Aggregate byte- oder wertgleich. Wie du das belegst, wählst du; der Nachweis gehört in den Report.

Das ist die harte Bedingung dieses Auftrags. Eine Änderung, die Phase A verschiebt, ist nicht
anzunehmen.

### Teil 3 — Beschriftungen und Farben für die Kampagnenvarianten

`analysis/utils/style.py` führt `VARIANT_COLORS` und `VARIANT_LABELS` und kennt
`evogrow_v2_2_stage_capped` nicht. Ergänze die Varianten, die in der Kampagne tatsächlich
vorkommen — die maßgebliche Liste steht in `VARIANTS` in `studies/regression/run_regression.jl` —
und achte darauf, dass die Farben unterscheidbar bleiben. Fehlt eine Beschriftung, darf das nicht
in einem `KeyError` mitten in der Tabellenerzeugung enden.

### Teil 4 — Ein Test, der den Defekt festhält

Ein Test, der mit Daten läuft, die eine der Ordnungsliste unbekannte Variante enthalten, und
sicherstellt, dass sie nicht stillschweigend verschwindet. Er muss gegen den **alten** Stand
fehlschlagen — zeige das im Report, indem du ihn einmal gegen den unveränderten Code laufen lässt.

Halte dich an `analysis/CONVENTIONS.md`.

## Verboten

- **Keine Cluster-Jobs, keine Kampagne, keine Regressions- oder Sondierungsläufe**, weder starten
  noch Manifeste dafür erzeugen.
- **Keine Änderung an Julia-Code.** Dieser Auftrag ist reine Python-Auswertung.
- **Keine Änderung an den eingefrorenen Phase-A-Artefakten** unter `experiments/`.
- **Keine neuen Metrikdefinitionen.** Wenn dir dabei eine fehlende oder fragwürdige Metrik
  auffällt, gehört sie in den Report, nicht in den Code.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

- Eine der Ordnungsliste unbekannte Variante verschwindet nicht mehr stillschweigend — belegt an
  einem konkreten Lauf mit Kampagnendaten, mit Zeilenzahl vorher und nachher.
- Die Phase-A-Auswertung liefert unverändert dieselben Ergebnisse, mit Nachweis.
- `evogrow_v2_2_stage_capped` hat Beschriftung und Farbe.
- Der neue Test schlägt gegen den alten Stand fehl und gegen den neuen nicht — beides belegt.
