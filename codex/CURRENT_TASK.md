# WP-OB-A — ODEBench-Smoke-Test: Pipeline, Orakel, Setup, Plausibilitätsprüfungen
**Language: Python**

Grundlage: `docs/ODEBENCH_SMOKE_TEST.md` (Entwurf, vollständig lesen). Dort stehen Systeme, Trajektorien,
Test-Anfangsbedingungen, Rauschmodelle, die Kette $L \to \hat f$, die Baselines, die Kategorien, die Metriken und die
Entscheidungsregel verbindlich. Dieser Auftrag sagt nur, was jetzt gebaut und ausgeführt wird. Bei Widerspruch oder
Unklarheit gilt das Dokument; dann `blocked` melden und nicht selbst entscheiden.

## Zu bauen

Neuer Ordner `experiments/annihilator_odebench_smoke/` (Paket mit `__init__.py`), Ergebnisse unter
`experiments/annihilator_odebench_smoke/results/`.

1. **Systeme und Daten** (§2, §3):
   - Die vier Systeme 3, 7, 19, 21 werden aus `benchmarks/data/strogatz_extended.json` per ID gelesen (Gleichung,
     Konstanten, gespeicherte Lösungen, `init_constraints`). Numerische und sympy-Ausdrücke für $f$ werden **aus
     den Katalogfeldern** erzeugt, nicht abgetippt; ein Test vergleicht sie mit den Formeln aus §2.
   - Andere IDs werden nicht geladen oder ausgegeben (Prüfset 4/49/59/62 bleibt ungesehen).
   - Daraus entstehen die Trainingsdomäne und die drei Test-Anfangsbedingungen nach der Regel aus §3, samt
     Prüfung der `init_constraints`.
   - Die Ground-Truth-Testtrajektorien werden erzeugt wie in §3.
2. **Orakel** (§2): Referenzklasse und $n_{\text{exact}}$ je System auf der Trainingsdomäne, mit derselben Logik wie
   `experiments/annihilator_gate2a_v3/oracle.py`: Kollokation, Nullraum in mpmath, Klassenordnung aus v3, symbolische
   Verifikation. Die nötigen Teile werden **kopiert und auf beliebige sympy-Ausdrücke und Domänen verallgemeinert**,
   denn v3 ist an seine Funktionsliste gebunden und bleibt unverändert. Ein Test zeigt, dass die Kopie für F4 und F5
   auf der v3-Domäne dieselbe Referenzklasse liefert wie v3.
3. **Annihilator, Oracle-$f$** (§4, §5): die Daten wie in §4, Suche mit `full_search` aus v3 (nur Import), Zustand
   gegen die Referenz, Kette $L \to \hat f$ mit Basisintegration, Auswertungsintervall, Kleinste-Quadrate-Fit und
   `FHAT_FAIL`-Gründen genau nach §5.
4. **Baselines** (§6): SINDy und W-SINDy mit pysindy 2.1, gemeinsame Library mit Zulässigkeitsregel, STLSQ mit
   `normalize_columns = True` über das Schwellengitter und AICc-Auswahl. Die im Code verwendeten pysindy-Parameter
   (auch die Standardwerte) werden in jeden Record geschrieben und im Report genannt.
5. **Kategorien und Metriken** (§7, §8) für alle drei Methoden, inklusive `STRUCT_OK`, $\mathrm{NRMSE}_f$,
   $\mathrm{NRMSE}_x$ und $R^2$ für Training und Test, Fehlschlagregeln ($\infty$) und Zählgrößen.
6. **Auswertung** (§9): eine Funktion, die aus den Records die Entscheidungsregel A, B, C, „weiter diskutieren“ und
   „sonst beenden“ berechnet, dazu die Ergebnistabelle aus §10.5 als `summary.md` und `summary.json`.
7. **CLI** `python -m experiments.annihilator_odebench_smoke.run` mit:
   - `--setup`: schreibt `setup.json` und `reference.json` und führt die beiden Plausibilitätsprüfungen aus §8 aus
     (`sanity.json`);
   - `--run --systems … --eta … --seeds … --methods …`: ein Record je (System, $\eta$, Seed, Methode) nach
     `records.jsonl`, Fortsetzen ohne Duplikate, `--workers N` für parallele Prozesse;
   - `--summarize`.

   `run.log` enthält keine Zustände, Kategorien oder Gleichungen, nur Zählgrößen und Sekunden.
8. **Tests** in `experiments/annihilator_odebench_smoke/tests/`:
   - Katalogparser gegen §2;
   - Regel für die Test-Anfangsbedingungen inklusive Ersatzfall;
   - Orakelkopie gegen v3 (F4, F5);
   - $L \to \hat f$ mit einem bekannten Operator, etwa $D^3$ auf einem Polynom zweiten Grades: exakte
     Reproduktion; Leitkoeffizient mit Nullstelle in der Domäne ergibt `FHAT_FAIL`;
   - Kategorien und `STRUCT_OK` je Methode;
   - Entscheidungsregel an Fixtures: jede Bedingung A, B, C einzeln auslösend, „weiter diskutieren“, Restfall. Die
     Fixtures werden aus einem echten Record abgeleitet, den der Test mit dem Modul erzeugt (Protokoll);
   - kein Ergebnis-Record aus einem Discovery-Lauf als Fixture.

## Ausführen

Alle neuen Tests, die bestehenden Tests in `experiments/annihilator_gate2a_v3/tests/` (mit `--basetemp` wie in
WP-RC-A) und `--setup`. **Kein** `--run`, auch nicht für einzelne Systeme oder $\eta = 0$. Den Pilot startet Claude
nach dem Einfrieren durch den Nutzer. Schlägt eine Plausibilitätsprüfung aus §8 fehl, wird der Befund mit Zahlen im
Report genannt und nichts an Methode oder Regel geändert.

## Verboten

- Änderungen an irgendeiner Datei unter `experiments/annihilator_gate2a_v3/` und an `docs/`.
- Discovery-Läufe (`full_search` auf Systemdaten, SINDy- oder W-SINDy-Fits auf Systemdaten). Erlaubt sind
  `full_search` bzw. Fits nur in Unit-Tests auf synthetischen Kleinstdaten.
- Andere System-IDs aus dem Katalog lesen oder ausgeben.
- Library, Schwellengitter, Seeds, Toleranzen, Regeln oder Schwellen anders als im Dokument.
- Neue Abhängigkeiten außer numpy, scipy, sympy, mpmath, pysindy (vorhanden).
- Git-Operationen. Nichts, was länger als 15 Minuten läuft.

## Abnahme

1. Alle neuen Tests und alle v3-Tests grün, kein `skip`.
2. `setup.json`, `reference.json` und `sanity.json` liegen vor. Der Report nennt je System die Trainingsdomäne, die
   drei Test-Anfangsbedingungen (mit Ersatzregel, falls gegriffen), die Referenzklasse und $n_{\text{exact}}$, beide
   Plausibilitätsprüfungen mit Zahlen und die geschätzten Kosten (Zahl der Klassen, die die Suche bis zur Referenz
   prüft).
3. Report `codex/reports/REPORT_WP_OB_A.md` mit Dateien, Kommandos, Testausgabe aus diesem Lauf und der Feldliste
   eines Records (aus einem Testlauf auf synthetischen Daten) mit Herkunft je Feld.
