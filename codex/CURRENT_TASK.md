> **Claude-Status:** `waiting for codex` — WP-A4 übergeben. Melde dich über `codex/STATUS.md`,
> nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-A4 — Die Auswertung muss Kampagnendaten tragen, ohne stumm Daten zu verlieren
**Language: Python**

## Warum

Phase B liefert 756 Zellen über 63 Systeme, davon 20 exakt und 43 Surrogat, in zwei
Anfangsbedingungs-Sätzen. Die Python-Pipeline unter `analysis/` ist auf Phase A geformt: zehn
Systeme, ein IC-Satz, Bewertung über Support-Treffer. WP-A1 hat eine Brücke gebaut und WP-A2 hat den
stummen Verlust auf der **Varianten**achse behoben. Drei Stellen verlieren weiterhin Daten, zwei
davon ohne jede Meldung.

**Defekt 1 — die Systemachse ist hartkodiert.** `analysis/scripts/plot/table_main_results.py` wählt
die Zeilen über zwei feste Listen von `system_id`. Das sind die zehn Phase-A-Systeme. Auf
Kampagnendaten fallen damit 53 von 63 Systemen heraus, ohne Warnung; enthält das Aggregat keine der
gelisteten IDs, entsteht eine **leere Tabelle mit Erfolgsmeldung**. Das ist genau die Klasse Fehler,
die dieses Projekt zweimal Evidenz gekostet hat.

**Defekt 2 — R² kommt nicht an.** Die Kampagnen-Records tragen seit WP-M1 die Felder `r2` und
`r2_by_dim`. Der Brücken-Konverter führt sie nicht, und das Aggregat kennt sie folglich auch nicht.
Damit ist die Bewertung der 43 Surrogatsysteme **nicht herstellbar** — und Grundsatz 8 in
`CLAUDE.md` schreibt genau diese getrennte Bewertung vor: exakte Systeme über Support-Recovery,
Surrogate über R². Die Hälfte der Paper-1-Ergebnisse hängt an einem Feld, das unterwegs verloren
geht.

**Defekt 3 — der IC-Satz wird weggemittelt.** Aggregiert wird über `(variant_slug, system_id)`. Die
beiden IC-Sätze verschwinden damit in einem Mittelwert. Der Stage Cap entscheidet aber je IC-Satz
unterschiedlich — System 31 ist der dokumentierte Fall —, also mittelt die Pipeline ausgerechnet die
Achse weg, an der der Beitrag des Papers hängt.

Konventionen und Ordnerregeln stehen in `analysis/CONVENTIONS.md`. Lies sie zuerst.

## Auftrag

### 1. Die Brücke muss die Felder durchreichen, die Paper 1 braucht

`analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py` schreibt eine feste
Spaltenliste. Ergänze die Felder, die in den Records vorhanden sind und in der Auswertung gebraucht
werden: **R²**, sowie die Aufwandszähler `total_parameter_fits` und `total_ode_solves`, und die
Identitätsfelder, die das Papier für die Provenienz verlangt (`stage_cap_behavior_fingerprint`; die
Kennungen `config_fingerprint` und `git_hash` sind bereits vorhanden).

Randbedingungen:

- Bestehende Spalten behalten Name und Reihenfolge. Neue Spalten werden **angehängt**, damit
  vorhandene Auswertungen nicht brechen.
- Ältere Records (Pilot, vor WP-M1) besitzen kein `r2`. Fehlt das Feld, bleibt die Zelle leer — das
  ist kein Fehlerfall. Ein `r2`, das im Record ausdrücklich `null` ist, bleibt ebenfalls leer, und
  beide Fälle müssen später von einem gemessenen `r2 = 0.0` unterscheidbar sein.
- Der Konverter interpretiert nichts. Er reicht durch.

### 2. Das Aggregat muss R² führen und den IC-Satz nicht verschlucken

`analysis/scripts/aggregate/aggregate_run_registry.py`:

- Ergänze eine R²-Kennzahl je Gruppe. Weil `r2` fehlen oder undefiniert sein darf, gehört **neben**
  den Mittelwert die Zahl der Läufe, die tatsächlich ein definiertes R² beigetragen haben. Ein
  Mittelwert ohne diese Zahl ist nicht interpretierbar.
- Ergänze die Aufwandszähler als Summen oder Mittelwerte — entscheide das einheitlich und
  dokumentiere die Wahl im Report.
- Der IC-Satz muss als Gruppierungsschlüssel **wählbar** sein. Standardverhalten bleibt das heutige,
  damit Phase A unverändert bleibt; für Kampagnendaten muss die Aufteilung nach IC-Satz ohne
  Codeänderung erreichbar sein — über die Konfigurationsdatei des Experiments, nicht über ein neues
  Kommandozeilen-Ökosystem.
- Wird nach IC-Satz aufgeteilt, obwohl die Daten die Spalte nicht führen, ist das ein **Abbruch mit
  benanntem Grund**, keine stille Rückkehr zum alten Verhalten.

### 3. Die Systemachse kommt aus der Klassifikation, nicht aus einer Liste im Code

