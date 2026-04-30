# Current Task

## Task: WP4 — `analysis/status.py` um Logdatei-Auswertung erweitern

### Kontext

`analysis/status.py` existiert bereits und funktioniert (WMI + Output-Datei-Timestamps).
Nach WP2 schreiben alle Skripte jetzt `run.log` in ihr jeweiliges `OUT_DIR`.
Die Logdatei enthält Marker:

```
=== Started at 2026-04-30 09:15:42 ===
...
=== Finished at 2026-04-30 11:30:17 ===
```

Dieser WP erweitert `status.py` um die Auswertung dieser Marker.

---

### Ziel

Für jedes bekannte Skript anzeigen:
- Wann es zuletzt gestartet wurde (aus `run.log`)
- Ob der letzte Start sauber abgeschlossen wurde (Finished-Marker nach dem letzten Started-Marker)
- Warnung wenn ein Skript unterbrochen wurde (Started ohne nachfolgendes Finished)

---

### Änderungen an `analysis/status.py`

#### 1. `LOG_PATHS` dict ergänzen (nach `OUTPUT_PATTERNS`)

```python
LOG_PATHS = {
    "experiments/run_experiment.jl":
        "experiments/paper1_phaseA_v1/run.log",
    "benchmarks/benchmark_evogrow.jl":
        "outputs/benchmarks/run.log",
    "studies/profiling/profile_init.jl":
        "outputs/studies/profiling/run.log",
    "studies/generalization/generalization_study.jl":
        "outputs/studies/generalization/run.log",
    "studies/debug/debug_single.jl":
        "outputs/studies/debug/run.log",
}
```

Hinweis: `experiments/run_experiment.jl` hat keine feste Experiment-ID im Pfad.
Für den Anfang den Pfad für `paper1_phaseA_v1` hardcoden — das ist das einzige
laufende Experiment. Später kann das dynamisch gemacht werden.

#### 2. Funktion `read_log_markers(script)` hinzufügen

```python
def read_log_markers(script):
    """
    Returns (last_started: datetime|None, last_finished: datetime|None).
    Reads the run.log for the given script and finds the timestamps of the
    last '=== Started at ...' and '=== Finished at ...' markers.
    """
```

Implementierung:
- Pfad aus `LOG_PATHS.get(script)` → `ROOT / path`
- Falls Datei nicht existiert: `(None, None)` zurückgeben
- Datei zeilenweise lesen (letzte 500 Zeilen reichen — tail-Logik mit `deque(maxlen=500)`)
- Regex: `r"=== (Started|Finished) at (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ==="` 
- Letztes `Started`-Match → `last_started`
- Letztes `Finished`-Match → `last_finished`
- Timestamps mit `datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")` parsen
- Bei Fehler: `(None, None)` zurückgeben

#### 3. Funktion `build_log_info(scripts)` hinzufügen

```python
def build_log_info(scripts):
    """Returns dict: script -> {'last_started': dt|None, 'last_finished': dt|None, 'clean': bool|None}"""
```

`clean` ist:
- `True`  wenn `last_finished` nicht None und `last_finished >= last_started`
- `False` wenn `last_started` nicht None und (`last_finished` ist None oder `last_started > last_finished`)
- `None`  wenn weder Started noch Finished vorhanden

#### 4. `print_known_scripts()` anpassen

In der bestehenden Funktion: nach der Output-Zeile für jedes Skript eine Log-Zeile einfügen.

**Format:**

Für `[LAEUFT]`-Skripte (via WMI bestätigt): keine Log-Zeile nötig (WMI-Info reicht).

Für `[LAEUFT?]`-Skripte (inferred):
```
           Log: gestartet 2026-04-30 09:15  (vor 2h 14m)  — läuft noch
```
(`clean=False` → "läuft noch"; `clean=True` → "sauber beendet — evtl. anderer Prozess aktiv")

Für `[idle]`-Skripte:
```
           Log: gestartet 2026-04-29 22:48  |  beendet 2026-04-30 06:41  (sauber)
```
oder wenn unterbrochen:
```
           Log: gestartet 2026-04-30 09:15  |  kein Finished-Marker  (! unterbrochen)
```
oder wenn keine Log-Datei:
```
           Log: (keine run.log gefunden)
```

#### 5. `main()` anpassen

`build_log_info(scripts)` aufrufen und das Ergebnis an `print_known_scripts()` übergeben.
Signatur von `print_known_scripts()` entsprechend erweitern.

---

### Was sich NICHT ändern darf

- WMI-Logik bleibt vollständig erhalten (kein Entfernen)
- Output-Datei-Timestamps bleiben vollständig erhalten
- Fortschritts-/ETA-Logik bleibt vollständig erhalten
- Keine neuen externen Dependencies
- Falls Logdatei nicht lesbar: graceful fallback (kein Crash), Zeile weglassen oder `(keine run.log gefunden)` anzeigen

---

### Verifikation

```
python analysis/status.py
```

Für jedes Skript mit vorhandener `run.log` muss eine Log-Zeile erscheinen.
Für Skripte ohne `run.log` muss `(keine run.log gefunden)` erscheinen, kein Fehler.
