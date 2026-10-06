# WP-RC-A2 — Reality-Check Stufe A: Annihilator-Vergleich je Gruppe (Nachbesserung zu WP-RC-A)
**Language: Python**

Grundlage: `docs/REALITY_CHECK_DIRECT_REGRESSION.md` §7 und der Report `codex/reports/REPORT_WP_RC_A.md`. Die
Arbeit aus WP-RC-A liegt uncommittet im Working Tree und bleibt bis auf den folgenden Punkt unverändert.

## Befund aus der Abnahme

`summarize_records` in `experiments/annihilator_gate2a_v3/diagnostics/direct_regression_check.py` fasst für den
Annihilator-Vergleich F1, F2, F6 (Kontrolle) und F4, F5, F8 (N1) in **einer** Menge zusammen und berechnet darüber
`wrong_given_n1`. §7 verlangt die Zahlen **je Gruppe**. Mit allen 100 Seeds ergäbe die heutige Zusammenfassung
118/415 statt 118/118. Der Test `test_summarize_thresholds_and_real_annihilator_records` fängt das nicht, weil er
die N1-Records selbst vorfiltert und `annihilator_state_summary` direkt aufruft, statt die Ausgabe von
`summarize_records` zu prüfen.

## Zu ändern

1. Im Feld `annihilator` von `summarize_records` je Gruppe (`N1` = F4, F5, F8; `I` = F1, F2, F6) und je Umfang
   (`paired` = Seeds 50000–50019, `reference` = alle Seeds) eine eigene Zusammenfassung mit Zustandszahlen und
   der Quote WRONG / (CORRECT + TRUE_NOT_REF + WRONG). Das Feld heißt neutral, etwa `wrong_given_unambiguous`,
   nicht `..._n1`.
2. Ebenso `baseline_false_unique` für die Baseline je Gruppe (primär, Kontrolle) und Verfahren (BS, STLSQ). Die
   bestehende Aufteilung bleibt, falls sie das schon leistet, nur sauber benannt.
3. `summary.md` zeigt den Vergleich als Tabelle: Gruppe × (Annihilator gepaart, Annihilator Referenz, BS, STLSQ).
4. Test: Er prüft die **Ausgabe von `summarize_records`** und nicht eine Hilfsfunktion. Erwartet wird
   `annihilator.reference.N1` = 118/118 und `annihilator.reference.I` = 0/297, beides aus den echten
   `records_merged.jsonl`. Dazu die gepaarten Zahlen für N1 und I, in den Test geschrieben als Werte, die aus diesen
   echten Records gezählt wurden (im Report mit Herkunft nennen).

## Ausführen

Nur die Tests in `experiments/annihilator_gate2a_v3/tests/test_direct_regression_check.py` und den ganzen Ordner
`experiments/annihilator_gate2a_v3/tests/` (mit `--basetemp` wie in WP-RC-A). **Kein** Lauf mit verrauschten
Daten, kein `--exact` erneut nötig.

## Verboten

- Änderungen an BS, STLSQ, Library, Zulässigkeit, Kategorien, Schwellen oder der Verdiktlogik.
- Änderungen an bestehenden v3-Dateien außer `direct_regression_check.py` und `test_direct_regression_check.py`.
- Änderungen an `docs/`. Git-Operationen.

## Abnahme

1. Alle Tests grün, kein `skip`.
2. Der neue Test schlägt mit der alten, zusammengefassten Berechnung nachweislich fehl. Im Report steht, wie das
   geprüft wurde.
3. Report `codex/reports/REPORT_WP_RC_A2.md` mit Testausgabe aus diesem Lauf.
