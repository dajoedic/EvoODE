> **Claude-Status:** `waiting for codex` — WP-A4b übergeben. Melde dich über `codex/STATUS.md`,
> nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-A4b — Die Abnahme-Fixtures aus WP-A4 liegen im ungetrackten Ordner
**Language: Python**

## Warum

WP-A4 ist geprüft und committet. Die Umsetzung trägt; alle fünf Abnahmepunkte habe ich unabhängig
nachvollzogen, Phase A ist byteidentisch, und der Rückfallpfad reproduziert exakt die alte
Aufteilung in acht exakte und zwei Surrogatsysteme.

Eine Sache ist dabei durchgerutscht: **`outputs/` ist in `.gitignore`.** Die Testdaten, die du
angelegt hast, liegen dort — `outputs/wp_a4_r2_fixture/campaign_history.jsonl` und die beiden
Klassifikationsdateien unter `outputs/wp_a4_error_fixtures/`. Sie sind damit nicht im Repository.

Committet sind aber die Konfigurationen, die auf sie zeigen. Fünf der acht `wp_a4_*.json` verweisen
nach `../outputs/...`. Auf einem frischen Klon zeigen sie ins Leere: Die R²-Abnahme und zwei der drei
Fehlerfälle sind nicht wiederholbar, und die Konfigurationen sind tote Dateien. Der Auftrag hatte
ausdrücklich eine **im Repository abgelegte** Testdatei verlangt.

Das ist kein Fehler in der Logik von WP-A4, sondern in der Ablage. Entsprechend klein ist der
Auftrag.

## Auftrag

Lege die drei Fixture-Dateien an einen Ort, den Git trägt, und ziehe die betroffenen
Konfigurationen darauf nach:

- die R²-Testdatei mit ihren sechs Records (gesetztes, `null`-gesetztes, fehlendes `r2`, plus
  Kontrollzeilen)
- die beiden Klassifikationsdateien der Fehlerfälle „kein überlappendes System" und
  „beobachtetes System ohne Klassifikationseintrag"

Randbedingungen:

- Der Ort muss zur Konvention in `analysis/CONVENTIONS.md` passen. `analysis/data/` ist dort
  ausdrücklich für **abgeleitete** Daten reserviert und deshalb der falsche Ort für handgeschriebene
  Eingaben — wähle einen, der Eingabe-Fixtures trägt, und begründe die Wahl im Report. Wenn dafür
  ein Abschnitt in `CONVENTIONS.md` fehlt, ergänze ihn in einem Satz.
- **Erzeugte** Artefakte bleiben, wo sie sind: konvertierte Registries, Aggregate und Tabellen
  gehören weiterhin unter `outputs/` beziehungsweise `analysis/data/` und `analysis/tables/`.
  Verschoben wird nur, was Eingabe ist.
- Die Inhalte der Fixtures bleiben unverändert. Dies ist ein Umzug, keine Neuerfindung.
- `.gitignore` wird nicht angefasst.

## Nicht Aufgabe

- Keine Änderung an der Logik von WP-A4.
- Keine neuen Abnahmefälle, keine zusätzlichen Metriken.
- Keine Git-Operationen.

## Abnahme

1. Aus einem sauberen Blick heraus prüfbar: Keine committete Konfiguration verweist mehr auf einen
   von `.gitignore` erfassten Pfad. Nenne im Report, wie du das geprüft hast.
2. Die drei betroffenen Läufe aus WP-A4 laufen erneut durch und liefern dieselben Zahlen wie im
   Report zu WP-A4: R²-Fixture mit `mean_r2 = 0.0 / n_r2 = 1` für den Null-Fall, leerem Mittel bei
   `null` und bei fehlendem Feld, sowie die beiden Fehlermeldungen im Wortlaut.
3. Phase A bleibt byteidentisch. Prüfe es erneut, auch wenn du nichts an der Logik anfasst.

## Report

`docs/WP-A4b.md`, kurz. Er hält den gewählten Ablageort samt Begründung fest und die Ergebnisse der
drei Abnahmepunkte.
