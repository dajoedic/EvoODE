# WP-C5 — Der Heartbeat-Leser muss Neustarts aushalten

**Language: Julia**

**Vorbemerkung:** Julia startet in deiner Sitzung nicht. Das ist bekannt und **kein Grund, den
Auftrag zu verwerfen**. Schreib das Paket fertig, melde `blocked`, ins `note`-Feld ausdrücklich
*Umgebung, nicht Sache*, und halte im Report fest, welche Abnahmepunkte offen bleiben. Claude fährt
die Abnahme. Erwartet wird trotzdem: **lies das Skript vor der Abgabe gegen die Dateien, die es
einbindet** — WP-R1 ist an einem fehlenden `include` gescheitert.

## Ausgangslage

Der Kampagnen-Runner schreibt Heartbeats **anhängend**: `open(sink.path, "a")` in
`studies/regression/run_regression.jl:520`. Läuft eine Zelle ein zweites Mal — Pod-Neustart,
fortgesetzter Job, wiederholter Lauf —, enthält dieselbe Datei danach **zwei Läufe hintereinander**.

Dieser Fall ist nicht hypothetisch. Am 14.09. liegen auf der Cluster-Freigabe **32 Heartbeat-Dateien
der Zellen 883–914** aus dem abgebrochenen C-3-Start, je 3 bis 6 Zeilen, ohne Ergebnis. Sobald C-3
fortgesetzt wird, schreiben genau diese Zellen in genau diese Dateien hinein.

**Die beiden Leser verhalten sich unterschiedlich falsch:**

- `studies/regression/analyze_wasted_search_levels.jl:98` (`read_heartbeat`) **verschmilzt still**.
  `start` überschreibt nur `start_time`, alle `level`-Ereignisse landen in **einer** Liste, die
  anschließend nach Levelnummer sortiert wird. Ergebnis: eine Reihe mit **doppelten Levelnummern**.
  Erschwerend — Julias `sort!` ist in der Voreinstellung **nicht stabil**, die Verschmelzung ist also
  nicht einmal reproduzierbar.
- `analysis/scripts/aggregate/aggregate_phaseb_heartbeat_waste_systems.py:219` **bricht laut ab**
  („contains multiple start events"). Das ist sicher, aber es legt die gesamte Auswertung lahm, statt
  den auswertbaren Teil zu liefern.

Die Level-Waste-Messung wird aus genau diesem `best_loss`-Strom rekonstruiert (`CLAUDE.md`, „Known
Gaps"). Eine verschmolzene Reihe verfälscht sie lautlos.

**Dieses Paket repariert die Julia-Seite** — die, die still verfälscht. Die Python-Seite folgt
getrennt; ändere sie hier **nicht**.

## Aufgabe

`read_heartbeat` soll den Strom an `start`-Ereignissen **segmentieren** und nur das **letzte**
Segment auswerten.

Anforderungen:

- Ein Strom **ohne** `start`-Ereignis vor den ersten `level`-Ereignissen darf nicht stillschweigend
  verworfen werden. Entscheide, wie du das behandelst, und begründe es im Report — wichtig ist nur,
  dass der Fall benannt ist und nicht in eine leere Liste mündet, die wie „keine Level" aussieht.
- **Die Zahl der verworfenen Segmente und der darin enthaltenen `level`-Ereignisse muss nach außen
  sichtbar werden** — als Feld im Rückgabewert und als Spalte in der Ausgabe, die das Skript
  schreibt. Ein stiller Rückschnitt wäre derselbe Fehler in Grün: die Auswertung sähe wieder sauber
  aus, ohne es zu sein.
- Ein Strom mit **genau einem** Segment muss **bit-identische** Ergebnisse liefern wie heute. Das ist
  die Regressionsgarantie, und sie ist an echten Daten zu zeigen, nicht zu behaupten.
- `malformed` und die übrige Fehlerbehandlung bleiben, wie sie sind.

## Fixtures — und der Haken dabei

**Protokollregel seit `221a3a7`: Fixtures werden aus echten Records abgeleitet, nie erfunden.**

Hier ist das nur zur Hälfte möglich, und das ist im Report zu benennen: **einen echten
zweisegmentigen Heartbeat gibt es noch nicht** — die 32 C-3-Reste sind einsegmentig, weil der zweite
Lauf noch nicht stattgefunden hat. Der zweisegmentige Fall ist deshalb durch **Aneinanderhängen
zweier echter Ströme** herzustellen, und dass er so entstanden ist, gehört in den Report.

Echte Ströme liegen bereits lokal: **162 Dateien** unter `outputs/`, unter anderem in
`outputs/smoke_wp_h1/tasks/`, `outputs/phase_c_pilot/` und `outputs/docker_wp_h2_default/tasks/`
(`find outputs -name "*.heartbeat.jsonl"`). Du brauchst **keinen** Netzwerk- oder Clusterzugriff.
Nimm davon, was passt; wähle bewusst einen Strom mit mehreren `level`-Ereignissen, damit der Test
etwas zu unterscheiden hat.

Zu prüfen ist mindestens: Einsegment unverändert; Zweisegment liefert **nur** das zweite Segment;
die Verwurfszahlen stimmen; ein Segment ohne `level`-Ereignisse kippt die Auswahl nicht in etwas
Unsinniges.

## Abnahme

1. Ein einsegmentiger Strom liefert dasselbe wie vorher — an echten Daten gezeigt.
2. Ein zweisegmentiger Strom liefert das letzte Segment, und nur dieses.
3. Verworfene Segmente und Level-Ereignisse sind gezählt und stehen in der Ausgabe.
4. Der Fall „kein `start`" ist benannt und behandelt.
5. Laufzeit unverändert unkritisch.

## Verboten

- **Keine Änderung an `run_regression.jl`.** Der Schreibmodus bleibt, wie er ist — die Konfiguration
  ist eingefroren und die Kampagne läuft. Dass Anhängen die Ursache ist, wird im Report festgehalten,
  nicht repariert.
- Keine Änderung an der Python-Seite; die folgt getrennt.
- Keine Cluster-Zugriffe, keine Kampagnen- oder Regressionsläufe, kein Manifest dafür.
- Keine Dateien auf der Freigabe anfassen — insbesondere die 32 C-3-Reste **nicht** löschen oder
  verschieben. Das ist ein Schritt, den der Nutzer vor dem Fortsetzen von Hand macht.
- Keine neue Planungsdatei. Report nach `codex/reports/REPORT_WP_C5.md`.
