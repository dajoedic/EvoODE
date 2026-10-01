# WP-N33a3 — Fixture des Quoting-Tests einfrieren
**Language: Python**

## Befund

`analysis/tests/test_robustness_stage_report.py::test_export_index_rejects_real_unquoted_stage1_row`
leitet seine „kaputte“ Fixture **zur Laufzeit** aus `outputs/stage1/data_export/index.csv` ab. Claude
hat diese Datei nach WP-N33a2 mit dem reparierten Export neu erzeugt, jetzt korrekt gequotet. Damit
existiert der kaputte Fall nicht mehr, und der Test schlägt fehl (`assert 0 != 0`). Ein Test darf
nicht davon abhängen, dass eine Ausgabedatei defekt bleibt.

## Umsetzung

Die alte, unquotierte Kopfzeile und Zeile 2 werden als **festes Literal** im Test hinterlegt, mit
einem Kommentar, woher sie stammen: die Stufe-1-Indexdatei vor WP-N33a2, 2026-10-01. Die
Werte stehen in Claudes Prüfung in `DIARY.md` 2026-10-01 bzw. lassen sich aus dem jetzigen,
gequoteten Index rekonstruieren: dieselben Felder, `[512,1]` und `[512]` unquotiert. Alle Tests, die
eine Datei unter `outputs/` lesen, prüfst du darauf, ob sie vom Zustand dieser Datei abhängen. Melde
sie im Report und friere sie ebenso ein.

## Verboten

Produktivcode ändern; Git; `docs/`; `codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

`python -m pytest analysis/tests/test_robustness_stage_report.py analysis/tests/test_compare_phasec_controls.py -q`
ist grün in deiner Sitzung. Report `codex/reports/REPORT_WP_N33A3.md`, `STATUS.md` nach Protokoll.
