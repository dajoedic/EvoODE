# WP-N14b — Ein Defekt aus der Abnahme von WP-N14

**Language: Python**

## Ausgangslage

WP-N14 ist im Kern richtig. Die Abnahme durch Claude hat ergeben:

- 26 Python-Tests grün, inklusive aller geforderten Fixture-Fälle,
- Phase-B-Ableitungen nach dem Herausziehen der Statistik nach `analysis/utils/paired_stats.py`
  **bitgleich** neu erzeugt — `git status` bleibt leer,
- die Erlaubnisliste wirkt in die richtige Richtung: unbekannte Spalten müssen gleich sein.

Ein Defekt bleibt, und er ist blockierend.

## Der Defekt — `campaign_manifest_index`

Die Spalte steht **nicht** in `ALLOWED_DIFFERENCE_COLUMNS`, muss nach der Erlaubnislogik also
zwischen den beiden Armen einer Paarung übereinstimmen.

Sie kann das nicht. Jeder Arm hat seine **eigene Zeile im Kampagnenmanifest** und damit seinen
eigenen Index; in der Phase-B-Registry unterscheidet sich die Spalte bereits in **378 von 378**
Paarungen. In Phase C wird das genauso sein.

Folge: die Auswertung von Claim B bräche auf echten Daten in **jeder** Paarung ab — und zwar
scheinbar mit dem Befund „die Bedingungen sind nicht identisch", also mit einer Meldung, die einen
Konfigurationsfehler behauptet, wo ein Buchhaltungsfeld abweicht. Das ist die schlechteste Sorte
Fehlalarm: er sieht aus wie ein wissenschaftlicher Befund.

**Zu tun:** Die Spalte gehört zu den zulässigen Unterschieden — sie identifiziert die Zelle
innerhalb der Kampagne, nicht ihre Bedingungen. Nimm sie auf, mit einem kurzen Kommentar, **warum**
sie dort steht, damit niemand sie später für einen übersehenen Fehler hält.

## Die zweite Stelle — vorsorglich, kein Fehler

`stage_cap_policy_active` und verwandte Kappen-Schalter kommen in der Phase-B-Registry **gar nicht**
vor, in den Julia-Records aber schon (`studies/regression/run_regression.jl` schreibt
`stage_cap_policy_active`). Sobald der Phase-C-Konverter dieses Feld durchreicht, unterscheidet es
sich zwangsläufig zwischen gekapptem und ungekapptem Arm — und würde denselben Fehlalarm auslösen.

`stage_caps` ist bereits in der Liste. Ergänze `stage_cap_policy_active` und prüfe die
Julia-Recordfelder auf weitere Schalter derselben Art, die sich zwischen den Armen unterscheiden
müssen. Nenne im Report, welche du geprüft und welche du aufgenommen hast.

**Nicht aufnehmen** darfst du dabei irgendetwas, das eine echte Bedingung beschreibt — Basis, Seed,
Levelbudget, Pretuning-Schalter, Screening-Schalter, Toleranzen, Fingerprints. Genau die sollen
abbrechen, wenn sie abweichen; das ist der Zweck der Prüfung.

## Der Test, der gefehlt hat

Die vorhandenen Fixtures decken ab, dass eine **unerlaubte** Abweichung abbricht. Es fehlt der
Gegenfall: dass eine Paarung, die sich **genau in den erlaubten Feldern** unterscheidet — inklusive
Armkennzeichnung, Manifestindex und Kappen-Schaltern — sauber **durchläuft**.

Ohne diesen Test wäre der Defekt nicht aufgefallen, weil kein Fixture den realistischen Fall
abbildete. Ergänze ihn.

## Verboten

- Keine Änderung an der Statistik, an der Paarungslogik oder an der Richtung der Erlaubnislogik.
  Unbekannte Spalten müssen weiterhin gleich sein.
- Keine Zahlen der Phase-B-Auswertung verändern.
- Das Skript nicht auf echten Phase-B-Daten laufen lassen und nichts daraus berichten.
- Keine neuen Abhängigkeiten, keine Julia-Datei anfassen.

## Abnahme

Python läuft bei dir — fahre sie selbst und melde `done`.

Zu belegen:

1. `python -m pytest analysis/tests/ -q` — alle grün, inklusive des neuen Positivtests.
2. Byte-Vergleich der Phase-B-Ableitungen weiterhin identisch.
3. Im Report: die vollständige Liste der Spalten, die du zusätzlich aufgenommen hast, je mit einem
   Satz Begründung, und die Liste derer, die du bewusst **nicht** aufgenommen hast.

Report nach `codex/reports/REPORT_WP_N14b.md`.
