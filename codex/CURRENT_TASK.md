# WP-OB-B — ODEBench-Smoke-Test Version 2: gleichmäßige Stichprobe, exakte Struktur
**Language: Python**

Grundlage: `docs/ODEBENCH_SMOKE_TEST_v2.md` (eingefroren, vollständig lesen) und `docs/ODEBENCH_SMOKE_TEST.md`
(v1, gilt, soweit v2 nichts ändert). Code in `experiments/annihilator_odebench_smoke/` (Stand `f177c8f`).

## Zu ändern

1. **Annihilator-Stichprobe (Änderung 1):** `_annihilator_record` verwendet statt der 1024 Trajektorienpunkte 2000
   gleichmäßige Punkte der Trainingsdomäne aus `setup.json`, mit $f + \eta\,\mathrm{rms}(f)\,\xi$, demselben
   Zufallsgenerator je (Seed, System, Methode) und demselben Aufruf von `full_search`. Auch der Fit von $\hat f$
   nutzt diese Punkte. Die Zahl der Punkte (2000) steht im Record.
2. **`STRUCT_OK` (Änderung 2):**
   - Annihilator: nur `CORRECT` und $\mathrm{NRMSE}_f \le 0{,}05$;
   - Baselines: nur `TRUE_STRUCTURE` und $\mathrm{NRMSE}_f \le 0{,}05$.

   Die Auswertung (`evaluate_decision`, Tabelle) berechnet `STRUCT_OK` aus Kategorie bzw. Zustand und
   $\mathrm{NRMSE}_f$ **neu** und ignoriert ein gespeichertes Feld.
3. **Version und Ablage:** Standard-Ergebnisordner `experiments/annihilator_odebench_smoke/results_v2/`. `--setup`
   kopiert dorthin `setup.json` und `reference.json` aus `results/` unverändert und prüft per Hash, dass sie
   identisch sind (nicht neu berechnen). Jeder Record trägt `spec_version: 2`. Die Auswertung bricht ab, wenn ein
   Record ohne `spec_version == 2` in der Datei steht.
4. **Plausibilitätsprüfung 2** (v1 §8) auf der neuen Stichprobe: exakter Referenzoperator, 2000 gleichmäßige
   Punkte, Produktivintervall, $\mathrm{NRMSE}_f < 10^{-6}$, dazu die Integration der Trainingstrajektorien.
   Zusätzlich muss der v3-Test (`evaluate_class` mit `test_operator`) für den exakten Referenzoperator auf diesen
   Punkten bei $\eta = 0$ **bestehen**; $T$ und der kritische Wert kommen in `sanity.json`. Schreibt
   `results_v2/sanity.json`. Scheitert etwas: Befund mit Zahlen in den Report, nichts ändern.
5. **Protokoll:** Im Worker-Pfad werden die Sekunden je Record geschrieben (heute `null`). Keine Zustände,
   Kategorien oder Gleichungen im Log.
6. **Losgelöster Start:** `--detach-marker` oder gleichwertig: Am Ende eines vollständigen `--run` wird
   `results_v2/DONE` mit Zeitstempel und Zahl der Records geschrieben, bei einem Fehler `results_v2/FAILED` mit
   Traceback.
7. **Tests:**
   - Die Annihilator-Stichprobe hat 2000 gleichmäßige Punkte auf der Domäne aus `setup.json`; das Rauschen ist
     reproduzierbar je Seed.
   - `STRUCT_OK` je Methode: Obermenge zählt nicht; Neuberechnung ignoriert ein gespeichertes `struct_ok`.
   - Abbruch der Auswertung bei einem Record ohne `spec_version == 2`.
   - Das Log enthält numerische Sekunden.
   - Bestehende Tests anpassen, wo sie die alte Definition prüfen. Der Feldlisten-Test auf echten Systemdaten
     (`test_record_fields_come_from_real_run_path`) wird auf eine **synthetische** Funktion umgestellt: Tests
     erzeugen keine Fits auf den Systemen 3, 7, 19, 21.

## Ausführen

Alle Tests (neu und v3, mit `--basetemp`), dann `--setup` für `results_v2/`. **Kein** `--run` auf den Systemen.

## Verboten

- Änderungen unter `experiments/annihilator_gate2a_v3/`, an `docs/` und an `results/` (v1, einschließlich
  `results/v1_pilot/`).
- Discovery-Läufe auf den vier Systemen, auch nicht in Tests.
- Andere Änderungen an Methode, Baselines, Library, Gitter, Seeds, Regeln oder Schwellen.
- Git-Operationen. Nichts über 15 Minuten.

## Abnahme

1. Alle Tests grün, kein `skip`.
2. `results_v2/setup.json` und `results_v2/reference.json` sind identisch mit `results/`. `results_v2/sanity.json`
   enthält je System $\mathrm{NRMSE}_f$, die Trajektorienfehler, $T$ und den kritischen Wert.
3. Report `codex/reports/REPORT_WP_OB_B.md` mit Änderungen je Punkt 1–7, Testausgabe aus diesem Lauf und den Zahlen
   der Plausibilitätsprüfung.
