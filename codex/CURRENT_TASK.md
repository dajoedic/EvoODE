# WP-N15b — Zwei Defekte aus der Abnahme von WP-N15

**Language: Python**

## Ausgangslage

WP-N15 ist in der Anlage richtig: die Schichtenlogik, die Trennung roh/ausgedünnt, die
Abbruchpfade und die `.gitignore`-Ausnahme sind da, und die gemeinsame Gleichheitsfunktion sitzt
korrekt in `analysis/utils/metrics.py`.

Zwei Defekte bleiben, und beide sind blockierend. Keiner davon stand im Report — sie kamen aus dem
Ausführen.

**Wichtig zur Einordnung:** der Report meldet „33 passed". Bei der Abnahme sind **4 von 33 rot**.
Die Ursache steht unter Defekt 1; die Zahl im Report war also nicht belastbar. Bitte diesmal die
volle Suite ausführen und das Ergebnis wörtlich übernehmen, nicht aus einem früheren Zwischenstand.

## Defekt 1 — die Erfolgspfade stürzen ab, sobald die Ausgabe außerhalb des Repos liegt

Am Ende von `main` wird der Ausgabepfad für die Abschlussmeldung relativ zum Repo-Wurzelverzeichnis
gemacht. Dieser Aufruf ist unbedingt. Liegt das Ausgabeverzeichnis nicht unterhalb des Repos, wirft
er `ValueError` — und alle Tests arbeiten auf `tmp_path`, wie es sich gehört.

Folge: **genau die vier Tests fallen um, die einen erfolgreichen Schreibvorgang erreichen**, während
die Abbruchpfade grün bleiben, weil sie vorher aussteigen. Das ist die unangenehme Sorte Fehler —
die Testsuite sieht überwiegend grün aus, aber kein einziger Erfolgsfall ist tatsächlich belegt.

Die Meldung ist reine Kosmetik, die Wegwerfbarkeit der Ausgabe ist es nicht: `--output-dir` ist
laut `analysis/CONVENTIONS.md` ein freier CLI-Parameter, und ein Ausgabeverzeichnis außerhalb des
Repos muss zulässig bleiben. Also: die Meldung darf den Pfad verkürzen, wenn er unterhalb des Repos
liegt, und muss ihn sonst vollständig ausgeben — abstürzen darf sie nie.

## Defekt 2 — ein normaler Wert wird als tödlicher Fehler behandelt

Der Lauf über die echten Records bricht sofort ab:

```text
Error: Record 37 field wp_n1_expected_support_terms must be a list
```

Der Exit-Code ist korrekt 1. Die Prüfung selbst ist falsch.

`wp_n1_expected_support_terms` ist für **Surrogatsysteme** `null`, und zwar konstruktionsbedingt:
`wp_n1_basis_probe.jl` setzt das Feld nur, wenn ein exakter Support hergeleitet werden konnte
(`_wp_n1_system_for_basis`). In den echten Daten ist das Feld in **221 von 335** Records `null` —
in **allen 221 Surrogatzellen** und in **keiner einzigen der 114 exakten**. Der Zusammenhang ist
exakt und muss geprüft, nicht umgangen werden.

Die bestehende Prüfung erklärt damit zwei Drittel des Datensatzes für kaputt. Sie sind es nicht.

Folge für die Wissenschaft, nicht nur für den Lauf: **Schicht C ist so unerreichbar.** Der Anteil
R² > 0,9 wird über alle Zellen berichtet, getrennt nach exakt und Surrogat — das ist die
Literaturkennzahl und nach Designprinzip 9 zwingend. Ein Skript, das an der ersten Surrogatzelle
stirbt, kann die Hälfte der geforderten Aussage nicht liefern.

Zu tun: `null` ist für Surrogatzellen der **erwartete** Wert und muss durchlaufen. Für exakte
Zellen bleibt eine Liste Pflicht — dort ist `null` weiterhin ein Abbruchgrund. Beide Trefferspalten
sind für Surrogatzellen leer im Sinne von „nicht anwendbar" und dürfen **nicht** als `False`
gefüllt werden: ein nicht vorhandener Strukturtreffer ist kein verfehlter Strukturtreffer, und in
keiner Aggregation darf ein Surrogat in einen Nenner der Strukturkennzahl geraten (Designprinzip 8).

## Warum die Tests das nicht gefunden haben

`analysis/tests/test_wp_n1_dim2_probe_aggregation.py` gibt in der Record-Fabrik **jeder** Zelle
`[["u1"], ["u2"]]` als erwartete Terme mit, auch den als Surrogat markierten. Diese Kombination —
`representability == "surrogate"` **mit** Termliste — kommt in echten Daten nicht vor. Die Fixture
bildet die Daten also an der entscheidenden Stelle falsch ab.

Die Fixtures müssen den realen Zusammenhang tragen: Surrogatzellen ohne Termliste, exakte Zellen
mit. Zusätzlich ein Test, der die **verbotene** Kombination absichert — eine exakte Zelle ohne
Termliste muss weiterhin mit einem von Null verschiedenen Exit-Code abbrechen.

## Abnahmekriterien

1. Die volle Suite unter `analysis/tests` ist grün, **alle** Erfolgspfade eingeschlossen, und die
   genannte Zahl stammt aus diesem Lauf.
2. Neue Tests: Ausgabeverzeichnis außerhalb des Repos läuft durch; Surrogatzelle ohne Termliste
   läuft durch; exakte Zelle ohne Termliste bricht mit Exit-Code ungleich Null ab.
3. Die Trefferspalten sind für Surrogatzellen als „nicht anwendbar" gekennzeichnet, nicht als
   `False`, und kein Surrogat erscheint in einem Nenner der Strukturkennzahlen.
4. Report nach `codex/reports/REPORT_WP_N15b.md`, knapp: was geändert wurde, welche Tests neu sind,
   das wörtliche Testergebnis.

Der Lauf über die echten Records bleibt blockiert, weil der Share `S:\` aus der Codex-Sitzung nicht
sichtbar ist — das ist bekannt und kein Mangel dieses Pakets. Diese Abnahme fährt Claude. Melde
den Datenlauf wieder als das, was er ist, und stütze **keine** Aussage auf echte Zahlen, die du
nicht selbst erzeugt hast.
