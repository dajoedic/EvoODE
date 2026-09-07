# WP-A9 — Die Verschwendungsmessung und das Bild je System

**Language: Python**

## Kontext

Die Phase-B-Auswertung ist bis auf zwei Punkte fertig. WP-A6 hat den gepaarten Kontrast gerechnet,
WP-A7 Effektstaerke und Seed-Kollaps, WP-A8 die deskriptiven Tabellen T1 bis T5. Alle drei sind
abgeschlossen und werden hier **nicht wiederholt**.

Offen sind: die **WP-B1-Verschwendungsmessung** auf Kampagnenbreite und das **Bild je System**.

Datengrundlage:
- `experiments/paper1_phaseB_v1/run_registry.csv`, 756 Zeilen, geprueft durch
  `verify_campaign_registry.py`
- **neu fuer dieses WP:** `experiments/paper1_phaseB_v1/runs/heartbeats/*.heartbeat.jsonl`, 756
  Dateien. Jede enthaelt ein `start`-Event, mehrere `level`-Events mit `level`, `stage`, `best_loss`
  und `timestamp`, und ein `complete`-Event.

Config: `analysis/configs/paper1_phaseB_v1.json`. Bestehende Bausteine fuer Paarung, Quantile und
Schwellengitter liegen in den A6/A7/A8-Skripten; wiederverwenden statt nachbauen, wo es passt.

## Teil 1 — Die Verschwendungsmessung aus den Heartbeat-Stroemen

`wasted_levels` in den Records bedeutet *Levels oberhalb der erwarteten Stufe* und ist nur auf
exakten Systemen definiert. Das ist **nicht** die WP-B1-Groesse. WP-B1 misst die Levels **nach der
letzten Verbesserung** — die braucht die Wahrheit nicht und gilt deshalb fuer alle 63 Systeme.
`CLAUDE.md` haelt ausdruecklich fest, dass sie aus dem `best_loss`-Strom rekonstruierbar ist und in
der Analyse-Pipeline gebaut wird, nie im Kampagnenpfad.

Je Zelle zu bestimmen:

- die Levelfolge mit ihrem `best_loss`
- das **letzte Level mit einer Verbesserung** von `best_loss` gegenueber dem bis dahin besten Wert
- `silent_levels` = Zahl der Levels danach
- `silent_fraction` = `silent_levels` geteilt durch die Zahl der Levels der Zelle

**Was „Verbesserung" heisst, ist eine Entscheidung und keine Selbstverstaendlichkeit.** Setze sie als
CLI-Parameter mit einer relativen Schwelle um (Vorgabe: jede echte Verringerung, also relative
Schwelle 0) und berichte zusaetzlich das Ergebnis fuer eine substanzielle Schwelle. Begruende im
Report, wie du mit gleichbleibendem `best_loss` und mit nicht-monotonen Folgen umgehst, falls solche
vorkommen.

**Eine Unstimmigkeit ist vorab bekannt und muss geprueft, nicht geglaettet werden:** Zelle 1 hat 20
`level`-Events, waehrend ihr Record `n_levels = 30` meldet, und `n_levels` ist in allen 756 Records
30. Ermittle die Verteilung der Level-Event-Zahl ueber alle 756 Stroeme, halte fest, in wie vielen
Zellen sie von `n_levels` abweicht, und berichte das als eigenen Punkt. **Wenn die Heartbeats den
Verlauf nicht vollstaendig abbilden, ist das eine Einschraenkung der Messung und muss so benannt
werden** — nicht durch Hochrechnen kaschiert.

Auszuweisen: Verteilung von `silent_levels` und `silent_fraction` als Quantile 5/10/25/50/75/90/95
und als Schwellengitter (Anteil der Zellen mit `silent_fraction` ueber 0,25 / 0,5 / 0,75 / 0,9), je
Dimension, Bedingung und Repraesentierbarkeit getrennt.

Zusaetzlich die Frage, die WP-B1 aufgeworfen hat: **wie viele Zellen verbessern sich zuletzt auf
Level 1** und rechnen danach nur noch stumme Levels? Als Zaehlung je Dimension.