`analysis/scripts/plot/table_main_results.py`:

- Die Aufteilung in exakte und Surrogatsysteme stammt aus
  `analysis/data/paper1_phaseB_v1/system_classification.csv`. Achtung: Diese Datei hat **eine Zeile
  je Gleichung**, nicht je System. Ein System gilt nur dann als exakt, wenn **alle** seine
  Gleichungszeilen exakt sind; eine einzige Surrogatgleichung macht das System zum Surrogat. Diese
  Regel gehört in den Report.
- Welche Systeme in der Tabelle erscheinen, ergibt sich aus dem Schnitt von beobachteten Daten und
  Klassifikation — nie aus einer Konstante im Quelltext. Die hartkodierten ID-Listen entfallen.
- Beide Tabellen bleiben **getrennt** (Grundsatz 8). Exakte Systeme werden über Loss und
  Support-Recovery dargestellt, Surrogatsysteme über Loss und **R²**. Die Spalte
  „exact match" darf in der Surrogattabelle nicht auftauchen, auch nicht leer.
- Phase-A-Daten führen keine Klassifikationsdatei mit sich. Fehlt sie, oder deckt sie kein
  beobachtetes System ab, muss das Skript entweder sauber auf das dokumentierte Phase-A-Verhalten
  zurückfallen **oder** mit benanntem Grund abbrechen — deine Wahl, aber sie muss explizit sein und
  im Report begründet werden.
- **Eine leere Tabelle ist nie ein Erfolg.** Enthält die Auswahl kein System oder keine Variante,
  bricht das Skript mit einer Meldung ab, die benennt, was beobachtet wurde und was erwartet war.
- Beobachtete Systeme, die die Klassifikation nicht kennt, dürfen nicht stumm verschwinden.

### 4. Phase A bleibt unverändert

`paper1_phaseA_v1` ist eingefrorene Evidenz. Nach deiner Änderung müssen sich Aggregat und Tabelle
für Phase A erzeugen lassen und **byteidentisch** zu den eingecheckten Dateien unter
`analysis/data/paper1_phaseA_v1/` und `analysis/tables/paper1_phaseA_v1/` sein. WP-E1 und WP-E2
haben dieses Projekt bereits dreimal gelehrt, was ein Abnahmelauf anrichtet, der seine eigene
Evidenz überschreibt.

## Nicht Aufgabe

- **Keine neuen Metriken erfinden.** Es wird nur durchgereicht und aggregiert, was die Records
  bereits enthalten.
- **Keine Julia-Änderungen.** Die Record-Seite ist vollständig.
- **Keine Kampagnen- oder Regressionsläufe**, keine Zugriffe auf `S:`.
- Keine Interpretation der Zahlen. Das Paket stellt die Auswertung her, es wertet nicht aus.
- Kein Umbau der Ordner- oder Konfigurationskonvention über das in Punkt 2 Genannte hinaus.

## Abnahme

Alle Läufe sind billig; nichts hier läuft länger als Sekunden.

1. **Kampagnendaten, echte Datei.** `outputs/wp_a1_realdata/campaign_history.jsonl` enthält
   33 Pilot-Records über 27 Systeme, exakt und Surrogat gemischt. Konvertieren, aggregieren,
   Tabelle erzeugen. Erwartung: alle beobachteten Systeme erscheinen, in der richtigen der beiden
   Tabellen. Diese Datei stammt aus der Zeit vor WP-M1 und trägt **kein** `r2` — die R²-Spalte ist
   hier also leer, und genau das ist das Verhalten, das du zeigen sollst.
2. **R² sichtbar machen.** Da lokal keine Records mit `r2` vorliegen, lege eine kleine, im Repository
   abgelegte Testdatei an, die eine Handvoll Records mit gesetztem, mit `null`-gesetztem und mit
   fehlendem `r2` enthält, und zeige daran alle drei Fälle bis in die Tabelle hinein. Es muss
   erkennbar bleiben, dass „kein R²" und „R² = 0" verschiedene Dinge sind.
3. **IC-Aufteilung.** Zeige an denselben Kampagnendaten, dass die Aufteilung nach IC-Satz die
   erwartete Zeilenzahl ergibt und dass das Standardverhalten sie weiterhin zusammenfasst.
4. **Fehlerfälle sind laut.** Zeige je eine Meldung für: leere Systemauswahl, beobachtetes System
   ohne Klassifikationseintrag, IC-Aufteilung ohne die nötige Spalte.
5. **Phase A byteidentisch**, wie oben.

## Report

`docs/WP-A4.md`. Er hält fest: die getroffenen expliziten Entscheidungen (Punkt 2 Aggregatform,
Punkt 3 Phase-A-Rückfall), die Regel „System exakt genau dann, wenn alle Gleichungen exakt",
die Zahlen aus den fünf Abnahmepunkten, und was weiterhin nicht getragen wird.

Wenn eine der Abnahmebedingungen nicht erreichbar ist, melde `blocked` mit dem Grund, statt die
Bedingung zu umgehen.
