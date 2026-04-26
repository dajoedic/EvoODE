# WP-R4 + WP-R5: Ordnerstruktur für Analysis und Paper anlegen

## Kontext

EvoODE wächst über ein reines Julia-Framework hinaus. Python-Analyse und Paper-Artefakte
kommen in absehbarer Zeit hinzu. Bevor die ersten Python-Skripte entstehen und bevor
Paper-1-Ergebnisse kuratiert werden, soll die dafür vorgesehene Ordnerstruktur
im Repository angelegt werden.

Diese beiden Work Packages berühren keinen laufenden Code und sind deshalb
sofort durchführbar.

---

## WP-R4: `analysis/`-Ordner anlegen

### Zweck

Python-Analyse-Skripte und optionale Notebooks bekommen eine dedizierte Heimat,
getrennt vom Julia-Framework-Code.

### Was anzulegen ist

```
analysis/
    requirements.txt        # leer, aber vorhanden; wird später mit pandas, matplotlib, seaborn befüllt
    paper1/
        .gitkeep
    exploratory/
        .gitkeep
```

### `.gitignore` ergänzen

Am Ende der bestehenden `.gitignore` folgende Zeilen hinzufügen:

```
analysis/.venv/
analysis/__pycache__/
**/*.pyc
```

### Was sich nicht ändern darf

- Alles in `src/`, `experiments/`, `benchmarks/`, `studies/` (noch nicht existent)
- Bestehende `.gitignore`-Einträge

### Abschlussbedingung

- `analysis/requirements.txt` existiert (leer)
- `analysis/paper1/` existiert (mit `.gitkeep`)
- `analysis/exploratory/` existiert (mit `.gitkeep`)
- `.gitignore` enthält die drei neuen Einträge
- Alle neuen Dateien sind gestaged (`git add`)

---

## WP-R5: `paper/`-Ordner anlegen

### Zweck

Finale Paper-Artefakte (Figuren, Tabellen, eingefrorene Result-Snapshots)
bekommen eine dedizierte Heimat, klar getrennt von Experiment-Outputs.

### Was anzulegen ist

```
paper/
    figures/
        .gitkeep
    tables/
        .gitkeep
    snapshots/
        .gitkeep
```

### Was sich nicht ändern darf

- Alles in `src/`, `experiments/`, `benchmarks/`
- Bestehende `.gitignore`-Einträge

### Abschlussbedingung

- `paper/figures/` existiert (mit `.gitkeep`)
- `paper/tables/` existiert (mit `.gitkeep`)
- `paper/snapshots/` existiert (mit `.gitkeep`)
- Alle neuen Dateien sind gestaged (`git add`)

---

## Gemeinsamer Commit

Nach Abschluss beider Work Packages einen einzelnen Commit erstellen:

```
Add analysis/ and paper/ skeleton for Python analysis and paper artifacts
```

Keine weiteren Dateien in diesem Commit.

---

## Was explizit nicht Teil dieser Aufgabe ist

- Keine Python-Skripte schreiben
- Keine Julia-Skripte anfassen
- Keine bestehenden Ordner umbenennen oder verschieben
- `SCRIPTS.md` oder `CLAUDE.md` nicht ändern
