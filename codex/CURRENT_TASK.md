# WP-N33a2 — CSV-Quoting im Datenexport und robuster Hash-Abgleich im Tor-Bericht
**Language: Julia** (Export) **und Python** (Tor-Bericht)

## Befund (Claude, Tor S1, 2026-10-01)

`studies/regression/export_phase_c_data_conditions.jl` schreibt `index.csv` mit unquotierten
Werten wie `[512,1]` in `time_shape` und `state_shape`. Beim Einlesen mit `csv.DictReader`
verschieben sich dadurch alle folgenden Spalten um eins: `time_sha256` enthält dann `state_max`.
`analysis/scripts/aggregate/robustness_stage_report.py` meldete deshalb
`check_observed_data_hash = not_passed`, obwohl die Hashes stimmen. Das hat Claude von Hand auf den
Rohzeilen geprüft. Reproduktion:

```
python analysis/scripts/aggregate/robustness_stage_report.py --stage-records outputs/stage1/s0.01_r0/tasks --clean-eval outputs/stage1/s0.01_r0/clean_eval/results.jsonl --reference-c1 outputs/phase_c_campaign_221a3a7 --export-index outputs/stage1/data_export/index.csv --output-dir outputs/wp_n33a2_check
```

## Umsetzung

1. Der Export schreibt RFC-4180-konformes CSV: Jedes Feld mit Komma, Anführungszeichen oder
   Zeilenumbruch wird gequotet. Die Spalten und ihre Reihenfolge bleiben gleich. Benutze, was das
   Projekt für CSV schon nutzt, und füge keine neue Abhängigkeit hinzu.
2. Der Tor-Bericht prüft beim Einlesen des Exportindex, ob jede Zeile genau so viele Felder hat wie
   der Kopf und ob `time_sha256` und `state_sha256` 64-stellige Hex-Werte sind. Ist das verletzt,
   **bricht er mit klarer Meldung ab**. Er rät keine Spalten und meldet auch kein `not_passed`.
3. Bestehende fehlerhafte Indexdateien werden **nicht** stillschweigend toleriert. Das Skript
   bricht bei `outputs/stage1/data_export/index.csv` mit der Meldung aus Punkt 2 ab. Claude erzeugt
   den Index danach mit dem reparierten Export neu.

## Verboten

Methodencode, Kampagnen-Runner, Fingerprints, die Datenerzeugung selbst (RNG, Seeds, Werte) ändern.
Git-Operationen, Läufe über 15 Minuten, `codex/CURRENT_TASK.md` bearbeiten, `docs/` ändern.

## Abnahme

1. Ein Python-Test mit einer Fixture, die aus der echten `outputs/stage1/data_export/index.csv`
   abgeleitet ist. Gegen den alten, kaputten Inhalt muss er abbrechen. Gegen einen korrekt
   gequoteten Inhalt mit denselben Werten muss er `passed` liefern, wenn der Record dazu passt
   (`outputs/stage1/s0.01_r0/tasks/cell_000001.jsonl`). Grün in deiner Sitzung.
2. Ein Julia-Test für das Quoting im Export (Kommando im Report, Claude führt ihn aus).
3. Im Report stehen die Kommandos, mit denen Claude den Stufe-1-Export neu erzeugt und den
   Tor-Bericht für beide Stufe-1-Bedingungen erneut rechnet. Erwartet ist
   `check_observed_data_hash = passed` in beiden.
4. Report: `codex/reports/REPORT_WP_N33A2.md`. `STATUS.md` nach Protokoll.
