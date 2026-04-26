# Pending: Repository-Strukturmigration (WP-R1 + WP-R2 + WP-R3)

## Wann ausführen

Erst ausführen, wenn alle drei folgenden Prozesse abgeschlossen sind:

- `experiments/run_experiment.jl paper1_phaseA_v1`
- `benchmarks/benchmark_evogrow.jl`
- `profile_init.jl`

Nicht vorher starten. Die Skripte schreiben noch in Pfade, die hier verändert werden.

---

## Ziel

Nach dieser Migration gilt:

- Benchmark-Quelldaten liegen in `benchmarks/data/`
- Explorative Studienskripte liegen in `studies/`
- Alle generierten Outputs landen unter `outputs/` (gitignored)
- `debug_results/` und `benchmarks/results/` sind abgelöst
- Der Repository-Root enthält keine losen `.jl`-Skripte mehr

---

## WP-R1: Benchmark-Daten trennen

### Schritt 1: Ordner anlegen

`benchmarks/data/` anlegen.

### Schritt 2: Datei verschieben

`benchmarks/odeformer/strogatz_extended.json` → `benchmarks/data/strogatz_extended.json`

### Schritt 3: Leeren Ordner entfernen

`benchmarks/odeformer/` ist danach leer und soll entfernt werden.

### Schritt 4: Pfadreferenzen in Skripten aktualisieren

In `benchmarks/benchmark_evogrow.jl` und `benchmarks/run_odebench.jl`:
- Alle Referenzen auf `benchmarks/odeformer/strogatz_extended.json`
  durch `benchmarks/data/strogatz_extended.json` ersetzen.

### Schritt 5: Ausgabepfad in `benchmark_evogrow.jl` aktualisieren

Den Ausgabe-Root von `benchmarks/results/` auf `outputs/benchmarks/` ändern.
Alle Dateiausgaben (summary CSV, aggregate CSV, PNGs, trajectory CSVs) folgen automatisch,
weil sie relativ zum Output-Root gebaut werden.

### Was sich nicht ändern darf

- Skript-Logik und Ausgabeformat von `benchmark_evogrow.jl`
- Alles in `src/`, `experiments/`, `studies/` (noch nicht existent)

---

## WP-R2: Studienskripte nach `studies/` verschieben

### Schritt 1: Ordnerstruktur anlegen

```
studies/
    generalization/
    profiling/
    debug/
```

### Schritt 2: Skripte verschieben

- `generalization_study.jl` → `studies/generalization/generalization_study.jl`
- `profile_init.jl` → `studies/profiling/profile_init.jl`
- `debug_single.jl` → `studies/debug/debug_single.jl`

### Schritt 3: Ausgabepfade in jedem Skript aktualisieren

`generalization_study.jl`:
- Ausgabe-Root von `debug_results/` (oder `debug_results/generalization_study/`)
  auf `outputs/studies/generalization/` ändern.

`profile_init.jl`:
- Ausgabe-Root von `debug_results/` (oder `debug_results/profile_init/`)
  auf `outputs/studies/profiling/` ändern.

`debug_single.jl`:
- Ausgabepfade für Log- und PNG-Dateien auf `outputs/studies/debug/` ändern.

In allen drei Skripten: sicherstellen, dass der Ausgabeordner via `mkpath` angelegt wird,
falls er noch nicht existiert.

### Was sich nicht ändern darf

- Skript-Logik, Ausgabeformat der CSVs und Logs
- Alles in `src/`, `experiments/`, `benchmarks/`

---

## WP-R3: `outputs/` als einzigen Output-Root definieren

### Schritt 1: `.gitignore` aktualisieren

Den Eintrag `outputs/` zur `.gitignore` hinzufügen (falls noch nicht vorhanden).
Die bestehenden Einträge `debug_results/` und `benchmarks/results/` bleiben erhalten
(für bereits vorhandene lokale Dateien).

### Schritt 2: `SCRIPTS.md` aktualisieren

Alle Ausgabepfade in `SCRIPTS.md` auf die neuen Ziele anpassen:

- `benchmark_evogrow.jl` → `outputs/benchmarks/`
- `generalization_study.jl` → `outputs/studies/generalization/`
- `profile_init.jl` → `outputs/studies/profiling/`
- `debug_single.jl` → `outputs/studies/debug/`

Die Pfade zu Skriptdateien selbst ebenfalls aktualisieren (neue Orte unter `studies/`).

### Was sich nicht ändern darf

- Bestehende `.gitignore`-Einträge (nur ergänzen, nicht entfernen)
- Alles in `src/`, `experiments/`

---

## Abschlussbedingung

Nach Abschluss aller drei Work Packages gilt:

- `benchmarks/data/strogatz_extended.json` existiert
- `benchmarks/odeformer/` existiert nicht mehr
- `studies/generalization/generalization_study.jl` existiert
- `studies/profiling/profile_init.jl` existiert
- `studies/debug/debug_single.jl` existiert
- Root enthält keine losen `.jl`-Dateien mehr
- `.gitignore` enthält `outputs/`
- `SCRIPTS.md` zeigt korrekte Pfade

## Verifikation

```
julia --project=. benchmarks/benchmark_evogrow.jl  # mit QUICK=true
julia --project=. studies/generalization/generalization_study.jl
```

Beide Skripte müssen starten und Ausgaben in `outputs/` schreiben.

---

## Commit

Nach Abschluss aller drei Work Packages einen einzelnen Commit:

```
Restructure repo: studies/, benchmarks/data/, outputs/ as unified output root
```
