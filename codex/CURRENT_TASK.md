# WP-A5 — Die Phase-B-Kampagne in die Analyse-Pipeline bringen

**Language: Python**

## Kontext

Die Phase-B-Kampagne ist am 2026-09-04 abgeschlossen: 756 von 756 Zellen, kein Record mit
gesetztem `error`, ein Identitäts-Tripel über alle Records (`git_hash = 91f88c4` mit
`git_dirty = false`, `config_fingerprint = 604e79733b22d64d`,
`stage_cap_behavior_fingerprint = ffb0266c7913352c`).

Die Records liegen bereits lokal und müssen **nicht** mehr geholt werden:

- `experiments/paper1_phaseB_v1/runs/records/` — 756 Endrecords (`cell_*.jsonl`, je 77 Felder)
- `experiments/paper1_phaseB_v1/runs/heartbeats/` — 756 Heartbeat-Ströme (in diesem WP unbenutzt)
- `experiments/paper1_phaseB_v1/history.jsonl` — die zusammengeführte History, 756 Zeilen
- `experiments/paper1_phaseB_v1/manifest.csv` und die Indexlisten

Beide `runs/`-Verzeichnisse sind über `experiments/*/runs/` gitignored. `history.jsonl` ist es
nicht — prüfe das und ergänze `.gitignore`, falls nötig; die History ist ein ableitbares Artefakt
und gehört nicht ins Repository.

**Eine Falle, die bereits einmal zugeschnappt ist.** `studies/regression/merge_batch_records.jl`
filtert sein Eingabeverzeichnis nicht nach Endrecords. Beim ersten Merge-Versuch lagen Records und
Heartbeats im selben Verzeichnis; das Skript meldete `added=756`, `skipped_failed=0` — und hatte
756 **Heartbeat-Zeilen** aufgenommen statt der Endrecords. Erkennbar war das nur an der Struktur:
15 Felder statt 77, ein Feld `event` vorhanden, `loss` und `git_hash` fehlend, und nur 378 statt
756 eindeutige Identitäten, weil `use_pretuning` im Heartbeat nicht vorkommt. Die vorliegende
`history.jsonl` ist bereits aus dem getrennten Record-Verzeichnis neu erzeugt und geprüft.

Diese Aufgabe ist der Grund für den Prüfschritt unten: eine Zusammenfassungszeile eines Skripts ist
kein Nachweis, dass die richtigen Daten angekommen sind.

## Ziel

Die 756 Kampagnen-Records reproduzierbar bis zum Aggregat in die Analyse-Pipeline bringen, mit
einer mechanischen Prüfung, die einen falschen Datenstand zum Fehlschlag macht statt zu einem
plausibel aussehenden Ergebnis.

**Ausdrücklich nicht Teil dieser Aufgabe:** jede wissenschaftliche Interpretation, jede Figur, jede
Signifikanzaussage, jede Tabelle für das Paper. Das sind spätere Work Packages. Hier geht es nur
darum, dass die Daten vollständig und identitätsrein ankommen.

## Deliverables

### 1. `analysis/configs/paper1_phaseB_v1.json`

Nach dem Muster von `analysis/configs/wp_a4_realdata_by_ic.json`. Die `experiment_id` ist
`paper1_phaseB_v1`. Die beiden IC-Sätze werden **nicht** gemittelt — die Gruppierung nach
IC-Satz ist eingeschaltet (WP-A4b hat das genau dafür eingebaut). Die Systemklassifikation kommt
aus der vorhandenen `analysis/data/paper1_phaseB_v1/system_classification.csv`, niemals aus einer
fest verdrahteten Systemliste. Pfade relativ, wie in den bestehenden Configs.

### 2. Ein Prüfskript

Neu unter `analysis/scripts/aggregate/`, benannt nach der Konvention `<verb>_<subject>.py`. Es liest
eine konvertierte `run_registry.csv` und prüft die folgenden Invarianten. Bei jeder Verletzung
beendet es sich mit einem Exit-Code ungleich null und einer Meldung, die sagt, welche Invariante
gebrochen ist und mit welchem gemessenen Wert — kein stiller Erfolg, keine Warnung, die man
übersehen kann.

Zu prüfende Invarianten:

- genau 756 Zeilen
- 756 eindeutige Identitäten aus System, Seed, IC-Satz und Bedingung
- keine Zeile mit `corrupted`, keine Zeile mit gesetztem Fehlergrund
- `git_hash` über alle Zeilen einwertig, `git_dirty` überall falsch
- `config_fingerprint` über alle Zeilen einwertig
- `stage_cap_behavior_fingerprint` über alle Zeilen einwertig
- 378 Zeilen je Bedingung
- genau 240 Zeilen mit `system_representability == "exact"` und 516 mit `"surrogate"`
- `exact_support_match` in genau den 240 exakten Zeilen belegt und in keiner Surrogat-Zeile
- `r2` in mindestens den 516 Surrogat-Zeilen numerisch belegt

