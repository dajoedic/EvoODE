# WP-O1 — Die Python-Tests an ihren Ort bringen und den roten Test reparieren

**Language: Python**

## Kontext und Zweck

Beim Repo-Durchgang am 2026-09-09 sind zwei zusammenhängende Befunde aufgetaucht, die zusammen ein
Arbeitspaket ergeben.

**Erstens: der Test ist rot und niemand merkt es.**
`tests/test_analysis_variant_visibility.py::test_unknown_variant_is_not_silently_dropped_from_main_table`
schlägt mit

```
TypeError: build_csv_table() missing 2 required positional arguments: 'exact_ids' and 'surrogate_ids'
```

fehl. Die beiden Parameter sind in WP-A4/A4b dazugekommen, als die Systemachse von fest verdrahteten
ID-Listen auf `system_classification.csv` umgestellt wurde. Der Test wurde nicht mitgezogen und ist
seit etwa 2026-08-21 rot. Es gibt keine CI für Tests — die GitLab-CI baut ausschliesslich das
Kampagnen-Image.

Das ist nicht irgendein Test. Die Invariante, die er absichert — **eine unbekannte Variante darf
nicht stillschweigend aus der Haupttabelle verschwinden** — ist genau die, um die es in WP-A4b ging
("an empty selection aborts instead of reporting success"). Der Wächter ist in dem Moment ausgefallen,
in dem er am wichtigsten wurde.

**Zweitens: die Tests liegen am falschen Ort.** `tests/` (Python, 2 Dateien) steht im Wurzelverzeichnis
direkt neben `test/` (Julia, 15 Dateien). Die beiden sind auf einen Blick nicht unterscheidbar, und
`analysis/CONVENTIONS.md` sieht in seiner Verzeichnisstruktur überhaupt kein `tests/` vor. Die Tests
prüfen ausschliesslich Code unter `analysis/`, gehören also dorthin.

Beides zusammen, weil der Umzug die Pfadkonstante in denselben Dateien anfasst, die der Fix anfasst.

## Was zu tun ist

### 1. Verschieben

`tests/` → `analysis/tests/`, mit `git mv`, damit die Historie erhalten bleibt.

Beide Dateien setzen `REPO_ROOT = Path(__file__).resolve().parents[1]`. Nach dem Umzug ist
`parents[1]` das Verzeichnis `analysis/` statt der Repo-Wurzel. Der Index muss entsprechend
angepasst werden. **Bitte nicht raten** — nach dem Umzug einmal nachrechnen und die Annahme im Test
selbst absichern, etwa indem geprüft wird, dass unter `REPO_ROOT` tatsächlich `benchmarks/` oder
`CLAUDE.md` liegt. Ein Test, der den falschen Ordner für die Repo-Wurzel hält und trotzdem grün ist,
wäre schlimmer als der jetzige Zustand.

### 2. Den roten Test reparieren

`build_csv_table` in `analysis/scripts/plot/table_main_results.py` hat heute die Signatur mit
`exact_ids` und `surrogate_ids`. Der Test muss sie mit Werten aufrufen, die zu seinen eigenen
Testdaten passen — er verwendet die Systeme 2 und 23.

**Wichtig: die Invariante darf sich nicht ändern.** Der Test prüft, dass
`campaign_unknown_variant` in der erzeugten Tabelle auftaucht und nicht stillschweigend
weggefiltert wird. Wenn der Test nach der Anpassung grün wird, weil die Invariante aufgeweicht
wurde statt weil der Aufruf korrekt ist, ist das ein Fehlschlag des Arbeitspakets. Prüfe das aktiv:
lass den Test einmal gegen eine absichtlich kaputte Variante von `build_csv_table` laufen (nur lokal,
nicht committen) und überzeuge dich, dass er dann **rot** wird.

Falls sich beim Lesen herausstellt, dass die Invariante durch WP-A4b bewusst geändert wurde und der
Test heute etwas Falsches fordert: **dann nicht anpassen, sondern `blocked` melden** und im Report
begründen. Das wäre eine wissenschaftliche Entscheidung, keine technische.

### 3. Den zweiten Test mitprüfen

`test_evaluate_hypotheses_dataset_classification.py` ist grün, hängt aber an `REPO_ROOT` für
`docs/paper1_freeze_memo_phaseA.md` und `debug_results/generalization_summary.csv`. Nach dem Umzug
muss er weiter grün sein, aus demselben Grund wie vorher und nicht durch Zufall.

### 4. Dokumentation nachziehen

- `analysis/CONVENTIONS.md`: `tests/` in die Verzeichnisstruktur aufnehmen, mit einer Zeile in der
  Tabelle "Allowed and forbidden per folder". Erlaubt sind Tests gegen `analysis/`-Code; verboten
  ist alles, was einen vollständigen Kampagnenlauf oder Cluster-Zugang braucht.
- `SCRIPTS.md`: falls dort ein Testaufruf steht, den Pfad korrigieren.
- `docs/WP-E2.md` nennt in Zeile 81/82 `pytest tests ...`. Das ist ein **historischer Report** —
  nicht ändern. Reports werden nicht nachgeführt.
- `CLAUDE.md`, Abschnitt "Known Gaps": die beiden Einträge, die ich am 2026-09-09 eingetragen habe
  ("the Python test suite is red" und "the Python tests live in a root-level `tests/`"), sind danach
  erledigt und müssen entfernt werden. Der Umstand, dass **nichts** die Tests ausführt, bleibt
  stehen — das löst dieses Paket nicht.

## Was ausdrücklich nicht Teil dieses Pakets ist

- **Keine CI einrichten.** Ob Tests automatisch laufen sollen, ist eine offene Frage und wird
  gesondert entschieden.
- **Kein `test/runtests.jl`** und kein `[targets]`-Abschnitt in `Project.toml`. Das ist Julia und
  steht in `CLAUDE.md` unter WP-D4b geparkt.
- **Keine neuen Tests.** Dieses Paket repariert, was da ist.
- **Keine Änderung an `analysis/scripts/plot/table_main_results.py`**, es sei denn, der Test deckt
  dort einen echten Fehler auf. Dann: `blocked` melden statt selbst entscheiden.

## Abnahmekriterium

```bash
python -m pytest analysis/tests -q -p no:cacheprovider
```

läuft mit **2 passed, 2 passed** — also allen vier Tests grün — und das Verzeichnis `tests/` im
Wurzelverzeichnis existiert nicht mehr. Zusätzlich im Report festhalten: welchen Index `parents[...]`
jetzt hat und woran du geprüft hast, dass er stimmt; und das Ergebnis der Gegenprobe aus Schritt 2.

## Report

`codex/REPORT_WP_O1.md`, plus `codex/STATUS.md` mit `status`, `task: WP-O1` und dem Reportpfad.
