# WP-DIAG-AMB-b — Diagnose AMBIGUOUS: Hauptlauf vorbereiten (Teile, Cache, Log, Tests)
**Language: Python**

Grundlage: `docs/DIAGNOSTIC_AMBIGUITY.md` (eingefroren, §6 ausgefüllt: $N = 100$, Orion, 11 Pods à 1 Kern) und
der Report `codex/reports/REPORT_WP_DIAG_AMB_A.md`. Zu ändern ist nur
`experiments/annihilator_gate2a_v3/diagnostics/ambiguity_diagnostic.py` und sein Test. Die Methode, die
Zustandslogik, die Zellen, die Seeds und die Auswertung B1–B4 bleiben **genau** wie sie sind. Bestehende Records
in `results/diagnostic_ambiguity/records.jsonl` (12 Pilot-Records) werden nicht verändert.

## Zu bauen

1. **Teile:** Argument `--part i/k` (0 ≤ i < k) zu `--reps N`. Die Aufgabenliste aus `tasks_for_reps(N)` wird
   deterministisch in k disjunkte Teile zerlegt, Teil i bekommt die Aufgaben mit Index `j % k == i`. Aufgaben, die
   schon in `records.jsonl` (Pilot) stehen, werden **vor** der Zerlegung entfernt. Jeder Teil schreibt in ein eigenes
   Verzeichnis `results/diagnostic_ambiguity/parts/part_<i>_of_<k>/` mit eigenem `records.jsonl`, `run.log`,
   `nullspace_cache.json` und `DONE`. Fortsetzen pro Teil wie bisher. Ohne `--part` bleibt das Verhalten wie heute.
   Ein Ausgabeverzeichnis lässt sich per `--outdir` überschreiben (für Pods, die auf ein gemountetes Volume
   schreiben). Standard bleibt `results/diagnostic_ambiguity/`.
2. **Zusammenführen:** `--merge` liest `records.jsonl` im Hauptverzeichnis und alle
   `parts/*/records.jsonl`. Abbruch bei doppeltem (Funktion, Seed) oder bei einem Seed außerhalb von
   50000…50000+N−1, wenn `--reps N` angegeben ist. Schreibt `records_merged.jsonl`. `--summarize` bekommt
   `--records <Pfad>` (Standard wie heute).
3. **Nullraum-Cache:** Schreiben atomar (temporäre Datei im selben Verzeichnis, dann `os.replace`). Beim Schreiben
   den gelesenen Stand mit dem eigenen zusammenführen statt überschreiben. Eine unlesbare oder halbe Datei beim
   Lesen gilt als leer (mit Warnung in `run.log`), kein Abbruch. Mehrere Prozesse, die gleichzeitig schreiben,
   dürfen den Lauf nicht abbrechen.
4. **`run.log` ohne Zustand:** Die Fortschrittszeile enthält Funktion, Seed, geprüfte Klassen, AML-Iterationen und
   Sekunden, aber **keinen Zustand, keine gewählte Klasse, keine Ambiguitätsquellen und keinen Bootstrap-Anteil**.
   Die Records selbst bleiben vollständig.
5. **Fixture:** Den echten Pilot-Record F2/Seed 50000 aus `results/diagnostic_ambiguity/records.jsonl` unverändert
   nach `experiments/annihilator_gate2a_v3/tests/fixtures/record_f2_seed50000.json` kopieren. Die Tests lesen ihn
   von dort, kein `skip` mehr. Fixtures für die Auswertung werden aus diesem Record abgeleitet (Protokoll:
   „Fixtures werden abgeleitet, nicht erfunden“).
6. **Tests** (zusätzlich zu den bestehenden, alle ohne `skip`):
   - Teile: Für N = 100, k = 11, ohne die 12 Pilot-Aufgaben ist die Vereinigung aller Teile genau die Menge der
     588 offenen Aufgaben, die Teile sind disjunkt, und ihre Größen unterscheiden sich um höchstens 1.
   - Zusammenführen: ein Duplikat zwischen Haupt- und Teildatei führt zum Abbruch.
   - Cache: Eine halb geschriebene Datei wird als leer gelesen. Zwei aufeinanderfolgende Schreibvorgänge mit
     verschiedenen Schlüsseln behalten beide Schlüssel.
   - Log: Die Fortschrittszeile enthält keinen der Zustandsnamen.

## Ausführen

Nur die Tests. **Kein** Lauf von `full_search`, kein Pilot, kein Hauptlauf. Danach `--merge --reps 2` und
`--summarize --records results/diagnostic_ambiguity/records_merged.jsonl` auf den Pilot-Records als Prüfung. Das
Ergebnis muss dieselben Zustandszahlen liefern wie `summary.json` heute.

## Verboten

Keine Änderung an Methode, Zustandslogik, Zellen, Seeds, Schwellen oder B1–B4. Keine bestehende Datei unter
`experiments/` außer `diagnostics/ambiguity_diagnostic.py` und `tests/test_ambiguity_diagnostic.py` ändern. Den
Pilot-Record nicht verändern. Keine Cluster-Manifeste, kein Lauf auf Orion. Nichts außerhalb von
`experiments/annihilator_gate2a_v3/diagnostics/`, `experiments/annihilator_gate2a_v3/tests/`,
`experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/`, `codex/STATUS.md` und `codex/reports/`. Kein
Git außer lesend.

## Abnahme

Alle Tests der Datei grün, keiner übersprungen. Die Prüfung mit `--merge`/`--summarize` reproduziert die
Pilot-Zustände. Report `codex/reports/REPORT_WP_DIAG_AMB_B.md` mit den Befehlen für einen Teil
(`--reps 100 --part i/11 --outdir <Pfad>`), für `--merge --reps 100` und für `--summarize`. `codex/STATUS.md` mit
`WP-DIAG-AMB-b`.
