# Current Task

## Task: WP2 — Stdout-Logging in alle Skripte einbauen

### Ziel

Alle fünf Skripte schreiben ihre wichtigsten Stdout-Ausgaben zusätzlich in eine
Logdatei im jeweiligen Output-Verzeichnis. So kann der Fortschritt auch dann
nachvollzogen werden, wenn kein Terminal offen ist.

---

### Betroffene Skripte

| Skript | OUT_DIR (nach WP-R) |
|--------|---------------------|
| `benchmarks/benchmark_evogrow.jl` | `outputs/benchmarks/` |
| `studies/profiling/profile_init.jl` | `outputs/studies/profiling/` |
| `studies/generalization/generalization_study.jl` | `outputs/studies/generalization/` |
| `studies/debug/debug_single.jl` | `outputs/studies/debug/` |
| `experiments/run_experiment.jl` | `experiments/<experiment_id>/` |

---

### Implementierung (gleiche Logik für alle Skripte)

#### 1. Log-Datei öffnen

Am Anfang des Skripts, **nach** dem `mkpath(OUT_DIR)`-Aufruf, eine Logdatei öffnen:

```julia
_log_io = open(joinpath(OUT_DIR, "run.log"), "a")
```

Append-Modus (`"a"`), damit mehrere Starts in dieselbe Datei schreiben und
der Verlauf erhalten bleibt.

**Ausnahme `run_experiment.jl`:** Das OUT_DIR ist dort dynamisch
(`experiments/<experiment_id>/`). Die Logdatei liegt dort ebenfalls:
`joinpath(EXPERIMENT_DIR, "run.log")`. `EXPERIMENT_DIR` ist bereits im Skript
definiert — nach dessen Initialisierung die Datei öffnen.

#### 2. Hilfsfunktion definieren

```julia
function log_println(msg::String)
    println(msg)
    println(_log_io, msg)
    flush(_log_io)
end
```

Und für formatierte Ausgaben:

```julia
macro logf(fmt, args...)
    :(log_println(@sprintf($(fmt), $(args...))))
end
```

#### 3. Start- und End-Marker schreiben

Direkt nach dem Öffnen der Logdatei:

```julia
log_println("=== Started at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")) ===")
```

Am Ende des Skripts (vor dem letzten `close`-Aufruf):

```julia
log_println("=== Finished at $(Dates.format(now(), "yyyy-mm-dd HH:MM:SS")) ===")
close(_log_io)
```

`using Dates` muss importiert sein (in den meisten Skripten bereits vorhanden).

#### 4. Wichtige Ausgaben auf `log_println` / `@logf` umstellen

Nicht ALLE Ausgaben müssen umgestellt werden — nur die inhaltlich wichtigen
Fortschritts- und Statusmeldungen. Komplett ersetzen:

- Alle `println("...")` auf Toplevel (außerhalb von Hilfsfunktionen)
- Alle `@printf(...)` auf Toplevel, die Fortschritt oder Ergebnisse melden

Nicht umstellen (bleibt als normales `println`/`@printf`):
- Ausgaben in `run_one()` und anderen Hilfsfunktionen (würde zu viel Umfang erzeugen)
- Julia-interne Warnings

**Konkret pro Skript:**

**`benchmark_evogrow.jl`** — folgende Toplevel-Blöcke umstellen:
- Startmeldung (`Systems: ... Variants: ...`)
- SKIP-Zeilen (`SKIP variant=...`)
- ERROR-Zeilen (`ERROR on variant=...`)
- Abschlussmeldung (`Individual runs -> ...`, `Aggregate -> ...`, `Done.`)
- `Resuming: N runs already completed` Zeile

**`profile_init.jl`** — folgende Toplevel-Blöcke umstellen:
- Startmeldung (`Running pretuning profiling experiment...`)
- Pro-Run-Fortschrittszeilen (`println(summary_io, ...)` bleibt; nur stdout-Zeilen)
- Abschlussmeldung (`Pretuning profiling experiment finished.`)

**`generalization_study.jl`** — analog: Start, Pro-Run-Zeilen, Abschluss

**`debug_single.jl`** — analog: alle Toplevel-Ausgaben

**`run_experiment.jl`** — folgende Toplevel-Blöcke umstellen:
- Startmeldung (Experiment-ID, Anzahl Runs)
- Pro-Run-Statuszeilen (`Running run_id ...`, `Finished`, `SKIP`)
- Abschlussmeldung

---

### Was sich NICHT ändern darf

- Keine Änderung an Ausgabeformat der CSV-Dateien
- Keine Änderung an der Skript-Logik
- Keine neuen Dependencies
- `run_one()` und andere Hilfsfunktionen bleiben unverändert
- Der bestehende per-Run-Log-Mechanismus in `profile_init.jl`
  (`set_log_file` / `close_log_file`) bleibt erhalten — `run.log` ist
  zusätzlich dazu, nicht ein Ersatz

---

### Verifikation

Nach der Implementierung:

1. Ein Skript kurz starten und stoppen (z.B. `QUICK=true julia benchmarks/benchmark_evogrow.jl`).
2. `outputs/benchmarks/run.log` öffnen — muss `=== Started at ... ===` enthalten
   sowie die Startmeldung.
3. Gleiches für `studies/profiling/profile_init.jl` prüfen.
