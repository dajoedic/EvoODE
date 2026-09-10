# WP-N13 — Die Kampagne wird ein expliziter, geprüfter Parameter der Auswertung

**Language: Python**

## Warum — und was an der ursprünglichen Annahme falsch war

Arbeitspaket B6 in `docs/paper1_phaseC_benchmark_plan.md` §2a lautet „Kampagnen-ID-Parameter für die
vorhandenen Aggregatskripte, sie sind auf `paper1_phaseB_v1` verdrahtet". **Nachgeprüft am
2026-09-10: das stimmt so nicht.** Die Skripte haben bereits `--registry`, `--classification`,
`--adequacy` und `--output-dir`; verdrahtet sind nur die **Defaults**.

Die tatsächliche Lücke ist eine andere und gefährlicher, weil sie still ist:

1. **`verify_campaign_registry.py` prüft `experiment_id` überhaupt nicht.** Die Spalte kommt in der
   Datei kein einziges Mal vor, steht auch nicht in `REQUIRED_COLUMNS`. Eine Registry, die Zeilen aus
   **zwei** Kampagnen enthält, besteht die Prüfung.
2. **Jeder Default zeigt auf Phase B.** Wer bei einer Phase-C-Auswertung ein Flag vergisst, erhält
   **Phase-B-Ergebnisse in einem Phase-C-Verzeichnis**, ohne Fehlermeldung. Der Plan verlangt in §5
   ausdrücklich: *Phase-B- und Phase-C-Zahlen erscheinen nie in derselben Tabelle.* Nichts erzwingt
   das derzeit.
3. **Es gibt keine Konsistenzprüfung zwischen den Eingaben.** Registry, `system_classification.csv`
   und `representational_adequacy.csv` werden unabhängig übergeben; sie dürfen heute aus
   verschiedenen Kampagnen stammen.

Das Projekt hat diesen Fehlertyp schon einmal bezahlt: ein Spaltenname mit zwei Bedeutungen (§4b),
und ein Wächtertest, der drei Wochen rot war, ohne dass es auffiel.

## Was zu bauen ist

### 1. Die Kampagne wird ein benanntes Argument

Alle Skripte unter `analysis/scripts/aggregate/`, die eine Kampagne auswerten, bekommen ein
Argument für die Kampagnen-Kennung. **Default bleibt `paper1_phaseB_v1`**, damit bestehende Aufrufe
unverändert weiterlaufen.

Aus dieser Kennung werden die übrigen Pfade abgeleitet, solange sie nicht ausdrücklich überschrieben
werden — Registry unter `experiments/<kennung>/`, abgeleitete Daten und Tabellen unter
`analysis/data/<kennung>/` bzw. `analysis/tables/<kennung>/`. Eine explizit übergebene Option hat
weiterhin Vorrang.

Betroffen sind mindestens `aggregate_phaseb_structure_metrics.py`,
`aggregate_phaseb_raw_pruned_support_comparison.py`, `aggregate_representability_threeway.py` und
`verify_campaign_registry.py`. **Prüfe die übrigen Skripte im Verzeichnis selbst** und behandle jedes
gleich, das eine Kampagne auswertet; nenne im Report, welche du warum ausgelassen hast.

### 2. Der Wächter prüft die Kampagnenidentität

`verify_campaign_registry.py` bekommt zusätzlich:

- `experiment_id` in den Pflichtspalten,
- die Prüfung, dass die Registry **genau einen** `experiment_id`-Wert enthält — mehrere sind ein
  Fehler mit einer Meldung, die die gefundenen Werte nennt,
- die Prüfung, dass dieser Wert mit der übergebenen Kampagnen-Kennung übereinstimmt.

Die bestehenden Erwartungswerte für Zeilenzahl, Bedingungen und Identitätstripel sind
Phase-B-Konstanten. Sie bleiben als Defaults, aber der Report muss festhalten, dass sie beim
Phase-C-Lauf gesetzt werden müssen — 378 statt 756 und so weiter.

### 3. Die Aggregatskripte lehnen gemischte Eingaben ab

Vor der Auswertung wird geprüft, dass die geladene Registry genau einen `experiment_id` trägt und
dass er der angeforderten Kampagne entspricht. Passt es nicht, **bricht das Skript mit einer klaren
Meldung ab**, statt zu rechnen. Ein leeres Ergebnis ist ebenfalls ein Abbruch, kein Erfolg — diese
Regel existiert seit WP-A4b und muss erhalten bleiben.

Wo eine Eingabedatei die Spalte gar nicht führt (`system_classification.csv` und
`representational_adequacy.csv` sind systemweit, nicht zellweise), wird **nicht** künstlich eine
Kampagnenspalte erfunden. Halte im Report fest, welche Eingaben systemweit sind und deshalb von der
Prüfung ausgenommen bleiben.

### 4. Tests

`analysis/tests/` bekommt Tests für:

1. Registry mit zwei verschiedenen `experiment_id`-Werten → Abbruch, und die Meldung nennt beide,
2. Registry, deren `experiment_id` nicht zur angeforderten Kampagne passt → Abbruch,
3. korrekter Fall → Erfolg,
4. Pfadableitung aus der Kennung, und dass eine explizite Option die Ableitung schlägt.

Die Tests arbeiten auf kleinen, selbst erzeugten Fixtures, **nicht** auf den echten Kampagnendaten.

## Verboten

- **Keine Zahlen der Phase-B-Auswertung verändern.** Das ist das schärfste Kriterium dieser Aufgabe.
- Keine Änderung an Metrikdefinitionen, an der Ausdünnungsregel oder an
  `analysis/utils/support_match_definition.py`.
- Keine neuen Abhängigkeiten.
- Keine Julia-Datei anfassen.
- `studies/regression/wp_n1_basis_probe.jl` und alles unter `experiments/paper1_phaseB_v1/` bleiben
  unberührt — Letzteres sind eingefrorene Kampagnendaten.

## Abnahme

**Python läuft in deiner Umgebung** — diese Aufgabe fährst du also selbst zu Ende und meldest `done`,
nicht `blocked`.

Vor der Abgabe auszuführen und im Report mit Ausgabe zu belegen:

1. `python -m pytest analysis/tests/ -q` — alle grün, inklusive der neuen Tests.
2. **Der Byte-Vergleich:** die vorhandenen Phase-B-Ableitungen unter `analysis/data/paper1_phaseB_v1/`
   und `analysis/tables/paper1_phaseB_v1/` mit den Skripten **neu erzeugen** — in ein temporäres
   Verzeichnis, nicht über die vorhandenen Dateien — und die Ergebnisse Byte für Byte gegen die
   eingecheckten Dateien vergleichen. Erwartung: **identisch**. Nenne im Report jede Datei, die du
   verglichen hast, und jede, die du nicht vergleichen konntest, mit Grund.
3. `verify_campaign_registry.py` gegen `experiments/paper1_phaseB_v1/run_registry.csv` — muss
   weiterhin bestehen.

Findest du bei (2) eine Abweichung, ist das ein Fund und kein Grund, die Erwartung anzupassen:
melde `blocked` und beschreibe die Abweichung.

Report nach `codex/reports/REPORT_WP_N13.md`.