**Kostenaussagen ruhen auf Zaehlwerten, nicht auf Zeit** (Design-Prinzip 7). Die Verschwendung wird
in **Levels** ausgedrueckt. Die Heartbeat-Zeitstempel duerfen fuer eine ergaenzende Zeitspalte genutzt
werden, aber nur mit ausdruecklicher Kennzeichnung als Nicht-Evidenz in der Tabellenbeschriftung.

## Teil 2 — Das Bild je System

Eine Tabelle mit **einer Zeile je System, IC-Satz und Bedingung** (63 x 2 x 2 = 252 Zeilen), die die
bisher ueber fuenf Tabellen verstreuten Groessen zusammenfuehrt:

Systemidentitaet und -klasse (`system_id`, `system_name`, `system_dim`, `system_representability`),
die Zielgroesse der jeweiligen Klasse (`exact_support_match`-Rate bei exakten, R²-Median bei
Surrogaten — **nie beides in einer Spalte**, Design-Prinzip 8), Loss, erreichte Stufe, `stage_caps`,
die Zaehler `total_loss_evals` / `total_ode_solves` / `total_parameter_fits`, und die
Verschwendungsgroessen aus Teil 1.

Diese Tabelle ist die Grundlage fuer die Diskussion einzelner Systeme im Paper. Sie soll **auffindbar
machen, welche Systeme aus dem Rahmen fallen** — deshalb zusaetzlich eine kurze Auszugstabelle: die
zehn Systeme mit den meisten stummen Levels und die zehn mit dem schlechtesten Zielwert ihrer Klasse,
beide Klassen getrennt.

## Teil 3 — Abbruchbedingungen

Wie bisher, plus: eine Heartbeat-Datei, die fehlt, sich nicht als JSONL lesen laesst, kein
`complete`-Event hat oder deren Identitaet (System, Seed, IC-Satz, Bedingung) nicht zu genau einer
Registry-Zeile passt. Kein stiller Ausschluss — 756 Stroeme muessen zu 756 Registry-Zeilen passen,
jede Abweichung ist ein Abbruch mit Meldung.

Fehlerpfad an einer Fixture unter `analysis/fixtures/` belegen.

## Verboten

- keine Aenderung an `src/`, `studies/`, `experiments/` oder Julia-Code — die Heartbeats werden
  **gelesen**, nie geschrieben
- keine Aenderung an `verify_campaign_registry.py` oder den A6/A7/A8-Skripten und ihren Ergebnissen
- keine Konvertererweiterung mehr; alles Noetige ist in der Registry oder in den Heartbeats
- **keine Figuren**
- **keine Signifikanztests, keine p-Werte, keine Vergleichsurteile zwischen den Bedingungen** — die
  Bedingungen stehen nebeneinander, gewertet wurde in A6/A7
- **keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`**
- kein Mittelwert oder Median als alleinige Zusammenfassung
- `elapsed_s` und Heartbeat-Zeiten nie als Kostenmass
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Beide Skripte laufen fehlerfrei; die Verschwendungstabelle und die Systemtabelle liegen als `.csv`
und `.tex` unter `analysis/tables/paper1_phaseB_v1/`, die Zwischendaten unter
`analysis/data/paper1_phaseB_v1/`. Die Systemtabelle hat 252 Zeilen. Die Zahl der ausgewerteten
Heartbeat-Stroeme ist 756. Auf der Fixture bricht die Aggregation mit Exit-Code ungleich null ab.

## Report

`codex/REPORT_WP_A9.md`. Enthaelt: die Kommandos, die Verteilung der Level-Event-Zahl und den Befund
zur `n_levels`-Unstimmigkeit, die Verschwendungstabellen, die Zaehlung „letzte Verbesserung auf
Level 1", die beiden Auszugstabellen der auffaelligen Systeme, die Begruendung der
Verbesserungsdefinition — und einen Absatz dazu, ob die Kampagnenzahlen die WP-B1-Pilotmessung
bestaetigen oder ihr widersprechen (Pilot: dim 1 rund 10 % der Zeit in stummen Levels, dim 2 50 %,
dim 3 44 %, dim 4 96 % — beachte, dass das Zeitanteile waren und deine Messung Levelanteile sind).