Die Sollwerte sind CLI-Parameter mit diesen Zahlen als Vorgabe, nicht fest verdrahtet — das Skript
muss auch auf einer künftigen Kampagne anderer Größe brauchbar sein. Die geforderten Fingerprints
werden als Parameter übergeben, damit die Prüfung eine Aussage gegen einen erwarteten Wert ist und
nicht nur gegen sich selbst.

Ergänze eine Fixture unter `analysis/fixtures/`, die eine verletzte Invariante enthält, und weise
im Report nach, dass das Skript daran scheitert. Ein Prüfskript, dessen Fehlerpfad nie gelaufen ist,
ist kein Prüfskript.

### 3. Der Durchlauf

Führe in dieser Reihenfolge aus und halte die exakten Kommandos im Report fest:

1. `convert_campaign_history_to_run_registry.py` auf `experiments/paper1_phaseB_v1/history.jsonl`,
   mit `--experiment-id paper1_phaseB_v1`, Ausgabe nach
   `experiments/paper1_phaseB_v1/run_registry.csv` (dieser Pfad ist gitignored)
2. das neue Prüfskript auf der erzeugten `run_registry.csv`
3. `aggregate_run_registry.py` mit der neuen Config

### 4. Lückenbericht zur Spaltenabdeckung

Der Konverter schreibt eine feste Spaltenliste. Vergleiche sie gegen die 77 Felder eines
Kampagnen-Records und liste im Report auf, **welche Felder verlorengehen**. Erweitere die
Spaltenliste in diesem WP **nicht** — die Entscheidung, welche Felder die späteren Stufen brauchen,
fällt informiert, wenn das Aggregat vorliegt. Der Bericht ist das Deliverable, nicht die Erweiterung.

Von Interesse sind mindestens: `condition`, `use_pretuning`, `n_levels`, `eq_overshoot`,
`eq_final_stages`, `eq_wasted_levels`, `stage_caps`, `representability`, `total_ode_solves`,
`total_parameter_fits`, `timestamp`.

### 5. Zwei Dokumentkorrekturen

In `SCRIPTS.md`:

- Der Hinweiskasten am Ende von Abschnitt 7 („Known gap … Whether the pipeline consumes that format
  has not been verified") ist überholt. Die Brücke existiert
  (`convert_campaign_history_to_run_registry.py`) und ist auf Kampagnendaten gelaufen. Ersetze den
  Kasten durch die tatsächliche Kette History → Registry → Aggregat.
- Bei `studies/regression/merge_batch_records.jl` fehlt die Warnung, dass `--input-dir` **nur**
  Endrecords enthalten darf. Ergänze sie mitsamt dem Erkennungsmerkmal aus dem Kontext oben
  (Feldzahl, `event`, fehlendes `git_hash`). Das Skript selbst wird hier **nicht** geändert — es ist
  Julia und gehört in ein eigenes WP.

Trage das neue Prüfskript in die Skripttabelle in Abschnitt 7 ein.

## Verboten

- keine Änderung an `studies/`, `src/`, `experiments/run_experiment.jl` oder irgendeinem Julia-Code
- keine Änderung an den Kampagnen-Records oder an `history.jsonl`
- kein erneutes Mergen
- keine Figuren, keine Paper-Tabellen, keine Signifikanztests, keine Interpretation der Zahlen
- keine fest verdrahteten Systemlisten — die Systemachse kommt aus `system_classification.csv`
- kein `git add -A`; committe nichts, lass die Dateien im Arbeitsbaum liegen

## Akzeptanzkriterium

Das Prüfskript läuft auf der aus `history.jsonl` konvertierten `run_registry.csv` **fehlerfrei
durch** und scheitert auf der verletzten Fixture mit Exit-Code ungleich null. `aggregate_run_registry.py`
erzeugt sein Aggregat unter `analysis/data/paper1_phaseB_v1/` ohne Fehler, und die Zeilenzahl des
Aggregats ist im Report genannt und plausibel gegen 63 Systeme × 2 Bedingungen × 2 IC-Sätze erklärt.

## Report

`codex/REPORT_WP_A5.md`. Enthält: die exakten Kommandos, die Ausgabe des Prüfskripts in beiden
Richtungen (Erfolg und erzwungener Fehlschlag), die Zeilenzahl des Aggregats mit Erklärung, und den
Lückenbericht aus Punkt 4 als Liste.
